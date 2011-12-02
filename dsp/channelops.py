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

'''Note that these functions expect a simple Data instance of sample type 
timeseries. (Simple Data implies that either there are no nested Data 
elements, or, if there are, that these functions don't need to process them, 
and that they won't be rendered unstable by changes to the top level Data 
instance. 
'''

from mien.datafiles.dataset import *
dscrop=crop

def reorderChannels(ds, order=[]):
	'''set channel order'''
	dat=ds.getData(order)
	ds.setData(dat)
	l=ds.getLabels()
	l=[l[i] for i in order]
	ds.setAttrib('Labels', i)

def ShiftChannels(ds, chans=[0], xcoord1=0, xcoord2=100):
	'''shifts the listed channels by xcoord1-xcoord2'''
	if xcoord1==xcoord2:
		return
	si=round((xcoord2-xcoord1)*ds.fs())
	for ci in chans:
		q=shift(channel((ds, ci)), si)
		ds.setData(q, [ci])
		
def duplicateChannel(ds, chan=0, cname=None):
	'''m akes a copy of the channel chanFrom and adds it to the dataset with
	name cnameTo'''
	chan=channel(ds, chan)
	if cname:
		cname=[cname]
	ds.addChans(chan, cname)
	return ds
	
def deleteChannels(ds, chans=[0]):
	ds.delChans(chans)
	
def crop(ds, dpath='/', firstSample=0, nsamples=None):
	'''Crop the data in dpath, by samples, not times. nsamples is the 
total length of the data after the crop. If it is unspecified, it will 
run to the end of the data
'''
	ds=ds.getSubData(dpath)
	if not nsamples:
		stop=ds.shape()[0]
	else:	
		stop=firstSample+nsamples
	dscrop(ds, (firstSample, stop))	

def ravel(ds, dpath='/'):
	'''Convert the selected data object to a single channel by stringing the existing channels together.'''
	ds=ds.getSubData(dpath)
	dat=ravel(transpose(ds.getData()))
	h=ds.header()
	h['Labels']=[h['Labels'][0]]
	ds.datinit(dat, h)
	
def qualityBasedMerge(ds, dpath='/', blocksize=2, qci=1):
	'''Merge channels in the data element dpath according to a quality indicator. The function assumes that the channels are dividied into some number of alternate recordings of the same information. The recordings have blocksize total channels. Of these, all but one of the channels are data records, and the single channel with index qci within each block is a quality indicator. The data are merged such that there are a total of blocksize final channels, and each one has the value at each sample point drawn from the block that had the highest value of the quality channel at that sample point.'''
	ds=ds.getSubData(dpath)
	if ds.shape()[1] % blocksize:
		raise StandardError('Data is not the right shape')
	qcs=arange(qci, ds.shape()[1], 	blocksize)
	dat=ds.getData()
	qcs=take(dat, qcs, 1)
	blockid=argmax(qcs, 1)*blocksize
	nd=zeros((dat.shape[0], blocksize), dat.dtype)
	x=arange(dat.shape[0])
	for i in range(blocksize):
		nd[:,i]=dat[x,blockid+i]
	h=ds.header()
	h['Labels']=h['Labels'][:blocksize]
	ds.datinit(nd, h)
	
def sameShape(ds, dpath1, dpath2):
	'''Makes dpath2 the same length, start, and Fs as dpath1'''
	d1=ds.getSubData(dpath1)
	d2=ds.getSubData(dpath2)
	compatLength(d1, d2)
		
	
