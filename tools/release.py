#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2008-10-14.

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

import os, sys
import mien.tools.repmaint as mrep
import mb_binary.tools.repmaint as brep

WD = '/Users/gic/release/'

brep.EDIR = WD
brep.BDIR=os.path.join(WD, 'mienblocks')
brep.DEBDIR=os.path.join(WD, 'deb')
mrep.EDIR = WD
mrep.MDIR=os.path.join(WD, 'mien')
mrep.DEBDIR=os.path.join(WD, 'deb')

if __name__=='__main__':
	force=False
	stab=None
	if "local" in sys.argv:
		brep.RDIR = WD+"repo"
		mrep.RDIR = WD+"repo"
	if "stable" in sys.argv:
		stab='s'
	elif "dev" in sys.argv:
		stab='d'
	if "force" in sys.argv:
		force=True
	sys.path.insert(0, '.')
	v=mrep.getMien(force)
	if v:
		mrep.package(v, stab)
	else:
		print "mien core is not changed"
	b=brep.getBlocks(force)
	if b:
		for bd in b:
			brep.package(bd[0], bd[1], stab)
	else:
		print "No blocks are changed"


