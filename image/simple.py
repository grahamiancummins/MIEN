
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

from mien.image.imagetools import *


def Add(doc, images, normalize=True, outputPath="CALC_OUTPUT"):
	'''Add all the images
SWITCHVALUES(normalize)=[True, False]	
'''
	dat=getImageData(doc, images, float32)
	ni=dat.shape[3]
	dat=dat.sum(3)
	if normalize:
		dat/=ni	
	if not outputPath:
		outputPath=images[0]
	setImageData(dat, outputPath, doc)
	

def _zpad(i, d, n, before=True):
	s=list(i.shape)
	s[d]=n
	p=zeros(tuple(s), i.dtype)
	if before:
		i=concatenate([p, i], d)
	else:
		i=concatenate([i, p], d)
	return i

def pad(doc, image, left=50, right=50, top=50, bottom=50, outputPath=''):
	'''Zero pad the image with the specified number of pixels in each dimension'''
	dat, h = getImageDataAndHeader(doc, image)
	dat=_zpad(dat, 0, left, True)
	dat=_zpad(dat, 0, right, False)
	dat=_zpad(dat, 1, top, True)
	dat=_zpad(dat, 1, bottom, False)
	if h.get('SpatialAnchor'):
		pw, ph, ss = voxelDims(h)
		x, y, z = h['SpatialAnchor']
		h['SpatialAnchor']=(x-left*pw, y-top*ph, z)
	setImageData(dat, outputPath or image, doc, h)

def flipVertical(doc, image, outputPath=''):
	'''Inverts the order of scan rows in the image (mirroring it along its horizontal center'''
	dat, h = getImageDataAndHeader(doc, image)
	dat=dat[:,arange(dat.shape[1]-1, -1, -1),:,:]
	setImageData(dat, outputPath or image, doc, h)
	
def flipHorizontal(doc, image, outputPath=''):
	'''Inverts the order of scan rows in the image (mirroring it along its horizontal center'''
	dat, h = getImageDataAndHeader(doc, image)
	dat=dat[arange(dat.shape[0]-1, -1, -1),:,:,:]
	setImageData(dat, outputPath or image, doc, h)



def _imrotate(i, t):
	ind=transpose(array(nonzero(ones(i.shape[:2]))))	
	s=(i.shape[0]/2, i.shape[1]/2)
	rind=ind.astype(float32)-s
	rind=rotate(rind, t)
	rind=roundtoint(rind)+s
	gi=nonzero(logical_and(all(rind>=(0,0), 1), all(rind<i.shape[:2],1)))
	ind=ind[gi]
	rind=rind[gi]
	out=ones_like(i)*i.dtype.type(i.mean())
	out[ind[:,0], ind[:,1], :, :]=i[rind[:,0], rind[:,1], :, :]
	return out

def fastRotate(doc, image, ang=45.0, outputPath=''):
	'''Rotate the image ang degrees counterclockwise, using a quick and dirty algorithm '''
	dat, h = getImageDataAndHeader(doc, image)
	ang=ang % 360
	if ang==0:
		dat=dat.copy()
	elif ang==90:
		dat=transpose(dat, [1,0,2,3])
	elif ang==180:
		dat=dat[arange(dat.shape[0]-1,-1,-1),:,:,:]
		dat=dat[:,arange(dat.shape[1]-1,-1,-1),:,:]
		pass
	elif ang==270:
		dat=transpose(dat, [1,0,2,3])
		dat=dat[arange(dat.shape[0]-1,-1,-1),:,:,:]
	else:
		dat=_imrotate(dat, ang)
	setImageData(dat, outputPath or image, doc, h)
	

def fastRescale(doc, image, width=512, height=-1, outputPath=''):
	'''Rescale the image to the indicated width and height using quick and dirty pixel sampling (no interpolation). If height is negative (default) it is chosen automatically so as to maintain the aspect ratio'''
	dat, h = getImageDataAndHeader(doc, image)
	oshape=dat.shape
	if height<1:
		height=int(round(float(width)*dat.shape[1]/dat.shape[0]))
	ws=uniformSampleIndex(dat.shape[0], width)
	hs=uniformSampleIndex(dat.shape[1], height)	
	dat=dat[ws,:,:,:]
	dat=dat[:,hs,:,:]
	if h.get('PixelWidth'):
		pw, ph, ss = voxelDims(h)
		h['PixelWidth']=float(pw)*oshape[0]/width
		h['PixelHeight']=float(ph)*oshape[1]/height
	setImageData(dat, outputPath or image, doc, h)
	

def threshold(doc, image, thresh=128, outputPath=""):
	dat, h = getImageDataAndHeader(doc, image)
	dat=((dat>=thresh)*255).astype(uint8)
	setImageData(dat, outputPath or image, doc, h)
	

def crop(doc, image, xmin=0, xmax=600, ymin=0, ymax=400, outputPath=""):
	'''crop an image or stack to contain only pixels in the indicated box '''
	dat, h = getImageDataAndHeader(doc, image)
	dat=dat[xmin:xmax,ymin:ymax,:,:]
	if not outputPath:
		outputPath=image
	if h.get('SpatialAnchor'):
		pw, ph, ss = voxelDims(h)
		x, y, z = h['SpatialAnchor']
		h['SpatialAnchor']=(x+xmin*pw, y+ymin*ph, z)
	setImageData(dat, outputPath or image, doc, h)
	
def cropToBB(doc, image, point1, point2, outputPath=""):
	'''crop an image or stack to contain only pixels in the indicated box '''
	dat, h = getImageDataAndHeader(doc, image)
	xmin=min(point1[0], point2[0])
	xmax=max(point1[0], point2[0])
	ymin=min(point1[1], point2[1])
	ymax=max(point1[1], point2[1])
	crop(doc, image, xmin, xmax, ymin, ymax, outputPath)



def setAtrributte(doc, image, attribute, value):
	'''Sets the named attribute in the specified image to the named value '''
	i=doc.getInstance(image)
	i.setAttr(attribuute, value)

try:
	import scipy.signal
	def gaussianBlur(doc, image, stddev=5.0, outputPath="CALC_OUTPUT"):
		'''blur the images'''
		dat, h = getImageDataAndHeader(doc, image, float32)
		fs=stddev*9
		filt=fromfunction(lambda x,y:makeGaussFilter(x,y,stddev), (fs,fs))
		m=dat.max()
		mi=dat.min()
		for i in range(dat.shape[2]):
			for j in range(dat.shape[3]):
				dc=scipy.signal.convolve2d(dat[:,:,i,j], filt, mode='same')
				dat[:,:,i,j]=dc
		dat-=dat.min()
		dat/=dat.max()
		dat*=(m-mi)
		dat+=mi
		setImageData(dat, outputPath or image, doc, h)
except:
	pass	


			



 
