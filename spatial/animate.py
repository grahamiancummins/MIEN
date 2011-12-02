#!/usr/bin/env python
# encoding: utf-8
#Created by gic on 2007-03-02.

# Copyright (C) 2007 Graham I Cummins
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA 02111-1307 USA
#
import os 
import mien.wx.graphs.glcolor as glc

from mien.spatial.cvextend import  getDisplayGroup 
def orbitAnimation(self):
	ns=int(100.0/self.graph.resolution)
	d = self.askParam([{"Name":"Number of Steps Per Half Cylce",
						"Value":ns},
						{"Name":"Directory",
						"Value":"CellGraph_Animation"}
						])
	if not d:
		return
	ns=d[0]	
	dir=d[1]
	self.graph.resolution=100.0/ns
	if os.path.isdir(dir):
		os.system("rm -rf %s" % dir)
	os.mkdir(dir)
	for i in range(2*ns):
		fname=os.path.join(dir, "frame%05i.png" % i)
		self.graph.screenShot(fname=fname)
		print fname
		self.graph.hOrbit(1)
	self.report("Saved Images")
	



def loadCellVoltageData(self):
	cell=self.getCell()		
	pn=self.getPlotName(cell)
	if not pn:
		self.report("Cell isn't plotted")
		return
	data = self.document.getElements(["Recording"])
	cdata={}
	timestep={}
	for e in data:
		dat=e.getCellData(cell.upath())
		if dat!=None:
			cdata[e.upath()]=dat
			timestep[e.upath()]=e.timestep()
	if not cdata:
		self.report("No data for this cell")
		return
	if len(cdata.keys())==1:
		datname=cdata.keys()[0]
	else:	
		d = self.askParam([{"Name":"Where",
							"Type":"List",
							"Value":cdata.keys()}])
		if not d:
			return
		datname=d[0]	
	d = self.askParam([{"Name":"Select Color Scale",
						"Type":"List",
						"Value":glc.colorscales.keys()}])
	if not d:
		return
	data=cdata[datname]
	timestep=timestep[datname]
	colordat = []
	r = [data.min(), data.max()]
	#r = [-60, -15]
	r[0] = r[0] - (r[1]-r[0])/30.0
	for i in range(data.shape[0]):
		colordat.append(glc.colorscale(data[i,:], scale=d[0],  r=r))
	scalecolors = glc.colorscale(glc.linspace(r[0], r[1], 30), scale=d[0],  r=None)
	self.graph.modelRefs[pn]["TimeSeries"]=colordat
	self.graph.modelRefs[pn]["TimeSeriesRaw"]=data
	self.graph.modelRefs[pn]["TimeSeriesStep"]=timestep
	if self.graph.plots.has_key('ColorScale'):
		del(self.graph.plots['ColorScale'])
	self.graph.addColorScale(min=r[0], max=r[1], colors=scalecolors, name="ColorScale")
	self.graph.showTimeSeries(0.0)

def showDataAtTime(self):
	d = self.askParam([{"Name":"At What Time?",
						"Value":0.0}])
	if not d:
		return
	self.graph.showTimeSeries(d[0])


def animate(self):
	nsteps=0
	for pn in self.graph.plots.keys():
		if not  self.graph.modelRefs.has_key(pn):
			continue
		if not self.graph.modelRefs[pn].has_key("TimeSeries"):
			continue
		alldat=self.graph.modelRefs[pn]["TimeSeries"]
		if alldat==None:
			continue
		nsteps=max(len(alldat), nsteps)
	if nsteps==0:
		self.report("No Data")
		return
	d = self.askParam([{"Name":"First Step",
						"Value":0},
					   {"Name":"Last Step",
						"Value":nsteps},
					   {"Name":"Directory",
						"Value":"CellGraph_Animation"}
					   ])
	if not d:
		return
	dir=d[2]
	if os.path.isdir(dir):
		os.system("rm -rf %s" % dir)
	os.mkdir(dir)
	for i in range(d[0], d[1]):
		self.graph.showTimeSeries(i, True)
		fname=os.path.join(dir, "frame%05i.bmp" % i)
		self.graph.screenShot(fname=fname)
		print fname
	#os.system("convert %s/frame* %s.mpg" % (dir, dir))	
	self.report("Saved Images")

def highlightEachGroup(self):
	for pn in self.graph.plots.keys():
		c=self.graph.plots[pn]['color']
		d=self.graph.plots[pn]['data'][:,3].copy()
		self.graph.plots[pn]['color']=[1.0,1.0,1.0]
		self.graph.plots[pn]['data'][:,3]=maximum(4, d*3)
		self.graph.recalc(pn)
		self.graph.OnDraw(pn)
		o=self.graph.modelRefs[pn]['mien.nmpml']
		ssn= getDisplayGroup(o) or o.name()
		self.graph.screenShot(ssn+'highlight.bmp')
		self.graph.plots[pn]['color']=c
		self.graph.plots[pn]['data'][:,3]=d
		self.graph.recalc(pn)


