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


from mien.wx.graphs.graph import Graph
from mien.wx.base import *
import inspect, time

from mien.datafiles.dataset import *
import mien.blocks
import mien.dsp.modules
import mien.dsp.widgets
from mien.interface.widgets import selectTreePath

DV_EXT={}

def makeCallback(smod, fn):
	def func(event):
		smod.autoWrapper(fn)
		return
	return func

class DVSignalMod:
	def __init__(self, DV):
		self.dv = DV
		self.sdsv=None

	def makeDspMenu(self):
		funcs={}
		for fn in mien.dsp.modules.FUNCTIONS.keys():
			f=mien.dsp.modules.FUNCTIONS[fn]
			mod=f.__module__
			if mod.startswith('mien.dsp'):
				mod=mod.split('.')[-1]
			sfn=fn.split('.')[-1]
			if not funcs.has_key(mod):
				funcs[mod]={}
			funcs[mod][sfn]=makeCallback(self, fn)
		self.dv.refreshMenu("Dsp", funcs)


	def makeMenus(self):
		self.dv.refreshMenu("Extensions", self.menu("UI_"))
		self.makeDspMenu()


	def menu(self, filter):
		d = {}
		for k in dir(self):
			if k.startswith(filter):
				d[k[3:]] = getattr(self, k)
		ef={}
		ef.update(mien.blocks.getBlock('DV'))
		ef.update(DV_EXT)
		for mn in ef.keys():
			fc=mien.blocks.makeFCall(ef[mn], self.dv)
			d[mn]=fc
		return(d)

	def report(self, s):
		self.dv.report(s)

	def autoWrapper(self, fn):		
		if self.dv.preferences["Always Reload Extensions"]:
			self.UI_ReloadDSPFunctions()
		d=mien.dsp.widgets.getArgChoice(fn, self.dv.data, self.dv)	
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
		func=mien.dsp.modules.FUNCTIONS[fn]
		sa=time.time()
		if not self.dv.data or self.dv.data.__tag__!="Data":
			dat=newData(None, {'SampleType':'group'})
			self.dv.document.newElement(dat)
			self.dv.report('Auto-generating Data element')
			self.dv.data=dat
			self.dv.onNewData()
		func(self.dv.data, **args)
		sp=time.time()-sa
		self.dv.update_all(object=self.dv.data)
		self.report("Completed %s in %.4f sec" % (fn, sp))

	def subPlot(self, data):
		plots=self.dv.getAllGuis()
		plots=[x for x in plots if isinstance(x, self.dv.__class__) and x!=self.dv]
		if plots:
			pn=["%i:%s" % (i, n.GetTitle()) for i,n in enumerate(plots)]
			pn=["New"]+pn
			d=self.dv.askParam([{"Name":"Which Plot?",
			                     "Type":"List",
			                     "Value":pn}])
			if d and d[0]!="New":	
				ind=pn.index(d[0])
				plot=plots[ind-1]
				plot.dataImport(data, True)
				return 
		p=self.dv.spawnViewer(data, zoom=True)
		n=len(plots)
		p.SetTitle("Output Plot %i" % n)

	def selectRange(self):
		return mien.dsp.widgets.bogoBrowse(self.dv, mien.dsp.widgets.DataSelectBrowse)

	def UI_HelpForDspFunctions(self, event):
		dlg=mien.dsp.widgets.FunctionFinder(self.dv, module=mien.dsp.modules)
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
		f=mien.dsp.modules.FUNCTIONS[fn]
		dl=inspect.getsource(f).split(':')[0][4:]
		if f.__doc__:
			dl+="\n\n"+f.__doc__
		self.dv.showText(dl)

	def UI_SearchDspFunctions(self, event):
		d = self.dv.askParam([{"Name": "Search for string", 'Type':str}])
		if not d:
			return
		s = d[0]
		for fn in mien.dsp.modules.FUNCTIONS.keys():
			f= mien.dsp.modules.FUNCTIONS[fn]
			dstring = f.__doc__ or ""
			if s in fn.lower() or s in dstring:
				self.dv.report(fn)

	def UI_CalcStats(self, event):
		sel=self.selectRange()
		dat=getSelection(self.dv.data, sel)
		for ci in range(dat.shape[1]):
			c=dat[:,ci]
			print "%3i: min %7.4g max %7.4g mean %7.4g std %7.4g" % (ci, c.min(), c.max(), c.mean(), c.std())			

	def UI_ReloadDSPFunctions(self, event=None):
		relaunch=[]		
		bl=mien.blocks.getBlock('DV')
		for widg in self.dv.GetChildren():
			for cn in bl.keys():
				try:
					cl=bl[cn]
					if isinstance(widg, cl):
						relaunch.append(cn)
						widg.onClose(None)
						break
				except:
					pass

		fl=mien.dsp.modules.refresh()
		self.makeMenus()
		if fl:
			self.report('Reload generated some errors: %s' % (str(fl),))
		else:
			self.report("Reload complete")
		bl=mien.blocks.getBlock('DV')
		for cn in relaunch:
			bl[cn](self.dv)

	def UI_DisplaySubData(self, event=None):
		d=selectTreePath(self.dv, {'data':True, 'filter':['Data']})
		if not d:
			return
		d=self.dv.data.getSubData(d)
		self.subPlot(d)

	def UI_CreateEventsFromMarks(self, event):
		locs = self.dv.getMarkIndexes()
		if not locs.shape[0]:
			self.report('No X Markers')
			return 
		l=self.dv.askParam([{'Name':'Path For New Events', 'Value':'/MarkerEvents'}])
		if not l:
			return
		if self.dv.data.getSubData(l[0]):
			self.report('Selected Path Exists. Deleting it')
			sd=self.dv.data.getSubData(l[0])
			del(sd)
		self.dv.data.createSubData(l[0], locs, {'SampleType':'events', 'SamplesPerSecond':self.dv.data.fs(), 'Lables':['XMarkerLocations']})	
		self.dv.update_all()

	def UI_HideData(self, event):
		extr=mien.dsp.modules.FUNCTIONS['subdata.extract']
		select=self.selectRange()
		if select:
			name=self.dv.data.getSubData(select[0]).name()
			extr(self.dv.data, select, "/hidden/%s" % (name,), True)
		self.dv.update_all()

	def UI_ShowData(self, event):
		hide=[]
		keys=self.dv.data.getHierarchy().keys()
		hide=[p for p in keys if 'hidden' in p and len(p)>7]
		if not hide:
			self.report('No hidden data')
			return
		l=self.dv.askParam([{'Name':'Data Element','Type':'List', 'Value':hide}])
		if not l:
			return
		mv=mien.dsp.modules.FUNCTIONS['subdata.move']
		mv(self.dv.data, l[0], '/')
		self.dv.update_all()


# 	def assign(self):
# 		chans=self.dv.channames()
# 		d=self.dv.askParam([{"Name":"Stimulus 0/180",
# 						  "Type":"List",
# 						  "Value":chans},
# 						 {"Name":"Stimulus L/R",
# 						  "Type":"List",
# 						  "Value":chans}])
# 		if not d:
# 			return
# 		self.chan_ids=[]
# 		self.chan_ids.append(chans.index(d[0]))
# 		self.chan_ids.append(chans.index(d[1]))
# 		self.report("Channel IDs assigned")
# 
# 	def UI_TrajectoryPlot(self, event=None):
# 		if not self.chan_ids:
# 			self.assign()
# 		g = self.subPlot()	
# 		g.fixAR = 1.0
# 		
# 		t=self.dv.datafile.get_x()
# 		l=self.dv.graph.limits
# 		start = self.dv.datafile.xind(l[0])
# 		stop = self.dv.datafile.xind(l[1])
# 		c=self.dv.datafile.data[start:stop]
# 		x=c[:,self.chan_ids[1]]
# 		y=c[:,self.chan_ids[0]]
# 		a=transpose(array((x,y)))
# 		g.addPlot(a, name="trajectory")
# 		inds=[]
# 		for m in self.dv.graph.xmarkers:
# 			ti =m['loc']
# 			if ti>l[0] and ti<l[1]:
# 				inds.append(self.dv.datafile.xind(ti))
# 		sx=take(x, inds)	
# 		sy=take(y, inds)		
# 		spikes=transpose(array((sx, sy)))
# 		g.addPlot(spikes, name="Marks", style="points", width=8)	
# 		for i, n in enumerate(self.dv.channames()):
# 			r= isBinary(self.dv.datafile.data[:,i])
# 			if r:
# 				m = max(r[0],r[1])
# 				chan = self.dv.datafile.data[start:stop,i]
# 				inds=nonzero(chan==m)
# 				sx=take(x, inds)	
# 				sy=take(y, inds)		
# 				spikes=transpose(array((sx, sy))) 
# 				g.addPlot(spikes, name=n, style="points", width=8)
# 		g.legend=False		
# 		g.fullScale()
# 		g.DrawAll()

# 	def UI_Rotate(self, event=None):
# 		if not self.chan_ids:
# 			self.assign()
# 		d=self.dv.askParam([{"Name":"Deg (clock)",
# 							 "Value":45.0}])
# 		if not d:
# 			return
# 		ds = self.dv.datafile.copy()
# 		chans = [self.chan_ids[0], self.chan_ids[1]]
# 		mien.datafiles.dataset.rotateDS(ds, chans, d[0])
# 		self.dv.assignNewDf(ds)
# 
# 	def UI_CountEvents(self, event=None):
# 		xr =None
# 		if len(self.dv.graph.xmarkers)>1:
# 			xr = [self.dv.graph.xmarkers[-2]["loc"],self.dv.graph.xmarkers[-1]["loc"]]
# 			xr.sort()
# 		ind=self.getRasterChan()
# 		n = len(ind)
# 		s = "%i events" % n
# 		if xr:
# 			mask=logical_and(ind>xr[0], ind<=xr[1])
# 			n=mask.sum()
# 			s+=", %i between marks." % n
# 			ind=take(ind, nonzero(mask))
# 		s+=" Mean: %.4f, StdDev %.4f" % (ind.mean(), ind.stddev())
# 		ms=ind-shift(ind, 1)
# 		ms=ms[1:].min()
# 		s+=" min sep: %.4f" % ms
# 		self.report(s)	
# 
# 
# 	def UI_MarksFromSpecial(self, event=None):
# 		'''select a key from ds.special. This key should contain a 1D array 
# 		of ints or floats. draw an x marker at each location specified.'''
# 		d=self.dv.askParam([{
# 							'Name':'Key',
# 							 "Type":"List",
# 							 "Value":self.dv.datafile.special.keys()
# 							},{
# 							'Name':'Index Type',
# 							'Type':'List',
# 							'Value':['Index', "Time"]
# 							}
# 							])
# 		if not d:
# 			return
# 		ind=self.dv.datafile.special[d[0]]
# 		if d[1]=="Index":
# 			ind=take(self.dv.datafile.get_x(), ind.astype(Int32))
# 		color = wx.Colour(0,200,180)
# 		for x in ind:
# 			print x
# 			self.dv.graph.xmarkers.append({"loc":x, "color":color})
# 		self.dv.graph.drawMarkers()
# 
# 
# 	def UI_ManualMark(self, event=None):
# 		d=self.dv.askParam([{
# 							'Name':'Dimension',
# 							 "Type":"List",
# 							 "Value":["X", "Y"]
# 							},{
# 							'Name':'Index Type',
# 							'Type':'List',
# 							'Value':['Index', "Time"]
# 							},{
# 							'Name':'Location',
# 							'Value':0.0
# 							}
# 							])
# 		if not d:
# 			return
# 		if d[1]=="Index":
# 			ind=self.dv.datafile.start+d[2]/self.dv.datafile.fs
# 		else:
# 			ind=d[2]
# 		color = wx.Colour(0,180,180)
# 		print ind
# 		if d[0]=="X":
# 			self.dv.graph.xmarkers.append({"loc":ind, "color":color})
# 		else:
# 			self.dv.graph.ymarkers.append({"loc":ind, "color":color})
# 		self.dv.graph.drawMarkers()
# 
# 
# 
# 	def UI_RotateStimulus(self, event=None):
# 		if not self.chan_ids:
# 			self.assign()
# 		d=self.dv.askParam([{"Name":"Degrees (clockwise)",
# 							 "Value":0.0}])
# 		if not d:
# 			return
# 		a=transpose(array([self.dv.datafile.channel(self.chan_ids[0]),
# 						   self.dv.datafile.channel(self.chan_ids[1])]))
# 		a = rotate(a, d[0])
# 		df = self.dv.datafile.assignChannel(self.chan_ids[0], a[:,0])
# 		df = df.assignChannel(self.chan_ids[1], a[:,1])
# 		self.dv.assignNewDf(df)			
# 		
# 
# 	def UI_DisplayPolarStimulus(self, event):
# 		if not self.chan_ids:
# 			self.assign()
# 		x, y = 	self.chan_ids
# 		r, theta = cart_to_pol(self.dv.datafile.channel(x), self.dv.datafile.channel(y))
# 		g = self.subPlot()
# 		g.addPlot(r, name="R", style="envelope")
# 		g.addPlot(theta, name="Theta", style="envelope")
# 		g.fullScale()
# 		g.DrawAll()
# 				
# 
# 	def UI_PowerSpectrum(self, event):
# 		chans=self.dv.selectChannels()
# 		if len(chans) == 1:
# 			dat = self.dv.datafile.channel(chans[0])
# 		elif len(chans) == 2:
# 			#chans  = map(lambda x: x+1, chans)
# 			dat = take(self.dv.datafile.data, chans, 1)
# 			dat = ones(dat.shape[0], Complex32)*dat[:,0]+1j*dat[:,1]
# 		else:
# 			self.report("PSD requires 1 or 2 channels for input")
# 			return
# 		self.report("Calculating power spectrum")
# 		psd = psde(dat, self.dv.datafile.fs)
# 		if psd == None:
# 			self.report("Not Enough Data")
# 			return
# 		g = self.subPlot()
# 		g.addPlot(psd, name="Power Spectrum Estimate", style="envelope")
# 		g.limit(array([-10.0,1010.0, 0.0, 1.0]))
# 		g.DrawAll()
# 		
# 	def UI_Coherence(self, event):
# 		d=self.dv.askParam([{"Name":"From Channels",
# 							 "Type":"Select",
# 							 "Value":self.dv.channames()},
# 							{"Name":"To Channels",
# 							 "Type":"Select",
# 							 "Value":self.dv.channames()}])
# 		if not d:
# 			return
# 		ichans = map(lambda x: self.dv.channames().index(x), d[0])
# 		if len(ichans) == 1:
# 			idat = self.dv.datafile.channel(ichans[0])
# 		elif len(ichans) == 2:
# 			idat = take(self.dv.datafile.data, ichans, 1)
# 			idat = ones(idat.shape[0], Complex32)*idat[:,0]+1j*idat[:,1]
# 		else:
# 			self.report("Coh requires 1 or 2 channels for input")
# 			return
# 		ochans = map(lambda x: self.dv.channames().index(x), d[1])
# 		if len(ochans) == 1:
# 			odat = self.dv.datafile.channel(ochans[0])
# 		elif len(ochans) == 2:
# 			odat = take(self.dv.datafile.data, ochans, 1)
# 			odat = ones(odat.shape[0], Complex32)*odat[:,0]+1j*odat[:,1]
# 		else:
# 			self.report("Coh requires 1 or 2 channels for input")
# 			return
# 		coh =  coherence(idat, odat, self.dv.datafile.fs)
# 		if coh == None:
# 			self.report("Not Enough Data")
# 			return
# 		g = self.subPlot()
# 		g.addPlot(coh, name="Coherence", style="envelope")
# 		g.limit(array([-10.0,1010.0, 0.0, 1.0]))
# 		g.DrawAll()
# 		
# 	def UI_Bode(self, event):
# 		d=self.dv.askParam([{"Name":"From Channels",
# 							 "Type":"Select",
# 							 "Value":self.dv.channames()},
# 							{"Name":"To Channels",
# 							 "Type":"Select",
# 							 "Value":self.dv.channames()},
# 							{"Name":"Attenuation Scale",
# 							 "Type":"List",
# 							 "Value":["Log", "Lin"]},
# 							{"Name":"Frequency Scale",
# 							 "Type":"List",
# 							 "Value":["Log", "Lin"]}
# 							])
# 		if not d:
# 			return
# 		ichans = map(lambda x: self.dv.channames().index(x), d[0])
# 		if len(ichans) == 1:
# 			idat = self.dv.datafile.channel(ichans[0])
# 		elif len(ichans) == 2:
# 			idat = take(self.dv.datafile.data, ichans, 1)
# 			idat = ones(idat.shape[0], Complex32)*idat[:,0]+1j*idat[:,1]
# 		else:
# 			self.report("Coh requires 1 or 2 channels for input")
# 			return
# 		ochans = map(lambda x: self.dv.channames().index(x), d[1])
# 		if len(ochans) == 1:
# 			odat = self.dv.datafile.channel(ochans[0])
# 		elif len(ochans) == 2:
# 			odat = take(self.dv.datafile.data, ochans, 1)
# 			odat = ones(odat.shape[0], Complex32)*odat[:,0]+1j*odat[:,1]
# 		else:
# 			self.report("Coh requires 1 or 2 channels for input")
# 			return
# 		freq, amp, phase =  bode(idat, odat, self.dv.datafile.fs)
# 		if d[2]=="Log":
# 			amp=log(amp)/log(10)
# 		if d[3]=="Log":
# 			freq=log(freq[1:])/log(10)
# 			amp=amp[1:]
# 			phase=phase[1:]
# 		g = self.subPlot()
# 		amp= transpose(array([freq, amp]))
# 		g.addPlot(amp, name="Attenuation", style="envelope")
# 		phase= transpose(array([freq, phase]))
# 		g.addPlot(phase, name="Phase", style="envelope")
# 		g.DrawAll()
# 
# 	def UI_ExtractStimulusComponent(self, event):
# 		if not self.chan_ids:
# 			self.assign()
# 		d=self.dv.askParam([{"Name":"Get Component",
# 							 "Type":"List",
# 							 "Value":["Magnitude", "Direction", "Projection"]},
# 							{"Name":"Axis (For Projection)",
# 							 "Value":315.0}])
# 		if not d:
# 			return
# 		stim = map(lambda x: x, self.chan_ids )
# 		stim =  take(self.dv.datafile.data, stim, 1)
# 		if d[0] in ["Magnitude", "Direction"]:
# 			m, t = cart_to_pol(stim[:,0],stim[:,1])
# 			if d[0]=="Magnitude":
# 				na = m
# 				lab = "Stimulus Magnitude"
# 			else:
# 				na =t
# 				lab = "Stimulus Direction"
# 		else:
# 			na = get_directional_projection(stim, d[1])
# 			lab = "Stimulus Projection on %.1f degrees" % d[1]
# 		df = self.dv.datafile.addchannel(lab, na)
# 		self.dv.assignNewDf(df)
# 		
# 		
# 	def UI_Stats(self, event):
# 		s = "\n"
# 		for i, cn  in enumerate(self.dv.channames()):
# 			d = self.dv.datafile.channel(i)
# 			m = d.mean()
# 			sd = ( ((d**2).sum()/len(d)) - m**2 )**.5
# 			s += "%s: mean %.8f, sd %.8f, min %.4f, max %.4f\n" % (cn , m, sd, d.min(), d.max())  
# 		self.report(s)
# 
# 

# 
# 		
# 	def UI_SpikeDetect(self, event=None):
# 		d=self.dv.askParam([{"Name":"Which Channel",
# 							 "Type":"List",
# 							 "Value":self.dv.channames()},
# 							{"Name":"Threshold Method",
# 							 "Type":"List",
# 							 "Value":["Above", "Below", "Schmit Above", "Max between",
# 									  "Min Between", "Above and Below"]},
# 							{"Name":"Event Length (ms)",
# 							 "Value":3.0},
# 							{"Name":"Action",
# 							 "Type":"List",
# 							 "Value":["Mark Spikes", "Convert Channel to Raster", "Add Raster Channel"]}])
# 		if not d:
# 			return
# 		channo=self.dv.channames().index(d[0])
# 		thresh=[]
# 		offsets = self.dv.offsets.get(d[0])
# 		try:
# 			thresh.append(self.dv.graph.ymarkers[-1]['loc'])
# 		except:
# 			self.report("You need to set thresholds first!")
# 			return
# 		if len(d[1])>6:
# 			try:
# 				thresh.append(self.dv.graph.ymarkers[-2]['loc'])
# 			except:
# 				self.report("You need to set 2 thresholds for this method!")
# 				pass
# 		if offsets:
# 			for i in range(len(thresh)):
# 				thresh[i] = (thresh[i]- offsets[0])/offsets[2]
# 		self.report("Thresholds: %s" % thresh)
# 		func = d[1]
# 		evtl = d[2]*self.dv.datafile.fs/1000.0
# 		pars=[thresh, evtl]
# 		f=spikedetect(self.dv.datafile, channo, func, pars)
# 		if d[3] == "Mark Spikes":
# 			color = wx.Colour(128,128,128)
# 			for x in f:
# 				self.dv.graph.xmarkers.append({"loc":x, "color":color})
# 			self.dv.graph.drawMarkers()
# 		elif d[3] == "Convert Channel to Raster":
# 			df=self.dv.datafile.copy()
# 			df.setRaster(channo, f)
# 			self.dv.assignNewDf(df)
# 		elif d[3] == "Add Raster Channel":
# 			c=zeros(len(self.dv.datafile), self.dv.datafile.data.dtype.char)
# 			df=self.dv.datafile.copy()
# 			df.addchannel("EventTimes", c)
# 			df.setRaster(df.data.shape[1]-1, f)
# 			self.dv.assignNewDf(df)
# 					
# 
# 
# 	def UI_EventLockedInsert(self, event=None):
# 		chans= self.dv.channames()
# 		d=self.dv.askParam([{"Name":"Insert From",
# 							 "Type":str,
# 							 "Browser":FileBrowse},
# 							 {"Name":"Sample Rate",
# 							 "Optional":True,
# 							 "Type":float},
# 							 {"Name":"Offset (ms)",
# 							 "Value":0.0},
# 							{"Name":"Which Channel?",
# 							 "Type":"List",
# 							 "Value":chans},
# 							{"Name":"Amp (%)",
# 							 "Value":0.0},
# 							{"Name":"Amp SD (%)",
# 							 "Value":0.0},
# 							{"Name":"Offset SD (ms)",
# 							 "Value":0.0},
# 							 {"Name":"Mode",
# 							 "Type":"List",
# 							 "Value":["Add", "Replace"]},
# 							 {"Name":"Smoothing",
# 							 "Value":10}])
# 		if not d:
# 			return
# 		ins = fromFile(d[0])
# 		if d[1]:
# 			ins.fs=d[1]
# 		ins.resample(self.dv.datafile.fs)	
# 		ins=ins.channel(0)
# 		chan = self.dv.channames().index(d[3])
# 		dat = self.dv.datafile.channel(chan)
# 		maxdat = dat.max() or 1.0
# 		if d[4]:
# 			ins = ins*(maxdat/ins.max())
# 			ins = ins*d[4]/100.0
# 		if d[8]:
# 			sp=min(d[8], int(.25*len(ins)))
# 			ins_template=ins[sp:-sp].copy()
# 		else:
# 			sp=False
# 		offset = (d[2]/1000.0)*self.dv.datafile.fs-len(ins)
# 		noa = 0
# 		newchan =dat.copy()
# 		indexes = self.getRasterChan()
# 		nins = len(indexes)
# 		if d[5]:
# 			ampJ = normal(1.0, d[5]/100.0, nins)
# 		else:
# 			ampJ = ones(nins)
# 		if d[6]:
# 			tsd = d[6]*self.dv.datafile.fs/1000.0
# 			tJ = normal(0, tsd, nins)
# 		else:
# 			tJ = zeros(nins)
# 		for i, m in enumerate(indexes):
# 			ind = self.dv.datafile.xind(m, True)
# 			if ind == None:
# 				continue
# 			ind += offset+tJ[i]
# 			ind = int(ind)
# 			sind = ind+len(ins)
# 			if not 0<=ind<newchan.shape[0]:
# 				continue
# 			if sp:
# 				if ind<2:
# 					lead=smoothConnect(array([0.0, 0.0]), ins_template, sp)	
# 				else:
# 					lead=smoothConnect(newchan[ind-2:ind], ins_template, sp)
# 				if sind>newchan.shape[0]-2:
# 					lag=smoothConnect(ins_template, array([0.0,0.0]), sp)
# 				else:
# 					lag=smoothConnect(ins_template, newchan[sind:sind+2], sp)
# 				ins=concatenate([lead, ins_template, lag])		
# 			if d[7]=="Replace":
# 				newchan[ind:sind] = ins*ampJ[i]
# 			else:	
# 				newchan[ind:sind] = newchan[ind:sind]+ins*ampJ[i]
# 			noa+=1
# 		df = self.dv.datafile.copy()
# 		self.report("Modifying channel %i" % chan)
# 		df.assignChannel(chan, newchan)
# 		self.dv.assignNewDf(df)
# 		self.report("Added %i inserts" % noa) 		
# 
# 	def UI_Window(self, event=None):
# 		inds=self.getRasterChan(True)
# 		if inds==None:
# 			self.report("create a raster channel before windowing")
# 			return
# 		d=self.dv.askParam([{"Name":"Time before mark (sec)",
# 						  "Value":.02},
# 						 {"Name":"Window Size (sec)",
# 						  "Value":.03}])
# 		if not d:
# 			return
# 		x=[]
# 		pre=int(round(self.dv.datafile.fs*d[0]))
# 		inds-=pre
# 		winlen=int(round(d[1]*self.dv.datafile.fs))
# 		self.dv.datafile.special["window"]=(winlen, inds)
# 		self.dv.display()
# 		self.report("windowing complete")


class ContrastControl(wx.Dialog):
	def __init__(self, master):
		wx.Dialog.__init__(self, master)
		self.dv=master
		self.imcenter=None
		self.SetTitle("DV Contrast Control")
		sizer = wx.BoxSizer(wx.VERTICAL)
		tw = self.GetTextExtent("W")[0]*30

		btn = wx.Button(self, -1, " Global Equalize ")
		wx.EVT_BUTTON(self, btn.GetId(), lambda x:self.dv.equalize('g'))
		sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

		btn = wx.Button(self, -1, " Local Equalize ")
		wx.EVT_BUTTON(self, btn.GetId(), lambda x:self.dv.equalize('l'))
		sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)						

		btn = wx.Button(self, -1, " Raw Amplitudes ")
		wx.EVT_BUTTON(self, btn.GetId(), lambda x:self.dv.equalize('n'))
		sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)												
		#Reset center

		btn = wx.Button(self, -1, " Global Contrast ")
		wx.EVT_BUTTON(self, btn.GetId(), lambda x:self.contrast('g'))
		sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)																	

		btn = wx.Button(self, -1, " Current Local Contrast ")
		wx.EVT_BUTTON(self, btn.GetId(), lambda x:self.contrast('l'))
		sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)	

		btn = wx.Button(self, -1, " Continuous Local Contrast ")
		wx.EVT_BUTTON(self, btn.GetId(), lambda x:self.contrast('c'))
		sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)	

		self.cmax = wx.TextCtrl(self, -1, "255.0", style=wx.TE_PROCESS_ENTER, size=(12,-1))
		wx.EVT_TEXT_ENTER(self, self.cmax.GetId(), lambda x:self.contrast('m'))
		sizer.Add(self.cmax, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)

		self.cmin = wx.TextCtrl(self, -1, "0.0", style=wx.TE_PROCESS_ENTER, size=(12,-1))
		wx.EVT_TEXT_ENTER(self, self.cmin.GetId(), lambda x:self.contrast('m'))
		sizer.Add(self.cmin, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)																				
		#quit
		btn = wx.Button(self, -1, " Close ")
		wx.EVT_BUTTON(self, btn.GetId(), lambda x:self.Destroy())
		sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		sizer.Fit(self)

	def contrast(self, event):
		if event == "m":
			try:
				cmin = float(self.cmin.GetValue())
			except:
				cmin = 0.0
			try:
				cmax = float(self.cmax.GetValue())
			except:
				cmax=255.0
		elif event == "g":
			cmin, cmax = self.getRange()
		else:
			cmin, cmax = self.getRange(True)
		self.cmin.SetValue(str(cmin))
		self.cmax.SetValue(str(cmax))
		if event=="c":
			self.dv.preferences["Image Contrast"]='local'
		else:
			self.dv.preferences["Image Contrast"]=(cmin, cmax)
		if self.dv.inMode=="Image":
			self.dv.display()

	def getRange(self, local=False):
		dat = self.dv.getImageData()
		if local:
			mii, mai = self.dv.getCurrentView()
			dat = dat[mii:mai,:]
		return (dat.min(), dat.max())