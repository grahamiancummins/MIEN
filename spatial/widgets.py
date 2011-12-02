
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
from mien.wx.dialogs import *
import mien.spatial.modules


		

def elemBrowse(master, dict, control):
	v=dict['Viewer']
	if not v:
		return
	els=v.getElements()
	e=[el.upath() for el in els]
	control.SetValue(repr(e))

def singleElemBrowse(master, dict, control):
	v=dict['Viewer']
	if not v:
		return
	e=v.getOneElement()
	control.SetValue(e.upath())
	
	
from mien.interface.widgets import ARGBROWSERS, getArgBrowser, FunctionFinder
ARGBROWSERS_SPATIAL={}
ARGBROWSERS_SPATIAL.update(ARGBROWSERS)

ARGBROWSERS_SPATIAL['elems']=elemBrowse
ARGBROWSERS_SPATIAL['elem']=singleElemBrowse

def lsort(s1,s2):
	return cmp(len(s1), len(s2))

def getDefRange(viewer):
	op=viewer.preferences['Processing Tools Act On']
	r=None
	if op==	'Current View':
		r=viewer.getCurrentView()
	elif op=='Marked Range':
		xm=viewer.graph.xmarkers
		if len(xm)>=2:
			r=viewer.xrange2index(xm[-2]['loc'], xm[-1]['loc'])
	return r
	

def veiwerDefaults(viewer, arglist):	
	'''Special treatment is given to the following list of arguments:
	1) elems: converted to the list of upaths of each element in viewer.getVisible()
	2) point1, point2: converted to viewer._foundSpatialPoint[1] and [0]
	3) cell: if there is only one Cell instance in viewer.getVisible(), convert to the upath of that element
	4) elpt1, elpt2: converted to viewer._foundLastPoint[1] and [0]
	5) secs (or "sections"): converted to the list of upaths of each element in viewer.selected()
	'''
	defv={}
	ellist=viewer.getVisible()
	for a in arglist:
		if a.startswith('elems'):
			defv[a]=[el.upath() for el in ellist]
		if a.startswith('point'):
			try:
				i=int(a[5:])
				v=tuple(viewer._foundSpatialPoint[-i])
				defv[a]=v
			except:
				pass
		if a.startswith('cell'):
			v=[el.upath() for el in ellist if el.__tag__=='Cell']
			if v:
				defv[a]=v[0]
		if a.startswith('elpt'):
			try:
				i=int(a[4:])
				v=tuple(viewer._foundLastPoint[-i])
				defv[a]=v
			except:
				pass
		if a.startswith("sec"):
			v=[e.upath() for e in viewer.selected]
			defv[a]=v
	return defv

def getArgChoice(fn, doc=None, viewer=None, previous={}):
	arglist, defaults, info=mien.spatial.modules.ARGUMENTS[fn]
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
			e['Value']=preval
		else:	
			if vdef.has_key(arg):
				e['Value']=vdef[arg]
			elif i>=nnd:
				e['Value']=defaults[i-nnd]
		if type(e.get('Value'))==bool:
			defv=e['Value']
			e["Type"]="List"
			e['Value']=[True, False]
			e['Default']=defv
		browse=getArgBrowser(arg, ARGBROWSERS_SPATIAL)
		if browse:
 			e['Doc']=doc
			e['Viewer']=viewer
			e['Browser']=browse
		d.append(e)
	return d	
