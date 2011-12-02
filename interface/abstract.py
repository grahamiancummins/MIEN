
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

import mien.dsp.modules, inspect
from mien.dsp.gui import blockHelp, initialData
from mien.dsp.gui import editBlock as _editBlock
from mien.interface.widgets import FileBrowse
ME={}  # 'menu entry':function

def mbHelp(self, event):		
	obj = event[0]
	blockHelp(obj, self)

def runAbst(self, event):
	abst = event[0]
	dat=initialData(self)
	self.report("Running abstract model")
	abst.run(dat)
	self.report("Run complete. Result stored in %s" % dat.upath())
	self.update_all(object=dat, event="Rebuild")

def moveBlockUp(self, event):
	obj = event[0]
	abs=obj.container
	ind=abs.elements.index(obj)
	ind-=1
	abs.reorderElement(obj, ind)
	self.update_all(object=abs, event="Rebuild")

	
def moveBlockDown(self, event):
	obj = event[0]
	abs=obj.container
	ind=abs.elements.index(obj)
	ind+=1
	abs.reorderElement(obj, ind)
	self.update_all(object=abs, event="Rebuild")

	
def editBlock(self, event):
	obj = event[0]
	_editBlock(obj, self)



def _setParObject(gui, obj, args):
	par=obj.getElements("Parameters")
	if par:
		par=par[0]
	else:
		par=gui.createElement("Parameters", {})
		obj.newElement(par)
	par.setValue(args)
	gui.update_all(object=obj, event="Rebuild")

def initNumParList(self, event):
	obj = event[0]
	args={}
	arglist=mien.dsp.modules.ARGUMENTS[obj.attrib('Function')][0]
	for an in arglist:
		args[an]=0.0
	_setParObject(self, obj, args)

def fileToBlock(gui, elems):
	obj=elems[0]
	d = gui.askParam([{"Name":"Parameter File",
							"Type":str,
							"Browser":FileBrowse}])
	if not d:
		return
	try:
		s=file(d[0]).readlines()
	except:
		gui.report("cant read parameter file")
		return
	args={}
	try:
		for l in s:
			ll=l.split()
			if len(ll)>1:
				pn=ll[0]
				val=ll[1]
				try:
					val=float(val)
				except:
					pass
				args[pn]=val
	except:
		gui.report("cant parse parameter file. Each non-empty line must contain 'name min max precision' lists separated by spaces. ")
		return
	arglist=mien.dsp.modules.ARGUMENTS[obj.attrib('Function')][0]
	cp=obj.getArguments()
	for a in arglist:
		if not args.has_key(a):
			if cp.has_key(a):
				args[a]=cp[a]
			else:
				args[a]="Unknown Value"
	_setParObject(gui, obj, args)
	
		
def	printPars(self, evt):
	obj = evt[0]
	v=obj.getValue('dict')
	for k in v.keys():
		print k, v[k], type(v[k])

		
def toggle(self, evt):
	obj = evt[0]
	abst=obj.container
	
	if not abst.attrib('Disable'):
		abst.setAttrib('Disable', [])
	dis=abst.attrib('Disable')
	i=abst.elements.index(obj)
	if i in dis:
		dis.remove(i)
		self.report("Enabled")
	else:
		dis.append(i)
		self.report("Disabled")

def addData(gui, elems):
	am=elems[0]
	d = gui.askParam([{"Name":"File Name",
							"Value":"",
							"Browser":FileBrowse}
						   ])
	if not d:
		return
	doc=gui.load(fname=d[0], returndoc=True)
	dat=doc.getElements('Data', depth=1)[0]
	obj=gui.createElement('MienBlock', {'Function':'mien.dsp.nmpml.receiveData'})
	am.newElement(obj)
	obj.newElement(dat)
	d={'upath':dat.upath(), 'dpath':'/', 'recurse':True}
	gui.add2tree(obj, am)
	gui.add2tree(dat, obj)
	_editBlock(obj, gui, args=d)
	

MECM={"Run Abstract Model":(runAbst, "AbstractModel"), 
	'Set Parameters':(editBlock, "MienBlock"),
	'Set Parameters (from file)':(fileToBlock, "MienBlock"),
	'Initialize all parameters (as numbers)':(initNumParList, "MienBlock"),
	'Function Documentation':(mbHelp,"MienBlock"),
	'Move Up': (moveBlockUp, "MienBlock"),
	'Move Down': (moveBlockDown, "MienBlock"),
	'Toggle Activation': (toggle, "MienBlock"),
	"Add Data Source": (addData, 'AbstractModel'),
	'Inspect': (printPars, "Parameters")
	}
