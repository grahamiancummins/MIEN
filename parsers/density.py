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

from mien.math.array import nonzero1d, zeros, Float32, array, reshape
import mien.parsers.nmpml

EDGE=4.2
EXTENT=(100,100,100)
ORIGIN=array((-161.89,-298.07,-131.32))


def writeDensityFile(of, a,  **kwargs):
	thresh=kwargs.get('thresh', .000001)
	norm=kwargs.get('norm', None)
	of.write("%.6g  #Max Density\n" % a.max())
	of.write("0  #Directional tuning (meaningless)\n")
	if norm:
		a=a*norm*(1.0/a.max())
	if thresh:
		nz=nonzero1d(a>thresh*a.max())
		#print nz[0].min(), nz[0].max()
		#print nz[1].min(), nz[1].max()
		#print nz[2].min(), nz[2].max()
		xr=range(nz[0].min(), nz[0].max())
		yr=range(nz[1].min(), nz[1].max())
		zr=range(nz[2].min(), nz[2].max())
	else:
		size=a.shape
		xr=range(size[0])
		yr=range(size[1])
		zr=range(size[2])
	for x in xr:
		for y in yr:
			for z in zr:
				v=a[x,y,z]
				of.write("%i %i %i %.6g 0 0\n" % (x,y,z,v))
	of.close()			


def readDens(inf, **kwargs):
	l=inf.readlines()	
	if len(l)==1000002:
		l=array([float(line.split()[3]) for line in l[2:]])	
		l=reshape(l, (100,100,100))
	else:
		v=array([float(line.split()[3]) for line in l[2:]])	
		ind=array([map(int, line.split()[:3]) for line in l[2:]])
		l=zeros((ind[:,0].max()+1, ind[:,1].max()+1, ind[:,2].max()+1), Float32)
		for i in range(v.shape[0]):
			l[ind[i,0],ind[i,1], ind[i,2]]=v[i]
	
	mv = l.max()	
	l/=mv
	o = mien.parsers.nmpml.createElement("SpatialField", {"Origin":ORIGIN.tolist(), "Edge":(EDGE,EDGE,EDGE),
			"Vertical":(0.0,1.0,0.0), "Depth":(0.0,0.0,-1.0), "MaxValue":mv,
			"mindensity":.0001, "maxdensity":.1})
	n = mien.parsers.nmpml.blankDocument()
	n.newElement(o)
	d=o.getData()
	d.datinit(l)
	return n

filetypes={}
filetypes['density']={'notes':'Format for storing averaged anatomical information',
					'read':readDens,
					'write':writeDensityFile,
					'data type':'numerical',
					'elements': ["array"],
					'extensions':['.density']}


			

