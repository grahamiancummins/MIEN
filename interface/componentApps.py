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
from mien.datafiles.viewer import Dataviewer
from mien.image.viewer import ImageViewer
from mien.sound.synth import WFGui
from mien.dsp.gui import DspGui
from mien.interface.cellview3D import CellViewer
from mien.interface.widgets import FileBrowse
from mien.datafiles.fview import LocusViewer

def getApp(gui, cl):
	plots=gui.getAllGuis()
	plots=[x for x in plots if isinstance(x, cl)]
	if plots:
		pn=["%i:%s" % (i, n.GetTitle()) for i,n in enumerate(plots)]
		pn=["New"]+pn
		d=gui.askParam([{"Name":"Which Plot?",
								"Type":"List",
								"Value":pn}])
		if d and d[0]!="New":	
			ind=pn.index(d[0])
			plot=plots[ind-1]
			return plot
	rd=makeReturnDat(gui)		
	a=cl(gui, returnData=rd)
	a.SetTitle("Mien Viewer %i" % len(plots))
	a.Show(True)
	return a

def returnData(gui, dat):
	datas = gui.document.getElements("Data")
	d = {}
	for o in datas:
		s = str(o.container)+"."+str(o)
		d[s]=o
	datas = d
	dlk=[s for s in datas.keys() if not s.startswith("SynapticEvents")]
	d = gui.askParam([{"Name":"Send to which element?",
							"Type":"List",
							"Value":dlk}])
	if not d:
		return
	de = datas[d[0]]
	de.datinit(dat.data, dat.header(), copy=True)
	gui.update_all(object=de)

def makeReturnDat(gui):
	def foo(dat):
		returnData(gui, dat)
	return foo	

def launchCV(gui):
	plot=getApp(gui, CellViewer)
	plot.onNewDoc()

def launchIV(gui, im=None):
	plot=getApp(gui, ImageViewer)
	if not im:
		plot.onNewDoc()
	else:
		plot.select(im)

def launchLV(gui):
	lv=LocusViewer(gui)
	lv.Show(True)
	lv.allFuncs()
	
	
def datToDV(gui, elems):
	if elems[0].attrib('SampleType')=='image':
		launchIV(gui, elems[0])
		return
	dv=getApp(gui, Dataviewer)
	dv.bindToData(elems[0])
	
def absToDSP(gui, elems):
	dsp=getApp(gui, DspGui)
	dsp.cleanState()
	dsp.document=gui.document
	dsp.model=elems[0]
	dsp.update_self(object=elems[0])	

def getData(gui, elems):
	data = elems[0]
	d = gui.askParam([{"Name":"File Name",
							"Value":"",
							"Browser":FileBrowse}
						   ])
	if not d:
		return
	doc=gui.load(fname=d[0], returndoc=True)
	dat=doc.getElements('Data', depth=1)[0]
	data.mirror(dat, True)
	gui.update_all(object=data)


	




def setAuto(gui):
	datas = gui.document.getElements("Data")
	for i, d in enumerate(datas):
		d.attributes["Url"]='auto://upath'
	gui.report("set attributes")
	
MECM={"Send To Viewer":(datToDV, 'Data'),
	"Import Data": (getData, 'Data'),
	"Launch DSP Editor":(absToDSP, 'AbstractModel')
	}

ME={"Show Cell Viewer":launchCV, 
	"Show Image Viewer":launchIV, 
	"Show Function Viewer":launchLV, 
	"Set automatic (local) urls for Data":setAuto}


