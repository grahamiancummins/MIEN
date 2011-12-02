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

from __future__ import unicode_literals
import numpy as N
from mien.nmpml.basic_tools import NmpmlObject

FLOAT_TYPES=[float, complex, N.float32, N.float64, N.complex64, N.complex128]
try:
	FLOAT_TYPES.extend([N.float128, N.complex256])
except AttributeError:
	#win 32 is too dmub to provide 128 bit numbers
	pass
INT_TYPES = [int, long, N.int8, N.uint8, N.int16, N.uint16, N.int32, N.uint32, N.int64, N.uint64]
STR_TYPES = [str, unicode] 
BOOL_TYPES=[bool, N.bool]
SEQ_TYPES=[list, tuple, N.ndarray]
NUM_TYPES = FLOAT_TYPES+INT_TYPES

TAG_RENAME={
	"AbstractModel":"ToolChain",
	"MienBlock":"Function"	
}


def cast2str(d):
	if type(d) in NUM_TYPES:
		return "%0.30g" % (d,)
	elif type(d) in SEQ_TYPES:
		return "|".join(map(cast2str, d))
	else:
		return str(d)
		
def cast2py(s):
	if "|" in s:
		return map(cast2py, s.split("|"))
	try:
		return int(s)
	except ValueError:
		try:
			return float(s)
		except ValueError:
			return s	

def make_nested(secs):
	root =None
	new={}
	for s in secs:
		ns=NmpmlObject({'tag':"Cell", 'attributes':s.attributes, 'elements':[], 'cdata':None})
		ns.data = s.getPoints()
		for e in s.elements:
			ns.newElement(e)
		if not s.parent():
			root = ns
		new[s.name()]=ns	
	for name in new:
		s = new[name]
		if s == root:
			continue
		p = s.attrib("Parent")
		del(s.attributes["Parent"])
		s.move(new[p])
	return root

def convert_tag(obj):
	if obj.__tag__ == "Fiducial":
		obj.__tag__ = "Fiducial"+obj.attrib("Style").title()
		obj.data = obj.getPoints()
		if obj.attrib("Style") in ["points", "line"]:
			obj.data = obj.data[:,:3]
		if obj.point_labels:
			obj.setAttrib("labels", obj.get_point_labels())
	elif obj.__tag__ == "Cell":
		if obj.container.__tag__=="Cell":
			return
		rs = obj.getSection(obj.root())
		allsecs = obj.getElements("Section")
		for atr in rs.attributes:
			if not atr in ['Name', "Parent"]:
				obj.attributes[atr]=rs.attributes[atr]
		for el in rs.elements:
			obj.newElement(el)
		obj.data = rs.getPoints()	
		obj.elements=[e for e in obj.elements if not e.__tag__=="Section"]
		nest = make_nested(allsecs)
		for e in nest.elements:
			obj.newElement(e)
	elif obj.__tag__ == "Parameters":
		obj.attributes.update(obj.getValue('dict'))
		for e in obj.elements[:]:
			e.sever()
		obj.data = None	
	elif obj.__tag__ == "Data":
		obj.getData()
		obj.__tag__ = obj.stype()		
	else:
		if obj.__tag__ in TAG_RENAME:
			obj.__tag__ = TAG_RENAME[obj.__tag__]
		if obj.cdata:
			obj.data = cast2str(obj.cdata)
		else:
			obj.data = None

def unique_names(obj):
	names = []
	for e in obj.elements:
		if e.name() in names:
			e.setName("%s_%s" % (e.name(), e.__tag__))
		names.append(e.name())


def convert2gdform(obj):
	convert_tag(obj)
	unique_names(obj)
	for e in obj.elements:
		convert2gdform(e)
		
	

def npath(obj):
	p=[e.name() for e in obj.xpath(1)[1:]]
	p="/"+"/".join(p)
	return p


def serialize(obj):
	l=[]
	for atr in sorted(obj.attributes):
		if atr=="Name":
			continue
		l.append(atr+"|"+cast2str(obj.attrib(atr))+"\n")
	if obj.data!=None:
		if type(obj.data) == N.ndarray:
			l.append("data|%s|%s\n" % (obj.data.dtype.str, "|".join(map(str, obj.data.shape))))
			l.append(obj.data.tostring())
		elif type(obj.data) in STR_TYPES:
			l.append("data|str|%i\n" % (len(obj.data)))
			l.append(obj.data)
		else:
			print("WARNING:unexpected data type")
	l.append("\n")
	return l
	
def writeObj(f, obj):
	l=serialize(obj)
	size = N.add.reduce(map(len, l))
	f.write("%s|%s|%i\n" % (npath(obj), obj.__tag__, size))
	for s in l:
		f.write(s)
	for e in obj.elements:
		writeObj(f, e)	

def write(f, doc, **kwargs):
	doc = doc.clone()
	convert2gdform(doc)
	for e in doc.elements:
		writeObj(f, e)

		
		
def read(f, **kwargs):
	els = 1		
		

def scangic(f):
	d={}
	f.seek(0)
	while 1:
		l = f.readline()
		try:
			name, tag, size = l.split("|")
		except:
			return d
		loc=f.tell()
		d[name]=(loc, int(size), tag)
		f.seek(int(size), 1)
		
filetypes={}
filetypes['gicdat']={'notes':'Proposed as the native format for gicdat (aka mien 2). Can handle any object type. Slightly slower than mdat or mien for old style models, particularly cells',
							'read':read,
							'write':write,
							'data type':'any',
				'elements':'all',
				'extensions':['.gic']}
				
if __name__=="__main__":
	import sys
	d=scangic(open(sys.argv[1], 'rb'))
	print d
					