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

import basic_tools
from mien.math.array import *
import re,time

class NamedRegion(basic_tools.NmpmlObject):
	'''Class for representing named regions of a cell (e.g. "axon")
spanning several sections. Contains some number af ElementReferences
pointing at sections. This should be a direct child of the referenced cell
'''
	
	_allowedChildren = ["Comments", "ElementReference"]
	_requiredAttributes = ["Name"]

	def __init__(self, node, container=None):
		basic_tools.NmpmlObject.__init__(self, node, container)
		self._sections=None
		self._order=None

	def getSections(self):
		'''returns a list of section instances contained in the region'''
		if self._sections==None:
			self._sections=[x.target() for x in self.getTypeRef("Section")]
		return self._sections

	def getSectionNames(self):
		return [x.name() for x in self.getSections()]
		
	def contains(self, point):
		'''3tuple => 1 or 0
true if the specified point is contained by a section that is a member of
the region.'''
		r = self.container.relativeLocation(point)
		if r[0] in self.getSectionNames():
			return 1
		else:
			return 0

	def getInverse(self):
		'''return the list of all the sections of the container
that are not part of this region'''
		secs = self.getSections()
		return [x for x in self.container._sections.values() if not x in secs]

	def depth(self, sec):
		depth=0
		while sec.parent():
			sec=self.container.getSection(sec.parent())
			depth+=1
			

	def getOrder(self):
		if self._order==None:
			secs = self.getSections()
			secs.sort(lambda x, y:-1*cmp(self.depth(x),self.depth(y)))
			self._order=secs
		return self._order


class Cell(basic_tools.NmpmlObject):
	'''Data structure for storing physiological model information about a
single cell, with methods for manipulating the information and doing
file/string I/O.
members:
    (These members are generated automatically)

	_sections (dict) => mapping of  section names to instances.
	_children (dict) => a mapping of section names onto lists of names
	                    of their child sections. Generated automatically
						during use to improve the efficiency of certain
						operations	
	_points_in_sec(dict) => tuples (first, last+1) on to section names	

attributes:
    Name (string) => identifir string. All Cells in the same Network must
	                 have unique names.
	Eleak => optional. Resolves to float. The leak conductance reversal
	potential. If specified, overrides calculation of Leak RP from
	child Ion objects

	ReferencePoint: upath to a referencepoint object

	Vrest => optional. Specify the resting potential, if it is different
	than the leak reversal potential.
'''
	_allowedChildren = ["Section", "Comments", "Function",
						"Data", "NamedRegion",
						"Parameters", "ElementReference"]
	_requiredAttributes = ["Name"]
	_specialAttributes = ["Eleak", "Vrest"]
	
	def __init__(self, node, container=None):
		'''As the parent class method, but also casts attributes to 
python data types, and initializes _references'''
		basic_tools.NmpmlObject.__init__(self, node, container)
		self._sections={}
		self._children={}
		self.points=zeros(0)
	
	def setElements(self, els):
		'''Set the list self.elements, and the link e.container'''
		basic_tools.NmpmlObject.setElements(self, els)
		secs=[e for e in self.elements if e.__tag__=='Section']
		self._sections={}
		self._children={}
		for e in secs:
			n = e.name()
			self._sections[n]=e
			p = e.parent()
			if not self._children.has_key(p):
				self._children[p]=set([])
			self._children[p].add(n)
		
	def removeElement(self, e):
		'''removes an element from self.elements. In this class, this 
is trivial, but subclasses may need to use it to maintain state.'''
		if not e in self.elements:
			return
		self.elements.remove(e)
		if e.__tag__=="Section":
			n = e.name()
			del(self._sections[n])
			p = e.parent()
			if self._children.has_key(p) and n in self._children[p]:
				self._children[p].remove(n)
			if  self._children.has_key(n):
				for c in self._children[n]:
					ci=self.getSection(c)
					ci.attributes['Parent']=None
				del(self._children[n])

	def getPoints(self, unique=False):
		'''returns an array of points in the cell. If unique is true,  duplicate points are removed. Duplicates occur because a child section specifies the last point in the parent section as its first point'''
		self._points_in_sec={}
		points = zeros((0,4), Float32)
		for sn in self.branch():
			s = self.getSection(sn)
			p =s.getPoints()
			start = len(points)
			if unique and s.parent():
				ppt=self.getSection(s.parent()).getPoints()[-1]
				if all(abs(p[0]-ppt)<.0001):
					p=p[1:,:]		
			points = concatenate([points, p])
			self._points_in_sec[sn]=(start, len(points))
		return points	

	def doAlignment(self, conv):
		for s in self.getElements("Section", {}, 1):
			s.doAlignment(conv)
			
	def setPoints(self, a, append=None):
		if append:
			s = self.getSection(append)
			s.setPoints(a, append=1)
		else:
			for k in self._points_in_sec.keys():
				r = self._points_in_sec[k]
				self.getSection(k).setPoints(a[r[0]:r[1]])

	def nthCenter(self, i):
		'''returns the relative location of the nth compartment center'''
		ind = 0
		for sn in self.branch():
			s = self.getSection(sn)
			npts =s.points.shape[0]
			if ind+npts-1>i:
				centi = i-ind
				r1 = s.relLocOfPtN(centi)
				r2 = s.relLocOfPtN(centi+1)
				rel = (r1+r2)/2.0
				return (sn, rel)
			else:
				ind+=(npts-1)
	
	def nthPoint(self, i):
		'''i (int) -> (str, float) 
		returns the relative location of the ith point in self.getPoints()'''
		for sn in self._points_in_sec.keys():
			start, stop=self._points_in_sec[sn]
			if start<=i:
				if stop>i:
					sec=self.getSection(sn)
					rel=sec.relLocOfPtN(i-start)
					return (sn, rel)
		return (None, -1)			
				
	def get_drawing_coords(self, spheres=False):
		'''ref (bool=False) => array 
return a 2Nx3 (or 2Nx4) array containing the start and stop coordinates for
each frustum specified in self.points.'''
		ord = self.branch()
		points = None
		for sn in self.branch():
			s = self.getSection(sn)
			p =s.getPoints()
			if spheres and s.attrib("Spherical"):
				cent=sum(p)/p.shape[0]
				p=array([cent, cent])
				p[1,3]=0.0
				p[0,3]=float(s.attrib("Spherical"))
			else:	
				s = p.shape
				p = concatenate([p, p],1)
				p = reshape(p.ravel(), (-1, s[1]))[1:-1]
				if p.shape[0] %2:
					print "Warning, %s has %i coords" % (sn, p.shape[0])
			if points == None:
				points = p
			else:
				try:
					points = concatenate([points, p])
				except:
					print points.shape, p.shape
					raise
		return points

	def sec_draw_indexes(self, secs, spheres=False):
		'''Lit of strings (section names) -> list of ints 
		Returns the indexes into self.get_drawing_coords() for each point contained
		in the sections listed in secs.'''
		inds = []
		ind=0
		for sn in self.branch():
			s = self.getSection(sn)
			if spheres and s.attrib("Spherical"):
				npts=2
			else:	
				p =s.getPoints()
				npts = p.shape[0]*2 - 2
			if sn in secs:
				inds.extend(range(ind, ind+npts))
			ind+=npts
		return inds

	def drawingCoordIndex(self, spheres=False):
		'''() -> list of (str, int)
		Returns a list of the same length as the array from self.get_drawing_coords, 
		specifying the location of each point in that array as tuples of (section name, 
		point index) (the point index such that self.getSection(name).getPoints()[index,:]
		returns the point
		'''
		ord = self.branch()
		points = []
		for sn in self.branch():
			s = self.getSection(sn)
			if spheres and s.attrib("Spherical"):
				points.append((sn, 0))
				points.append((sn, 1))
			else:
				p =s.getPoints()
				s = p.shape
				p=arange(p.shape[0])
				p = concatenate([p[:,NewAxis], p[:,NewAxis]],1)
				p = reshape(p, (-1, 1))[1:-1]
				points.extend([(sn, i[0]) for i in p])
		return points

	def getSectionBoundaries(self):
		'''-> array
		return an array containing the ening points of each section
		(in the order used by self.branch()). The first element is the
		starting point of the root section (all other sections should
		start where their parent ends)''' 
		pts=[]
		r= self.getSection(self.root())
		pts.append(r.points[0])
		for sn in self.branch():
			s = self.getSection(sn)
			pts.append(s.points[-1])
		return array(pts)

		
	def doAlignment(self, conv):
		align = self.getElements("Section")
		for o in align:
			o.doAlignment(conv)
		

	def getSection(self, name):
		'''name(str) => instance (or None)
find a section instance by name'''
		return self._sections[name]
		
	def root(self):
		'''None => str
		returns the name of the root section'''
		s = self._children[None]
		if len(s)!=1:
			raise "Cell does not have a unique root! (Badly formed cell)"
		return list(s)[0]
	
	def __getitem__(self, s):
		'''string => instance
return the section instance named "string" or None (if no such section)'''
		return self._sections.get(s)

	def getChildren(self, s):
		'''name (str) => list of strings
		returns all the sections with parent "name".'''
		return list(self._children.get(s, []))
			
	def branch(self, root=None, depth=-1):
		'''root (str) depth(int = -1), => list of strings
return a list of section names coresponding to the branch pattern
(depth first) of the cell, starting at the section "root". If
"depth" is positive, only that number of succesive children are
returned. If root is not specified, self.root() is used.
If showDepth is true, returns a list of tuples containg the 
section names and their branch depths.
'''
		if not root:
			root=str(self.root())	
		order=[root]
		if depth==0:
			return order
		depth-=1
		for kid in self.getChildren(root):
			order.extend(self.branch(kid, depth))
		return order

	def relativeLocation(self, point):
		'''3tuple => 2tuple
Takes a point in space as an (x,y,z) tuple of floats, and returns a
location as ("name", float) representing the name of the section containing
the point and the relativeLocation of the point in that section. Returns
("", -1) if the point is not in any section. NOTE: It is technically possible
for a spacial point to be in more than one section. In this case the first
match is returned. Since the order depends on the ordering of hash values,
this may not always return the same result (but t=self.relativeLocation(pt),
p = self.sections[t[0]].absoluteLocation(t[1]) should always return p==pt
to within float rounding error.)'''
		for s in  self.getElements("Section", {}, 1):
			r = s.relativeLocation(point)
			if r != -1:
				return (s.name(), r)
		return ("", -1)

	def ptInSec(self, point):
		'''Returns a tuple containing section name, point index for a
		point exactly matching te given point. "", -1 if no match'''
		for s in self._sections.values():
			m=alltrue(point[NewAxis,:]==s.points[:,:3], 1)
			if any(m):
				id=nonzero1d(m)[0]
				return (s.name(), id)
		return ("", -1)	



	def absoluteLocation(self, loc):
		'''loc (tuple of string and float on [0 to 1]) =>
		point (tuple of 4 floats (x,y,z,d))
The inverse of relativeLocation.'''
		s = self.getSection(loc[0])
		return s.absoluteLocation(loc[1])
		

	def getPath(self, s1, s2):
		'''s1 (str), s2 (str) => (p (str), list of strings)
if s1 and s2 are section names, returns the path between them. p==s1 
if s1 is a (grand)parent of s2 (or if s1 == s2), p==s2 if s2 is a
(grand)parent of s1, and otherwise p is the name of the mutual parent
of s1 and s2. the list is a list of all the sections passed through to
get from s1 to s2 (not including s1, s2, or p)'''
		if s1 == s2:
			return (s1, [])
		sec = self.getSection(s1)
		s1p =[]
		while sec.parent():
			if sec.parent() == s2:
				return (s2, s1p)
			s1p.append(sec.parent())
			sec=self.getSection(sec.parent())
		s2p =[]
		sec = self.getSection(s2)
		while sec.parent():
			if sec.parent() == s1:
				return (s1, s2p)
			if sec.parent() in s1p:
				s1p=s1p[:s1p.index(sec.parent())]
				s2p.reverse()
				s1p+=s2p
				return (sec.parent(), s1p)
			s2p.append(sec.parent())
			sec=self.getSection(sec.parent())
		raise "No Path Between Points"	

	def pathLength(self, loc1, loc2=None):
		'''tuple, tuple=None => float
Takes 2 cell relativeLocation tuples and returns the path length between
them. If the second tuple is not given, it defaults to (self.root(), 0)'''
		if not loc2:
			loc2=(str(self.root()), 0)
		if 	loc1[0] == loc2[0]:
			return self.getSection(loc1[0]).stats()[0]*abs(loc1[1]-loc2[1])
		par, path = self.getPath(loc1[0], loc2[0])
		if par == loc1[0]:
			d= self.getSection(loc1[0]).stats()[0]*(1-loc1[1])
			d+=self.getSection(loc2[0]).stats()[0]*(loc2[1])
		elif par == loc2[0]:
			d= self.getSection(loc2[0]).stats()[0]*(1-loc2[1])
			d+=self.getSection(loc1[0]).stats()[0]*(loc1[1])
		else:
			d= self.getSection(loc2[0]).stats()[0]*(loc2[1])
			d+=self.getSection(loc1[0]).stats()[0]*(loc1[1])
		for s in path:
			d+=self.getSection(s).stats()[0]
		return d

	def _addDistal(self, section, howfar, dist, exclude=[]):
		'''str, float, float, list of strings => list of strings'''
		secs=[]
		if dist<howfar:
			kids=self.getChildren(section)
			for k in kids:
				if k in exclude:
					continue
				secs.append(k)
				l=self.getSection(k).stats()[0]
				if l+dist < howfar:
					secs.extend(self._addDistal(k, howfar, l+dist, exclude))
		return secs			

	def _addProximal(self, section, howfar, dist):
		secs=[]
		if dist<howfar:
			par=self.getSection(section).parent()
			if not par:
				return []
			secs.append(par)
			secs.extend(self._addDistal(par, howfar, dist, [section]))
			l=self.getSection(par).stats()[0]
			if l+dist<howfar:
				secs.extend(self._addProximal(par, howfar, l+dist))
		return secs	

	def getWithinPathLength(self, loc, pl, dir="All"):
		'''loc (2tuple, (str, float)), pl (float), dir (str) => list of strings
		Return a list af the names of sections within pl microns of loc. A
		Section is included if any of its points are within pl. Distance is
		measured along the dendrite, not throegh space. If dir is Proximal, or
		Distal, then only the specified direction is searched'''
		secs = [loc[0]]
		section=self.getSection(loc[0])
		seclen=section.stats()[0]
		if not dir=="Proximal":
			tail = seclen*(1-loc[1])
			secs.extend(self._addDistal(loc[0], pl, tail))
		if not dir=='Distal':
			head=seclen*(loc[1])
			secs.extend(self._addProximal(loc[0], pl, head))
		return secs	

	def morphInfo(self):
		'''Returns a dictionary containing information about the cell morphology.
		This is the sum of the results returned by Section.morphInfo for every 
		section'''
		info=None
		for sn in self.branch():
			sec=self.getSection(sn)
			if not info:
				info=sec.morphInfo()
			else:
				d=sec.morphInfo()
				for k in info.keys():
					info[k]+=d[k]
		return info

	def newSectionName(self):
		'''=> String
		returns an unused section name'''
		name = "section"
		secnames = [x for x in self._sections.keys() if x.startswith(name)]
		i=0
		while "%s[%i]" % (name, i) in secnames:
			i+=1
		name = "%s[%i]" % (name, i)
		return name

	def uniformSectionLength(self, l=None):
		'''Float (None) => None
		Subdivides all sections so that they are as close as possible to having a
		uniform length. If l is specified, try to attain this length. Otherwise,
		use the length of the shortest section. All sections longer than this length
		will be devided into a number of equal length subsections, such that the length
		of the subsection is as crose as possible to l'''
		slens=dict([(x.name(), x.stats()[0]) for x in self._sections.values()])
		if not l:
			l=min(slens.values())
		for s in slens.keys():
			if slens[s]<1.5*l:
				continue
			splits=int(round(slens[s]/l))-1
			sec = self.getSection(s)
			print "%s, len %.2f, split %i times" % (s, slens[s], splits)
			for r in range(splits+1,1,-1):
				rel = 1.0/r
				sec.splitAtRel(rel)
		
	def	nearestTip(self, sec):
		'''s (str) => str
returns the name of the distal tip section that is closest to section s'''
		d=1
		while 1:
			b=self.branch(sec, d)
			for s in branch:
				if len(self.getChildren[s])==0:
					return s
			d+=1	

	def branchDepth(self, sec):
		'''s (str) => int
return the branch depth of section s (0 for root, 1 for primary branches...'''
		bd = 0
		sec=self.getSection(sec)
		while sec.parent():
			sec=self.getSection(sec.parent())
			bd+=1
		return bd

		
	def contains(self, point):
		'''point (x,y,z tuple)=> Bool
return 1 if point (x,y,z) is contained in one of this cells sections'''
		if self.relativeLocation(point)[0]:
			return 1
		else:
			return 0
		
	def diam(self, point):
		'''point (x,y,z tuple)=> float
if point (x,y,z) is contained in one of this cells sections return the
section diameter at that point. Else return -1'''
		r = self.relativeLocation(point)
		if not r[0]:
			return -1
		p = self.getSection(r[0]).absoluteLocation(r[1])
		return p[3]

	def cPath(self, point):
		'''point (x,y,z tuple)=> float
if point (x,y,z) is contained in one of this cells sections return the
path length from root to this point. Else return -1'''
		p = self.relativeLocation(point)
		if not p[0]:
			return -1
		return self.pathLength(p)

	def icPath(self, point):
		'''point (x,y,z tuple)=> float
if point (x,y,z) is contained in one of this cells sections return the
path length from the nearest distal tip  to this point. Else return -1'''
		p = self.relativeLocation
		if not p[0]:
			return -1
		t = self.nearestTip(p[0])
		return self.pathLength(p, (t, 1))

	def bDepth(self, point):
		'''point (x,y,z tuple)=> int
if point (x,y,z) is contained in one of this cells sections return the
order of the branch containing this point. Else return -1'''
		p = self.relativeLocation(point)
		if not p[0]:
			return -1
		return self.branchDepth(p[0])	

	def inRegion(self, sectionname):
		'''sectionname (str) => list
Returns a list of all NamedRegions (instances, not names) containing the
named section. This list may be empty.'''
		regions = []
		reg = self.getElements("NamedRegion")
		for r in reg:
			if sectionname in r.sections:
				regions.append(r)
			else:
				pass
				#print r.sections	
		return regions


	def getEquilibriumVm(self):
		if self.attrib('Vrest'):
			return float(self.attrib('Vrest'))
		elif self.attrib('Eleak'):
			return float(self.attrib('Eleak'))
		else:
			e=self.getElements("Channel", {"Ion":"Leak"})
			if not e:
				return -60.0
			e=e[0].attrib('Reversal')
			if type(e)==list:
				e=e[0]
			return e
			

	def compartmentCenters(self):
		'''No Args: returns a list of [sec, [p1 p2 p3]] contianing the
		name of each section and the list of relative locations at the
		center of each compartment in the section'''
		sl=[]
		for sn in self.branch():
			sec = self.getSection(sn)
			ind=sec.points.shape[0]
			rels=[]
			for i in range(ind):
				rels.append(sec.relLocOfPtN(i))
			rels=array(rels)
			rels=(rels[:-1]+rels[1:])/2
			rels=list(rels)
			sl.append([sn, rels])
		return sl	
		
							   
	def getDensityMap(self, tag, name=None):
		ord = self.branch()
		points = None
		for sn in self.branch():
			sec = self.getSection(sn)
			p =sec.getPoints()
			p = concatenate([p[:-1], p[1:]],1)
			centers = (p[:,:3]+p[:,4:7])/2
			if tag=="Ra":
				val=float(sec.attrib("Ra"))
				val=ones(centers.shape[0], Float32)*val
			else:
				c=sec.getElements(tag, name)
				if not c:
					val=zeros(centers.shape[0], Float32)
				else:
					c=c[0]
					if tag=="Channel":
						val=c.attrib("Density")
					else:
						val=c.attrib("Values")
					if type(val) in [int, float]:
						val=[val]
					if len(val)==1:
						val=ones(centers.shape[0], Float32)*val[0]
					else:
						if centers.shape[0]==1:
							val=array([(val[1]+val[0])/2.0])
						else:
							pathl = cumsum(eucd(centers, shift(centers, 1)))
							totl=sec.stats()[0]
							rell=pathl/totl
							grad=val[1]-val[0]
							grad=rell*grad
							val=grad+val[0]
			if points == None:
				points = val
			else:
				try:
					points = concatenate([points, val])
				except:
					print points.shape, p.shape
					raise
		return points

	def writeHoc(self, of):
		pars = self.getElements("Parameters", {"ParameterSetType":"NeuronSimulatorParameters"})
		#print pars
		if pars:
			for pl in pars:
				pnames = pl.keys()
				#print pl, pnames
				for p in pnames:
					#print "%s = %.6f\n" % (p, pl[p])
					of.write("%s = %.6f\n" % (p, pl[p]))
		of.write('\n')
		objrefloc=of.tell()
		objrefs=["%s_objref" % self.name(), 0]
		pad=len("objref %s[%i]" % (objrefs[0], 10000000))
		of.write(" "*pad+"\n")
		of.write("\n")
		sections = self.branch()
		of.write("create %s[%i]\n" % (self.name(), len(sections)))
		for i, s in enumerate(sections):
			of.write("\n")
			sec=self.getSection(s)
			sn="%s[%i]" % (self.name(), i)
			if sec.parent():
				spn=sections.index(sec.parent())
				spn="%s[%i]" % (self.name(), spn)
			else:
				spn=None
			sec.writeHoc(of, sn, spn, objrefs)
		of.write("\n")
		if objrefs[1]:
			cur=of.tell()
			of.seek(objrefloc)
			of.write("objref %s[%i]" % (objrefs[0], objrefs[1]))
			of.seek(cur)
		of.write("access %s[0]\n" % self.name())
	
ELEMENTS = {"Cell":Cell, "NamedRegion":NamedRegion}
