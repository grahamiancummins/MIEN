#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2008-05-02.

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

from mien.tools.identifiers import *
import mien.xml.html2dict as h2d
import urllib, tempfile, tarfile

PREFNAME="UpadteManager"

PKGNAME=re.compile("\w+_(\d+)_([^.]+)\.tgz$")

def getAllExtensionDirs():
	ed=getExtensionDirs()
	led=os.path.join(getHomeDir(), 'mienblocks')
	if not led in ed:
		ed.insert(0, led)
	return ed

def del_tree(d):
    for name in os.listdir(d):
        path = os.path.join(d, name)
        if os.path.isdir(path):
            del_tree(path)
        else:
            os.unlink(path)
    os.rmdir(d)

def getAllProjects():
	p=[('core',  getMienDir())]
	b=findAllBlocks()
	k=b.keys()
	k.sort()
	for key in k:
		p.append((key, b[key]))
	return p

def haveSvn():
	svnc=[]
	check=os.popen('svn --version').read()
	if not check or "not found" in check:
		return None
	for p in getAllProjects():			
		try:
			vs=os.popen('svn info %s' % p[1]).read()
			m=SVNREV.search(vs)
			if m:
				svnc.append(p[0])
		except:
			pass
	return svnc
	
def haveApt():
	if not DEB_PORTS.has_key(getPlatform()):
		return False
	check=os.popen('apt-get').read()	
	if not check or "not found" in check:
		return False
	return True
	

def defaultPrefs():
	p={}
	p['BlockInstall']=getAllExtensionDirs()[-1]
	p['Rev']='dev'
	p['Repository']="http://mien.msu.montana.edu/repository"
	p['Warnings']='on'
	return p
	

def getPrefs():
	z=loadPrefs(PREFNAME)
	if not z:
		z=defaultPrefs()
		savePrefs(PREFNAME, z)
	return z	
	
	
def revinfo(fl):
	arch={}
	avl={}
	mv=0
	for fn in fl:
		m=PKGNAME.match(fn)
		if m:
			v, a = m.groups()
			v=int(v)
			if v>mv:
				mv=v
			if v>avl.get(a, -1):
				arch[a]=fn
				avl[a]=v
	return (mv, arch)
	
def getPackageInfo(url):
	s=h2d.url2object(url)
	deps=[]
	desc=" "
	links=s.getElements('a')
	files=[]
	for l in links:
		targ=l.attrib('href') or " "
		if targ=='DEPENDANCIES':
			try:
				deps=urllib.urlopen(url+'/DEPENDANCIES').read()
				deps=eval(deps)
			except:
				deps="FAILED"
		elif targ=='DESCRIPTION':
			try:
				desc=urllib.urlopen(url+'/DESCRIPTION').read()
			except:
				pass
		elif targ.endswith('.tgz'):
			files.append(targ)
	ri=revinfo(files)		
	return (url, ri[0], desc, ri[1], deps)	
	
def checkRepo():
	p=getPrefs()
	rep=p['Repository']+'/'+p['Rev']
	s=h2d.url2object(rep)
	links=s.getElements('a')
	pkgs={}
	for l in links:
		if l.cdata.strip().endswith('/'):
			targ=l.attrib('href')
			n=targ.rstrip('/')
			url=rep+'/'+targ
			pkgs[n]=getPackageInfo(url)
	return pkgs			

	
def getStatus(rv):
	if rv=='nocheck':
		rv={}	
	elif not rv:
		rv=checkRepo()
	lv=getVersions()
	status=[]
	local=[]
	for p in lv:
		pn, plv = p
		local.append(pn)
		prv = rv.get(pn)
		if prv:
			prv=prv[1]
		else:
			prv=-1
		status.append((pn, plv, prv))
	keys=rv.keys()
	keys=set(keys)-set(local)
	keys=list(keys)
	keys.sort()
	for k in keys:
		status.append((k, -1, rv[k][1]))
	return status
		
	
def printStatus(rv=None):
	st=getStatus(rv)
	for p in st:
		if p[2]==-1:
			print "%s: Not in repository" % (p[0])
		elif p[1]==-1:
			print "%s: Not Installed" % (p[0])
		elif p[2]>p[1]:
			print "%s: Can update. (local %i, latest %i)" % p
		elif p[2]==p[1]:
			print "%s: Up to date (%i)" % (p[0], p[1])
		else:
			print "%s: Bleeding Edge. (local %i, repository %i)" % p
	
def needsUpdate(rv=None):
	st=getStatus(rv)
	upd=[]
	for p in st:
		if p[2]>p[1] and p[1]>0:
			upd.append(p[0])
	return upd		
	
def getFromRepo(pkg, rv, dep=False):
	p=getPrefs()	
	if dep:
		rep=p['Repository']+'/dependancies/'+pkg+".tgz"	
	else:		
		archs=rv[pkg][3]
		if archs.has_key('all'):
			fn=archs['all']
		elif archs.has_key(getPlatform()):
			fn=archs[getPlatform()]
		else:
			raise StandardError("this package doesn't support your platform")
		rep=p['Repository']+'/'+p['Rev']+'/'+pkg+"/"+fn	
	rf=urllib.urlopen(rep)
	lfid, lfn = tempfile.mkstemp(".tgz")
	os.write(lfid, rf.read())
	os.close(lfid)
	return lfn	
	
def installtar(tfn, ldir):
	ldir=os.path.split(ldir)[0]
	tfn=tarfile.open(tfn, "r:gz")
	tfn.extractall(ldir)	
	
def update(pkg, rv):
	if pkg=='core':
		ldir=getMienDir()
	else:
		ldir=findAllBlocks()[pkg]
	print "downloading %s" % pkg
	tfn=getFromRepo(pkg, rv)
	print "installing %s" % pkg
	del_tree(ldir)
	installtar(tfn, ldir)
	os.unlink(tfn)
	print "done"
	
def remove(pkg):
	ldir=findAllBlocks()[pkg]
	del_tree(ldir)
	print "deleted block %s" % pkg
	
def checkDeps(pkg, rv):
	archs=rv[pkg][3]
	if not archs.has_key('all') and not archs.has_key(getPlatform()):
		return (3, "No support for your platform")
	if not rv[pkg][4]:
		return (0, "No dependancies")
	elif rv[pkg][4]=='FAILED':
		return (1, "Dependancy information can't be downloaded. Hope for the best?")
	else:
		deps=rv[pkg][4]
		try:
			for d in deps:
				exec("import %s" % (d[0],))
		except:
			return (2, "Package has unmet dependancies", deps)
		return (0, "All dependancies check out")


def listRepDeps():
	p=getPrefs()
	rep=p['Repository']+'/dependancies/'
	s=h2d.url2object(rep)
	deps=[]
	links=s.getElements('a')
	for l in links:
		targ=l.attrib('href') or " "
		if targ.endswith('.tgz'):
			deps.append(targ[:-4])
	return deps
	
def installRepDep(pn):
	p=getPrefs()
	bdp=p['BlockInstall']
	if 'site-packages' in bdp:
		dd=bdp.split('site-packages')[0]+'site-packages'
	else:
		if not os.path.isdir(bdp):
			os.mkdir(bdp)
		dd=os.path.join(bdp, 'dependancies')	
		if not os.path.isdir(dd):
			os.mkdir(dd)
	ldir=os.path.join(dd, pn)		
	print "downloading %s" % pn
	tfn=getFromRepo(pn, {}, True)
	print "installing %s" % pn
	installtar(tfn, ldir)
	os.unlink(tfn)
	print "done"
	

def notInstalled(rv):
	st=getStatus(rv)
	upd=[]
	for p in st:
		if p[1]<0:
			upd.append(p[0])
	return upd

def install(pkg, rv, dchf=None):
	dc=checkDeps(pkg, rv)
	if dc[0] and dchf:
		c=dchf(dc)
		if c:
			return
	elif dc[0]:
		print "%s: dependancy check failed and no handler is present. Will install, but package may not work"
	bdp=getPrefs()['BlockInstall']
	if not os.path.isdir(bdp):
		os.mkdir(bdp)
	if not os.path.isdir(os.path.join(bdp, pkg)):
		os.mkdir(os.path.join(bdp, pkg))
	open(os.path.join(bdp, pkg, '__init__.py'), 'w'). write(' ')	
	update(pkg, rv)
	
def update_all(rv=None):
	if not rv:
		p=getPrefs()
		rep=p['Repository']+'/'+p['Rev']
		print "checking repository %s"  % (rep)
		rv=checkRepo()
	pkgs= needsUpdate(rv)	
	print "%i packages need updates" % (len(pkgs),)
	for pkg in pkgs:
		print "updating %s" % pkg
		update(pkg, rv)
	
	
APT_MESSAGE='''You seem to be on a linux system using the Debian Advanced Package Tool. You can use apt-get to install and maintain mien packages. This method does not provide access to development snapshot packages, but it does provide much nicer handling of 3rd party dependancies. Go to http://mien.sourceforge.net/docs/apt.html for more information'''	

def SVN_MESSAGE(svn):
	s="The following packages appear to be under subversion version control:\n"
	for p in svn:
		s+="   %s\n" % p
	s+="You should update these packages using 'svn up', not using the mien packaging system"
	return s 			


preferenceInfo=[				
			{"Name":"BlockInstall", 
			'Type':'List',
			'Value':getAllExtensionDirs()},
			{"Name":"Rev", 
			'Type':'List',
			'Value':['stable', 'dev']},
			{"Name":"Warnings", 
			'Type':'List',
			'Value':['on', 'off']},
			{"Name":'Repository', 
			'Type':'Prompt',
			"Value":["http://mien.msu.montana.edu/repository"]}
			
		]			
			
class CLI(object):
	def __init__(self):
		self.rv=None
		self.depth=0
		self.deplist=None
		self.prefs=getPrefs()
		if haveApt():
			print "*****************"
			print APT_MESSAGE
			print "*****************"
		svn=haveSvn()
		if svn:
			print "*****************"
			print SVN_MESSAGE(svn)
			print "*****************"		
		self.commands=[
			('p','(P)rint package status',self.show),
			('c', '(C)onfigure your settings',self.conf),
			('u', '(U)pdate a package',self.up),
			('a', 'Update (A)ll out of date packages', self.up_all),
			('d', 'Fetch (D)ependancies', self.get_deps),
			('r', '(R)emove a package',self.kill),
			('i', '(I)nstall a package', self.add)]
		self.loop(self.commands)
	
	def loop(self, com):
		self.depth+=1
		while True:
			print "*****************"
			print "Update Manager CLI"
			print "Available Actions:"
			print "*****************"
			for c in com:
				print "%s : %s" % (c[0], c[1])
			if self.depth>1:
				print "q : (Q)uit (return to previous menu)"
			else:
				print "q : (Q)uit"
			act=raw_input(" > ")
			act=act.lower().strip()
			if act=='q':
				break
			for c in com:
				if act==c[0]:
					c[2]()
					break
			else:
				print "Unknown action selected"
		self.depth-=1
	
	def getrv(self):
		if not self.rv:
			print "connecting to the repository ..."
			self.rv=checkRepo()
			print "done"
		return self.rv
	
	def show(self):
		printStatus(self.getrv())
		
	def getFromList(self, l):
		for i, v in enumerate(l):
			print "%i : %s" % (i,v)
		r=raw_input("Select entry by number > ")
		try:
			r=l[int(r)]
		except:
			print "invalid selection."
			r=""
		return r
		
	def changePref(self, k):
		print "Editing preference %s (currently %s) " % (k, repr(self.prefs[k]))
		for d in preferenceInfo:
			if d['Name']==k and d['Type']=='List':
				r=self.getFromList(d['Value'])
				break
		else:
			r=raw_input("New Value : ")
		r=r.strip()	
		if not r:
			print "will not use empty value"
			return
		self.prefs[k]=r
		savePrefs(PREFNAME, self.prefs)
		print "Setting changed"
		
	def cpfactory(self, key):
		def f():
			self.changePref(key)
		return f	
		
	def conf(self):
		p=self.prefs
		k=p.keys()
		k.sort()
		com=[]
		for i, key in enumerate(k):
			z=self.cpfactory(key)
			com.append( ("%i" % i, "Edit Setting: %s = %s " % (key, repr(p[key])), z ) )
		self.loop(com)
		
	def up(self):
		nu=needsUpdate(self.getrv())
		if not nu:
			print "There are no packages that need to be updated"
			return
		print "Choose package to update"	
		pack=self.getFromList(nu)	
		r=pack.strip()	
		if not r:
			print "will not use empty value"
			return
		update(r, self.getrv())
		
	def up_all(self):
		update_all(self.getrv())
		
	def kill(self):
		packs=findAllBlocks().keys()
		packs.sort()
		if not packs:
			print "There are no packages installed"
			return
		print "Choose package to delete"	
		pack=self.getFromList(packs)	
		r=pack.strip()	
		if not r:
			print "will not use empty value"
			return
		remove(r)
		
	def depcheck(self, dc):
		if dc[0]==3:
			print "This package isn't supported on your platform. Aborting"
			return 1
		elif dc[0]==1:
			print "The dependancy information for this package is missing. Installing it and hoping for the best"
			return 0
		print "In order for the package you are installing to work, you will need to install some third party packages to provide dependancies."
		print "Please install the following:"
		for dp in dc[2]:
			print "%s (%s)" % (dp[0], dp[2])
		return 0
			
	def add(self):
		nu=notInstalled(self.getrv())
		if not nu:
			print "There are no new packages to install"
			return
		print "Choose package to install"	
		pack=self.getFromList(nu)	
		r=pack.strip()	
		if not r:
			print "will not use empty value"
			return
		install(r, self.getrv(), self.depcheck)
		
	def get_deps(self):
		if self.deplist==None:
			self.deplist=listRepDeps()
		if not self.deplist:
			print "There are no dependancy packages in the repository"
			return
		print "Choose package to install"	
		pack=self.getFromList(self.deplist)	
		r=pack.strip()	
		if not r:
			print "will not use empty value"
			return
		installRepDep(r)
		
						
			
		
			
	
	
