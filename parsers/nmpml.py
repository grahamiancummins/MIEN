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

'''Parser module for reading NMPML type XML files (the native dialect of MIEN). This module creates a dictionary "elements" that maps all supported nmpml tags onto the python classes that implement their behaivior. It also also provides several functions for creating new python objects of type NmpmlObject.'''

from time import strftime
import os, sys, copy
import mien.xml.xmlhandler
import cPickle
import StringIO
from mien.nmpml import __all__ as nmpmlmods 

style = {}
elements = {}

def datestamp():
	return strftime("%H:%M %b %d, %Y")

for m in nmpmlmods:
	try:
		exec("import mien.nmpml.%s as mod" % m)	
		elements.update(mod.ELEMENTS)
	except:
		print 'Seem to be working offline.  Beware.'
import mien.blocks
elements.update(mien.blocks.getBlock('NMPML'))

def tagClasses():
	'''Return a dictionary of strings onto lists of strings. The keys are names of base classes from which Nmpml subclasses are derived (e.g. PointContainer). The strings composing the values are the names of classes derived from them. If tags have the same names as their associated classes (as they should), then the idiom foo.getElements(tagClasses('Bar')) will return all subelements of Nmpml object foo that are of types derived from class Bar (e.g. foo.getElements(tagClasses('PointContainer')) will return all Sections and Fiducials.'''
	nmpb=elements['Nmpml']
	cl={}
	for c in elements.values():
		if c==nmpb:
			continue
		pc=c.__bases__[0]
		if pc==nmpb:
			continue
		pcn=pc.__name__	
		if not cl.has_key(pcn):
			cl[pcn]=[]
		cl[pcn].append(c.__name__)
	return cl	
		


def fromString(xml, dat=None):
	'''Read xml in the string type input "xml" and return an NmpmlObject. If dat is specified, it should be a Pickle string containing a serialized data archive, which will be used to assign data to Data tags in the xml'''
	xml=StringIO.StringIO(xml)
	o=mien.xml.xmlhandler.readXML(xml, elements)
	if dat:
		datstruct = cPickle.loads(dat)
		for k in datstruct:
			try:
				d = o.getInstance(k)
				d.datinit(datstruct[k]['data'], datstruct[k]['header'])
			except:
				print "Warning could not load %s" % k
	return o

def createElement(tag, attrs, cdata=''):
	'''Return an NmpmlObject subclass of type "tag" with the specified attributes and cdata set.'''
	node={'tag':tag, 'attributes':attrs, 'elements':[], 'cdata':cdata}
	cl=	elements.get(tag, elements['default class'])
	return cl(node)
	
def forceGetPath(doc, path):
	'''Returns the instance within doc with upath path. If there is no such instance, creates it, recursively if needed'''
	if not path or path=='/':
		return doc
	e=doc.getInstance(path, True)
	if e:
		return e
	path=path.split('/')
	if len(path)==1:
		local=path
		path=''
	else:	
		local=path[-1]
		path="/".join(path[:-1])
	parent=forceGetPath(doc, path)
	tag, name= local.split(':')
	local=createElement(tag, {'Name':name})
	parent.newElement(local)
	return local
	
def addPath(doc, path, replace=False):
	'''Adds an element with upath "path". If there is already such an element, and replace is False (default), increments the name associated with path until it is unique, thus preserving the existing element. If replace is True, the existing element is severed, and a new element of the same type and name is created in its place. Return value is the new element instance.'''
	e=doc.getInstance(path, True)
	if not e:
		return forceGetPath(doc, path)
	if replace:
		e.sever()
		return forceGetPath(doc, path)
	
	path=path.split('/')
	tag, name = path[-1].split(':')
	if len(path)==1 or not path[0]:
		par=doc
	else:
		par=forceGetPath(doc, "/".join(path[:-1]))	
	el=createElement(tag, {'Name':name})
	par.newElement(el)	
	return el
	
		

def blankDocument():
	'''Return an NmpmlObject of type Nmpml (toplevel document). The document will contain a Comment child noting the date and time of creation, but is otherwise empty.'''
	document = createElement("Nmpml", {'Name':'0'})
	#document.addComment("Created on %s" % datestamp())
	return document

def wrapInDocument(els):
	doc=blankDocument()
	for e in els:
		doc.newElement(e)
	return doc	

def nameFromFile(f):
	if not type(f) in [str, unicode]:
		try:
			f="file://%s" % (f.name,)
		except:
			try:
				f=f.geturl()
			except:
				f="UnknownSource"
	fn=os.path.split(f)[-1]
	fn=os.path.splitext(fn)[0]			
	attr={'Name':fn}
	return attr

filetypes={}
filetypes['nmpml']={'notes':"Mien's native format",
					'read':True,
					'write':True,
					'data type':'any',
					'elements':elements.keys(),
					'xml dialect':elements,
					'extensions':['.nmpml']}
