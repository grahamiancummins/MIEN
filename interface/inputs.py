
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
from mien.wx.dialogs import FileBrowse
from mien.math.array import *
from mien.wx.base import *
from mien.wx.dataeditors import dataEdit, EDITABLETYPES
import os
from mien.interface.widgets import browseTree

def nameHash(objs):
	d = {}
	for o in objs:
		d[str(o)]=o
	return d

def attrInRange(o, a, r):
	try:
		av = float(o.attrib(a))
		if av < r[0]:
			return False
		if av > r[1]:
			return False
		return True
	except:
		return False

class SynapseEditor(BaseGui):
	def __init__(self, gui, se):
		self.gui=gui
		self.se=se
		self.conditions=[]
		self.location=None
		self.selectInverted=0
		self.getSyns()
		
		BaseGui.__init__(self, gui, title="Edit Synaptic Connections", menus=["File", "Selection", "Synapse"], pycommand=True,height=4)
		commands=[["File", "Quit", lambda x: self.Destroy()],
				  ["Selection", "Location Condition", self.setLocSel],
				  ["Selection", "Add Attribute Condition", self.newAttr],
				  ["Selection", "Edit Attribute Conditions", self.editAttrs],
				  ["Selection", "Clear Conditions", self.killSel],
				  ["Synapse", "Add", self.addSyns],
				  ["Synapse", "Remove", self.killSyns],
				  ["Synapse", "Set Weight", self.weightSyns]]

		self.fillMenus(commands)

		id = wx.NewId()
		self.menus["Selection"].AppendCheckItem(id, "Inverse Selection")
		wx.EVT_MENU(self, id, self.doInvert)

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(wx.StaticText(self.main, -1, "%s" % str(self.se)), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.info=wx.StaticText(self.main, -1, "0 Synapses, 0 Selected, 0 Active")
		sizer.Add(self.info, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

		self.main.SetSizer(sizer)
		self.main.SetAutoLayout(True)
		sizer.Fit(self)

		self.doSelect()
		self.SetSize(wx.Size(400,250))
		
	def getSyns(self):	
		syns={}
		for e in self.se.synRefs():
			i=int(e.attrib("Index"))
			wt=float(e.attrib("Data"))
			try:
				s=e.target()
				syns[i]=[s,wt,e]
			except StandardError:
				self.gui.report('No target for synapse ref %s' % (str(e),))
		self.synapses=syns
	
	def setInfo(self):
		ns=len(self.synapses.keys())
		ss=len(self.selected)	
		a=len([s for s in self.synapses.values() if s[1]!=0])
		self.info.SetLabel("%i Synapses, %i Selected, %i Active" % (ns, ss, a))
		
	def setLocSel(self, event):
		lc=self.location
		if not lc:
			inf=float('inf')
			lc=[[-1.0*inf,inf],[-1.0*inf,inf],[-1.0*inf,inf]]
		d=self.gui.askParam([{'Name':'xmin',
								'Value':lc[0][0]},
								{'Name':'xmax',
								'Value':lc[0][1]},
								{'Name':'ymin',
								'Value':lc[1][0]},
								{'Name':'ymax',
								'Value':lc[1][1]},
								{'Name':'zmin',
								'Value':lc[2][0]},
								{'Name':'zmax',
								'Value':lc[2][1]}])
		if not d:
			return
		lc=[[d[0],d[1]],[d[2],d[3]],[d[4],d[5]]]
		self.location=lc
		self.doSelect()

	def newAttr(self, event):
		d=self.gui.askParam([{'Name':'Attribute',
								'Type':str},
								{'Name':'Condition',
								'Type':'List',
								'Value':['==', '<', '>']},
								{'Name':'Value',
								'Type':str}])
		if not d:
			return
		self.conditions.append([d[0], d[1], d[2]])	
		self.doSelect()

	def editAttrs(self, event):
		cl=self.conditions[:]
		cl = dataEdit(self, cl)
		if cl!=None:
			self.conditions=cl
			self.doSelect()

	def killSel(self, event):
		self.conditions=[]
		self.location=None
		self.doSelect()

	def doInvert(self, event):
		if event.IsChecked():
			self.selectInverted=1
		else:
			self.selectInverted=0
		self.doSelect()	
		
	def doSelect(self):
		if not self.conditions and not self.location:
			self.selected=self.synapses.keys()
		else:
			sel=[]
			for ind in self.synapses.keys():
				out=False
				if self.location:
					loc = self.synapses[ind][0].xyz()
					for i in range(3):
						if loc[i]<self.location[i][0]:
							out=True
							break
						if loc[i]>self.location[i][1]:
							out=True
							break
				if out:
					continue			
				for c in self.conditions:
					atr=self.synapses[ind][0].attrib(c[0])
					if atr==None:
						out=True
						break
					try:
						test=eval('%s%s%s' % (atr, c[1], c[2]))
					except:	
						try:
							test=eval('"%s"%s"%s"' % (atr, c[1], c[2]))
						except:
							self.report('could not test conditon %s. assuming False' % str(c))
							out=True
							break
					if 	not test:
						out=True
						break
				if not out:	
					sel.append(ind)
			if self.selectInverted:
				sel=[i for i in self.synapses.keys() if not i in sel]
			self.selected=sel	
		self.setInfo()	
	
	def addSyns(self, event):
		d=self.gui.askParam([{'Name':'Source Model',
								'Value':'/Cell:',
								'Browser':browseTree}])
		if not d:
			return
		c=self.gui.document.getInstance(d[0])
		print c
		synapses=c.getElements("Synapse")
		print len(synapses)
		if not synapses:
			self.report("No synapses found")
			return
		i=len(self.synapses.keys())
		for s in synapses:
			atrs = {"Data":"1.0",
					"Name":"SynCon%i" % i,
					"Index":i,
					"Target":s.upath()}
			i+=1		
			self.gui.makeElem("ElementReference", atrs, self.se)
			#print i
		self.getSyns()	
		self.doSelect()
		
	def killSyns(self, event):
		for i in self.selected:
			er=self.synapses[i][2]
			er.sever()	
		self.gui.update_all(object=self.se, event="Rebuild")
		self.getSyns()
		self.doSelect()

	def weightSyns(self, event):
		if self.selected:
			cwt=self.synapses[self.selected[0]][1]
		elif self.synapses.keys():
			cwt=sel.synapses.values()[0][1]
		else:
			cwt=1.0
		d=self.askParam([{'Name':'Weight',
							'Value':cwt}])
		if not d:
			return
		for i in self.selected:
			er=self.synapses[i][2]	
			er.attributes["Data"]=str(d[0])
			self.synapses[i][1]=d[0]
		self.report("set weights")
		self.setInfo()
		

	def manualEventAdd(self, event):
		sev = self.gui.objecttree.GetPyData(self.gui.contextMenuSelect[0])
		d = self.gui.askParam([{"Name":"Time",
								"Value":.1}
							   ])
		if not d:
			return
		sev.addEvent(d[0])

ME={}


def synEdit(gui, l):
	c=SynapseEditor(gui, l[0])


def countSyn(gui, l):
	stim= l[0]
	vals=stim.data.getData()
	ne=vals.shape[0]
	nu=unique(vals[:,1]).shape[0]
	gui.report( "%i events in %i units" % (ne, nu) )


	
def shiftSyn(gui, l):
	stim = l[0]
	d=gui.askParam([{"Name":"Offset",
							"Value":0.007}])
	if not d:
		return
	m=where(stim.data.values<0, 0, d[0])
	stim.data.values+=m
	gui.report("Moved events")
	
def clearSyn(gui,l):
	stim = l[0]
	stim.clearEvents()
	gui.report("Removed events from queues")
	
def delSyn(gui,l):
	stim = l[0]
	for el in stim.synRefs()[:]:
		el.sever()
	gui.update_all(object=stim, event="Rebuild")
	gui.report("Deleted Element References")

MECM={"Launch Synapse Editor":(synEdit, "SynapticEvents"),
	"Count Synaptic Events":(countSyn ,"SynapticEvents"),
	"Clear Synapse References": (delSyn,"SynapticEvents"),
	"Clear Synaptic Events": (clearSyn,"SynapticEvents")
}


		
