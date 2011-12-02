#!/usr/bin/evn python

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

import basic_tools
NmpmlObject=basic_tools.NmpmlObject
stringToType=basic_tools.stringToType
typeToString=basic_tools.typeToString
from string import join
from mien.math.array import *


class Number(NmpmlObject):
	_allowedChildren = []
	_specialAttributes = ["Precision", "Range", "Units"]

	def __init__(self, node, container=None):
		'''As the parent class method, but also casts attributes to 
python data types, and initializes _references'''
		NmpmlObject.__init__(self, node, container)
		self._value=None
		
	def getValue(self, constrain=False):
		if self._value==None:
			self._value=eval(self.cdata)
		if constrain:
			self._value=self.constrain(self._value)
		return self._value
		
	def constrain(self, v):
		q=self.attrib("Precision")
		r=self.attrib("Range")
		if r:
			v=max(v, r[0])
			v=min(v, r[1])	
		if q:
			if r:
				v=v-r[0]
			if v%q:
				n,rem=divmod(v,q)
 				if rem/q >=.5:
					n=n+1
				v=n*q	
			if r:
				v=v+r[0]
			if r and not (q%1.0 or r[0]%1):
				v=int(v)
			elif not q%1.0:
		 		v=int(v)
		return v
		
	def setValue(self, v, constrain=True):
		if not type(v) in [float, int]:
			v=float(v)
		if constrain:
			v=self.constrain(v)
		self._value=v
 		self.cdata=repr(v)
		
	def setCdata(self, st):
		self.setValue(eval(st.strip()))
				
		
class String(NmpmlObject):
	_allowedChildren = []
		
	def getValue(self):
 		return str(self.cdata)
	
	def setValue(self, v):
		self.cdata=v.strip()
		
	def setCdata(self, st):
		self.cdata=st.strip()
		self.getValue()
				
class PyCode(NmpmlObject):
	_allowedChildren = []

	def __init__(self, node, container=None):
		'''As the parent class method, but also casts attributes to 
python data types, and initializes _references'''
		NmpmlObject.__init__(self, node, container)
		self._value=None
		
	def getValue(self):
		if self._value==None:
			self.checkValue()
		return self._value
	
	def setValue(self, v):
		if not type(v) in [str, unicode]:
			self._value=v
			self.cdata=repr(v)
		else:
			self.setCdata(v)
		
	def setCdata(self, st):
		if not type(st) in [str, unicode]:
			self.setValue(st)
		else:	
			self.cdata=st.strip()
			self.getValue()
			
	def checkValue(self):
		self._value=eval(self.cdata.strip())

class Boolean(NmpmlObject):
	_allowedChildren = []
	
	def getValue(self):
		foo=self.cdata.strip()
		if not foo or foo in ['None', 'False', '0', 'No', 'nil', 'null']:
			return False
		else:
			return True
	
	def setValue(self, v):
		self.cdata=str(v)
		
	def setCdata(self, st):
		self.cdata=st.strip()

def tagforpytype(value):
	if type(value) in [int, float]:
		return "Number"
	elif type(value) in [str, unicode]:
		return "String"
	elif type(value) in [bool, type(None)]:
		return "Boolean"
	elif type(value) in [list, dict]:
		return "Parameters"
	else:
		return "PyCode"

class Parameters(NmpmlObject):
	'''Class that implements a hash table or list of parameter elements

	Attributes:

	DataType: controls the behavior of the "getValue" method. This may be
"dict" or "list".	
	'''
	_allowedChildren = ["Number", "String", "PyCode", "Boolean", "Parameters"]
	_specialAttributes = ["DataType"]
		
	def __getitem__(self, key):
		v = self.getElements(None, {"Name":key},depth=1)
		if not v:
			raise KeyError("%s not in parameter set" % key)
		return v[0].getValue()

	def __setitem__(self, k, v):
		e=self.getEntry(k)
		if e==None:
			self.newEntry(str(k), v)
		else:
			e.setValue(v)

	def __delitem__(self, k):
		e=self.getEntry(k)
		if e==None:
			return
		e.sever()

	def getEntry(self,key):
		ents=self.getElements(depth=1)
		if type(key)==int:
			try:
				return ents[key]
			except IndexError:
				return None
		else:
			en=[k.name() for k in ents]
			try:
				key=en.index(key)
			except:
				return None
			return ents[key]
			
	def insert(self, i, v, name='p'):
		self.newEntry(name, v, i)
	
	def newEntry(self, name, value, insert=None):
		t=tagforpytype(value)
		#print t, value, type(value)
		ob={'tag':t, 'attributes':{'Name':name}, 'elements':[], 'cdata':[]}
		if t=='Parameters':
			if type(value)==list:
				ob['attributes']['DataType']='list'
			else:
				ob['attributes']['DataType']='dict'		
		if t=='Number' and type(value)==int:
			ob['attributes']['Precision']=1
		ob=ELEMENTS[t](ob)
		ob.setValue(value)
		self.newElement(ob, insert)
	
	def keys(self):
		k = self.getElements(depth=1)
		return [x.name() for x in k]

	def get(self, key, default = None):
		try:
			return self[key]
		except KeyError:
			return default

	def getValue(self, mode=None):
		if mode==None:
			mode=self.attrib('DataType') or 'dict'
		v=[(k.name(), k.getValue()) for k in self.getElements(depth=1)]
		if mode=='raw':
			return v
		elif mode=='dict':
			d={}
			for i in v:
				d[i[0]]=i[1]
			return d
		else:
			return [i[1] for i in v]
		
	def setValue(self, d, override=False):

		if type(d)==dict:
			names=d.keys()
			vals=d.values()
		else:
			vals=d
			names=["p%i" % ind for ind in range(len(d))]
		have={}
		for e in self.elements[:]:
			if override:
				e.sever()
			elif e.name() in names:
				have[e.name()]=e
			else:
				e.sever()
		for i in range(len(vals)):
			try:
				have[names[i]].setValue(vals[i])
			except:
				if have.has_key(names[i]):
					have[names[i]].sever()
				self.newEntry(names[i], vals[i])

	def update(self, d):
		for k in d.keys():
			self[k]=d[k]
			
class ParameterSet(NmpmlObject):
	'''This class acts as a container for an ordered list of numerical parameters. All the children of this class must be ElementReferences to Number, and all targets must have Range and Precision specified. Adding other ElementReference children results in legal XML, but serious runtime errors in many of the methods. 
	The class is primarily used by Optimizers, consequently the interface is optimized for speed. It will not "play nice" with interactive GUI access. Manual calls to "cache" and "flush" are required to maintain accurate state information if other elements (or file I/O) interact with the target Number instances. Calls to Number.getValue() sholud always be safe, but other calls (polling cdata and changing attributes in particular) are not always safe. Mest methods will fail if "cache" is not first called manually. Methods of this class directly manipulate the _value attribute of target Numbers without using Number's interface.'''
	
	_allowedChildren = ["ElementReference"]

	def __init__(self, node, container=None):
		'''As the parent class method, but also casts attributes to 
python data types, and initializes _references'''
		NmpmlObject.__init__(self, node, container)
		self._pars=None
		self._ranges=None
		self._prec=None
		self._constrain=None
		self._values=None
		self._bins=None
		self._ints=None


#	def __len__(self):
# 		'''returns the number of referenced parameters'''
# 		return len(self.elements)

	def cache(self):
		'''Create (or update) the cached values _pars, _ranges, _prec,  _values. '''
		self._pars=[q.target() for q in self.elements]
		r=[]
		for q in self._pars:
			ra=q.attrib('Range')
			r.append([min(ra), max(ra)-min(ra)])	
		self._ranges=array(r)
		mp=self._ranges[:,1]/65535.
		self._prec=array([q.attrib('Precision') or 0.0 for q in self._pars])
		self._prec=maximum(mp,self._prec)
		self._ints=nonzero1d(logical_not(logical_or(self._prec%1, self._ranges[:,0]%1)))
		if any(self._prec>mp):
			ci=nonzero1d(self._prec>mp)
			cr=take(self._ranges[:,0].ravel(), ci)
			cp=take(self._prec, ci)
			self._constrain=(ci, cr, cp)
			self._bins=(self._ranges[:,1]/self._prec).astype(uint16)+1
		else:
			self._bins=ones(len(self._pars))*65535
		self._bins=self._bins.astype(uint16)	
		if any(self._bins<2):
			id=nonzero1d(self._bins<2)[0]
			p=self._pars[id]
			print "WARNING: ParameterSet member %s can not vary. Automatically Increasing range" % str(p)
			r=p.attrib("Range")
			minr=self._prec[id]
			p.setAttrib('Range', [r[0], r[0]+minr])
			self.cache()
			return
		self._bits=None
		self._values=array([q.getValue() for q in self._pars])

		
	def quickset(self, a=None):
		'''Set all the _value attributes of target Numbers. if a is specified, uses these values. Otherwise, use the cached array.'''
		if a==None:
			a=self._values
		else:
			self._values=a
		for i, q in enumerate(self._pars):
			if i in self._ints:
				q._value=int(a[i])
			else:
				q._value=a[i]
			#print q.upath(), q.getValue(), a[i]	
				
		
	def flush(self, fast=False):
		'''Cause the state of the target numbers to be up to date with the cached values. This uses the normal Number interface and gaurantees correct cdata, value constraints, etc.'''
		for i, q in enumerate(self._pars):
			q.setValue(self._values[i])
				
	def getNames(self):
		'''Return a list of strings containing the names of the referenced parameters'''
		return [q.name() for q in self._pars]
		
	def getBins(self):
		'''Return an array of ints containing the number of values available to each referenced parameter. These numbers are int(floor((max(range) - min(range))/Precision)) Parameters used by MIEN optimizers have 16 bit resolution, so if Precision is 0, unspecified, or very very small, the number of bins will be 65536 (no value of precision will result in a bigger number of bins).''' 
		return self._bins

	def size(self):
		'''Return the number of points in the search space specified by the referenced parameters'''
		return multiply.reduce(self.getBins())
			
	def constrain(self, a, bound=True):
		'''Return a potential value array based on "a" such that the values obey the precision constraints of the referenced Numbers. 
		Setting bound to False skips checking if values are in range.'''
		a=a.astype(float64)
		if self._constrain==None:
			return a
		(ci, cr, cp)=self._constrain
		cv=take(a, ci)
		cv=divmod(cv-cr, cp)
		cv=cv[0]+(cv[1]>(.5*cp))
		cv=cr+cp*cv
		#print a.dtype, cv.dtype, ci.dtype
		put(a, ci, cv)
		if bound:
			a=maximum(a, self._ranges[:,0])
			a=minimum(a, self._ranges[:,0]+self._ranges[:,1])
		return a
					 	
	def code16toPar(self, a):
		'''Return a potential value array determined by the int16 code in "a"'''
		a=(a.astype(float64)+32768)/65536.
		a=(a*self._ranges[:,1])+self._ranges[:,0]
		return 	self.constrain(a, False)	
		 	
	def getCode16(self, a=None):
		'''Return a 1D int array of length len(self) containing a 16bit int encoding of a. If a is unspecified, use the current value of the parameters'''
		if a==None:
			a=self._values
		a=(a.astype(float64)-self._ranges[:,0])/self._ranges[:,1]
		a=(a*65536)-32768
		return round(a)
		
	def getNumBits(self):
		'''Return an array of ints specifying the number of real bits of information required to specify each parameter ("real" bits are used to efficiently code the state of a multi-state parameter, not the datatype. A float prameter will use 64 storage bits for the data type, but if it is constrained to a range of 0-6 and a precision of .5, then it has only 12 possible values, so the information content is fully specified by 4 bits).
		A side effect of this function is to cache the bit shifts required to code or decode binary parameter specifications, so it must be called before calling the methods getBits and bitstoPar'''	
		br=self._bins
		nbits=ones_like(br)
		mv=2**nbits
		toofew=mv<br
		while any(toofew):
			nbits+=toofew
			mv=2**nbits
			toofew=mv<br
		self._bits=cumsum(concatenate([[0], nbits[:-1]]))		
		return nbits
		
	def setBitPrec(self, a):
		'''Sets the precision attributes of each parameter such that each one has a number of states exactly specified by the number of bits in the coresponding entry of "a" (an int array). This makes binary assignment more efficient'''
		for i, p in enumerate(self._pars):
			r=self._ranges[i,1]
			pr=floor(r/2**a[i])
			p.setAttrib('Precision', pr)
		v=self._values.copy()
		self.cache()
		v=self.constrain(v)
		self.quickset(v)
		self.flush()
				
	def getIndex(self, a=None):
		'''Return an array of int16 representing "a" as indexes into the ranges of allowed parameter values (e.g. if a parameter has Range (14.3-28.2), Precision .4, and value 15.1 the index is 2 - this is because the array of possible values is [14.3, 14.7, 15.1, 15.5 ...], and 15.1 has python array index 2 in this array). If a is unspecified, use the current value of the parameters'''
		if a==None:
			a=self._values
		a=((a-self._ranges[:,0])/self._prec).astype(uint16)
		return a
		
	def indextoPar(self, a):
		'''return an array of potential parameter values from an int array of indexes 
		Note that indexes will be rendered modulo bins, so indexes larger than the total number of bins for a parameter will "wrap" to low values of the parameter.'''
		a=a%self._bins
		return self._ranges[:,0]+self._prec*a		
			
	def getBits(self, a=None):
		'''return a single python Long representing "a" in a binary code. If a is unspecified, use the current value of the parameters'''
		a=self.getIndex(a)
		v=a[0]
		for i in range(1,a.shape[0]):
			v+=(a[i]<<self._bits[i])
		return v
			
	def bitstoPar(self, v):
		'''Convert an int (interpreted as a bit string) to potential parameter values. This function converts the bits to indexes and calls self.indextoPar, so "wrapping" behavior is the same as in that function.'''
		ind=zeros(len(self._pars))
		for i in range(ind.shape[0]-1, -1, -1):
			nv=v>>self._bits[i]
			ind[i]=nv
			v-=(nv<<self._bits[i])
		return self.indextoPar(ind)
		
			

	
ELEMENTS={"Number":Number,
	"String":String, 
	"PyCode": PyCode,
	"Boolean": Boolean,
	"Parameters": Parameters,
	"ParameterSet":ParameterSet}
