#!/usr/bin/env python

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

import mien.image.modules as modules
reload(modules)

def makeCallback(smod, fn):
	def func(event):
		smod.autoWrapper(fn)
		return
	return func

class IVmod:
	def __init__(self, master):
		self.master = master

	def makeMenus(self):
		self.master.refreshMenu("Extensions", self.menu("UI_"))
		funcs={}
		for fn in modules.FUNCTIONS.keys():
			f=modules.FUNCTIONS[fn]
			if f.__module__=='gicImage.modules':
				continue
			mod=f.__module__.split('.')[-1]
			if not funcs.has_key(mod):
				funcs[mod]={}
			funcs[mod][fn]=makeCallback(self, fn)
		for k in funcs.keys():
			self.master.refreshMenu(k, funcs[k])
		self.chan_ids = []
		
	def menu(self, filter):
		d = {}
		for k in dir(self):
			if k.startswith(filter):
				d[k[3:]] = getattr(self, k)
		return(d)

	def autoWrapper(self, fn):
		arglist, defaults=modules.ARGUMENTS[fn]
		if defaults==None:
			defaults=[]
		nnd=len(arglist)-len(defaults)
		d=[]
		for i, arg in enumerate(arglist):
			e={"Name":arg,
			   "Type":str}
			if i>=nnd:
				e['Value']=repr(defaults[i-nnd])
			d.append(e)
		if d:	
			l=self.master.askParam(d)
			if not l:
				return {}
			args={}
			for i, arg in enumerate(arglist):
				try:
					val=eval(l[i])
				except:
					val=l[i]
				args[arg]=val
		else:
			args={}
		func=modules.FUNCTIONS[fn]
		images=self.master.getData()
		out=func(images, **args)
		self.master.storeResponse(out)
		self.master.report("Completed %s" % fn)

	def UI_test(self, event):
		self.master.report("Test1 OK")


	def UI_ReloadTools(self, event):
		self.master.bounce()


