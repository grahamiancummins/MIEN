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
from mien.math.sigtools import psde, coherence

 		
def cohere(ds, select1=(None,[0],None), select2=(None,[1],None), dpath='/coh'):
	'''For each channel in the data specified by select1, calculate the coherence between this and the coresponding channel in select2. Store the 
array of coherences in dpath. If events are selected, they are converted to
timeseries of zeros and ones before the calculation (this conversion affects 
only the calculation, not the stored event data).'''
	dat1=getSelection(ds, select1, evts2ts=True)
	dat2=getSelection(ds, select2, evts2ts=True)
	if dat2.shape[0]>dat1.shape[0]:
		dat2=dat2[:dat1.shape[0],:]
	elif dat2.shape[0]<dat1.shape[0]:
		nfs=dat1.shape[0]-dat2.shape[0]
		fill=zeros((nfs, dat2.shape[1]), dat2.dtype)
		dat2=concatenate([dat2, fill], 0)
	fs=getSelectionHeader(ds, select1)['SamplesPerSecond']
	allcoh=[]
	for i in range(dat1.shape[1]):
 		coh =  coherence(dat1[:,i], dat2[:,i], fs)
		fi=coh[1,0]-coh[0,0]
		allcoh.append(coh[:,1])
	coh=transpose(array(allcoh))
	head={'SamplesPerSecond':1.0/fi, 'StartTime':0.0, 'SampleType':'timeseries'}
	ds.createSubData(dpath, coh, head, delete=True)


def PSD(ds, select=(None, None, None), dpath='/psd'):
	'''for each channel of data specified in select, calculate the power 
spectrum. Store the resulting data in dpath'''
	dat=getSelection(ds, select)
	fs=getSelectionHeader(ds, select)['SamplesPerSecond']
	acpsd=[]
	for ci in range(dat.shape[1]):
		psd = psde(dat[:,ci], fs)
		fi=psd[1,0]-psd[0,0]
		acpsd.append(psd[:,1])
	psd=transpose(array(acpsd))
	head={'SamplesPerSecond':1.0/fi, 'StartTime':0.0, 'SampleType':'timeseries'}
	ds.createSubData(dpath, psd, head, delete=True)
	
