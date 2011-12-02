#Simple python functions for waveform handling 

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

import struct, os
from copy import deepcopy
from mien.math.array import *
from numpy.fft import irfft, rfft
inverse_real_fft=irfft
fft=rfft

import numpy.linalg as la
SAME=1

#from scipy import fft

def makeRaster(evts, bin):
	'''1D array, float => 1D array'''
	evts = evts - evts.min()
	t = arange(0, evts.max()+bin, bin)
	rast = zeros(t.shape[0], t.dtype.char)
	if evts.shape[0]>t.shape[0]:
		#print "method 1"
		for i in range(t.shape[0]-1):
			#print t[i], t[i+1], where(logical_and(evts>= t[i], evts<t[i+1]), 1,0).sum()
			rast[i] = where(logical_and(evts>= t[i], evts<t[i+1]), 1,0).sum()
	else:
		evts = (evts/bin).astype(Int32)
		for i in range( evts.shape[0]):
			rast[evts[i]]+=1
	return rast
#====================EDGE WARPING==============================
def make_bow(n, d1, d2):
	dstep=(d2-d1)/(n+1)
	ds=arange(1,n+1)
	ds=ds*dstep+d1
	return cumsum(ds)

def make_shift(n, d):
	'''n (int), d (float) => array
returns a length n array specifying a sigmoid that covers a vertical distance d'''
	x=arange(n).astype(Float32)
	mid=float(n-1)/2
	slope=4.0/mid
	shift=d/(1.0+exp( (-1*(x-mid))*slope))
	return shift

def warp_from_zero(n, x, d):
	if type(x)!=type(1.0):
		x=float(x)
	if type(d)!=type(1.0):
		d=float(d)
	switch=0
	if x<0:
		switch=1
		d=-1*d
		x=-1*x
	if d==0:
		func=sin(arange(-pi/2, pi/2, pi/n)[:n])
		func=x*(func+1)/2.0
  	elif d>0 and 2*x/d<=n:
		fn=2*x/d
		f=make_bow(fn, 0, d)
		f2=zeros(n-fn, Float32)
 		func=concatenate([f2, f])
	else:
		f=make_bow(int(n/3), 0, d)
		f2=warp_from_zero(n-int(n/3), x-f[-1], 0)
		f=f+x-f[-1]
		func=concatenate([f2, f])
	if switch:
		func=-1*func
	return func

def smooth(f, n):
	f=f.copy()
	if len(f)<2*n:
		smooth=len(f)/2
	else:
		smooth=n
	sfunc1=warp_from_zero(smooth, f[smooth], f[smooth+1]-f[smooth])
	sfunc2=warp_from_zero(smooth, f[-smooth], f[-smooth-1]-f[-smooth])
	sfunc2=take(sfunc2, arange(len(sfunc2)-1, -1, -1))
	put(f, arange(smooth), sfunc1)
	put(f, arange(-smooth, 0), sfunc2)
	return f

def smoothConnect(a1, a2, npts):
	'''a1 (array), a2 (array), npts => array
returns an array of length npts that will smoothly connect a1 to a2'''
	d1=a1[-1]-a1[-2]
	d2=a2[1]-a2[0]
	con=make_bow(npts+1, d1, d2)
	con+=a1[-1]
	di=a2[0]-con[-1]
	ada=make_shift(npts+1, di)
	con=con+ada
	return con[:-1]

#=====================FILTERING===================================

def deriv(a, samp):
	return ((a-concatenate(([a[0]], a[:-1])))*samp)

def hamming(n):
	k=arange(n)
	w=0.54-0.46*cos(2*pi*k/(n-1))
	return w

def hanning(n):
	k=arange(n)
	w=.5-.5*cos(2*pi*k/(n-1))
	return w

def makebandpass(n, low, high):
	r=arange((n/2)+1)
	ideal=greater_equal(r, low*(n/2))*less_equal(r,high*(n/2))
	while n<600 and all(ideal==0):
		print "Warning, filter length to short to see this band"
		print "increasing length by 10"
		n+=10
		r=arange((n/2)+1)
		ideal=greater_equal(r, low*(n/2))*less_equal(r,high*(n/2))
	rft=inverse_real_fft(ideal)
	rft=concatenate((rft[n/2:], rft[:n/2+1]))
	w=hamming(len(rft))
	return w*rft

def convertfreq(bw, Hz):
		'''
		convert from a frequency in Hz (Hz) sampled at the sampling rate "bw" to normalized frequency (units of pi
		radians/sample
		
		bw is the full sampling rate (not Nyquist)
		
		'''
		if Hz>=bw:
			f=1.0
		elif Hz<=0:
			f=0.0
		else:
			f=2*Hz/bw
		return f
	
def numfilter(dat, filt):
	ds=dat.shape[0]
	fs=len(filt)
	filt = reverseArray(filt)
	dat=concatenate([zeros(fs, dat.dtype),  dat, zeros(fs, dat.dtype)])
	dat=convolve(dat, filt, 'same')
	dat=concatenate([dat[fs-1:fs+ds-1]])
	return dat
		
	
def bandpass(sig, low, high, bw=None):
	'''low, high, and bw are in Hz. bw is the full sampling frequency (not the
nyquist limit''' 
	if bw:
		high=convertfreq(bw, high)
		low=convertfreq(bw, low)
	try:
		n = max(90, int(4.0/(high-low)))
	except:
		n=90
	if n%2:
		n+=1
	f=makebandpass(n, low, high)
	#print high, low, n, f.sum()
	z=numfilter(sig, f)
	return z



#=================Stimulus Transforms======================

def cart_to_pol(x,y):
	mag=sqrt(x**2+y**2)
	try:
		theta=arctan(y/x)*360/(2*pi)
	except OverflowError:
		x+=.00000001
		#put(x,nonzero(less(abs(x), .00000001)) ,.00000001*ones(len(x), x.dtype.char))
		theta=arctan(y/x)*360/(2*pi)
	sinefix=(x<0)*180
	theta+=sinefix
	theta-=360*(theta>180)
	return (mag,theta)

def pol_to_cart(r, theta):
	theta=theta*2*pi/360
	x=r*sin(theta)
	y=r*cos(theta)
	return [x,y]


#========================Signal Analysis================================

def makeGWN(N, std, rseed=0, band=None):
	''' N (int), std (float), rseed (int=0), band (tuple = None) => array
	returns a length N array of gausian noise. Seeds the
	random number generator with 1, rseed (0 generates a random
	seed from the clock). If band, bandpass the result (band is length 2,
	lower, upper, on the range 0 to 1 (not in Hz))'''
	if rseed:
		seed(1, rseed)
	wn = normal(0, std, N)
	if band:
		wn = bandpass(wn, band[0], band[1])
		if wn.shape[0]>N:
			wn = wn[-N:]
	return wn

#========================Coherence=======================================

def sinc(x):
	return where(x==0, 1.0, sin(pi*x)/(pi*x))

def slepian(M,width,sym=1):
    if (M*width > 27.38):
        raise ValueError, "Cannot reliably obtain slepian sequences for"\
              " M*width > 27.38."
    if M < 1:
        return array([])
    if M == 1:
        return ones(1,'d')
    odd = M % 2
    if not sym and not odd:
        M = M+1
    twoF = width/2.0
    alpha = (M-1)/2.0
    m = arange(0,M)-alpha
    n = m[:,NewAxis]
    k = m[NewAxis,:]
    AF = twoF*sinc(twoF*(n-k))
    [lam,vec] = la.eigenvectors(AF)
    ind = argmax(abs(lam))
    w = abs(vec[:,ind])
    w = w / max(w)
    if not sym and not odd:
        w = w[:-1]
    return 


def ampPhaseToComplex(amp, phase):
	'''construct a complex vector of the form a+bi from magnitued and phase vectors'''
	return amp*exp(1j*phase)

def complexToAmpPhase(c):
	amp = abs(c)
	phase = arctan2(c.imag, c.real)
	return (amp, phase)

def windowedFFT(dat, fs):
	nfft = int(round(min(fs, dat.shape[0])))
	nfft = min(16384, nfft)
	if nfft%2:
		nfft+=1
	window = nfft/2
	over = int(window/2)
	winstep = window-over
	nwin = int((dat.shape[0]-over)/winstep)
	if nwin < 1:
		nwin=1
		window=inp.shape[0]
		over=0
	hann=hanning(window)
	fts = []
	for i in range(nwin):
		dsec=dat[i*winstep:i*winstep+window]
		dsec=(dsec-dsec.mean())*hann
		fts.append(rfft(dsec, nfft))
	ft = array(fts).mean(0)
	freq = arange(ft.shape[0])*fs/(2.0*ft.shape[0])
	amp = abs(ft)
	wfac = hann.sum()/hann.shape[0]
	amp*=2.0/(wfac*min(window, nfft))
	phase = arctan2(ft.imag, ft.real)
	return (freq, amp, phase)

def getSpectraHann(inp, out=None, nfft=None, over=None):
	'''inp and out are 1D arrays of the same length. Returns (Pxx, Pyy, Pxy).
	Uses a sliding Hanning window. If nfft is uspecified it
	defaults to min(16384, len(inp)). If over is unspecified
	it defaults to nfft/4'''
	if nfft==None:
		nfft=min(16384, inp.shape[0])	
	if nfft%2:
		nfft+=1
	window = nfft/2
	if over==None:
		over=int(window/2)
	winstep = window-over
	nwin = int((inp.shape[0]-over)/winstep)
	if nwin < 1:
		nwin=1
		window=inp.shape[0]
		over=0
		print "Warning: dataset is short. Using single window"
	hann=hanning(window)
	powX = zeros(window+1, Float64)
	cross = zeros(window+1, Complex64)
	powY = zeros(window+1, Float64)
	for i in range(nwin):
		inpsec=inp[i*winstep:i*winstep+window]
		inpsec=(inpsec-inpsec.mean())*hann
		inpfft=fft(inpsec, nfft)
		psec=(inpfft*conjugate(inpfft))
		powX+=psec.real[:window+1]
		outsec=out[i*winstep:i*winstep+window]
		outsec=(outsec-outsec.mean())*hann
		outfft=fft(outsec, nfft)
		csec=outfft*conjugate(inpfft)
		cross+=csec[:window+1]
		psec=(outfft*conjugate(outfft))
		powY+=psec.real[:window+1]
	return (powX, powY, cross)

def transferFunction(inp, out, nfft=None, over=None):
	'''inp and out are 1D arrays of the same length. Compute the
	an estimate of the transfer function of the sytem that converts
	inp to out (a 1D complex array)'''
	Pxx, Pyy, Pxy = getSpectraHann(inp, out, nfft, over)
	return Pxy/Pxx


def psde(dat, fs):
	'''dat: 1D array, fs (sampling freq in Hz)
	=> 2D array (power spectrum estimate), frequency on chan 0'''
	freq, amp=windowedFFT(dat, fs)
	psd = transpose(array([freq, log(amp**2)]))
	return psd

def coherence(idat, odat, fs):
	'''idat (1D array), odat (1D array), fs (sampling freq in Hz)
	=> 2D array (coherence estimate)'''
	nfft=2**int(log(fs)/log(2)) #Try and match this to fs (16384 at 20KHz)
	while nfft>idat.shape[0]:
		nfft=nfft/2
	Pxx, Pyy, Pxy=getSpectraHann(idat, odat, nfft)
	freq = arange(Pxx.shape[0]).astype(Float64)*fs/(2*Pxx.shape[0])
	coh = abs(Pxy)**2/(Pxx*Pyy)
	fcd = transpose(array([freq, coh]))
	return fcd

def bode(idat, odat, fs):
	'''idat (1D array), odat (1D array), fs (sampling freq in Hz)
	=> 1D array (coherence estimate)'''
	nfft=2**int(log(fs)/log(2)) #Try and match this to fs (16384 at 20KHz)
	while nfft>idat.shape[0]:
		nfft=nfft/2
	trans=transferFunction(idat, odat, 1024, 256)
	freq = arange(trans.shape[0]).astype(Float64)*fs/(2*trans.shape[0])
	amp=abs(trans)
	phase=arctan2(trans.imag, trans.real)
	return (freq, amp, phase)

#==============================discriminators=======================

def disc1D(a, target):
	'''a (1D array), target(1D array of len <= len(a)) -> arrray (same shape as a)'''
	shifted=zeros((a.shape[0]-target.shape[0], target.shape[0]), a.dtype.char)
	for i in range(target.shape[0]):
		shifted[:,i]=a[i:i+shifted.shape[0]]
	dif=(shifted-target)**2
	dif=sum(dif, 1)
	nor=sum(shifted**2, 1)	
	out=1.0-(dif/nor)
	out=concatenate([zeros(target.shape, a.dtype.char), out])
	return out

#==============================probability=======================

def histFromEvents(evts, dx, lim=False):
	'''evts (1D array), dx (float), lim (tuple or False) -> 1D array
	build a histogram with bins of width dx from a list of events in evts.
	If lim is a tuple, the histogram bins will run from lim[0] to 
	<= lim[1]+dx. Otherwise they will run from min(evts) to <=max(evts)+dx.'''
	if not lim:
		lim=(evts.min(), evts.max())
	nbins=int(ceil( (lim[1]-lim[0])/dx))
	bins=(arange(nbins)+1)*dx+lim[0]
	hist=zeros(nbins)
	past = 0
	for i in range(bins.shape[0]):
		env = (evts<bins[i]).sum()
		hist[i] = env - past
		past = env
	return hist
		
def drawFromHist(n, a):
	'''return n samples drawn from probabilities specified in array a.
	A is first scaled to act as a probability distribution (a=a/a.sum()).
	Return vaules are the integers and index a (e.g. a "3" represents an 
	event of the type in histogram bin a[3]).'''
	pd=a/float(a.sum())
	pd=cumsum(pd)
	evts=uniform(0, 1, n)
	indexes=array([(pd<=e).sum() for e in evts])
	return indexes
		
	
