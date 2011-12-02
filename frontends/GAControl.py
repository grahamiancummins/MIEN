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
from mien.optimizers.ga import GA
from mien.optimizers.analysis import AccessGA
from mien.optimizers.gui import GAMonitor, GAEditor, GAAnalyzer, wx 
from sys import argv, exit

usage='''
	GAControl.py i|b|r|a|e [directory]
	
	i -> interactive (command line) analysis
	b -> batch (command line) run (resumes previous run)
	r -> gui run monitor
	a -> gui analysis 
	e -> gui editor
'''

try:
	cmd=argv[1]
	if not cmd in ['b', 'i', 'r', 'a', 'e']:
		raise StandardError("command not supported")
except:
	print "usage:"
	print usage
	exit()

try:
	d=argv[2]
except:
	if cmd in ['r', 'b']:
		print "directory argument required for run"
		exit()
	d = None	

if cmd=='r':
	ga=GA('resume', d)
	app = wx.PySimpleApp()
	gam=GAMonitor(None, ga, None)
	gam.Show(True)
	app.MainLoop() 
elif cmd=='a':
	app = wx.PySimpleApp()
	gae=GAAnalyzer(None, d)
	app.MainLoop() 
elif cmd=='e':
	app = wx.PySimpleApp()
	gae=GAEditor(None, d)
	app.MainLoop() 
elif cmd=='b':
	ga=GA('resume', d)
	ga.run()
elif cmd=='i':
	import code
	ga=AccessGA(d)
	from gicMath.sigtools import *
	l=locals()
	l.update(globals())
	code.interact("Interactive Analysis", local=l)
