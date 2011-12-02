
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

from mien.math.array  import zeros, vstack, ravel, reshape, array, round
ArrayType=type(zeros(1))


def FileBrowse(master, dict, control):
	dlg=wx.FileDialog(master, message="Select file name", style=wx.OPEN)
	dlg.CenterOnParent()
	if dlg.ShowModal() == wx.ID_OK:
		control.SetValue(dlg.GetPath())	
	dlg.Destroy()
	
	
def DirBrowse(master, dict, control):
	dlg=wx.DirDialog(master, message="Select Directory Name", style=wx.DD_NEW_DIR_BUTTON)
	dlg.CenterOnParent()
	if dlg.ShowModal() == wx.ID_OK:
		control.SetValue(dlg.GetPath())	
	dlg.Destroy()


def float2str(f, prec=None):
	if prec==None:
		return str(f)
	if prec==0:
		return str(int(f))
	else:
		s="%"+"."+str(prec)+"f"
		return s % f
		

def arraytostring(a, prec=None):
	if len(a.shape)==1:
		return ','.join(map(lambda x:float2str(x, prec), a))
	if len(a.shape)==2:
		return ';'.join([','.join(map(str, r)) for r in a])
	else:
		return repr(a.shape)+':'+arraytostring(ravel(a))

def arrayfromstring(s, prec=None):
	if '(' in s:
		shape, values=s.split(':')
		return reshape(arrayfromstring(values), eval(shape))
	elif ";" in s:
		return vstack([arrayfromstring(l) for l in s.split(';')])
	elif prec or ("." in s):
		return array(map(float, s.split(',')))
	else:
		return array(map(int, s.split(',')))
		
class OptionValidator(wx.PyValidator):
	def __init__(self, dict):
		wx.PyValidator.__init__(self)
		self.dict=dict
		self.stringtypes = [type(u" "), type(" ")]
		self.type = 'flex' #dict["Type"]

	def Clone(self):
		return OptionValidator(self.dict)

	def Validate(self, win):
		try:
			v=self.castValue()
			return True
		except:
			Ctrl = self.GetWindow()	
			Ctrl.SetValue("--ERROR--")
			return False

	def TransferToWindow(self):
		Ctrl = self.GetWindow()
		try:
			if self.dict.get("Value")!=None:
				if type(self.dict["Value"]) in self.stringtypes:
					Ctrl.SetValue(self.dict["Value"])
				elif type(self.dict["Value"])==ArrayType:
					self.type=ArrayType
					s=arraytostring(self.dict["Value"], self.dict.get("Precision"))
					Ctrl.SetValue(s)
				elif type(self.dict["Value"])==float:
					Ctrl.SetValue(float2str(self.dict["Value"], self.dict.get("Precision")))
					if self.dict.get("Precision")==0:
						self.type=int
				elif type(self.dict["Value"])==int and self.dict.get("Precision"):
					Ctrl.SetValue(float2str(self.dict["Value"], self.dict.get("Precision")))
					self.type=float						
				else:
					Ctrl.SetValue(repr(self.dict["Value"]))
			return True
		except:
			return False

	
	def castValue(self):
		Ctrl = self.GetWindow()
		val = Ctrl.GetValue()
		if self.dict.get("Optional") and val=="":
			return None
		elif self.type in self.stringtypes:	
			return val
		elif self.type==ArrayType:
			return arrayfromstring(val,self.dict.get("Precision"))
		elif self.type in [list, tuple, 'flex']:
			try:
				return eval(val)
			except:
				return val
		else:
			try:
				return self.type(eval(val))
			except:
				return self.type(eval('"%s"' % val))
		

	def TransferFromWindow(self):
		self.dict["Value"]=self.castValue()
		return True



class EntryValidator(wx.PyValidator):
	def __init__(self, p):
		wx.PyValidator.__init__(self)
		self.list = p
		self.stringtypes = [type(u" "), type(" ")]
		if type(self.list[1])==type(type(" ")):
			self.type = self.list[1]
			self.list[1]=""
		else:
			self.type = type(self.list[1])

	def Clone(self):
		return EntryValidator(self.list)

	def Validate(self, win):
		Ctrl = self.GetWindow()
		val = Ctrl.GetValue()
		if self.type in self.stringtypes:
			return True
		try:
			val = eval(val)
			v = self.type(val)
		except:
			Ctrl.SetValue("--ERROR--")
			return False

	def TransferToWindow(self):
		Ctrl = self.GetWindow()
		try:
			if self.type in self.stringtypes:
				Ctrl.SetValue(self.list[1])
			else:
				Ctrl.SetValue(repr(self.list[1]))
			return True
		except:
			return False

	def TransferFromWindow(self):
		Ctrl = self.GetWindow()
		val = Ctrl.GetValue()
		if self.type in self.stringtypes:	
			self.list[1]=val
		else:
			self.list[1]=eval(val)
		return True


def ColorBrowser(master, dict, control):
	dlg=wx.ColourDialog(master)
	#dlg.GetColourData().SetChooseFull(True)
	if dlg.ShowModal() == wx.ID_OK:
		data = dlg.GetColourData()
		tup = data.GetColour().Get()
		dict["Value"]=tup
		control.SetValue(str(tup))	
	dlg.Destroy()
		


def manyEntries(l, parent):
	vsize = wx.BoxSizer(wx.VERTICAL)
	for p in l:
		hsize = wx.BoxSizer(wx.HORIZONTAL)
		hsize.Add(wx.StaticText(parent, -1, p[0]), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		ts = max(len(repr(p[1]))+3, 10)
		ts = parent.GetTextExtent("W")[0]*ts
		txt = wx.TextCtrl(parent, -1, "", size=(ts,-1), validator = EntryValidator(p))
		hsize.Add(txt,1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		vsize.Add(hsize, 1, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
	return vsize
			

def makeEntryWidget(parent, dict):
	if not dict.has_key("Type"):
		dict["Type"]=type(dict["Value"])
		if dict["Type"]==type(u" "):
			dict["Type"]=str
			dict["Value"]=str(dict["Value"])
	sizer = wx.BoxSizer(wx.HORIZONTAL)
	sizer.Add(wx.StaticText(parent, -1, dict["Name"]), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
	size = max(len(repr(dict.get("Value")))+3, 10)
	size = parent.GetTextExtent("W")[0]*size
	val=OptionValidator(dict)
	txt = wx.TextCtrl(parent, -1, "", size=(size,-1), validator = val)
	sizer.Add(txt,1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
	if dict.get("Browser"):
		id = wx.NewId()
		but = wx.Button(parent, id, "Browse")
		def MakeBrowse(event):
			dict["Browser"](parent, dict, txt)
		wx.EVT_BUTTON(parent, id, MakeBrowse)
		sizer.Add(but,0, wx.ALIGN_CENTRE|wx.ALL, 5)
	return sizer


class OptionDialog(wx.Dialog):
	
	def __init__(self, l, parent, id=-1, **opts):
		self.entrytypes = {'List':self.makeListEntry,
			  			'Prompt':self.makePromptEntry,
			  			'Select':self.makeSelectEntry,				  
			  			'Choice':self.makeChoiceEntry,				  
			  			}	

		self.parent = parent
		wxopts = {'title':"User Input"}
		wxopts.update(opts)
		if 	len(l)>8:
			style = wxopts.get('style', 0)
			wxopts['style']=style|wx.VSCROLL
		wx.Dialog.__init__(self, parent, id, **wxopts)
		self.optionList=l
		sizer = wx.BoxSizer(wx.VERTICAL)
		if type(self.optionList[0])==type(" "):
			sizer.Add(wx.StaticText(self, -1, self.optionList[0]), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
			self.optionList = self.optionList[1:]
		for k in self.optionList:
			s=self.makeEntry(k, sizer)
			
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
		wx.EVT_BUTTON(self, wx.ID_OK, self.OnOK)

	
	def makeEntry(self, dict, parsizer):
		if not dict.get("Type") in self.entrytypes:
			if dict.get("Default"):
				if not dict.get("Value"):
					dict["Value"]=dict["Default"]
		if not dict.has_key("Type"):
			dict["Type"]=type(dict["Value"])
		if dict["Type"]==type(u" "):
			dict["Type"]=str
			dict["Value"]=str(dict["Value"])
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(wx.StaticText(self, -1, dict["Name"]), 0, wx.ALIGN_TOP|wx.ALL, 5)
		if dict["Type"] == "Label":
			pass
		elif dict['Type'] in self.entrytypes:
			self.entrytypes[dict['Type']](dict, sizer)
		else:
			size = max(len(repr(dict.get("Value")))+3, 10)
			size=min(size, 80)
			size = self.GetTextExtent("W")[0]*size
			txt = wx.TextCtrl(self, -1, "", size=(size,-1), validator = OptionValidator(dict))
			sizer.Add(txt,1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
			if dict.get("Browser"):
				id = wx.NewId()
				but = wx.Button(self, id, "Browse")
				def MakeBrowse(event):
					dict["Browser"](self.parent, dict, txt)
				wx.EVT_BUTTON(self, id, MakeBrowse)
				sizer.Add(but,0, wx.ALIGN_CENTRE|wx.ALL, 5)
		sv = 0
		if dict['Type'] == 'Select':
			sv = 10
		parsizer.Add(sizer, sv, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
			

	def makeListEntry(self, dict, sizer):
		id = wx.NewId()
		l = dict["Value"][:]
		if not l:
			dict["Value"].append("No choices")
			l.append("No choices")
		ch = wx.Choice(self,id, choices=map(str, dict["Value"]))
		def HandleList(event):
			dict["Value"]=l[event.GetInt()]
		wx.EVT_CHOICE(self, id, HandleList)
		defsel = dict.get("Default")
		if defsel:
			try:
				ind = l.index(defsel)
				ch.SetSelection(ind)
			except IndexError:
				if type(defsel)==int:
					ind =defsel
					ch.SetSelection(defsel)
				else:
					print("WARNING:proposed default value isn't in list of choices")
			dict["Value"]=l[ind]
		else:
			dict["Value"]=dict["Value"][0]
		sizer.Add(ch,1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		
	def makePromptEntry(self, dict, sizer):
		id = wx.NewId()
		if not dict["Value"]:
			dict["Value"].append("No choices")
		astype=type(dict["Value"][0])
		for dv in dict["Value"][1:]:
			if type(dv)!=astype:
				astype=str
				break
		ch= wx.ComboBox(self,id, choices=map(str, dict["Value"]))
		def HandleSelect(event):
			dict["Value"]=astype(ch.GetStringSelection())
		def HandleText(event):
			dict["Value"]=astype(ch.GetValue())
		wx.EVT_COMBOBOX(self, id, HandleSelect)
		wx.EVT_TEXT(self, id, HandleText)
		defsel = dict.get("Default")
		if defsel:
			defsel = ch.FindString(str(defsel))
			ch.SetSelection(defsel)
		else:
			ch.SetSelection(0)
		ch.SetValue(ch.GetStringSelection())	
		dict["Value"]=astype(ch.GetStringSelection())
		sizer.Add(ch,1, wx.ALIGN_CENTRE|wx.ALL, 5)
		if dict.get("Browser"):
			id = wx.NewId()
			but = wx.Button(self, id, "Browse")
			def MakeBrowse(event):
				dict["Browser"](self.self, dict, ch)
			wx.EVT_BUTTON(self, id, MakeBrowse)
			sizer.Add(but,0, wx.ALIGN_CENTRE|wx.ALL, 5)
	
	def makeSelectEntry(self, dict, sizer):
		id = wx.NewId()
		l = dict["Value"][:]
		dict["Value"]= []
		maxl = max(map(lambda x: len(repr(x)),l ))
		hsize = self.GetTextExtent("W")[1]*(len(l)+2)
		hsize=min(hsize, 400)
		sel = wx.ListBox(self,id, choices=map(str, l), style=wx.LB_EXTENDED|wx.LB_NEEDED_SB,  size=(-1, hsize))
		#sel.SetMaxSize((600, 400))
		def HandleSel(event):
			dict["Value"]= []
			selections = 	sel.GetSelections()
			for i in selections:
				dict["Value"].append(l[i])
		wx.EVT_LISTBOX(self, id, HandleSel)
		sizer.Add(sel,6, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		
	def OnChoice(self, event, d, vd, sizer):
		if type(event) in [str, unicode]:
			ind =d['_keys'].index(event)
			d['_list'].SetSelection(ind)
		else:	
			event =d['_keys'][event.GetInt()]
		
		active = set(d[event])
		for i in range( 1, len(sizer.GetChildren())):
			if i in active:
				sizer.Show(i, True)
			else:
				sizer.Hide(i, True)
		vd['_chosen'] = event		
		sizer.Layout()
		self.Fit()
		self.Refresh()
			
	def makeChoiceEntry(self, dict, sizer):
		id = wx.NewId()
		choice = {'_keys':dict['Value'].keys()}
		subsizer = wx.BoxSizer(wx.VERTICAL)
		ch = wx.Choice(self ,id, choices=choice['_keys'])
		choice['_list'] = ch
		subsizer.Add(ch, 0, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		sizer.Add(subsizer, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		if 'Default' in dict:
			dv = dict['Default']
			if type(dv) in [tuple, list]:
				if dv[0] in choice['_keys']:
					dict['Default'] = dv[0]
					dv = dv[1:]
				else:
					for k in dict['Value']:
						if len(dict['Value'][k]) == len(dv):
							dict['Default'] = k
				for i,v in enumerate(dv):
					ld = dict['Value'][dict['Default']][i]
					if ld.get('Type') in self.entrytypes:
						ld['Default'] = v
					else:
						ld['Value'] = v 
		else:
			dict['Default'] = choice['_keys'][0]
		for k in dict['Value'].keys():
			startat = len(subsizer.GetChildren())
			for d in dict['Value'][k]:
				self.makeEntry(d, subsizer)		
			inds = range(startat,len(subsizer.GetChildren()))
			choice[k] = inds
		wx.EVT_CHOICE(self, id, lambda x:self.OnChoice(x, choice,dict, subsizer))
		self.OnChoice(dict['Default'], choice, dict, subsizer)
		

 	def OnOK(self, event=None):
		if self.Validate() and self.TransferDataFromWindow():
			if self.IsModal():
				self.EndModal(wx.ID_OK)
			else:
				self.SetReturnCode(wx.ID_OK)
				self.Show(False)
		


def extractSetValues(l):
	ret=[]
	for i in l:
		if type(i)==type(" "):
			continue
		if i.get("Type")=="Label":
			continue
		if i.has_key("_chosen"):
			l2= [i['_chosen']] + extractSetValues(i['Value'][i['_chosen']])
			ret.append(l2)
		else:	
			ret.append(i["Value"])
	return ret

def askParameters(parent, l):
	c=OptionDialog(l, parent)
	c.CenterOnParent()
	val = c.ShowModal()
	if val == wx.ID_OK:
		ret=extractSetValues(l)
		del(c)
		return ret 
	else:
		del(c)
		return []
