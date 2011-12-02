
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
from mien.wx.base import wx,BaseGui,spawnControlFrame
from mien.datafiles.viewer import Dataviewer
import threading, os
from mien.wx.graphs.graph import Graph 
#from mien.tools.synapticInputs import *
from mien.math.sigtools import *
from time import time, sleep, strftime
from StringIO import StringIO
import os

HOME=os.environ.get("HOME", os.getcwd())

stimulus_location = os.path.join(HOME, 'datafiles/Stimuli')

def nameHash(objs):
	return dict([(str(o), o) for o in objs])

wxEVT_UPDATE_GUI = wx.NewEventType()
wxEVT_GUI_REPORT = wx.NewEventType()

def EVT_UPDATE_GUI(win, func):
    win.Connect(-1, -1, wxEVT_UPDATE_GUI, func)

def EVT_REPORT(win, func):
    win.Connect(-1, -1, wxEVT_GUI_REPORT, func)
	
class UpdateEvent(wx.PyEvent):
	def __init__(self, best, units):
		wx.PyEvent.__init__(self)
		self.SetEventType(wxEVT_UPDATE_GUI)
		self.best = best
		self.units = units
				
class ReportEvent(wx.PyEvent):
	def __init__(self, value):
		wx.PyEvent.__init__(self)
		self.SetEventType(wxEVT_GUI_REPORT)
		self.value = value

class RunController(BaseGui):
	def __init__(self, parent, exp):
 		BaseGui.__init__(self, parent, id=-1, title="RunControl", menus = ["File", "Recording", "Control"], pycommand=True, height=6, memory=100000)
		guicommands=[["File","Write Hoc", self.writeHoc],
					 ["Recording","Set Display", self.display],
					 ["Recording","Load neuron output", self.loadBat],
					 ["File","Quit", lambda x:self.Destroy()]]
		self.fillMenus(guicommands)
		self.gui=parent
		id = wx.NewId()
		self.menus["Control"].AppendCheckItem(id, "Clear Directory")
		wx.EVT_MENU(self, id, self.setCD)
		self.CD=True
		self.menus["Control"].Check(id, True)

		self.exp=exp
		self.exp.report = self.threadReport
		self.xm=parent

		sizer = wx.BoxSizer(wx.VERTICAL)
		self.tit =  wx.StaticText(self.main, -1, self.exp.upath())
		sizer.Add(self.tit, 0, wx.GROW|wx.ALIGN_LEFT|wx.ALL, 0)
		
		rhs=wx.BoxSizer(wx.HORIZONTAL)
		l= wx.StaticText(self.main, -1, "Directory:")
		rhs.Add(l, 0, wx.GROW|wx.ALIGN_LEFT|wx.ALL, 0)
		cw=os.getcwd()
		l= wx.StaticText(self.main, -1, cw)
		rhs.Add(l, 0, wx.GROW|wx.ALIGN_LEFT|wx.ALL, 0)		
		sizer.Add(rhs, 0, wx.GROW|wx.ALL, 0)

		self.main.SetSizer(sizer)
		self.main.SetAutoLayout(True)
		#self.SetSize((400,180))
		sizer.Fit(self.main)
		
		EVT_UPDATE_GUI(self, self.OnUpdate) 	
		EVT_REPORT(self, self.OnReport)
	
	def writeHoc(self, event):
		exp = self.exp
		exp.writeModel("model.hoc")
		self.report("Wrote model.hoc")

	def display(self, event):
		pass

	def loadBat(self, event=None):
		recordings = self.exp.getComponents()["recs"]	
		if len(recordings)==0:
			self.report("No recordings defined")
			return
		dlg=wx.FileDialog(self, message="Select file", style=wx.OPEN)
		dlg.CenterOnParent()
		if dlg.ShowModal() == wx.ID_OK:
			fname=dlg.GetPath()
		else:
			self.report("Canceled File Load.")
			return	
		flo=StringIO()	
		self.exp.writeModel(flo)
		flo.close()
		inf = open(fname, 'rb')
		l = inf.readlines()[2:]
		output = array(map(lambda x:map(float, x.split()), l))
		recsps = str(1000.0/self.exp._recdt)
		for i, r in enumerate(self.exp._recordings):
			dat = output[:,i]
			tit = str(r[0])
			rec = r[1]
			col = r[2]
			rec.attributes["SamplesPerSecond"]=recsps
			rec.setData(dat, col, tit)
			

			
	def setCD(self, event):
		if event.IsChecked():
			self.CD=True
		else:
			self.CD=False
	
	def run(self, event):
		t1=threading.Thread(target=self.ga.run)
		t1.setDaemon(True)
		t1.start()
		ts=strftime("%m/%d, %H:%M")
		self.start.SetLabel('Started at %s' % (ts,))
		t2=threading.Thread(target=self.monitorRun)
		t2.setDaemon(True)
		t2.start()
		self.report('ready')

	def OnReport(self, event):
		self.report(event.value)

	def threadReport(self, s):
		#print s
		evt = ReportEvent(s)
		wx.PostEvent(self, evt)
		
	def OnUpdate(self, event):
		try:
			self.stats.SetLabel('%i Units, best: %.3f(%i)' % (event.units, event.best[0],event.best[1]))
		except:
			pass
		
	def monitorRun(self):
		while 1:
			try:
				s=self.ga.stop()
				b=self.ga.best
				n=self.ga.nunits
				break
			except:
				sleep(1)
		self.threadReport('Starting Monitor')		
		while not self.ga.stop():
			evt = UpdateEvent(self.ga.best, self.ga.nunits)
			wx.PostEvent(self, evt)
			sleep(3)
		self.threadReport('Stoping Monitor')			

ME={}


def RunCon(gui, l):
	RunController(gui, l[0])

def runExp(gui, l):
	exp = l[0]
	exp.run()
	gui.report('run complete')


MECM={'Launch Simulator Controls':(RunCon, 'Experiment'),
	'Run Experiment':(runExp, 'Experiment')
	}
