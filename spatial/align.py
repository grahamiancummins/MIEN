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

'''This module provides alignment and scaling functions for use in spatial model tool chains and the CellViewer "spatial" extension menu. All of these functions expect the first argument, doc, to be an nmpml document instance. Most of them also expect the second, elems, to be a list of strings a list of strings. These strings are upaths in doc that reference spatial objects (in general, these are instances of subclasses of PointContainer, or Cell instances.)'''

from mien.spatial.alignment import alignObject, array, eucd

		
def manualAlign(doc, elems=[], trans_x=0.0, trans_y=0.0, trans_z=0.0, rot_x=0.0, rot_y=0.0, rot_z=0.0, scale_x=1.0, scale_y=1.0, scale_z=1.0, scale_d=1.0, order='Trans,Rot,Scale'):
	'''Apply the spatial transformation specified by the various trans, rot, and scale arguments to all the elements specified by upaths in the list "elems". The parameter "order" determines the order in which the translation, rotation, and scaling transforms are applied.'''
	spTrans={'Trans_x':trans_x,'Trans_y':trans_y, 'Trans_z':trans_z,
	 	'Rot_x':rot_x, 'Rot_y':rot_y, 'Rot_z':rot_z, 
		'Scale_x':scale_x, 'Scale_y':scale_y, 'Scale_z':scale_z, 'Scale_d':scale_d,
		'Order':order}
	for on in elems:
		obj=doc.getInstance(on)
		alignObject(obj, spTrans)

def scaleXYZ(doc, elems=[], factor=1.5):
	'''Scale all X Y and Z (but not D) dimensions by factor'''
	spTrans={'Scale_x':factor, 'Scale_y':factor, 'Scale_z':factor}
	for on in elems:
		obj=doc.getInstance(on)
		alignObject(obj, spTrans)
		
# 		
# ['Spatial',"Align Points by Translation", cv.coRegPointsTrans],
# ['Spatial',"Align Points by Rot/Scale", cv.coRegPointsRotScale],
# ['Spatial',"Co-register First Branch", cv.alignFirstBranch],
# ['Spatial',"Set Zero", cv.setZero],
# ['Spatial',"Distance Between Points", cv.ptDist],
# ['Spatial',"Scale Selected Diameters", cv.scaleSelDia],
# ['Spatial',"Set Selected Diameters", self.setSelDia],
# ['Spatial',"Make Sphere", self.makeSoma],
# 		

def coRegPointsTrans(doc, elems=[], point1=[0,0,0], point2=[0,0,0]):
	'''Apply a translation to all the elements in "elems" such that point1 is moved to the location of point2 (all points in elems are shifted by point2-point1)'''
	objl = [doc.getInstance(p) for p in elems]
	pt=array(point2)-array(point1)
	conv = 	{'Trans_x':pt[0],
			 'Trans_y':pt[1],
			 'Trans_z':pt[2]}
	for obj in 	objl:
		print obj, conv
		alignObject(obj, conv)


def coRegPointsRotScale(doc, elems=[], point1=[0,0,0], point2=[0,0,0]):
	'''Apply a rotation and scaling to the elements in elems such that point1 is moved to the location of point2. this is accomplished by first rotating such that the vectors point1 and point2 are colinear, and then scaling by ||point2||/||point1||. Scaling applied by this function does not scale diameters of 4D points. The scale factor used is printed and returned, so that it can be passed to "scaleDiameter" if needed.'''
	#FIXME
	for d in parlist:
		conv[d["Name"]]=d["Value"]
	for obj in 	objl:
		alignObject(obj, conv, cv.report)
		if cv.xm:	
			cv.update_all(object=obj)		
	cv.addAll()

def ptDist(doc, point1=[0,0,0], point2=[0,0,0]):
	'''print and return the euclidian distance between point1 and point2'''
	d=eucd(array(point1), array(point2))
	print "Distance: %.4f" % (d,)
	return d

def setZero(doc, elems=[], point1=[0,0,0]):
	'''Translate the selected objects so that pont1 has coordinates [0,0,0] in the new system. Equivalent to coRegPointsTrans if the argument point2 is [0,0,0]'''
	objl = [doc.getInstance(p) for p in elems]
	conv = 	{'Trans_x':-1*point1[0],
			 'Trans_y':-1*point1[1],
			 'Trans_z':-1*point1[2]}
	for obj in objl:
		alignObject(obj, conv)
		
# 
# def alignFirstBranch(cv, event=None):
# 	cell=cv.getCell()
# 	objl=cv.document.getElements("Cell")
# 	points = []
# 	for f in cv.document.getElements("Fiducial"):
# 		if f.point_labels:
# 			points.append(f)
# 		else:
# 			objl.append(f)
# 	if not points:
# 		cv.report("Non labelod fiducials")
# 		return
# 	fedpts=points[0]
# 	point1=points[0].getNamedPoint("FIRST_BRANCH_AFFERENT")
# 	if point1==None:
# 		l = fedpts.point_labels
# 		d=cv.askUsr("First Branch Name?", fedpts.point_labels.values())
# 		if not d:
# 			cv.report("No Alignment!")
# 			return
# 		point1 = fedpts.getNamedPoint(d)
# 	point2 = cell.getSection(cell.root()).points[-1,:3]
# 	cv.report("First Branch was %s" % str(point2))
# 	xyz = point1[:3] - point2[:3]
# 	conv={"Trans_x":xyz[0], "Trans_y":xyz[1], "Trans_z":xyz[2]}
# 	for obj in 	objl:
# 		alignObject(obj, conv, cv.report)
# 		if cv.xm:
# 			cv.update_all(object=obj)		
# 	cv.addAll()
# 
def scaleDiameter(doc, elems=[], value=1.0):
	'''Scale the diameters of all 4D points in elems by value'''
	objl = [doc.getInstance(p) for p in elems]
	conv = 	{'Scale_d':value}
	for obj in objl:
		alignObject(obj, conv)

def setDiameter(doc, sections=[], value=4.0):
	'''Set the value of the diameter for all points in the selected sections to be value.'''
	objl = [doc.getInstance(p) for p in sections]
	conts=[]
	for s in objl:
		if not s.container in conts:
			conts.append(s.container)
		s.points[:,3]=value
	print "Set diam in %i sections" % len(objl)
	for c in conts:
		c.refresh()

# def makeSoma(cv, event=None):
# 	cell, sec, loc, name=cv._foundLastPoint[0]
# 	d = cv.askParam([{"Name":"Radius",
# 						"Value":27.5}])
# 	if not d:
# 		return
# 	rad=d[0]
# 	sec=sec=cell._sections[sec]
# 	ind = sec.ptAtRel(loc)
# 	pathl = cumsum(eucd(sec.points, shift(sec.points, 1)))
# 	dist=abs(pathl-pathl[ind])
# 	for i, x in enumerate(dist):
# 		if x>=rad:
# 			continue
# 		y=sqrt(rad**2-x**2)
# 		sec.points[i,3]=2*y
# 	cv.update_all(object=cell)
	
