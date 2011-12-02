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
import wx,  mien.nmpml, sys
from mien.interface.widgets import browseTree

class SearchGui(wx.Dialog):
	def __init__(self, xm, id=-1, **opts):
		self.xm=xm
		self.conditions=[]
		self.found=[]
		wxopts = {'title':"Mien Search"} 
		if "linux" in sys.platform:
			wxopts["style"]=wx.RESIZE_BORDER
		wxopts.update(opts)
		wx.Dialog.__init__(self, xm, id, **wxopts)
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		
		box = wx.BoxSizer(wx.HORIZONTAL)
		self.newTagB = wx.Button(self, -1, " Tag ")
		wx.EVT_BUTTON(self, self.newTagB.GetId(), self.addTagCond)
		box.Add(self.newTagB, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.newAtrB = wx.Button(self, -1, " Attribute ")
		wx.EVT_BUTTON(self, self.newAtrB.GetId(), self.addAtrCond)
		box.Add(self.newAtrB, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.newPathB = wx.Button(self, -1, " Path ")
		wx.EVT_BUTTON(self, self.newPathB.GetId(), self.addPathCond)
		box.Add(self.newPathB, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.applyB = wx.Button(self, -1, " Search Results ")
		wx.EVT_BUTTON(self, self.applyB.GetId(), self.applySearch)
		box.Add(self.applyB, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.dismissB = wx.Button(self, -1, " Dismiss ")
		wx.EVT_BUTTON(self, self.dismissB.GetId(), lambda x:self.Destroy())
		box.Add(self.dismissB, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

		self.searchMenu=wx.Menu()
		id=wx.NewId()
		self.searchMenu.Append(id, " Do Search ")
		wx.EVT_MENU(self, id, self.runSearch)
		id=wx.NewId()
		self.searchMenu.Append(id, " Select Hits ")
		wx.EVT_MENU(self, id, self.selectRes)
		id=wx.NewId()
		self.searchMenu.Append(id, " Make References ")
		wx.EVT_MENU(self, id, self.refRes)

		self.info=wx.StaticText(self, -1, "         0 Objects Found      ")
		self.sizer.Add(self.info, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.SetSizer(self.sizer)
		self.SetAutoLayout(True)
		self.sizer.Fit(self)
		self.Show(True)

	def applySearch(self, event):
		self.PopupMenu(self.searchMenu, self.applyB.GetPosition())
		
	def getSearchConditions(self):
		search=[]
		for c in self.conditions:
			dowhat=c[1].GetStringSelection()
			if dowhat=="Ignore":
				continue
			sc=[dowhat, c[0]]	
			if c[0]=="paths":
				path=c[2].GetValue().strip()
				sc.append(path)
			elif c[0]=="tags":
				tag=c[2].GetStringSelection()
				sc.append(tag)
			else:
				at=c[2].GetValue().strip()
				mat=c[3].GetStringSelection()
				pat=c[4].GetValue().strip()
				sc.extend([at, mat, pat])
			search.append(sc)
		return search
		
	def runSearch(self, event):
		s=self.getSearchConditions()
		if not s:
			self.xm.report("No Search Conditions")
			self.found=[]
		else:	
			self.found=self.xm.document.compoundSearch(s)	
		self.info.SetLabel("    %i Objecs found    " % len(self.found))

	def selectRes(self, event):
		if not self.found:
			self.xm.report("No search results")
			return
		self.xm.contextMenuSelect=[]
		try:
			self.xm.objecttree.UnselectAll()
		except:
			pass
		for obj in self.found:
			self.xm.objecttree.SelectItem(obj._guiinfo["treeid"])
			self.xm.objecttree.EnsureVisible(obj._guiinfo["treeid"])
			self.xm.contextMenuSelect.append(obj._guiinfo["treeid"])
		self.xm.report("Selected %i objects. They may not all appear highlighted depending on the Wx library version" % len(self.found) )	



	def refRes(self, event):	
		if not self.found:
			self.xm.report("No search results")
			return
		d=self.xm.askParam([{"Name":"Where?",
								"Type":str,
								"Browser": browseTree}])
		if not d:
			return
		par=self.xm.document.getInstance(d[0])
		i=0
		for el in self.found:
			self.xm.makeElem('ElementReference', {"Name":"el%i" % i, "Target":el.upath(), "Index":i, "Data":0}, par)
			i+=1
		self.xm.report("Placed search result links in element %s" % str(par))	

		


	def addAtrCond(self,event):
		cond=["attributes"]
		box = wx.BoxSizer(wx.HORIZONTAL)
		dowhat=	wx.Choice(self,-1, choices=["Or", "And", "Or Not", "And Not", "Ignore"])
		cond.append(dowhat)
		box.Add(dowhat,  0, wx.ALIGN_CENTRE|wx.ALL, 5)	
		box.Add(wx.StaticText(self, -1, "Attribute"), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		ts = self.GetTextExtent("W")[0]*16
		th= self.GetTextExtent("W")[1]*2
		atname = wx.TextCtrl(self, -1, "", size=(ts,th))
		box.Add(atname,1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		cond.append(atname)
		searchtype=	wx.Choice(self,-1, choices=["Equals", "Is Defined", "Is True", 
												"Matches Regex", "Is Numerically Greater",
												"Is Numerically Less", "Contains Substring"])
		cond.append(searchtype)	
		box.Add(searchtype,  0, wx.ALIGN_CENTRE|wx.ALL, 5)
		atvalue = wx.TextCtrl(self, -1, "", size=(ts, th))
		cond.append(atvalue)
		box.Add(atvalue,  1, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		self.conditions.append(cond)
		self.sizer.Add(box, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.sizer.Fit(self)

	def addPathCond(self, event):
		cond=["paths"]
		box = wx.BoxSizer(wx.HORIZONTAL)
		dowhat=	wx.Choice(self,-1, choices=["Or", "And", "Or Not", "And Not", "Ignore"])
		cond.append(dowhat)
		box.Add(dowhat,  0, wx.ALIGN_CENTRE|wx.ALL, 5)	
		box.Add(wx.StaticText(self, -1, "Is in XmodPath"), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		ts = self.GetTextExtent("W")[0]*32
		th= self.GetTextExtent("W")[1]*2
		path = wx.TextCtrl(self, -1, "", size=(ts,th))
		box.Add(path,1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		cond.append(path)
		
		browse=wx.Button(self, -1, " Browse ")
		wx.EVT_BUTTON(self, browse.GetId(), lambda x:browseTree(self.xm, {}, path))
		box.Add(browse,  0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.conditions.append(cond)
		self.sizer.Add(box, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.sizer.Fit(self)


	
	def addTagCond(self, event):
		cond=["tags"]
		box = wx.BoxSizer(wx.HORIZONTAL)
		dowhat=	wx.Choice(self,-1, choices=["Or", "And", "Or Not", "And Not", "Ignore"])
		cond.append(dowhat)
		box.Add(dowhat,  0, wx.ALIGN_CENTRE|wx.ALL, 5)	
		box.Add(wx.StaticText(self, -1, "Tag"), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		tags=mien.parsers.nmpml.elements.keys()	
		withwhat=wx.Choice(self,-1, choices=tags)
		cond.append(withwhat)
		box.Add(withwhat,  0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.conditions.append(cond)
		self.sizer.Add(box, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.sizer.Fit(self)

def makeMod(gui):
	return None

