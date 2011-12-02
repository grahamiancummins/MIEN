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
from mien.wx.graphs.graphFSR import GraphFSR
from mien.wx.graphs.graph import Graph
from mien.math.functiongenerator import Funcgen, envfuncdict
from mien.math.array import *
from mien.math.sigtools import cart_to_pol
from mien.sound.wav import array2wav, playArray
import os
from mien.wx.dialogs import FileBrowse
from mien.datafiles.filewriters import writeFile
		
envfuncdict["Filter"][0]["Browser"]=FileBrowse

class EnvEditor(wx.Dialog):
	def __init__(self, master, i):
		wx.Dialog.__init__(self, master, -1, "Envelope Editor", style=wx.DEFAULT_DIALOG_STYLE)
		
		self.control=master
		self.i=i
		name=self.control.choose_env.GetString(i)
		self.id=int(name.split(":")[0])
		
		info=self.control.generator.envelopes[self.id]
		self.parentries={}
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.etype = info["type"]
		sizer.Add(wx.StaticText(self, -1, "Envelope %s (%s type)" % (name, self.etype)), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.pars = []
		for k in info.keys():
			if k in ["type", "filt"]:
				continue
			self.pars.append([k, info[k]])
		vs = manyEntries(self.pars, self)
		sizer.Add(vs, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		
		box = wx.BoxSizer(wx.HORIZONTAL)
		btn = wx.Button(self, -1, " Apply ")
		wx.EVT_BUTTON(self, btn.GetId(), self.parset)
		btn.SetDefault()
		box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		btn = wx.Button(self, -1, " Delete ")
		wx.EVT_BUTTON(self, btn.GetId(), self.kill)
		box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		btn = wx.Button(self, wx.ID_CANCEL, " Cancel ")
		box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		sizer.Fit(self)
		self.Show(True)
		
	def parset(self, event=None):
		if self.Validate() and self.TransferDataFromWindow():
			d = {"type":self.etype}
			for par in self.pars:
				d[par[0]]=par[1]	
			self.control.generator.envelopes[self.id]=d
			self.control.make_change()
			self.control.report("%s:Modified envelope %i" % (self.control.id, self.i))
		else:
			self.control.report("Couldnt read parameter values")
			
	def kill(self, event=None):
		self.control.generator.kill_envelope(self.id)
		self.control.choose_env.Delete(self.i)
		self.control.make_change()
		self.control.report("%s:Deleted Envelope %i" % (self.control.id, self.i))
		self.Destroy()
			

class WaveEditor(wx.Dialog):
	def __init__(self, master, i):
		wx.Dialog.__init__(self, master, -1, "Function Editor", style=wx.DEFAULT_DIALOG_STYLE)
		self.control=master
		self.i=i

		sizer = wx.BoxSizer(wx.VERTICAL)
		box = wx.BoxSizer(wx.HORIZONTAL)
 		waveinfo=self.control.generator.waves[self.i]
		self.wavetype = waveinfo['type'] 
 		self.pars = []
 		for v in ["amp", "freq", "phase", "offset", "seed"]:
 			self.pars.append([v, waveinfo[v]])
 		vs = manyEntries(self.pars, self)
 		sizer.Add(vs, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		
 		box = wx.BoxSizer(wx.HORIZONTAL)
 		box.Add(wx.StaticText(self, -1, "AM Envelopes"), 1, wx.ALIGN_CENTRE|wx.ALL, 5)
 		box.Add(wx.StaticText(self, -1, "FM Envelopes"), 1, wx.ALIGN_CENTRE|wx.ALL, 5)
 		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

		
 		box = wx.BoxSizer(wx.HORIZONTAL)
		
 		envs=map(str, self.control.generator.envelopes.keys())
		
 		ts = master.GetTextExtent("W")
 		ts = (ts[0]*20, ts[1]*5)
		
 		self.selectAM = wx.ListBox(self, -1, choices=envs, style=wx.LB_EXTENDED, name="AM Envelopes", size=ts)
 		box.Add(self.selectAM, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
 		self.selectFM = wx.ListBox(self, -1, choices=envs, style=wx.LB_EXTENDED, name="FM Envelopes", size=ts)
 		box.Add(self.selectFM, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
 		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
		
 		for i in range(len(envs)):
 			if i in waveinfo["AM"]:
 				self.selectAM.SetSelection(i)
 			if i in waveinfo["FM"]:
 				self.selectFM.SetSelection(i)
		
		box = wx.BoxSizer(wx.HORIZONTAL)
		btn = wx.Button(self, -1, " Apply ")
		wx.EVT_BUTTON(self, btn.GetId(), self.parset)
		box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		btn = wx.Button(self, -1, " Delete ")
		wx.EVT_BUTTON(self, btn.GetId(), self.kill)
		box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		btn = wx.Button(self, wx.ID_CANCEL, " Cancel ")
		box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		sizer.Fit(self)
		self.Show(True)

	def parset(self, event=None):
		if self.Validate() and self.TransferDataFromWindow():
			d={"type":self.wavetype,
				"AM":list(self.selectAM.GetSelections()),
			   "FM":list(self.selectFM.GetSelections())}
			for par in self.pars:
				d[par[0]]=par[1]
			self.control.generator.waves[self.i]=d
			self.control.make_change()
			self.control.report("%s:Modified wave %i" % (self.control.id, self.i))	
		else:
			self.control.report("Couldnt read parameter values")

		
	def kill(self, event=0):
		self.control.generator.kill_wave(self.i)
		self.control.choose_wave.Delete(self.i)
		self.control.make_change()
		self.control.report("%s:Deleted wave %i" % (self.control.id, self.i))
		self.Destroy()
		


class ChannelControls(wx.Panel):
	def __init__(self, master, main, id=""):
		wx.Panel.__init__(self, master, -1)
		self.id=id
		self.main = main
		
		ts = master.GetTextExtent("W")
		ts = (ts[0]*15+20, ts[1]*6+20)
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.info = wx.StaticText(self, -1, "%s Controls" % self.id)
		sizer.Add(self.info, 0, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 2)

		box = wx.BoxSizer(wx.HORIZONTAL)
		self.choose_wave=wx.ListBox(self, -1, choices=[], style=wx.LB_SINGLE, name="Functions", size=ts)
		wx.EVT_LISTBOX_DCLICK(self, self.choose_wave.GetId(), self.edit_wave)
		box.Add(self.choose_wave, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 2)
		self.choose_env = wx.ListBox(self, -1, choices=[], style=wx.LB_SINGLE, name="Envelopes", size=ts)
		wx.EVT_LISTBOX_DCLICK(self, self.choose_env.GetId(), self.edit_env)
		box.Add(self.choose_env, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 2)
		sizer.Add(box, 6, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
		
		box = wx.BoxSizer(wx.HORIZONTAL)
		self.add_w_b = wx.Button(self, -1, "Add Function")
		box.Add(self.add_w_b, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 2)
		wx.EVT_BUTTON(self, self.add_w_b.GetId(), self.add_wave)
		self.add_e_b = wx.Button(self, -1, "Add Env")
		box.Add(self.add_e_b, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 2)
		wx.EVT_BUTTON(self, self.add_e_b.GetId(), self.add_env)
		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
		
		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		self.Show(True)
		

	def set(self, generator=None):
		self.choose_env.Clear()
		self.choose_wave.Clear()
		self.generator=generator
 		if not self.generator:
 			return
 		for f in range(len(self.generator.waves)):
			name="%s(%s,%.1f)" % (self.generator.waves[f]["type"],
								  self.generator.waves[f]["freq"],
								  self.generator.waves[f]["phase"])
			
			self.choose_wave.Append(name)

		for f in self.generator.envelopes:
			name="%i:%s" % (f,
							self.generator.envelopes[f]["type"])
			self.choose_env.Append(name)	
			
	def report(self, test):
		print t

	
	def add_wave(self, event=None):
		d=self.main.askParam([{"Name":"Amp (relative)",
							   "Value":1.0},
							  {"Name":"Frequency (Hz or (RiseTime,Falltime))",
							   "Value":(100.0,)},
							  {"Name":"Phase (degrees or repeat len for WN)",
							   "Value":0.0},
							  {"Name":"Offset",
							   "Value":0.0},
							  {"Name":"Seed",
							   "Value":0},
							  {"Name":"Function Type",
							   "Type":"List",
							   'Value':self.generator.functions.keys()}])
		if not d:
			return
		c={"amp":d[0], "freq":d[1], "phase":d[2], "offset":d[3],
		   "seed":d[4], "type":d[5], "FM":[], "AM":[]}
		self.generator.add_wave(c)
		
		name="%s(%s,%.1f)" % ( self.generator.waves[-1]["type"],
							   self.generator.waves[-1]["freq"],
							   self.generator.waves[-1]["phase"])
		
		self.choose_wave.Append(name)
		self.make_change()

	def edit_wave(self, event=None):
		try:
			i = event.GetSelection()
			self.report("%s:Editing Wave %i" % (self.id, i))
		except:
			self.report("%s:No wave selected" % self.id)
			return
		ed=WaveEditor(self, i)
		
	def add_env(self, event=None):
		d=self.main.askParam([{"Name":"function",
							   "Type":"Choice",
							   "Value":envfuncdict}])
		if not d:
			return
		env = {"type":d[0][0]}
		epl = envfuncdict[d[0][0]]
		pars = d[0][1:]
		for i, v in enumerate(pars):
			env[epl[i]["Name"]]=pars[i]
		n=self.generator.add_envelope(env)
		name="%i:%s" % (n,
						   self.generator.envelopes[n]["type"])
		self.choose_env.Append(name)

	def edit_env(self, event=None):
		try:
			i=event.GetSelection()
			self.report("%s:Editing Envelope %i" % (self.id, i))
		except:
			self.report("%s:No envelope selected" % self.id)
			return
		ed=EnvEditor(self, i)
		
	def make_change(self):
		print "Change"

	
class WFGui(BaseGui):
	def __init__(self, parent=None, **kwargs):
		nchans=kwargs.get('nchans', 2) 
		returnData=kwargs.get('returnData')
 		BaseGui.__init__(self, parent, title="Waveform Generator", menus = ["File", "Control"], pycommand=True,height=4)

		commands=[["File","New" , lambda x: self.new()],
				  ["File","Change Domain" ,self.resize],
 				  ["File","Play" , self.play],
 				  ["File","Save" ,lambda x: self.save(0)],
 				  ["File","Save As" , lambda x:self.save(1)],
				  ["File","----"],
				  ["File","Load Parameters" , self.load_params],
				  ["File","----"],
				  ["File", "Quit", lambda x:self.Destroy()],
				  ["Control", "Smoothing Points", self.set_smooth_points],
				  ["Control", "Fill dcl with silence", self.set_silent_fill],
				  ["Control","Refresh Display",lambda x: self.make_change()],
				  ["Control","Plot trajectory",self.trajectoryplot]]
		
		if returnData:
			self.returnDataMono=lambda x:returnData(self.dataExport(1))
			self.returnDataStereo=lambda x:returnData(self.dataExport(2))
			commands.insert(2, ["File", "Export Data (Mono)", self.returnDataMono])
			commands.insert(2, ["File", "Export Data (Stereo)", self.returnDataStereo])
			
		self.fillMenus(commands)
		id = wx.NewId()
		self.menus["Control"].AppendCheckItem(id, "Smooth Transitions")
		wx.EVT_MENU(self, id, self.change_smoothing)

		self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.main.SetSizer(self.mainSizer)
		self.main.SetAutoLayout(True)
	
		self.graph=GraphFSR(self.main,-1)		
		self.mainSizer.Add(self.graph,1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		
	   	self.display=self.display_cart
		
		vsizer2 = wx.BoxSizer(wx.VERTICAL)
		self.channels=[]
		self.controls=[]

		for s in range(nchans):
			control=ChannelControls(self.main,self, "Channel %i" % s)
			vsizer2.Add(control, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
			control.report=self.report
			control.make_change=self.make_change
			self.controls.append(control)
			self.channels.append(None)
		self.mainSizer.Add(vsizer2,1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		
		self.filename=None
		self.savetype = None
		self.smoothpoints=50
		self.silent_fill=(0,0)
	   		
		self.mainSizer.Fit(self.main)
		self.SetSize(wx.Size(800,600))
		self.new(1.0, .00005)
		
	def set_silent_fill(self, event=None):
		d=self.askParam([{"Name":"Seconds of silence",
						  "Value":2.0},
						 {"Name":"Offset",
						  "Value":0.0}])
		if not d:
			return
		self.silent_fill=tuple(d)

	def dataExport(self, Channels=2):
		self.evaluate()
		self.fillResults()
		a=self.results.astype(Float32)
		if Channels==1:
			a=reshape(a[:,0], (-1,1))
		h = {"Labels":map(str, range(a.shape[1])),
			 "SamplesPerSecond":str(1.0/self.sampling)}
		return DataSet(a, h)
		
		
	def set_smooth_points(self, event=None):
		d=self.askParam([{"Name":"Number of points",
							   "Value":self.smoothpoints}])
		if not d:
			return
		self.smoothpoints=d[0]
		self.report("set number of smoothing points to %i" % self.smoothpoints)
		if self.smoothing:
			for c in self.channels:
				c.smoothing=self.smoothpoints
			self.make_change()	

	def trajectoryplot(self, event=None):
		bar = {'size':(400,400), 'style':wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE}
		tp = wx.Frame(self, -1, "Trajectory Plot", **bar)
		tp.g=Graph(tp, -1)
		tp.g.fixAR = 1.0
		tp.Show(True)
		self.evaluate()
		l=self.graph.limits
		if l[0]>0:
			st = int(l[0]/self.sampling)
		else:
			st=0
			
		if l[1]<self.duration:
			sp =int(l[1]/self.sampling)
		else:
			sp = -1
		a=self.results[st:sp,:2]
		tp.g.addPlot(a, name="Trajectory")
		tp.g.fullScale()
		tp.g.DrawAll()
		
			
	def change_smoothing(self, event):
		if event.IsChecked():
			for c in self.channels:
				c.smoothing=self.smoothpoints
		else:
			for c in self.channels:
				c.smoothing=0
		self.make_change()	

	def make_change(self):
		self.display()
		
	def new(self, duration=None, sampling=None):
		if not duration:
			d=self.askParam([{"Name":"Duration(sec)",
							  "Value":0.2},
							 {"Name":"Sampling Rate(Hz)",
							  "Value":10000.0}])
			if not d:
				return
			self.duration=d[0]
			self.sampling=1.0/d[1]
		else:
			self.duration=duration
			self.sampling=sampling
		for s in range(len(self.channels)):
			self.channels[s]=Funcgen((0, self.duration, self.sampling))
			self.controls[s].set(self.channels[s])
		self.report("New Waveform: %.5f seconds at %.3f Hz" % (self.duration, 1/self.sampling))
		xp = self.duration*.05
		self.graph.fs = 1.0/self.sampling
		self.graph.limit(array([-xp, self.duration+xp, -2, 2]))
		self.display()
		self.filename=None

	def resize(self, event=None):
		d=self.askParam([{"Name":"Duration(sec)",
						  "Value":	self.duration},
						 {"Name":"Sampling Rate(Hz)",
						  "Value":1.0/self.sampling}])
		if not d:
			return
		self.duration=d[0]
		self.sampling=1.0/d[1]
		for s in range(len(self.channels)):
			self.channels[s].set_domain((0, self.duration, self.sampling))
		self.report("New duration: %.5f s, New sampling: %.3f Hz" % (self.duration, 1/self.sampling))
		xp = self.duration*.05
		self.graph.limit(array([-xp, self.duration+xp, -2, 2]))
		self.display()
		
	def evaluate(self):
		self.results=map(lambda x: x.generate(), self.channels)
		self.results=array(self.results)
		self.results=transpose(self.results)


	def fillResults(self):	
		if self.silent_fill[0]:
			fill=zeros((int(self.silent_fill[0]/self.sampling), self.results.shape[1]), self.results[0].dtype.char)
			fill = fill + self.silent_fill[1]
			self.results = concatenate([fill, self.results, fill])
		

	def play(self, event=None):
		self.evaluate()
		playArray(self.results, int(1.0/self.sampling))	

   	def save(self, ask):
		if ask or not self.filename:
			if self.filename:
				dir = os.path.split(self.filename)[0]
			else:
				dir = ""
			dlg=wx.FileDialog(self, message="Select file name", defaultDir=dir, wildcard="Parameters | *.param| Wave | *.wav | Stimulus | *.dcl | Stimulus (Channel 0 only) | *.scl | Matlab | *.mat | Python |*.pydat ", style=wx.SAVE)
			dlg.CenterOnParent()
			if dlg.ShowModal() == wx.ID_OK:
				self.filename=dlg.GetPath()
				self.savetype = dlg.GetFilterIndex()
			else:
				self.report("Canceled File Save.")
				return
		self.evaluate()
		if self.savetype == 0:
			if not self.filename.endswith(".param"):
				self.filename+=".param"
			self.save_params(self.filename)
		elif self.savetype == 1:
			if not self.filename.endswith(".wav"):
				self.filename+=".wav"
			array2wav(self.results, int(1.0/self.sampling), self.filename)
		elif self.savetype == 2:
			if not self.filename.endswith(".dcl"):
				self.filename+=".dcl"
			self.fillResults()
			writeFile(self.filename, self.results, {}, "dcl")
		elif self.savetype == 3:
			if not self.filename.endswith(".scl"):
				self.filename+=".scl"
			self.fillResults()
			writeFile(self.filename, reshape(self.results[:,0], (-1, 1)), {}, "scl")	
		elif self.savetype == 4:
			if not self.filename.endswith(".mat"):
				self.filename+=".mat"
			head = {"SamplesPerSecond":1.0/self.sampling}
			self.fillResults()
			writeFile(self.filename, self.results, head, "mat")	
		elif self.savetype == 5:
			if not self.filename.endswith(".pydat"):
				self.filename+=".pydat"
			head = {"SamplesPerSecond":1.0/self.sampling}
			self.fillResults()
			writeFile(self.filename, self.results, head, "pydat")	
		
	def save_params(self, file):
		par={}
		par["Duration"]=self.duration
		par["Sample Period"]=self.sampling
		par["Channels"]=[]
		for i in range(len(self.channels)):
			c={}
			c["Envelopes"]=self.channels[i].envelopes
			c["Waves"]=self.channels[i].waves
			par["Channels"].append(c)
		
		open(file, 'w').write(repr(par))

				
	def load_params(self, event=None):
		if self.filename:
			dir = os.path.split(self.filename)[0]
		else:
			dir = ""
		dlg=wx.FileDialog(self, message="Select file", defaultDir=dir, wildcard="*.param", style=wx.OPEN)
		dlg.CenterOnParent()
		if dlg.ShowModal() == wx.ID_OK:
			fname=dlg.GetPath()
		else:
			self.report("Canceled File Load.")
		   	return
		pars=eval(open(fname).read())
		self.new(pars['Duration'], pars['Sample Period'])
		for i in range(len(pars["Channels"])):
			if i>len(self.channels):
				self.report("File specifies more than the supported number of channels")
				break
			c=pars["Channels"][i]
			self.channels[i].envelopes=c["Envelopes"]
			self.channels[i].waves=c["Waves"]
			self.controls[i].set(self.channels[i])
		self.make_change()
		self.filename=fname.split('.')[0]

	def display_cart(self):
		self.evaluate()
   		self.graph.plots = {}
		for i in range(self.results.shape[1]):
			dat = self.results[:,i]
			self.graph.addPlot(dat, "Channel %i" % i, style = "envelope")
		self.graph.DrawAll()	

	
if __name__=='__main__':
	app = wx.PySimpleApp()
	x = WFGui()
	x.Show(True)
	app.MainLoop()
	
