#!/usr/bin/env python
# encoding: utf-8
#Created by Graham Cummins on 2007-10-08.

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

'''This is a batch script for launching a distributed optimizer and its computation clients as background processes (with this script, the server and clients run on the same machine.) Usage is "optRun.py file.mien", where file.mien is a mien discriptor for the optimizer.'''

''

import sys, os, time, mien, signal
import mien
import mien.parsers.fileIO as io
from mien.tools.remoteeval import EClient, NCPUS, ADDR

signal.signal(signal.SIGCHLD, signal.SIG_IGN)

def runEachClient(port):
	c=EClient(ADDR, port)
	c.run()
	print 'done'

def bindIO(fname):
	dn=file('/dev/null')
	log=file(fname, 'w')
	sys.stdin=dn
	sys.stdout=log
	sys.stderr=log
	
def runClient(port):	
	print "client running"
	sys.stdout.flush()
	if NCPUS>1:
		master = True
		for i in range(NCPUS-1):
			if master:
				print 'forking'
				pid=os.fork()
				if not pid:
					master = False
	runEachClient(port)
	sys.exit()


def getOptFromFile(fname):
	from mien.parsers.nmpml import tagClasses
	ocl=tagClasses()['Optimizer']
	doc=io.read(fname)
	opts=doc.getElements(ocl)
	if not opts:
		return None
	o=opts[0]
	d=o.getElementOrRef('Distributer')
	if not d:
		return None
	return (o, d)
	
def runServe(fname):
	print "server running"
	o=getOptFromFile(fname)[0]
	sys.stdout.flush()
	r=getattr(o, 'run')
	r()
	

def callSelfSilent(fname, port):
	self=sys.argv[0]
	clf=os.path.expanduser('~/mien_optrun_client.log')
	slf=os.path.expanduser('~/mien_optrun_server.log')
	print "Starting server"
	os.system("%s %s serve </dev/null >%s 2>%s &" % (self, fname, slf, slf))
	print "Starting clients"
	os.system("%s %s compute </dev/null >%s 2>%s &" % (self, port, clf, clf))
	print "Done"
	

if __name__=='__main__':
	print "Starting"
	fname=sys.argv[1]
	if len(sys.argv)>2:
		mode=sys.argv[2]
		if mode=='serve':
			runServe(fname)
		elif mode=='compute':
			port=int(fname)
			time.sleep(2)
			runClient(port)
	else:
		o=getOptFromFile(fname)
		if not o:
			print "No distributed optimizer in this file"
			sys.exit()
		d=o[1]
		port=d.attributes["Port"]
		callSelfSilent(fname, port)
		
			
