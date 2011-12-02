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

from mien.image.imagetools import *

def cropFrames(doc, image, firstFrame=0, lastFrame=100, stride=1, outputPath=""):
	'''Select only the frames in a stack going from firstFrame to lastFrame in steps of stride '''
	dat, h = getImageDataAndHeader(doc, image)
	if stride>1:
		if h.has_key("StackSpacing"):
			h["StackSpacing"]*=stride
	dat=dat[:,:,:,firstFrame:lastFrame+1:stride]
	if not outputPath:
		outputPath=image
	setImageData(dat, outputPath, doc, h)
	
def splitStack(doc, image, delete=False):
	'''Convert an image stack to a sequence of single frame images. If delete is True, also delete the origional stack. Otherwise, it will be unchanged
SWITCHVALUES(delete)=[True, False]'''	
	dat=getImageData(doc, image)
	for i in range(dat.shape[3]):
		d=dat[:,:,:,i:i+1]
		p=image+"_frame%04i" % i
		setImageData(d, p, doc)
	if delete:
		i=doc.getInstance(image)
		i.sever()

def thinStack(doc, image, stride=2, outputPath=''):
	'''remove frames in a stack, keeping 1 frame every stride'''	
	a, h = getImageDataAndHeader(doc, image)
	steps = arange(0, a.shape[3], stride)
	a=a[:,:,:,steps]
	if not outputPath:
		outputPath=image
	h["StackSpacing"]=(h.get("StackSpacing") or 1.0) * stride
	setImageData(a, outputPath, doc, h)
	
	
def extractFrame(doc, image, frame=0, outputPath="frame"):
	'''Copy the specified frame out of the specified stack to a new image '''
	dat=getImageData(doc, image)
	d=dat[:,:,:,frame]
	setImageData(d, outputPath or image, doc)
			
		
def buildStack(doc, images, outputPath="NEW_STACK", delete=True):
	'''Convert a collection of images (or stacks) into a single stack. All images must have the same dimensions. If delete is True, remove the source images. Otherwise, they are unchanged'''
	dat=getImageData(doc, images)
	setImageData(dat, outputPath, doc)
	if delete:
		for image in images:
			i=doc.getInstance(image)
			i.sever()	
			
def invertStackOrder(doc, image, outputPath=''):
	'''Reverses the order of the images in a stack, such that the deepest image is now on top, and the top.'''
	dat, h = getImageDataAndHeader(doc, image)
	dat=dat[:,:,:,arange(dat.shape[3]-1, -1, -1)]
	setImageData(dat, outputPath or image, doc, h)

def frameCompare(doc, imageA, imageB, mode='nand', outputPath='sum'):
	'''Compare the two stacks a frame at a time (stacks must have the same shape) 
SWITCHVALUES(mode)=['add', 'nand', 'and']
'''
	dat1, h = getImageDataAndHeader(doc, imageA)
	dat2, h = getImageDataAndHeader(doc, imageB)
	dat3=zeros_like(dat1)
	for i in range(dat1.shape[3]):
		if mode=='add':
			dat3[:,:,:,i]=dat2[:,:,:,i]+dat1[:,:,:,i]
		else:
			mask=dat2[:,:,:,i]!=0
			if mode=='nand':
				mask=logical_not(mask)
			dat3[:,:,:,i]=where(mask, dat1[:,:,:,i], dat1[:,:,:,i].min())
			
	setImageData(dat3, outputPath or imageA, doc)


def _makeball(xc, yc, r, shape):
	rs=r**2
	def ballf(x,y):
		return (x-xc)**2+(y-yc)**2<=rs 
	return fromfunction(ballf, shape[:2])
		
def _ptimage(d, ps, shape):
	im=_makeball(d[0], d[1], ps, shape).astype(float32)
	im=im.reshape(shape[0], shape[1], 1, 1)
	if len(d)==2:
		im*=255
	elif len(d)==3:
		im*=d[2]
	elif len(d)==4:
		im=concatenate([d[2]*im, d[3]*im, 0.0*im], 2)
	else:
		im=concatenate([d[2]*im, d[3]*im, d[4]*im], 2)
	return im

def fromTimeSeries(doc, upath, ptsize=2.0, width=-1, outputPath='timeseries'):
	'''Convert a timeseries data set to an image stack by plotting the point specified  by the various channels of the series. The function will use x and y as the first two channels. If there is as third, it will be cast to greyscale intensity. If there are more than 3, channels 3, 4, and 5 will be used as RGB values is an a color image. Channels beyond 5 will be discarded. upath specifies the path to the timeseries data. ptsize specifies the radius of the plotted point. width specifies the width of the generated image. Data will be scaled to the range 0,width unless width is -1. In this case the literal values of the data (which must be strictly positive) are used.''' 
	dat=doc.getInstance(upath)
	h={'StackSpacing':dat.fs(), 'SpatialAnchor':(0,0,0)}
	dat=dat.getData().astype(float32)
	minv=dat.min(0)
	maxv=dat.max(0)
	ran=maxv-minv
	frames=[]
	if width==-1:
		width = maxv[0]+ptsize+1
		height = maxv[1]+ptsize+1
	else:
		h['SpatialAnchor']=(minv[0], minv[1], 0)
		ar=ran[1]/ran[0]
		height = ceil(width*ar)
		dat[:,0]=width*(dat[:,0]-minv[0])/ran[0]
		dat[:,1]=height*(dat[:,1]-minv[1])/ran[1]
	if dat.shape[1]>2:
		dat[:,2:]=255*(dat[:,2:]-minv[2:])/ran[2:]
	for i in range(dat.shape[0]):
		frames.append(_ptimage(dat[i,:], ptsize, (width, height)))
	dat=concatenate(frames, 3)
	setImageData(dat, outputPath, doc, h)
	
def toSpatialField(doc, image, mindens=.3, maxdens = 0.8, name="density"):
	'''Convert an image stack to a spatial field representing the image density in 3D. The result is stored in a Data element of type SpatialField at upath.'''
	dat, h = getImageDataAndHeader(doc, image)
	mv = dat.max()
	head = {"Origin":h.get("SpatialAnchor", (0.0,0,0)), 
			"Edge":(h.get("PixelWidth", 1.0),
			  		h.get("PixelHeight", 1.0),
					h.get("StackSpacing", 1.0)), 
			"mindensity":mindens,
			"maxdensity":maxdens,
			"MaxValue":mv,
			"Vertical":h.get("SpatialVertical", (0.0,1.0,0)), 
			"Depth":h.get("SpatialDepth", (0.0,1.0,0))}
	dat = dat.astype(float32).sum(2)/mv
	dat = dat[:,arange(dat.shape[1]-1,-1,-1),:]
	head['Name']=name
	doc.report("%i pixels visible" % ((dat>mindens).sum(),))
	import mien.parsers.nmpml as nmp
	o = nmp.createElement("SpatialField", head)
	doc.newElement(o)
	d=o.getData()
	d.datinit(dat)
	doc.report("Wrote element at %s" % (o.upath(),))
	

def toSpatialField(doc, image, mindens=.3, maxdens = 0.8, name="density"):
	'''Convert an image stack to a spatial field representing the image density in 3D. The result is stored in a Data element of type SpatialField at upath.'''
	dat, h = getImageDataAndHeader(doc, image)
	mv = dat.max()
	head = {"Origin":h.get("SpatialAnchor", (0.0,0,0)), 
			"Edge":(h.get("PixelWidth", 1.0),
			  		h.get("PixelHeight", 1.0),
					h.get("StackSpacing", 1.0)), 
			"mindensity":mindens,
			"maxdensity":maxdens,
			"MaxValue":mv,
			"Vertical":h.get("SpatialVertical", (0.0,1.0,0)), 
			"Depth":h.get("SpatialDepth", (0.0,1.0,0))}
	dat = dat.astype(float32).sum(2)/mv
	dat = dat[:,arange(dat.shape[1]-1,-1,-1),:]
	head['Name']=name
	doc.report("%i pixels visible" % ((dat>mindens).sum(),))
	import mien.parsers.nmpml as nmp
	o = nmp.createElement("SpatialField", head)
	doc.newElement(o)
	d=o.getData()
	d.datinit(dat)
	doc.report("Wrote element at %s" % (o.upath(),))
	

	
def toPointCloud(doc, image, thresh=128, color=0, name="imagepoints"):
	'''Convert the image stack to a collection of points in a point fiducial. Points with value greater than threshold are reported. If the image stack is in color, only one color channel is used for the thresholding'''
	dat, h = getImageDataAndHeader(doc, image)
	mv = dat.max()
	head = {"Name":name,
			"Style":"points"}
	edge = array((h.get("PixelWidth", 1.0),
			  		h.get("PixelHeight", 1.0),
					h.get("StackSpacing", 1.0)));
	dat = dat[:,arange(dat.shape[1]-1,-1,-1),color,:]
	hits = nonzero(dat>thresh)
	vals = dat[hits]
	coords = column_stack(hits).astype(float32)
	coords*=edge
	pts = column_stack([coords, vals])
	head['Name']=name
	doc.report("%i pixels visible" % (pts.shape[0],))
	import mien.parsers.nmpml as nmp
	o = nmp.createElement("Fiducial", head)
	doc.newElement(o)
	d=o.setPoints(pts)
	doc.report("Wrote element at %s" % (o.upath(),))
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	