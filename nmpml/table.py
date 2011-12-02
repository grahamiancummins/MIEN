
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

from mien.math.array import *
import os

class Table(NmpmlObject):
	'''Class for representing tables of values. Values are stored
as a numeric array.

members:
    data: Dynamically assigned pointer to a Data instance.			
	poll: (array) The sampling order. See self.setPoll.
	spatial (array or None): Array of indexes of columns containing
                            x,y,z,[d] information. Used by several
							methods.
			
attributes:
    Granularity: float. If specified and non-zero, table lookups
	             will return the nearest value with a (euclidean)
				 distance less than this value from the requested
				 vector.
	Grow: Bool. If True, the Table will add entires for values calculated                 by interpolate or calculate methods, speeding up subsequent
	      lookups (using __getitem__ or getValue. Explicit calls to
		  interpolate and calculate will recalculate the results), but
		  increasing the memory size of the table. If not specified,
		  defaults to false.
		  

Tables will act like PointContainers (supporting getPoints, setPoints,
and doAlignment) if they have columns labled x, y, and z (and optionally d).
The performance of a table will be slower than a PointContainer, so they
should not be used if these are the _only_ column labels.

If a Table has a child object which is a Function, the
calculate method will evaluate the function for the specified
poll value, and the getValue method will attempt to calculate
after attempting lookup, but before interpolation. WARNINGS:
1) Functions only return single values, and
2) Functions dont support varriable numbers of arguments, so setPoll
will almost certainly break calculate.

If calculate fails (for any reason) within getValue, the method moves
on silently to attemp interpolation (failures within explicit calls to
calculate will raise exceptions).
'''
	_allowedChildren =["Comments", "Function", "Data", "ElementReference"]
	_requiredAttributes = ['Name']
	_specialAttributes = ['Granularity','Grow','Name']
	
	def findDataElement(self):
		datr = ["Type", "Labels", "Columns", "Url", "DataType", "SamplesPerSecond"]
		attrs = {"Type":"Auto"}
		for k in datr:
			if self.attributes.has_key(k):
				attrs[k]=self.attrib(k)
				del(self.attributes[k])
		de = self.getElements("Data")
		if de:
			self.data = de[0]
		else:
			print "Can't find a data element. Making an empty one"
			from mien.nmpml.data import newData
			self.data = newData(zeros((0,0), float32),  {'SampleType':'Locus'})
			self.newElement(self.data)

	def setValues(self, dat):
		self.findDataElement()
		h=self.data.header()
		self.data.datinit(dat, h)

	def refresh(self):
		self._instance_references = {}
		self.findDataElement()
		labels = self.data.attrib("Labels").split(',')
		self.setPoll(labels[:-1], [labels[-1]])
		if 'x' in labels and 'y' in labels and 'z' in labels:
			self.spatial=[]
			for k in ['x','y','z']:
				self.spatial.append(labels.index(k))
			if 'd' in labels:
				self.spatial.append(labels.index('d'))
			self.spatial = array(self.spatial)
		else:
			self.spatial = None
	

	def setLabels(self, l):
		self.findDataElement()
		self.data.setAttrib('Labels', l)
		
	def setPoll(self, li, lo):
		'''li (list of strs), lo (list of strs)=>
		[array, array] or None
Arguments are sequences of labels. If all these are not in Labels,
return False. Otherwise returns the attribute sell.poll (set to its new
value). This is a list of two arrays of ints, corresponding to the column
indexes of the labels in oi and lo.

If return is not False, this method changes the behavior of __getitem__
and interpolate. By default these accept a list or array of values
for the first M-1 columns, and return the value in the Mth column.
This method causes the sampling methods to accept a sequence of
values for the variables in li, and return values for the varriables
in lo. If lo is len 1, a scalar value is returned. Otherwise an Nx1 array
is returned where N is the len(lo).'''
		labels = self.data.getLabels()
		for e in li+lo:
			if not e in labels:
				return False
		self.poll =[[],[]]
		for e in li:
			self.poll[0].append(labels.index(e))
		for e in lo:
			self.poll[1].append(labels.index(e))
		self.poll = [array(self.poll[0]), array(self.poll[1])]	
		return self.poll

	def __getitem__(self, tup):
		'''ind (sequence) => float or array of floats
Returns the value of the return column (the last entry in self.poll)
for which the index columns (all entries but the last in self.poll)
equal ind (or are within Granularity of ind). If there is no such value,
return None. '''
		inds = take(self.data.values, self.poll[0], 1)
		vals = take(self.data.values, self.poll[1], 1)
		if not type(tup)==ArrayType:
			tup=array(tup)
		ind = nonzero1d(alltrue(inds == tup, 1))
		if len(ind):
			r=vals[ind[0]]
			if len(r)==1:
				return r[0]
			else:
				return r
		else:
			g=self.attrib("Granularity")
			if not g:
				return None
			else:
				g=float(g)
				d = eucd(tup, inds)
				a = argsort(d)[0]
				if d[a]<g:
					r = vals[a]
					if len(r)==1:
						return r[0]
					else:
						return r
				else:
					return None

	def interpolate(self, tup):
		'''ind (sequence) => float or array of floats
Acts like getitem, except uses linear interpolation based on
the two nearest points to generate new points.'''
		inds = take(self.data.values, self.poll[0], 1)
		vals = take(self.data.values, self.poll[1], 1)
		if not type(tup)==ArrayType:
			tup=array(tup)
			
		d = eucd(tup, inds)
		neighbors = argsort(d)[:2]
		i=2
		nbi=[0, 1]
		nb = inds[neighbors[0]],inds[neighbors[1]]
		while not all(nb[-1]-nb[0]):
			if i>=len(neighbors):
				return None
			nb[-1]=inds[neighbors[i]]
			nbi[1]=i
			i+=1
		rel, offl = projectToLine(tup, nb[0], nb[1])
		sep = eucd(nb[0],nb[1])
		rel = rel/sep
		sv = vals[nbi[0]]
		change = vals[nbi[1]] - sv
		r =  sv + change*rel
		if self.attrib("Grow") and self.attrib("Grow")!="False":
			newline = list(tup)+r.tolist()
			self.addEntry(array(newline))
		if len(r)==1:
			return r[0]
		else:
			return r

	def calculate(self, tup):
		'''tup (tuple) => float
evaluate child function using input tuple.'''
		f = self.getElements("Function", {}, 1)[0]
		out = f[tup]
		if self.attrib("Grow") and self.attrib("Grow")!="False":
			newline = list(tup)+[out]
			self.addEntry(array(newline))
		return out

	def getValue(self, tup):
		'''ind (sequence) => float or array of floats
Tries getitem, then tries calculate, then interpolate.'''
		r = self[tup]
		#print "lookup",tup,  r
		if r==None:
			try:
				r = self.calculate(tup)
				#print "calc", r
			except:
				r = self.interpolate(tup)
				#print "interp", r
		return r
		
	def getPoints(self):
		'''No Args => array or None
If there are x,y,z, [d] columns in the table, return an array of them.'''
		if not self.spatial:
			return None
		return  take(self.data.values, self.spatial, 1)

	def setPoints(self, points, append=None):
		'''May not append'''
		if not self.spatial:
			raise "No points"
		elif points.shape[0]!=self.data.values.shape[0] or points.shape[1]!=len(self.spatial):
			raise "Point array has wrong dimensions"
		for i in range(len(self.spatial)):
			self.data.valeus[:,self.spatial[i]]=points[:,i]

	def addEntry(self, a):
		'''a (array) => None
add the entry line specified in the 1D array a to the table
if it is not already included'''
		if not sum(alltrue(self.data.values==a)):
			self.data.values=concatenate([self.data.values, a[NewAxis, :]])
		
	def doAlignment(self, conv):
		'''No Args => None
align all points acording to the conversion dict "conv"'''
		points = self.getPoints()
		try:
			points = alignPoints(points, conv)
			self.setPoints(points)
			self.addComment("Scaled by %s" % str(conv))
			self.report("%s Aligned by %s" % (str(self), str(conv)))
		except:
			self.report("%s: FAILED ALIGNMENT" % str(self))
		
	def uniformSample(self, ra):
		'''ra (len(self.poll[0])x3 array) => Table instance
returns a table with entries sampling the ranges specified in ra.
ra has three columns containing [min, max, step], and one row
for each entry in self.poll[0]. The values fro the new table
are determined by self.getValues. The attributes of the new
table will be the same as self, but the container will be None,
and there will be no child elements.'''
		atr = {}
		atr.update(self.attributes)
		t = Table(atr, tag = self.__tag__)
		t.addComment("generated by uniformSample(%s) from %s" % (repr(ra), str(self)))
		#FIXME
		

if __name__=="__main__":
	a = arange(30)
	a = reshape(a, (6,5))
	attribs = {"Type":"Base64", "Labels":"x,y,z,d,v"}
	t = Table(attribs=attribs, values = a)
	t.attributes["Granularity"]=1.0
	t.setPoll(['x','y','z'], ['d','v'])
##  from mien.parsers.fileIO import READERS, WRITERS, genDoc
## 	doc = READERS['nmpml']('test.xml')
## 	t=doc.getElements("Table")[-1]
	print t.data.values
	print "0,1,2=>", t[[0,1,2]]
	print "4, 5.1, 6=>", t[[4, 5.1,6]]
	print "interp 3,40,5 =>", t.interpolate([3,40,5])
	#print "cal 3,20,5 =>",t.calculate([3,20,5])

	print "get 3,19,5 =>",t.getValue([3,19,5])
	print t.writeXML()
