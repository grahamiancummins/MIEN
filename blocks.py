#!/usr/bin/env python
# encoding: utf-8

#Created by gic on 2007-04-10.

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

import sys, os, re, inspect, traceback
from  mien.tools.identifiers import getExtensionDirs

EDIR=getExtensionDirs()
for ed in EDIR:
	if not ed in sys.path:
		sys.path.insert(0, ed)
	ddir=os.path.join(ed, 'dependancies')
	if os.path.isdir(ddir) and not ddir in sys.path:
		sys.path.append(ddir)

BLOCKTYPES=['DSP','SPATIAL','DV','CV','ME', 'PARSERS', 'NMPML', 'MECM', 'IMG']

BLOCKS={}
FAILED_LOAD={}
MODULES={}
BLOCKINDEX={}

def clear():
	for k in BLOCKINDEX.keys():
		BLOCKINDEX.pop(k)
	for k in BLOCKS.keys():
		BLOCKS.pop(k)
	for k in FAILED_LOAD.keys():
		FAILED_LOAD.pop(k)
	for k in MODULES.keys():
		MODULES.pop(k)


def getpackage(dn, pn=''):
	m=[]	
	for f in os.listdir(dn):
		if f.startswith('.') or f.startswith('_'):
			continue
		elif f.endswith('.py'):
			m.append(pn+os.path.splitext(f)[0])	
		else:
			fn=os.path.join(dn, f)
			if os.path.isdir(fn) and os.path.exists(os.path.join(fn, '__init__.py')):
				m.extend(getpackage(fn, pn+f+'.'))
	return m			
	
def tryLoad(mn):
	if MODULES.has_key(mn):
		return MODULES[mn]
	elif FAILED_LOAD.has_key(mn):
		return None
	try:
		exec "import %s as mod" % mn
		reload(mod)
		MODULES[mn]=mod
	except:
		print "error loading module %s" % mn
		e= sys.exc_info()
		FAILED_LOAD[mn]=e
		apply(traceback.print_exception, e)
		mod=None
	return mod

switchval=re.compile(r"\s*SWITCHVALUES\((\w+)\)=(.+)")

def getarginfo(fun):
	inf={'switch values':{}}
	ds=fun.__doc__
	if ds:
		ds=ds.split('\n')
		for l in ds:
			sv=switchval.match(l)
			if sv:
				switch, value=sv.groups()
				value=eval(value)
				inf['switch values'][switch]=value
	return inf

def getArguments(FUNCTIONS):
	arguments={}
	for f in FUNCTIONS.keys():
		fun=FUNCTIONS[f]
		args=inspect.getargspec(fun)
		info=getarginfo(fun)
		args=(args[0][1:], args[-1], info)
		arguments[f]=args
	return arguments

def functionIndex(modname):
	fmod=tryLoad(modname)
	if not fmod:
		return {}
	functions={}
	for f in dir(fmod):
		if f.startswith('_'):
			continue
		fun=getattr(fmod, f)
		if inspect.isfunction(fun) and fun.__module__==modname:
			fn=fun.func_name
			ffn="%s.%s" % (modname,fn)
			functions[ffn]=fun
	return functions

def buildIndex():	
	for k in BLOCKTYPES:
		BLOCKINDEX[k]=[]
	if not EDIR:
		return 
	if os.environ.get('MIEN_EXTENSION_DISABLE'):
		print "Extensions Disabled"
		return 
	for ed in EDIR:	
		disabled=[]	
		dfile=os.path.join(ed, 'disabled_blocks.txt')
		if os.path.isfile(dfile):
			disabled=[fn.strip() for fn in file(dfile).readlines()]
		for f in os.listdir(ed):
			if f in disabled:
				print "ignoring disabled block %s" % f
				continue
			fn=os.path.join(ed, f)
			if os.path.isdir(fn) and os.path.exists(os.path.join(fn, '__init__.py')):
				mod=tryLoad(f)
				if mod:
					for modtype in BLOCKTYPES:
						if modtype in dir(mod):
							BLOCKINDEX[modtype].append(mod)
					
def loadBlock(btype):
	block={}
	for mod in BLOCKINDEX[btype]:
		modlist=getattr(mod, btype)
		mn=mod.__name__
		if modlist=='ALL':	
			fn = os.path.split(mod.__file__)[0]
			modlist=getpackage(fn)
		for s in modlist:	
			if type(s) in [tuple, list]:
				mn=mod.__name__+'.'+s[0]
			else:
				mn=mod.__name__+'.'+s
			lmod=tryLoad(mn)
			if not lmod:
				continue
			if type(s) in [tuple, list]:
				objn=s[1]
				obj=getattr(lmod, objn)
				if len(s)>2:
					name=s[2]
				else:
					name=mn+'.'+objn
				block[name]=obj
			elif type(s) in [str, unicode]:
				for lmfn in dir(lmod):
					if lmfn.startswith('_'):
						continue
					fun=getattr(lmod, lmfn)
					if inspect.isfunction(fun) and fun.__module__==lmod.__name__:
						n=lmod.__name__+'.'+lmfn
						block[n]=fun
	BLOCKS[btype]=block

def makeFCall(f, arg):
	def foo(x, report=False):
		if report:
			return arg
		return f(arg)
	return foo
		
def getBlock(id):
	if not BLOCKINDEX:
		buildIndex()
	if not BLOCKS.get(id):
		loadBlock(id)
	return BLOCKS.get(id, {})
	


