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

from tokenizer import Tokenizer
from mien.parsers.nmpml import createElement
from mien.math.array import all
import os

NL_TOKENS = {"(":{"return":1},
			 ")":{"return":1},
			 ";":{"readto":"\n"},
			 '"':{"readto":'"'},
			 '|':{"return":1},
			 "\n":{},
			 ",":{}}
			 
class NLReader:
	'''Class for reading neurolucida files'''
	def __init__(self, f=None):
		if f:
			self.read(f)

	def read(self, f):
		try:
			filename=f.name
		except:
			try:
				filename=f.geturl()
			except:
				filename='unknown'
		self.filename=filename
		self.object_list=[]
		self.comment_list=[]
		self.current_object=None
		self.depth=0
		self.toke =  Tokenizer(f, NL_TOKENS)
		self.waiting = None
		self.accumulate=None
		self.cellnames=[]
		while 1:
			t = self.toke.next()
			if t=="EOF":
				break
			elif self.depth==0:
				if t[0]==";" and len(self.object_list)==0:
					self.comment_list.append(t[1:].strip())
				elif t[0]=="(":
					self.current_object={'sections':[], 'current_section':[],
										 'parents':{}, 'attribs':{}, 'csd':1}
					self.depth+=1
			else:
				if t[0]==";":
					continue
				elif t=="(":
					self.increase_depth()
				elif t==")":
					self.decrease_depth()
				elif t=="|":
					self.close_section()
				elif t[0]=='"':
					if not t[-1] =='"':
						raise StandardError("Unmatched Quotes")
					self.handle_string(t[1:-1])
				else:
					try:
						t=int(t)
						self.handle_number(t)
					except:
						try:
							t=float(t)
							self.handle_number(t)
						except ValueError:
							self.handle_word(t)
					
					

	def increase_depth(self):
		self.depth+=1
		self.accumulate=[]

	def handle_string(self, s):
		if self.depth==1:
			self.current_object["attribs"]["Name"]=s
		elif self.waiting:
			self.current_object["attribs"][self.waiting]=s
			self.waiting = None	
			
	def handle_word(self, s):
		self.accumulate=None
		if not self.current_object:
			return
		if s in ["Color", "Resolution", "Name", "RGB", "Font"]:
			self.waiting = s
		elif s in ["Incomplete", "Axon"]:
			self.current_object["attribs"][s]=1
		elif self.waiting:
			self.current_object["attribs"][self.waiting]=s
			self.waiting=None
		elif self.depth==1:
			self.current_object["attribs"]["MarkerType"]=s
		elif self.depth==2 and not self.current_object["attribs"].get("Name"):
			self.current_object["attribs"]["Name"]=s

			
	def handle_number(self, s):
		if self.waiting and  self.waiting!="RGB":
			self.current_object["attribs"][self.waiting]="%.4s" % s
			self.waiting = None
		elif self.accumulate!=None:
			self.accumulate.append(s)

	def close_section(self):
		if not self.current_object["current_section"]:
			self.current_object["current_section"]=[]
			self.current_object["csd"]=self.depth
			return
		if self.current_object["csd"]==1:
			parent="None"
		else:
			try:
				parent = self.current_object["parents"][self.current_object["csd"]]
				firstpoint = self.current_object["sections"][parent][1][-1]
				self.current_object["current_section"] = [firstpoint]+ self.current_object["current_section"]
			except:
				print self.current_object
				raise
		self.current_object["sections"].append((parent, self.current_object["current_section"]))
		self.current_object["current_section"]=[]
		self.current_object["csd"]=self.depth

	def decrease_depth(self):
		self.depth-=1
		if self.depth<self.current_object["csd"]:
			self.close_section()
			if self.depth==0:
				self.make_object()
		elif self.accumulate:
			point  = self.accumulate[:]
			if self.waiting =="RGB":
				point = "RGB "+str(tuple(map(int, point)))
				self.current_object['attribs']["Color"]=point
				self.waiting = None
			else:
				if self.depth ==  self.current_object["csd"]:
					self.current_object["current_section"].append(point)
				else:
					self.close_section()
					self.current_object["parents"][self.depth]=len(self.current_object["sections"])-1
					self.current_object["current_section"].append(point)
		self.accumulate = None	
			
	def make_object(self):
		cobj = self.current_object
		if len(cobj["sections"])==0:
			#print "Object %s contains no points. Ignoring it" % str(cobj["attribs"])
			pass
		else:
			attribs = cobj["attribs"]
			if len(cobj['sections'])==1 and not attribs.get('Axon'):
				if attribs.has_key("Resolution"):
					attribs["Style"] = "line"
				else:
					attribs["Style"] = "points"
				obj = createElement("Fiducial", attribs) 
				obj.setPoints(cobj["sections"][0][1])
				obj.addComment("Imported from Neurolucida file %s" % self.filename)
				#print "Loaded Fiducial object %s" % attribs["Name"]
			else:
				if len(cobj['sections'])==1 and len(cobj["sections"][0][1]) <3:
					print("WARNING: Found an 'Axon' with < 3 points. Assuming this is a mistake and discarding it.")
					return
				n = attribs.get("Name", "Cell")
				attribs["Name"]=n
				if n in self.cellnames:
					i=2
					tn = "%s_%i" % (n, i)
					while tn in self.cellnames:
						i+=1
						tn = "%s_%i" % (n, i)
					attribs["Name"]=tn
				self.cellnames.append(n)
				obj = createElement("Cell", attribs)
				obj.addComment("Imported from Neurolucida file %s" % self.filename)
				for s in range(len(cobj["sections"])):
					n= "section[%i]" % s
					sec = cobj["sections"][s]
					if sec[0]=='None':
						p="None"
					else:
						p = "section[%i]" % sec[0]
					s = createElement("Section", {"Name":n, "Parent":p})
					s.setPoints(sec[1])
					obj.newElement(s)
				#print "Loaded Cell object %s" % attribs["Name"]
			self.current_object = None
			self.object_list.append(obj)

def readNL(f, **kwargs):
	nlr = NLReader(f)
	objlist=[]
	singlepoint=[]
	for o in nlr.object_list:
		if o.__tag__=="Fiducial" and o.attrib("Style")=="points":
			if o.points.shape[0]==1:
				singlepoint.append(o)
				continue
			d = o.getPoints()[:,3]
			if not all(d == d[0]):
				o.attributes["Style"]="spheres"
		objlist.append(o)
	if singlepoint:
		f = createElement("Fiducial", singlepoint[0].attributes)
		for o in singlepoint:
			p = o.points[0]
			n = o.name()
			f.setPoints(p, append=1)
			i = len(f.points)-1
			f.point_labels[i]=n
		objlist.append(f)
	n = createElement("Nmpml", {"Name":"Doc"})
	for o in objlist:
		n.newElement(o)
	return n


def sortSections(s, s2):
	return cmp(str(s), str(s2))

def write_section(sec, depth, file):
	indent = "  "*depth
	points =  sec.points
	if depth>1:
		points =points[1:]
	for point in points:
		file.write(indent+"( %.2f %.2f %.2f %.2f)\n" % tuple(point))
	c = sec.container.getChildren(sec.name())
	if c:
		c.sort(sortSections)
		file.write(indent+"(\n")
		for n in c:
			ns =  sec.container.getSection(n)
			write_section(ns, depth+1, file)
			if n!=c[-1]:
				file.write(indent+"|\n")
		file.write(indent+")\n")
				
def cell2NL(cell, file):
	if cell.attributes.has_key("Color"):
		color = cell.attributes["Color"]
	else:
		color = "Blue"
  	file.write('\n( (Color %s)\n' % color)
  	file.write('  (Axon)\n')
	sec = cell.getSection(cell.root())
	write_section(sec, 1, file)
	file.write(")\n")

def fiducialPoints2NL(fed, file):
	desc = fed.attributes["Name"]
	if fed.attributes.has_key("Color"):
		color = fed.attributes["Color"]
	else:
		color = "Blue"
	if fed.attributes.has_key("MarkerType"):
		mtype = fed.attributes["MarkerType"]
	else:
		mtype = "OpenCircle"
	header = '\n(%s\n' % mtype
	header+='  (Color %s)\n' % color
	if not fed.point_labels:
		header+='  (Name "%s")\n' % desc
		file.write(header)
		for p in fed.points:
			if len(p)==3:
				p = list(p)+[1.0]
			file.write("  ( %.2f %.2f %.2f %.2f)\n" % tuple(p))
		file.write(")\n")
	else:
		for i in fed.point_labels.keys():
			h = header+'  (Name "%s")\n' %fed.point_labels[i]
			file.write(h)
			p = fed.points[i]
			if len(p)==3:
				p = list(p)+[1.0]
			file.write("  ( %.2f %.2f %.2f %.2f)\n" % tuple(p))
			file.write(")\n")
				
			

def fiducialLine2NL(fed, file):
	desc = fed.attributes["Name"]
	file.write("\n")
	file.write('("%s"\n' % desc)
	res = .1
	if fed.attributes.has_key("Color"):
		color = fed.attributes["Color"]
	else:
		color = "Blue"
	if fed.attributes.has_key("Resolution"):
		res = fed.attributes["Resolution"]
	else:
		res = "0.1"
	file.write("  (Color %s)\n" % color)
	file.write("  (Resolution %s)\n" % res)
	for p in fed.points:
		if len(p)==3:
			p = list(p)+[.1]
		file.write("  ( %.2f %.2f %.2f %.2f)\n" % tuple(p))
	file.write(")\n")

def writeNL(s, doc, **kwargs):
	'''filename objectlist headerlist. write neurolucida .asc files'''
	s.write("; written by nmpml translation system\n")
	s.write("\n(Sections)\n")
	for o in doc.elements:
		if o.__tag__=="Cell":
			#print "Writing Cell Object %s" % str(o)
			cell2NL(o, s)
		elif o.__tag__=="Fiducial":
			if o.attributes["Style"] == "line": 
				#print "Writing Fiducial Line %s" % str(o)
				fiducialLine2NL(o, s)
			if o.attributes	["Style"] == "points": 
				#print "Writing Point List %s" % str(o)
				fiducialPoints2NL(o, s)
			if o.attributes	["Style"] == "spheres":
				#print "Writing Point List %s" % str(o)
				fiducialPoints2NL(o, s)
				
		else:
			print "No NL filter for object type %s. Ignoring object." % o.__tag__

filetypes={}
filetypes['asc']={'notes':'Neuroleucida format',
					'read':readNL,
					'write':writeNL,
					'data type':'anatomy',
					'elements': ["Cell", "Fiducial"],
					'extensions':['.asc']}


