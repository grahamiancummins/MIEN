
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
import mien.dsp.modules

from mien.interface.widgets import ARGBROWSERS, FunctionFinder, getArgBrowser, browseTree

def ChannelBrowse(master, dict, control):
	data=dict.get("DataSet")
	if data:
		labels = data.getLabels()
	else:
		labels = ["Channel%i" % x for x in range(10)]
	l=askParameters(master, [{"Name":"Channels",
							  "Type":"Select",
							  "Value":labels}])
	if l:
		chans = map(lambda x: labels.index(x), l[0])
		control.SetValue(repr(chans))

def OneChannelBrowse(master, dict, control):
	data=dict.get("DataSet")
	if data:
		labels = data.getLabels()
	else:
		labels = ["Channel%i" % x for x in range(10)]
	l=askParameters(master, [{"Name":"Channels",
							  "Type":"List",
							  "Value":labels}])
	if l:
		chan=labels.index(l[0])
		control.SetValue(repr(chan))



def XMarkBrowse(master, dict, control):
	dv=dict.get("Viewer")
	if dv:
		locs = ["%.7g" % x['loc'] for x in dv.graph.xmarkers]
		locs.append("%.7g" %  (dv.graph.limits[0],))
		locs.append("%.7g" %  (dv.graph.limits[1],))
	else:
		return
	l=askParameters(master, [{"Name":"X Coordinate",
							  "Type":"List",
							  "Value":locs}])
	if l:
		control.SetValue(repr(float(l[0])))

		
def YMarkBrowse(master, dict, control):
	dv=dict.get("Viewer")
	if not dv:
		return
	locs = [x['loc'] for x in dv.graph.ymarkers]
	if not locs:
		return 
	locstr={}
	for l in locs:
		locstr["%.5g" % l]=l
	off={}	
	for c in dv._channels:
		offsets=dv.offsets.get(c[0], (0.0, 0.0, 1.0))
		if offsets[0] or offsets[2]!=1.0:
			off[c[0]]=(offsets[0], offsets[2])
	pd=	[{"Name":"Y Coordinate",
		"Type":"List",
		"Value":locstr.keys()}]
	if off:
		cos=["No"]+off.keys()
	pd.append( {"Name":"Correct coordinates for view offsets?",
				"Type":"List",
				"Value":cos})
	l=askParameters(master, pd) 
	if l:
		tv=locstr[l[0]]
		if off and l[1]!="No":
			od=off[l[1]]
			tv = (tv- od[0])/od[1]
		control.SetValue(repr(tv))

class BogoControl:
	def __init__(self):
		self.value=None
		
	def SetValue(self, v):
		self.value=v
	
def bogoBrowse(viewer, bf):
	dic={'DataSet':viewer.data, 'Viewer':viewer}
	con=BogoControl()
	bf(viewer, dic, con)
	return eval(con.value)
	
def SubDataBrowse(master, dict, control):
	data=dict.get("DataSet")
	if not data:
		return
	d=data.getHierarchy().keys()
	l=askParameters(master, [{"Name":"SubData Path",
							  "Type":"List",
							  "Value":d}])
	if l:
		control.SetValue(repr(l[0]))
		
def NewPathBrowser(	master, dict, control):
	data=dict.get("DataSet")
	if not data:
		return
	d=data.getHierarchy().keys()
	l=askParameters(master, [{"Name":"SubData Path",
							  "Type":"Prompt",
							  "Value":d}])
	if l:
		control.SetValue(repr(l[0]))
	
def AttribBrowser(master, dict, control):
	data=dict.get("DataSet")
	if not data:
		return
	l=askParameters(master, [{"Name":"Attribute Name",
							  "Type":"Prompt",
							  "Value":data.attributes.keys()}])
	if l:
		control.SetValue(repr(l[0]))
		

def EventsBrowse(master, dict, control):
	data=dict.get("DataSet")
	if not data:
		return
	events=[d.dpath() for d in data.getElements('Data') if 'events' in d.stype()]
	if not events:
		return
	l=askParameters(master, [{"Name":"SubData Path",
							  "Type":"Select",
							  "Value":events}])
	if l:
		control.SetValue(repr(l[0]))
				
def DataSelectBrowse(master, dict, control):
	data=dict.get("DataSet")
	if not data:
		return	
	sel=[None, None, None]
	d=data.getHierarchy().keys()
	if len(d)>1:			
		l=askParameters(master, [{"Name":"SubData Path",
								  "Type":"List",
								  "Value":d}])
		if not l:
			return
		if l[0]!='/': 
			sel[0]=l[0]
			data=data.getSubData(l[0])
	labels = data.getLabels()[:]
	viewer=dict.get('Viewer')
	if viewer:
		defran=getDefRange(viewer) or (0, data.shape()[0])
		defran=list(defran)
		locs = list(viewer.getMarkIndexes())
		dfs=defran[0]
		dls=defran[1]
		defran.extend(locs)
		fsd={"Name":"First Sample",
			"Type":'Prompt',
			"Default":dfs, 
			"Value":defran}
		lsd={"Name":"Last Sample",
			"Type":'Prompt',
			"Default":dls, 
			"Value":defran}
	else:
		fsd={"Name":"First Sample",
			"Value":0}
		lsd={"Name":"Last Sample",
			"Value":data.shape()[0]}


	l=askParameters(master, [{"Name":"Channels",
							  "Type":"Select",
							  "Value":labels},
							  fsd,lsd])
	if l:
		if l[0] and len(l[0])<len(labels):
			sel[1]=[labels.index(x) for x in l[0]]
		r1=int(l[1])
		r2=int(l[2])
		if r1>0 or r2<data.shape()[0]:
			sel[2]=(r1, r2)
		control.SetValue(repr(sel))


ARGBROWSERS_DSP={}
ARGBROWSERS_DSP.update(ARGBROWSERS)
ARGBROWSERS_DSP.update({"chans":ChannelBrowse,
			 "chan":OneChannelBrowse,
			 "xcoord":XMarkBrowse,
			 "ycoord":YMarkBrowse,
			 "thresh":YMarkBrowse,
			 "sel":DataSelectBrowse,
			 "select":DataSelectBrowse,
			 "dpath":SubDataBrowse,
			 "events":EventsBrowse,
			 "newpath":NewPathBrowser,
			 'attrib':AttribBrowser})


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
	

def getArgChoice(fn, data=None, viewer=None, previous={}):
	arglist, defaults, info=mien.dsp.modules.ARGUMENTS[fn]
	if defaults==None:
		defaults=[]
	nnd=len(arglist)-len(defaults)
	d=[]
	if viewer:
		xcd = [x['loc'] for x in viewer.graph.xmarkers]
		xcd.append("%.7g" %  (viewer.graph.limits[0],))
		xcd.append("%.7g" %  (viewer.graph.limits[1],))
		ycd = [x['loc'] for x in viewer.graph.ymarkers]
	else:
		xcd=ycd=None
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
			defv=None
			if viewer and arg.startswith('select'):
				defv=(None, None, getDefRange(viewer))
			elif arg.startswith('xco') and xcd:
				defv=float(xcd.pop(0))
			elif (arg.startswith('yco') or arg.startswith('thresh') ) and ycd:
				defv=float(ycd.pop(0))
			elif i>=nnd:
				defv=repr(defaults[i-nnd])
			if defv:
				e['Value']=defv
		browse=getArgBrowser(arg, ARGBROWSERS_DSP)
		if not data and not browse in [FileBrowse, browseTree]:
			browse=None
		if not viewer and browse in [XMarkBrowse,YMarkBrowse]:
			browse=None
		if browse:
 			e['DataSet']=data
			e['Viewer']=viewer
			e['Browser']=browse
		if not e["Type"]:
			e["Type"]=='flex'	
		d.append(e)
	return d	
