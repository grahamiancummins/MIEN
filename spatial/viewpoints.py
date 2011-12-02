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


from mien.parsers.nmpml import addPath, createElement, blankDocument
from mien.nmpml.data import newData
from numpy import zeros, array


#vps are stored as 4x3 arrays. The rows are:
# 0: the vector "viewpoint" (location of the camera
# 1: the vector "forward" (facing direction of the camera)
# 2: the vector "up" (vertical roll orientation of the camera)
# 3: [3,0] is "extent" (the width of the view box), [3,1] is "depth" (depth of the view box), [3,2] is ignored

def showView(cv, vp, n='defaultview'):
	d={}
	d['vp']=vp[0,:].copy()
	d['forward']=vp[1,:].copy()
	d['ext']=vp[3,0]
	d['up']=vp[2,:].copy()
	d['depth']=vp[3,1]
	cv.graph.views[n]=d
	cv.graph.presetView(n)
	
def showDefault(cv):
	try:
		vg=cv.document.getInstance('/Data:CVViewpoints')
	except StandardError:
		return
	dv = vg.getElements('Data', {'SampleType':'CVViewpoint', 'DefaultView':True}, depth=1)
	if dv:
		showView(cv, dv[0].getData())		
	
def viewGroup(cv):
	try:
		vg=cv.document.getInstance('/Data:CVViewpoints')
	except StandardError:
		vg=addPath(cv.document, '/Data:CVViewpoints')
		vg.datinit(None, {'SampleTye':'group'})
	return vg

def getCurrentVP(cv):
	g=cv.graph
	view=zeros((4,3))
	view[0,:]=g.viewpoint.copy() 
	view[1,:]=g.forward.copy()
	view[2,:]=g.up.copy()
	view[3,0]=g.extent  
	view[3,1]=g.depthoffield  
	return view
	

def saveView(cv):
	vg=viewGroup(cv)
	pv = vg.getElements('Data', {'SampleType':'CVViewpoint'}, depth=1)
	vpn = "View%03d" % len(pv)
	d=cv.askParam([{'Name':'Name This View', 'Value':vpn}])
	if not d:
		return
	n=d[0]
	nd = newData(None, {'SampleType':'CVViewpoint'})
	vg.newElement(nd)
	nd.setName(n)
	view=getCurrentVP(cv)
	nd.datinit(view)
	cv.report('view added')

def selectView(cv):
	vg=viewGroup(cv)
	pv = vg.getElements('Data', {'SampleType':'CVViewpoint'}, depth=1)
	pvn= [d.name() for d in pv]
	if not pvn:
		cv.report('no saved viewpoints. Using current view')
		vp=getCurrentVP(cv)
		dv=addPath(cv.document, '/Data:CVViewpoints/Data:ViewPoint')
		dv.datinit(vp, {'SampleType':'CVViewpoint'})
		return dv
	if len(pvn)==1:
		return pv[0]
	d=cv.askParam([{'Name':'Which Viewpoint', 'Type':'List', 'Value':pvn}])
	if not d:
		return
	return vg.getElements('Data', d[0], depth=1)[0]

def setView(cv):
	v=selectView(cv)
	if v:
		showView(cv, v.getData(), v.name())
	
def setDefault(cv):
	v=selectView(cv)
	if not v:
		return
	vg=viewGroup(cv)
	pv = vg.getElements('Data', {'SampleType':'CVViewpoint'}, depth=1)
	for e in pv:
		if e==v:
			e.setAttrib('DefaultView',True)
		elif e.attrib('DefaultView'):
			e.setAttrib('DefaultView',False)
	showDefault(cv)
	cv.report('default set')
	
def writeDisplaySpec(cv):
	vpdoc = createElement('CellViewerDisplay', {})
	vp=getCurrentVP(cv)
	attr = {'viewpoint':tuple(vp[0,:]),
		'forward':tuple(vp[1,:]),
		'up':tuple(vp[2,:]),
		'extent':vp[3,0],
		'depth':vp[3,1],
		'background':cv.graph.clearcolor,
		'slices':cv.graph.slices,
		}
	vpdoc.newElement(createElement('ViewerSettings', attr))	
	vpdoc.newElement(createElement('Filter', {'filter':cv.displayfilter}))
	cv.save(doc=vpdoc)

def readDisplaySpec(cv, fn = None):
	spec = cv.load(fname=fn, returndoc=True)
	vs = spec.getElements("ViewerSettings")
	if vs:
		vs = vs[0]
		cv.graph.clearcolor = vs.attrib('background')
		cv.graph.slices = vs.attrib('slices')
		d={}
		d['vp']=array(vs.attrib('viewpoint'))
		d['forward']=array(vs.attrib('forward'))
		d['ext']=vs.attrib('extent')
		d['up']=array(vs.attrib('up'))
		d['depth']=vs.attrib('depth')
		cv.graph.views['fromfile']=d
		cv.graph.presetView('fromfile')
	filt = spec.getElements('Filter')
	if filt:
		filt = filt[0].attrib('filter')
		if filt == 'None':
			filt = None
		if type(filt) in [str, unicode]:
			filt = [filt]
	if filt:
		cv.displayfilter=filt
		cv.addAll()
	else:
		cv.graph.OnDraw()
				
		
	