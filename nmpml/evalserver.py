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
## start, stop, batch, eval

from mien.nmpml.basic_tools import NmpmlObject
from mien.tools.remoteeval import EServer, ADDR, startClients, startClient
import os, sys

class Distributer(NmpmlObject):
	'''Class for specifying a socket server that queues jobs
	for execution by remote clients
	
	The Distributer may take chilld objects of String type. These should be the addresses or names of machines that will run computation clients. If present, the Distributer will start these clients automatically after starting the server. For non-local clients the calling account must have automatically authenticating ssh access to the client machines.

	attributes:

	Port : the port for the server to run on

	Requeue: Should the server requeue jobs (good for fast jobs that may hang,
	         bad for very long jobs)
	'''
	_requiredAttributes = ["Name", "Port"]
	_specialAttributes = ["Requeue"]
	_allowedChildren = ["String", "Comments"]

	def __init__(self, node, container=None):
		NmpmlObject.__init__(self, node, container)
		self.server=None

	def Id(self):
		return (ADDR, int(self.attrib('Port')))

	def start(self):
		if not self.server:
			doc=self.xpath(1)[0]
			self.server=EServer(doc, int(self.attrib('Port')), self.attrib("Requeue"))
		self.server.start()
		clients = self.getElements('String')
		clients=[s.getValue() for s in clients]
		#startClients(self.server, clients) 
		#for cl in clients:
		#	print cl
		#	startClient(self.server, cl) 

	def stop(self):
		if self.server:
			self.server.stop()
			self.server.sever()
			self.server=None
			
	def busy(self):
		return self.server.busy()

	def eval(self, path, meth, args):
		#if not self.server:
		#	self.start()
		return self.server.eval(path, meth, args)	
		

	def batch(self, path, meth, args):
		if not self.server:
			self.start()
		return 	self.server.batch(path, meth, args)	
		self.stop()	


ELEMENTS = {'Distributer':Distributer}
