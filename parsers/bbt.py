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
from mien.parsers.nmpml import createElement
from mien.math.array import eucd
import re, os

BBT_DATALINE =re.compile(r"\s*\d+\s+(\w)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+")

def killzeros(cell):
	'''delete sections with zero length'''
	sections = filter(lambda x:x.__tag__=="Section", cell.elements)
	for s in sections:
		stats = s.stats()
		if stats[0] == 0:
			n=str(s)
			del(s)
			print "Removed 0 length section %s" % n
			
def readBBT(fileobj, **kwargs):
	fname=kwargs['parsed_url'][2]
	header = []
	comment=0
	branches=[]
	varic=[]
	fiducial_list=[]
	term=1
	branch=0
	fiducial=0
	varicosity=0
	lineno=0
	cname = os.path.split(fname)[-1]
	cname = re.sub(r"\.[^.]*$", "", cname)
	cname = re.sub(r"\W", "_", cname)
	cell = createElement("Cell", {"Name":cname})
	cell.addComment("Imported from bbt file %s" % fname)
	for line in fileobj.readlines():
		lineno+=1		
		if comment:
			e=line.find("*/")
			if e==-1:
				header.append(line)
				continue
			else:
				header.append(line[:e])
				line=line[e+2:]
				comment=0
		elif line.find("/*")!=-1:
			if line.find("*/")!=-1:
				header.append(line[line.find("/*")+2:line.find("*/")])
				line=line[:line.find("/*")]+line[line.find("*/")+2:]
			else:
				comment=1
				header.append(line[line.find("/*")+2:])
				line=line[:line.find("/*")]
		
		m=BBT_DATALINE.match(line)
		if m:
			type=m.group(1)
			point=tuple(map(float, m.groups()[1:])) 
			if type=="V":
				varic.append(point)
				if not varicosity:
					varicosity=point
			elif varicosity and type=="T":
				varic.append(point)
				point=varicosity
				varicosity=0
			else:
				varicosity=0	
			if type=="F":
				if len(fiducial_list)==0:
					fiducial_list.append([])
				fiducial_list[-1].append(point)	
				fiducial=1
				
				continue
			elif type=="f":
				fiducial_list.append([])
				
				if fiducial:
					fiducial_list[-2].append(point)
				elif varicosity:
					varic.append(point)
					fiducial=1
						
				else:
					fiducial=1
					type="T"
			elif type=="c":
				if fiducial:
					fiducial_list[-1].append(point)
					fiducial=0
					type="F"
					continue
			elif term and fiducial and type in ['t', 'T']:
				fiducial=0
				fiducial_list[-1].append(point)
				continue
			else:
				fiducial=0
			if type=="b":
				type=="C"
			type=type.lower()
			
			if not type in ["c", "t", "b", "s"]:
				continue
			if term:
				term=0
				if branches:
					pid = branches.pop()
					parent="section[%i]" % pid
				else:
	
					if not cell.getElements("Section"):
						pid = None
						parent="None"
					else:
						print "WARN: unattached branch at %i" % lineno
						pid=1
						name="section[1]"
				name="section[%i]" % len(cell.elements)				
				sec=createElement('Section', {"Name":name, "Parent":parent})
				cell.newElement(sec)
				if pid!=None:
					sec.setPoints(cell.elements[pid].points[-1], append=1)
			if branch:
				branch=0
				parent="section[%i]" % (len(cell.elements)-1,)
				name="section[%i]" % len(cell.elements)
				branches.append(len(cell.elements)-1)
				pp=cell.elements[-1].points[-1]
				sec=createElement('Section', {'Name': name, 'Parent':parent})
				cell.newElement(sec)
				sec.setPoints(pp, append=1)
			if type=="b":
				branch=1
			if type=="t":
				term=1
			cell.elements[-1].setPoints(point, append=1)
	killzeros(cell)
	
	out = [cell]
	if fiducial_list:
		i=0
		for sl in fiducial_list:
			if not sl:
				continue
			try:
				f = createElement('Fiducial',{"Style":"line",
													 "Name":"%s_%s_%i" % (cname, 'fiducial', i)})
													 
				f.setPoints(sl)
			except:
				print sl
				raise
			i+=1
			out.append(f)
	if varic:
		v = createElement('Fiducial', {"Style":"spheres",
												 "Name":"%s_varicosities" % cname})
		v.setPoints(varic)
		out.append(v)
	header = map(lambda x: x.strip(), header)
	n = createElement("Nmpml", {"Name":"Doc"})
	for o in out:
		n.newElement(o)
	return n	


filetypes={}
filetypes['bbt']={'notes':'Nevin Binary tree format',
					'read':readBBT,
					'write':None,
					'data type':'anatomy',
					'elements': ["Cell", "Fiducial"],
					'extensions':['', '.bbt'],
					"extension patterns":[r"[123456789]\d+"]}




WRITEABLE_OBJECTS =[]




# 
# 
# def correctBBT(file):
# 	lines=open(file).readlines()
# 	n,b,t,s, lcb=readbbt(lines)
# 	print "found %i 'b's" % lcb
# 	minskew=s
# 	print "skew is %f" % minskew
# 	if t==b+1:
# 		print "file OK"
# 		return
# 	else:
# 		print "file contains %i missing terminations (or extra branches)" % (b-t+1)
# 	location=0
# 	for i in range(len(lines)):
# 		testlines=lines[:]
# 		spl= testlines[i].split()
# 		if len(spl)<6:
# 			continue
# 		if spl[1].lower()=="b":
# 			spl[1]="C"
# 			testlines[i]=join(spl)
# 		elif spl[1].lower()=="c":
# 			spl[1]="T"
# 			testlines[i]=join(spl)
# 		else:
# 			continue
# 		n,b,t,s, lcb=readbbt(testlines)
# 		if s<minskew:
# 			location=i
# 			minskew=s
# 		if i%50==0:
# 			print "at line %i, got %f by changing %i" % (i, minskew, location)
# 	print "minimal skew of %f obtained by modifying line %i" % (minskew,location) 
# 		
# 	
# correctBBT(sys.argv[1])
# sys.exit()
# 
# ################################################################
# x=model.Neuron(sys.argv[1])
# x.write("test.hoc")
# 
# l=[]
# for n in x.names:
# 	for i in range(len(x.names[n])):
# 		if len(x[(n,i)]['children'])%2!=0:
# 			cs=[]
# 			for c in x[(n,i)]['children']:
# 				cs.append(x.ptsinsec[c][0])
# 						 
# 			l.append([len(x[(n,i)]['children']), x.ptsinsec[(n,i)][0], x.ptsinsec[(n,i)][-1]]+cs)
# 
# for i in l:
# 	print join(map(str, i))
# 
# 
# length=[]
# type=[]
# for l in open(sys.argv[1]).readlines():
# 	t, x = l.split()[1:3]
# 	type.append(t)
# 	length.append(float(x))
# 
# length=array(length)
# offset=take(length, arange(1,len(length)))
# length=take(length, arange(len(length)-1))
# offset=offset-length
# avoff=sum(offset)/len(offset)
# 
# maxslip=[0,0]
# for i in range(len(offset)):
# 	x=offset[i]
# 	if x>maxslip[0]:
# 		if type[i]!="T":
# 			maxslip[0]=x
# 			maxslip[1]=i
# 
# 







