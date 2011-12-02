#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2009-03-02.

# Copyright (C) 2009 Graham I Cummins
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


from mien.wx.graphs.graph import Graph
from mien.wx.base import wx, BaseGui
import mien.datafiles.dataset as D
import numpy as N
import mien.interface.widgets as W

class LocusViewer(BaseGui):
	def __init__(self, dv, **kwargs):
		tty=kwargs.get('tty', None) 
		title=kwargs.get('title',"Locus Viewer")
		BaseGui.__init__(self, dv, title=title, menus=["File", "Display"], pycommand=True,height=4, TTY=tty, showframe=False)
		controls=[["File","Select Elements To Show", self.select],
					["Display", "Show All Functions", self.allFuncs],
					["Display", "Select Data", self.select],
					]	
		self.dv = dv	
		if dv:
			self.document = self.dv.document
		self.fillMenus(controls)
		self.mainSizer = wx.BoxSizer(wx.VERTICAL)
		self.main.SetSizer(self.mainSizer)
		self.main.SetAutoLayout(True)
		self.graph=Graph(self.main, -1)		
		self.mainSizer.Add(self.graph, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		self.SetSize(wx.Size(800,600))
 		self.stdFileMenu()
		self.data = []
		
	def dataImport(self, df, add=False, zoom=False):
		dpath = df.upath()
		if not df.xpath(1)[0] == self.document:
			if add:
				df=df.clone()
				self.document.newElement(df)
		if self.data and not add:
			self.data = []
		self.data.append(df.upath())
		print self.document, self.data
		self.display()
		self.report("Done Loading Data")
		
	
	def select(self, event=None):
		els=[e.upath() for e in self.document.getElements('Data')]
		l = self.askParam([{"Name":"Which Objects",
							"Type":'Select',
							"Value":els}])
		if not l:
			return
		self.data = l[0]
		self.display()
	
	def allFuncs(self, event=None):
		f = self.document.getElements("Data", {"SampleType":"function"})
		self.data = [i.upath() for i in f] 
		self.display()
		
	def display(self):
		#import time;st=time.time()
		self.graph.plots={}
		for p in self.data:
			dat = self.document.getInstance(p)
			dd = dat.getData()
			if dat.stype() in ['ensemble', 'histogram', 'timeseries']:
				for i in range(dd.shape[1]):
					self.graph.addPlot(dd[:,i], sampr=1.0/dat.fs(), style = 'line')
			elif 'events' in dat.stype():
				t = dd[:,0]/float(dat.fs())
				if 'labeled' in dat.stype():
					y = dd[:,1].astype(t.dtype())
				else:
					y = N.zeros_like(t)
				self.graph.addPlot(N.column_stack([t, y]), style = 'points', width = 3)
			else:
				style = dat.attrib("style") or 'points' 
				for i in range(1, dd.shape[1]):
					self.graph.addPlot(dd[:,[0,i]], style = style)
		self.graph.fullScale()
		self.graph.DrawAll()		
		