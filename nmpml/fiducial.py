#!/usr/local/bin/python

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
from mien.nmpml.pointcontainer import PointContainer

class Fiducial(PointContainer):
	'''Data structure representing fiducial marks
members:
	points (Nx3or4 array of floats) : the fiducial data.

attributes:	
    Description (Optional): meaning of the line (or point). Not a
	              unique ID (many fiducials in the same network
				  might have the same description.
	ReferencePoint: (Optional) reference to a ReferencePoint object
	Style : A drawing instruction. May be "points" or
	        "line" or "spheres".
'''
	_allowedChildren =["Point", "Comments", "ElementReference"]
	_requiredAttributes = ["Name"]
	_specialAttributes = ["Style"]

	def __init__(self, node, container=None):
		PointContainer.__init__(self, node, container)
		if not self.attributes.has_key("Style"):
			self.attributes["Style"]="points"
			

ELEMENTS= {"Fiducial":Fiducial}
