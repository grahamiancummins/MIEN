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

from tokenizer import Tokenizer, WHITESPACE
import mien.nmpml
from mien.math.array import alltrue
import re
import os



HOC_TOKENS = {"(":{},
			  ")":{},
			  "{":{},
			  "}":{},
			  "/*":{"readto":"*/"},
			  "//":{"readto":"\n"},
			  '"':{"readto":'"'},
			  '=':{"return":1},
			  "\n":{},
			  ",":{}}

HOC_TOKENS.update(WHITESPACE)


def getNameIndex(s):
	if s.find("[")==-1:
		return (s, None)
	else:
		n = s[:s.find("[")]
		i = int(s[s.find("[")+1:s.find("]")])
		return (n,i)


class HocReader:
	'''class fr reading Hoc files
Currently reads only connectivity and pt3dadd morphology'''
	def __init__(self, fobj, name):
		self.fname = name
		self.toke =  Tokenizer(fobj, HOC_TOKENS)
	

	def read(self):
		cname = re.sub(r"\.[^.]*$", "", self.fname)
		cname = re.sub(r"\W", "_", cname)
		cell = mien.nmpml.elements['Cell'](attribs={"Name":cname})
		cell.addComment("Imported from hoc file %s" % self.fname)
		self.current_section = None
		secnames = []
		srefs ={}
		while 1:
			t = self.toke.next()
			if t=="EOF":
				break
			if t.startswith("/*"):
				cell.addComment(t[2:-2])
			elif t.startswith("//"):
				cell.addComment(t[2:])
			elif t=="create":
				t = self.toke.next()
				n,i = getNameIndex(t)
				secnames.append(n)
				regl = []
				for s in range(i):
					sec = mien.nmpml.elements["Section"](attribs={'Name':"%s[%i]" % (n,s),
										   'Parent':"None"}, container=cell)
					regl.append(sec.name())
					srefs[sec.name()]=sec
					cell.elements.append(sec)
			elif t=="connect":
				first = self.toke.next()
				first = srefs[first]
				floc = float(self.toke.next())
				second = self.toke.next()
				if getNameIndex(second)[0] in secnames:
					sloc = float(self.toke.next())
					second = srefs[second]
				else:
					sloc = float(second)
					second = self.current_section
				if floc>sloc:
					floc, sloc = slco, floc
					second, first = first, second
				first.attributes["Parent"]=second.name()
			elif getNameIndex(t)[0] in secnames:
				self.current_section = srefs[t]
			elif not self.current_section:
				continue
			else:
				if t == "pt3dadd":
					pt = []
					for i in range(4):
						pt.append(float(self.toke.next()))
					self.current_section.setPoints(pt, 1)	
				else:
					#print t
					pass
		return cell		
	
def hoc2cell(fobj):
	try:
		fname=fobj.name
	except:
		try:
			fname=fobj.geturl()
		except:
			fname='unknown'
	rdr = HocReader(fobj, fname)
	cell=rdr.read()
	cell.refresh()
	return cell

def cell2hoc(of, cell):
	of.write("/* written by nmpml translation system\n")
	of.write("*/\n\n")
	cell.writeHoc(of)
	of.close()
	
def readHoc(fname, **kwargs):
	#note, fname is not a name, its a file object now!
	c = hoc2cell(fname)
	n = mien.nmpml.elements["NmpmlDocument"](attribs={"Name":"Doc"}, tag="NmpmlDocument")
	n.newElement(c)
	return n
	
def writeHoc(fileobj, doc, **kwargs):
	cells = doc.getElements("Cell")
	if len(cells)==1:
		cell2hoc(fileobj, cells[0])
	else:
		if not type(fileobj)==file:	
			raise IOError('writing cells to hoc at once is only supported for local files')
		fname=fileobj.name
		fileobj.close()
		fname=kwargs['parsed_url'][2]
		base, ext = os.path.splitext(fname)
		for i in range(len(cells)):
			fn = base+str(i)+ext
			fobj=file(fn, 'wb')
			cell2hoc(fobj, cells[i])


filetypes={}
filetypes['hoc']={'notes':'Neuron format. Only reads a small subset of hoc code',
					'read':readHoc,
					'write':writeHoc,
					'data type':'anatomy, physiology',
					'elements': ["Cell"],
					'extensions':['.hoc']}


			
