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

import os
from mien.wx.base import *
import mien.interface.widgets
from mien.math.array import *
import mien.blocks
import mien.interface.wxobjectedit
import mien.interface.search


EXPANSION_MODS = [
				  'mien.interface.componentApps',
				  'mien.interface.abstract',
 				  'mien.interface.modelbuilder',
  				  'mien.interface.optimizers',
  				  'mien.interface.simulatorcontrol',				  
 				  'mien.interface.inputs',
 				  'mien.interface.alignment',
			 	  'mien.interface.parallel'
				]

CORE_MECM={}
CORE_ME={}

def makeCMCheck(l):
	def foo(los):
		if len(los)!=1:
			return False
		if los[0] in l:
			return True
		return False		
	return foo

def assignCMCheck(d):
	z={}
	for k in d.keys():
		try:
			f, c=d[k]
			if not callable(c):
				if type(c) in [str, unicode]:
					c=[c]
				c=makeCMCheck(c)
			z[k]=(f,c)
		except:
			print('failed to bind MECM extension %s' % str(d))
	return z			
			
for m in EXPANSION_MODS:
	exec("import %s as mod" % m)
	CORE_MECM.update(assignCMCheck(mod.MECM))
	CORE_ME.update(mod.ME)


def CreateObject(gui, elems):
	obj=elems[0]
	try:
		children = elements[obj.__tag__]._allowedChildren
	except:
		children=None
	if children == None:
		children = elements.keys()
	if not children:
		gui.report("The selected object can not contain child objects")
		return
	children.sort()
	ct = gui.askUsr("New Object Class:", children)
	if not ct:
		return
	atr = 	gui.getElemAttribs(ct)
	if atr == None:
		return
	e=gui.makeElem(ct, atr, obj)	

def cliobject(gui, elems):
	obj=elems[0]
	gui.interact(ns={'el':obj})		

def moveOrCopy(gui, elems):
	if gui.document in elems:
		gui.report("Can't move the toplevel object (use 'save as'+'add')")
		return
	gui.object_to_move=elems
	if len(elems)==1:
		gui.report("Picked up object %s" % elems[0].upath())
	else:
		gui.report("Picked up %i objects" % (len(elems),))
		

def rebuildTree(gui, elems):
	obj = elems[0]
	if obj != gui.document:
		gui.update_all(object=obj, event="Rebuild")
	else:
		gui.onNewDoc()

def classHelp(gui, elems):
	obj = elems[0]
	s = obj.__tag__+"\n"+obj.__class__.__doc__
	gui.showText(s)		

def DeleteObject(gui, objs):
	objs=[o for o in objs if not o.container in objs]
	if not objs:
		return
	check=gui.askUsr("Really delete?" )
	if check!="Yes":
		gui.report("aborted delete")
		return
	gui.objecttree.UnselectAll()
	gui.contextMenuSelect=[]	
	if gui.document in objs:
		gui.newDoc()
		return
	c=set([o.container for o in objs if o.container])
	while len(c)>1:
		c = set([o.container for o in c if o.container])
	rcont=list(c)[0]
	for obj in objs: 
		gui.report("Deleting "+str(obj))
		obj.sever()
	if rcont:
		gui.update_all(object=rcont, event='Rebuild')	


def setManyAttributes(gui, objs):
	attrs = None
	for s in objs:
		if attrs:
			attrs = attrs.intersection(set(s.attributes.keys()))
		else:
			attrs = set(s.attributes.keys())
	attrs=list(attrs)
	if 'Name' in attrs:
		attrs.remove('Name')
	attrd = []
	for p in attrs:
		attrd.append({"Name":p,
					  "Type":str,
					  "Optional":1})
	dp = {"Add Attrib":[{"Name":"Attribute",
						 "Type":str},
						{"Name":"Value",
						 "Type":str}],
		  "Del Attrib":[{"Name":"Which",
						 "Type":"List",
						 "Value":list(attrs)}],
		  "Set Attribs":attrd}
	d = gui.askParam([{"Name":"Action",
						"Type":"Choice",
						"Value":dp}])
	if not d:
		return 	
	d=d[0]
	if d[0]=="Del Attrib":
		for o in objs:
			del(o.attributes[d[1]])
	elif d[0]=="Add Attrib":
		for o in objs: 
			o.setAttrib(d[1],d[2])
	else:
		newattrs = {}
		for i, a in  enumerate(attrs):
			if d[i+1]:
				for o in objs:
					o.setAtrib(a,d[i+1])
	for o in objs:
		gui.update_self(object=o, event='Modify')				

def followRefs(gui, objs):
	gui.objecttree.UnselectAll()
	gui.contextMenuSelect=[]
	for obj in objs:
		if obj.__tag__ == "ElementReference":
			newobj = obj.target()
			gui.objecttree.SelectItem(newobj._guiinfo["treeid"])
			gui.objecttree.EnsureVisible(newobj._guiinfo["treeid"])
			gui.contextMenuSelect.append(newobj._guiinfo["treeid"])
		else:
			gui.objecttree.SelectItem(s)
			gui.contextMenuSelect.append(s)
	if len(gui.contextMenuSelect) > 1:
		gui.report("%i objects selected (but only the last one will be highlighted!)" % len(gui.contextMenuSelect))
	try:
		obj = gui.objecttree.GetPyData(gui.contextMenuSelect[-1])
	except:
		return
	gui.editPaneObject = obj
	gui.setEditPane(obj)



def makeCMCall(gui, f, elems):
	def foo(x):
		return f(gui, elems)
	return foo

def isSingle(l):
	if len(l)==1:
		return True
	return False		

def isMult(l):
	if len(l)>1:
		return True
	return False		

def isType(l, s):
	if len(l)==1 and str(l[0])==s:
		return True
	return False			
	
def areTypes(l, s):
	if not l:
		return False
	if set([str(x) for x in l]).issubset(set(s)):
		return True	
	return False		


CORE_MECM["Add Child Object"]=(CreateObject, isSingle)
CORE_MECM["Move/Copy/Link"]=(moveOrCopy, lambda x:True)
CORE_MECM["Refresh Tree"]=(rebuildTree, isSingle)
CORE_MECM["Bind to 'el' in cli"]=(cliobject, isSingle)
CORE_MECM["Help"]=(classHelp, isSingle)
CORE_MECM["Delete"]=(DeleteObject, lambda x:True)
CORE_MECM["Change common attributes"]=(setManyAttributes, isMult)
CORE_MECM["Dereference"]=(followRefs, lambda x:areTypes(x, ['ElementReference']))


def nameHash(objs):
	return dict([(str(o), o) for o in objs])
	# d = {}
	# for o in objs:
	# 	d[str(o)]=o
	# return d

class MienGui(BaseGui):
	'''Base class for Mien guis.'''
	def __init__(self, parent=None):
 		BaseGui.__init__(self, parent, id=-1, title="Mien Toplevel", menus = ["File", "Control", "Extensions"], pycommand=True, height=6, memory=100000)
		
		guicommands=[
					 ["Control", "Reload Extension Modules", self.bounceSpawners],
					 ["Control", "Check Element Refs", lambda x: self.resolveElemRefs()],
					 ["Control", "Search", self.searchEl]]
		self.preferences['Use NMPML']=True
		self.contextMenuSelect = []
		self.contextMenuCommands={}
		self.fillMenus(guicommands)
		self.stdFileMenu()
		self.savefile=""
		self.loaddir=""
		self.expansionMods = []
		self.editPaneObject=None
		self.split = wx.SplitterWindow(self.main, -1)
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.split, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		self.main.SetSizer(sizer)
		self.main.SetAutoLayout(True)
		
		self.objecttree=wx.TreeCtrl(self.split, -1, style = wx.TR_MULTIPLE|wx.TR_HAS_BUTTONS)
		wx.EVT_LEFT_DCLICK(self.objecttree, self.OnLeftDClick)
		#wx.EVT_LEFT_UP(self.objecttree, self.OnLeftUp)
		wx.EVT_TREE_SEL_CHANGED(self.objecttree, self.objecttree.GetId(), self.OnLeftUp)
		wx.EVT_TREE_KEY_DOWN(self.objecttree, self.objecttree.GetId(), self.OnTreeKey)
		wx.EVT_RIGHT_UP(self.objecttree, self.OnRightClick)
		self.editsizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self.editpane=wx.Panel(self.split)
		self.split.SplitVertically(self.objecttree, self.editpane, 375)
		self.split.SetMinimumPaneSize(200)
		self.newDoc()
		self.split.SetSashPosition(300)
		self.bindExpansions()
		self.SetSize((750,560))
		self.object_to_move=None
		self.objecttree.SetDropTarget(self.dropLoader)
		self.load_saved_prefs()

	def OnTreeKey(self, event):
		k = event.GetKeyCode()
		if k==32:
			#space
			self.contextMenuSelect=self.objecttree.GetSelections()
			self.OnRightClick(None)
		elif  k==13:
			#enter
			try:
				obj = self.objecttree.GetPyData(self.objecttree.GetSelections()[0])
				self.editPaneObject = obj
				self.setEditPane(obj)
			except:
				pass
		elif k==316:
			#left
			try:
				obj = self.objecttree.GetSelections()[0]
				self.objecttree.Collapse(obj)
			except:	
				pass
		event.Skip()

	def getEnv(self):
		g = globals()
		l = locals()
		return None, g, l


	def searchEl(self, event):
		s=mien.interface.search.SearchGui(self)	
		
	def bindExpansions(self):
		me={}
		me.update(CORE_ME)
		me.update(mien.blocks.getBlock('ME'))	
		m={}
		for mn in me.keys():
			fc=mien.blocks.makeFCall(me[mn], self)
			m[mn]=fc
		self.refreshMenu("Extensions", m)
		self.contextMenuCommands={}
		self.contextMenuCommands.update(CORE_MECM)
		self.contextMenuCommands.update(assignCMCheck(mien.blocks.getBlock('MECM')))	
			
	def bounceSpawners(self, event=None):
		fl=mien.blocks.clear()
		self.bindExpansions()
		mien.dsp.modules.refresh(False)
		mien.spatial.modules.refresh(False)
		if fl:
			self.report('Reload generated some errors: %s' % (str(fl),))
		else:
			self.report("Reload complete")
						
## File Menu callbacks ----------------------

	def onNewDoc(self):
		self.contextMenuSelect = []
		self.objecttree.DeleteAllItems()
		id=self.objecttree.AddRoot(str(self.document))
		self.document._guiinfo["treeid"]=id
		self.objecttree.SetPyData(id, self.document)
		self.setEditPane()
		for o in self.document.elements:	
			self.add2tree(o)
		for m in self.GetChildren():
			if 'onNewDoc' in dir(m):
				try:
					m.onNewDoc()
				except:
					self.report("Warning: could not refresh module %s" % str(m))	




## ----------------------Object Tree ----------------

	def setEditPane(self, obj=None):
		obj=mien.interface.wxobjectedit.ObjectEditor(self.split, obj, self)
		self.split.ReplaceWindow(self.editpane, obj)
		self.editpane.Destroy()
		self.editpane = obj
		self.split.Layout()
		
	
	def OnLeftDClick(self, event):
		pt = event.GetPosition();
		item, flags = self.objecttree.HitTest(pt)
		try:
			obj = self.objecttree.GetPyData(item)
		except:
			return
		self.editPaneObject = obj
		self.setEditPane(obj)
		
 	def OnLeftUp(self, event):
 	 	self.contextMenuSelect = self.objecttree.GetSelections()
 	 	event.Skip()
			
	def add2tree(self, object, parent=None):
		#object.report = self.report
		if not object.__dict__.has_key('_guiinfo'):
			object._guiinfo={}
		if not parent:
			parent = self.objecttree.GetRootItem()
		else:
			if parent.__dict__.has_key("_guiinfo"):
				parent = parent._guiinfo["treeid"]		
		id = self.objecttree.AppendItem(parent,str(object))
		self.objecttree.SetPyData(id, object)
		object._guiinfo["treeid"]=id
		if parent != self.objecttree.GetRootItem():
			self.objecttree.Collapse(id)
		else:
			self.objecttree.EnsureVisible(id)
		kids = object.elements[:]
		for i in kids:
			self.add2tree(i, object)
		
# 		else:
# 			#hack since treectrl doesn't support more than about 3600 lines
#			#Appears to be fixed in wx 2.6 
# 			for i,k in enumerate(kids):
# 				if not i%2000:
# 					n="elements%i" % int(i/2000)
# 					pid = self.objecttree.AppendItem(id,n)
# 					self.objecttree.SetPyData(pid, object)
# 				self.add2tree(k,pid)	
										
	def update_self(self, **kwargs):
		event=kwargs.get('event', 'modify').lower()
		for obj in self.getObjectsFromKWArgs(kwargs):
			try:
				if obj==self.editpane.object:
					self.editpane.update_self(**kwargs)
			except:
				pass
			if event=="delete":	
				self.objecttree.Delete(obj._guiinfo["treeid"])
			elif event=="modify":	
				self.objecttree.SetItemText(obj._guiinfo["treeid"], str(obj))
			elif event in ["move", "rebuild"]:	
				self.objecttree.Delete(obj._guiinfo["treeid"])
				self.add2tree(obj, obj.container)
			elif event=="create":
				self.add2tree(obj, obj.container)		
		self.Refresh()

	def OnRightClick(self, event):
		if len(self.contextMenuSelect) == 0:
			self.report("No selection")
			return
		elif self.object_to_move:
			par = self.objecttree.GetPyData(self.contextMenuSelect[0])
			objtags=set([o.__tag__ for o in self.object_to_move])
			if len(self.object_to_move)==1:
				disc=self.object_to_move[0].name()
			else:
				disc="%i objects" % (len(self.object_to_move),)
			
			rccontent=[("Abort Move/Copy/Link",lambda x:self.finishMove('abort'))]
			if par._allowedChildren==None or objtags.issubset(par._allowedChildren):
				rccontent.append(("Copy %s here" % disc,lambda x:self.finishMove('copy')))
				rccontent.append(("Move %s here" % disc,lambda x:self.finishMove('move')))
			if par._allowedChildren==None or "ElementReference" in par._allowedChildren:
				rccontent.append(("Link %s here" % disc,lambda x:self.finishMove('link')))
		else:		
			rccontent=[]
			els=[self.objecttree.GetPyData(x) for x in self.contextMenuSelect]
			tags=[e.__tag__ for e in els]
			for fn in self.contextMenuCommands.keys():
				fd=self.contextMenuCommands[fn]
				if fd[1](tags):
					func=makeCMCall(self, fd[0], els)
					rccontent.append((fn, func))
			rccontent.sort(lambda x, y: cmp(x[0], y[0]))
		rcmenu = wx.Menu()
		for i in range(len(rccontent)):
			id = wx.NewId()
			rcmenu.Append(id, rccontent[i][0])
			wx.EVT_MENU(self, id, rccontent[i][1])
		try:
			loc = 	event.GetPosition()
		except:
			loc=(0,0)
		self.PopupMenu(rcmenu, loc)
		rcmenu.Destroy()
		
	def finishMove(self, mode='abort'):
		if mode=='abort':
			self.report('aborted move/copy')
			self.object_to_move=None
			return	
		par = self.objecttree.GetPyData(self.contextMenuSelect[0])
		objlist = self.object_to_move
		self.object_to_move=None
		ulist=[]
		umode=None
		for obj in objlist:
			if mode=='copy':
				foo=obj.clone()
				par.newElement(foo)
				ulist.append(foo)
				umode="Create"
			elif mode=='link':
				foo=self.createElement('ElementReference', {"Target":obj.upath()})
				par.newElement(foo)
				ulist.append(foo)
				umode="Create"
			else:
				if par==obj.container:
					return
				ulist.append(obj)
				umode="Move"
				obj.move(par)
		self.update_all(objects=ulist, event=umode)
				
	def	makeElem(self, what, attr, parent, update=True):
		new=self.createElement(what, attr)
		parent.newElement(new)
		if update:
			self.update_all(object=new, event="Create")
		return new	

	def getElemAttribs(self, ct, current={}):
		choices=[]
		elcl = elements[ct]
		choices.append({"Name":"Name",
						"Value":ct})
		for a in elcl._guiConstructorInfo.keys():
			dic = {}
			dic.update(elcl._guiConstructorInfo[a])
			choices.append(dic)
		for a in elcl._requiredAttributes:
			if a in elcl._guiConstructorInfo.keys():
				continue
			elif a=="Name":
				continue
			else:	
				choices.append({"Name":a,
								"Value":current.get(a, '')})
		for a in elcl._specialAttributes:
			if a in elcl._guiConstructorInfo.keys():
				continue
			elif a=="Name":
				continue
			else:	
				choices.append({"Name":a,
								"Value":current.get(a, ''),
								"Optional":1})
		browsers=mien.interface.widgets.ATTRIBUTE_BROWSERS.get(ct)
		if browsers:
			for k in choices:
				if browsers.has_key(k['Name']):
					k["Browser"]=browsers[k["Name"]]
		atr = {}
		d = self.askParam(choices)
		if not d:
			return None
		for i in range(len(d)):
			if d[i]:
				par = choices[i]["Name"]
				val = d[i]
				atr[par]=val
		return atr			
			
