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
from mien.datafiles.dataset import *

def delete(ds, dpath='/'):
	'''delete the data element at dpath'''
	d=ds.getSubData(dpath)
	d.sever()

def move(ds, dpath='/', newpath='/'):
	'''Moves a data element from dpath to newpath. Newpath should be the path of
the new container (not the new path for the element itself). If newpath doesn't
exist, a new element of SampleType "group" will be created with that path.'''
	if not dpath or dpath=='/':
		print "Can't move the top level element"
		return
	np=ds.getSubData(newpath)
	if not np:
		np=ds.createSubData(newpath)
	dat=ds.getSubData(dpath)
	dat.move(np)

def swap(ds, dpath1='/sub1', dpath2='/sub2'):
	'''Exchange the data element at dpath1 with the one at dpath2.'''
	d1=ds.getSubData(dpath1)
	d2=ds.getSubData(dpath2)
	d1p=d1.container
	d2p=d2.container
	d1.move(d2p)
	d2.move(d1p)


def copy(ds, dpath='/', newpath='/'):
	'''Like move, but generates a clone of the original to place at the new
location'''
	dat=ds.getSubData(dpath).clone()
	np=ds.getSubData(newpath)
	if not np:
		np=ds.createSubData(newpath)
		np.datinit(dat.getData(), dat.header())
	else:
		np.newElement(dat)

def rename(ds, dpath='/', name='new'):
	'''Change the name of the element at dpath'''
	ds=ds.getSubData(dpath)
	ds.setAttrib("Name", name)

def combine(ds, dpath1='/', dpath2='/', copy=False):
	'''Combine the two data elements. For timeseries, this adds channels in
dpath2 to dpath1. If copy is False, dpath2 is then removed.
SWITCHVALUES(copy)=[False, True]
'''
	d1=ds.getSubData(dpath1)
	d2=ds.getSubData(dpath2)
	combineData(d1, d2, copy)

def appendSamples(ds, select=(None, None, None), dpath=None, delete=True):
	'''Add the samples in "select" to the existing data in element dpath (this
must be sampled data with the same number of channels). If delete is true,
then remove the selected adat after the copy.
SWITCHVALUES(delete)=[False, True]
'''
	targ=ds.getSubData(dpath)
	source=ds.getSubData(select[0])
	if source==targ:
		return
	if not source.stype()==targ.stype():
		raise StandardError("can't append samples to data of differing SampleType - target type is %s" % targ.stype())
	if not source.fs()==targ.fs():
		raise StandardError("can't (safely) append samples to data of differing sampling rate. Target rate is %.4g" % targ.fs())
	dat=getSelection(ds, select)
	targ.concat(dat)
	

def extract(ds, select=(None, [1], None), newpath="/extractedevents", delete=True):
	'''Move the selected data to a new data element at newpath.
If delete is False, leave the data in the original location as well (copy
rather than move). For all types other than events, delete is only possible if
select specifies either all samples, all channels, or the entire element.
If select specifies an entire element (it is of the form ("foo", None, None)),
this function acts as move or copy (depending on the value of "delete").

SWITCHVALUES(delete)=[False, True]
'''
	pde=ds.getSubData(select[0])
	if not (select[1] or select[2]):
		oldname=pde.name()
		oldpath=select[0]
		newpath=newpath.split('/')
		newname=newpath[-1]
		if newname and newname!=oldname:
			ds.setAttrib("Name", newname)
			oldpath=ds.dpath()
		newpath='/'.join(newapath[:-1])
		if delete:
			move(oldpath, newpath)
		else:
			copy(oldpath, newpath)
		return
	if ds.getSubData(newpath):
		print 'Selected Path Exists. Deleting it'
		sd=ds.getSubData(newpath)
		sd.sever()
	dat=getSelection(ds, select)
	labs=pde.getLabels()
	if select[1]:
		labs=[labs[i] for i in select[1]]
	head={'SampleType':pde.stype(), 'Labels':labs}
	if isSampledType(pde):
		head['SamplesPerSecond']=pde.fs()
		if isSampledType(pde):
			if isSampledType(pde)=='e' or not select[2]:
				head['StartTime']=pde.start()
			else:
				sa=getRangeFromSelect(ds, select)[0]
				head['StartTime']=pde.start()+sa/pde.fs()
		if pde.stype()=='labeledevents' and select[1] and len(select[1])==1:
			head['SampleType']='events'
	ds.createSubData(newpath, dat, head)
	if delete:
		deleteSelection(ds, select, True)

def moveToTop(ds, dpath='/sub', swap=False):
	'''Use the data specified in dpath as the contents of the toplevel data element. If swap is True, also copy the data from the toplevel element into dpath. Otherwise, delete these data, and the subelement dpath
SWITCHVALUES(swap)=[False, True]'''
	if not dpath or dpath=='/':
		return
	new=ds.getSubData(dpath)
	if not new:
		print 'no such path'
		return
	if swap:
		od=ds.getData()
		oh=ds.header()
	ds.datinit(new.getData(), new.header())
	if swap:
		new.datinit(od, oh)
	else:
		new.sever()

def insert(ds, dpathSource="/test", dpathTarget="/", channelOffset=0, sampleOffset = -1, remove=True):
	'''Insert the data from element dpathSource into the data element at dpathTarget.
The entire data array from dpathSource is inserted (it must therefore be <= the dimensions of the existing data array at dpathTarget). If the data array at dpathSorce is I, its shape is S, and the data array at dpathTarget is D, then the data are inserted as: D[sampleOffset:sampleOffset+S[0], channelOffset:channelOffset+S[1]] = I. If sampleOffset is <0 (the default), the sampleOffset is calculated using the sample rate and start time of the two data elements. Otherwise, sampleOffset is taken to be an integer index. If "remove" is true, the element at dpathSource is deleted after the insertion (unless it is "/").
SWITCHVALUES(remove)=[True, False]
'''
	I = ds.getSubData(dpathSource)
	D = ds.getSubData(dpathTarget)
	if sampleOffset < 0:
		to = I.start() - D.start()
		sampleOffset = int(round(to*D.fs()))
		if sampleOffset < 0:
			print("WARNING: automatic sample offset is <0. Aborting. Use a manual offset")
			return
	S = I.data.shape
	D.data[sampleOffset:sampleOffset+S[0], channelOffset:channelOffset+S[1]] = I.data.copy()
	if remove and I!=ds:
		I.sever()


def addChannels(ds, dpathSource="/sub", dpathTarget="/", channelOffset=-1, remove=True):
	'''Add the data from element dpathSource into the data element at dpathTarget.
The entire data array from dpathSource is inserted (it must therefore have the same length as the existing data array at dpathTarget). All channels of dpathSource are added to dpath target with the 0 channel of dpathSource taking the index channelOffset (-1 indicates append to the existing array). Channels of dpathTarget are not overwritten. If needed, these channels are added onto the array after the new channels from dpathSource.
If remove is True, dpathSource is deleted after the operation. 
SWITCHVALUES(remove)=[True, False]
'''
	I = ds.getSubData(dpathSource)
	D = ds.getSubData(dpathTarget)
	h = D.header()
	tlabs = D.getLabels()
	ilabs = I.getLabels()
	idat = I.getData()
	tdat = D.getData()
	if channelOffset== -1:
		dat = column_stack([tdat, idat])
		labs = tlabs + ilabs
	elif channelOffset==0:
		dat = column_stack([idat, tdat])
		labs = ilabs + tlabs
	else:
		dat = column_stack([tdat[:,:channelOffset], idat, tdat[:,channelOffset:]])
		labs = tlabs[:channelOffset] + ilabs + tlabs[channelOffset:]
	h["Labels"]= labs
	D.datinit(dat, h)
	if remove and I!=ds:
		I.sever()	

def colapseAllToTop(ds):
	'''fold all subdata into the top level element if possible'''
	h=ds.getHierarchy()
	squish=[]
	for k in h.keys():
		if k=='/':
			continue
		sd=ds.getSubData(k)
		if sd.fs()!=ds.fs():
			continue
		if sd.stype()!=ds.stype():
			continue
		try:
			dat=sd.getData()
			labs=sd.getLabels()
			ds.addChans(dat, labs)
			squish.append(sd)
		except:
			print k
			raise
			pass
	for sd in squish:
		try:
			sd.sever()
		except:
			print str(sd)
			pass
			


