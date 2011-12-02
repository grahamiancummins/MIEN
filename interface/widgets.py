
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
from mien.wx.dialogs import wx, FileBrowse, askParameters, DirBrowse



def lowerCaseSort(s1, s2):
	return cmp(s1.lower(), s2.lower())

def xpathBrowser(master, dict, control, tags= [], attribs = {}):
	els = [x.upath() for x in master.document.getElements(tags, attribs)]
	d=master.askParam([{"Name":"Path",
						"Type":"List",
						"Value":els}])
	if d:
		control.SetValue(d[0])	


class TreeBrowser(wx.Dialog):
	def __init__(self, parent, options, **wxopts):
		if not wxopts.get('title'):
			wxopts['title']="Browse Tree"
		self.options=options
		doc=self.options.get('doc') or parent.document
		self.elements=[]
		wx.Dialog.__init__(self, parent, -1, **wxopts)
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.tree = wx.TreeCtrl(self, -1, style = wx.TR_SINGLE|wx.TR_HAS_BUTTONS)
		sizer.Add(self.tree, 6, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		wx.EVT_TREE_SEL_CHANGED(self.tree, self.tree.GetId(), self.setNode)
		self.fillTree(doc)

		pl=self.options.get("selectionlabel", "Selection")
		mult=self.options.get('multiple')
		if mult:
			pl=pl+" (double-click to remove)"
		btn = wx.StaticText(self, -1, pl)
		sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		if not mult:
			self.selected = wx.TextCtrl(self, -1, "/", size = (500,-1))
		else:
			self.selected=wx.ListCtrl(self, -1, style=wx.LC_SINGLE_SEL, name="upath", size=(500,100))
			wx.EVT_LIST_ITEM_ACTIVATED(self, self.selected.GetId(), self.deselect)
		sizer.Add(self.selected, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 2)

		box = wx.BoxSizer(wx.HORIZONTAL)
		btn = wx.Button(self, wx.ID_OK, " OK ")
		btn.SetDefault()
		box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		btn = wx.Button(self, wx.ID_CANCEL, " Cancel ")
		box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		sizer.Add(box, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		sizer.Fit(self)


	def setNode(self, event=None):
		item = event.GetItem()
		try:
			obj = self.tree.GetPyData(item)
		except:
			return
		if self.options.get('filter'):
			if not obj.__tag__ in self.options['filter']:
				return
		if self.options.get('data'):
			s=obj.dpath()
		else:
			s=obj.upath()
		if self.options.get('multiple'):
			self.selected.InsertStringItem(0, s)
			self.elements.insert(0, obj)
		else:	
			self.selected.SetValue(s)
			self.elements=[obj]

	def noadd(self, obj):
		f=self.options.get('filter')
		if not f:
			return False
		if obj.__tag__ in f:
			return False
		if obj.getElements(f):			
			return False
		return True
		
	def addKidz(self, node, parent):
		for obj in node.elements:
			if self.noadd(obj):
				continue
			id = self.tree.AppendItem(parent, str(obj))
			if parent != self.tree.GetRootItem():
				self.tree.Collapse(id)
			else:
				self.tree.EnsureVisible(id)
			
			self.tree.SetPyData(id, obj)
			self.addKidz(obj, id)

	def deselect(self,event):
		id = event.GetIndex()
		self.selected.DeleteItem(id)
		self.elements.pop(id)

	def fillTree(self, doc):
		id=self.tree.AddRoot(str(doc))
		self.tree.SetPyData(id, doc)
		self.addKidz(doc, id)

	def getElements(self):
		return self.elements

	def getPath(self, event=None):
		if self.options.get('multiple'):	
			return [e.upath() for e in self.elements]
		else:
			return self.selected.GetValue()
		
def browseTree(master, dict, control):
	'''Simple interface to get a single upath from an nmpml tree'''
	dlg=TreeBrowser(master, {})
	dlg.CenterOnParent()
	val = dlg.ShowModal()
	if val == wx.ID_OK:
		control.SetValue(dlg.getPath())	
	dlg.Destroy()

def selectTreePath(master, options):
	'''More advanced interface to get a single upath from an nmpml tree. The options dictionary is passed directly to a TreeBrowser class. The return value will be a string (path) if options doesn't set "multiple", otherwise it will be a list of strings.'''  
	dlg=TreeBrowser(master, options)
	dlg.CenterOnParent()
	val = dlg.ShowModal()
	if val == wx.ID_OK:
		path=dlg.getPath()
	else:
		path=None
	dlg.Destroy()
	return path

def selectTreeElement(master, options):
	'''Just like selectTreePath, but the return value is always a list of instances (this will be a length 1 list if options doesn't set "multiple")'''
	dlg=TreeBrowser(master, options)
	dlg.CenterOnParent()
	val = dlg.ShowModal()
	if val == wx.ID_OK:
		els=dlg.getElements()
	else:
		els=[]
	dlg.Destroy()
	return els
	

def select(doc, **kwargs):
	'''Interface to extract a subset of an nmpml document '''
	if len(doc.getElements())<2:
		return doc
	elements=[]
	gui=kwargs.get('gui', True)
	if gui is True:
		gui=None
	dlg=TreeBrowser(gui, {"multiple":True, 'doc':doc})
	dlg.CenterOnParent()
	val = dlg.ShowModal()
	if val == wx.ID_OK:
		elements=dlg.getElements()
	else:
		return doc
	dlg.Destroy()
	unique=[]
	
	for e in elements:
		par=e.xpath(True)[:-1]
		for pe in par:
			if pe in elements:
				break
		else:
			unique.append(e)
	if kwargs.get('prune'):
		doc.elements=[]		
		for e in unique:
			e.container=None
			doc.newElement(e)
	else:	
		from mien.parsers.nmpml import blankDocument
		doc = blankDocument()
		for e in unique:
			doc.newElement(e.clone())
	return doc


def optionPanel(title, choices, gui):
	if gui is True:
		dlg = wx.SingleChoiceDialog(None, title, 'User Input', choices, wx.OK|wx.CANCEL)
		dlg.CenterOnParent()
		if dlg.ShowModal() == wx.ID_OK:
			return dlg.GetStringSelection()
		else:
			print "Canceled Choice Dialog"
			return ""
		del(dlg)
	else:
		return gui.askUsr(title, choices)

	



def selectDvData(source, **kwargs):
	header=source.header
	args={'chans':None, 'start':0, 'stop':None, 'SR':None}
	gui=kwargs.get('gui', True)
	if gui is True:
		gui=None
#	d = askParameters(gui, d)
	cns = header["Labels"]
	toomany=False
	if len(cns)>35:
		toomany=len(cns)
		modes=self.modes.keys()
		cns=["Load all (%i) channels" % toomany, "Select channels using ranges"]
	fs = header.get("SamplesPerSecond", 1.0)
	l = askParameters(gui, [{"Name":"Start",
						"Value":0},
					   {"Name":"Stop",
						"Value":int(header["Length"])},
					   {"Name":"Channels",
						"Type":"Select",
						"Value":cns},
					   {"Name":"Set SamplesPerSecond",
						"Value":fs},
						{"Name":'Down-sample', 'Value':0}
					   ])
	if not l:
		args['abort']=True
		return args
	start, stop, chans, set_sr, down = l[0], l[1], l[2], l[3], l[4]
	if chans:
		if not toomany:
			chans = [cns.index(x) for x in chans]
		elif "Select" in chans:
			d=askParameters(gui, [{"Name":"Channels (python list or range from %i total channels)" % toomany,
									"Value":"range(10)"}])
			try:
				chans=eval(d[0])
			except:
				chans=range(10)
	return {'Channels':chans, 'Start':start, 'Stop':stop, 'SamplesPerSecond':set_sr, 'Downsample':down}


class FunctionFinder(wx.Dialog):
	def __init__(self, parent, id=-1, module=None, **opts):
		self.module=module
		wxopts = {'title':"Browse Functions"}
		wxopts.update(opts)
		wx.Dialog.__init__(self, parent, id, **wxopts)
		funcs={}
		for fn in self.module.FUNCTIONS.keys():
			f=self.module.FUNCTIONS[fn]
			if not funcs.has_key(f.__module__):
				funcs[f.__module__]=[]
			funcs[f.__module__].append(fn)	
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.tree = wx.TreeCtrl(self, -1, style = wx.TR_SINGLE|wx.TR_HAS_BUTTONS)
		sizer.Add(self.tree, 6, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		wx.EVT_TREE_SEL_CHANGED(self.tree, self.tree.GetId(), self.setName)
		self.fillTree(funcs)

		btn = wx.StaticText(self, -1, " Function ")
		sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		self.path = wx.TextCtrl(self, -1, "None", size = (500,-1))
		sizer.Add(self.path, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)

		box = wx.BoxSizer(wx.HORIZONTAL)
		btn = wx.Button(self, wx.ID_OK, " OK ")
		btn.SetDefault()
		box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		btn = wx.Button(self, wx.ID_CANCEL, " Cancel ")
		box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		sizer.Add(box, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		sizer.Fit(self)


	def setName(self, event=None):
		id = event.GetItem()
		nc = self.tree.GetChildrenCount(id)
		if nc:
			#print nc
			return
		s=self.tree.GetItemText(id)
		self.path.SetValue(s)


	def fillTree(self, funcs):
		root=self.tree.AddRoot('Functions')
		fks=funcs.keys()
		fks.sort()
		for mod in fks:
			id = self.tree.AppendItem(root, mod)
			self.tree.EnsureVisible(id)
			mif=funcs[mod]
			mif.sort(lowerCaseSort)
			for func in mif:
				id2=self.tree.AppendItem(id, func)
				self.tree.Collapse(id2)

	def GetPath(self, event=None):
		return self.path.GetValue() 

def browseBlockFunctions(master, dict, control):
	import mien.dsp.modules
	dlg=FunctionFinder(master, module=mien.dsp.modules)
	dlg.CenterOnParent()
	val = dlg.ShowModal()
	if val == wx.ID_OK:
		control.SetValue(dlg.GetPath())	
	dlg.Destroy()


ARGBROWSERS={"filename":FileBrowse,
			 "dirname":DirBrowse,
			 "fname":FileBrowse,
			 "upath":browseTree} 
			
def lsort(s1,s2):
	return cmp(len(s1), len(s2))

def getArgBrowser(arg, abd):
	if abd.has_key(arg):
		return abd[arg]
	keys=abd.keys()
	keys.sort(lsort)
	ab=None
	for k in keys:
		if arg.startswith(k):
			ab=abd[k]
	return ab			

ATTRIBUTE_BROWSERS ={"ElementReference":{"Target":browseTree},
					 "Data":{"Url":FileBrowse},
					 "GeneticAlgorithm":{'Directory':DirBrowse,
										 'DistributerProfile':browseTree},
					 "AbstractModel":{'Distributer':browseTree},
					 "ScriptEval":{'Distributer':browseTree},
					 "MienBlock":{'Function': browseBlockFunctions}}

