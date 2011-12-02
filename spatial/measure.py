#!/usr/bin/env python
# encoding: utf-8
#Created by Graham Cummins on 2007-07-19.

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
from math import pi

def showStats(doc, elems=[]):
	elems=[doc.getInstance(e) for e in elems]
	cells = [c for c in elems if c.__tag__=='Cell']
	fids = [c for c in elems if c.__tag__=='Fiducial']
	fids=[x for x in fids if x.attrib("Style")=='spheres']
	for e in cells:
		s="Cell Morphology Info - "
		i=e.morphInfo()
		for k in i.keys():
			s=s+"%s: %.2f -" % (k, i[k])
		doc.report(s)
	for e in fids:
		p=e.getPoints()
		rads=p[:,3]/2.0
		areas=4*pi*rads**2
		vols=(4/3)*pi*rads**3
		s="Sphere Geometry Info (%i spheres):\n" % (rads.shape[0],)
		s+="Radius: min - %.2f, max - %.2f, mean - %.2f, total - %.2f\n" % (rads.min(), rads.max(), rads.mean(), rads.sum())
		s+="Area: min - %.2f, max - %.2f, mean - %.2f, total - %.2f\n" % (areas.min(), areas.max(), areas.mean(), areas.sum())
		s+="Volume: min - %.2f, max - %.2f, mean - %.2f, total - %.2f\n" % (vols.min(), vols.max(), vols.mean(), vols.sum())
		doc.report(s)