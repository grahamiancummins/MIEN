
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

from mien.xml.xmlclass import BaseXMLObject
import re, copy, os
from mien.math.array import ArrayType, any, nonzero1d

notinname=(re.compile(r"[\s/?:]"))

integertail=re.compile(r"(\D*)(\d*)(.*)$")

DONOTCONVERT=['Url', 'FileName']

def uniqueName(name, used):
	if not name in used:
		return name
	parts=integertail.match(name)
	base, num, tail=parts.groups()
	if num=='':
		num=1
	else:
		num=int(num)
	while name in used:
		num+=1
		name="%s%i%s" % (base, num, tail)
	return name


def stringordersort(a, b):
	return cmp(str(a), str(b))

def stringToType(s):
	if not type(s) in [str, unicode]:
		return s
	if ',' in s:
		return [stringToType(x) for x in s.split(',') if x]
	else:
		try:
			sat=eval(s)
			if type(sat) in [float, int, list, tuple, ArrayType]:
				return sat
			else:
				return s
		except:
			return s

def typeToString(v, pre=6):
	if type(v) in [str, unicode]:
		return v
	if type(v) in [list, tuple]:
		v=[typeToString(x, pre) for x in  v]
		s = ','.join(v)
		if len(v)<2:
			s = s + ","
		return s 
	if type(v)==float:
		s=str(v)
		if len(s)>pre:
			s="%."+str(pre)+'g'
			s=s % (v,)
		return s
	else:
		return str(v)
		
class NmpmlObject(BaseXMLObject):
	'''Base class for nmpml objects
attributes:
   Keys in this hash are strings containing no whitespace. Values are strings (that
   may contain space).
   The attribute "Name" is treated specially: if present it should be a unique
   identifier amoung instances haveing the same value of "__tag__".
   Values of the form ClassNameReference are treated specially.
   These serve as pointers to instances of ClassName, which have the
   "Name" attribute equal to the specified value.
'''
		
	_allowedChildren = None
	_requiredAttributes = ["Name"]
	_specialAttributes = []
	_guiConstructorInfo ={}
	_hasCdata = True
	DONOTCONVERT=['Url', 'FileName']
	
	
	def __init__(self, node, container=None):
		'''As the parent class method, but also casts attributes to 
python data types, and initializes _references'''
		BaseXMLObject.__init__(self, node, container)
		self.castAttributes()
		self._references=[]	
	
	def sever(self):
		for q in self.elements[:]:
			q.sever()
		for q in self._references:	
			q.clearTarget()
		self._references=[]
		self.elements=[]
		try:
			self.container.removeElement(self)
		except:
			pass
		self._guiinfo=None
		self._owner=None		
		self.container=None
		
		
	def initIsValid(self, node):
		if not node['attributes'].get('Name'):
			node['attributes']['Name']="0"
			#print "Warning: <%s> initialized with no name. Added one." % (node['tag'],)
		return BaseXMLObject.initIsValid(self, node)

	def __str__(self):
		return self.__tag__+":"+str(self.name())
			
	def name(self):
		return str(self.attributes['Name'])
		
	def getDoc(self):
		q=self	
		while q.container:
			q=q.container
		return q

	def update_refs(self):
		'''correct the target fields of registered references. This is
recursive (which it usually has to be, since changing an element changes
the paths of all its children)'''
		for r in self._references:
			r.setTarget(self)
		for c in self.elements:
			c.update_refs()

	def move(self, nc):
		'''move self to a new container. Verify name uniquness and 
update references.'''
		if self.container:
			self.container.removeElement(self)
		nc.newElement(self)
		self.update_refs()  

	def castAttributes(self):
		'''convert the values of self.attributes to python data types'''
		a={}
		for k in self.attributes.keys():
			if k in self.DONOTCONVERT:
				a[k]=self.attributes[k]
			else:
				a[k]=stringToType(self.attributes[k])
		self.attributes=a
		
	def getAttributes(self):
		'''Return a copy of the attribute dictionary. Cast all the 
		elements to strings (with floating point precision of 6 places)'''
		a={}
		for k in self.attributes.keys():
			a[k]=typeToString(self.attributes[k])
		return a
	
	def setAttrib(self, a, v, inherit=False):
		'''set attributes key a to v, with cast to python datatypes'''
		if a=="Name":
			self.setName(v)
		else:	
			if not a in self.DONOTCONVERT:
				v=stringToType(v)
			BaseXMLObject.setAttrib(self, a, v, inherit)

	def setName(self, name=None):
		'''always use this function to change the name of an nmpml 
object, to avoid generating non-unique names.
If this function is called without arguments (or name is None), it will
verify name uniqueness of the current name.

Return value is the actual name that was set (which may be different than
the provided argument do to required name uniqueness)

Its a very good idea to call "update_refs" after calling this function, 
since it may break references
'''
 		if name==None:
			try:
 				name=self.name()
			except:
				name="element"
 		name=notinname.sub('_', name)
 		if self.container:
 			sibs=self.container.getElements(depth=1)
 			sibs.remove(self)
 			sibs=[x.name() for x in sibs]
 			name=uniqueName(name, sibs)
		self.attributes['Name']=name
		self.update_refs()
		return name
	
	def newElement(self, e, index=None):
		'''add the element e to self.elements. Verify name 
uniqueness'''
		e.container=self
		if index==None:
			self.elements.append(e)
		else:
			self.elements.insert(index, e)
 		e.setName()

	def setElements(self, els):
		'''Set the list self.elements, and the link e.container'''
		self.elements=els
		for e in self.elements:
			e.container=self
		if not os.environ.get("MIEN_NO_VERIFY_XML"):
			ns=[e.name() for e in self.elements]
			bnc=[notinname.search(n) for n in ns]
			if any(bnc):
				self.report('warning: fixing illegal names')
				ind=nonzero1d(bnc)
				for i in ind:
					on=ns[i]
					nn=notinname.sub('_', on)
					ns[i]=nn
					self.elements[i].attributes['Name']=nn
					self.elements[i].update_refs()				
			us=set(ns)
			if len(us)==len(ns):
				return
			self.report('warning: non unique names')
			sibs=[]
			for i, n in enumerate(ns[:]):
				if n in sibs:
					nn=uniqueName(n, sibs)
					self.elements[i].attributes['Name']=nn
					self.elements[i].update_refs()
					sibs.append(nn)
				else:	
					sibs.append(n)

	def getInstance(self, xpath, orNone=False):
		'''upath (string) => instance
		return the instance with the specified upath. If it is not present, return None if orNone is True, or raise a StandardError if it is False (default).
As with pathSearch, paths beginning with / are treated as absolute, others are relative'''
		s = xpath
		if s.startswith("/"):
			if self.container:
				e = self
				while e.container:
					e = e.container
				return e.getInstance(s, orNone)
			else:
				s = s[1:]
				if not s:
					return self
		if s. endswith("/"):
			s = s[:-1]
		s = s.split("/")
		match = self
		while s:
			ct = s.pop(0)
			tag, name = ct.split(":")
			try:
				match = [x for x in match.elements if x.__tag__==tag and x.name()==name][0]
			except:
				if orNone:
					return None
				raise StandardError("No element with path %s" % xpath) 
		return match	
		
	def upath(self):
		'''  => string
		Returns the unique path to this element. This resembles an Xpath,
		but rather than /tag/tag ..., it contains /tag:Name/tag:Name
		In valid nmpml, this is a unique ID for any element that has it
		(Points and Comments dont have a modPath). As with xpath, the path
		ends in a / iff the element has children. (Note: The xpath(True) method
		of BaseXMLObject can be used to get a list of instance references,
		which is also unique)'''
		p = [self]
		e = self.container
		while e:
			p = [e]+p
			e = e.container
		path = "/"
		for e in p[1:]:
			path+=e.__tag__+":"+e.name()+"/"
		if self.container and not self.elements:
			path = path[:-1]	
		return path

  	def addComment(self, s):
		''' s (str) => None'''
		com  = filter(lambda x: x.__tag__ == 'Comments', self.elements)
		if com:
			com = com[0]
			com.setCdata(com.getCdata()+'\n'+s)
		else:
			com =Comment({'tag':"Comments", 'attributes':{'Name':'c0'}, 'cdata':s, 'elements':[]})
			self.newElement(com)

	def getTypeRef(self, tag, target=False):
		'''tag(str) => list of instances
return all ElementReference instances that are direct children of self, and 
that point to objects with __tag__ == tag. If "target" is True, return the 
targets, rather than the references'''
		ers = self.getElements("ElementReference", {},1)
		gers = []
		for e in ers:
			t = e.attrib("Target").split("/")
			t = t[-1] or t[-2]
			t=t.split(":")[0]
			if tag == t:
				gers.append(e)
		if target:
			gers=[g.target() for g in gers]
		return gers

	def getElementOrRef(self, tag):
		'''Returns an instance that is one of:
1) the first direct child element with the specified tag
2) The target of the first ElementReference that is a direct child of 
	the instance such that the target has the specified tag
3) None, if niether of the first two classes of elements exist'''
		els= self.getElements(tag, {},1)
		if els:
			return els[0]
		els=self.getTypeRef(tag)
		if els:
			return els[0].target()
		return None		
				
	def extendedSearch(self, cond, els=None):
		if els==None:
			els=set(self.getElements())
		elif not type(els)==set:
			els=set(els)
		if cond[1]=="paths":
			hits=[e for e in els if e.upath().startswith(cond[2])]
		elif cond[1]=="tags":
			hits=[e for e in els if e.__tag__==cond[2]] 
		elif cond[1]=="attributes":
			attr, mode, pat = cond[2:]
			print attr, mode, pat
			if mode=="Equals":
				hits=[e for e in els if repr(e.attrib(attr))==repr(pat)]
			elif mode=="Is Defined":
				hits=[e for e in els if attr in e.attributes]
			elif mode=="Is True":
				fvs=[None, "No", "0", "False", ""]
				hits=[e for e in els if not e.attrib(attr) in fvs]
			elif mode=="Matches Regex":
				r = re.compile(pat)
				hits=[e for e in els if e.attrib(attr) and r.search(str(e.attrib(attr)))]
			elif mode.startswith("Is Numerically"):
				hits=[]
				pat=float(pat)
				for e in els:
					try:
						v=float(e.attrib(attr, True))
						if mode.endswith("Greater"):
							if v>pat:
								hits.append(e)
						elif v<pat:
							hits.append(e)
					except:
						pass
			elif mode.startswith("Contains"):
				hits=[e for e in els if pat in e.attrib(attr)]
			else:
				hits=[]
		else:
			hits=[]
		hits=set(hits)	
		if cond[0].endswith("Not"):
			hits=els-hits
		return hits
	
	def compoundSearch(self, conds):
		locked=False
		hits=self.extendedSearch(conds[0])
		if conds[0][0].startswith("And"):
			locked=True
		for c in conds[1:]:
			if locked:
				newhits=self.extendedSearch(c, hits)
			else:
				newhits=self.extendedSearch(c)
			if c[0].startswith("And"):
				locked=True
				hits=hits.intersection(newhits)
			else:
				hits=hits.union(newhits)
			if locked and len(hits)==0:
				return []
		return list(hits)

	def cloneData(self, clone):
		'''called by clone. Subclasses that use special data members should 
overload this method to attach deep copies (no side effects!) of these 
members to the clone. This function is called after child elements are 
added to the clone'''
		pass
		
	def clone(self, recurse=True):
		'''Return a deep copy of self. If recurse is true, clone all
child elements as well'''
		node=self.getTree(recurse=0)
		q=self.__class__(node)
		if recurse:
			for e in self.elements:
				q.newElement(e.clone())
		self.cloneData(q)
		return q

class Comment(NmpmlObject):
	'''This class is allowed as a child of almost all nmpml classes.
The purpose of this class is to hold a comment string, which is stored as 
cdata. The class provides no special methods, can not contain children, 
and has no attributtes (though it should have a "Name" attribute in order to 
support searching using upath functions).''' 	
	_allowedChildren = []
	_requiredAttributes = []
	
	def __str__(self):
		s = self.cdata[:20].replace("\n", "/")
		return "Comments: " + s
	
class Group(NmpmlObject):
	__tag__ = "Group"
	_hasCdata = False

class ElementReference(NmpmlObject):
	'''Class for representing a link to another element'''
	_allowedChildren = ["Comments"]
	_requiredAttributes = ["Name", "Target"]
	_specialAttributes = ["Index", "Data"]
	_hasCdata = False


	def __init__(self, node, container=None):
		'''As the parent class method, but also casts attributes to 
python data types, and initializes _references'''
		NmpmlObject.__init__(self, node, container)
		self._target=None

	def onLoad(self):
		try:
			self.setTarget()
		except:
			pass
		NmpmlObject.onLoad(self)

	def __str__(self):
		epath = self.attrib("Target").split("/")
		epath = epath[-1] or epath[-2]
		return "Ref-%s" % epath

	def setAttrib(self, a, v, inherit=False):
		'''set attributes key a to v, with cast to python datatypes'''
		if a=="Name":
			self.setName(v)
		elif a=="Target":
			self.setTarget(v)
		else:	
			NmpmlObject.setAttrib(self, a, v, inherit)

	def clearTarget(self):
		try:
			t=self.target()
			t._references.remove(self)
		except:
			pass
		self._target=None
		
	def setTarget(self, newtarget=None):
		'''newtarget is a upath or an instance'''
		if newtarget==None:
			newtarget=self.attrib("Target")
		if type(newtarget) in [str, unicode]:
			self.attributes["Target"]=newtarget
			self._target=self.getInstance(newtarget)
		else:
			self._target=newtarget
			self.attributes["Target"]=newtarget.upath()
		if not self in self._target._references:
			self._target._references.append(self)			
		
	def target(self):
		if not self._target:
			self._target=self.getInstance(self.attrib("Target"))
		return self._target

		
class NmpmlCompat(NmpmlObject):
	'''This class can read generic xml without altering it, and will 
provide the majority of features specific to the mien interface (and will
prevent the interface from throwing errors all the time). 

Without the required, unique, "Name" attribute, mien's mode of horizontal 
reference won't work. This class implements a partial fix, but it won't hold 
up under user interaction that moves objects around.'''	
	_allowedChildren = None
	_requiredAttributes = []
	_xmlHandler = None
	_hasCdata = True

	def __init__(self, node, container=None):
		BaseXMLObject.__init__(self, node, container)
		self.castAttributes()
				
	def initIsValid(self, node):
		return BaseXMLObject.initIsValid(self, node)
	
	def newElement(self, e):
		e.container=self
		self.elements.append(e)
	
	def name(self):
		if self.attrib("Name"):
			return self.attrib("Name")
		if not self.container:
			return "0"
		return str(self.container.elements.index(self))	
	
	def update_refs(self):
		pass
	
	def setName(self, name=None):
		'''Just sets the attribute Name'''
		self.attributes['Name']=name
		return name
		



ELEMENTS = {"default class":NmpmlObject,
			"Nmpml": NmpmlObject,
			"Comments":Comment,
			"Group":Group,
			"ElementReference":ElementReference}
