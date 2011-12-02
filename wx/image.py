#!/home/gic/bin/python

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
import wx


def get_image_stats(a):
	stats = {}
	stats['max'] = max(ravel(a))
	stats['min'] = min(ravel(a))
	stats['ave'] = sum(ravel(a.astype(Float64)))/len(ravel(a))
	stats['range'] = stats['max'] - stats['min']
	return stats
	
	
def array_to_bytes(a, ran='auto'):
	if ran==None:
		minval=armin(a)
		maxval = armax(a)
	else:
		minval=ran[0]
		maxval = ran[1]
	if minval==maxval:
		a=ones((a.shape[0],a.shape[1], 3))
		ar=(a*128).astype('b')
	else:
		a=a-minval
		a=a.astype('d')/(maxval-minval)
		ar=(a*255).astype('b')
	return ar	

def array_to_image(ar, z=1.0, normalize=None):
	a = ar.copy()
	if normalize:
		a=array_to_bytes(a, normalize)
	if a.dtype.char!='b':	
		a=a.astype('b')	
	if len(a.shape)==2:
		a=concatenate([a[:,:,NewAxis],a[:,:,NewAxis],a[:,:,NewAxis]],2)
	img=wx.EmptyImage(a.shape[0], a.shape[1])
	a=transpose(a, (1,0,2))	
	img.SetData(a.tostring())
	if z!=1.0:
		if type(z) in [int, float]:
			z=(z,z)
		size = (int(size[0]*z[0]), int(size[1]*z[1]))
		img.Rescale(size[0], size[1])	
	return img

def image_to_data(image):
	d=image.GetData()
	s=image.GetSize()	
	a=fromstring(d, UInt8)
	a=reshape(a, (s[1], s[0], 3))
	a=transpose(a, (1,0,2))
	if all(ravel(a[:,:,0]==a[:,:,1])) and all(ravel(a[:,:,1]==a[:,:,2])):
		a=a[:,:,1]
	return a

