
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
from mien.wx.base import wx, AWList, elements
from mien.wx.dataeditors import dataEdit, EDITABLETYPES
import mien.nmpml
from mien.interface.widgets import ATTRIBUTE_BROWSERS

class ObjectEditor(wx.Panel):
	def __init__(self, master, obj, base):
		wx.Panel.__init__(self, master, -1)
		self.Show(True)
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.object = obj
		self.base=base
		if not self.object:
			self.namelabel = wx.StaticText(self, -1, 'no object selected')
			self.sizer.Add(self.namelabel, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
			self.SetSizer(self.sizer)
			self.SetAutoLayout(True)
			self.sizer.Fit(self)
			return
		lab = obj.name()+" ("+obj.__tag__+")"
		self.namelabel = wx.StaticText(self, -1, lab)
		self.sizer.Add(self.namelabel, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		hs = wx.BoxSizer(wx.HORIZONTAL)
 		b = wx.Button(self, -1, "Add Attrib")
 		wx.EVT_BUTTON(self, b.GetId(), self.addAttrib)
 		hs.Add(b, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
 		b = wx.Button(self, -1, "Rename")
 		wx.EVT_BUTTON(self, b.GetId(), self.rename)
		hs.Add(b, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
 		b = wx.Button(self, -1, "Attrib Editor")
 		wx.EVT_BUTTON(self, b.GetId(), self.getattribs)
		hs.Add(b, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.sizer.Add(hs, 0, wx.ALIGN_CENTRE|wx.ALL, 5)			
		self.attriblist = AWList(self, -1, style=wx.LC_REPORT
								 | wx.SUNKEN_BORDER
								 | wx.LC_SINGLE_SEL)
		self.attriblist.InsertColumn(0, "Attribute")
		self.attriblist.InsertColumn(1, "Value")
		i=0
		for k in self.object.attributes.keys():
			if k=='Name':
				continue
			self.attriblist.InsertStringItem(i, k)
			self.attriblist.SetStringItem(i, 1,str(self.object.attrib(k)))
			i+=1
		self.sizer.Add(self.attriblist, 10,
					   wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		
		hs = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(self, -1, 'cdata')
 		hs.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
 		b = wx.Button(self, -1, "Set cData")
 		wx.EVT_BUTTON(self, b.GetId(), self.setCdata)
 		hs.Add(b, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.sizer.Add(hs, 0, wx.ALIGN_CENTRE|wx.ALL, 5)	
 		self.cdata=wx.TextCtrl(self, -1, style=wx.TE_WORDWRAP|wx.TE_MULTILINE)
 		self.cdata.SetValue(obj.getCdata())
		self.sizer.Add(self.cdata,3, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		
		if self.object.__tag__ in ['Fiducial', 'Section']:
			hs = wx.BoxSizer(wx.HORIZONTAL)
			p=self.object.getPoints()
			s='%i %iD Points (%i labeled)' % (p.shape[0],p.shape[1], len(self.object.point_labels.keys())) 
			self.pointlabel = wx.StaticText(self, -1, s)
 			hs.Add(self.pointlabel, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
 			b = wx.Button(self, -1, "edit points")
 			wx.EVT_BUTTON(self, b.GetId(), self.editPoints)
 			hs.Add(b, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
 			b = wx.Button(self, -1, "edit labels")
 			wx.EVT_BUTTON(self, b.GetId(), self.editPointLab)
 			hs.Add(b, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
			self.sizer.Add(hs, 0, wx.ALIGN_CENTRE|wx.ALL, 5)	
		elif self.object.__tag__ in ['Data']:	
			hs = wx.BoxSizer(wx.HORIZONTAL)
			d=self.object.data
			if d==None or len(d.shape)==0 or d.shape[0]==0:
				label = wx.StaticText(self, -1, 'No Data')
 				hs.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
 			else:
				self.datalabel = wx.StaticText(self, -1, '%s Data Array' % str(d.shape))
 				hs.Add(self.datalabel, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
 				b = wx.Button(self, -1, "edit data")
 				wx.EVT_BUTTON(self, b.GetId(), self.editData)
 				hs.Add(b, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
			self.sizer.Add(hs, 0, wx.ALIGN_CENTRE|wx.ALL, 5)	
		wx.EVT_LEFT_DCLICK(self.attriblist, self.OnAttribDClick)
		wx.EVT_ENTER_WINDOW(self.attriblist, lambda x: self.attriblist.SetFocus())
  		wx.EVT_LIST_ITEM_SELECTED(self.attriblist, self.attriblist.GetId(), self.OnSelect)
		self.SetSizer(self.sizer)
		self.SetAutoLayout(True)
		self.sizer.Fit(self)

		self.selectedItem=None
		
		self.keyBindings={'e':self.editAttrib,
						  'enter':self.editAttrib,
						  'd':self.killAttrib,
						  'n':self.addAttrib,
						  'up':self.attriblist.selectLast,
						  'down':self.attriblist.selectNext
						  }
		wx.EVT_CHAR(self.attriblist, self.OnChar)
		self.attriblist.SetFocus()
		
	def getStupidListSelection(self):
		try:
			id=self.attriblist.selected()[0]
		except IndexError:
			id=0
		return id	

	def rename(self, event=None):
		l = self.base.askParam([{"Name":"New Name",
								 "Value":self.object.name()}])
		if not l:
			return
		name=self.object.setName(l[0])
		self.object.update_refs()
		print name, type(name), self.object.__tag__, type(self.object.__tag__ )
		lab = name + " (" + self.object.__tag__ + ")"
		self.base.update_all(object=self.object)
		self.namelabel.SetLabel(lab)

	def setCdata(self, event=None):
		self.object.setCdata(self.cdata.GetValue())
		self.base.report('set data')
		self.base.update_all(object=self.object)

	def OnSelect(self, event):
		self.selectedItem=event.GetIndex()
	
	def OnChar(self, event):
		self.selectedItem=self.getStupidListSelection()
		k = self.base.getKeyFromCode(event.GetKeyCode())
		if self.keyBindings.has_key(k):
			self.keyBindings[k]()
		else:
			#print k
			event.Skip()

	def update_self(self, **kwargs):
		event=kwargs.get('event', "modify").lower()
		for obj in self.getObjectsFromKWArgs(kwargs):
			if self.object==obj:
				if event=="Delete":
					if obj.container:
						self.gui.setEditPane(mien.nmpml.interface.wxobjectedit.ObjectEditor(self.split, obj.container, self))
					else:
						self.gui.setEditPane()
				else:
					self.gui.setEditPane(mien.nmpml.interface.wxobjectedit.ObjectEditor(self.split, obj, self))
		
	def addAttrib(self, event=None):
		l = self.base.askParam([{"Name":"Attribute",
								 "Value":""},
								{"Name":"Value",
								 "Value":""}])
		if not l:
			return
		nk = l[0]
		nv = l[1]
		i = self.attriblist.GetItemCount()
		self.attriblist.InsertStringItem(i, nk)
		self.attriblist.SetStringItem(i, 1, str(nv))
		self.object.setAttrib(nk,nv)
		self.base.update_all(object=self.object)
		
	
	def killAttrib(self, event=None):
		if event:
			l = self.base.askParam([{"Name":"Attribute",
									 "Type":"List",
									 "Value":self.object.attributes.keys()}])
			if not l:
				return
			name = l[0]
		else:
			item=self.selectedItem
			name = self.attriblist.GetItem(item, 0).GetText()
			l=self.base.askUsr("Delete attribute %s?" % name, ["Yes", "No"])
			if not l=="Yes":
				return
		del(self.object.attributes[name])
		i = self.attriblist.FindItem(-1, name)
		self.attriblist.DeleteItem(i)
		self.base.update_all(object=self.object)	
		
		
	def OnAttribDClick(self, event):
		pt = event.GetPosition();
		item, flags = self.attriblist.HitTest(pt)
		self.selectedItem=item
		try:
			name = self.attriblist.GetItemText(item)
		except:
			return
		self.editAttrib()

	def editAttrib(self):
		item=self.selectedItem
		name = self.attriblist.GetItem(item, 0).GetText()
		val = self.attriblist.GetItem(item, 1).GetText()
		ct = self.object.__tag__
		if elements[ct]._guiConstructorInfo.has_key(name):
			choice = {}
			choice.update(elements[ct]._guiConstructorInfo[name])
			if choice.get("Type") in ["List", "Select", "Choice", "Prompt"]:
				choice["Default"] = self.object.attrib(name)
			else:
				choice["Value"] = self.object.attrib(name)
		else:	
			choice ={"Name":name,
					 "Value":self.object.attrib(name),
					 "Optional":1}
		browsers=ATTRIBUTE_BROWSERS.get(ct)
		if browsers:
			if browsers.has_key(choice['Name']):
					choice["Browser"]=browsers[choice["Name"]]
		l = self.base.askParam([choice])
		if not l:
			return
		nv = l[0]
		self.attriblist.SetStringItem(item, 1, repr(nv))
		self.object.setAttrib(name,nv)	
		self.base.update_all(object=self.object)	
	
	def getattribs(self, event):
		attr=self.base.getElemAttribs(self.object.__tag__, self.object.attributes)
		if not attr:
			return
		for k in self.object.attributes.keys():
			if not k in attr.keys():
				del(self.object.attributes[k])
		self.attriblist.DeleteAllItems()
		i=0
		for k in attr.keys():
			self.object.setAttrib(k,attr[k])
			if k=='Name':
				continue
			self.attriblist.InsertStringItem(i, k)
			self.attriblist.SetStringItem(i, 1,str(attr[k]))
			i+=1
		self.base.update_all(object=self.object)	


	
	def editPoints(self, event):
		d = dataEdit(self, self.object.getPoints())
		if d!=None:
			self.object.setPoints(d)
			s='%i %iD Points (%i labeled)' % (d.shape[0],d.shape[1], len(self.object.point_labels.keys())) 
			self.pointlabel.SetLabel(s)
			self.base.update_all(object=self.object)
	
	def editPointLab(self, event):
		d = dataEdit(self, self.object.point_labels)
		if d!=None:
			self.object.point_labels=d
			s='%i %iD Points (%i labeled)' % (d.shape[0],d.shape[1], len(self.object.point_labels.keys())) 
			self.pointlabel.SetLabel(s)
			self.base.update_all(object=self.object)
	
	def editData(self, event):
		d = dataEdit(self, self.object.data)
		if d!=None:
			self.object.data=d
			self.datalabel.SetLabel('%ix%i Data Array' % d.shape)
			self.base.update_all(object=self.object)

class ObjEdMod:
	def __init__(self, xmg):
		self.gui = xmg
		self.contextClassFeatures = {"Section":[("Export Point",self.sendPoint)]
									 }



	
	def sendPoint(self, event):
		obj = self.gui.objecttree.GetPyData(self.gui.contextMenuSelect[0])
		pts = obj.getPoints()
		pcs = self.gui.document.getElements(["Recording", "IClamp"])
		pcd = {}
		for e in pcs:
			pcd[str(e)]=e
		d = self.gui.askParam([{"Name":"Which",
								"Type":"Select",
								"Value":pts},
								{"Name":"Where",
								 "Type":"List",
								 "Value":pcd.keys()}])
		if not d:
			return
		targ = pcd[d[1]]
		for pt in d[0]:
			rel=obj.relativeLocation(pt)
			nelems=len(targ.getTypeRef("Section"))
			self.gui.makeElem("ElementReference", {"Name":"IClampLocation",
								"Target":obj.upath(),
								"Data":str(rel),
								"Index":str(nelems)},
								targ)

			
def makeMod(xmg):
	m = ObjEdMod(xmg)
	return m
