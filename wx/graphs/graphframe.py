#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2008-01-18.

# Copyright (C) 2008 Graham I Cummins
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA 02111-1307 USA
#


from mien.wx.graphs.graph import *
from mien.wx.graphs.graphGL import GraphGL
from mien.wx.base import BaseGui
import mien, time, os, sys
from mien.tools.identifiers import getHomeDir

class GraphFrame(BaseGui):
	graph_type=Graph	
	default_size=(600,700)	
	init_defaults={'title':"Graph Viewer", 'menus':["File", "Graph"], 'pycommand':True,'height':4, 'showframe':False}
	controlpanel=None
			
	def __init__(self, parent=None, **kwargs):
		kwargs.update(self.init_defaults)
		BaseGui.__init__(self, parent, **kwargs)
		self.fillMenus(self.gen_controls())
		self.mainSizer = wx.BoxSizer(wx.VERTICAL)
		self.main.SetSizer(self.mainSizer)
		self.main.SetAutoLayout(True)
		if self.controlpanel:
			self.panel=self.controlpanel(self.main, self)
			self.mainSizer.Add(self.panel, self.panel.gr, wx.ALIGN_BOTTOM|wx.ALL, 5)
		
		if self.preferences:
			self.load_saved_prefs()
		
		self.graph=None	
		self.newGraph(kwargs.get('gclass'), kwargs.get('size'))	

	def gen_controls(self):		
		controls=[
					  ["File", "Quit", lambda x:self.Destroy()],
				 ]
		return controls		
	
	def newGraph(self, gclass=None, size=None):
		if not gclass:
			gclass=self.graph_type
		if not size:
			size=self.default_size	
		if self.graph:
			self.graph.report=None
			self.graph.Destroy()
			del(self.graph)
		self.graph=gclass(self.main)
		self.graph.report=self.report
		self.graphKeyBind()
		self.buildGraphMenu()
		self.mainSizer.Add(self.graph, 20, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		self.graph.Show(True)
		self.mainSizer.Fit(self.main)
		self.SetSize(apply(wx.Size,size))
		self.frame=0	
		self.onNewGraph()

		
	def graphKeyBind(self):
		pass	
		
	def onNewGraph(self):
		self._setview()
		self._gda()
		
	def buildGraphMenu(self):	
		try:
			self.refreshMenu('Graph', dict(self.graph.contextMenuContents))
		except:
			pass	
	
	def _setview(self):
		if self.graph.__class__==GraphGL:
			self.graph.stdView()
		else:
			self.graph.fullScale()
		
	def _gda(self):
		if self.graph.__class__==GraphGL:
			self.graph.OnDraw()
		else:
			self.graph.DrawAll()

def launchGraphFrame(refbox=None):
	h=getHomeDir()
	cd=os.path.join(h, '.mien')
	os.environ['MIEN_CONFIG_DIR']=cd
	app=wx.PySimpleApp()
	z=GraphFrame()
	if refbox!=None:
		refbox.append(z)
	z.Show(True)
	app.MainLoop()

	
	
def launchThread():
	from threading import Thread
	from time import sleep
	rb=[]
	t = Thread(target=launchGraphFrame, args=(rb,))
	t.start()
	n=0
	s=None
	while n<10:
		try:
			s=rb[0]
			break
		except:
			n+=1
			sleep(1)
	return s	
		
if __name__=='__main__':
	launchGraphFrame()	