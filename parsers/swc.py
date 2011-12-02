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
import mien.parsers.nmpml
from mien.math.array import array, eucd, zeros, float32, sqrt, vstack
import re, os

DATALINE =re.compile(r"\s*(\d+)\s+(\d+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d]+)")

def finishSection(accum, par, cell, points, regions):
	pts=zeros((len(accum),4), float32)
	reg={}
	if len(accum)<2:
		name="s%s" % (accum[0],)	
	else:
		name="s%s_%s" % (accum[0], accum[-1])
	for i, pid in enumerate(accum):
		pts[i]=points[pid]
		rp=regions[pid]
		if not reg.has_key(rp):
			reg[rp]=1
		else:
			reg[rp]+=1
	if len(reg.keys())==1:
		reg=reg.keys()[0]
	else:
		ar=reg.keys()
		ar, rest=ar[0], ar[1:]
		nr=reg[ar]
		for k in rest:
			if reg[k]>nr:
				nr=reg[k]
				ar=k

		print "Neuron-style section %s contains points assigned to several regions (%s). Using %s (which contains the most points)" % (name, str(reg.keys()),ar) 
		reg=ar
	if par:
		try:
			ppt=cell.getSection(par).getPoints()[-1]
		except:
			print [s.name() for s in cell.getElements('Section')]
			print cell._sections
			raise
		pts=vstack([ppt, pts])
	if not par:
		par="None"
	s=mien.parsers.nmpml.createElement('Section', {"Name":name, "Parent":par})
	cell.newElement(s)
	s.setPoints(pts)
	return (name, reg)

def buildSections(pt, par, cell, points, children, regions, sregions, accum):
	accum.append(pt)
	kids=children.get(pt, [])
	if len(kids)==1:
		buildSections(kids[0], par, cell, points, children, regions, sregions, accum)
	else:
		name, reg=finishSection(accum, par, cell, points, regions)
		if not sregions.has_key(reg):
			sregions[reg]=[]
		sregions[reg].append(name)
		for k in kids:
			buildSections(k, name, cell, points, children, regions, sregions, [])

def read(f, **kwargs):
	points={}
	children={}
	regions={}
	sregions={}
	fname=kwargs['parsed_url'][2]
	cname = os.path.split(fname)[-1]
	cname = re.sub(r"\.[^.]*$", "", cname)
	cname = re.sub(r"\W", "_", cname)
	header=["Imported from swc file %s" % fname]	
	for line in f.readlines():
		if line[0]=="#":
			header.append(line[1:])
			continue	
		m=DATALINE.match(line)
		if not m:
			continue
		info=m.groups()
		id, reg=info[:2]
		par=info[-1]
		if par=='-1':
			root=id
		else:
			if not children.has_key(par):
				children[par]=[]
			children[par].append(id)
		regions[id]=reg
		points[id]=tuple(map(float, info[2:-1]))
	header = [x.strip() for x in header]	
	n = mien.parsers.nmpml.blankDocument()
	cell = mien.parsers.nmpml.createElement('Cell', {"Name":cname})
	cell.addComment("\n".join(header))
	parent=None
	cpid=root
	buildSections(root, None, cell, points, children, regions, sregions, [])
	n.newElement(cell)
	if len(sregions.keys())>1:
		for r in sregions.keys():
			reg = mien.parsers.nmpml.createElement('NamedRegion',{"Name":"region_%s" % r})
			cell.newElement(reg)
			for i, s in enumerate(sregions[r]):
				sec=cell.getSection(s)
				sup=sec.upath()
				ref=mien.parsers.nmpml.createElement('ElementReference', {"Name":"el%i" % i, "Target":sup})
				reg.newElement(ref)
	return n
	
def write(fileobj, doc, **kwargs):
	c=doc.getElements('Cell')
	if not c:
		print "No cells to write to SWC format"
		return
	if len(c)>1:
		print "WARNING: document contains multiple cells. SWC format can only store 1 cell. Using the first cell object for file write."
	c=c[0]
	cid=1
	secorder=c.branch()
	secids={None:-1}
	regions=c.getElements('NamedRegion', depth=1)
	for sn in secorder:
		sec=c.getSection(sn)
		for i, r in enumerate(regions):
			if sec in r.getSections():
				reg=i+1
				break
		else:
			reg=len(regions)+1
		pts=sec.getPoints()
		pid=secids[sec.parent()]
		for i in range(pts.shape[0]):
			pt=pts[i]
			if i==0 and sec.parent():
				ppt=c.getSection(sec.parent()).getPoints()[-1]
				if all(abs(pt-ppt)<.0001):
					continue
			line="%i %i %.3f %.3f %.3f %.3f %i\n" % (cid, reg, pt[0], pt[1], pt[2], pt[3], pid)
			fileobj.write(line)
			pid=cid
			cid+=1 
		secids[sec.name()]=pid
			
		

filetypes={}
filetypes['swc']={'notes':'Common database anatomy format',
					'read':read,
					'write':write,
					'data type':'anatomy',
					'elements': ["Cell"],
					'extensions':['.swc']}

