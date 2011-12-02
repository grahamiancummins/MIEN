#! /usr/bin/env/python

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

import mien.optimizers.arraystore as ast
import threading, os
from mien.wx.base import wx, BaseGui
from time import time, sleep, strftime
import mien.optimizers.analysis
#from mien.wx.graphs.graph import Graph
from mien.math.array import ones, logical_and, take, nonzero1d, argmin, argsort

wxEVT_UPDATE_GUI = wx.NewEventType()
wxEVT_GUI_REPORT = wx.NewEventType()

def EVT_UPDATE_GUI(win, func):
    win.Connect(-1, -1, wxEVT_UPDATE_GUI, func)

def EVT_REPORT(win, func):
    win.Connect(-1, -1, wxEVT_GUI_REPORT, func)
	

class UpdateEvent(wx.PyEvent):
	def __init__(self, best, units, stop=False):
		wx.PyEvent.__init__(self)
		self.SetEventType(wxEVT_UPDATE_GUI)
		self.best = best
		self.units = units
		self.stopped=stop
				
class ReportEvent(wx.PyEvent):
	def __init__(self, value):
		wx.PyEvent.__init__(self)
		self.SetEventType(wxEVT_GUI_REPORT)
		self.value = value



def loadArrayStore(gui):
	fn=''
	try:
		file=gui.ga.attrib('File')
		dp, fn=os.path.split(file)
		if not dp:
			file=self.document.fileinformation["filename"]
			dp=os.path.split(file)[0]
	except:
		dp=os.getcwd()
	dlg=wx.FileDialog(gui, message="Select arraystore file", defaultDir=dp, defaultFile=fn, style=wx.OPEN)
	dlg.CenterOnParent()
	if dlg.ShowModal() == wx.ID_OK:
		fname=dlg.GetPath()
	else:
		gui.report("Canceled File Load.")
		return None
	gui.report("Loading file  %s" % fname)
	pars=gui.ga.params()
	w=len(pars._pars)+1	
	if gui.ga.attrib('EvalConditions'):
		w+=int(gui.ga.attrib('EvalConditions'))
	if not ast.verify(fname, w, minlength=1):
		gui.report("File  %s is not an appropriate arraystore (it is not an arraystore at all, it has the wrong width, or it is empty." % fname)
		return None
	return fname
		
	
class OptMonitor(BaseGui):
	def __init__(self, parent, ga):
 		BaseGui.__init__(self, parent, id=-1, title="Optimizer Control", menus = ["Algorithm"], pycommand=True, height=10, memory=100000, TTY=False)
		guicommands=[["Algorithm","Test", self.test],
				     ["Algorithm","Prep", self.prep],
				     ["Algorithm","Load previous run", self.resume],
					 ["Algorithm","Quick Resume", self.rerun],
					 ["Algorithm","Run", self.run],
					 ["Algorithm","Stop", self.stop],
					 ["Algorithm","Snapshot", self.snapshot],
					 ["Algorithm","Assign Best", self.assign],
					 ["Algorithm","Quit", self.quit]]
		self.fillMenus(guicommands)

		self.ga=ga
		self.runthread=None
		self._oldreport=self.ga.report
		self.ga.report = self.threadReport

		sizer = wx.BoxSizer(wx.VERTICAL)
		self.tit =  wx.StaticText(self.main, -1, self.ga.attrib('File'))
		sizer.Add(self.tit, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)

		pars=ga.params()
		inf = "%i params, %.5g values" % (len(pars._pars), pars.size())
		self.inf =  wx.StaticText(self.main, -1,inf)
		sizer.Add(self.inf, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)

		self.start =  wx.StaticText(self.main, -1,'Not Running')
		sizer.Add(self.start, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)

		self.stats =  wx.StaticText(self.main, -1, '%i Units, best: %.3f' % (0, -1))
		sizer.Add(self.stats, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		self.main.SetSizer(sizer)
		self.main.SetAutoLayout(True)
		sizer.Fit(self.main)
		self.SetSize((400,400))


		EVT_UPDATE_GUI(self, self.OnUpdate) 	
		EVT_REPORT(self, self.OnReport)


	def prep(self, event):
		if self.runthread:
			self.report("Can't prep while running!")
		self.ga.prep()
		pars=self.ga.params()
		inf = "%i params, %.5g values" % (len(pars._pars), pars.size())
		self.inf.SetLabel(inf)
		#self.report("Prep complete")
		
	def resume(self, event):
		if self.runthread:
			self.report("Can't resume while running!")
		fn=loadArrayStore(self)
		if not fn:
			return 
		self.tit.SetLabel(fn)	
		self.ga.resume(fn)
		evt = UpdateEvent(self.ga._best, self.ga._nunits)
		wx.PostEvent(self, evt)
			
	def quit(self, event):
		self.ga.report=self._oldreport
		try:
			self.stop()
		except:
			pass				
		self.Destroy()

	def stop(self, event=None):
		if self.runthread:
			self.ga._abort=True
			self.runthread.join(20)
			self.runthread=None
			self.report('run terminated')

	def test(self, event):
		rc, fit, ec=self.ga.test()
		self.report("OK: %s => (%.3f, %s)" % (str(rc)[:50], fit, ec))
	
	def rerun(self, event):
		self.ga.resume()
		self.run(None)
	
	def run(self, event):
		t1=threading.Thread(target=self.ga.run)
		t1.setDaemon(True)
		t1.start()
		self.runthread=t1
		ts=strftime("%m/%d, %H:%M")
		self.start.SetLabel('Started at %s' % (ts,))
		t2=threading.Thread(target=self.monitorRun)
		t2.setDaemon(True)
		t2.start()
		self.report('running...')

	def OnReport(self, event):
		self.report(event.value)

	def threadReport(self, s):
		#print s
		evt = ReportEvent(s)
		wx.PostEvent(self, evt)
		
	def OnUpdate(self, event):
		if event.stopped:
			try:
				self.start.SetLabel('Not Running')
			except:
				raise
		try:
			self.stats.SetLabel('%i Units, best: %.3f(%i)' % (event.units, event.best[0],event.best[1]))
		except:
			pass
		
	def monitorRun(self):
		self.threadReport('Starting Monitor')	
		s=False
		while (not s):
			try:
				s=self.ga.done()
				b=self.ga._best
				n=self.ga._nunits
			except:
				s=False
				sleep(1)
				continue	
			evt = UpdateEvent(b, n)
			wx.PostEvent(self, evt)
			sleep(3)
		if self.runthread:
			try:
				self.runthread.join(10)
				self.runthread=None
			except:
				pass
		try:
			b=self.ga._best
			n=self.ga._nunits
		except:
			b='foo'
			n='bar'
		evt = UpdateEvent(b, n, True)
		wx.PostEvent(self, evt)
		self.threadReport('Stoping Monitor')			

				
	def getChrom(self, id):
		os=1
		if self.ga.attrib('EvalConditions'):
			os+=1
		if self.ga._store:
			self.ga.lock.acquire()
			try:
				chrom = self.ga._store[id]
				print id, chrom
				chrom=chrom[os:]
			except:
				self.report("Can't find a unit index %s" % id)
				chrom = None
			self.ga.lock.release()
			return chrom
		else:
			try:
				store=ast.ArrayStore(self.ga.attrib("File"), 'r') 
			except:
				self.report("Can't open unit archive")
				raise
				return None
			try:
				chrom = store[id]
				chrom=chrom[os:]
			except:
				self.report("Can't find a unit index %s" % id)
				chrom=None
			store.close()
			return chrom					

	def snapshot(self, event):
		chrom = self.getChrom(self.ga._best[1])
		if chrom==None:
			return
		rep="best unit is index %i, with fitness %.6f\n" % (self.ga._best[1],self.ga._best[0])
		pars=self.ga.params()
		names=pars.getNames()		
		pvs= dict(zip(names, chrom))
		for pn in pvs.keys():
			rep+="%s -> %.6f\n" % (pn, pvs[pn])
		self.showText(rep)
		
	def assign(self, event):
		chrom = self.getChrom(self.ga._best[1])
		if chrom==None:
			return
		pars=self.ga.params()
		pars.quickset(chrom)
		pars.flush()
		self.report("Assign call complete")

class OptAnalyzer(BaseGui):
	def __init__(self, parent=None, opt=None):
 		BaseGui.__init__(self, parent, id=-1, title="Optimizer Analysis", menus = ["Data", "Units", "Analysis"], pycommand=True, height=6, memory=100000)
		guicommands=[["Data","Load Data", self.load],
					 ["Data", "Create Data Element", self.save],
					 ["Data","----"],
					 ["Data","Reload Analysis Module", self.bounce],
					 ["Data","Quit", self.quit],
					 ["Units", "Show", self.displayUnit],
					 ["Units", "Assign", self.assign],
					 ["Units", "Re-Evaluate", self.evalUnit]]
		
		self.ga=opt
		self.pars=opt.params()
		self.condition={}
		self.fillMenus(guicommands)

		sizer = wx.BoxSizer(wx.VERTICAL)
		
		self.tit =  wx.StaticText(self.main, -1, 'No Algorithm')
		sizer.Add(self.tit, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		self.sizeinf =  wx.StaticText(self.main, -1, ' No Data ')
		sizer.Add(self.sizeinf, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		self.stats =  wx.StaticText(self.main, -1, ' -- ')
		sizer.Add(self.stats, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		
		
		self.main.SetSizer(sizer)
		self.main.SetAutoLayout(True)
		sizer.Fit(self.main)
		self.SetSize((600,200))
		self.bounce()
		self.np=len(self.pars._pars)
		self.nunits=0
		if opt.attrib('EvalConditions'):
			self.hasEC=opt.attrib('EvalConditions')
		else:
			self.hasEC=0
		storesize=self.np+1+self.hasEC
		self.data=None
		if ast.verify(opt.attrib('File'), storesize, 1):
			self.ast=ast.ArrayStore(opt.attrib('File'), 'w')
		else:	
			self.report("Optimizer File attribute does not refference a valid arraystore. You will need to load data by hand") 
			self.ast=None
		self.showInfo()	
		
	def quit(self, event):
		try:
			self.ast.close()
		except:
			pass
		self.Destroy()

	def getCondition(self):
		'''Return a 1D array of integers representing the unit IDs for which all specified conditions are met'''
		if not (self.ast or self.data):
			return None
		if not self.condition:
			return arange(self.nunits)
		inds=ones(self.nunits)
		for k in self.condition.keys():
			colid=self.parnames.index(k)
			if self.data:
				col=data.getData()[:,colid]
			else:	
				col=self.ast.getColumn(colid)
			mi, ma = self.condition[k]
			newinds=logical_and(col>=mi, col<=ma)
			inds=logical_and(inds, newinds)
		return nonzero1d(inds)

	def showInfo(self):
		tit = "%s (%i params, %.5g points)" % (self.ga.attrib('File'), self.np, self.pars.size())
		self.parnames=['Fitness'] 
		if self.hasEC:
			for i in range(self.hasEC):
				self.parnames.append('EvalCondition%i' % i)
		self.parnames.extend(self.pars.getNames()) 
		if self.ast:	
			self.nunits=len(self.ast)
			fit=self.ast.getColumn(0)
			if self.condition:
				mask=self.getCondition()
				cfit=take(fit, mask)
			else:
				cfit=fit
			inf = "%i units, %i selected" % (self.nunits, cfit.shape[0])
			stats='min: %.3f, mean: %.3f, max:%.3f, stddev: %.3f' % (cfit.min(), cfit.mean(), cfit.max(), cfit.std())
		else:
			inf=' No Data Loaded '
			stats=' -- '
		self.tit.SetLabel(tit)
		self.stats.SetLabel(stats)
		self.sizeinf.SetLabel(inf)

	def load(self, event=None, dname=None):
		fn=loadArrayStore(self)
		if not fn:
			return
		self.ast=ast.ArrayStore(fn, 'w')
		self.showInfo()

	def save(self, event=None):
		if not self.ast:
			self.report("No Data")
			return
		
	def bounce(self, event=None):
		reload(mien.optimizers.analysis)
		self.spm = mien.optimizers.analysis.GuiAnalysisModule(self)
		self.spm.makeMenus()
		self.report("Reloaded")

	def makeGraph(self):
		bar = {'size':(600,600), 'style':wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE}
		frame = wx.Frame(self, -1, "GA Analysis Graph", **bar)
		frame.g = Graph(frame, -1)
		frame.Show(True)
		return frame.g

	def assign(self, event):
		chrom = self.getChrom(None)
		if chrom==None:
			return
		self.pars.quickset(chrom[1+self.hasEC:])
		self.pars.flush()
		self.report("Assign call complete")

	def displayUnit(self, event):
		chrom = self.getChrom(None)
		if chrom==None:
			return
		rep=""
		for i, pn in enumerate(self.parnames):
			rep+="%s -> %.6f\n" % (pn, chrom[i])
		self.showText(rep)
		
	def evalUnit(self, event):
		chrom = self.getChrom(None)
		if chrom==None:
			return			
		(fit, ec)=self.ga.local_eval(chrom[1+self.hasEC:])
		rep=""
		for i, pn in enumerate(self.parnames):
			rep+="%s -> %.6f\n" % (pn, chrom[i])
		rep+="Old fitness -> %.4f\n" % (chrom[0],)
		rep+="New fitness -> %.4f\n" % (fit,)
		self.showText(rep)

	def getChrom(self, id=None):
		if not id:
			l=self.askParam([{
							"Name":"Mode",
							"Type":"List",
							"Value":["Ordinal", "Index", "Fitness"]
							},{
							"Name":"Value",
							"Value":0.0
							}
							])
			if not l:
				return
			fit=self.ast.getColumn(0)	
			if l[0].startswith("I"):
				id=int(l[1])
			elif l[0].startswith("O"):
				id=argsort(fit)[int(l[1])]
			else:
				id=argmin(abs(fit-l[1]))
			self.report("Selected Unit %i (fitness %.4f)" % (id, fit[id]))
		return self.ast[id]

