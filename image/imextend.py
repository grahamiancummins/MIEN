#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2008-06-20.

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


		
import mien.image.modules
import mien.image.widgets
from mien.wx.base import *
import inspect, time
import os, sys, traceback

def makeCallback(smod, fn):
	def func(event):
		smod.autoWrapper(fn)
		return
	return func

def makeFCall(f, arg):
	def foo(x, report=False):
		if report:
			return arg
		return f(arg)
	return foo


class IVExtMod(object):
	def __init__(self, master):
		self.iv=master
		
	def makeMenus(self):
		funcs={'Reload Extensions': self.ReloadExtensions, 
			'Help for Image Tools':self.Help,
			'Delete Images':self.delete}
		for fn in mien.image.modules.FUNCTIONS.keys():
			f=mien.image.modules.FUNCTIONS[fn]
			mod=f.__module__
			if mod.startswith('mien.image'):
				mod=mod.split('.')[-1]
			sfn=fn.split('.')[-1]
			if not funcs.has_key(mod):
				funcs[mod]={}
			funcs[mod][sfn]=makeCallback(self, fn)
		self.iv.refreshMenu("Tools", funcs)
		
	def report(self, s):
		self.iv.report(s)

	def autoWrapper(self, fn):	
		d=mien.image.widgets.getArgChoice(fn, self.iv.document, self.iv)	
		if d:	
			l=self.iv.askParam(d)
			if not l:
				return
			args={}
			for i, di in enumerate(d):
				arg=di['Name']
				if di['Type']==str:	
					try:
						val=eval(l[i])
					except:
						val=l[i]
				else:
					val=l[i]
				args[arg]=val
		else:
			args={}
		func=mien.image.modules.FUNCTIONS[fn]
		sa=time.time()
		func(self.iv.document, **args)
		sp=time.time()-sa
		self.iv.update_all()
		self.report("Completed %s in %.4f sec" % (fn, sp))
		
	def delete(self, event):
		ims=self.iv.getSelected('instances')
		DeleteObject(self.iv, ims)
		self.iv.update_all()
			

	def Help(self, event):
		dlg=mien.image.widgets.FunctionFinder(self.iv, module=mien.image.modules)
		dlg.CenterOnParent()
		val = dlg.ShowModal()
		if val == wx.ID_OK:
			fn=dlg.GetPath()
			dlg.Destroy()
		else:
			dlg.Destroy()
			self.report("Canceled")
			return
		print fn	
		f=mien.image.modules.FUNCTIONS[fn]
		dl=inspect.getsource(f).split(':')[0][4:]
		if f.__doc__:
			dl+="\n\n"+f.__doc__
		self.iv.showText(dl)		

	def ReloadExtensions(self, event=None):
		fl=mien.image.modules.refresh()
		self.makeMenus()
		if fl:
			self.report('Reload generated some errors: %s' % (str(fl),))
		else:
			self.report("Reload complete")
		