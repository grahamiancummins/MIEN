#!/usr/bin/env python

## Copyright (C) 2006 Gary Orser
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


def nameHash(objs):
	d = {}
	for o in objs:
		d[str(o)]=o
	return d

class MienGuiApp(BaseGui):
	'''Base class for Mien guis.'''
	def __init__(self, parent=None):
                v = open("version","r")
                try:
                  self.version = v.readline()
                  v.close()
                except:
                  self.version = "Unknown" 
 		BaseGui.__init__(self, parent, id=-1, title="Mien Toplevel - Version " + self.version, menus = ["Applications"], pycommand=False, height=6, memory=100000)
		
		guicommands=[
		["Applications","MienViewer",self.runMienViewer],
		["Applications","CellViewer",self.runCellViewer],
		["Applications","DataViewer",self.runDataViewer],
		["Applications","ImageViewer",self.runImageViewer],
		["Applications","DSP",self.runDSP],
		["Applications","WaveForm",self.runWaveForm],
		["Applications", "Close", lambda x: self.Destroy()]
		]
		self.contextMenuSelect = []
		self.fillMenus(guicommands)
		self.savefile=""
		self.loaddir=""
		self.expansionMods = []
		self.editPaneObject=None
		self.SetSize((750,560))
		self.object_to_move=None
		self.main.SetAutoLayout(True)
	def getEnv(self):
		g = globals()
		l = locals()
		return None, g, l

	def searchEl(self, event):
		s=mien.nmpml.interface.search.SearchGui(self)	
		
	def killwindows(self, event=None):
		for m in self.expansionMods:
			try:
				m.killWindows()
			except:
				pass
	def runMienViewer(self,event=None):
                #mien main
                from mien.interface.main import MienGui
                x = MienGui()
                x.Show(True)

	def runCellViewer(self,event=None):
		from mien.interface.cellview3D import CellViewer
		print "using OpenGL"
		x = CellViewer()
		x.Show(True)

	def runImageViewer(self,event=None):
		from mien.image.viewer import ImageViewer
		x = ImageViewer()
		x.Show(True)

	def runDataViewer(self,event=None):
		#try:
			from mien.datafiles.viewer import Dataviewer
			x = Dataviewer(self,showframe=True)
			x.Show(True)
		#except:
		#	print "No Dataviewer available"

	def runWaveForm(self,event=None):
		from mien.sound.synth import WFGui
		x = WFGui()
		x.Show(True)

	def runDSP(self,event=None):
		from mien.dsp.gui import DspGui
		x = DspGui()
		x.Show(True)


