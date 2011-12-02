#!/usr/bin/env python
#test import 

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
import re
import mien.nmpml
from mien.math.array import array

			
PYPOS_LINE = re.compile(r"(\S+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)")

def readPyPos(f, **kwargs):
	r = f.readlines()
	header = []
	points = {}
	for l in r:
		l=l.strip()
		if not l:
			continue
		m = PYPOS_LINE.match(l)
		if not m:
			header.append(l)
			continue
		point = tuple(map(float, m.groups()[1:]))
		name = m.groups()[0]
		points[name] = point	
	return (points, header)
			
def pypos2fed(f):
	points, head = readPyPos(f)
	correctedpoints = []
	labels = {}
	for n in points.keys():
		labels[len(correctedpoints)]=n.strip()
		p=points[n]
		p = ( p[1],p[0],-p[2])
		correctedpoints.append(p)
	points = array(correctedpoints)
	fed=mien.nmpml.elements["Fiducial"](attribs={"Name":"LeicaStageCoordinates",
						  "Style":"points",
						  "MarkerType": "OpenQuadStar"},
				 container=None, points=points, labels=labels)			 	
	n = mien.nmpml.elements["NmpmlDocument"](attribs={"Name":"Doc"}, tag="NmpmlDocument")
	n.newElement(fed)
	return n

def writePyPos(f, doc, **kwargs):
	for i in doc.elements:
		if i.__tag__!="Fiducial":
			print "PyPos file only supports Fiducials. Ignoring %s" % i.__tag__
			continue
		if i.points.shape[0]==1:
			print "PyPos file only supports 1 point per Fiducial. Discarding %i points from %s" % (i.points.shape[0]-1, str(i))
			p = i.points[0]
			n = i.attributes["Description"]
			f.write("%s %.4f %.4f %.4f\n" % tuple([n]+list(p)))
		else:	
			for p in range(len(i.points)):
				l = i.point_labels.get(p)
				if not l:
					print "PyPos file requires labeled points or 1 point per Fiducial. Discarding unlabeled point %i from %s" % (p, str(i))
				point = i.points[p]
				f.write("%s %.4f %.4f %.4f\n" % tuple([l]+list(point)))
				
				
	f.close()	


filetypes={}
filetypes['lieca']={'notes':'Format for storing anatomical alignment information from lieca scopes',
					'read':readPyPos,
					'write':writePyPos,
					'data type':'spatial',
					'elements': ['Fiducial'],
					'extensions':['.pypos']}
			
			
