
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
import mien.nmpml
from mien.spatial.alignment import all_alignables, alignByRP, alignObject
import mien.parsers.fileIO
import wx, os
from mien.math.array import take, nonzero1d

#genRef("ManualAlignment", "micrometers", self.document)


parlist = [{"Name":'Trans_x',
			"Value":0.0},
		   {"Name":'Trans_y',
			"Value":0.0},
		   {"Name":'Trans_z',
			"Value":0.0},
		   {"Name":'Rot_x',
			"Value":0.0},
		   {"Name":'Rot_y',
			"Value":0.0},
		   {"Name":'Rot_z',
			"Value":0.0},
		   {"Name":'Scale_x',
			"Value":1.0},
		   {"Name":'Scale_y',
			"Value":1.0},
		   {"Name":'Scale_z',
			"Value":1.0},
		   {"Name":'Scale_d',
			"Value":1.0},
		   {"Name":'Order',
			"Value":'Trans,Rot,Scale'}]
			
def nameHash(objs):
	d = {}
	for o in objs:
		d[str(o)]=o
	return d

ME={}

def setReference(gui, o):
	obj = o[0]
	rps = gui.document.getElements("ReferencePoint")
	rps = nameHash(rps)
	l = gui.askUsr("Use Reference Point:", rps.keys())
	if not l:
		return
	newref =rps[l]
	rprs = obj.getTypeRef("ReferencePoint")
	for rp in rprs:
		gui.update_all(object=rp, event="Delete")
	gui.makeElem("ElementReference",
					  {"Name":"RefPoint",
					   "Target":newref.upath()},
					  obj)
	gui.update_all(object=obj)
	
def namedPoint(gui, o):
	obj = o[0]
	if not obj.point_labels:
		self.report("Points are not labeled")	
	points = {}
	for i in obj.point_labels:
		points[obj.point_labels[i]] = obj.getPoints()[i,:]
		
	d=gui.askUsr("Which point?", points.keys())
	if not d:
		self.report("Canceled")
	gui.report("%s => %s" % (d, str(points[d])))


MECM={"Set Reference Point":(setReference, ["Cell", "Fiducial", "ReferenceConversion"]),
	"Get Named Point":(namedPoint, 'Fiducial'),
	
}


	# 		
	# def alignAllElements(self, event=None):
	# 	rps = self.gui.document.getElements("ReferencePoint")
	# 	if rps:
	# 		rpd = {}
	# 		for r in rps:
	# 			rpd[str(r)] = r
	# 		targ=self.gui.askUsr("Align to which ReferencePoint?", rpd.keys())
	# 		if not targ:
	# 			return
	# 		
	# 	objs = all_alignables(self.gui.document) + [rpd[targ]]
	# 	alignByRP(objs, self.report)
	# 	for o in objs[:-1]:
	# 		self.gui.update_all(object=o)
	# 	self.report("Aligned all to %s" % targ)
	# 	
	# 
	# def UI_AddFiducialPoints(self, event=None):
	# 	dlg=wx.FileDialog(self.gui, message="Select file", defaultDir=self.gui.loaddir, style=wx.OPEN)
	# 	dlg.CenterOnParent()
	# 	if dlg.ShowModal() == wx.ID_OK:
	# 		fname=dlg.GetPath()
	# 	else:
	# 		self.gui.report("Canceled File Load.")
	# 		return
	# 	if fname.endswith(".xml"):
	# 		h = "Neurosys Fiducials"
	# 	else:
	# 		h = "Stage Coords"
	# 	try:	
	# 		doc = mien.parsers.fileIO.READERS[h](fname)
	# 	except:
	# 		self.gui.report("This doesn't seem to be a fiducial file!")
	# 		return
	# 	fedpts = doc.elements[0]
	# 	point1 = fedpts.getNamedPoint("FIRST_BRANCH_AFFERENT")
	# 	if point1 == None:
	# 		l = fedpts.point_labels
	# 		d=self.gui.askUsr("First Branch Name?", fedpts.point_labels.values())
	# 		if not d:
	# 			self.report("No Alignment!")
	# 			return
	# 		point1 = fedpts.getNamedPoint(d)
	# 	cells = self.gui.document.getElements("Cell")
	# 	if len(cells)==0:
	# 		self.report("Cant generate conversion. No cells")
	# 		return
	# 	elif len(cells)==1: 
	# 		cell = cells[0]
	# 	else:
	# 		cd = {}
	# 		for c in cells:
	# 			cd[str(c)] = c
	# 		cell=self.gui.askUsr("Which cell is the afferent?", cd.keys())
	# 		if not cell:
	# 			return
	# 		cell = cd[cell]
	# 	point2 = cell.getSection(cell.root()).points[-1,:3]
	# 	self.report("First Branch was %s" % str(point2))
	# 	xyz = point1[:3] - point2[:3]
	# 	conv={"Trans_x":xyz[0], "Trans_y":xyz[1], "Trans_z":xyz[2]}
	# 	for obj in 	all_alignables(self.gui.document):
	# 		alignObject(obj, conv, self.gui.report)
	# 		self.gui.update_all(object=obj)		
	# 	self.gui.document.newElement(fedpts)
	# 	self.gui.update_all(object=fedpts, event="Create")
	# 
	# 					
	# def manualAlign(self, event=None):
	# 	obj = self.gui.objecttree.GetPyData(self.gui.contextMenuSelect[0])
	# 	d = self.gui.askParam(parlist)
	# 	if not d:
	# 		return
	# 	conv = {}
	# 	for d in parlist:
	# 		conv[d["Name"]]=d["Value"]
	# 	alignObject(obj, conv, self.gui.report)
	# 	rprs = obj.getTypeRef("ReferencePoint")
	# 	for rp in rprs:
	# 		self.gui.update_all(object=rp, event="Delete")
	# 	self.report("Aligned.")
	# 	self.gui.update_object(obj)		
