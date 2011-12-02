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
from mien.math.sigtools import bandpass


def blankTS(ds, nchans=2, dur=10.0, fs=10000.0):
	'''Cause ds to contain data of SampleType timeseries that is all zeros.
The new data will be of type float32, have nchans (int) channels, and a 
duration of dur (float) seconds at a sampling rate of fs (float) Hz. 
StartTime is set to 0, and channels are labeled c0 c1 c2 etc.'''
	dur=round(fs*dur)
	newdat=zeros((dur, nchans), Float32)
	head={'SamplesPerSecond':fs, 'Labels':["c%i" % i for i in range(int(nchans))], 
	'StartTime':0.0, 'SampleType':'timeseries'}
	ds.datinit(newdat, head)

def newBlankSubData(ds, dpath='/', nchans=2, fs=1000.0, dur=10.0):
	'''Generates data as blankTS, but stores it in a new subdata 
element at dpath.'''
	dur=round(fs*dur)
	newdat=zeros((dur, nchans), Float32)
	head={'SamplesPerSecond':fs, 
		'Labels':["c%i" % i for i in range(int(nchans))], 
		'StartTime':0.0, 'SampleType':'timeseries'}
	ds.createSubData(dpath, newdat, head)

def zeros_like(ds, newpath="/zeros"):
	'''Create a subdata element equivalent to ds, but containing only zeros'''
	nd = ds.createSubData(newpath, zeros(ds.data.shape, ds.data.dtype), ds.header(), True)
	

def addSubToMain(ds, dpath='/', select=(None, None, None), delete=True):
	'''get the data contained in the subelement dpath and add it to the 
data specified by select. If delete is True, then delete element dpath.

SWITCHVALUES(delete)=[True, False]
'''
	de=ds.getSubData(dpath)
	dat=de.getData()
	od=getSelection(ds, select)
	dat=od+dat
	setSelection(ds, dat, select)
	if delete:
		de.sever()
		
def GWN(ds, select=(None, None, None), bandMin=5.0, bandMax=150.0, std=1.0, rseed=None, invert=False):
	'''Generates band limited Gaussian white noise in the frequency band 
(bandMin, bandMax) with mean 0, and standard deviation std. This noise is
added to all the data specified by select. If rseed is specified it will be 
used to seed the random number generator before generation. This will allow
repeated generation of identical "noise". Rseed should probably be an integer, 
though it may also be an array of ints. 

If invert is True, the noise will be multiplied by -1. This is usally irelevant,
but can be used in combination with rseed to add and later remove identicle 
noise samples. 

Notes:
	
	std is specified before bandpass filtering, so for very narrow bandwidths
	it will act as an upper bound rather than an exact measure.
	
	bandMin and bandMax are implicitly limited to the range 0, ds.fs()/2, and 
	no filter will be applied if they are outside these limits, or if both are 
	False. bandMax will be automatically set to ds.fs()/2 if it is None but 
	bandMin is >0.
	'''	
	if rseed:
		seed(rseed)
	od=getSelection(ds, select)
	wn=normal(0, std, od.shape)
	if bandMin or bandMax:
		fs=getSelectionHeader(ds, select)['SamplesPerSecond']
		nqf=fs/2
		if bandMax==None:	
			bandMax=nqf
		if bandMin==bandMax:
			print "eek. Zero bandwidth. aborting."
			return
		elif bandMin>bandMax:
			print "which part of 'Min' and 'Max' don't you understand?"
			bandMin, bandMax=bandMax, bandMin	
		if bandMin>=0 and bandMax<=nqf:
			for i in range(wn.shape[1]):
				wn[:,i]=bandpass(wn[:,i], bandMin, bandMax, fs)
	if invert:
		wn*=-1
	wn=od+wn
	setSelection(ds, wn, select)
	
	
def Sine(ds, select=(None, None, None), freq=100.0, amp=1.0, phase=0.0):
	'''Generates a sine wave s=amp*sin( (2*pi*freq*x - phase*pi/180 ) and adds it to the selected data. (Therefor freq is in Hz and phase is in degrees). Note that this is a sine function, so use phase -90 to get a cosine, and expect all fourier-based methods to show a 90 degree difference in phase from the phase specified to this method
	'''	
	od=getSelection(ds, select)
	fs=getSelectionHeader(ds, select).get('SamplesPerSecond') or ds.fs()
	x=arange(od.shape[0])/fs
	s=amp*sin( 2*pi*freq*x - phase*pi/180 )
	for i in range(od.shape[1]):
		od[:,i]+=s
	setSelection(ds, od, select)
						
		
def randomEvts(ds, n=5000, newpath='/rnd'):
	dat = randint(0, ds.data.shape[0], (n, 1))
	head = {"SampleType":"events", "StartTime":ds.start(), "SamplesPerSecond":ds.fs(), 'Labels':['Random']}
	ds.createSubData(newpath, dat, head)
		
