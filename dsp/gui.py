
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
from mien.datafiles.viewer import Dataviewer
from mien.dsp.widgets import getArgChoice, FunctionFinder
from mien.wx.text import blockIndent
import mien.dsp.modules

import  os, time, inspect

GUIS={}

def blockHelp(obj, gui):
	f = obj.attrib("Function")
	f=mien.dsp.modules.FUNCTIONS[f]
	dl=inspect.getsource(f).split(':')[0][4:]
	if f.__doc__:
		dl+='\n\n'+f.__doc__
	gui.showText(dl)



def clearData(gui):
	doc=gui.document
	dats=doc.getElements('Data', depth=1)
	dats=[x for x in dats if 'AbstractModelData' in x.name()]
	for d in dats:
		d.clearAll()
		
	

def initialData(gui):
	doc=gui.document
	dats=doc.getElements('Data', depth=1)
	dats=[x for x in dats if 'AbstractModelData' in x.name()]
	if not dats:
		dat=gui.createElement("Data", {'Name':'AbstractModelData', 'SampleType':'group'})
		doc.newElement(dat)
		gui.update_all(object=dat, event="Create")
	else:
		dat=dats[0]
		dat.clearAll()
	if hasattr(gui, 'batchfile') and gui.batchfile:
		doc=gui.load(fname=gui.batchfile, append=False, returndoc=True)
		bd=doc.getElements('Data', depth=1)[0]
		dat.mirror(bd, True)	
	return dat	

def ssmatch(k, tk):
	if not tk.endswith(k[-1]):
		return 0
	necm=1
	ss=k[-2:]
	while tk.endswith(ss) and necm<len(k)+2:
		ss=k[necm+1]
		necm+=1
	return necm

def closestmatch(k, l):
	mm=0
	bi=-1
	for i, tk in enumerate(l):
		tm=ssmatch(k, tk)
		if tm>mm:
			mm=tm
			bi=i
	if bi==-1:
		return None
	return l[bi]
		

def editBlock(obj, gui, data=None, viewer=None, args=None, update=True):
	if not args:
		pars=obj.getArguments()
		if GUIS.has_key(obj.attrib("Function")):
			args=GUIS[obj.attrib("Function")](self.dv)
		else:		
			d=getArgChoice(obj.attrib('Function'), data, viewer, previous=pars)
			args={}
			if d:	
				l=gui.askParam(d)
				if not l:
					return False
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
		if not args:
			return False
 	par=obj.getElements("Parameters")
	if par:
		par=par[0]
	else:
		par=gui.createElement("Parameters", {})
		obj.newElement(par)
	par.setValue(args, override=True)
	if update:
		gui.update_all(object=obj, event="Rebuild")
	return True


def d2str(d):
	s=''
	for k in d.keys():
		if type(d[k])==float:
			rok="%.3g" % d[k]
		else:
			rok=repr(d[k])
			if len(rok)>20:
				rok=rok[:8]+'...'+rok[-8:]
		s+=str(k)+':'+rok+'*'
	return s

class DspGui(BaseGui):
	def __init__(self, master=None, **kwargs):
		BaseGui.__init__(self, master, title="Abstract Model Editor", menus=["File", "Model", "Component"], pycommand=True,height=6)

		controls=[["File","Load New Data to Data Sources",self.updateSource],
				  ["File","Save Checkpoint Data",self.cpToFile],
				  ["File","Save Without Data",self.saveInstruct],
				  ["Model","Run Whole Chain",self.runChain],
				  ["Model", "New Viewer", self.launchViewer],
				  ["Model", "New Sub-Data Viewer", self.subViewer],
				  ["Model", "Fix Function Pointers", self.fixFuncs],
				  ["Model", "Print Functions", self.printMod],
				  ["Model", "Reload Model Components", self.bounce],
				  ["Model", "Flush All", self.clean],
				  ["Model", "Start Chain from Checkpoint", self.shortcut],
				  ["Model", "Search Available Components", self.findComponents],
				  ["Model", "List Available Components", self.showComponents],
				  ["Model","Data Editor",self.launchEditor],
				  ["Component","New                (n)",lambda x: self.addMod()],
				  ["Component","Create Check Point (c)",self.makeCheck],
				  ["Component","Create Data Source", self.importData],
				  ["Component","Flush Subsequent   (f)", self.flushMod],
				  ["Component","Edit               (e)", self.editModArgs],
				  ["Component","Move (or use <- or ->)", self.moveMod],
				  ["Component","Delete", self.killMod],
				  ["Component","Inspect            (i)", self.inspectMod],
				  ["Component","Toggle Activatiot  (t)", self.toggleMod],
				  ["Component","Help               (h)", self.helpMod]
				  ]

		self.fillMenus(controls)

		self.preferences={"Debug":1, "Run on Edit":1, "Gui Text Boxes":0, "Always Run to Checkpoint":1, 'Save Data':1}
		
		self.mainSizer = wx.BoxSizer(wx.VERTICAL)

		box=wx.BoxSizer(wx.HORIZONTAL)
		
		box.Add(wx.StaticText(self.main, -1, "Batch Input:"), 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		self.batchin=wx.StaticText(self.main, -1, " None ")
		box.Add(self.batchin, 3, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		self.setBatchButton=wx.Button(self.main, -1, " Set ")
		self.batchfile=None
		wx.EVT_BUTTON(self.main, self.setBatchButton.GetId(), self.setBatch)
		box.Add(self.setBatchButton, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)


		self.mainSizer.Add(box, 0,
						   wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)

		self.sequence=AWList(self.main, -1, style=wx.LC_REPORT
							 | wx.SUNKEN_BORDER
							 | wx.WANTS_CHARS
							 | wx.LC_SINGLE_SEL)

		self.mainSizer.Add(self.sequence, 10,
						   wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		
		self.sequence.InsertColumn(0, "Index")
		self.sequence.InsertColumn(1, "Function")
		self.sequence.InsertColumn(2, "Status")
		self.sequence.SetColumnWidth(1, 300)					  
		wx.EVT_LIST_ITEM_SELECTED(self, self.sequence.GetId(), self.OnItemSelect)
		wx.EVT_LIST_ITEM_RIGHT_CLICK(self, self.sequence.GetId(), self.editModArgs)
		wx.EVT_CHAR(self.sequence, self.OnChar)


		self.keyBindings={'n':self.addMod,
						  'r':self.runMod,
						  'e':self.editModArgs,
						  'f':self.flushMod,
						  't':self.toggleMod,
						  'i':self.inspectMod,
						  'h':self.helpMod,
						  'left':lambda :self.moveMod(None, 'up'),
						  'right':lambda :self.moveMod(None, 'down'),
						  'up':self.sequence.selectLast,
						  'down':self.sequence.selectNext
						  }

		
		self.stdFileMenu()
		self.cleanState()
		self.main.SetSizer(self.mainSizer)
		self.main.SetAutoLayout(True)
		self.mainSizer.Fit(self)
		self.SetSize(wx.Size(600,600))
		self.load_saved_prefs()

	def showText(self, s):
		if self.preferences["Gui Text Boxes"]:
			BaseGui.showText(self, s)
		else:
			print s

	def cleanState(self):
		self.sequenceSelection=None
		self.model=None
		self.data=None
		self.lastrun=None
		self.modified=None
		
	
	def selectModel(self):
		abst=self.document.getElements(['AbstractModel', 'FlowControl'])
		if not abst:
			abst=self.createElement('AbstractModel', {})
			self.document.newElement(abst)
			return abst
		elif len(abst)==1:
			return abst[0]
		else:
			amp={}
			for a in abst:
				amp[a.upath()]=a
			d=self.askParam([{'Name':'Which Model?', 'Type':'List', 'Value':amp.keys()}])
			if not d:
				return None
			return amp[d[0]]	
	
	def onNewDoc(self):
		self.cleanState()
		self.model=self.selectModel()
		if self.model.attrib('defaultBatchFile'):
			self.setBatch(fname=self.model.attrib('defaultBatchFile'))
		self.update_self(object=self.model)
	 
	def setModel(self, mod):
		doc=mod.xpath(True)[0]
		if doc!=self.document:
			self.document=doc
		self.cleanState()
		self.model=mod
		self.update_self(object=self.model)
	
	def bounce(self, event=None):
		mien.dsp.modules
		fl=mien.dsp.modules.refresh()
		if fl:
			self.report('Reload generated some errors: %s' % (str(fl),))
		else:
			self.report("Reload complete")
				
	def killMod(self, event):
		e=self.model.elements[self.sequenceSelection]
		self.modified=self.sequenceSelection
		self.update_all(object=e, event='Delete', dspinternal=1)
		e.sever()
		self.updateList() 

	def cpToFile(self, event):
		dat=self.selectData()
		if dat:
			self.save(subelement=dat[0])

	def save(self, **kwargs):
		"""Overloads the base gui method to handle batch saves. If kwargs specifes 'doc' or 'subelement', or the gui isn't in batch mode, or the preference 'Always Save Data' is True, uses the superclass method"""
		base=False
		if self.preferences['Save Data']:
			base=True
		elif kwargs.has_key('subelement'):
			base=True
		elif kwargs.has_key('doc'):
			base=True
		elif not self.batchfile:
			base=True
		if base:
			BaseGui.save(self, **kwargs)
			return
		self.saveInstruct(None, **kwargs)
		

	def saveInstruct(self, event, **kwargs):
		"""Save nmpml format (or mien format if there are data elements not associated to checkpoints or sources in the model) file without any data components. This will contain a clone of the primary abstract model only, and all data sources and checkpoints will be removed. This file will be much smaller than a full save, and is suitable for use as a batch mode instruction file."""
		el=self.model.clone()
		for e in el.elements[:]:
			if e.name().startswith("Source") and e.attrib('Function')== 'mien.dsp.nmpml.receiveData':
				e.sever()
			elif e.name().startswith("Checkpoint") and e.attrib("Function")== 'mien.dsp.nmpml.sendData':
				e.sever()
		hdat=el.getElements('Data')
		if hdat:
			ext='.mien'
			format='Mien'
		else:
			ext='.nmpml'
			format='nmpml'			
		try:
			fname=self.document.fileinformation["filename"]
			fname=os.path.splitext(fname)[0]
			if not fname.endswith('_bat'):
				fname=fname+'_bat'
		except:
			fname='dsp_instructions_bat'
		fname=fname+ext	
		doc=blankDocument()
		doc.newElement(el)
		kwargs.update({'fname':fname, 'doc':doc, 'format':format})
		if not kwargs.get('ask'):
			kwargs[ask]=False
		BaseGui.save(self, **kwargs)	
		
	def importData(self, event=None):
		'''Get a filename interactively and generate a Data element
from that file, produce a "receiveData" block, nest the new Data element in 
the new block, and point the upath of the block at the data.
The new block appears just before the currently selected location in the sequence
(or location 0 by default), and has parameters recurse:True, dpath:/ 
'''
		doc=self.load(returndoc=True)
		dat=doc.getElements('Data')[0]
		obj=self.createElement('MienBlock', {"Name":"Source",'Function':'mien.dsp.nmpml.receiveData'})
		self.model.newElement(obj)
		ind=self.sequenceSelection or 0
		self.model.reorderElement(obj, ind)
		par=self.createElement("Parameters", {})
		obj.newElement(par)
		obj.newElement(dat)
		par.setValue({'recurse':True, 'dpath':'/', 'upath':dat.upath()})
		self.update_all(object=obj, event="Create")

	def updateSource(self, event=None):
		sources=[]
		for i,e in enumerate(self.model.elements):
			if e.name().startswith("Source") and e.attrib('Function')=='mien.dsp.nmpml.receiveData':
				sources.append("%i %s" % (i, e.name()))
		if not sources:
			self.report("No data sources. Add one using Component->Create Data Source")
			return
		elif len(sources)>1:
			d=self.askParam([{"Name":"Which Source?",
							"Type":"List",
							"Value":sources}])
			if not d:
				return
			sources=d[0]
		else:
			sources=sources[0]
		ind=int(sources.split()[0])
		dat=self.model.elements[ind].getElements("Data")[0]
		doc=self.load(returndoc=True)
		new=doc.getElements('Data')[0]
		dat.mirror(new, True)
		self.modified=ind
		self.update_all(object=dat)
		self.report("loaded")

	def makeCheck(self, event=None):
		'''Produce a "sendData" block, nest a data element inside it, and 
set it's parameters "appropriately" - recurse:True, dpath:"/", upath: points
to the nested data. The block will also have a name beginning with "Checkpoint"
which will cause dsp to treat it differently than other "sendData" elements,
in that it can be used to resume a partially completed run and send data to
viewers. The object is created just after the currently selected block.'''
		obj=self.createElement('MienBlock', {"Name":"Checkpoint",'Function':'mien.dsp.nmpml.sendData'})
		self.model.newElement(obj)
		ind=0
		if self.sequenceSelection!=None:
			ind=self.sequenceSelection+1
		self.model.reorderElement(obj, ind)
		self.modified=ind
		dat=self.createElement("Data", {'Name':'CheckpointData', 'SampleType':'group'})
		obj.newElement(dat)
		par=self.createElement("Parameters", {})
		obj.newElement(par)
		par.setValue({'recurse':True, 'dpath':'/', 'upath':dat.upath()})
		self.update_all(object=obj, event="Create")
			
	def getDataAndViewer(self, index):
		if index<0 or index>=len(self.model.elements):
			if not self.batchfile:
				return (None, None)
			return (initialData(self), None)	
		if self.lastrun==index:
			return (self.data, self.getViewer("DSP: Top"))	
		e=self.model.elements[index]
		d=e.getElements('Data', depth=1)
		if d:
			n="%i - %s" % (index, e.name())
			n="DSP: %s" % n
			return (d[0], self.getViewer(n))	
		return self.getDataAndViewer(index-1)
	
	def editModArgs(self, event=None):
		e=self.model.elements[self.sequenceSelection]
		d, v=self.getDataAndViewer(self.sequenceSelection-1)
		#print d, v
		c=editBlock(e, self, data=d, viewer=v)
		if c:
			self.modified=self.sequenceSelection
			self.update_all(object=e)
			if self.preferences["Run on Edit"]:
				self.runMod()

	def setBatch(self, event=None, fname=None):
		if self.batchfile:
			self.batchfile=None
			self.batchin.SetLabel(' None ')
			self.setBatchButton.SetLabel(' Set ')
			if self.model and self.model.attrib('defaultBatchFile'): 
				del(self.model.attributes['defaultBatchFile'])
		else:
			if not fname:
				dlg=wx.FileDialog(self, message="Select file", style=wx.OPEN)
				dlg.CenterOnParent()
				if dlg.ShowModal() == wx.ID_OK:
					fname=dlg.GetPath()
				else:
					self.report("Canceled File Load.")
					return
			self.batchfile=fname
			self.batchin.SetLabel(fname)
			self.setBatchButton.SetLabel(' UnSet ')
			if self.model:
				self.model.setAttrib('defaultBatchFile', fname)				

	def addMod(self, function=None, args=None):
		if not function:			
			dlg=FunctionFinder(self, module=mien.dsp.modules)
			dlg.CenterOnParent()
			val = dlg.ShowModal()
			if val == wx.ID_OK:
				function=dlg.GetPath()
				dlg.Destroy()
			else:
				dlg.Destroy()
				self.report("Canceled")
				return
		obj=self.createElement('MienBlock', {'Function':function})
		self.model.newElement(obj)
		ind=-1
		if self.sequenceSelection!=None:
			ind=self.sequenceSelection+1
		if ind==-1:
			ind=len(self.model.elements)-1
		self.model.reorderElement(obj, ind)
		self.modified=ind
		d,v=self.getDataAndViewer(ind)
		print d
		editBlock(obj, self, data=d, viewer=v, args=args, update=False)
		self.update_all(object=obj, event="Create")

	def fixFuncs(self, event):
		cantfix=[]
		for i, m  in enumerate(self.model.elements):
			if m.__tag__=='MienBlock':
				try:
					m.getFunction()
				except KeyError:
					cfn=m.attrib('Function')
					nfn=closestmatch(cfn,mien.dsp.modules.FUNCTIONS.keys())
					if not nfn:
						cantfix.append(i)
						print "can't find a substitute for unknown function %s" % cfn
					else:
						print "Function %s not found. Using %s" % (cfn, nfn)
						m.setAttrib('Function', nfn)
		self.updateList()
		if cantfix:
			self.report('failed to correct function for blocks: %s' % (str(cantfix),))
		else:
			self.report('all function names corrected')

	def moveMod(self, event=None, index=None):
		if index==None:
			d=self.askParam([{"Name":"New Index for Module",
							  "Type":"List",
							  "Value":range(len(self.dsp.modules))}])
			if not d:
				return
			index=d[0]
		elif index=="up":
			index=max(0, self.sequenceSelection-1)
		elif index=="down":
			index=min(len(self.model.elements)-1, self.sequenceSelection+1)
		obj=self.model.elements[self.sequenceSelection]
		self.model.reorderElement(obj, index)
		self.modified=index
		self.sequenceSelection=index
		self.update_all(object=self.model, event="Rebuild")



	def update_self(self, **kwargs):
		if not self.model:
			self.sequence.DeleteAllItems()
			return
		if kwargs.get('dspstatus'):
			self.statusreport()
			return
		elif kwargs.get('dspinternal'):
			return
		event=kwargs.get('event', 'modify').lower()
		for obj in self.getObjectsFromKWArgs(kwargs):
			path=obj.xpath(True)
			for el in path:
				if el==self.model:
					self.updateList() 
					return
				
	def statusreport(self):
		dis=self.model.attrib('Disable') or []
		mod=self.modified
		scrub=None
		if mod!=None:
			if self.lastrun<=mod:
				self.lastrun=None
			scrub=mod
			lr=-1
		else:
			lr=self.lastrun
			if lr==None:
				lr=-1
			else:	
				scrub=lr+1
		if scrub!=None:
			self.clearCheckpoints(scrub)		
 		for i in range(len(self.model.elements)):
 			e=self.model.elements[i]
 			if lr==i:
 				dat="TOP: %s" % (str(self.data.shape()),)
 			elif e.name().startswith("Source") and e.attrib("Function")=='mien.dsp.nmpml.receiveData':
				d=e.getElements("Data")[0]
				if d.noData():
					dat="SOURCE: no data"
				else:
					dat="SOURCE: %s" % (str(d.shape()),) 				
 			elif e.name().startswith("Checkpoint") and e.attrib("Function")=='mien.dsp.nmpml.sendData':
				d=e.getElements("Data")[0]
				if d.noData():
					dat="CP: no data"
				else:
					dat="CP: %s" % (str(d.shape()),)
			elif i in dis:
				dat="DISABLED"
			elif i<lr:
				dat="--"
			else:
				dat="(  )"
 			self.sequence.SetStringItem(i, 2, dat)
 		if self.sequenceSelection!=None:
 			self.sequenceSelection=min(self.sequenceSelection, self.sequence.GetItemCount()-1)  
 			self.sequence.SetItemState(self.sequenceSelection, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED,wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)
	
	def updateList(self):
		self.sequence.DeleteAllItems()
		if not self.model:
			return
		comps=self.model.elements[:]
		dis=self.model.attrib('Disable') or []
		for i,m in enumerate(comps):
		 	if m.name().startswith("Source") and m.attrib("Function")=='mien.dsp.nmpml.receiveData':
				lab="data source"
			elif m.name().startswith("Checkpoint") and m.attrib("Function")=='mien.dsp.nmpml.sendData':
				lab="checkpoint"
			else:	
				lab=str(m)
			self.sequence.InsertStringItem(i, str(i))
			self.sequence.SetStringItem(i, 1, lab)	
			#status?
			if i in dis:
				self.sequence.SetItemTextColour(i, wx.Colour(128,128,128))
			else:
				cv=m.checkFunction()
				if cv=='OK':
					self.sequence.SetItemTextColour(i, wx.Colour(0,0,0))
				elif cv=="Unknown Function":
					self.sequence.SetItemTextColour(i, wx.Colour(255,0,0))
				elif cv.startswith('Uns'):
					self.sequence.SetItemTextColour(i, wx.Colour(0,255,0))
				elif cv.startswith('Ex'):
					self.sequence.SetItemTextColour(i, wx.Colour(255,255,0))	
		self.statusreport()


	def getLastData(self, index=0):
		if index<0:
			return (-1, initialData(self))	
		if self.lastrun==index:
			return (index, self.data)
		e=self.model.elements[index]
		if e.name().startswith("Checkpoint") and e.attrib("Function")=='mien.dsp.nmpml.sendData':
			d=e.getElements("Data")[0]
			if not d.noData():
				return (index, d)
		return self.getLastData(index-1)		


	def showComponents(self, event=None):
		funcs={}
		fnl=mien.dsp.modules.FUNCTIONS
		for fn in fnl.keys():
			f=fnl[fn]
			if not funcs.has_key(f.__module__):
				funcs[f.__module__]=[]
			funcs[f.__module__].append(f)	
		text=""
		mods=funcs.keys()
		mods.sort()
		for mn in mods:
			funs=funcs[mn]
			if funs:
				text+="____MODULE %s____\n" % (mn,)
				for fun in funs:
					text+=fun.__name__+"\n"
					if fun.__doc__:
						text+=blockIndent(fun.__doc__, 4)
						text+="\n"
					text+="\n"
		self.showText(text)

	def findComponents(self, event=None):
		d=self.askParam([{"Name":"Search String", "Type":str}])
		if not d:return
		d=d[0]
		fnl=mien.dsp.modules.FUNCTIONS
		hits=[]
		for f in fnl.values():
			if d in f.__name__ or (f.__doc__ and d in f.__doc__):
				hits.append(f)
		if not hits:
			self.report("No matches")
			return 
		text=""	
		for f in hits:
			text+="%s.%s\n" % (f.__module__, f.__name__)
			if f.__doc__:
				text+=blockIndent(f.__doc__, 4)
				text+="\n"
			text+="\n"
		self.showText(text)
			
		

	def clean(self, event=None):
		self.clearCheckpoints(0)
		self.update_self(dspstatus=1)		

	def flushMod(self, event=None):
		i=self.sequenceSelection or 0
		self.clearCheckpoints(i)
		self.update_self(dspstatus=1)		

	def clearCheckpoints(self, scrub):
		lr=self.lastrun or 0
		if scrub<lr:
			clearData(self)
		for i in range(scrub, len(self.model.elements)):
			e=self.model.elements[i]
			if e.name().startswith("Checkpoint") and e.attrib("Function")=='mien.dsp.nmpml.sendData':
				d=e.getElements("Data")[0]
				if not d.noData():
					d.clearAll()
					self.update_all(object=d, dspinternal=1)
					
				
	def getNextCp(self, i):
		if i>=len(self.model.elements)-1:
			return len(self.model.elements)-1
		e=self.model.elements[i]
		if e.name().startswith("Checkpoint") and e.attrib("Function")=='mien.dsp.nmpml.sendData':
			return i
		return self.getNextCp(i+1)	
		
	def runChain(self, event=None):
		self.runMod(event, True) 
		
	def runMod(self, event=None, start=False):
		if self.preferences['Debug']:self.bounce()
		if start:
			dat=initialData(self)
			self.report("Running full abstract model")
			r=None
			i=len(self.model.elements)-1
		else:		
			i=self.sequenceSelection
			datat, data=self.getLastData(i-1)
			if datat>-1 and data!=self.data:
				dat=initialData(self)
				dat.mirror(data, True)
			else:	
				dat=data
			if self.preferences["Always Run to Checkpoint"]:
				i=self.getNextCp(i)
			if datat==i:
				self.report("Already have current data at %i. No need to run" % i)
				return
			if datat==i-1:
				self.report("Running component %i" % (i,))
			else:	
				self.report("Running components %i to %i" % (datat+1, i))
			r=range(datat+1, i+1)
			dis=self.model.attrib('Disable') or []
			r=list(set(r)-set(dis))
			r.sort()
		st=time.time()
		self.model.run(dat, r)
		tt=time.time()-st
		self.data=dat
		dh=dat.getHierarchy()
		dats=""
		for k in dh.keys():
			dats+="%s -> %s\n" % (k, str(dh[k]))
		self.showText(dats)	
		self.lastrun=i
		self.modified=None
		if self.batchfile and (r==None or max(r)==len(self.model.elements)-1):
			fn, ext=os.path.splitext(self.batchfile)
			fn=fn+"_mien_batch.mdat"
			self.save(fname=fn, subelement=dat, ask=False)
		self.report("Run complete in %.2f sec" % tt)
		if not r:
			r=range(len(self.model.elements))	
		self.update_all(object=dat, event="Rebuild", dspinternal=1)
		for i in r:
			e=self.model.elements[i]
			if e.name().startswith("Checkpoint") and e.attrib("Function")=='mien.dsp.nmpml.sendData':
				d=e.getElements("Data")[0]
				self.update_all(object=d, event="Rebuild", dspinternal=1)	
		self.update_self(dspstatus=True)

	def helpMod(self, event=None):
		i=self.sequenceSelection
		fn=self.model.elements[i].attrib("Function")
		f=mien.dsp.modules.FUNCTIONS[fn]
		dl=inspect.getsource(f).split(':')[0][4:]
		if f.__doc__:
			dl+="\n\n"+f.__doc__
		self.showText(dl)

	def OnItemSelect(self, event):
		#print event.GetIndex()
		self.sequenceSelection=event.GetIndex()
		
	def getStupidListSelection(self):
		try:
			id=self.sequence.selected()[0]
		except IndexError:
			id=0
		return id	

	def toggleMod(self, event=None):
		i=self.sequenceSelection
		if not self.model.attrib('Disable'):
			self.model.setAttrib('Disable', [])
		dis=self.model.attrib('Disable')
		if i in dis:
			dis.remove(i)
			self.sequence.SetItemTextColour(i, wx.Colour(0,0,0))
			self.report("Enabled")
		else:
			dis.append(i)
			self.sequence.SetItemTextColour(i, wx.Colour(128,128,128))
			self.report("Disabled")
		
	def OnChar(self, event):
		#self.sequenceSelection=event.GetIndex()
		self.sequenceSelection=self.getStupidListSelection()
		k = self.getKeyFromCode(event.GetKeyCode())
		if self.keyBindings.has_key(k):
			self.keyBindings[k]()
		else:
			#print k
			event.Skip()

	def inspectMod(self, event=None):
		i=self.sequenceSelection
		e=self.model.elements[i]
		s="Module %i, %s:\n\n" % (i, str(e))
		if not e.__tag__=="MienBlock":
			s+=e.__tag__
			self.showText(s)
			return
		try:
			par=e.getElements('Parameters')[0]
			d=par.getValue('dict')
		except:
			d={}
		if not d:
			s+="No Params\n"
		else:
			for k in d.keys():
				s+="%s: [ %s ] %s\n" % (str(k), str(d[k]), str(type(d[k])))
		s+='\n'
		cv=e.checkFunction()
		if cv!='OK':
			s+="!! "+cv+'\n'
		d=e.getElements('Data')
		if d:
			s+="Contains nested Data tags\n"
			for dat in d:
				if dat.noData():
					s+="%s - empty\n" % (dat.name(),)
				else:
					s+="%s - %s\n" % (dat.name(),str(dat.shape()))
			s+="\n"		
		self.showText(s)

	def printMod(self, event=None):
		s="\n".join(self.model.tagScan())
		self.report(s)	
	
	def selectData(self):
		choices=[]
		if self.data:
			choices.append("Top")
		for i, e in enumerate(self.model.elements):
			d=e.getElements('Data', depth=1)
			if d:
				choices.append("%i - %s" % (i, e.name()))
		if not choices:
			self.report('No data to display')
			return
		elif len(choices)>1:	
			d=self.askParam([{"Name":"Show Which Data?",
							"Type":"List",
							"Value":choices}])
			if not d:
				return
			choices=d[0]
		else:
			choices=choices[0]
		if choices=="Top":
			dat=self.data
		else:
			i=int(choices.split()[0])	
			dat=self.model.elements[i].getElements("Data")[0]
		return (dat, choices)		
	
	def launchViewer(self, event):
		dat=self.selectData()
		if not dat:
			return
		dat, name=dat	
		v=Dataviewer(self)
		v.preferences["Display Nested Data to Depth"]=1
		v.graph.legend=True
		v.bindToData(dat)
		v.SetTitle("DSP: %s" %  name)
		v.Show(True)
		
	def	subViewer(self, event):
		choices={}
		for i, e in enumerate(self.model.elements):
			d=e.getElements('Data', depth=1)
			if d:
				if e.name().startswith("Checkpoint"):
					sd=d[0].getHierarchy()
					del(sd['/'])
					for k in sd.keys():
						choices["%i - %s - %s" % (i, e.name(), k)]=sd[k]
		if not choices:
			self.report('No data to display. SubData display requires a checkpoint with complex data currently saved.')
			return
		elif len(choices.keys())>1:	
			d=self.askParam([{"Name":"Show Which Data?",
							"Type":"List",
							"Value":choices.keys()}])
			if not d:
				return
			choices=choices[d[0]]
		else:
			choices=choices.values()[0]
		v=Dataviewer(self) 	
		v.bindToData(choices)
		v.SetTitle("DSP: %s" % str(choices))
		v.Show(True)
		
	def shortcut(self, event):
		choices=[]
		for i in range(len(self.model.elements)):
			m=self.model.elements[i]
			if m.name().startswith("Checkpoint") and m.attrib("Function")=='mien.dsp.nmpml.sendData':
				d=m.getElements('Data', depth=1)
				if d:
					d=d[0]
					if not d.noData():
						choices.append(i)
		if not choices:
			self.report('Requires at least one checkpoint with stored data')
			return
		d=self.askParam([{"Name":"Start from Which Checkpoint?",
							"Type":"List",
							"Value":choices}])
		if not d:
			return
		choices=int(d[0])	
		kill=self.model.elements[:choices]
		el=self.model.elements[choices]
		el.setAttrib("Function", 'mien.dsp.nmpml.receiveData')
		for e in kill:
			e.sever()
		el.setName('Source')
		d=el.getElements('Data', depth=1)[0]
 		par=el.getElements("Parameters")[0]
		par['upath']=d.upath()
		self.update_all(object=self.model, event='rebuild')
		
		
	def getViewer(self, tit):
		plots=self.getAllGuis()
		plots=[x for x in plots if isinstance(x, Dataviewer) and x.GetTitle()==tit]
		if plots:
			return plots[0]
		return None
						
	def launchEditor(self, event=None):
		from mien.interface.main import MienGui
		d=MienGui(self)
		d.newDoc(self.document)
