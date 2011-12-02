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

from mien.wx.base import *
import inspect, time

import mien.spatial.modules
import mien.spatial.widgets
import os, sys, traceback
import re, os, mien.nmpml



GUIS={}

def getDisplayGroup(el, first=True):
	dgs = []
	dg = el.attrib("DisplayGroup", True)
	if dg:
		dgs.append(dg)
	els = el.xpath(True)
	els.reverse()
	for e in els:
		if e.__tag__ == "Group":
			dgs.append(e.upath())
	if first:
		if not dgs:
			return None
		return dgs[0]
	return dgs

def makeCallback(smod, fn):
	def func(event):
		smod.autoWrapper(fn)
		return
	return func

def makeFCall(f, arg):
	def foo(x, report=False):
		if report:
			return arg
		return f(arg)
	return foo
		

import mien.spatial.stacktool
import mien.spatial.cvvis
import mien.blocks
import mien.spatial.animate
import mien.spatial.measure
import mien.spatial.viewpoints

CV_EXT={"Launch Image Stack Tool":mien.spatial.stacktool.launchStackTool,
		"Visualize.Show Mechanisms":mien.spatial.cvvis.showChan,
		"Visualize.Show Masks":mien.spatial.cvvis.showMask,
		"Visualize.Show Best Direction":mien.spatial.cvvis.showBestDir,
		"Visualize.Show Synapses":mien.spatial.cvvis.showSynapses,
		#"Visualize.Color Synapses":mien.spatial.cvvis.colorSynapses,
		"Visualize.Show Synapse Activation":mien.spatial.cvvis.loadSynapseActivationData,
		"Animate.Make Orbit Animation":mien.spatial.animate.orbitAnimation,
		"Animate.Load Cell Voltage Data":mien.spatial.animate.loadCellVoltageData,
		"Animate.Show Time":mien.spatial.animate.showDataAtTime,
		"Animate.Record Time Animation":mien.spatial.animate.animate,
		"Visualize.Show Section Boundaries":mien.spatial.cvvis.showSections,
		"Viewpoints.Save Current View":mien.spatial.viewpoints.saveView,
		"Viewpoints.Select a View":mien.spatial.viewpoints.setView,
		"Viewpoints.Save Display Specification":mien.spatial.viewpoints.writeDisplaySpec,
		"Viewpoints.Load Display Specification":mien.spatial.viewpoints.readDisplaySpec,
		"Viewpoints.Set a Default View":mien.spatial.viewpoints.setDefault,
		"Measure.Show Morphology Stats":mien.spatial.measure.showStats}
	
class CVExtMod:
	def __init__(self, DV):
		self.dv = DV
		self.subguis=[]
		
	def makeSpatialMenu(self):
		funcs={}
		for fn in mien.spatial.modules.FUNCTIONS.keys():
			f=mien.spatial.modules.FUNCTIONS[fn]
			mod=f.__module__
			if mod.startswith('mien.spatial'):
				mod=mod.split('.')[-1]
			sfn=fn.split('.')[-1]
			if not funcs.has_key(mod):
				funcs[mod]={}
			funcs[mod][sfn]=makeCallback(self, fn)
		self.dv.refreshMenu("Spatial", funcs)
		
	def addAll(self):
		for i in range(len(self.subguis)):
			try:
				self.subguis[i].addAll()
			except:
				pass

	def update_self(self, **kwargs):
		for i in range(len(self.subguis)):
			try:
				self.subguis[i].update_self(**kwargs)
			except:
				pass
		pass

	def makeMenus(self):
		m=self.menu("UI_")
		ecmd={}
		ecmd.update(mien.blocks.getBlock('CV'))
		ecmd.update(CV_EXT)	
		for cn in ecmd.keys():
			fc=makeFCall(ecmd[cn], self.dv)
			if not '.' in cn:
				m[cn]=fc
			else:
				fmn=cn.split('.')
				smn='.'.join(fmn[:-1])
				lmn=fmn[-1]
				if not m.has_key(smn):
					m[smn]={}
				m[smn][lmn]=fc
		self.dv.refreshMenu("Extensions", m)
		self.makeSpatialMenu()

	def menu(self, filter):
		d = {}
		for k in dir(self):
			if k.startswith(filter):
				d[k[3:]] = getattr(self, k)
		return(d)

	def report(self, s):
		self.dv.report(s)

	def autoWrapper(self, fn):
		if self.dv.preferences["Always Reload Extensions"]:
			self.UI_ReloadExtensions()
		if GUIS.has_key(fn):
			args=GUIS['fn'](self.dv)
			if args==None:
				return
		else:		
			d=mien.spatial.widgets.getArgChoice(fn, self.dv.document, self.dv)	
			if d:	
				l=self.dv.askParam(d)
				if not l:
					return
				args={}
				for i, di in enumerate(d):
					arg=di['Name']
					if di['Type']==str:	
						try:
							val=eval(l[i])
						except:
							val=l[i]
					else:
						val=l[i]
					args[arg]=val
			else:
				args={}
		func=mien.spatial.modules.FUNCTIONS[fn]
		sa=time.time()
		func(self.dv.document, **args)
		sp=time.time()-sa
		self.dv.update_all(event='rebuild')
		self.report("Completed %s in %.4f sec" % (fn, sp))
		
	def launchExtensionPanel(self, cl):
		w=cl(self.dv)
		w.Show(True)
		self.subguis.append(w)

	def UI_HelpForSpatialFunctions(self, event):
		dlg=mien.spatial.widgets.FunctionFinder(self.dv, module=mien.spatial.modules)
		dlg.CenterOnParent()
		val = dlg.ShowModal()
		if val == wx.ID_OK:
			fn=dlg.GetPath()
			dlg.Destroy()
		else:
			dlg.Destroy()
			self.report("Canceled")
			return
		print fn	
		f=mien.spatial.modules.FUNCTIONS[fn]
		dl=inspect.getsource(f).split(':')[0][4:]
		if f.__doc__:
			dl+="\n\n"+f.__doc__
		self.dv.showText(dl)		

	def UI_ReloadExtensions(self, event=None):
		fl=mien.spatial.modules.refresh()
		self.makeMenus()
		if fl:
			self.report('Reload generated some errors: %s' % (str(fl),))
		else:
			self.report("Reload complete")
		

