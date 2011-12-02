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
from mien.parsers.nmpml import forceGetPath, addPath

def voxelDims(im):
	'''im is a Data instance (not an array), or a header dictionary (as generated by im.header()). Return (PixelWidth, PixelHeight, StackSpacing). Provides sensible defaults, and sets the attributes if they are not set (note that if im is a header, the attributtes are set in the header only, not the source image).'''
	if type(im)==dict:
		h=im
	else:
		h=im.header()
	attr=['PixelWidth','PixelHeight', 'StackSpacing']
	if h.get('PixelWidth') and not h.get('PixelHeight'):
		h['PixelHeight']=h['PixelWidth']
	for a in attr:
		if not h.get(a):
			h[a]=1.0
			if type(im)!=dict:
				im.setAttrib(a, 1.0)
	return [h[a] for a in attr]

def imageShape(d, h=None):
	'''(d, h) are a tuple (array, dict) containing image data and header (which may be None). Return a tuple (d, h), where the data is in canonical image shape (4D (x,y,c,z)), and header is always a dict with SampleType:image'''
	if not h:
		h={}
	h['SampleType']='image'
	if not h.get("Url"):
		h['Url']='Unknown Stream (Locally Calculated)'
	if len(d.shape)==2:
		d=reshape(d, (d.shape[0], d.shape[1], 1, 1))
	if len(d.shape)==3:
		d=reshape(d, (d.shape[0], d.shape[1], d.shape[2], 1))	
	return (d, h)	

def getImageData(doc, paths, cast=None):
	'''Return the conditioned data for all images in the list paths, concatenated as a stack. If cast is specified (as a numpy type instance), all data is cast to that type. Otherwise, if all data has the same type it will be maintained, and if not all data will be cast to float32'''
	if type(paths) in [str, unicode]:
		paths=[paths]
	images=[doc.getInstance(p) for p in paths]
	images=[i for i in images if i.__tag__=='Data' and i.attrib('SampleType')=='image']
	dat=[]
	for i in images:
		d=imageShape(i.getData())[0]
		dat.append(d)
	if cast:
		dat=[d.astype(cast) for d in dat]
	elif len(set([d.dtype for d in dat]))>1:
		dat=[d.astype(float32) for d in dat]
	return concatenate(dat, 3)
	
def getImageDataAndHeader(doc, image, cast=None):
	'''Return the tuple (d, h) where d is an array of image data and h is a header dict, based on a single image upath "image" into the document instance doc. If cast is specified, data is cast to that type.'''
	i=doc.getInstance(image)
	h=i.header()
	d, h=imageShape(i.getData(), h)
	if cast:
		if not d.dtype==cast:
			d=d.astype(cast)
	return (d, h)

def setImageData(dat, path, doc, h=None, replace=1):
	'''Sets the image data in the element at path, in doc, to dat. If h is specified, sets the header also to contain the header information in h. If replace is 1 (default), reinitializes an existing element at the path. If it is 2, hard deletes any such element. If it is 0, changes path to be unique, so nothing is ever overwritten. If path doesn't include a colon, it is changed to "/Data:path (e.g. it is treated as "name" and the element is assumed to be at the top level in the document). '''
	if not ":" in path:
		path="/Data:"+path	
	if replace==1:
		e=forceGetPath(doc, path)
	else:
		e=addPath(doc, path, replace)
	dat, h=imageShape(dat, h)
	e.datinit(dat, h)

def isBinary(im):
	'''Return a tuple (minval, maxval) if the data in array im has at most two value, return False otherwise.'''
	if im.dtype==bool:
		if any(im):
			return (0,1)
		return (0,0)
	ran=(im.min(), im.max())
	ne=(im==ran[0]).sum()+(im==ran[1]).sum()
	if ne==im.size:
		return ran
	return False

def colorOverlay(im, o):
	'''Return a 4D image array that overlays grey images im and o into the color channels of a single color image. For non-binary images, im goes on the red channel and o on the green. For binary images, the return is RGB=(im only, o only, im AND o)'''
	if len(im.shape)<4:
		im=reshape(im, (im.shape[0], im.shape[1], 1, 1))
	if len(o.shape)<4:	
		o=reshape(o, (o.shape[0], o.shape[1], 1, 1))
	if im.shape[2]>1:
		im=im[:,:, 0:1, :]
	if o.shape[2]>1:
		o=o[:,:, 0:1, :]
	o=o.astype(float32)/o.max()
	im=im.astype(float32)/im.max()
	imbin=isBinary(im)
	obin=isBinary(o)
	if imbin and  obin:
		if imbin[0]!=0:
			im=im-imbin[0]
		if obin[0]!=0:
			o=o-obin[0]
		im=concatenate([logical_and(im, logical_not(o)), logical_and(o, logical_not(im)), logical_and(o,im)], 2)
	else:
		im=concatenate([im, o, zeros_like(o)], 2)
	return im


def makeGaussFilter(x, y, sigma):
	sig=float(sigma)
	x=x-x.shape[0]/2
	y=y-y.shape[0]/2
	x= exp( -1.0*x**2 / sig**2 )
	y= exp( -1.0*y**2 / sig**2 )
	return x*y

def get_image_stats(a):
	stats = {}
	stats['max'] = max(ravel(a))
	stats['min'] = min(ravel(a))
	stats['ave'] = sum(ravel(a.astype(Float64)))/len(ravel(a))
	stats['range'] = stats['max'] - stats['min']
	return stats
	
def get_contrast_level(a, f):
	s = sort(ravel(a))
	r = int(f*(len(s)-1))
	return s[r]

def shiftarray(a, sc):
	new = zeros(a.shape, a.dtype.char)
	ind = indices(a.shape)
	for i in range(len(a.shape)):
		ind[i] -= sc[i]
		ind[i]*=ind[i]>0
		last = ones(ind[i].shape)*(a.shape[i]-1)
		ind[i] = where(ind[i]>=a.shape[i], last, ind[i])
		factor = product(a.shape[i+1:])
		ind[i]*=factor
	ind = ravel(sum(ind))
	new = reshape(take(a.flat, ind), a.shape)
	return new
		

def neighbors(a, r):
	if r==0:
		return a.copy() 
	sl = transpose(array([concatenate([arange(-r,1),arange(0,r+1)]),
						  concatenate([arange(0,-r-1,-1),arange(r,-1,-1)])]))
	n = zeros(a.shape, Float64)
	for i in range(sl.shape[0]):
		n+=shiftarray(a,sl[i])
	n = n.astype(Float64)/sl.shape[0]
	return n
	
def gaussblur(a, sig):
	wts = exp( -1.0*arange(2*sig)**2 / sig**2 )
	ns = array(map(lambda x: neighbors(a, x), range(2*sig)))
	new = sum(ns*wts[:,NewAxis, NewAxis])/sum(wts)
	new = new.astype(a.dtype.char)+((new%1)>0)
	return new

def diamondblur(a, sig):
	shifts = [array([-1*sig, 0]), array([0, -1*sig]),
			  array([sig, 0]), array([0, sig])]
	ar = array([a] + map(lambda x:shiftarray(a, x), shifts))
	ar = sum(ar).astype(Float64)/5
	ar = ar.astype(a.dtype.char)+((ar%1)>0)
	return ar

def image_hotspot(a, h, sig):
	ar=a.copy()
	for i in range(1, sig+1):
		ar+=neighbors(a, i)
	c = get_contrast_level(ar, h)
	return a*(ar>c)




