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

from mien.math.array import *

class NDGauss:
	'''implements the special case of a single gaussian center in N dimensions with independent variances (diagonal covariance)'''
	def __init__(self, data):
		'''Generates a model from a 2D array. The first index of the array specifies dimensions of the model. The columns of the array indicate samples.'''
		self.means=data.mean(1)
		self.vars=data.var(1)
		

class Gmm:
	'''implements Gausian Mixture models similar to those from the netlib Matlab library.'''
	def __init__(self, dim, ncenters, covar):
		pass
