#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2008-06-20.

# Copyright (C) 2008 Graham I Cummins
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


from mien.math.array import *

def a2hot(a):
	a=a*100
	r=255.0/(1.0 + exp(-1*(a-50)/2.0))
	g=255.0*exp(-.5*(((a-45)/10)**2))+r*exp(-.4*(100-a))
	b=255.0*exp(-.5*(((a-20)/10)**2))+r*exp(-.4*(100-a))
	a=concatenate([r, g, b],2)
	a=a.astype(uint8)
	return a

def linterp(fr, to, vals, rmin, rmax):
	vals = vals - rmin
	vals = vals/(rmax-rmin)
	out = fr + (to - fr)*vals
	return out
	
def a2rgb(a):
	a=a*400
	r = zeros_like(a)
	g = zeros_like(a)
	b = zeros_like(a)
	bmask = logical_and(a<=100, a>0)
	b[bmask] = linterp(30, 255, a[bmask], 0, 100)
	bgmask = logical_and(a>100, a<=200)
	b[bgmask] = linterp(255, 0, a[bgmask], 100, 200)
	g[bgmask] = linterp(0, 255, a[bgmask], 100, 200)
	grmask = logical_and(a>200, a<=300)
	g[grmask] = linterp(255, 0, a[grmask], 200, 300)
	r[grmask] = linterp(0, 255, a[grmask], 200, 300)
	rwmask = a>300
	r[rwmask] = 255
	v = linterp(0, 255, a[rwmask], 300, 400)
	g[rwmask] = v
	b[rwmask] = v
	a=concatenate([r, g, b],2)
	a=a.astype(uint8)
	return a
	
	

pcolorfunctions={"hot":a2hot,
				 "rgb":a2rgb}

def pcolorImage(a, crange=None, cs='hot'):
	a=a.astype(float64)
	if not crange:
		crange=(a.min(), a.max())
	a=a-crange[0]
	a=a/(crange[1]-crange[0])
	return pcolorfunctions[cs](a)	
	
def image_to_array(image, BandW=-1):
	d=image.GetData()
	s=image.GetSize()	
	a=fromstring(d, uint8)
	a=reshape(a, (s[1], s[0], 3))
	a=transpose(a, (1,0,2))
	if BandW==-1:
		BandW=all(ravel(a[:,:,0]==a[:,:,1])) and all(ravel(a[:,:,1]==a[:,:,2]))
	if BandW:
		a=reshape(a[:,:,0], (a.shape[0], a.shape[1], 1, 1))
	else:
		a=reshape(a, (a.shape[0], a.shape[1], 3, 1))
	return a

def images_to_stack(ims):
	a=[image_to_array(ims[0])]
	BandW= a[0].shape[2]==1
	for im in ims[1:]:
		na=image_to_array(im, BandW)
		a.append(na)
	if len(a)==1:
		a=a[0]
	else:
		a=concatenate(a,3)
	return a

def array_to_image(a, crange=None, pcolor=False, wx=None):	
	if len(a.shape)==2:
		a=reshape(a, (a.shape[0], a.shape[1], 1, 1))
	if len(a.shape)==3:
		a=reshape(a, (a.shape[0], a.shape[1], a.shape[2], 1))
	if pcolor or crange or a.dtype!=uint8:
		if pcolor and a.shape[2]==1:
			if not pcolorfunctions.has_key(pcolor):
				pcolor='hot'
			a=pcolorImage(a, crange, pcolor)
		else:
			if crange:
				minval = min(crange)
				maxval = max(crange)
			else:
				minval=a.min()
				maxval=a.max()
			if minval==maxval:
				a=ones(a.shape)*128
			else:	
				a=a-minval
				a=255*a.astype('d')/(maxval-minval)
		a=where(a>255, ones(a.shape)*255, a)
		a=where(a<0, zeros(a.shape), a)
		a=a.astype(uint8)	
	if a.shape[2]==1:
		a=concatenate([a, a, a],2)
	if not wx:
		return a
	a=transpose(a, (1,0,2,3))
	imgs=[]
	for i in range(a.shape[3]):
		img=wx.EmptyImage(a.shape[1], a.shape[0])
		img.SetData(a[:,:,:,i].tostring())
		imgs.append(img)
	if len(imgs)==1:
		return imgs[0]
	return imgs


