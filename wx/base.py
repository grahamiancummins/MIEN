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
import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
from mien.wx.dialogs import askParameters, ColorBrowser, manyEntries
from time import strftime
from sys import platform, exc_info
import mien.parsers.fileIO
from mien.parsers.nmpml import blankDocument, createElement, elements
from copy import deepcopy
import sys, os, code, threading, re
from mien.tools.identifiers import getPrefFile, loadPrefs, savePrefs

KEYCODES={13:'enter',
          8:'backspace',
          127:'delete',
          9:'tab',
          27:'escape',
          315:"up",
          317:'down',
          316:'right',
          314:'left',
          32:'space',
          312:'end',
          313:'home',
          323:'insert',
          366:'pageup',
          367:'pagedown',
          16:'popup',
          352:'printscreen',
          310:'break',
          340:'f1',
          341:'f2',
          342:'f3',
          343:'f4',
          344:'f5',
          345:'f6',
          346:'f7',
          347:'f8',
          348:'f9',
          349:'f10',
          350:'f11',
          351:'f12'
          }

def getAllChildren(window):
	child=window.GetChildren()
	rv=[]
	for c in child:
		rv.append(c)
		rv.extend(getAllChildren(c))
	return rv	

def stringToType(s):
	if ',' in s:
		return [stringToType(x) for x in s.split(',')]
	try:
		sat=eval(s)
		return sat
	except:
		return s

if sys.platform=='darwin' and wx.GetOsDescription().startswith("Mac"):
	MAC_CARBON=True
else:
	MAC_CARBON=False  


class AWList(wx.ListCtrl, ListCtrlAutoWidthMixin):
	def __init__(self, parent, ID, **opts):
		wx.ListCtrl.__init__(self, parent, ID, **opts)
		ListCtrlAutoWidthMixin.__init__(self)

	def selected(self):
		selected=[]
		id=-1
		while 1:
			id=self.GetNextItem(id,wx.LIST_NEXT_ALL,wx.LIST_STATE_SELECTED)
			if id==-1:
				break
			else:
				selected.append(id)
		return selected

	def find(self, s):
		id=-1
		while 1:
			id=self.GetNextItem(id)
			if id==-1:
				return -1
			t=self.GetItemText(id)
			if t==s:
				return id


	def selectLast(self):
		try:
			id=self.selected()[0]
		except IndexError:
			id=0
		id=max(0, id-1)
		self.select(id)

	def selectNext(self):	
		try:
			id=self.selected()[0]
		except IndexError:
			id=self.GetItemCount()
		id=min(id+1, self.GetItemCount()-1)
		self.select(id)

	def select(self, id):
		self.SetItemState(id, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

def extractOptions(opts, get):
	'''opts (dict),  get (list) => 2Tuple of dicts
returns one hash (the first return value) containing all the
keys from opt that are in list, and a second containing the remaining keys'''
	oinl ={}
	left ={}
	for k in opts:
		if k in get:
			oinl[k]=opts[k]
		else:
			left[k]=opts[k]
	return (oinl, left)


def textwrap(s, wrap):
	lines=s.split('\n')
	ml=max([len(st) for st in lines])
	if ml<wrap+10:
		return lines
	lines=[]
	s=re.split(r"\s", s)
	lines.append(s.pop(0))
	while s:
		ne=s.pop(0)
		if len(lines[-1])+len(ne)<wrap:
			lines[-1]=lines[-1]+" "+ne
		else:
			lines.append(ne)
	return lines		

class ControlPanel(wx.Panel):
	def __init__(self, parent, clist = [], object=None, **opts):
		wx.Panel.__init__(self, parent, id=-1, **opts)
		sizer =  wx.BoxSizer(wx.VERTICAL)
		self.controls={}
		if object:
			self.object = object[0](self, id=-1, **object[1])
			sizer.Add(self.object, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		for d in clist:
			hsize = wx.BoxSizer(wx.HORIZONTAL)
			for k in d:
				btn = wx.Button(self, -1, k)
				self.controls[k] = btn.GetId()
				hsize.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
			sizer.Add(hsize, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		sizer.Fit(self)

	def bind(self, d):
		for k in d:
			wx.EVT_BUTTON(self, self.controls[k], d[k])

def spawnControlFrame(parent, clist, object, **opts):

	bar = {'style':wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE, 'title':'ControlFrame'}
	for k in bar:
		if opts.has_key(k):
			bar[k]=opts[k]
			del(opts[k])
	frame = wx.Frame(parent, -1,**bar)
	frame.panel = ControlPanel(frame, clist, object, **opts)
	size = frame.panel.GetSize()
	frame.bind = frame.panel.bind
	frame.Show(True)
	frame.SetSize(size)
	return frame

def DeleteObject(gui, objs):
	objs=[o for o in objs if not o.container in objs]
	if not objs:
		return
	check=gui.askUsr("Really delete?" )
	if check!="Yes":
		gui.report("aborted delete")
		return
	if gui.document in objs:
		gui.newDoc()
		return
	c=set([o.container for o in objs])
	if len(c)==1:
		rcont=list(c)[0]
	else:
		rcont=False
	for obj in objs: 
		gui.report("Deleting "+str(obj))
		obj.sever()
		if not rcont:
			gui.update_all(object=objs[0], event='Delete')	
	if rcont:
		gui.update_all(object=rcont, event='Rebuild')

class PyCommand(wx.TextCtrl):
	def __init__(self, parent, id, size):
		wx.TextCtrl.__init__(self, parent, id, size=(size,30))
		wx.EVT_CHAR(self, self.OnChar)
		self.report = parent.report
		self.app = parent
		self.history = []

	def OnChar(self, event):
		key = event.KeyCode
		if key == 13:
			com = self.GetValue()
			self.Clear()
			self.eval(com)
		elif key == 317:
			com =  self.getFromHist()
			self.Clear()
			self.WriteText(com)
		else:
			#319 is down
			#print key
			event.Skip()

	def getEnv(self):
		s="self.app"
		g = globals()
		g.update(sys.modules)
		l = locals()
		return (s, g, l)

	def eval(self, s):
		self.addToHist(s)
		sp, g, l = self.getEnv()
		if sp:
			s = s.replace("self", sp)
		try:
			s=compile(s, "string", "eval")
		except:
			try:
				s=compile(s, "string", "exec")
			except:
				self.report(str(exc_info()[1]))
				return
		try:
			o=eval(s, g, l)
		except:
			o=str(exc_info()[1])
		if type(o)!=type(" "):
			o=str(o)
		self.report(o)

	def addToHist(self, s):
		self.history.append(s)
		if len(self.history)>20:
			self.history = self.history[-20:]	

	def getFromHist(self):
		s = self.history.pop()
		self.history.insert(0, s)
		return s

class FileDropLoad(wx.FileDropTarget):
	def __init__(self, cv):
		self.target=cv
		wx.FileDropTarget.__init__(self)

	def OnDropFiles(self, x, y, fnames):
		doc = mien.parsers.fileIO.readall(fnames)
		if not self.target.document:
			self.target.newDoc(doc)
			return
		for e in doc.getElements():
			e._guiinfo={}
		self.target.document.addDocument(doc)
		self.target.resolveElemRefs()
		self.target.onNewDoc()


		# for fn in fnames:
		# 	self.target.load(fname=fn, append=True)


class BaseGui(wx.Frame):
	def __init__(self, parent, **opts):
		baseopts = {'id':-1, 'title':"WX Base Gui",'style':wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE, 'width':50, 'menus':["File"], 'pycommand':False}
		baseopts.update(opts)
		opts, wxOpts = extractOptions(baseopts, ['width', 'height', 'memory', 'menus', 'panel', 'pycommand', 'TTY', 'showframe'])
		wx.Frame.__init__(self, parent, **wxOpts)
		del wxOpts['id']
		del wxOpts['title']
		self.memory=opts.get("memory", 1000)
		self.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
		mb = self.makeMenus(opts["menus"])
		size = self.GetTextExtent("W")
		self.document=None
		self.preferences={}
		self.preferenceInfo=[]
		self.fileinformation={}
		self.iodefaults={'save':{}, 'load':{}}
		if opts.get("panel"):
			self.main=opts["panel"]
		else:
			self.main = wx.Panel(self, -1, **wxOpts)
		sizer = wx.BoxSizer(wx.VERTICAL)
		if self.mbButtonBar:
			sizer.Add(self.mbButtonBar, 0, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		sizer.Add(self.main, 20, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		if opts.get("TTY")!=None:
			self.hasTTY=opts['TTY']
		else:
			try:
				if os.isatty(sys.stdout.fileno()) and os.isatty(sys.stdin.fileno()):
					self.hasTTY=True
				else:
					self.hasTTY=False
			except:
				self.hasTTY=False
		rh=opts.get('height', 3)
		size=(size[0]*opts["width"]+20, rh*size[1])
		if not rh:
			self.status = None
		elif rh==1:
			self.status =  wx.StaticText(self, -1, "--")
		elif not self.hasTTY:
			self.status=wx.TextCtrl(self, -1, style=wx.TE_READONLY|wx.TE_WORDWRAP|wx.TE_MULTILINE,
						            size=size)
			wx.Log_SetActiveTarget(wx.LogTextCtrl(self.status))
		else:
			self.status =  wx.StaticText(self, -1, "--")

		if opts['pycommand']:
			self.addMainMenu('Python')
			if self.hasTTY:		
				self.addmenucommand(['Python', 'Command Line', self.interact])
				try:
					from IPython.Shell import IPShellEmbed
					self.addmenucommand(['Python', 'iPython', self.ipinteract])
				except:
					pass

				self.addmenucommand(['Python', '(inferior) GUI Command Line ', self.guiinteract])

			else:	
				self.addmenucommand(['Python', 'GUI Command Line ', self.guiinteract])
		if self.status:	
			sizer.Add(self.status, 0, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		self.baseSizer=sizer
		self.dropLoader=FileDropLoad(self)
		#setting this causes a bus error bug if a derived class also sets
		#self droploader to be the drop target for any other widget
		#self.SetDropTarget(self.dropLoader)
		wx.EVT_CLOSE(self, self.onClose)
		if opts.get('showframe', True):
			self.Show(True)

	def onClose(self, event):
		self.Destroy()	

	def stdFileMenu(self):
		fmen=self.menus['File']
		curfmen=fmen.GetMenuItems()
		if curfmen:
			fmen.InsertSeparator(0)
		com =[["New Document",lambda x:self.newDoc(None)],
			  ["Load",lambda x: self.load()],
			  ["Append",lambda x: self.load(append=True)],
			  ["Append Subset",lambda x: self.load(append=True, select=True)],
			  ["Save", lambda x:self.save(ask=False)],
			  ["Save As", lambda x:self.save(ask=True)],
			  ["Save Subset", lambda x:self.save(ask=True, select=True)]]
		if self.preferences.keys():
			com.append(["Preferences", self.setPreferences])
		com.reverse()	
		for command in com:
			id = wx.NewId()
			fmen.Insert(0, id, command[0])
			wx.EVT_MENU(self, id, command[1])
		if curfmen:
			fmen.AppendSeparator()
		id = wx.NewId()
		fmen.Append(id, 'Quit')
		wx.EVT_MENU(self, id, lambda x:self.Destroy())	

	def addmenucommand(self, command):
		if command[1]=="----":
			self.menus[command[0]].AppendSeparator()
		elif type(command[2])==dict:
			self.addMainMenu([command[0], command[1]])
			key=command[2].keys()
			key.sort()
			for k in key:
				self.addmenucommand([command[1], k, command[2][k]])
		else:
			id = wx.NewId()
			self.menus[command[0]].Append(id, command[1])
			wx.EVT_MENU(self, id, command[2])		

	def load_saved_prefs(self):
		p = loadPrefs(self.__class__.__name__)
		if not p:
			if p is None:
				self.report("can't read config file at %s" % (getPrefFile(self.__class__.__name__).name,))
			else:
				#self.report('no config information')
				pass
			return	
		self.preferences.update(p)

	def setPreferences(self, event, pd=None):
		if not pd:
			pd=deepcopy(self.preferenceInfo)
		pdk=[x['Name'] for x in pd]
		for k in self.preferences.keys():
			if not k in pdk:
				pd.append({"Name":k, "Value":self.preferences[k]})
				pdk.append(k)
			else:
				i=pdk.index(k)
				pd[i]['Default']=self.preferences[k]		
		d=self.askParam(pd)
		if not d:
			return
		for i, p in enumerate(pdk):
			self.preferences[str(p)]=d[i]
		self.onSetPreferences()
		savePrefs(self.__class__.__name__, self.preferences)

	def onSetPreferences(self):
		self.report("Set Preferences")	

	def interact(self, event=None, ns={}):
		l=globals()
		l.update(locals())
		if ns:
			l.update(ns)
		l['gui']=self
		t=threading.Thread(target=code.interact, args=("Interactive (name 'gui' bound to creating object)",), kwargs={'local':l})
		t.start()

	def getObjectsFromKWArgs(self, d):
		objs=[]
		if d.has_key('object'):
			objs.append(d['object'])
		objs.extend(d.get('objects', []))
		if not objs:
			objs.append(self.document)
		return objs


	def ipinteract(self, event=None, ns={}):
		l=globals()
		l.update(locals())
		if ns:
			l.update(ns)
		l['gui']=self
		from IPython.Shell import IPShellEmbed
		ipshell = IPShellEmbed(argv=[])
		t=threading.Thread(target=ipshell, args=(), kwargs={'local_ns':l})
		t.start()

	def guiinteract(self, event=None, ns={}):
		l=globals()
		l.update(locals())
		if ns:
			l.update(ns)
		l['gui']=self
		import wx.py.crust
		f=wx.py.crust.CrustFrame(self, locals=l)
		f.Show(True)
		#print "gui"

	def addMainMenu(self, name):
		if type(name)==type(" "):
			if self.mbButtonBar:
				if type(name)!=str:
					name = name[-1]
				self.menus[name]=wx.Menu()
				mButton = wx.Button(self, -1, name)
				self.mbButtonBar.Add(mButton, 0, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
				def popUpMB(event):
					self.PopupMenu(self.menus[name], mButton.GetPosition())
				wx.EVT_BUTTON(self, mButton.GetId(), popUpMB)
			else:
				self.menus[name]=wx.Menu()
				self.menuBar.Append(self.menus[name], name)
		else:
			n=name[-1]
			parent=name[0]
			self.menus[n]=wx.Menu()
			id = wx.NewId()
			self.menus[parent].AppendMenu(id, n, self.menus[n])


	def getKeyFromCode(self, i):
		if KEYCODES.has_key(i):
			return KEYCODES[i]
		try:
			c=chr(i)
		except:
			c=i
		return c	

	def makeMenus(self, names):
		self.mbButtonBar = None
		if True or MAC_CARBON:
			self.menuBar = None
			self.mbButtonBar = wx.BoxSizer(wx.HORIZONTAL)
		else:	
			self.menuBar = wx.MenuBar()
			self.SetMenuBar(self.menuBar)
		self.menus={}
		for n in names:
			self.addMainMenu(n)

	def fillMenus(self, cl):
		for command in cl:
			self.addmenucommand(command)

	def clearMenu(self, menu):
		mis = self.menus[menu].GetMenuItems()
		mis=list(mis)
		while mis:
			mi = mis.pop()
			self.menus[menu].Delete(mi.GetId())

	def refreshMenu(self, menu, dict):
		if self.menus.has_key(menu):
			self.clearMenu(menu)
		else:
			self.addMainMenu(menu)
		keys = dict.keys()
		keys.sort()
		for k in keys:
			self.addmenucommand([menu, k, dict[k]])


	def askParam(self, d):
		d = askParameters(self, d)
		if not d:
			self.report("Canceled Parameter Dialog")
		return d

	def quickParam(self, l):
		'''l is a list of names. Construct and display an askParameters dialog with a string entry for each name. Cast the resulting strings to python types if possible, and return a list of the result'''
		d=[]
		for n in l:
			d.append({'Name':n, 'Type':str})
		d=self.askParam(d)
		if not d:
			return []
		return [stringToType(x) for x in d]	


	def report(self, text):
		text = "-- %s -- %s\n" % (strftime("%H:%M:%S"), text)
		if self.hasTTY:
			print text[:-1]
		if not self.status:
			return
		if self.status.__class__==wx.StaticText:
			text=text.split("\n")[0][:80]
			self.status.SetLabel(text)
		else:
			self.status.AppendText(text)
			l = self.status.GetLastPosition()
			if l>self.memory:
				self.status.Remove(0, l-self.memory)
				l = self.status.GetLastPosition()
			self.status.ShowPosition(self.status.GetLastPosition())


	def showText(self, s, t="Text Output", wrap=80):
		if wrap:
			lines=textwrap(s, wrap)
		else:	
			s=s.replace("\t", "    ")
			s=s.rstrip()
			lines=s.split('\n')
		bar = {'style':wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE, 'title':t}
		frame = wx.Frame(self, -1,**bar)
		sizer = wx.BoxSizer(wx.VERTICAL)
		h=max(5, len(lines))
		lls=[len(x) for x in lines]
		longest=lines[lls.index(max(lls))]
		longest=longest.replace(" ", "W")
		size = self.GetTextExtent(longest)
		h=max(5, len(lls))
		size=(size[0]+40, h*size[1]+5)
		tc=wx.TextCtrl(frame, -1, style=wx.TE_READONLY|wx.TE_WORDWRAP|wx.TE_MULTILINE, size=size)
		size = self.GetTextExtent(longest)
		sizer.Add(tc, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		btn = wx.Button(frame, wx.ID_OK, " OK ")
		btn.SetDefault()
		wx.EVT_BUTTON(frame, wx.ID_OK, lambda x:frame.Destroy())
		sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		frame.SetSizer(sizer)
		frame.SetAutoLayout(True)
		frame.Show(True)
		sizer.Fit(frame)
		tc.AppendText(s)

	def alertUsr(self, s):
		dlg = wx.MessageDialog(self, s, 'Alert', wx.OK)
		dlg.CenterOnParent()
		dlg.ShowModal()
		dlg.Destroy()

	def askUsr(self, s, choices=["Yes","No"]):
		dlg = wx.SingleChoiceDialog(self, s, 'User Input', choices, wx.OK|wx.CANCEL)
		dlg.CenterOnParent()
		if dlg.ShowModal() == wx.ID_OK:
			return dlg.GetStringSelection()
		else:
			self.report("Canceled Choice Dialog")
			return ""
		del(dlg)

	def load(self, event=None, fname=None, append=False, **kwargs):
		for k in self.iodefaults['load'].keys():
			if not kwargs.has_key(k):
				kwargs[k]=self.iodefaults['load'][k]
		if not fname:
			loaddir=self.fileinformation.get('load directory')
			if not loaddir:
				try:
					fn=self.document.fileinformation["filename"]
					loaddir=os.path.split(fn)[0]
				except:
					loaddir=os.getcwd()
			dlg=wx.FileDialog(self, message="Select file", defaultDir=loaddir, style=wx.OPEN)
			dlg.CenterOnParent()
			if dlg.ShowModal() == wx.ID_OK:
				fname=dlg.GetPath()
				self.fileinformation['load directory']=os.path.split(fname)[0]
			else:
				self.report("Canceled File Load.")
				return
		self.report("Loading file  %s" % fname)
		kwargs["gui"]=self		
		doc = mien.parsers.fileIO.read(fname, **kwargs)
		if kwargs.get('returndoc'):
			return doc
		self.SetTitle(fname)
		self.report("Importing %i objects" % len(doc.elements))
		if self.document and append:
			for e in doc.getElements():
				e._guiinfo={}
			self.document.addDocument(doc)
			self.resolveElemRefs()
			self.onNewDoc()
		else:
			self.newDoc(doc) 

	def askForFile(self, existing=True):
		if existing:
			dir=self.fileinformation.get('load directory')
			if not dir:
				try:
					fn=self.document.fileinformation["filename"]
					dir=os.path.split(fn)[0]
				except:
					dir=os.getcwd()
			dstyle=wx.OPEN	
		else:
			dir=self.fileinformation.get('save directory')
			if not dir:
				try:
					dir=self.document.fileinformation["filename"]
					dir=os.path.split(dir)[0]
				except:
					dir=os.getcwd()
			dstyle=wx.SAVE
		dlg=wx.FileDialog(self, message="Select file", defaultDir=str(dir), style=dstyle)
		dlg.CenterOnParent()
		if dlg.ShowModal() == wx.ID_OK:
			return dlg.GetPath()	
		else:
			self.report("Canceled File Choice.")
			return ""


	def onNewDoc(self):
		pass

	def getAllGuis(self):
		q=self
		p=q.GetParent()
		while p:
			q=p
			p=q.GetParent()
		wins=[q]+getAllChildren(q)
		wins=[q for q in wins if isinstance(q, BaseGui)]
		return wins

	def update_all(self, **kwargs):
		for g in self.getAllGuis():
			g.update_self(**kwargs)

	def update_self(self, **kwargs):
		pass

	def resolveElemRefs(self):
		er=self.document.getElements('ElementReference')
		for e in er:
			try:
				e.setTarget()
			except:
				self.report('cant find target for reference %s' % (str(e),))

	def newDoc(self, doc=None):
		if self.document and doc==self.document:
			return
		try:	
			self.document.sever()
			del(self.document)
		except:
			pass
		if doc:
			self.document = doc
		else:	
			self.document = blankDocument()
		self.document._owner=self
		self.document._guiinfo={}
		for e in self.document.getElements():
			e._guiinfo={}
		self.resolveElemRefs()
		self.onNewDoc()

	def createElement(self, tag, attrs, cdata=None):
		o=createElement(tag, attrs, cdata)
		o._guiinfo={}
		return o

	def save(self, **kwargs):
		for k in self.iodefaults['save'].keys():
			if not kwargs.has_key(k):
				kwargs[k]=self.iodefaults['save'][k]
		ask=kwargs.get('ask', True) 
		fname=kwargs.get('fname')
		sev=False
		if kwargs.has_key('doc'):
			doc=kwargs['doc']
			del(kwargs['doc'])
		elif kwargs.has_key('subelement'):
			el=kwargs['subelement']
			del(kwargs['subelement'])
			el=el.clone()
			doc=blankDocument()
			doc.newElement(el)
			sev=el
		else:	
			doc=self.document
		if kwargs.has_key('fname'):
			del(kwargs['fname'])
		else:	
			try:
				fname=self.document.fileinformation["filename"]
			except:
				fname=None
		if not fname:
			ask=True
		if kwargs.get('select'):
			kwargs['gui']=self
			doc=mien.parsers.fileIO.select_elements(doc, **kwargs)	
		if ask:
			if kwargs.get('format'):
				f=kwargs['format']
				formats=[f]
				ext=mien.parsers.fileIO.filetypes[f]['extensions'][0]
				formatstring="%s |*%s" % (f, ext)
			else:
				formats=['guess']+mien.parsers.fileIO.legal_formats(doc)
				formatstring="guess from filename | * |"
				for f in formats[1:]:
					ext=mien.parsers.fileIO.filetypes[f]['extensions'][0]
					formatstring+=f+" |*"+ext+"|"
				formatstring=formatstring[:-1]	
			dir=self.fileinformation.get('save directory')
			if not dir:
				try:
					dir=self.document.fileinformation["filename"]
					dir=os.path.split(dir)[0]
				except:
					dir=os.getcwd()
			dlg=wx.FileDialog(self, message="Save to File", defaultDir=str(dir), style=wx.SAVE, wildcard=formatstring)
			dlg.SetFilterIndex(0)
			dlg.CenterOnParent()
			if dlg.ShowModal() == wx.ID_OK:
				fname=str(dlg.GetPath())
				format=formats[dlg.GetFilterIndex()]
			else:
				self.report("Canceled")
				return
			kwargs['format']=format
			kwargs['forceext']=True
			dir=os.path.split(fname)[0]	
			self.fileinformation['save directory']=dir
			doc.fileinformation["filename"]=fname
			doc.fileinformation["type"]=format
		check=mien.parsers.fileIO.write(doc, fname, **kwargs)
		if sev:
			el.sever()
			doc.sever()
		if check:
			try:
				fname=kwargs['wrotetourl']
			except:
				pass
			self.report("Wrote to %s" % fname)
		else:
			self.report('save failed')

def do_test(frame, event):
	#frame.alertUsr("Testing")
	#l="foo"
	l=frame.askUsr("Test Question", ["foo", "bar"])
	sub = {"First":[{"Name":"booga",
		             "Type":type(" ")},
		            {"Name":"ooga",
		             "Type":type(1.0)}],
		   "Next":[{"Name":"auto?",
		            "Type":"List",
		            "Value":["yes", "no"]}],
		   "Last":[{"Name":"foo",
		            "Type":type(" ")},
		           {"Name":"bar",
		            "Value":5.0}]}
## 	l = frame.askParam([{"Name":"Color",
## 						 "Type":type((1,)),
## 						 "Value":(255,255,255),
## 						 "Browser": ColorBrowser},
## 						{"Name":"Spam",
## 						 "Type":type(1.0),
## 						 "Value":2.0},
## 						{"Name":"Plot",
## 						 "Type":"List",
## 						 "Value":[1,2,3]}
## 						,
## 						{"Name":"How?",
## 						 "Type":"Choice",
## 						 "Value":sub}
## 						])
	frame.report(str(l))


if __name__=='__main__':
	app = wx.PySimpleApp()
	frame = BaseGui(None)
	controls=[["File","----"],
		      ["File", "Quit", lambda x:frame.Destroy()]]
	frame.fillMenus(controls)
	wx.EVT_LEFT_DOWN(frame.main, lambda x :do_test(frame, x))
	frame.Show(True)
	app.MainLoop()


