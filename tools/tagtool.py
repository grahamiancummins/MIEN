#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2008-04-16.

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
from mien.parsers.nmpml import elements
from mien.parsers.fileIO import read as mread
from mien.parsers.fileIO import write as mwrite
import os

extensions=['.nmpml', '.mien']

def alltags(fname):
	doc=mread(fname)
	tags=set([doc.__tag__]+[foo.__tag__ for foo in doc.getElements()])
	return tags


def ffind(arg, dn, files):
	if dn.startswith('.'):
		return
	for f in files:
		if not os.path.splitext(f)[-1] in arg[0]:
			continue
		fullf = os.path.join(dn, f)
		arg[1].append(fullf)

def flist(d, ext=None):
	if not ext:
		ext=extensions
	fl=[]
	os.path.walk(d, ffind, (ext, fl))
	return fl

if __name__=='__main__':
	import sys, os, getopt
	usage='''
		r (recursive)
		f tag (find)
		n (convert top level tag to Nmpml)
		c tag (change - aka replace. Requires f)
	'''
	try:
		options, files = getopt.getopt(sys.argv[1:], "rnf:c:", ["version"])
	except getopt.error:
		print usage
		sys.exit()	
	switches={}
	for o in options:
		switches[o[0].lstrip('-')]=o[1]
	if switches.has_key('r'):
		files=flist(os.getcwd())	
	disp=switches.has_key('d')	
	for fname in files:
		doc=mread(fname)
		if switches.has_key('n'):
			if not doc.__tag__=='Nmpml':
				print "Changing top level tag from %s to Nmpml in %s" % (doc.__tag__, fname)
				doc.__tag__="Nmpml"
				doc.update_refs()
				mwrite(doc, fname)
			continue
		tags=set([doc.__tag__]+[foo.__tag__ for foo in doc.getElements()])
		if switches.has_key('f'):
			if switches['f'] in tags:
				print fname
				if switches.has_key('c'):
					print "Replacing tag"
					els=doc.getElements(switches['f'])
					for e in els:
						e.__tag__=switches['c']
					doc.update_refs()
					mwrite(doc, fname)

