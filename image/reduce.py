#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2009-05-19.

# Copyright (C) 2009 Graham I Cummins
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

from mien.image.imagetools import *

def convertToGreyscale(doc, image, r=1.0, g=1.0, b=1.0, outputPath=""):
	a, h = getImageDataAndHeader(doc, image)
	dt = a.dtype
	if a.shape[2]!=3:
		doc.report("not a color image")
		return
	weight = array([r,g,b])
	a/=weight.sum()
	a*=weight[newaxis,newaxis,:,newaxis]
	a=a.sum(2)
	a=a.reshape([a.shape[0], a.shape[1], 1, a.shape[2]]).astype(dt)
	if not outputPath:
		outputPath=image
	setImageData(a, outputPath, doc, h)
	
def boxDownSample(doc, image, outputPath=""):
	a, h = getImageDataAndHeader(doc, image)
	dt = a.dtype
	if a.shape[0] % 2:
		a=a[:-1,:,:,:]
	if a.shape[1] % 2:
		a=a[:,:-1,:,:]
	out = zeros((a.shape[0]/2, a.shape[1], a.shape[2], a.shape[3]), a.dtype)	
	ev = arange(0, a.shape[0], 2)
	od = arange(1, a.shape[0], 2)
	out = (a[ev,:,:,:]+a[od,:,:,:])/2
	ns = out.shape[1]/2
	out[:,:ns,:,:] = (out[:,ev,:,:]+out[:,od,:,:])/2
	out = out[:,:ns,:,:]
	h['PixelWidth']=h.get("PixelWidth", 1.0)*2
	h['PixelHeight']=h.get("PixelHeight", 1.0)*2
	if not outputPath:
		outputPath=image
	setImageData(out, outputPath, doc, h)	
	
	
def differencingFilter(doc, image, outputPath=""):
	a, h = getImageDataAndHeader(doc, image)	
	lshift = a[:-1,:,:,:] != a[1:,:,:,:]
	ushift = a[:,:-1,:,:] != a[:,1:,:,:]
	dshift = logical_or(lshift[:,1:,:,:], ushift[1:,:,:,:]).astype(uint8)*255
	if not outputPath:
		outputPath=image
	setImageData(dshift, outputPath, doc, h)		
	
	
	