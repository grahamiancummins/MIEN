#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2009-05-20.

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

import numpy as N

def setDensityLimits(doc, elems=[], mindens = 0.0001, maxdens=0.1, mode="relative"):
	'''Set the mindens and maxdensity attributes on SpatialField elements (this effects the way these are displayed in 3D views). In "absolute" mode, set them to the indicated values. In "relative" mode, set them to the indicated fraction of the maximum density value.
SWITCHVALUES(mode)=["absolute", "relative"]	
	'''
	for e in elems:
		el = doc.getInstance(e)
		if not el.__tag__=="SpatialField":
			continue
		print(el.upath())
		if mode=='absolute':
			mind=mindens
			maxd=maxdens
		else:
			mv = el.getData().getData().max()
			mind = mv*mindens
			maxv=mv*maxdens
		el.setAttrib("mindensity", mind)
		el.setAttrib("maxdensity", maxd)