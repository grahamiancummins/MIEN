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

from mien.tools.remoteeval import EClient, NCPUS
from sys import argv, exit
import os, socket, signal, threading


addr=argv[1]

if not addr[0] in ['123456789']:
	addr=socket.gethostbyname(addr)
print addr


port = int(argv[2])

print NCPUS

def run():
	c=EClient(addr, port)
	c.run()
	print 'done'

if NCPUS>1:
	signal.signal(signal.SIGCHLD, signal.SIG_IGN)
	master = True
	for i in range(NCPUS-1):
		if master:
			print 'forking'
			pid=os.fork()
			if not pid:
				master = False

# if NCPUS>1:
# 	for i in range(NCPUS-1):
# 		t = threading.Thread(target=run, args=())
# 		t.setDaemon(True)
# 		t.start()

run()
exit()





