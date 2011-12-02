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

from data import Float64,fromstring,reshape,zeros, array, newData
from sys import byteorder
from mien.nmpml.basic_tools import NmpmlObject
import base64
from mien.math.array import Float32

def sortByIndAttrib(a, b):
	return cmp(a.attrib("Index"), b.attrib("Index"))


class Recording(NmpmlObject):
	'''Subclass for representing a record of a particular variable in
	a model. Intended to be a child element of an Experiment.  
	Each Recording can record any number of points in space,
	but a separate Recording should be used for each varriable.
	Points are stored as ElementReferences referencing Sections, with the
	Data atribute indicating the relative location along the section.
	If there is more than one such reference, they must also have 
	Index attributes.
	
	If no points are specified, the "Variable" is recorded directly  (useful 
	for global and object variables).
	
	Samples are stored in a child Data element, which is 
	automatically created if needed.
	Attributes:
	
	Variable: name of the varriable to be recorded. At some point
	           these names should be standardized, but for now they
			   are the names used by the Neuron simulator
	
	SamplesPerSecond: The recording rate in Hz.
	
	DataType:Optional. If not specified, uses Float32. Useful for very
	          long/spatially complex recordings of low prescision or
			  discrete variables, in order to save space.
	
	'''
	_allowedChildren =["Comments", "Data","ElementReference"]
	_requiredAttributes = ["Name","Variable","SamplesPerSecond"]
	_specialAttributes = ["DataType"]
	
	def __str__(self):
		return "Recording: %s" % (self.attrib('Variable'))

	def getData(self):
		de = self.getElementOrRef("Data")
		if de:
			self.data = de
		else:
			print "Can't find a data element. Making an empty one"
			attrs = {"Url":"auto://upath", "Name":"recordingdata","SamplesPerSecond":self.attrib("SamplesPerSecond"), 'SampleType':'timeseries'}
			self.data = newData(None, attrs)
			self.newElement(self.data)
		return self.data.getData()
	
	def setData(self, dat, col=None, tit=None):
		#print dat.shape, dat.max(), dat.min()
		self.getData()
		fs=self.attrib("SamplesPerSecond")
		if self.data.attrib("SamplesPerSecond")!=fs:
			self.data.setAttrib("SamplesPerSecond", fs)
		if col == None:
			self.data.datinit(dat, self.data.header())
			if tit:
				if type(tit)!=list:
					tit=[tit]
				self.data.setAttrib('Labels', tit)
		elif self.data.shape()[1]==0 or dat.shape[0]!=self.data.shape()[0]:		
			self.data.datinit(dat, self.data.header())
			self.data.setAttrib('Labels', [tit])
		elif col<self.data.shape()[1]:			
			self.data.setData(dat, [col])
			if tit:
				self.data.setChanName(tit, col)
		else:
			if tit and type(tit)!=list:
				tit=[tit]
			self.data.addChans(dat, tit)	
					
	def setAllData(self, dat, labels=None):
		self.getData()
		head=self.data.header()
		head["SamplesPerSecond"]=self.attrib("SamplesPerSecond")
		head["SampleType"]="timeseries"
		if labels:
			head["Labels"]=labels
		print dat.shape	
		self.data.datinit(dat, head)
		
	
	def getPoints(self):
		prs=self.getTypeRef("Section")
		pts=[]
		prs.sort(sortByIndAttrib)
		for pr in prs:
			rel = float(pr.attrib("Data"))
			sec = pr.target()
			pts.append([sec, rel])
		cells=self.getTypeRef("Cell")
		cells.sort(sortByIndAttrib)
		for c in cells:
			c=c.target()		
			print c
			for sec in c.branch():
				sec = c.getSection(sec)
				pts.append([sec, 0.0])
				pts.append([sec, 1.0])
		return pts	

	def clearValues(self):
		try:	
			fs=self.data.fs()
			self.data.datinit(None, self.data.header())
		except:
			self.getData()
	
	def getCellData(self, path):
		path=path.rstrip('/')
		prs=self.getTypeRef("Section")
		if prs:
			return None
		cells=self.getTypeRef("Cell")
		poss=[]
		for c in cells:
			if c.attrib("Target").rstrip('/')==path.rstrip('/'):
				poss.append(c)
		if len(poss)!=1:
			return None	
		cell=poss[0].target()
		ncols=cell.get_drawing_coords(spheres=True).shape[0]/2
		dat=self.getData()
		if dat==None:
			print "no data"
			return
		out=zeros((dat.shape[0], ncols), Float32)
		insat=0
		for i, sec in enumerate(cell.branch()):
			si=cell.getSection(sec)
			sv=dat[:,2*i]
			ev=dat[:,2*i+1]
			if si.attrib("Spherical"):
				npts=2
			else:	
				npts=si.points.shape[0]
			diff=(ev-sv)/npts
			for j in range(1,npts):
				na=sv+diff*j
				na=na.astype(Float32)
				out[:,insat]=na
				insat+=1
		return out

	def timestep(self):
		self.getData()
		fs=self.data.fs()
		return 1.0/fs
	
		
		
ELEMENTS={"Recording":Recording}
