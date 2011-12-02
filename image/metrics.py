#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2008-07-08.

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

from mien.image.imagetools import *


def _norm(a):
	return a/sqrt((a**2).sum())

def densityStats(doc, image, xmin=0, xmax=-1, ymin=0, ymax=-1):
	dat=getImageData(doc, image)
	dat=dat[xmin:xmax,ymin:ymax,:,:]
	for frame in range(dat.shape[3]):
		for color in range(dat.shape[2]):
			v=dat[:,:,color,frame]
			print("Frame %i, Channel %i: max: %.3G mean %.3G min %.3G std %.3G" % (frame, color, v.max(), v.mean(), v.min(), v.std()))
	
	
def measureAngle(doc, point1, point2, point3):
	'''measures the angle between the line segment point1-point2 and the line segment point2-point3, in degrees'''
	ls1=array(point1)-array(point2)
	ls2=array(point3)-array(point2)
	ls1=_norm(ls1)
	ls2=_norm(ls2)
	a=arccos(dot(ls1, ls2))
	a=180*a/pi
	print a
	
def angleFromHorizontal(doc, point1, point2):
	'''Measures the angle between the horizontal and the line segment defined by two points, in degrees counterclockwise. This is such that fastRotate on the negative of the returned angle will render the line segment horizontal in the resulting image'''
	point3=(point2[0]-5, point2[1])
	measureAngle(doc, point3, point2, point1)