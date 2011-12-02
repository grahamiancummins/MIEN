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

from mien.optimizers.base import *
from mien.math.array import cumproduct, zeros, concatenate



class ExhaustiveSearch(Optimizer):
	'''Optimizer subclass.
	Search every possible combination allowed by the range and precision of the ParameterSet.'''
			
	def init_local_vars(self):
		self._cached=0
		self._size=self._params.size()
		self._strides=cumproduct(concatenate([[1], self._params._bins])[:-1])
		
	def prerun(self):
		'''make sure _cached=0'''
		self._cached=0
		
	def done(self):
		'''Adds a stop condition for the case where the space has been exhasuted'''
		if self._nunits+self._cached>=self._size:
			return True
		return Optimizer.done(self)
			
	def nthPoint(self, ind):
		'''Return a set of parameters coresponding to the index i in the 1D parameter space (0<=i<self.size()). The index is interpreted first-parameter-first. i=0 is the state where every parameter is set to the botom of its range. i=1 sets the first parameter to one precision step greater than the minimum. i=self._bins[0] sets the second parameter one step up, etc.'''
		indexes=zeros(self._np)
		for i in range(indexes.shape[0]-1, -1, -1):
			l, ind=divmod(ind, self._strides[i])
			indexes[i]=l
		return self._params.indextoPar(indexes)	
			
	def next(self):
		'''Return the next set of parameters to be evaluated. Thin wrapper around nthPoint with thread-safe accounting.''' 
		self.lock.acquire()
		id=self._nunits+self._cached
		self._cached+=1
		self.lock.release()
		return self.nthPoint(id)
				
	def bfrecord(self, c, f):			
		self.lock.acquire()
		try:
			n=self.record(c, f)
			self._nunits+=1
			self._cached-=1
		except:
			self.report('record attempt failed')
			self.lock.release()
			raise
		self.lock.release()	
		
	def evaluate(self, c):
		self.general_eval(c, self.bfrecord)
		
