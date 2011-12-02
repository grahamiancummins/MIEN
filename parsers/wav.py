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

import wave
import nmpml #does this need to be "mien.parsers.nmpml"?
from mien.math.array import ArrayType, reshape, fromstring, ones, any, ravel, dtype, all, array_resample, array

	

def read(f, **kwargs):
	wf=wave.open(f)
	head={}
	head['SamplesPerSecond']=wf.getframerate()
	head['SampleType']='timeseries'
	nc=wf.getnchannels()
	nf=wf.getnframes()
	nbits=wf.getsampwidth()
	data=wf.readframes(nf)
	dt="i%i" % (nbits,)
	dt=dtype(dt)
	data=fromstring(data, dt)
	data=reshape(data, (-1, nc))
	if nc==2 and all(data[:,0]==data[:,1]):
		print "this is a mono file pretending to be stereo"
		data=reshape(data[:,0], (-1,1))
	data=data.astype('f4')/2**(8*nbits-1)
	try:
		url="file://%s" % (f.name,)
	except:
		try:
			url=f.geturl()
		except:
			url=None
	attributes={'Name':'Wavdata'}
	if url:
		attributes['Url']=url
	de=nmpml.createElement('Data', attributes)
	de.datinit(data, head)
	n = nmpml.blankDocument()
	n.newElement(de)
	return n
	

def write(f, doc, **kwargs):
	dats=doc.getElements('Data')
	if len(dats)>1:
		print "can only save a single Data element as Wave. Using first element"
	dat=dats[0]
	oldfs=dat.fs()
	dat=dat.data
	if dat.shape[1]>2:
		print "maximum of 2 channels in wave data. Truncating"
		dat=dat[:,:2]
	if oldfs!=44100:
		print "warning, saveing wave file with unconventional sampling rate"
	#	chans=[]
 	#	for i in range(dat.shape[1]):
 	#		chans.append(array_resample(dat[:,i], 1.0/oldfs, 1.0/44100))
 	#	oldfs=44100	
 	#	dat=transpose(array(chans))
 	dt=dat.dtype.str
 	if dt[1]=='i' and int(dt[2])<4:
 		pass
 	else:
 		ran=abs(dat).max()
 		if dt[1]=='i' and ran<32768:
 			pass
 		else:
 			dat=dat.astype('f8')
 			if ran>1.0:
 				print "rescaling data"
 				dat=dat/ran
 			dat=dat*32767
 	dat=dat.astype('i2')		
 	wf=wave.open(f, 'w')
 	wf.setnchannels(dat.shape[1])
 	wf.setsampwidth(2)
 	wf.setframerate(oldfs)
 	wf.writeframes(dat.tostring())


filetypes={}
				 
filetypes['Wav']={'notes':"Common audio recording format",
					'read':read,
					'write':write,
					'data type':'numerical timeseries',
					'elements':['Data'],
					'extensions':['.wav']}