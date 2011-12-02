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

'''Functions for fiting 1D data with math functions'''

from mien.math.array import *

def regress(dat, fs=1.0, start=0.0, ranal=0):
	'''calculate linear regression for the data in dat. If dat is 2D, it is taken to be Nx2, and to contain the x and y samples in the two columns. If dat is 1D it is taken to be y values sampeled at fixed sampling frequency fs (Hz) starting at x value start (start and fs are ignored for Nx2 dat). 
	ranal is a flag specifying the return value. If it is False (default), the return is a tuple of floats (m, b) specifing the regression line y=mx+b. If ranal is 1, the return is a tuple (m, b, r) where r is the fraction of variance explained by the regression line. If ranal is any other true value, return is (m,b, r**2, tv,rv,l)  where tv is the total variance, rv is the residual variance, and l samples drawn from the regression line for each value in x.'''
	n=float(dat.shape[0])
	if len(dat.shape)==2:
		x=dat[:,0]
		y=dat[:,1]
	else:
		y=dat
		x=start+arange(n).astype(dat.dtype)/fs
	sumxx=(x**2).sum()
	sumyy=(y**2).sum()
	sumxy=(x*y).sum()
	Sxx = sumxx-x.sum()**2/n
	Sxy = sumxy-y.sum()*x.sum()/n
	m =Sxy/Sxx;
	b = (y.sum()-m*x.sum())/n
	if not ranal:
		return (m, b)
	tv=y.var()
	l=x*m+b
	rv=(y-l).var()
	r=1-(rv/tv)
	if ranal==1:
		return (m, b, r)
	return (m, b, r**2, tv, rv, l)
		
