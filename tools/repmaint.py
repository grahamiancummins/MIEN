#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2008-05-07.

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

import os, re, sys

RDIR='/var/www/repository'
URL='http://mien.msu.montana.edu/svn/mien/mien'
EDIR='/opt/src/work/'


MDIR=os.path.join(EDIR, 'mien')
DEBDIR=os.path.join(EDIR, 'deb')
sviv=re.compile("Last Changed Rev:\s*(\d+)")

DEB_CONTROL='''
Package: python-mien
Version: 0.0.VERSION
Section: python
Priority: optional
Maintainer: Graham Cummins <gic@cns.montana.edu>
Depends: python (>= 2.6), python-numpy (>=1.0), python-opengl (>= 3.0), python-wxgtk2.8
Recommends: python-profiler
Suggests: ipython
Description: Provides a scientific modeling environment in python
	MIEN includes file format support, visualization, network, and 
	computational tools for approaching scientific modeling and data
	analysis tasks. MIEN is particularly designed for use in neuroscience.
	MIEN also provides a framework for writing general purpose extension
	blocks.
Installed-Size: SIZE
Architecture: all
'''

DEB_PORTS= ['i386', 'ia64', 'amd64']

def movefile(foo, bar):
	open(bar, 'w').write(open(foo).read())
	os.unlink(foo)

def insureDir(d):
	d=d.rstrip('/')
	dirs=[]
	while not os.path.exists(d):
		d, t = os.path.split(d)
		dirs.append(t)
	while dirs:
		d=os.path.join(d, dirs.pop())
		os.mkdir(d)

def getVersion(url):
	vs=os.popen('svn info %s' % url).read()
	m=sviv.search(vs)
	return int(m.group(1))
	
def tarrevnum(fn):
	n=os.path.splitext(fn)[0]
	n=n.split('_')[1]
	try:
		n=int(n)
	except:
		n=-1
	return n	
	
def revsort(a, b):
	return cmp(tarrevnum(a), tarrevnum(b))

def isStable(url):
	vs=os.popen('svn log -r HEAD %s' % url).read()
	for x in vs.split('\n'):
		if x.strip().lower().startswith('stable release:'):
			return True
	return False
		
def getMien(force=False):
	if not os.path.isdir(MDIR):
		os.mkdir(MDIR)
	vf=os.path.join(MDIR, 'VERSION')
	try:
		ov=int(open(vf).read())
	except:
		ov=-1
	nv=getVersion(URL)
	if nv<=ov and not force:
		return None
	os.system('svn export --force %s %s > /dev/null' % (URL, MDIR))
	open(vf, 'w').write("%i\n" % nv)
	return nv	
	

def backup(sd):
	fi=[f for f in os.listdir(sd) if f.endswith('tgz')]
	if not fi:
		return
	fi=fi[0]
	td=os.path.join(RDIR, 'old', 'core')
	insureDir(td)
	movefile(os.path.join(sd, fi), os.path.join(td, fi))
	if len(fi)>4:
		fi.sort(revsort)
		os.unlink(os.path.join(td, fi[0]))
	
def trimdir(d, mn):
	fi=[f for f in os.listdir(d) if f.endswith('tgz')]
	if len(fi)<=mn:
		return	
	fi.sort(revsort)
	print fi
	while(len(fi)>mn):
		f=fi.pop(0)
		os.unlink(os.path.join(d, f))

def deb_build(v):
	insureDir(DEBDIR)
	curdir=os.getcwd()
	os.chdir(DEBDIR)
	if os.path.isdir('./python-mien'):
		os.system('rm -rf ./python-mien')
	os.mkdir('python-mien')
	os.mkdir('python-mien/DEBIAN')
	cs=DEB_CONTROL.replace('VERSION', str(v))
	size=os.popen('du -s %s' % MDIR).read()
	size=size.split()[0]
	cs=cs.replace('SIZE', str(size))
	open('python-mien/DEBIAN/control', 'w').write(cs)
	insureDir("./python-mien/usr/lib/python2.6/dist-packages/")
	insureDir("./python-mien/usr/bin")
	os.system('cp -r %s python-mien/usr/lib/python2.6/dist-packages/' % MDIR)
	os.system('cp python-mien/usr/lib/python2.6/dist-packages/mien/frontends/mien python-mien/usr/bin/')
	os.system('chmod +x python-mien/usr/bin/mien')
	pn='python-mien_0.0.%i_all.deb' % v
	os.system('dpkg -b python-mien %s' % pn)
	os.system('rm -rf ./python-mien')
	os.chdir(curdir)
	return pn

def rebuild_apt_repo():
	dtd=os.path.join(RDIR, 'ubuntu')
	curdir=os.getcwd()
	os.chdir(dtd)
	for arch in DEB_PORTS:
		ad=os.path.join(RDIR, 'ubuntu', 'dists', 'jaunty', 'main', 'binary-%s' % arch)
		insureDir(ad)
		pfn=os.path.join(ad, 'Packages.gz')
		if os.path.exists(pfn):
			os.unlink(pfn)
		print "generating package index %s" % pfn
		os.system('dpkg-scanpackages -a %s pool /dev/null | gzip -9c > %s' % (arch, pfn))
	os.chdir(curdir)	

def apt_update(v):
	pn=deb_build(v)
	dtd=os.path.join(RDIR, 'ubuntu', 'pool')
	insureDir(dtd)
	for f in os.listdir(dtd):
		if f.startswith('python-mien_0.0'):
			os.unlink(os.path.join(dtd, f))
	movefile(os.path.join(DEBDIR, pn), os.path.join(dtd, pn))
	rebuild_apt_repo()
	

	
def package(v, stab=None):
	if stab=='d':
		stable=False
	elif stab=='s':
		stable=True
	else:
		stable = isStable(URL)
	if stable:
		dn='stable'
	else:
		dn='dev'		
	print "packaging mien revision %i (%s)" % (v, dn)
	td=os.path.join(RDIR, dn, 'core')
	insureDir(td)
	fn="mien_%s_all.tgz" % (v)
	cmd='tar -C %s -czf %s mien' % (EDIR, os.path.join(EDIR, fn))
	print cmd
	os.system(cmd)
	print "built tgz"
	movefile(os.path.join(EDIR, fn), os.path.join(td, fn))
	print "checking for moved file: ", os.path.exists(os.path.join(td, fn))
	if stable:
		apt_update(v)
		trimdir(td, 4)	
	else:
		trimdir(td, 1)	
	

if __name__=='__main__':
	force=False
	stab=None
	if "stable" in sys.argv:
		stab='s'
	elif "dev" in sys.argv:
		stab='d'
	if "force" in sys.argv:
		force=True
	v=getMien(force)
	if v:
		package(v, stab)
	else:
		print "mien core is not changed"

	
