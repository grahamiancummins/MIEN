#!/usr/bin/env python
# encoding: utf-8
#Created by gic on 2007-03-02.

# Copyright (C) 2007 Graham I Cummins
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

				
				
		# 		  ['Selection',"Create Synapse", self.synFromPoint],
		# 		  ['Spatial',"Kill Points", self.killPoint],
		# 
		# 		  ['Edit',"Split Section", self.splitSec],
		# 		  ['Edit',"Edit Point", self.changePoint],
		# 		  ['Edit',"Remove Point", self.rmOnePt],
		# 		  ['Edit',"Add Point", self.addOnePt],
		# 		  ['Edit',"Remove Selected Sections", self.rmSelSecs],
		# 		  ['Edit',"Set Root", self.setRoot],
		# 		  ['Edit',"Add Section", self.newSec],
		# 		  ['Edit',"Change Section Parent", self.moveSec]
		# 		  ]
		# 
		# 
		# 
		# 
		# 
		# 
		# 
		# 
		# 
		# 
		# 
		# 
		# 
		# 
		# 		def synFromPoint(self, event=None):
		# 			if not self._foundLastPoint:
		# 				self.report("No points selected")
		# 				return
		# 			cell, sec, loc=self._foundLastPoint[0][:3]
		# 			sec=cell._sections[sec]
		# 			pind = sec.ptAtRel(loc)
		# 			nsyns = len(cell.getElements(["Synapse"]))
		# 			d=self.askParam([{"Name":"Type",
		# 							"Value":"GSyn"},
		# 							{"Name":"Direction",
		# 							"Value":"315"},
		# 							{"Name":"Length",
		# 							"Value":"1000"},
		# 							{"Name":"Cercus",
		# 							"Value":"L"}
		# 								])
		# 			if not d:
		# 				return
		# 			atr={'Type':d[0],'Direction':d[1],'Length':d[2],
		# 				'Id':str(nsyns), 'Point':str(pind), 'Cercus':d[3],
		# 				'Name':"%s%i" % (d[0], nsyns)}
		# 			self.xm.makeElem("Synapse", atr, sec)
		# 
		# 
		# 			def changePoint(self, event=None):
		# 				cell, sec, loc, name=self._foundLastPoint[0]
		# 				ps="%s.%s(%.3f) " % (cell.name(), sec, loc)
		# 				sec=cell._sections[sec]
		# 				ind = sec.ptAtRel(loc)
		# 				pt=sec.points[ind, :]
		# 				d=self.askParam(["Editing %s" % ps,
		# 								 {"Name":"X",
		# 								  "Value":pt[0]},
		# 								 {"Name":"Y",
		# 								  "Value":pt[1]},
		# 								 {"Name":"Z",
		# 								  "Value":pt[2]},
		# 								 {"Name":"D",
		# 								  "Value":pt[3]}])
		# 				if not d:
		# 					return
		# 				for i in range(4):
		# 					sec.points[ind,i]=d[i]
		# 				style=self.graph.plots[name]["style"]	
		# 				self.graph.kill(name)
		# 				self.graph.addShapePlot(None, cell, style)
		# 
		# 			def rmOnePt(self, event=None):
		# 				cell, sec, loc, name=self._foundLastPoint[0][:4]
		# 				ps="%s.%s(%.3f) " % (cell.name(), sec, loc)
		# 				sec=cell._sections[sec]
		# 				ind = sec.ptAtRel(loc)
		# 				r=range(sec.points.shape[0])
		# 				r.remove(ind)
		# 				sec.points=sec.points[r]
		# 				self.report("deleted %s" % ps)
		# 				style=self.graph.plots[name]["style"]	
		# 				self.graph.kill(name)
		# 				self.graph.addShapePlot(None, cell, style)
		# 
		# 
		# 			def addOnePt(self, event=None):
		# 				cell, secn, loc, name=self._foundLastPoint[0][:4]
		# 				sec=cell._sections[secn]
		# 				ind = sec.ptAtRel(loc)
		# 				pt=sec.points[ind, :]
		# 				d=self.askParam(["Add Point in  %s.%s" % (cell.name(), secn),
		# 								 {"Name":"Index",
		# 								  "Type":"List",
		# 								  "Default":ind+1,
		# 								  "Value":range(sec.points.shape[0]+1)},
		# 								 {"Name":"X",
		# 								  "Value":pt[0]},
		# 								 {"Name":"Y",
		# 								  "Value":pt[1]},
		# 								 {"Name":"Z",
		# 								  "Value":pt[2]},
		# 								 {"Name":"D",
		# 								  "Value":pt[3]}])
		# 				if not d:
		# 					return
		# 				pts=zeros((sec.points.shape[0]+1, sec.points.shape[1]),sec.points.dtype.char)
		# 				r=range(pts.shape[0])
		# 				r.remove(d[0])
		# 				pts[r]=sec.points
		# 				for i in range(4):
		# 					pts[d[0],i]=d[i+1]
		# 				sec.setPoints(pts)
		# 				style=self.graph.plots[name]["style"]	
		# 				self.graph.kill(name)
		# 				self.graph.addShapePlot(None, cell, style)
		# 
		# 			def rmSelSecs(self, event=None):
		# 				secs= self.selected[:]
		# 				if not secs:
		# 					self.report("No sections selected")
		# 					return
		# 				d=self.askParam(["Deleting %i sections" % len(secs),
		# 								 {"Name":"Delete sections?",
		# 								  "Type":"List",
		# 								  "Value":["Yes", "No"]}])	
		# 				if not d or d[0]=="No":
		# 					return
		# 				conts=[]
		# 				self._foundLastPoint = []
		# 				self.selected=[]
		# 				for s in secs:
		# 					if not s.parent():
		# 						self.report("can't delete root section")
		# 						continue
		# 					if not s.container in conts:
		# 						conts.append(s.container)
		# 					kids=s.container.getChildren(s.name())
		# 					for k in kids:
		# 						ks=s.container._sections[k]
		# 						if ks in secs:
		# 							continue
		# 						ks.attributes["Parent"]=s.parent()
		# 						ks.points[0]=s.container._sections[s.parent()].points[-1].copy()
		# 					s.container.elements.remove(s)
		# 				for c in conts:		
		# 					c.refresh()
		# 					self.update_all(object=c)
		# 
		# 			def newSec(self, event=None):
		# 				cell, secn, zoc, name=self._foundLastPoint[0][:4]
		# 				sec=cell._sections[secn]
		# 				pt=sec.points[-1,:]
		# 				d=self.askParam(["Adding section as child of %s.%s" % (cell.name(), secn),
		# 								 {"Name":"End X",
		# 								  "Value":pt[0]},
		# 								 {"Name":"End Y",
		# 								  "Value":pt[1]},
		# 								 {"Name":"End Z",
		# 								  "Value":pt[2]},
		# 								 {"Name":"End D",
		# 								  "Value":pt[3]}])
		# 				if not d:
		# 					return
		# 				pts=zeros((2,4), Float32)
		# 				pts[0,:]=pt.copy()
		# 				for i in range(4):
		# 					pts[1,i]=d[i]
		# 				pars={"Name":cell.newSectionName(),"Parent":secn}
		# 				if self.xm:
		# 					new=self.xm.makeElem("Section", pars, cell)
		# 				else:
		# 					new = mien.nmpml.elements["Section"](pars)
		# 					cell.newElement(new)	
		# 				new.setPoints(pts)
		# 				cell.refresh()
		# 				self.update_all(object=cell)
		# 
		# 
		# 			def setRoot(self, event=None):
		# 				cell, secn,loc,name=self._foundLastPoint[0][:4]
		# 				sec=cell._sections[secn]
		# 				parn=sec.parent()
		# 				if not parn:
		# 					self.report("section is already root")
		# 					return
		# 				kids=cell.getChildren(secn)
		# 				if kids:
		# 					par=cell._sections[parn]
		# 					par.points[-1]=sec.points[-1].copy()
		# 				else:
		# 					sec.setPoints(sec.points[arange(sec.points.shape[0]-1, -1,-1)])
		# 				sec.attributes["Parent"]="None"
		# 				tsn=secn
		# 				while parn:
		# 					par=cell._sections[parn]
		# 					kids=cell.getChildren(parn)
		# 					for k in kids:
		# 						if k==tsn:
		# 							continue
		# 						ks=cell._sections[k]
		# 						ks.attributes["Parent"]=tsn
		# 					par.setPoints(par.points[arange(par.points.shape[0]-1, -1,-1)])
		# 					parn=par.parent()
		# 					par.attributes["Parent"]=tsn
		# 					tsn=par.name()
		# 
		# 				cell.refresh()
		# 				self._foundLastPoint = []
		# 				self.update_all(object=cell)
		# 
		# 
		# 			def moveSec(self, event=None):
		# 				cell, sec, loc, name=self._foundLastPoint[0][:4]
		# 				cell2, sec2=self._foundLastPoint[1][:2]
		# 				if cell!=cell2:
		# 					self.report("The selected points are not in the same cell")
		# 					return
		# 				sec=cell._sections[sec]
		# 				sec2=cell._sections[sec2]
		# 				if not sec2.parent():
		# 					self.report("can't move the root section")
		# 					return
		# 				sec2.attributes["Parent"]=sec.name()
		# 				sec2.points[0]=sec.points[-1].copy()
		# 				self._foundLastPoint = []
		# 				cell.refresh()
		# 				self.update_all(object=cell)
		# 
		

from numpy import take, logical_not

def killPoints(doc, elems=[], Xthresh=0.0, Xabove=True, Ythresh=-1000.0, Yabove=True, Zthresh=-1000.0, Zabove=True):
	''' 
	
'''
	objl = [doc.getInstance(e) for e in elems]
	if not objl:
		return
	for obj in objl:
		print obj
		pts=obj.getPoints()
		xm=(pts[:,0]>=Xthresh)==Xabove
		ym=(pts[:,1]>=Ythresh)==Yabove
		zm=(pts[:,2]>=Zthresh)==Zabove
		mask=logical_not((xm*ym*zm).astype('?'))
		npts=mask.sum()
		if not npts:
			doc.report("object %s is being deleted, because all points are in the exclusion range" % (str(obj),))
			obj.sever()
			continue
		if npts == pts.shape[0]:
			doc.report("object %s is not altered" % (str(obj),))
			continue
		doc.report("removing %i points from object %s" % (pts.shape[0]-npts, str(obj),))
		pts = pts[mask, :]
		obj.setPoints(pts)
			
		# 
		# 
		# 
		# 
		# 
		# 
		# ["File", "Store Group Colors", self.storeColors],
		# 		  ["File", "Load Group Colors", self.loadColors],
		# 		  ["File", "Load Microscope Image Stack", self.loadImages],
		# 		
