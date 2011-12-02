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

from mien.math.array import log
from numpy import *
#import otherfuncs as oth
#from mien.wx.graphs.glcolor import colorscales

def showChan(cv):
	c = cv.getCell()
	plotid = cv.getPlotName(c)
	mechanisms=["Ra"]
	for s in c._sections.values():
		ell=s.getElements(["Channel", "RangeVar"])
		for e in ell:
			n="%s:%s" % (e.__tag__, e.name())
			if not n in mechanisms:
				mechanisms.append(n)
	d=cv.askParam([{"Name":"Mechanism",
					  "Type":"List",
					  "Value":mechanisms}])
	if not d:
		return
	d=d[0].split(':')
	if len(d)>1:
		tag, name=d[:2]
	else:
		tag=d[0]
		name=None
	mask =c.getDensityMap(tag, name)
	pad=(max(mask)-min(mask))/30.0
	colorrange = [min(mask)-pad,max(mask)]
	print mask.shape
	cv.graph.set_color(plotid,mask, 'hot', colorrange)
	cv.graph.OnDraw()
	
	
def showSections(cv):
	c=cv.getCell()
	name=cv.getPlotName(c)
	eos=[x for x in c.branch() if c.branchDepth(x)%2]
	cv.graph.highlightSections(name, eos)

def showMask(cv):
	c = cv.getCell()
	t = c.getElements("Data", {"SampleType":"mask"})
	if not t:
		cv.report('No masks')
		return
	td=dict([(n.name(), n) for n in t])
	d = cv.askParam([{"Name":"Mask",
						"Type":"Select",
						"Value":td.keys()}])
	if not d:
		return

	print d, d[0], td
	if not d[0]:
		masks=td.values()
	else:
		masks=[td[x] for x in d[0]]
	mask = masks[0].getData()
	for m in masks[1:]:
		try:
			mask+=m.getData()
		except:
			print "can't add mask %s to existing masks" % (m.name(),)
	mask+=max(mask)*1e-4
	mask = log(mask)
	colorrange = [min(mask),max(mask)]
	cv.graph.set_color(cv.getPlotName(c),mask, 'hot', colorrange)
	cv.graph.OnDraw()

def angle_mean(vect, weights):
    #check on inputs CHECK INPUTS
    vect = array(vect)
    vect = vect % 360 #cast to one circle
    #first linear domain
    smallangs = vect<=180
    if smallangs.any():
        weigh1 = weights[smallangs]
        sw1 = sum(weigh1)
        round1 = sum(vect[smallangs]*weigh1)/sw1
    else:
        round1 = sw1 = 0.
    #second linear domain
    largeangs = vect>180
    if largeangs.any():
        weigh2 = weights[largeangs]
        sw2 = sum(weigh2)
        round2 = sum(vect[largeangs]*weigh2)/sw2
    else:
        round2 = sw2 = 0.
    #still avoiding rounding errors and such
    if round2-round1>180:
        averageang = (round1*sw1+(round2-360)*sw2)/(sw1+sw2)
        averageang = averageang % 360 
    else:
        averageang = (round1*sw1+round2*sw2)/(sw1+sw2)
    return averageang
	
def _dirmask_from_cell(c,distality):
	minreal = 1e-11
	t = c.getElements("Data", {"SampleType":"mask"})
	t = [n for n in t if not n.attrib("meta_cercus")==None]
	if distality==0:
		t = [n for n in t if not n.attrib("meta_class")==0]
	elif distality==1:
		t = [n for n in t if not n.attrib("meta_class")!=0]

	wghts = array([m.getData().flatten() for m in t])
	ngles = [m.attributes['meta_directional_tuning'] for m in t]
	mask = zeros((wghts.shape[1],1))
	for m in range(wghts.shape[1]):
		mask[m] = round(angle_mean(ngles, weights=wghts[:,m])) 
	
	totalweight = sum(wghts,axis=0)
	mask[totalweight<minreal] = 360 #the first impossible integer value
	return mask
	
def showBestDir(cv):
	c = cv.getCell()
	#mask = dirweight/totalweight#this should give us sum(angle*weight)/sum(weight) for each point
	#distops = {'Just Proximal':0,'Just Distal':1,'Both':2}
	distops = ['Just Proximal','Just Distal','Both']
	d = cv.askParam([{"Name":"Include Distal?",
						"Type":"List",
						"Value":distops}])
	if not d:
		return
	print d
	distality = distops.index(d[0])

	mask = _dirmask_from_cell(c, distality)
	#scaling
	mask = mask.astype(int)
	#map the axon to white somwhere along the way here
	regions = c.getElements('NamedRegion')
	if 'NoSynapses' in [r.name() for r in regions]:
		trunkregion = [r for r in regions if r.name()=='NoSynapses']
	if 'Axon' in [r.name() for r in regions]:
		trunkregion += [r for r in regions if r.name()=='Axon']
	if len(trunkregion):
		trunksegments=[]
		for rg in trunkregion:
			trunksegments += rg.getSections()
		trunknames = [n.name() for n in trunksegments]
		for m in range(len(mask)):
			if c.nthCenter(m)[0] in trunknames:
				mask[m]=360
	#drawing
	cv.graph.set_color(cv.getPlotName(c),mask, cs="dir", r="absolute")
	cv.graph.OnDraw()

def _getSynTemplate(syn, diam=4):
	nsyn = len(syn)
	print nsyn
	synloc = ones((nsyn,4), float32)*diam
	for i, s in enumerate(syn):
		loc = s.xyz()
		synloc[i, :3]=loc
	return synloc	

		
def showSynapses(cv, cell=None):
	if not cell:
		cell = cv.getCell()
	syn = cell.getElements("Synapse")
	synloc=_getSynTemplate(syn, 6)
	pn = cv.graph.addSpherePlot(synloc)
	cell._guiinfo["synapse plot name"]=pn
	cv.graph.modelRefs[pn]={'mien.nmpml':cell, 'aux':'synapses', 'synapses':syn}
	cv.graph.OnDraw()		

# def colorSynapses(cv, cell=None):
# 	if not cell:
# 		cell = cv.getCell()
# 	spn= cell._guiinfo.get('synapse plot name')
# 	if not spn:
# 		print "no spn"
# 		print cell._guiinfo
# 		showSynapses(cv, cell)	
# 		spn = cell._guiinfo.get('synapse plot name')
# 	d=cv.askParam([{'Name':'Color using which attribute?', 'Type':str, 'Value':'Direction'}, 
# 					{'Name':'Color Scale Type', 'Type':'List', 'Value':colorscales.keys()}])
# 	if not d:
# 		return 
# 	CS_TYPE=d[1]
# 	syn = cv.graph.modelRefs[spn]['synapses']
# 	sattr = zeros(len(syn), float32)
# 	for i, s in enumerate(syn):
# 		try:
# 			a = float(s.attrib(d[0]))
# 			sattr[i]=a
# 		except:
# 			pass
# 	cv.graph.set_color(spn , sattr, CS_TYPE)
# 	
# 	cv.graph.addColorScale(min=sattr.min(), max=sattr.max(), cs=CS_TYPE)
# 	cv.graph.OnDraw()		
	
def loadSynapseActivationData(self):
	cell=self.getCell()		
	syn = cell.getElements("Synapse")
	if not syn:
		self.report("Cell has no synapses.")
		return
	sevts=self.document.getElements("SynapticEvents")
	if not sevts:
		self.report("Cell has no active synapses.")
		return
	if len(sevts)>1:
		sed={}
		for s in sevts:
			sed[s.upath()]=s
		d=self.askParam([{"Name":"Which Event Queue",
							"Type":"List",
							"Value":sed.keys()}])
		if not d:
			sevts=sevts[0]
		else:
			sevts=sed[d[0]]
	else:
		sevts=sevts[0]
	sevts.findDataElement()
	st=sevts.data.start()+max(sevts.data.getData()[:,0])/sevts.data.fs()
	d=self.askParam([{'Name':'Start', 'Value':sevts.data.start()},
					 {'Name':'Stop', 'Value':st},
					 {'Name':'Step', 'Value':1.0/sevts.data.fs()}	])
	if not d:
		return
	pn=cell._guiinfo.get("synapse plot name")
	if not self.graph.modelRefs.get(pn):
		showSynapses(self, cell)
		pn=cell._guiinfo.get("synapse plot name")	
	self.graph.modelRefs[pn]["TimeSeries"]=sevts.synapseTimeSeries(syn, d[0], d[1], d[2])
	self.graph.modelRefs[pn]["TimeSeriesStep"]=d[2]
	self.graph.showTimeSeries(0, True)		
		
	
	
	
