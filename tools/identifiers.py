#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2008-05-15.

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

import os, sys, re
from distutils.util import get_platform

PLATFORMS=['macosx', 'win32', 'linux-i686', 'linux-ia64', 'linux-x86_64']
DEB_PORTS={'linux-i686':'i386', 'linux-ia64':'ia64', 'linux-x86_64':'amd64'}


SVNREV=re.compile("Last Changed Rev:\s*(\d+)")


def getExtensionDirs():
	EDIR=[]
	sd=[p for p in sys.path if p.endswith('site-packages') or p.endswith('dist-packages')]	
	for p in sd:
		sd=os.path.join(p, 'mienblocks')
		if os.path.isdir(sd):
			EDIR.append(sd)
	ed=os.environ.get('MIEN_EXTENSION_DIR')
	if ed:
		for ede in ed.split(':'):
			if os.path.isdir(ede):
				EDIR.append(ede)
	else:
		ed=os.path.join(getHomeDir(), 'mienblocks')
		if ed and os.path.isdir(ed):
			EDIR.append(ed)
	return EDIR		

def findAllBlocks():
	blocks={}
	for ed in getExtensionDirs():	
		for f in os.listdir(ed):
			if f in ['mb_binary']:
				continue
			fn=os.path.join(ed, f)
			if os.path.isdir(fn) and os.path.exists(os.path.join(fn, '__init__.py')):
				blocks[f]=fn
	return blocks

def getPlatform():
	plat=os.environ.get("MIEN_BINARY_PLATFORM")
	if plat:
		return plat
	plat=get_platform()
	if plat.startswith("macosx"):
		return "macosx"	
	return plat	
	
def getHomeDir():
	h=os.environ.get('HOME')
	if not h:
		print "Warning: HOME environment variable not defined. \nThis is a BAD THING. You should define it. \nFor now, Mien will use the current directory"
		h=os.getcwd()
		os.environ['HOME']=h
	return h

def setConfigFile():	
	cd=os.environ.get('MIEN_CONFIG_DIR')
	if not cd:
		h=getHomeDir()
		cd=os.path.join(h, '.mien')
		os.environ['MIEN_CONFIG_DIR']=cd
	if not os.path.isdir(cd):
		os.mkdir(cd)

def getMienDir():
	sfn= __file__			
	sfn=os.path.split(sfn)[0]
	sfn=os.path.split(sfn)[0]
	return sfn
	
	
def getPrefFile(cn, mode='r'):
	cd=os.environ.get('MIEN_CONFIG_DIR')
	if not cd:
		setConfigFile()
		if not cd:
			return None
	cf=os.path.join(cd,cn)
	if not os.path.isfile(cf):
		file(cf, 'w').write('{}')	
	return file(cf, mode)
			
def loadPrefs(cn):
	cf=getPrefFile(cn)
	if not cf:
		return {}
	try:
		s=cf.read()
		cf.close()
		p=eval(s)
		return p
	except:	
		return None
		
def savePrefs(cn, pd):
	cf=getPrefFile(cn, 'w')
	if cf:
		cf.write(repr(pd))
		cf.close()	
	
def getDirVersion(d):
	v=-1
	vfn=os.path.join(d, 'VERSION')
	if os.path.exists(vfn):
		try:
			v=int(open(vfn).read())
		except:
			pass
	if v<0:		
		try:
			vs=os.popen('svn info %s' % d).read()
			m=SVNREV.search(vs)
			if m:
				v=int(m.group(1))
		except:
			pass
	return v
	
def getVersions():
	v=[]
	v.append(('core', getDirVersion(getMienDir())))
	blocks=findAllBlocks()
	keys=blocks.keys()
	keys.sort()
	for b in keys:
		v.append((b, getDirVersion(blocks[b])))
	return v
