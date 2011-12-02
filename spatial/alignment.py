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
'''provides functions for scaling and alignment.'''
from mien.math.array import *
from mien.nmpml.reference import ReferencePoint

def blankReport(s):
	print s

def all_alignables(doc):
	'''instance (Document) => list
return a list of child objects containing the highest level
alignable children.'''
	align = []
	for e in doc.elements:
		if 'doAlignment' in dir(e):
			align.append(e)
		else:
			l = all_alignables(e)
			align+=l
	return align

def geometricCenter(a):
	'''a (Nx3 array) => array.
return a location array([x,y,z]) specifying the average location of all
3d points in a'''
	return sum(a, 0)/a.shape(0)

def centerOfMass(a):
	'''a (Nx4 array) => array.
return a location array([x,y,z,d]) specifying the average location of all
3d points in a wieghted by the values of d. The d value in the return is the
average d.'''
	pass

def translatePoints(conv, a, diams):
	trans = array([conv.get("Trans_x", 0.0), conv.get("Trans_y", 0.0), conv.get("Trans_z", 0.0)])
	if any(trans):
		trans = resize(trans, a.shape)
		a = a+trans
	return (a, diams)

def scalePoints(conv, a, diams):
	scale = array([conv.get("Scale_x", 1.0), conv.get("Scale_y", 1.0), conv.get("Scale_z", 1.0)])
	if any(scale!=1):
		scale =  resize(scale, a.shape)
		a = a*scale	
	if diams!=None:
		sd = conv.get("Scale_d", 1.0)
		if sd!=1.0:
			diams = diams*sd
	return (a, diams)

def rotatePoints(conv, a, diams):
	rot = array([conv.get("Rot_x", 0.0), conv.get("Rot_y", 0.0), conv.get("Rot_z", 0.0)])
	if any(rot):
		a = rotate3D(a, rot) 
	return (a, diams)	

def alignPoints(a, conv):
	''' array, tuple => array. Used by alignObject'''
	order  = conv.get("Order", ["Trans","Rot","Scale"])
	if type(order)!=type([]):
		order = order.split(",")
	order = map(lambda x : x[0].lower(), order)
	diams = None
	if a.shape[1]==4:
		diams = a[:,3]
		a = a[:,:3]

	actions = {"t":	translatePoints, "r":rotatePoints, "s":scalePoints}
	for se in order:
		a, diams = actions[se](conv, a, diams) 
		
	if diams!=None:
		a = concatenate([a, diams[:, NewAxis]], 1) 
	return a

def alignObject(obj, conv, report=blankReport):
	'''obj(instance), conv(dict), report(funcion=blackReport)
scales and aligns obj according to the instructions in conv.
Knows how to scale align PointContainers, or a anything
with a doAlignment method (a PointContainer with doAlignment
will be aligned according to its method in preference to
the default alignment for PointContainers).

Children listed in .elements will be searched recursively for
alignment methods.

angles are in degrees counterclockwise, scale values are unitless,
and translations are assumed to be in the same units as the objects
points (unit coversion should be handled higher up!).

conv dictionaries are described in model.reference.ReferenceConversion
keys that are not specified are treated as null operations
(1 for Scale, and 0 for translation and rotation)

If the key "Order" is not specified, the default order:
"Trans,Rot,Scale" is used.
'''
	if 'doAlignment' in dir(obj):
		try:
			obj.doAlignment(conv)
			obj.addComment("Scaled by %s" % str(conv))
			report("Aligned %s" % str(obj))
		except AttributeError:
			report("FAILED ALIGNMENT ON  %s" % str(obj))
			raise
	else:		
		report("%s ignored (no doAlignment method)" % str(obj))
		children = obj.elements
		for c in children:
			alignObject(c, conv)

def alignByRP(obj_list, report=blankReport):
	'''obj_list (list) => list
Aligns a list of objects. The last object in the list is used as the
standard to which other elements are aligned. It can be either a
ReferencePoint instance itself, or have a (resolvable)
ReferencePointReference attribute'''
	target=obj_list[-1]
	if target.__tag__=="ReferencePoint":
		targ_rp = target
	else:
		targ_rp = target.getInstance(target.attrib("ReferencePoint"))
	report("aligning to reference: %s" % str(targ_rp))
	for obj in obj_list[:-1]:
		try:
			rp = obj.getInstance(target.attrib("ReferencePoint"))
		except:
			report("%s has no reference. skipping" % str(obj))
			continue
		if rp == targ_rp:
			report("%s already has correct alignment" % str(obj))
			continue
		conv = rp.getConversion(targ_rp)
		if not conv:
			report("%s refernce (%s) has no conversion info for this target . skipping" % (str(obj), str(rp)))
		else:
			try:
				alignObject(obj, conv, report)
				obj.attributes["ReferencePointReference"]= str(targ_rp)
				obj.refresh()
			except:
				report("FAILED ALIGNMENT ON  %s" % str(obj))
				raise

