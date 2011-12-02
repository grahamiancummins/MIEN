
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

def isiStats(ds, cindex=1, length=.02, bins=40, sKey='isidist'):
	'''Characterizes the distribution of isis in the indicated channel, out to the indicated time'''
	rast=ds.getChannel(cindex)
	thresh = (rast.max()-rast.min())/2.0
	ind = nonzero1d(rast>thresh)
	spb=int(round((length/bins)*ds.fs))
	spi=spb*bins
	lis=float(spi)/ds.fs
	if lis!=length:
		print "actual event length is %.3g" % lis
	ind-=spi
	dat=ds.takeWindows(cindex, ind, spi)
	nevts=dat.shape[1]
	dat=reshape(dat, (bins, spb, nevts))
	dat=sum(dat, 1)
	ns={}
	q=sum(dat)
	for i, n in enumerate(q):
		if not ns.has_key(n):
			ns[n]=[]
		ns[n].append(i)
	nclass=len(ns)	
	if ns.has_key(0):
		p=float(len(ns[0]))/nevts
		rposib=float(nevts)/bins
		print "%i -> %.3f" % (0, p)
		del(ns[0])
	else:
		rposib=0.0
	isidist=zeros((bins+2,len(ns)), Float32)
	for i, k in enumerate(ns.keys()):
		p=float(len(ns[k]))/nevts
		print "%i -> %.3f" % (k, p)
		isidist[0,i]=k
		isidist[1,i]=p
		insts=take(dat, ns[k], 1)
		isidist[2:,i]=sum(insts, 1)/insts.shape[1]
	isids=DataSet(isidist, {"SamplesPerSecond":ds.fs/spb})
	isids.special['psib']=rposib
	ds.special[sKey]=isids
	return ds

#sysID

def lagSelect(ds, chanS=0, chanE=1, sKey='LagStats', numBootstraps=20, maxLags=40, momentWeight=[1.0,1.0,1.0,0.0]):
	''' '''
	stim=ds.getChannel(chanS)
	ucdist=zeros((numBootstraps, 4), Float32)
	for i in range(numBootstraps):
		substim=take(stim, randint(0,stim.shape[0],stim.shape[0]))
		me=substim.mean()
		st=substim.stddev()
		skew=(((substim-me)/st)**3).sum()/substim.shape[0]
		kurt=(((substim-me)/st)**4).sum()/substim.shape[0] - 3
		ucdist[i,:]=array([me,st,skew,kurt])
	ucdist=concatenate([mean(ucdist), std(ucdist)])	
	print ucdist
	ind = nonzero1d(ds.getChannel(chanE))
	ind-=maxLags
	dat=ds.takeWindows(chanS, ind, maxLags)
	return ds


#specialpurpose


def checkCovar(ds, sKeyEnsemble='EvtCond'):
	'''Calculate and save the covar, second moment, and difference'''
	ens=transpose(ds.special[sKeyEnsemble].data)
	sm=dot(transpose(ens), ens)/(ens.shape[0]-1)
	moe=mean(ens,0)
	emz=ens-moe
	cov=dot(transpose(emz), emz)/(emz.shape[0]-1)
	dif=sm-cov
	return ds

#disabled


def isiHistoryToKey(ds, cindex=0, length=5, mode='isi', sKey='isiHistory'):
	'''Produces a matrix of event conditioned waveforms, similar to eventConditionedWavesTosKey,
	However, the waveforms are drawn from the same (discrete) channel that they are conditioned 
	on, and are in the space of inter-spike intervals. There are two modes: 'isi' and 'time'.
	In isis mode, length is an integer specifying the number of isis to record, and each
	channel in the result will have this length. In time mode, length specifies the amount of time
	to look before the event. The length of the output rows will be determined by the largest 
	number of isis that occur in this window. For other events, rows corresponding to 
	isis that did not occur in the window will be set equal to length.'''
	rast=ds.getChannel(cindex)
	thresh = (rast.max()-rast.min())/2.0
	ind = nonzero1d(rast>thresh)
	ind=ind.astype(Float32)/ds.fs
	isi=(ind-shift(ind, 1))[1:]
	if mode=='isi':
		ec=zeros((length, len(isi)-length), Float32)
		for i in range(ec.shape[1]):
			ec[:,i]=isi[i:i+length]
	else:
		print "not implemented yet"	
		length=int(round(length*ds.fs))
	ds2=DataSet(ec)
	ds.special[sKey]=ds2
	return ds

def smoothedEventHistoryToKey(ds, cindex=0, length=0.020, lead=0.020, smoothWidth= .001, sKey="EventHistory") :
	'''Produces a matrix of event conditioned waveforms, similar to eventConditionedWavesTosKey,
	However, the waveforms are drawn from the same (discrete) channel that they are conditioned 
	on. In addition, the extracted waveforms are convolved with a gaussian of sigmo=smoothWidth'''
	rast=ds.getChannel(cindex)
	thresh = (rast.max()-rast.min())/2.0
	ind = nonzero1d(rast>thresh)
	ind-=int(round(lead*ds.fs))
	length=int(round(length*ds.fs))
	sig=int(round(smoothWidth*ds.fs))
	if sig<1:
		print "warning, smoothWidth is too small. No smoothing will occur"
	else:
		filt=arange(-3*sig, 3*sig)
		filt=filt.astype(Float32)
		filt=(1/(2.5066*sig))*exp((-1*filt**2)/(2*sig**2))
		rast=convolve(rast, filt, mode=SAME)
	ind=sort(take(ind, nonzero1d( logical_and(ind>=0, (ind+length)<rast.shape[0]))))
	new=zeros((length, len(ind)), ds.data.dtype.char)
	for i, c in enumerate(ind):
		new[:,i]=rast[c:c+length]
	ds2=DataSet(new)
	ds2.fs=ds.fs
	ds.special[sKey]=ds2
	return ds
	
#coherence


def getBode(ds, channelsin, channelsout, sKey='bode'):
	'''calculate the bode plot from channelsin to channelsout
	(1 or 2 channels each), and store it in sKey, as a Nx3 array with
	columns containing: freq, amp, phase'''
	if len(channelsin) == 1:
		idat = ds.channel(channelsin[0])
	elif len(channelsin) == 2:
		idat = take(ds.data, channelsin, 1)
		idat = ones(idat.shape[0], Complex32)*idat[:,0]+1j*idat[:,1]
	if len(channelsout) == 1:
		odat = ds.channel(channelsout[0])
	elif len(channelsout) == 2:
		odat = take(ds.data, channelsout, 1)
		odat = ones(odat.shape[0], Complex32)*odat[:,0]+1j*odat[:,1]	
	freq, amp, phase =  bode(idat, odat, ds.fs)
	ds.special[sKey]=transpose(array([freq, amp, phase]))
	return ds

def compareBode(ds, sKeyBode='bode', standard='BODE10_3SOMARin', sKeyError='Error'):
	'''calculate error between the bode plot stored in sKeyBode and the
	internal reference specified by standard. Addd the resulting error to
	sKeyError (creating the key with an initial value of 0 if needed'''
	bode=ds.special[sKeyBode]
	ind=nonzero1d(bode[:,0]>360)[0]
	bode= bode[:ind+1,:]
	b=bracket(bode[:,0], 1.0)
	if type(b)==int:
		bode=bode[b:,:]
	else:
		bode=bode[b[0]:,:]
		bode[0,0]=1.0
		bode[0,1:]=bode[0,1:]+(bode[1,1:]-bode[0,1:])*b[1]
	bode=uniformsample(bode, 4)[:90]
	standard=eval(standard)
	if standard.shape[1]==1:
		bode=bode[:,0]
	diff=(standard-bode)**2
	ds.special[sKeyError]=diff.sum()
	return ds
	

def makeOverlay(ds, sKeyBode='bode', standard='BODE10_3SOMARin'):
	bode=ds.special[sKeyBode]
	ind=nonzero1d(bode[:,0]>360)[0]
	bode= bode[:ind+1,:]
	b=bracket(bode[:,0], 1.0)
	if type(b)==int:
		bode=bode[b:,:]
	else:
		bode=bode[b[0]:,:]
		bode[0,0]=1.0
		bode[0,1:]=bode[0,1:]+(bode[1,1:]-bode[0,1:])*b[1]
	bode=uniformsample(bode, 4)[:90]
	standard=eval(standard)
	if standard.shape[1]==1:
		bode=bode[:,0]
	diff=(standard-bode)**2
	print diff.sum()
	ds.data=bode
	ds.labels=['Measured Amp', 'Measured Phase'][:bode.shape[1]]
	ds.fs=4.0
	ds.start=1.0
	ds.special={}
	ds.addchannel('Standard Amp',standard[:,0])
	if standard.shape[1]==2:
		ds.addchannel('Standard Phase', standard[:,1])
	return ds
	
#celltypes



def random(ds, rate=100):
	'''generate random events at rate (Hz)'''
	t = ds.domain()
	howmany=int(round((t[-1]-t[0])*rate))
	f = uniform(t[0], t[-1], howmany)
	c=zeros(ds.data.shape[0], ds.data.dtype.char)
	ind=ds.setChannel(-1, c)
	ds.setRaster(ind, f)
	return ds

def isiDistribution(ds, sKey='isidist'):
	'''generates random events with a particular isi distribution (specified
	in an sKey)'''
	mt=ds.data.shape[0]*ds.fs
	dist=ds.special[sKey]
	dx=1.0/dist.fs
	isis=arange(dist.data.shape[0])*dx+dist.start+.5*dx
	expisi=dist.data[:,0]*isis
	expisi=expisi.sum()/dist.data[:,0].sum()
	dur=ds.domain()
	dur=dur[1]-dur[0]
	nspikes=dur/expisi
	nspikes = int(nspikes+.1*nspikes)
	isis = drawFromHist(nspikes, dist.data[:,0])
	isis = isis*dx+.5*dx
	spikes=cumsum(isis)+ds.start
	toobig=nonzero1d(spikes>=ds.domain()[1])
	if len(toobig)>0:
		spikes=spikes[:toobig[0]]
	c=zeros(ds.data.shape[0], ds.data.dtype.char)
	ind=ds.setChannel(-1, c)
	ds.setRaster(ind, spikes)
	return ds

	

	
def poisson(ds, fname='rate.pydat'):
	''' '''


def refractoryPoisson(ds, cindexGenerator=0, nreps=1, threshold=.5, max=1.0, refractMag=.5, refractTao=.002, addResults=False):
	'''generate a random sequence ranging from threshold to max. If Generator is 
	greater than this value, create an event. Modify the event sequence to include
	refractory effects as follows:
	For ease of optimization, threshold and refractMag are expressed as fractions of
	max, so, e.g. if max = 2.0 and threshold = .5 a threshold of 1 is used.
	For each event, reduce the generator by refractMag*exp(-dt/refractTao) where dt
	is the time (seconds) since the last event. If this reduces G below the random value,
	remove the event.
	repeat the procedure nreps times, adding a new channel for each set of spikes.
	If nreps is greater than one, and addResults is true, produce a single output channel 
	that is the sum of nreps separate realizations.'''
	dp=ds.getChannel(cindexGenerator)
	threshold=max*threshold
	refractMag=max*refractMag
	for rep in range(nreps):
		thresh=uniform(threshold, max, dp.shape)
		evts=nonzero1d(dp>thresh)
		if len(evts)>0:
			new=[evts[0]]
			ts=refractTao*ds.fs
			diffs=take(dp-thresh, evts)
			for ind in range(1, len(evts)):
				dt=evts[ind]-new[-1]
				pen=refractMag*exp(-dt/ts)
				if diffs[ind]>pen:
					new.append(evts[ind])
			evts=array(new)		
			new=zeros(dp.shape, dp.dtype.char)
			put(new, evts, 1)
		else:
			new=zeros(dp.shape, dp.dtype.char)
		print int(new.sum())	
		if rep==0 or not addResults:
			ochannelindex=ds.setChannel(-1, new)
			ds.labels[ochannelindex]="rp_%i_%i" % (cindexGenerator, rep)
		else:
			ds.data[:,ochannelindex]+=new
			
def lif(ds, cnameDP=0, cnameSpikes=-1, refract=1.0, leak=1.0, threshold=.5, rnoise=0):
	'''Use cnameDP as a driver potential for a leaky integrate and fire model. 
	Place the output spike train in cnameSpikes. 
		Refract: The amount to reduce the driver potential when an event
			occurs
		Leak: The "current" which returns the accumulated potential to
			0. Units are in exitation units per dP per second
		Threshold: The potential at which events trigger
		rnoise: The stdev of the distribution of Refract (default 0) '''
	leak=leak/ds.fs
	nei = []
	v=0
	vdp = ds.getChannel(cnameDP)/ds.fs
	storev = []
	for i in range(vdp.shape[0]):
		v+= vdp[i]
		v-= v*leak
		storev.append(v)
		if v>= threshold:
			nei.append(i)
			v-=refract
			if 	rnoise:
				v -= normal(0, rnoise)
	ind=ds.setChannel(cnameSpikes, zeros(ds.data.shape[0], ds.data.dtype.char))
	if len(nei)==0:
		storev = array(storev)
		print "No Events", storev.max(),  storev.mean()
	else:
		nei=array(nei)
		put(ds.data[:,ind], nei, 1.0)
		if len(nei)>1:
			delays=nei[1:]-nei[:-1]
		else:
			delays=array([0.0,1])
		print len(nei), delays.min(), 1.0/delays.mean()
	return ds
	

	

def Filter(ds, cindexInput=0, cindexOutput=-1, sKey="Kernel", filterChannel=0):
	'''extracts a kernel from the indicated key and applies one channel (by default the 
	first one, as a filter to the specified channel of ds, stering the result in 
	the indicated output index (by default, a new channel)'''
	filt=ds.special[sKey]
	filt = filt.data[:,filterChannel]
	filt = reverseArray(filt)
	dat = convolve(ds.data[:,cindexInput], filt, mode=SAME)
	ind=ds.assignChannel(cindexOutput, dat)
	ds.labels[ind]="Filter_%s" % sKey
	return ds

