#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2008-06-20.

# Copyright (C) 2008 Graham I Cummins
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
from mien.wx.dialogs import *
import mien.image.modules

from mien.interface.widgets import ARGBROWSERS, FunctionFinder, getArgBrowser


def veiwerDefaults(viewer, arglist):	
	'''Special treatment is given to the following list of arguments:
	1) images: defaults to the selected images in the viewer list
	'''
	defv={}
	mv=viewer.measurements[:]
	for a in arglist:
		try:
			if a.startswith('images'):
				defv[a]=viewer.getSelected('paths')
			elif a.startswith('image'):
				defv[a]=viewer.getCurrentImage().upath()
			elif a.startswith('xmin'):
				defv[a]=viewer.getBoundaries()[0,0]
			elif a.startswith('xmax'):
				defv[a]=viewer.getBoundaries()[1,0]
			elif a.startswith('ymin'):
				defv[a]=viewer.getBoundaries()[0,1]
			elif a.startswith('ymax'):
				defv[a]=viewer.getBoundaries()[1,1]
			elif a.startswith('frame'):
				defv[a]=viewer._current_display[1]
			elif a.startswith('point'):
				if mv:
					defv[a]=mv.pop(0)
		except:
			pass
	return defv

def ImagesSelect(master, dict, control):
	doc=dict.get("Doc")
	if not doc:
		return
	im=doc.getElements('Data', {'SampleType':'image'})
	if not im:
		return
	im=[i.upath() for i in im]
	l=askParameters(master, [{"Name":"Image Paths",
							  "Type":"Select",
							  "Value":im}])
	if l:
		control.SetValue(repr(l[0]))

def ImageSelect(master, dict, control):
	doc=dict.get("Doc")
	if not doc:
		return
	im=doc.getElements('Data', {'SampleType':'image'})
	if not im:
		return
	im=[i.upath() for i in im]
	l=askParameters(master, [{"Name":"Image Paths",
							  "Type":"List",
							  "Value":im}])
	if l:
		control.SetValue(l[0])



ARGBROWSERS_IMAGE={}
ARGBROWSERS_IMAGE.update(ARGBROWSERS)

def XBrowse(master, dict, control):
	dv=dict.get("Viewer")
	if not dv:
		return	
	x=dv.getBoundaries()[:,0]
	x2=dv.getMarkers()[0]
	x=list(x)
	x.extend(list(x2))
	x.sort()
	l=askParameters(master, [{"Name":"X Coordinate",
							  "Type":"List",
							  "Value":x}])
	if l:
		control.SetValue(str(int(l[0])))

def YBrowse(master, dict, control):
	dv=dict.get("Viewer")
	if not dv:
		return
	x=dv.getBoundaries()[:,1]
	x2=dv.getMarkers()[1]
	x=list(x)
	x.extend(list(x2))
	x.sort()
	l=askParameters(master, [{"Name":"Y Coordinate",
							  "Type":"List",
							  "Value":x}])
	if l:
		control.SetValue(str(int(l[0])))

def PointBrowse(master, d, control):
	dv=d.get("Viewer")
	if not dv:
		return
	x=dict([(repr(m), m) for m in dv.measurements])
	k=x.keys()
	k.sort()
	l=askParameters(master, [{"Name":"Y Coordinate",
							  "Type":"List",
							  "Value":k}])
	if l:
		control.SetValue(repr(x[l[0]]))

ARGBROWSERS_IMAGE["images"]=ImagesSelect
ARGBROWSERS_IMAGE["image"]=ImageSelect
ARGBROWSERS_IMAGE["point"]=PointBrowse
ARGBROWSERS_IMAGE["xmin"]=XBrowse
ARGBROWSERS_IMAGE["xmax"]=XBrowse
ARGBROWSERS_IMAGE["xcoord"]=XBrowse
ARGBROWSERS_IMAGE["ymin"]=YBrowse
ARGBROWSERS_IMAGE["ymax"]=YBrowse
ARGBROWSERS_IMAGE["ycoord"]=YBrowse




def getArgChoice(fn, doc=None, viewer=None, previous={}):
	arglist, defaults, info=mien.image.modules.ARGUMENTS[fn]
	if defaults==None:
		defaults=[]
	nnd=len(arglist)-len(defaults)
	d=[]
	if viewer:
		vdef=veiwerDefaults(viewer, arglist)
	else:
		vdef={}
	for i, arg in enumerate(arglist):
		if previous.has_key(arg):
			preval=previous[arg]
			pvs=True
		else:
			pvs=False
		svl=info['switch values'].get(arg)
		if svl:
			e={"Name":arg,
			"Type":"List",
			"Value":svl}
			if pvs:
				e["Default"]=preval
			d.append(e)
			continue
		e={"Name":arg,
			"Type":str}
		if pvs:
			e['Value']=repr(preval)
		else:	
			if vdef.has_key(arg):
				e['Value']=vdef[arg]
			elif i>=nnd:
				e['Value']=repr(defaults[i-nnd])
		browse=getArgBrowser(arg, ARGBROWSERS_IMAGE)
		if browse:
 			e['Doc']=doc
			e['Viewer']=viewer
			e['Browser']=browse
		d.append(e)
	return d	
