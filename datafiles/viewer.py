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
from mien.wx.graphs.graphFSR import GraphFSR
from mien.wx.base import *
from mien.datafiles.dataset import *
import mien.datafiles.dataproc
from mien.wx.dialogs import FileBrowse
import os, time

class Dataviewer(BaseGui):
	
	def __init__(self, master=None, **kwargs):
		tty=kwargs.get('tty', None)
		title=kwargs.get('title',"Data Viewer")
		returnData=kwargs.get('returnData')
		BaseGui.__init__(self, master, title=title, menus=["File", "Edit", "Display", "Extensions", "Dsp"], pycommand=True,height=4, TTY=tty, showframe=False)
		
		controls=[["File","Open Part of a File", lambda x:self.load(select=True)],
				  ["File","Create Blank (all zeros) Data", self.blank],
				  ["File", "Load SubData", self.loadSub],
				  ["File", "Switch Viewed Data", self.changedat],
				  ["File", "Combine Data", self.combinedat],
				  ["Edit","Undo",self.undo],
				  ["Edit","Redo",self.redo],
				  ["Edit","Save Checkpoint",self.setcheck],
				  ["Edit","Load Checkpoint",self.getcheck],
				  ["Edit","Crop",self.crop],
				  ["Edit","Data Editor",self.launchEditor],
				  ["Edit","Delete Channels",self.delChan],
				  ["Display","Marker Locations",self.markLoc],
				  ["Display","Marker Difference",self.markDiff],
				  ["Display","Set Mark",self.addMark],
				  ["Display","Width 4",self.w4],
				  ["Display","Redraw",lambda x:self.onNewData()],
				  ['Display', 'Global Equalize', lambda x:self.equalize('g')],
				  ['Display', 'Local Equalize', lambda x:self.equalize('l')],
				  ['Display', 'Raw Amplitudes', lambda x:self.equalize('n')],
				  ['Display', 'Show Contrast Controls', self.launchContrast]
				  ]

		
		if returnData:
			self.returnData = lambda x:returnData(self.data)
			controls.insert(2, ["File", "Export Data", self.returnData])
		self.fillMenus(controls)
		#self.bounceST()
		self.modes = {"Separate": self.makeYSep,
					  "Quick Sep": self.makeQSep,
					  "Local Sep": self.makeLSep,
					  "Y Overlay": self.makeYover,
					  "Raw":self.zeroOffset,
					  "Image":self.asImage }
		self.preferenceInfo=[{"Name":"Use image mode for more than X channels",
			"Value":30},
			{"Name":"Image Contrast",
			"Type":"Choice",
			"Value":{"local":[],
				"global":[],
				"Manual":[{"Name":"Min", "Value":-70.0},
					{"Name":"Max", "Value":30.0}]}},
			{"Name":"Display Range",
			'Type':'List',
			'Value':['global', 'local', 'manual']},
			{"Name":"Processing Tools Act On",
			'Type':'List',
			'Value':['All Data', 'Current View', 'Marked Range']},
			{"Name":'Save referenced data files when saving xml',
			'Type':'List',
			'Value':['Yes', 'No']},
			{"Name":'Ensemble display mode',
			'Type':'List',
			'Value':['Stats', 'Mean', 'Overlay', 'Sequential', 'MeanAndCov', 'Hide']},
			{"Name":"On Multiple Open",
			"Type":"List",
			"Value":["Merge", "Nest", "Ignore"]},
			{"Name":"Default View Mode",
			"Type":"List",
			"Value":self.modes.keys()},
			{"Name":"Always Reload Extensions",
			"Type":"List",
			"Value":[True, False]},
			{"Name":'Show Only Same Length Data',
			"Type":"List",
			"Value":[True, False]},
			{"Name":"Simple Subsample",
			"Type":"List",
			"Value":["No", "Yes"]},
			{"Name":"defaultPlotStyle",
			"Type":"List",
			"Value":["envelope", "points", "line"]},
			{"Name":"Checkpoint Directory",
			"Type":str,
			"Browser":FileBrowse},
			{"Name":"Save Multiple Data as",
			"Type":"List",
			"Value":["Directory", "Automatic File Names"]}]
		
		self.preferences={"Use image mode for more than X channels":30,
			"Image Contrast":"global",
			"Processing Tools Act On":"Marked Range",
			'Ensemble display mode':'Stats',
			"defaultPlotStyle":'envelope',
			"Number of Undo Steps":3,
			"Display Nested Data to Depth":4,
			"Display Range":"global",
			"Simple Subsample":'No',
			'Show Only Same Length Data':False,
			"Default View Mode":'Quick Sep',
			"Always Reload Extensions":False,
			"Checkpoint Directory":os.path.expanduser('~/.dvcheckpoints'),
			"On Multiple Open":'Nest', #"Merge", #"Ignore",
			'Save referenced data files when saving xml':'Yes',
			"Save Multiple Data as":"Automatic File Names",
			"Hide Data In":["hidden"]}
		self.mainSizer = wx.BoxSizer(wx.VERTICAL)
		self.main.SetSizer(self.mainSizer)
		self.main.SetAutoLayout(True)
		
		self.graph=GraphFSR(self.main, -1)
		self.graph.applyConfig=self.applyGraphConfig
		
		self.mainSizer.Add(self.graph, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		
		cbox = wx.BoxSizer(wx.HORIZONTAL)

		
		self.chooseChan = wx.Choice(self.main, -1, choices=["No channels loaded"])
		cbox.Add(self.chooseChan, 1, wx.GROW|wx.ALL, 5)
		wx.EVT_CHOICE(self.main, self.chooseChan.GetId(), self.doSelectChannel)
		cbox.Add(wx.StaticText(self.main, -1, "Y off:"), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.setYOff = wx.TextCtrl(self.main, -1, "-", style=wx.TE_PROCESS_ENTER, size=(12,-1))
		wx.EVT_TEXT_ENTER(self.main, self.setYOff.GetId(), self.doApplyOff)
		cbox.Add(self.setYOff, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		cbox.Add(wx.StaticText(self.main, -1, "X off:"), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.setXOff = wx.TextCtrl(self.main, -1, "-", style=wx.TE_PROCESS_ENTER, size=(12,-1))
		wx.EVT_TEXT_ENTER(self.main, self.setXOff.GetId(), self.doApplyOff)
		cbox.Add(self.setXOff, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		cbox.Add(wx.StaticText(self.main, -1, "Y sca:"), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.setYscale = wx.TextCtrl(self.main, -1, "-", style=wx.TE_PROCESS_ENTER, size=(12,-1))
		wx.EVT_TEXT_ENTER(self.main, self.setYscale.GetId(), self.doApplyOff)
		cbox.Add(self.setYscale, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		#self.applyOff = wx.Button(self.main, -1, " Apply ")
		#cbox.Add(self.applyOff, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		#wx.EVT_BUTTON(self.main, self.applyOff.GetId(), self.doApplyOff)
		modes = self.modes.keys()
		self.chooseMode = wx.Choice(self.main, -1, choices=modes)
		self.load_saved_prefs()
		dvm=self.preferences["Default View Mode"]
		self.chooseMode.SetSelection(modes.index(dvm))
		self.inMode = dvm
		
		cbox.Add(self.chooseMode, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		wx.EVT_CHOICE(self.main, self.chooseMode.GetId(), self.doSelectMode)
		
		
		self.mainSizer.Add(cbox, 0, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		#self.mainSizer.Fit(self.main) - segv in 2.5, seems unneeded and slow
		self.SetSize(wx.Size(800,600))
		
		self.graph.SetDropTarget(self.dropLoader)
		self.clear_attributes()
 		self.stdFileMenu()
		
		self.spm = mien.datafiles.dataproc.DVSignalMod(self)
		self.datapath="/"
		self.spm.makeMenus()
		self.load_saved_prefs()
	
	def has_nested_data(self):
		if self.preferences["Display Nested Data to Depth"]<1:
			return False
		if self.data.stype()=='group':
			return True
		nc=self.data.shape()[1]
		toomany=self.preferences.get("Use image mode for more than X channels", 60)
		if nc>toomany:
			return False
		dats=self.data.getElements('Data', depth=1)
		dats=[d for d in dats if not "hidden" in d.name()]
		if dats:
			return True
		return False
	
	def w4(self, event=None):
		for p in self.graph.plots:
			self.graph.plots[p]['width']=4
		self.graph.DrawAll()
		
	def applyGraphConfig(self, conf):
		if not self.plotColors:
			GraphFSR.applyConfig(self.graph, conf, True)
		else:
			GraphFSR.applyConfig(self.graph, conf, False)
			self.graph.plots={}
			self.plotColors=self.graph.nextcolor(len(self.plotColors))
			self.display()
			
	
	def launchContrast(self, event):
		#reload(mien.datafiles.dataproc)
		x=mien.datafiles.dataproc.ContrastControl(self)
		x.Show(True)
	
	def loadSub(self, event=None):
		doc = self.load(returndoc=True)
		dat=doc.getElements('Data', depth=1)
		if not dat:
			self.report("No data instances in this document")
			return
		dat=dat[0]
		pl=[{"Name":"Name", "Value":dat.name()}]
		dp=self.data.getHierarchy().keys()
		if len(dp)>1:
			pl.append({"Name":"Add To Path", "Type":"List", "Value":dp})
		d=self.askParam(pl)
		if not d:
			return
		if len(d)==1:
			par=self.data
		else:
			par=self.data.getSubData(d[0])
		if d[0]!=dat.name():
			dat.setName(d[0])
		par.newElement(dat)
		q=dat.dpath()
		self.report('Added data with path %s' % q)
		self.onNewData()
	
	def addMark(self, event=None):
		d=self.askParam([{'Name':"Coordinate", 'Value':0.0},
				{'Name':'Orientation','Type':'List','Value':['X (Vertical)','Y (Horizontal)']},
				{'Name':'Use Index (not time. X only)', 'Type':'List', 'Value':['No', 'Yes']}])
		if not d:
			return
		color = self.graph.marker_color
		if d[1].startswith('Y'):
			self.graph.ymarkers.append({"loc":float(d[0]), "color":color})
		else:
			if d[2].startswith('N'):
				loc = float(d[0])
			else:
				loc = int(round(d[0]/self.data.fs()))
			self.graph.xmarkers.append({"loc":loc, "color":color})
		self.graph.drawMarkers()
	
	def onSetPreferences(self):
		if self.data:
			self.data.setUndoLength(self.preferences["Number of Undo Steps"], True)
		ic=self.preferences['Image Contrast']
		if type(ic)==list:
			if str(ic[0])=='Manual':
				self.preferences['Image Contrast']=tuple(ic[1:])
			elif str(ic[0]) in ["local", "global"]:
				self.preferences['Image Contrast']=str(ic[0])
		#if logical_xor(bool([x for x in self._channels if x[2][0]!='/']), self.has_nested_data()):
		self.onNewData()
		#else:
		#	self.display()
		self.report("Set Preferences")
	
	def clear_attributes(self, event=None):
		self.document=None
		self.selectedChan = "No channels loaded"
		self.data = None
		self._channels=[]
		self.offsets = {}
		self._datacache={}
		self.plotColors=[]
		self.graph.plots={}
	
	def spawnViewer(self, data=None, mode=None, zoom=True):
		if data and not mode:
			if isSampledType(data):
				mode='dv'
			elif data.stype()=='image':
				mode='image'
			else:
				mode=='locus'
		if mode=='dv':
			v=Dataviewer(self, returnData=self.dataImport)
			v.Show(True)
			v.dataImport(data, zoom=zoom)
		elif mode=='image':
			from mien.image.viewer import ImageViewer
			v=ImageViewer(self)
			if data:
				v.select(data)
		else:
			import mien.datafiles.fview
			v= mien.datafiles.fview.LocusViewer(self)
			v.Show(True)
			v.dataImport(data, zoom=zoom)
		return v
	
	def onNewData(self, zoom=False, remode=True):
		if not self.data or not self.data.__tag__=='Data':
			return
		self.datapath=self.data.upath()
		self._datacache={}
		if self.data.stype()=='image':
			self.spawnViewer(self.data, 'image')
			return
		if self.has_nested_data() or self.data.stype()!='timeseries':
			dep=int(self.preferences["Display Nested Data to Depth"])
			self._channels=getDataList(self.data, ['histogram', 'ensemble', 'events', 'labeledevents', 'timeseries'], dep, self.preferences["Hide Data In"], self.preferences['Show Only Same Length Data'])
		else:
			self._channels=[(str(x), 'timeseries', (self.data.dpath(),i)) for i, x in enumerate(self.data.getLabels())]
		if not self._channels:
			self.graph.killAll()
			self.report('no data that can be displayed')
			return
		if self.data.stype()=='group':
			dts = self.data.getSubData(self._channels[0][2][0])	
			self._channels[0][2] = ("/", self._channels[0][2][1]) 
			self.data.datinit(dts.data, dts.header())
			if dts.elements:
				dts.datinit(None, {"SampleType":'group'})
			else:
				dts.sever()
		nus=self.preferences["Number of Undo Steps"]
		self.data.setUndoLength(nus, True)
		if nus:
			self.data.logflags['undoCheckpoints']=True
			self.data.log_change('checkpoint')
		self.graph.fs = self.data.fs()
		if self.data.attrib('StartTime')==None:
			self.data.setAttrib('StartTime', 0.0, False)
		if zoom:
			t = domain(self.data)
			self.graph.limits[0] = t[0]
			self.graph.limits[1] = t[-1]
		offsets = self.offsets
		self.offsets = {}
		self.chooseChan.Clear()
		toomany=self.preferences.get("Use image mode for more than X channels", 60)
		if len(self._channels)>toomany:
			self.report("There are too many channels in this dataset. Forcing image view. Other view modes will fail")
			self.inMode="Image"
			self.display()
			return
		elif len(self._channels)!=len(self.plotColors):
			self.graph.plots={}
			self.plotColors=self.graph.nextcolor(len(self._channels))
		for c in self._channels:
			n=c[0]
			self.chooseChan.Append(n)
			if offsets.has_key(n):
				self.offsets[n] = offsets[n]
		if remode and self.modes.has_key(self.inMode):
		 	self.modes[self.inMode]()
		self.display()
	
	
	def update_self(self, **kwargs):
		event=kwargs.get('event', 'modify').lower()
		remode=kwargs.get('calc_offsets', True)
		for ob in self.getObjectsFromKWArgs(kwargs):
			#print event, remode, ob
			try:
				ndi=self.document.getInstance(self.datapath)
				if kwargs.get('event')=='delete':
					if od==ndi:
						raise StandardError('data has been removed from the document')
			except:
				self.data=None
				self.onNewData()
				return
			if not self.data==ndi:
				self.data=ndi
				self.onNewData()
				return
			if ob==self.data or ob==self.data.getTop() or ob==self.document:
				self.onNewData(remode=remode)
				return
			elif ob in self.data.getElements('Data'):
				if self.has_nested_data():
					self.onNewData(remode=remode)
					return
	
	
	def onNewDoc(self):
		self.data=None
		df=self.document.getElements('Data', depth=1)
		if not df:
			self.graph.killAll()
			self.report("There are no numerical data elements to display")
			return
		df, rem=df[0],df[1:]
		for d in rem:
			if self.preferences["On Multiple Open"]=="Merge":
				combineData(df, d, False)
			elif self.preferences["On Multiple Open"]=="Nest":
				if isSampledType(d)=='e':
					compatLength(df, d)
				d.move(df)
		fn=self.document.fileinformation['filename']
		if fn:
			self.SetTitle(fn)
		self.data = df
		s=self.data.stype()
		if s=='function' or (s in ['events', 'labledevents'] and not self.data.fs()):
			resample(self.data, None)
		elif s=='locus':
			self.spawnViewer(self.data, 'locus')
			self.data=None
			return
		checkd=	self.preferences['Checkpoint Directory']
		if not os.path.exists(checkd):
			os.mkdir(checkd)
		else:
			for f in os.listdir(checkd):
				os.unlink(os.path.join(checkd, f))
		self.onNewData(zoom=True)
	
	def changedat(self, event):
		df=self.document.getElements('Data', depth=1)
		if len(df)<2:
			self.report("There are no data elements to switch to")
			return
		dats=dict([(d.name(),d) for d in df])
		d=self.askUsr("Which element?", dats.keys())
		if d:
			self.data = dats[d]
			self.onNewData(zoom=True)
	
	def combinedat(self, event):
		df=self.document.getElements('Data', depth=1)
		if len(df)<2:
			self.report("There are no additional data elements to combine")
			return
		dats=dict([(d.name(),d) for d in df if d!=self.data])
		d=self.askParam([{'Name':"Which element?",
			'Type':'List', 'Value':dats.keys()},
			{'Name':'Mode','Type':'List','Value':['Nest','Merge']}])
		if not d:
			return
		nd=	dats[d[0]]
		if d[1]=="Merge":
			combineData(self.data, nd, False)
		else:
			if isSampledType(nd)=='e':
				compatLength(self.data, nd)
			nd.move(self.data)
		self.onNewData()
	
	def bindToData(self, data):
		self.document=data.xpath(True)[0]
		self.graph.killAll()
		self.data = data
		self.onNewData(zoom=True)
	
	def launchEditor(self, event=None):
		from mien.interface.main import MienGui
		d=MienGui(self)
		d.newDoc(self.document)
	
	def makeYSep(self, **kw):
		cranges = {}
		tr = 0
		for c in self._channels:
			off = self.offsets.get(c[0], (0.0,0.0,1.0))
			mi, ma=yrange(self.data, c[2])
			ma = ma*off[2]
			ra = ma-(mi*off[2])
			cranges[c[0]] = (ma, ra, off[2], off[1])
			tr += ra
		ran=array([[x[0]-x[1], x[0]] for x in cranges.values()])
		if self.preferences["Display Range"]!="local":
			self._datacache["range"]=(ran[:,0].min(), ran[:,1].max())
		pad = tr*.02
		if pad==0.0:
			pad=1.0
		ra = cranges[self._channels[0][0]]
		self.offsets[self._channels[0][0]] = (0.0, ra[3],ra[2])
		start = ra[0]-ra[1]-pad
		for c in self._channels[1:]:
			ra =  cranges[c[0]]
			off = start - ra[0]
			self.offsets[c[0]] = (off, ra[3],ra[2])
			start = start - ra[1] - pad
	
	def makeLSep(self, **kw):
		"""Generate offsets such that the currently displaped data will use the full vertical range of the graph."""
		st, sp= self. getCurrentView()
		ymin=self.graph.limits[2]
		ymax=self.graph.limits[3]
		r=ymax-ymin
		# print r
		cr=r/len(self._channels)
		#cr=10
		#co=0
		co=ymax
		for c in self._channels:
			off = self.offsets.get(c[0], (0.0,0.0,1.0))
			mi, ma=yrange(self.data, c[2], (st, sp))
			sca=cr/(ma-mi)
			co=co-ma*sca
			self.offsets[c[0]] = (co, off[1], sca)
			co=co+mi*sca
		self._datacache["range"]=(ymin, ymax)
	
	def setcheck(self, event=None, fn=None):
		checkd=	self.preferences['Checkpoint Directory']
		if not os.path.exists(checkd):
			os.mkdir(checkd)
		if fn:
			fn = os.path.join(checkd, fn)
		else:
			d=self.askParam([{'Name':'Checkpoint Name', 'Value':'CheckPoint%i' % (len(os.listdir(checkd)),)}])
			if not d:
				return
			fn = os.path.join(checkd, d[0])
		self.save(ask=False, fname=fn, subelement=self.data, format='mdat')
	
	def getcheck(self, event=None, fn=None):
		checkd=	self.preferences['Checkpoint Directory']
		if not os.path.exists(checkd):
			os.mkdir(checkd)
		files=os.listdir(checkd)
		if not files:
			self.report('No Checkpoints')
			return
		if not fn:
			d=self.askParam([{'Name':'Checkpoint Name', 'Type':'List', 'Value':files}])
			if not d:
				return
			fn = d[0]
		if not fn in files:
			self.report('Unknown Checkpoint')
			return
		fn=os.path.join(checkd, fn)
		doc=self.load(fname=fn, format='mdat', returndoc=True)
		dat=doc.getElements('Data')[0]
		self.data.mirror(dat, True)
		self.update_all(object=self.data)
	
	def makeQSep(self, **kw):
		if not self._datacache.get("range"):
			dat=self.data.getData()
			if 'events' in self.data.stype():
				self._datacache['range']=(0, 1)
			else:
				if self.preferences["Display Range"]!="local":
					st, sp= self.getCurrentView()
					self._datacache['range']=(dat[st:sp,:].min(), dat[st:sp,:].max())
				else:
					self._datacache['range']=(dat.min(), dat.max())
		mi, ma=self._datacache['range']
		off=float(ma)-mi
		for i, c in enumerate(self._channels):
			o=self.offsets.get(c[0], (0.0,0.0,1.0))
			self.offsets[c[0]]=(-1*i*off, o[1], o[2])
	
	def makeYover(self, **kw):
		for c in self._channels:
			off = self.offsets.get(c[0], (0.0,0.0,1.0))
			if 'events' in c[1] or c[1]=='histogram':
				me=0.0
			else:
				me = channel(self.data, c[2]).mean()*off[2]
			self.offsets[c[0]] = (-me, off[1] ,off[2])
	
	def xrange2index(self, sax, spx):
		if sax>spx:
			sax,spx=spx,sax
		if sax<=self.data.start():
			sa=0
		else:
			sa=(sax-self.data.start())*self.data.fs()
		sp=(spx-self.data.start())*self.data.fs()
		if sp>self.data.shape()[0]:
			sp=self.data.shape()[0]
		if sa>=sp:
			print "warning: view indexes out of range"
			return (0, self.data.shape()[0])
		return (round(sa),round(sp))
	
	def getCurrentView(self, index=True):
		if not index:
			return (self.graph.limits[0], self.graph.limits[1])
		else:
			return self.xrange2index(self.graph.limits[0], spx=self.graph.limits[1])
	
	def getMarkIndexes(self):
		mi=[x['loc'] for x in self.graph.xmarkers]
		if not mi:
			return array([])
		mi.sort()
		mi=(array(mi)-self.data.start())*self.data.fs()
		return round(mi)
	
	def equalize(self, mode):
		if mode=='n':
			for k in self.offsets.keys():
				v=self.offsets[k]
				self.offsets[k]=(v[0], v[1], 1.0)
		else:
			if mode=='l':
				ran=self.getCurrentView()
			else:
				ran=None
			cranges = {}
			for c in self._channels:
				off = self.offsets.get(c[0], (0.0,0.0,1.0))
				
				dmin, dmax = yrange(self.data, c[2], ran)
				ra = dmax - dmin
				sc=1.0
				if ra != 0:
					sc = 1.0/ra
				self.offsets[c[0]]=(off[0], off[1], sc)
		self.modes[self.inMode](eq=True)
		self.display()
				
	
	def zeroOffset(self, **kw):
		self.offsets={}
		self._datacache['range']=None
		self._datacache['limits']=None
		self.report("Removed all offsets")
	
	def asImage(self, **kw):
		pass
	
	def doSelectChannel(self, event):
		self.selectedChan = event.GetString()
		offsets = self.offsets.get(self.selectedChan, (0.0,0.0,1.0))
		for i, c in enumerate([self.setYOff, self.setXOff, self.setYscale]):
			c.SetValue(str(offsets[i]))
	
	def doSelectMode(self, event):
		import time; st=time.time()
		self.inMode= event.GetString()
		if self.modes.has_key(self.inMode):
			self.modes[self.inMode]()
		#print time.time()-st
		self.display()
	
	def	doApplyOff(self, event):
		self.report("Setting Offsets")
		offsets = []
		for c in [self.setYOff, self.setXOff, self.setYscale]:
			offsets.append(c.GetValue())
		try:
			offsets = tuple(map(float, offsets))
			self.offsets[self.selectedChan] = offsets
			self.display()
		except:
			self.report("All offsets must have float values")
	
	def selectChannels(self, event=None):
		chans= [x[0] for x in self._channels]
		l = self.askParam([{"Name":"Which Channels?",
							"Type":"Select",
							"Value":chans}])
		if not l or len(l[0])==0:
			return None
		else:
			return [chans.index(x) for x in l[0]]
	
	def markDiff(self, event=None):
		for var in [("X", self.graph.xmarkers), ("Y", self.graph.ymarkers)]:
			if var[1]:
				locs = [m['loc'] for m in var[1]]
				locs.sort()
				fl = locs[0]
				ll = fl
				self.report("%s Differences ----------" % var[0])
				self.report("Min X = %.8g" % fl)
				for l in locs[1:]:
					df = l - fl
					dl = l - ll
					ll = l
					self.report("%s=%.8g: %.8g from min, %.8g from previous" % (var[0], l, df, dl))


	
	def markLoc(self, event=None):
		rep = "\n"
		for m in self.graph.xmarkers:
			t = m['loc']
			i = xindex(self.data, t)
			rep+= "X Mark at %.12g (sample %i)\n" % (t, i)
		for m in self.graph.ymarkers:
			t = m['loc']
			rep+= "Y Mark at %.12g\n" % (t,)
		self.report(rep)
	
	def delChan(self, event=None):
		chans=self.selectChannels()
		if not chans:
			return
		chans=[self._channels[i][2] for i in chans]
		delChans(self.data, chans)
		self.onNewData()
	
	def undo(self, event=None):
		self.data.undo()
		self.onNewData()
	
	def redo(self, event=None):
		self.data.redo()
		self.onNewData()
	
	def crop(self, event=None):
		mode = self.askParam([{"Name":"Crop Mode",
								"Type":"List",
								"Value":["Delete before mark",
										 "Delete after mark",
										 "Crop to view",
										 "By x value",
										 "By sample index"]},
								{'Name':'Set Start Time To 0?',
								"Type":"List",
								"Value":["Yes", "No"]}])
		if not mode:
			return
		mode, reset=mode
		xmin = None
		xmax = None
		if mode == "Crop to view":
			xmin, xmax =  [xindex(self.data, x) for x in self.graph.limits[:2]]
		elif mode == "Delete before mark":
			try:
				xmin = xindex(self.data, self.graph.xmarkers[-1]["loc"])
				xmax=-1
			except:
				self.report("No Markers")
		elif mode == "Delete after mark":
			try:
				xmax = xindex(self.data, self.graph.xmarkers[-1]["loc"])
				xmin = 0
			except:
				self.report("No Markers")
		elif mode == "By x value":
			d=domain(self.data)
			l2 = self.askParam([{'Name':"Start",
								"Value":d[0]},
							   {'Name':"Stop",
								"Value":d[-1]}])
			if l2:
				xmin, xmax =  [xindex(self.data, x) for x in l2]
		elif mode == "By sample index":
			l2 = self.askParam([{'Name':"Start",
								 "Value":0},
								{'Name':"Stop",
								 "Value":self.data.shape()[0]}])
			if l2:
				xmin, xmax = l2
		if xmin==None or xmax==None:
			self.report("Limits not specified")
		else:
			dats=set([x[2][0] for x in self._channels])
			for d in dats:
				dat=self.data.getSubData(d)
				crop(dat, (xmin, xmax))
				if reset=="Yes":
					dat.setAttrib('StartTime', 0.0)
			self.onNewData()
			self.report("Crop complete")
	
	def blank(self, event=None):
		d=self.askParam([{"Name":"Length(s)",
						"Value":100.0},
						{"Name":"Fs (Hz)",
						"Value":10000.0},
						{"Name":"Channels",
						"Value":1}])
		if not d:
			return
		shape=(d[0]*d[1],d[2])
		if self.data:
			dat=zeros(shape, Float32)
			h={'SamplesPerSecond':d[1], 'Labels':["c%i" % i for i in range(shape[1])], 'SampleType':'timeseries'}
			self.data.datinit(dat, h)
		else:
			if not self.document:
				self.newDoc()
			data=blankTimeSeries(shape, {'Name':'new','SamplesPerSecond':d[1]})
			self.document.newElement(data)
			self.data=data
		self.onNewData()
		self.report("Generated Blank Data")
		
	
	def dataImport(self, df, add=False, zoom=False):
		if add and self.data:
			combineData(self.data, df, True)
		else:
			self.newDoc(None)
			self.data=df.clone()
			self.document.newElement(self.data)
			if not zoom:
				zoom=True
		if zoom=='never':
			zoom=False
		self.onNewData(zoom)
		self.report("Done Loading Data")
	
	def displayOther(self, notop=True):
		if self.preferences["Display Range"]!="manual":
			maxY = -100000000
			minY = 1111111111
			trackRange=True
		else:
			trackRange=False
		for i, chan in enumerate(self._channels):
			name, style, ref=chan
			if notop and ref[0]==self.data.dpath():
				continue
			data=channel(self.data, ref)
			opts={'name':name}
			opts['color']=self.plotColors[i][0]
			opts['dashStyle']=self.plotColors[i][1]
			offsets = self.offsets.get(name, (0.0, 0.0, 1.0))
			if 'events' in style:
				opts['style']='raster'
				opts['offset']=offsets[0]
				opts['width']=4
				opts['height']=offsets[2]
				if  trackRange:
					maxY = max(offsets[2], maxY)
					minY = min(offsets[0], minY)
				data=channel(self.data, chan[2])
				if data.shape[1]>2:
					opts['colormode']='periodic'
			elif style=='histogram':
				di=self.data.getSubData(ref[0])
				bin=di.attrib('BinWidth') or 20
				if type(bin)==float:
					bin=round(bin*di.fs())
				opts['offset']=offsets[0]
				opts['binwidth']=bin
				opts['scale']=offsets[2]
				opts['style']='hist'
				if  trackRange:
					maxY = max(offsets[2], maxY)
					minY = min(offsets[0], minY)
			else:
				if style=='ensemble':
					q=self.preferences['Ensemble display mode']
					if q=='Stats':
						me=reshape(mean(data, 1), (-1, 1))
						sd=reshape(std(data, 1), (-1, 1))
						data=concatenate([me-sd, me, me+sd], 1)
					elif q=='Mean':
						data=reshape(mean(data, 1), (-1, 1))
					elif q=='Overlay':
						pass
					elif q=='Sequential':
						r=(data.max(), data.min())
						r=transpose(resize(r, (data.shape[1],2)))
						data=vstack([data, r])
						data=reshape(transpose(data), (-1, 1))
					elif q == 'MeanAndCov':
						cv = cov(data)
						data = reshape(mean(data, 1), (-1, 1))
						strt = domain(self.data.getSubData(ref[0]))[0]+ offsets[1]
						cvst =  strt + data.shape[0]/self.data.fs()
						yp=(self.graph.limits[2],self.graph.limits[3]-self.graph.limits[2])
						self.graph.addPlot(cv, style="image", start=cvst, colorrange='local', offset=yp[0], height=yp[1])
					else:
						print "ensemble display disabled"
						continue
				opts['style'] = self.preferences['defaultPlotStyle']
				if 	offsets[2]!=1.0:
					data = data * offsets[2]
				if offsets[0]:
					data = data + offsets[0]
				if  trackRange:
					if self.preferences["Display Range"]=="global":
						maxY = max(data.max(), maxY)
						minY = min(data.min(), minY)
					elif self.preferences["Display Range"]=="local":
						st, sp= self.getCurrentView()
						maxY = max(data[st:sp,:].max(), maxY)
						minY = min(data[st:sp,:].min(), minY)
			opts['start'] = domain(self.data.getSubData(ref[0]))[0]+ offsets[1]
			pn=self.graph.addPlot(data, **opts)
		if trackRange:
			if 	self._datacache.get("limits"):
				mi ,ma=self._datacache["limits"]
				minY=min(minY, mi)
				maxY=max(maxY, ma)
			self._datacache["limits"]=(float(minY), float(maxY))
	
	
	def getImageData(self):
		scales=[]
		if not self.has_nested_data():
			dat=self.data.getData()
			scales=zeros((1, dat.shape[1]), dat.dtype)
			labs=self.data.getLabels()
			for i in range(dat.shape[1]):
				try:
					l=labs[i]
				except IndexError:
					l=None
				scales[0,i]=self.offsets.get(l, (0.0, 0.0, 1.0))[2]
			if any(scales!=1):
				dat=dat*scales
		else:
			dat=None
			ind=0
			for chan in self._channels:
				name, style, ref=chan
				if 'events' in style:
					evts=self.data.getSubData(ref[0])
					data=events2ts(evts, self.data.shape()[0], self.data.start())
					data=data.astype(Float32)
				else:
					data=channel(self.data, ref)
				if not ind:
					dat=data
				else:
					dat=concatenate([dat, data], 1)
				offsets = self.offsets.get(name, (0.0, 0.0, 1.0))
				if offsets[1]:
					oi=round(offsets[1]*self.data.fs())
					for i in range(ind, ind+data.shape[1]):
						dat[:,i]=shift(dat[:,i], oi)
				scales.extend([offsets[2]]*data.shape[1])
				ind+=data.shape[1]
			scales=array(scales)
			if any(scales!=1):
				dat=dat*scales
		return dat
	
	def displayImage(self):
		dat = self.getImageData()
		cr=self.preferences["Image Contrast"]
		yp=(self.graph.limits[2],self.graph.limits[3]-self.graph.limits[2])
		if self.data.attrib('imageYrange'):
			yp = self.data.attrib('imageYrange')
			self.graph.limit(array([0, self.data.data.shape[0]/self.data.fs(), yp[0], yp[0]+yp[1]]))
		if cr=="local":
			self.graph.addPlot(dat, style="image", start=self.data.start(), colorrange=cr, offset=yp[0], height=yp[1])
		else:
			if cr=="global":
				minval=dat.min()
				maxval=dat.max()
				m=maxval-minval
			else:
				minval, maxval = cr
				dat = where(dat<minval, minval, dat)
				m=maxval-minval
				dat = where(dat>maxval, maxval, dat)
			dat=dat-minval
			if m!=0:
				m=m/255.0
				dat=dat/m
			dat=dat.astype('b')
			self.graph.addPlot(dat, style="image", start=self.data.start(), rawbytes=True, offset=yp[0], height=yp[1])
	
	def displayBlock(self):
		chans=[x for x in self._channels if x[2][0] in ['/', self.data.dpath()]]
		if not chans:
			return
		names = [c[0] for c in chans]
		name= names[0]
		offsets=array([self.offsets.get(c[0], (0.0, 0.0, 1.0)) for c in chans])
		dat = self.data.getData(copy=False)
		if any(offsets[:,1]):
			dat=dat.copy()
			for ind in range(offsets.shape[0]):
				oi=round(offsets[ind,1]*self.data.fs())
				dat[:,ind]=shift(dat[:,ind], oi)
		offsets=offsets.take([0,2], 1)
		if self.preferences["Simple Subsample"]=='Yes':
			plfast=True
		else:
			plfast=False
		self.graph.addPlot(dat, style="polyline", start=self.data.start(), color=[c[0] for c in self.plotColors[:dat.shape[1]]], dashStyle=[c[1] for c in self.plotColors[:dat.shape[1]]], offsets=offsets, fastdraw=plfast, name=name, namelist=names)
		if not self._datacache.get("range"):
			if self.preferences["Display Range"]=="local":
				st, sp= self. getCurrentView()
				self._datacache['range']=(dat[:sp,:].min(), dat[st:sp,:].max())
			else:
				self._datacache['range']=(dat.min(), dat.max())
		mi, ma=self._datacache['range']
		self._datacache["limits"]=(mi+offsets[:,0].min(), ma+offsets[:,0].max())
	
	def display(self):
		#import time;st=time.time()
		self.graph.plots={}
		if self.inMode=="Image":
			self.displayImage()
		else:
			if self.data.stype()=='timeseries' and self.preferences['defaultPlotStyle']!="points":
				self.displayBlock()
				if self.has_nested_data():
					self.displayOther()
			else:
				self.displayOther(notop=False)
			if self.inMode!="Local Sep" and self.preferences["Display Range"]!="manual":
				if not 	self._datacache.get("limits"):
					self._datacache["limits"]=[-1, 2]
				minY, maxY = self._datacache["limits"]
				pad = (maxY - minY)*.05
				if pad==0:
					pad=.01
				self.graph.limits[2] = 	float(minY-pad)
				self.graph.limits[3] = 	float(maxY+pad)
		self.graph.DrawAll()
		#print time.time()-st;st=time.time()



if __name__=='__main__':
	from sys import argv
	app = wx.PySimpleApp()
	x = Dataviewer()
	x.Show(True)
	if len(argv)>1:
		x.load(argv[1])
	app.MainLoop()
	
	
