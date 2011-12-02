
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
import os

def get_all_children(object, tags, attribs, depth, heads):
	matches = []
	e = object.elements[:]
	if tags:
		tags = map(lambda x: str(x).strip(), tags)
		e = filter(lambda x: x.__tag__ in tags, e)
	for k in attribs.keys():
		v = attribs[k]
		e = filter(lambda x:x.attrib(k)==v, e)
	matches.extend(e)
	depth-=1
	if depth!=0:
		for e in object.elements:
			if heads and e in matches:
				continue
			else:	
				matches.extend(get_all_children(e, tags, attribs, depth,heads))
	return matches

class BaseXMLObject(object):
	'''Base class for XML objects
members:
   _allowedChildren: list of tags that can be nested in this tag (An empty
                     list allows no children, but None allows any children).
   _requiredAttributes: list of required attributes for this tag (default [])
   _xmlHandler: BaseXMLHandler subclass to use for parsing
                this tag (BaseXMLHandler will be used if this is None)
   _hasCdata: If True, collect cdata for this tag
    container (Instance): a reference to the containing XML object, or None
	elements (list): a (possibly empty) list of child objects
	__tag__ (str) : the name of the xml tag that defines this object
	attributes (dict): a dict of xml attributes
	cdata (str) : A string containing xml cdata. If this is None (not a string)
	              associated handlers will ignore cdata. BaseXMLHandler resets this according
				  to the value of the "cdata" key in taginfo (see xmllib.BaseXMLHandler)

    attributes (dict): Keys in this hash are strings containing no whitespace. Values are
	                   strings (that may contain space).
'''
	_allowedChildren = None
	_requiredAttributes = []
	_xmlHandler = None
	_hasCdata = True

	def __init__(self, node, container=None):
		'''node is a dictionary containing keys "tag" (string), 
"attributes" (dict), "elements" (list of dicts), "cdata" (string 
or list of strings). This init function will ignore the "elements" 
list (in general, each of those nodes will be converted to different
classes by somefunction (like xmlhandler.assignClasses) which can then
be added to this element using "newElement". Subclasses may opt to 
handle ther child elements internally instead. In this case, the 
subclass __init__ function should remove any handled children from
node["elements"] manually, so that functions like assignClasses will 
not redundantly add child elements based on these entries.'''
		if node['cdata']:
			if type(node['cdata'])==list:
				node['cdata'] = "".join(node['cdata']).strip()
			else:	
				node['cdata'] = node['cdata'].strip()
		else:
			node['cdata']=''
		# test=self.initIsValid(node)
		# if not test:
		# 	if not os.environ.get("MIEN_NO_VERIFY_XML"):
		# 		raise IOError("xml class init on invalid data")
		# 	else:
		# 		print "Warning: xml class initialized with invalid data"
		self.elements=[]
		self.fileinformation={"filename":None,
								"appended":[],
								"type":None}
		self.container = container
		self.attributes=node['attributes']
		self.cdata=node['cdata']
		self.__tag__=node['tag']
		self._owner=None

	def initIsValid(self, node):
		if not self._hasCdata:
			if node['cdata']:
				print "<%s> initialized with (nontrivial) cdata, and tag doesn't support cdata" % node['tag']
				return False
		for r in self._requiredAttributes:
			if not r in node['attributes']:
				#print r, node['attributes']
				print "<%s> initialized without required attribute %s" % (node['tag'], r)
				return False
		if not self._allowedChildren==None:
			kids=[x['tag'] for x in node['elements']]
			if not set(kids).issubset(self._allowedChildren):
				print  "<%s> initialized with un-allowed child element" % (node['tag'],)
				print "allowed Children: %s" % (str(self._allowedChildren),)
				print "aassigned Children: %s" % (str(set(kids)),)
				return False
		return True		

	def move(self, nc):
		'''move self to a new container. Verify name uniquness and 
update references.'''
		if self.container:
			self.container.removeElement(self)
		nc.newElement(self)

	def newElement(self, e):
		'''add a new element to the element list''' 
		e.container=self
		self.elements.append(e)
	
	def setElements(self, els):
		'''Set the list self.elements, and the link e.container'''
		self.elements=els
		for e in self.elements:
			e.container=self
	
	def removeElement(self, e):
		'''removes an element from self.elements. In this class, this 
is trivial, but subclasses may need to use it to maintain state.'''
		if e in self.elements:
			self.elements.remove(e)
	
	def addDocument(self, d):
		'''adds all the top level elements from a document d to self'''
		nfi=d.fileinformation
		for e in d.elements[:]:
			e.fileinformation=nfi
			self.newElement(e)
		self.fileinformation['appended'].append(d.fileinformation['filename'])	
		self.fileinformation['appended'].extend(d.fileinformation['appended'])	


				
	def __str__(self):
		'''return self.__tag__'''
		return self.__tag__

	def attrib(self, name, inherit=False):
		'''name(str) => value(str) or none
shortcut to self.attributes.get(name)'''
		if not inherit:
			return self.attributes.get(name)
		if name in self.attributes:
			return self.attributes[name]
		if self.container:
			return self.container.attrib(name, True)
		else:
			return False
	
	def getInheritedAttributes(self):
		els = self.xpath(True)
		d = {}
		for e in els:
			d.update(e.attributes)
		return d


	def setAttrib(self, a, v, inherit=False):
		'''set attributes key a to v'''
		if not inherit:
			self.attributes[a]=v
		elif a in self.attributes:
			self.attributes[a] = v
		else:
			els = self.xpath(True)[:-1]
			els.reverse()
			for e in els:
				if a in e.attributes:
					e.attributes[a]=v
					break
				else:
					self.attributes[a]=v


	def isTrue(self, attrib):
		'''attrib (str) => bool
Returns true if the specified attribute is defined and doesn't have a 
value of "", "0", "None", "False", or "No" ("0", "None", and "False" are true 
in normal python treatment, since they are strings)''' 
		a=self.attrib(attrib)
		if not a:
			return False
		if a in ["0", "None", "False", "No"]:
			return False
		return True	

	def getElements(self, tags=[], attribs={}, depth=-1, heads=False):
		'''returns all children recursively to a depth "depth". If depth
is negative (or 0), recurses all the way to the leaf level. If it is 1,
only immeadiate children are returned. If arguments are specified, the
list is filtered to contain only children with __tag__ in tags,  and
self.attrib(key)==value for every key in attribs. if "tags" is a string,
it is converted to [tags]. If attribs is a string, it is converted to
{"Name":attribs}. If "heads" is true, the search does not descend below a 
match (e.g. no children of a matching element will be returned.'''
		if type(tags)==type(" ") or type(tags)==type(u" "):
			tags = [tags]
		if type(attribs)==type(" ") or type(attribs)==type(u" "):
			attribs = {"Name":attribs}
		return get_all_children(self, tags, attribs, depth, heads)


	def getSibling(self, tags, attrs):
		'''nearest match to getElement with the same arguments'''
		e = self
		while e.container:
			e=e.container
			elems = e.getElements(tags, attrs, -1)
			if len(elems)>0:
				if len(elems)==1:
					return elems[0]
				else:
					raise StandardError("This is not a unique ID")
		raise StandardError("Could not find referenced instance") 

	def getParent(self, tag):
		'''tag (st)=> instance
returns the lowest order parent that is of type "tag". A matching
parent will be returned and end the search, but if the parent doesnt
match the grandparent will be tested, etc. If no member of the
parent tree matches tag, raise a StandardError. This method will
_not_ find siblings.'''
		e = self
		while e.container:
			e=e.container
			if e.__tag__==tag:
				return e
		raise StandardError("Could not find referenced instance") 

	def xpath(self, inst=False):
		''' inst (Bool=False) => list or string
		Returns the xml path to this element. If inst is true,
		the return value is a list containing instance references
		to the instances on the path (begining with the document root
		and ending with self). If inst is false (default) the return
		is an xpath string'''
		p = [self]
		e = self.container
		while e:
			p = [e]+p
			e = e.container
		if inst:
			return p
		else:
			path = "/"
			for e in p:
				path+=e.__tag__+"/"
			if self.container and not self.elements:
				path = path[:-1]	
			return path

	def pathSearch(self, s):
		''' s (string) => list
		returns a list (possibly empty) of instances matching
		the xpath specified in s. If s begins with a / the search
		is performed from the document root. Otherwise it is performed
		relative to this element'''
		if s.startswith("/"):
			if self.container:
				e = self
				while e.container:
					e = e.container
				return e.pathSearch(s)
			else:
				s = s[1:]
				if s. endswith("/"):
					s = s[:-1]
				s = s.split("/")
				if s[0]!=self.__tag__:
					return []
				else:
					s = s[1:]
		else:		
			if s. endswith("/"):
				s = s[:-1]
			s = s.split("/")
		match = [self]
		while s:
			ct = s.pop(0)
			m = []
			for e in match:
				m.extend(e.getElements(ct, {}, 1))
			if not m:
				return []
			match = m
		return match	
	
	def tagScan(self, depth=1, atdepth=0, indent=True, maxlist=6):
		'''returns a recursive list of elements, including self, to the
specified depth. (set depth to a negative integer to scan to unlimited depth)'''
		info=[]
		if indent:
			ws="  "*atdepth
		else:
			ws=""
		info.append(ws+str(self))
		if depth>0 and atdepth>=depth:
			return info
		kids=self.getElements([],{},1)
		ktags={}
		for k in kids:
			t=k.__tag__
			if not ktags.has_key(t):
				ktags[t]=[]
			ktags[t].append(k)
		ktk=ktags.keys()
		ktk.sort()
		for k in ktk:
			if len(ktags[k])>maxlist:
				info.append(ws+"  %i %s" % (len(ktags[k]), k))
			else:
				for el in ktags[k]:
					info.extend(el.tagScan(depth, atdepth+1, indent, maxlist))
		return info			

	def getInstance(self, xpath):
		'''xpath (string) => instance
		return the instance with the specified xpath,
		or raise an exception if it cant be found. As with pathSearch,
		paths beginning with / are treated as absolute, others are relative'''
		s = xpath
		if s.startswith("/"):
			if self.container:
				e = self
				while e.container:
					e = e.container
				return e.getInstance(s)
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
			try:
				match = [x for x in match.elements if x.__tag__==ct][0]
			except:
				raise StandardError("No element with xpath %s" % xpath) 
		return match	

	def report(self, s):
		'''s (str) => None
prints s. Overloaded by gui classes to redirect output'''
		if self._owner:
			self._owner.report(s)
		elif self.container:
			self.container.report(s)
		else:	
			print s

	def getCdata(self):
		'''returns a string containing cdata.'''
		return self.cdata
		
	def setCdata(self, s):
		'''sets self.cdata to s'''
		self.cdata=s.strip()
		
	def getAttributes(self):
		'''return a copy of the attribute dictionary'''
		a={}
		a.update(self.attributes)
		return a

	def getTree(self, recurse=-1):
		'''return a dictionary representation of self (in the same
form used by __init__ and the methods is xmlhandler). if recurse is a 
possitive integer, limit the representation of child elements to the 
specified depth'''
		d={'tag':self.__tag__, 'attributes':self.getAttributes(),
			'cdata':self.getCdata(), 'elements':[]}
		if recurse!=0:
			for e in self.elements:
				cd=e.getTree(recurse-1)
				d['elements'].append(cd)
		return d		

	def clone(self, recurse=True):
		'''Return a deep copy of self. If recurse is true, clone all
child elements as well'''
		node=self.getTree(recurse=0)
		q=self.__class__(node)
		if recurse:
			for e in self.elements:
				q.newElement(e.clone())
		return q


	def onLoad(self):
		'''recursive update function that should be called on the toplevel
instance after loading (from a disk file or stream)'''
		for e in self.elements:
			e.onLoad()
			
	def onSave(self, fn):
		'''recursive update function that should be called on the toplevel
instance after loading (from a disk file or stream)'''
		for e in self.elements:
			e.onSave(fn)
	
