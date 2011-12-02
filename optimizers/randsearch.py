#!/usr/bin/env python
# encoding: utf-8
#Created by Graham Cummins on 2007-08-23.

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

from mien.optimizers.base import *
from mien.math.array import *

class RandomSearch(Optimizer):
	'''This is not an optimizer per se, but uses the same setup and evaluation as an optimizer. This class repeatedly evaluates random points in the parameter space'''
	'''Optimizer subclass.
	Search every possible combination allowed by the range and precision of the ParameterSet.'''
			
	def next(self):
		'''Return a random point''' 
		r=self.random()
		return r
				
	def saferecord(self, c, f):	
		self.lock.acquire()
		try:
			n=self.record(c, f)
			self._nunits+=1			
			if f[0]>0:
				print f
				#self._abort=True
			if not self._nunits % 100:
				print self._nunits
			
			self.lock.release()
		except:
			self.report('record attempt failed')
			self.lock.release()
		
	def evaluate(self, c):
		self.general_eval(c, self.saferecord)
	