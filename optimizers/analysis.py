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
import mien.optimizers.arraystore as ast
from mien.math.sigtools import *
import os, cPickle


def makeHist(samps, t):
	num = zeros(t.shape[0], t.dtype.char)
	past = 0
	if len(samps)>0:
		for i in range(t.shape[0]):
			env = nonzero(samps<t[i]).shape[0]
			num[i] = env - past
			past = env
	return concatenate([t[:,NewAxis],num[:,NewAxis]], 1)	



def make2dHist(a, b1, b2):
	b1=arange(b1).astype(Float32)
	b1=(b1/b1.max())*(a[:,0].max()-a[:,0].min())
	b1=b1+a[:,0].min()
	b2=arange(b2).astype(Float32)
	b2=(b2/b2.max())*(a[:,1].max()-a[:,1].min())
	b2=b2+a[:,1].min()
	out=zeros((b1.shape[0], b2.shape[0]), a.dtype.char)
	for i in range(1, b1.shape[0]):
		inds=nonzero(logical_and(a[:,0]>=b1[i-1], a[:,0]<=b1[i]))
		evts=take(a[:,1], inds)
		if not len(evts):
			continue
		q=makeHist(evts, b2)
		out[i, :]=q[:,1]
	return out

class GuiAnalysisModule:
	def __init__(self, gui):
		self.gui=gui

	def makeMenus(self):
		self.gui.refreshMenu("Analysis", self.menu("UI_"))

	def menu(self, filter):
		d = {}
		for k in dir(self):
			if k.startswith(filter):
				d[k[3:]] = getattr(self, k)
		return(d)

	def UI_removeDuplicates(self, event):
		dat=self.gui.data.data[:,1:]
		unique=[0]
		for i in range(1, dat.shape[0]):
			if any(alltrue(take(dat, unique)==dat[i])):
				continue
			unique.append(i)
		ne=dat.shape[0]		
		self.gui.data.data=take(self.gui.data.data, array(unique))
		nnd=self.gui.data.data.shape[0]
		nd=ne-nnd
		self.gui.report("found and removed %i duplicates" % nd)
		self.gui.showInfo()
	
	def UI_addCondition(self, event):
		l=self.gui.askParam([{"Name":"Parameter",
							"Type":"List",
							"Value":self.gui.data.labels},
							{"Name":"Min",
							"Value":-1.0},
							{"Name":"Max",
							"Value":100.0}])
		if not l:
			return
		colid=self.gui.data.labels.index(l[0])
		self.gui.condition[l[0]]=(l[1], l[2])
		self.gui.showInfo()
	
	def UI_clearConditions(self, event):
		self.gui.condition={}
		self.gui.showInfo()

	def UI_showConditons(self, event):
		s=""
		for k in self.gui.condition.keys():
			v=self.gui.condition[k]
			s+="%s %.4f to %.4f\n" % (k, v[0], v[1])
		self.gui.report(s)	

	def UI_cropToConditions(self, event):
		dat=self.gui.getConditionalData()
		self.gui.data.data=dat
		self.gui.condtion={}
		self.gui.showInfo()
		
	def UI_showParameterStats(self, event):
		dat=self.gui.getConditionalData()
		out=[]
		for i,l in enumerate(self.gui.data.labels):
			d=dat[:,i]
			s=(l, d.min(), d.max(), d.mean(), d.stddev())
			out.append("%s: min: %.4g, max:%.4g, mean:%.4g, std:%.4g" % s)
		s="\n".join(out)
		print s
			

	def UI_parVsFit(self, event=None):
		n = self.gui.askUsr("Which parameter", self.gui.data.labels)
		i = self.gui.data.labels.index(n)
		a= take(self.gui.getConditionalData(),[0,i], 1)
		g=self.gui.makeGraph()
		g.addPlot(a, n, style="points")

	def UI_fitVsPar(self, event=None):
		n = self.gui.askParam([{"Name":"Which parameter",
								"Type":"List",
								"Value":self.gui.data.labels},
							   {"Name":"Number of points",
								"Value":100}])
		i = self.gui.data.labels.index(n[0])
		npts=n[1]
		a= take(self.gui.getConditionalData(),[i,0], 1)
		ind=argsort(a[:,0])
		a=take(a, ind)
		pstep=(a[-1,0]-a[0,0])/npts
		pr=arange(a[0,0], a[-1,0], pstep)
		fmin=zeros(pr.shape, Float32)
		fmax=zeros(pr.shape, Float32)
		fmean=zeros(pr.shape, Float32)
		last=0
		for i in range(pr.shape[0]):
			next=nonzero(a[:,0]>pr[i])[0]
			if next<=last:
				if i>0:
					fmin[i]=fmin[i-1]
					fmax[i]=fmax[i-1]
					fmean[i]=fmean[i-1]
			else:
				fits=a[last:next,1]
				fmin[i]=fits.min()
				fmax[i]=fits.max()
				fmean[i]=fits.mean()
			last=next	
		
		g=self.gui.makeGraph()
		a=transpose(array([pr, fmin]))
		g.addPlot(a, "min")
		a=transpose(array([pr, fmax]))
		g.addPlot(a, "max")
		a=transpose(array([pr, fmean]))
		g.addPlot(a, "mean")

		
	def UI_fitVsPar1Par2(self, event=None):
		n = self.gui.askParam([{"Name":"First Parameter",
								"Type":"List",
								"Value":self.gui.data.labels},
							   {"Name":"Second Parameter",
								"Type":"List",
								"Value":self.gui.data.labels},
							   {"Name":"Show",
								"Type":"List",
								"Value":["min", "max", "mean"]},
							   {"Name":"Width",
								"Value":2},
							   ])
		i = self.gui.data.labels.index(n[0])
		j = self.gui.data.labels.index(n[1])
		a= take(self.gui.getConditionalData(),[i,j, 0], 1)		
		g=self.gui.makeGraph()
		
		pn=g.addPlot(a[:,:2], "fit", style="points", stat=n[2],width=n[3])
		pad = (a[:,2].max()-a[:,2].min())/5
		ran=(a[:,2].min()-pad,a[:,2].max())
		g.set_color(pn, a[:,2],cs='hot', r=ran)
		

	def UI_Histogram(self, event):
		n = self.gui.askUsr("Which parameter", self.gui.data.labels)
		i = self.gui.data.labels.index(n)
		a= self.gui.getConditionalData()[:,i]
		g=self.gui.makeGraph()
		t=a.max()-a.min()
		p=t*.05
		t=arange(a.min()-p, a.max()+p, p)
		a=makeHist(a, t)
		g.addPlot(a, n, style="hist")


	def UI_2DHist(self, event):
		n = self.gui.askParam([{"Name":"Conditioning Parameter",
								"Type":"List",
								"Value":self.gui.data.labels},
							   {"Name":"Varying Parameter",
								"Type":"List",
								"Value":self.gui.data.labels}
							   ])

		i = self.gui.data.labels.index(n[0])
		i2= self.gui.data.labels.index(n[1])
		a= take(self.gui.getConditionalData(), [i,i2], 1)
		g=self.gui.makeGraph()
		a=make2dHist(a, 10, 20)
		print a
		g.addPlot(a, 'hist', style="ScalingImage", colorrange=(a.min(), a.max()))



# 
# import os, re
# from mien.math.sigtools import *
# from cPickle import load, dump
# from string import join
# 
# try:
# 	import mien.wx.graphs.graph
# 	reload(mien.wx.graphs.graph)
# 	from mien.wx.graphs.graph import Graph, wx
# except:
# 	print "gui not avalable"
# 
# def genFitTab(pnames, pranges, patrs, chroms, data):
# 	checkatrs=[]
# 	for i, a in enumerate(patrs):
# 		if a.get("Step"):
# 			checkatrs.append(i)
# 	ft=[]
# 	pnames=["id", "fit", "reps"]+pnames
# 	if len(data.keys())>0:
# 		datl=len(data[data.keys()[0]])
# 		pnames.extend(["data%i" % x for x in range(datl)])
# 	else:
# 		datl=0
# 	ids=chroms.keys()
# 	ids=[int(x) for x in ids]
# 	ids.sort()
# 	ft=zeros((len(ids),len(pnames)), Float32)
# 	maxrow=0
# 	for i, k in enumerate(ids):
# 		fit = chroms[str(k)][0]
# 		if fit<0:
# 			continue
# 		val = chroms[str(k)][1]
# 		row = -1
# 		if i>0:
# 			dup=nonzero1d(ft[:i,1]==fit)
# 			if dup.shape[0]:
# 				pds=take(ft, dup)
# 				pds=pds[:,3:-datl]
# 				match=alltrue(pds==val,1)
# 				if any(match):
# 					row = nonzero1d(match)[0]
# 					row = dup[row]
# 		if row==-1:
# 			#print "row %i is new. %i unique rows" %( i, maxrow)		
# 			ft[maxrow,0]=k
# 			ft[maxrow,1]=fit
# 			ft[maxrow,2]=1
# 			if datl:
# 				ft[maxrow,3:-datl]=val.astype(Float32)
# 				try:
# 					d=data[str(k)]
# 					d=array(d, ft.dtype.char)
# 					ft[maxrow,-datl:]=d
# 				except:
# 					#print "cant append data for unit %i" % k
# 					pass
# 			else:
# 				ft[maxrow,3:]=val.astype(Float32)
# 			maxrow+=1
# 		else:
# 			#print "row %i duplicates %i" % (i, row)
# 			ft[row,2]+=1
# 	ft = ft[:maxrow,:]
# 	ft[:,1]
# 	val = ft[:,3:-datl or None]
# 	val =(val.astype(Float64)+32768)/65535.0
# 	val=val*(pranges[:,1]-pranges[:,0]) + pranges[:,0]
# 	for i in checkatrs:
# 		at=patrs[i]
# 		s = at.get("Step")
# 		if s:
# 			s=float(s)
# 			m=pranges[i][0]
# 			val[:,i]=lock2step(val[:,i],m,s)
# 	ft[:,3:-datl or None]=val.astype(Float32)
# 	return DataSet(ft, {"Labels":pnames})
# 
# 
# 
# 
# class GAAnalMod:
# 	
# 	def __init__(self, anal):
# 		self.gui = anal
# 		self.gui.refreshMenu("Analysis", self.menu())
# 
# 	def menu(self):
# 		d = {}
# 		for k in dir(self):
# 			if k.startswith("UI_"):
# 				d[k[3:]] = getattr(self, k)
# 		return(d)
# 
# 	def report(self, s):
# 		self.gui.report(s)
# 
# 	def makeGraph(self):
# 		bar = {'size':(600,600), 'style':wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE}
# 		frame = wx.Frame(self.gui, -1, "GA Analysis Graph", **bar)
# 		frame.g = Graph(frame, -1)
# 		frame.Show(True)
# 		return frame.g
# 
# 	def genfittab(self):
# 		ft=[]
# 		pnames, pranges, patr=self.gui.ga.parRanges()
# 		return genFitTab(pnames, pranges, patr, self.gui.chroms, self.gui.data)
# 
# 	def UI_selectRange(self, event=None):
# 		fit=self.gui.fittab.data[:,1]
# 		self.report("min %.3f, mean%.3f, max%.3f" % (fit.min(), fit.mean(), fit.max()))
# 		n = self.gui.askParam([{"Name":"Min fit",
# 								"Value":fit.min()},
# 							   {"Name":"Max fit",
# 								"Value":fit.max()}])
# 		ind=nonzero1d((fit>=n[0])*(fit<=n[1]))
# 		if ind.shape[0]==0:
# 			self.report('no units in range')
# 			return
# 		dat = take(self.gui.fittab.data, ind)
# 		self.gui.fittab.data=dat
# 		self.report("selected %i units" % self.gui.fittab.data.shape[0])
# 
# 
# 	def UI_parVsFit(self, event=None):
# 		n = self.gui.askUsr("Which parameter", self.gui.fittab.labels)
# 		i = self.gui.fittab.labels.index(n)
# 		a= take(self.gui.fittab.data,[1,i], 1)
# 		g=self.makeGraph()
# 		g.addPlot(a, n, style="points")
# 
# 	def UI_fitVsPar(self, event=None):
# 		n = self.gui.askParam([{"Name":"Which parameter",
# 								"Type":"List",
# 								"Value":self.gui.fittab.labels},
# 							   {"Name":"Number of points",
# 								"Value":100}])
# 		i = self.gui.fittab.labels.index(n[0])
# 		npts=n[1]
# 		a= take(self.gui.fittab.data,[i,1], 1)
# 		ind=argsort(a[:,0])
# 		a=take(a, ind)
# 		pstep=(a[-1,0]-a[0,0])/npts
# 		pr=arange(a[0,0], a[-1,0], pstep)
# 		fmin=zeros(pr.shape, Float32)
# 		fmax=zeros(pr.shape, Float32)
# 		fmean=zeros(pr.shape, Float32)
# 		last=0
# 		for i in range(pr.shape[0]):
# 			next=nonzero1d(a[:,0]>pr[i])[0]
# 			if next<=last:
# 				if i>0:
# 					fmin[i]=fmin[i-1]
# 					fmax[i]=fmax[i-1]
# 					fmean[i]=fmean[i-1]
# 			else:
# 				fits=a[last:next,1]
# 				fmin[i]=fits.min()
# 				fmax[i]=fits.max()
# 				fmean[i]=fits.mean()
# 			last=next	
# 		
# 		g=self.makeGraph()
# 		a=transpose(array([pr, fmin]))
# 		g.addPlot(a, "min")
# 		a=transpose(array([pr, fmax]))
# 		g.addPlot(a, "max")
# 		a=transpose(array([pr, fmean]))
# 		g.addPlot(a, "mean")
# 
# 		
# 	def UI_fitVsPar1Par2(self, event=None):
# 		n = self.gui.askParam([{"Name":"First Parameter",
# 								"Type":"List",
# 								"Value":self.gui.fittab.labels},
# 							   {"Name":"Second Parameter",
# 								"Type":"List",
# 								"Value":self.gui.fittab.labels},
# 							   {"Name":"Show",
# 								"Type":"List",
# 								"Value":["min", "max", "mean"]},
# 							   {"Name":"Width",
# 								"Value":2},
# 							   ])
# 		i = self.gui.fittab.labels.index(n[0])
# 		j = self.gui.fittab.labels.index(n[1])
# 		a= take(self.gui.fittab.data,[i,j, 1], 1)		
# 		g=self.makeGraph()
# 		
# 		pn=g.addPlot(a[:,:2], "fit", style="points", stat=n[2],width=n[3])
# 		pad = (a[:,2].max()-a[:,2].min())/5
# 		ran=(a[:,2].min()-pad,a[:,2].max())
# 		g.set_color(pn, a[:,2],cs='hot', r=ran)
# 		
#  
