
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
from mien.math.array import ArrayType, array
from types import *

class ReprValidator(wx.PyValidator):
	def __init__(self, master):
		wx.PyValidator.__init__(self)
		self.master=master
		if type(self.master.data)==ArrayType or self.master.data:
			self.type = type(self.master.data)
		else:
			self.type = None

	def Clone(self):
		return ReprValidator(self.master)

	def Validate(self, win):
		Ctrl = self.GetWindow()
		val = Ctrl.GetValue()
		if not self.type:
			return True
		try:
			val = eval(val)
			return True
		except:
			Ctrl.SetValue("--ERROR--")
			return False

	def TransferToWindow(self):
		Ctrl = self.GetWindow()
		val = self.master.data
		try:
			if type(val)!=type(" "):
				Ctrl.SetValue(repr(val))
			else:
				Ctrl.SetValue(val)
			return True
		except:
			return False

	def TransferFromWindow(self):
		Ctrl = self.GetWindow()
		val = Ctrl.GetValue()
		if self.type in [type(1), type(1.0), type(" ")]:	
			self.master.data=self.type(val)
		else:
			self.master.data=eval(val)
		return True

class SimpleEditor(wx.Dialog):
	def __init__(self, data, parent, id=-1, **opts):
		if not opts.has_key("title"):
			opts["title"]="Data Editor"
		if not opts.has_key("style"):
			opts["style"]=wx.DEFAULT_DIALOG_STYLE
		wx.Dialog.__init__(self, parent, id, **opts)
		self.data = data
		sizer = wx.BoxSizer(wx.VERTICAL)
		w = self.GetCharWidth()*min(len(repr(self.data))+5, 80)
		h = 1+divmod(len(repr(self.data)), 60)[0]
		h = max(h, repr(data).count("\n"))
		h = min(h, 30)
		h = self.GetCharHeight()*h
		h=max(h, 60)
		self.edit = wx.TextCtrl(self, -1, style=wx.TE_WORDWRAP|wx.TE_MULTILINE,
								size=(w,h), validator = ReprValidator(self) )
		sizer.Add(self.edit, 1,wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
		box = wx.BoxSizer(wx.HORIZONTAL)
		btn = wx.Button(self, wx.ID_OK, " OK ")
		btn.SetDefault()
		box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		btn = wx.Button(self, wx.ID_CANCEL, " Cancel ")
		box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		sizer.Fit(self)
	



EDITABLETYPES = [ArrayType, IntType, LongType, FloatType, ComplexType, StringType,
				 UnicodeType, TupleType, ListType, DictType]

def dataEdit(parent, data):
	c=SimpleEditor(data, parent)
	c.CenterOnParent()
	val = c.ShowModal()
	if val == wx.ID_OK:
		return c.data
	else:
		return None

def dataDisplay(parent, data):
	c=SimpleEditor(data, parent)
	c.CenterOnParent()
	c.Show()
