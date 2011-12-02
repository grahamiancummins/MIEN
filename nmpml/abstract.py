#!/usr/bin/env python

## Copyright (C) 2005-2006 Graham I Cummins
## This program is free software; you can redistribute it and/or modify it under 
## the terms of the GNU General Public License as published by the Free Software 
## Foundation; either version 2 of the License, or (at your option) any later version.
## 
## This program is distributed in the hope that it will be useful, but WITHOUT ANY 
## WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
## PARTICULAR PURPOSE. See the GNU General Public License for more details.
## 
## You should have received a copy of the GNU General Public License along with 
## this program; if not, write to the Free Software Foundation, Inc., 59 Temple 
## Place, Suite 330, Boston, MA 02111-1307 USA
## 

from basic_tools import NmpmlObject
import base64, os,  gc, cPickle
from sys import byteorder
from mien.math.array import *
from data import newData

	
class AbstractModel(NmpmlObject):
	'''Class for any abstract model that takes inputs, runs
a code object on them, and generates output. This class acts as a container for 
computational elments, including MienBlock instances (which run functions defined in 
"mien.blocks.*"), FlowControl instances, and nested AbstractModel instances. 
AbstractModels may also contain ElemntReferences if the target of the reference 
is a legal AbstractModel component.

The order of the AbstractModel's "elements" list is essential to proper function.
For this reason, it is _strongly_ reccomended that the elements list never be modified 
directly. Use newElement, removeElemnt, and the additional method reorderElement
if you need to modify it. This is particularly important if you use the "Disable"
attribute.
	
Attributes

	Distributer : may be a upath reference to a Distributer. If so, 
		when "run" is called with a Data element that is of SampleType "group",
		the model will execute each subelement of Data in parallel via the specified
		server.

	FileReference and FileUPath :
		If FileReference is specified, this instance acts as a pointer to an 
		AbstractModel defined in a different nmpml file. If FileUPath is specified, 
		this will be tho model with that upath. Otherwise, this instance will 
		open the file and get the first AbstractModel returned by 
		doc.getElements('AbstractModel'). When run, this instance will call that 
		model's run method (this means that any children of this AbstractModel will 
		be ignored and never run. This also means that local values of other 
		attributes (like Disable and Distributer) are ignored.)
		
	Disable:
		This may be a Boolean value or a list of ints. If it is True, 
		the run method of this instance will simply pass. If it is a list, The
		run method will not call any child objects with indexes in the list.

	InputData:
		This may be a url specifying a file to load data from. This will then be used to acquire initial data if the run method is called without arguments.
 		
	Description:
		This field can be used to hold arbitrary text describing the model, it is 
		provided because unlike most nmpml elements AbstractModel does not allow
		Comment children (they were considered too likely to cause errors in the 
		indexing of the computational elemnts
'''

	_allowedChildren = ["ElementReference", "FlowControl", "MienBlock", "AbstractModel"]
	_specialAttributes = ["Distributer","FileReference","FileUPath", "Disable", "Description"]
	_guiConstructorInfo = {} 
	_xmlHandler = None
	_hasCdata = False

	def removeElement(self, e):
		if not e in self.elements:
			return
		i=self.elements.index(e)
		NmpmlObject.removeElement(self, e)
		dis=self.attrib('Disable')
		if dis and i in dis:
			dis.remove(i)

	def reorderElement(self, e, newi):
		'''causes the element e (an instance) to have index i in self.elements'''
		newi=max(newi, 0)
		newi=min(newi, len(self.elements)-1)
		self.elements.remove(e)
		self.elements.insert(newi,e)
		
	def run(self, data=None, elements=None, forcelocal=False):
		'''data (instance of Data or URL or None, =None) elements (list of ints or None, =None)
		forcelocal(bool, =False)=> Data instance 
Calls the run method all the child elements of self, sequentially, on
data, and then returns data. Attributtes of the instance may modify which
elements are run. If data is initially False, this method creates a new
Data instance and passes it to the first element. This element will be
initialized with SampleType "group".

If data is a group containing more than one depth 1 child, then distributed computation may be used to process all of the grouped elements in parallel.

forcelocal is a flag that, when True, supresses distributed computation. It is intended
for internal use by EServer (to prevent re-distribution from the compute nodes, for jobs 
that use nested data groups), but it can also be used for testing a model locally before
running it remotely.

If the argument "elements" is specified, only the indexes listed in that list will be 
run, and these will be run even if they are specified in self.attrib('Disable').
'''
		rem=self.getExternalFile()
		if rem:
			rem.run(data, elements, forcelocal)
			return 
		if 	data==None and self.attrib('InputData'):
			data=self.attrib('InputData')
		if data==None:
			doc=self.xpath(True)[0]
			d=doc.getElements('Data', 'AbstractModelData')
			if d:
				data=d[0]
			else:	
				data=newData(None, {'Name':'AbstractModelData', 'SampleType':'group'})
				doc.newElement(data)
		if type(data) in [str, unicode]:
			import mien.parsers.fileIO
			doc=mien.parsers.fileIO.read(data)
			data=doc.getElements('Data')[0]
			self.xpath(True)[0].newElement(data)
		if not elements:
			elements=range(len(self.elements))
			dis=self.attrib('Disable')
			if dis:
				elements=list(set(elements).symmetric_difference(set(dis)))
		if not forcelocal and self.attrib('Distributer') and data.stype()=='group' and len(data.getElements('Data', depth=1))>1: 
			es=self.getInstance(self.attrib('Distributer'))
			es.batch(self.upath(), 'run', [(d, elements, True) for d in data.getElements('Data', depth=1)])
		else:
			for ind in elements:
				e=self.elements[ind]
				#self.report("-- " + str(e))
				if e.__tag__=="ElementReference":
					e=e.target()
				e.run(data, forcelocal=forcelocal)
				if data.attrib('AbortAbstractRun'):
					self.report('Run aborted by component %i' % ind)
					break
		return data

	def getExternalFile(self):
		ef=self.attrib('FileReference')
		if not ef:
			return None
		from mien.parsers.fileIO import read
		doc=read(ef)
		ep=self.attrib('FileUPath')
		if ep:
			return doc.getInstance(ep)
		else: 
			return doc.getElements('AbstractModel')[0]

	def tagScan(self, depth=1, atdepth=0, indent=True, maxlist=6):	
		maxlist=max(maxlist, 20)
		return NmpmlObject.tagScan(self, depth, atdepth, indent, maxlist)	

class FlowControl(AbstractModel):
	'''This class is a subclass of AbstractModel that allows more complex execution
order than is provided by the basic AbstractModel. The attribute "ControlType" 
determines the behavior'''
	pass

class MienBlock(NmpmlObject):
	'''This class provides the basis for adding computational elements to 
AbstractModels. Each MienBlock instance wraps a function defined in one of 
the submodules of mien.blocks. The MienBlock provides a run method that will 
run the function, and acts as a container for a Parameters instance that
specifies the parameters for the function.

Attributes

	Function: name of the function called by this instance. This name 
		assumes the namespace "mien.blocks." 
'''
	_allowedChildren = ["Comments", "Parameters", "Data", 'ElementReference']
	_requiredAttributes = ["Name", "Function"]
	
	def __str__(self):
		return "Block: %s" % self.attrib('Function')
		
	def getFunction(self):
		import mien.dsp.modules
		fn=self.attrib('Function')
		try:
			f=mien.dsp.modules.FUNCTIONS[fn]
		except:
			self.report("unknown function %s" % (fn,))
			raise
		return f 
	
	def getArguments(self):
		par=self.getElements("Parameters")
		if not par:
			return {}
		par=par[0]	
		return par.getValue('dict')	
		
	def tagScan(self, depth=1, atdepth=0, indent=True, maxlist=6):
		'''returns a recursive list of elements, including self, to the
specified depth. (set depth to a negative integer to scan to unlimited depth)'''
		info=[]
		if indent:
			ws="  "*atdepth
			offset="  "
		else:
			info.append(s)
			ws=""
			offset=""
		import mien.dsp.modules
		try:
			self.getFunction()
			fn=self.attrib('Function')
		except:
			fn="! "+self.attrib('Function')+" !"	
		args=self.getArguments()
		try:
			ao=mien.dsp.modules.ARGUMENTS[fn][0]
		except:
			if not fn.startswith("!"):
				raise
			ao=args.keys()
		arg=""
		for k in ao:
			v=str(args.get(k, "?"))
			arg+="%s=%s," % (k, v)
		for k in args.keys():
			if not k in ao:
				arg+="+%s=%s+," % (k, str(args[k]))
		arg=arg.rstrip(',')	
		i=self.container.elements.index(self)
		dis=i in self.container.attributes.get('disable', [])
		if dis:
			dis=" -- "
		else:
			dis=" "
		info.append(ws + offset+ str(i)+dis+fn )
		info.append(ws+offset+offset+arg)
		return info
	
	def checkFunction(self):
		import mien.dsp.modules
		try:
			self.getFunction()
		except:
			return "Unknown Function"
		args = self.getArguments()
		args=set(args.keys())
		fa=mien.dsp.modules.ARGUMENTS[self.attrib('Function')]
		fa=set(fa[0])
		if fa==args:
			return "OK"
		if fa-args:
			return "Unspecified args: %s" % (tuple(list(fa-args)),)
		else:
			return "Extra args: %s" % (tuple(list(args-fa)),)
		
	
	def run(self, data, **kw):
		f=self.getFunction()
		kwargs=self.getArguments()
		f(data, **kwargs)

	def getParInstance(self):
		par=self.getElements("Parameters")
		if par:
			return par[0]
		else:
			import parameters
			ob={'tag':'Parameters', 'attributes':{}, 'elements':[], 'cdata':''}
			pi=parameters.Parameters(ob)
			self.newElement(pi)
			return pi		

	def setArguments(self, args):
	 	par=self.getParInstance()
		par.setValue(args)


ELEMENTS = {"AbstractModel":AbstractModel,
			"MienBlock":MienBlock,
			"FlowControl":FlowControl}

