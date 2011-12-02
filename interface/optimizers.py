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
#from mien.wx.base import wx
#import mien.nmpml.ga.gui 
#reload(mien.nmpml.ga.gui)
#from mien.nmpml.ga.gui import GAMonitor, GAAnalyzer
#import threading, os
#from mien.math.sigtools import *

from mien.parsers.nmpml import tagClasses
from mien.interface.widgets import selectTreeElement, FileBrowse
from mien.optimizers.gui import OptMonitor, OptAnalyzer

optclasses=tagClasses()['Optimizer']

def newOpt(gui, elems): 	
	abs=elems[0]
	d = gui.askParam([{"Name":"Type of Optimizer?",
								"Type":'List',
								"Value":optclasses}])
	if not d:
		return
	ct=d[0]	
	atr=gui.getElemAttribs(ct)
	new=gui.createElement(ct, atr)
	ps=gui.createElement('ParameterSet', {})
	new.newElement(ps)
	er=gui.createElement('ElementReference', {"Target":abs.upath()})
	new.newElement(er)		
	gui.document.newElement(new)
	gui.update_all(object=new, event="Create")
	
def getPars(gui, elems):
	ps=elems[0]
	pars=gui.document.getElements('Number') 			
	if len(pars)<3:
		pd=dict([(p.upath(), p) for p in pars])
 		d = gui.askParam([{"Name":"Choose Parameters",
								"Type":'Select',
								"Value":pd.keys()}])
		pars=[]
		if d:
			pars=[pd[q] for q in d[0]]
	else:	
		pars=selectTreeElement(gui, {'multiple':True, 'filter':['Number', 'MienBlock']})
	if not pars:
		return
	for e in ps.elements[:]:
		e.sever()
	npars=[]
	for p in pars:
		if p.__tag__=='Number':
			npars.append(p)
		else:
			npars.extend(p.getElements('Number'))
	for p in npars:
		v=p.getValue()
		try:
			v=float(v)
		except:
			v=0.0
		if None in [p.attrib('Range'), p.attrib("Precision")]:
			if p.attrib('Range'):
				rmin=min(p.attrib('Range'))
				rmax=max(p.attrib('Range'))
			else:
				rmin=0.0
				rmax=1.0
			prec=p.attrib("Precision") or 0.0	
	 		d = gui.askParam([{"Name":"%s (%.4f)" % (p.upath(),v),
								"Type":'Label'},
								{"Name":"Minimum",
								"Value":rmin},
								{"Name":"Maximum",
								"Value":rmax},
								{"Name":"Precision",
								"Value":prec}])
			if not d:
				d=[rmin, rmax, prec]
			r=[float(d[0]), float(d[1])]
			p.setAttrib('Range', r)	
			p.setAttrib('Precision', d[2])
		er=gui.createElement('ElementReference', {"Target":p.upath()})
		ps.newElement(er)		
	gui.update_all(object=ps, event="Rebuild")

def getParsFromFile(gui, elems):
	ps=elems[0]
	d = gui.askParam([{"Name":"Parameter File",
							"Type":str,
							"Browser":FileBrowse}])
	if not d:
		return
	try:
		s=file(d[0]).readlines()
	except:
		gui.report("cant read parameter file")
		return
	fpl=[]
	try:
		for l in s:
			ll=l.split()
			if len(ll)>1:
				pn=ll[0]
				mi, ma, pr = map(float, ll[1:])
				fpl.append([pn, mi, ma, pr])
	except:
		gui.report("cant parse parameter file. Each non-empty line must contain 'name min max precision' lists separated by spaces. ")
		return
	abst=ps.container.getTypeRef("AbstractModel")[0].target()
	for z in ps.getElements('ElementReference', depth=1):
		z.sever()
	for p in fpl:
		par=abst.getElements('Number', p[0])
		if len(par)>1:
			gui.report("parameter name %s is non unique. Skipping." % (p[0],))
		elif len(par)==0:
			gui.report("parameter name %s is not found. Skipping." % (p[0],))
		else:
			par=par[0]
			par.setAttrib('Range', [p[1], p[2]])
			par.setAttrib('Precision', p[3])
			er=gui.createElement('ElementReference', {"Target":par.upath()})
			ps.newElement(er)
	gui.update_all(object=ps, event="Rebuild")
	

def testOpt(gui, elems):		
	opt=elems[0]
	data=opt.test()
	gui.report("Test OK: %s" % (str(data),))
	
def evalOpt(gui, elems):
	opt=elems[0]
	d=gui.askParam([{'Name':'Params', 'Type':str}])
	if not d:
		return
	import numpy	
	d=numpy.array(map(float, d[0].split()))
	f=opt.local_eval(d)
	gui.report("Eval OK: %s" % (str(f),))
		
	
def runOpt(gui, elems):	
	g=OptMonitor(gui, elems[0])
	g.Show(True)

def optAnal(gui, elems):
	g=OptAnalyzer(gui, elems[0])
	g.Show(True)

def defGAPars(gui, elems):
	g = elems[0]
	dp = {
				"Maximize":0,
				"MaxTime":1.0,
				"ThreadSafe":1,
				"EvalConditions":0,
				"Fitness":'error', 
				"File":'ga',
				"TargetFitness":0,					
				'MutationProbability':.1, 
				'CrossoverProbability':.7, 
				'PopulationSize':100,
				'Cull':200.0,
				  'CompeteToReplace':False,
				  'Death':"Worst",
				  'NewBlood':001,
				  'TransposeProbability':0,
				  'SelectionMethod':"Ordinal",
				  'MaxDuplicates':5,
				  'MutationRange':0.0,
				  'MinimumBreedInterval':0
	}
	for k in dp:
		g.setAttrib(k, dp[k])
	

def isOpt(l):
	if not len(l)==1:
		return False
	if str(l[0]) in optclasses:
		return True
	return False		

ME={}
MECM={"Create Optimizer":(newOpt, "AbstractModel"),
	"Assign Parameters": (getPars,"ParameterSet"),
	"Read Param File": (getParsFromFile,"ParameterSet"),
	'Test Optimizer':(testOpt, isOpt),
	'Evaluate Parameter Set':(evalOpt, isOpt),
	"Optimizer Run Controls":(runOpt,isOpt),
	"Set Default Parameters":(defGAPars, 'GeneticAlgorithm'),
	"Optimizer Analysis":(optAnal, isOpt) 
}

 		
