
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
from mien.nmpml.basic_tools import NmpmlObject
from mien.spatial.alignment import alignPoints
from mien.math.array import array, ArrayType, concatenate, zeros, NewAxis, Float32, reshape, alltrue
from string import join

def add_point(a, p):
	if a.shape[1]>len(p):
		p2 = zeros(a.shape[1], p.dtype.char)
		p2[:len(p)]=p
		p=p2	
	elif a.shape[1]<len(p):
		a2=zeros((a.shape[0]+1, len(p)), a.dtype.char)
		a2[:-1,:a.shape[1]]=a
		a2[-1]=p
		return a2
	return concatenate([a, p[NewAxis, :]])

def pointsToTree(points, labels):
	nodes=[]
	for i in range(points.shape[0]):
		d={'tag':'Point', 'elements':[], 'cdata':'', 'attributes':{}}
		for j, a in enumerate(['x', 'y', 'z', 'd']):
			if j<points.shape[1]:
				d['attributes'][a]="%.4e" % points[i,j]
		if labels.get(i):
			d['attributes']['Description']=labels[i]
		nodes.append(d)
	return nodes	

def treeToPoints(nodes):
	points = []
	labels={}
	for i, n in enumerate(nodes):
		point=[]
		for v in ['x' , 'y', 'z' ]:
			point.append(float(n['attributes'][v]))
		if n['attributes'].has_key('d'):
			point.append(float(n['attributes']['d']))
		l=n['attributes'].get('Description')
		if l:
			labels[i]=l
		points.append(point)	
	points=array(points)		
	return (points, labels)

class PointContainer(NmpmlObject):
	'''Subclass for handling objects that contain a numerical array named "points"

members:
    points (array): may be Nx3 or Nx4 (x,y,z, [d])
	point_labels (hash) : Indexed by integers which reference rows in
		self.points. If this is specified, points will be output to xml
		with "Description" attribute.
'''
	
	_allowedChildren = ["Comments", "Point",
						"ElementReference"]
	
	
	def __init__(self, node, container=None):
		''' adds "Point" subelements to self, and removes them from node.
Creates the array self.points and the hash self.point_labels'''
		if node.has_key('point_data'):
			self.points, self.point_labels =node['point_data']
			del(node['point_data'])
			NmpmlObject.__init__(self, node, container)
		else:	
			NmpmlObject.__init__(self, node, container)
			pnodes=[d for d in node['elements'] if d['tag']=="Point"]
			for n in pnodes:
				node['elements'].remove(n)	
			self.points, self.point_labels=treeToPoints(pnodes)
				
	def getPoints(self):
		'''No Args => array
return a copy of self.points'''
		return self.points.copy()
	
	def setPoints(self, a, append=None):
		'''a (array), append (bool=False) => None
sets self.points to the specified array. If append is true, it
adds this array to the existing self.points'''
		if type(a)!=ArrayType:
			a=array(a, Float32)
		if not append or self.points==None or self.points.shape[0]==0:
			if len(a.shape)==1:
				a=array([a])
			self.points = a.copy()
		else:
			if len(a.shape)==2:
				self.points = concatenate([self.points, a])
			else:
				self.points = add_point(self.points, a)

	def getNamedPoint(self, name):
		'''name(str) => array or None
tries to find an entry in self.point_labels with value matching name,
and returns the point with index equal to the coresponding key.
Returns None if no match is found (common, since most PointContainers
dont have point_labels!)'''
		for i in self.point_labels.keys():
			if self.point_labels[i]==name:
				return self.points[i, :]
		return None

	def get_drawing_coords(self):
		'''No Args => array
return a 2Nx3 (or 2Nx4) array containing the start and stop coordinates for each
frustum specified in self.points.'''
		points =self.getPoints()
		s = points.shape
		points = concatenate([points, points],1)
		points = reshape(points, (-1, s[1]))[1:-1]
		return points

	def get_point_labels(self):
		'''No Args => list of strings'''
		l = []
		for i in range(self.points.shape[0]):
			try:
				l.append(self.point_labels[i])
			except:
				l.append("No Label")
		return l
		
	def doAlignment(self, conv):
		'''No Args => None
align all points acording to the conversion dict "conv"'''
		points = self.getPoints()
		try:
			points = alignPoints(points, conv)
			self.setPoints(points)
			#self.report("%s Aligned by %s" % (str(self), str(conv)))
		except:
			self.report("%s: FAILED ALIGNMENT" % str(self))
			raise

	def getTree(self, recurse=-1):
		'''return a dictionary representation of self (in the same
form used by __init__ and the methods is xmlhandler). if recurse is a 
possitive integer, limit the representation of child elements to the 
specified depth'''
		d={'tag':self.__tag__, 'attributes':self.getAttributes(),
			'cdata':self.getCdata(), 'elements':[]}
		if recurse!=0:
			d['elements'].extend(pointsToTree(self.points, self.point_labels))
			for e in self.elements:
				cd=e.getTree(recurse-1)
				d['elements'].append(cd)
		return d		

	def cloneData(self, clone):
		'''Internal method that makes clones have copies of (not references to ) 
the same data as the origional'''
		clone.setPoints(self.getPoints())
ELEMENTS={}
