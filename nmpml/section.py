#!/usr/local/bin/python

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
from mien.math.array import *
from mien.nmpml.pointcontainer import  PointContainer
from mien.nmpml.basic_tools import NmpmlObject

class Section(PointContainer):
	'''Data primative for use by class "cell". A Section describes a continuous
unbranched cell process. The section data container has the following
members:
    points - an Nx4 (N>=2) array of Floats. Each sublist contains
             4 floats: x,y,z,d
attributes:
    Name -   a string identifying the segment. All segments in the same
             cell must have unique names.	 
    Parent - the name of the next most proximal section,
             or "None" (iff this section is the root of the tree)
	Ra - axial resitivity in ohm*centimeter		 
'''
	__tag__ = "Section"
	_allowedChildren =["Point", "RangeVar","Comments","Synapse", "Ion", "Channel"]
	_requiredAttributes = ['Parent', 'Name']
	
	def __str__(self):
		return self.name()

	def writeHoc(self, of, s, p, objrefs):
		self._hocID=s
		if p:
			of.write("connect %s(0), %s(1)\n" % (s , p))
		of.write("%s {\n" % (s))
		if self.attrib("Ra"):
			of.write("    Ra = %s\n" % self.attrib("Ra"))	
		points = self.getPoints()
		nseg = self.attrib("Nseg")
		if not nseg:
			nseg = points.shape[0]
		of.write("    nseg = %i\n" % nseg)
		for p in points:
			of.write("    pt3dadd(%.6f,%.6f,%.6f,%.6f)\n" % tuple(p[:4]))
		for e in self.getElements():
			if "writeHoc" in dir(e):
				e.writeHoc(of, objrefs)
		of.write("}\n")

	def relLocOfPtN(self, i):
		pathl = cumsum(eucd(self.points, shift(self.points, 1)))
		return pathl[i]/pathl[-1]

	def ptAtRel(self, rel):
		pathl = cumsum(eucd(self.points, shift(self.points, 1)))
		loc = rel*pathl[-1]
		try:
			pt = nonzero1d(pathl>=loc)[0]
		except:
			pt = -1
		return pt

	def relativeLocation(self, point):
		'''point (tuple of 3 floats (x,y,z) => float on [0, 1] or -1 
convert the absolute possition (x,y,z) to a percentage of the distance from
the begining to the end of the section. Distance is measured along the
center of the section to the perpendicular plane containing the point.
Returns -1  if the point does not lie within the section.'''
		return inManifold(self.getPoints(), point[:3])
	
		
	def absoluteLocation(self, point):
		'''location(float on [0 to 1]) => tuple of 4 floats (x,y,z,d)
The inverse of relativeLocation.'''
		pathl = cumsum(eucd(self.points, shift(self.points, 1)))
		pathl=pathl/pathl[-1]
		rpt = nonzero1d(pathl>=point)[0]
		if pathl[rpt]==point:
			return self.points[rpt]
		dist=(point-pathl[rpt-1])/(pathl[rpt]-pathl[rpt-1])
		return  self.points[rpt-1]+(self.points[rpt]-self.points[rpt-1])*dist

	def parent(self):
		'''No Args => str or None
returns self.attributes["Parent"] or None if self.attributes["Parent"]=="None"'''
		p = self.attrib("Parent")
		if str(p) == "None":
			return None
		else:
			return str(p)
	
	def stats(self):
		'''No Args => tuple
(pathlength, euclideanlength, min diam, max diam, ave diam)'''
		try:
			dists = eucd(self.points, shift(self.points, 1))
		except:
			print self.points, self.name()
		pl = sum(dists)
		if pl==0:
			return (0,0,0,0,0)
		el = eucd(self.points[0], self.points[-1])
		dias=self.points[:,3]
		ad=sum(dias*(dists/pl))
		return (pl, el, min(dias), max(dias), ad)

	def morphInfo(self):
		'''returns a dictionary containing "volume", "area" and "length". Length
		is the path length along the core of the cylinder'''
		try:
			dists = eucd(self.points, shift(self.points, 1))
		except:
			print self.points, self.name()
		dists=dists[1:]
		rads=((self.points[:,3]+ shift(self.points[:,3], 1))/4.0)[1:]
		v=pi*(rads**2)*dists
		a=2*rads*pi*dists
		return {"volume":v.sum(), "length":dists.sum(), "area":a.sum()}

	def sample(self, n):
		'''n(int) => n x 4 array of floats
returns an array of points generated drawing n equally spaced absolute
locations along the section (0 is always sampled. 1 is never sampled).'''
		step = 1.0/n
		pts=arange(0, 1, step)
		locs = map(self.absoluteLocation, pts)
		return array(locs)

	def splitAtRel(self, loc):
		'''loc (relative location) => None'''
		print self.upath()
		if loc in [0.0, 1.0]:
			self.report("This is already a section edge")
			return
		node=self.getTree(recurse=0)
		node['attributes']['Name']=self.container.newSectionName()
		print self.upath()
		newparent = Section(node)
		for k in ["Ra"]:
			if self.attrib(k):
				newparent.attributes[k]=self.attrib(k)
		self.attributes["Parent"]=newparent.name()
		points = self.getPoints()
		sp = self.absoluteLocation(loc)
		pid = self.ptAtRel(loc)
		if all(points[pid] ==  sp):
			print "Exact"
			spts = points[pid:,:]
			ppts = points[:pid+1,:]
		else:
			spts = points[pid:,:]
			spts = concatenate([array([sp]), spts])
			ppts = points[:pid,:]
			ppts = concatenate([ppts, array([sp])])
		newparent.setPoints(ppts)
		self.setPoints(spts)
		for e in self.elements:
			if  e.__tag__=="Synapse":
				synpt = int(e.attrib("Point"))
				if synpt < pid:
					newparent.newElement(e)
					print "moved %s" % str(e)
				else:
					synpt = synpt - pid
					e.attributes["Point"]=synpt
					
			else:
				newparent.newElement(e.clone())		
		self.container.newElement(newparent)
		print self.upath()
	
	def setName(self, name=None):
		'''always ues this function to change the name of an nmpml 
object, to avoid generating non-unique names.
If this function is called without arguments (or name is None), it will
verify name uniqueness of the current name.

Return value is the actual name that was set (which may be different than
the provided argument do to required name uniqueness)

Its a very good idea to call "update_refs" after calling this function, 
since it may break references
'''
		on=self.attributes['Name']
		name=NmpmlObject.setName(self, name)
		cell=self.container
		if name==on and cell._sections.get(name)==self:
			return
		if cell._sections.has_key(on):
			del(cell._sections[on])
		cell._sections[name]=self		
		p = self.parent()
		if cell._children.has_key(p):
			if on in cell._children[p]:
				cell._children[p].remove(on)
			cell._children[p].add(name)
		else:
			cell._children[p]=set([name])
		if  cell._children.has_key(on):
			for c in cell._children[on]:
				c=cell._sections[c]
				c.attributes['Parent']=name
			cell._children[name]=cell._children[on]	
			del(cell._children[on])
	
ELEMENTS = {"Section":Section}
					
def makeTestSection():
	name="test"
	parent=None
	points = array([[0,0,0,1], [0,1,0,2], [1.6, 1.1, 0.1, 2.1], [3.0, 1, 1, 1]])
	return Section(name, parent, points)
