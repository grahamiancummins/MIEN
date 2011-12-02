
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

#import mien.nmpml.data
#reload(mien.nmpml.data)
from mien.nmpml.data import *
import time



def arrayGetData(dat, chans=None, range=None, copy=False):
	'''duplicates the Data.getData method for an array'''
	if chans:
		if type(chans)==int:
			chans=[chans]
		dat=take(dat, chans, 1)
	if range:
		s=genslice(range, dat.shape[0])
		dat=dat[s]
	if copy:
		dat=dat.copy()
	return dat	

def isSampledType(data):
	'''Returns "e" for events and labeledevents, "s" for timeseries, ensemble, 
and histogram, and False for other types'''
	print data
	if data.stype() in ['events', 'labeledevents']:
		return 'e'
	elif data.stype() in ['ensemble', 'histogram', 'timeseries']:
		return 's'
	return False	
	

def selectEvents(evts, chans, ran):
	'''Selects data from events and labeldevents Data instances 
Only events in the indicated range are returned. 
For "events" data, a 1D array is returned no matter what value is given to 
chans
For labeledevents, different labels are treated as different channels. If chans
has one element (or is type int), the return result will be a 1D array of events 
for a single source. If sel[1] has more than one element, the result is always an 
Nx2 array (just like the origional labeledevents), but only contains rows with labels 
included in chans.
'''
	evd=evts.getData()
	if ran:
		ml=evd[:,0].max()+1
		ran= genslice(ran, ml)
		sa=ran.start or 0
		ind=nonzero1d(logical_and(evd[:,0]>=sa, evd[:,0]<=ran.stop))
		evd=take(evd, ind)
	if chans and evts.stype()=='labeledevents':
		if len(chans)==1:
			chans=chans[0]
		if type(chans)==int:
			evd=take(evd[:,0], nonzero1d(evd[:,1]==chans))
		else:
			ne=None
			for ci in chans:
				n=take(evd, nonzero1d(evd[:,1]==ci), 0)
				if n.shape[0]>0:
					if ne==None:
						ne=n
					else:
						ne=concatenate([ne, n])
			if ne==None:
				ne=zeros((0,2))
			evd=ne
	return evd	


def getLabeledEvent(evts, lab):
	'''Returns a Data instance of sample type "events" containing the events in evts, of sample type labeledevents, in channel "lab" '''
	evd=evts.getData()
	evd=take(evd[:,0], nonzero1d(evd[:,1]==lab), 0)
	h=evts.header()
	h['SampleType']='events'
	h['Labels']=[evts.getLabels()[lab]]
	return newData(evd, h)
			
		
def getOrCreate(ds, path):
	sd=ds.getSubData(path)
	if not sd:
		sd=ds.createSubData(path)
	return sd	
			
def assignEvents(evts, values, chans, ran):
	'''Inverse of selectEvents, except that if evts is of type "events", and 
chans is not None, evts will be converted to type labeledevents (all events 
will have label chans[0] if values is 1d)'''
	if values==0.0 or values==None or len(values.shape)<1:
		if chans or evts.stype()=='labeledevents':
			values=zeros((0,2))
		else:
			values=zeros((0,1))
	old=[]
	evd=evts.getData()
	head=evts.header()
	if ran:
		ran= genslice(ran, evd[:,0].max()+1)
		sa=ran.start or 0
		if sa:
			old.append(take(evd, nonzero1d(evd[:,0]<sa), 0))
		if ran.stop<evd[:,0].max():	
			old.append(take(evd, nonzero1d(evd[:,0]>ran.stop), 0))
		ind=nonzero1d(logical_and(evd[:,0]>=sa, evd[:,0]<=ran.stop))
		evd=take(evd, ind)
	if chans and evts.stype()=='events':
		head['SampleType']=='labeledevents'
		if type(chans)!=int:
			chans=chans[0]	
		for a in old:
			values=concatenate([values,a])
		new=ones((values.shape[0], 2), values.dtype)*chans
		new[:,0]=values	
	elif chans:
		if len(chans)==1:
			chans=chans[0]
		if type(chans)==int:
			old.append(take(evd[:,0], nonzero1d(evd[:,1]!=chans)))
		else:	
			all=set(evd[:,1])
			chans=all.symmetric_difference(set(chans))
			for ci in chans:
				old.append(take(evd, nonzero1d(evd[:,1]==ci)))			
	for a in old:
		values=concatenate([values,a])
	new=values
	evts.datinit(new, head)

def getSelection(data, sel, evts2ts=False):
	'''Returns a block of data specified by sel. Sel is a 3 tuple. Any element may be None, resulting in a default selection. The indicies work as follows:
	
	sel[0] - None or string - the dpath of the subdata element to select. None uses the instance passed as "data" (this isn't always identical to "/")
	sel[1] - None or int or sequence of ints. Specifies the channels to select. A single int x is converted to the trivial sequence [x]. None selects all channels
	sel[3] - None, range, or tuple. This is interpreted as in mien.nmpml.data.Data.getData

	Selection on events uses selectEvents (which acts differently than some other functions including channel and Data.getData)

	if "sel" is a numerical array, it is returned unchanged. This allows some  functions a greater degree of polymorphism, but should be used with caution.

	Selection on ensembles will still return a 2D array of width  data.attrib('Reps')*len(s[1])

	If evts2ts is True, and the target is of event data type, convert it to a time series of zeros and ones'''
	if type(sel)==ArrayType:
		return sel
	sd, chan, ran = sel
	if sd:
		print sd, data
		print 'chans=',chan, ran, data.getSubData(sd)
		data = data.getSubData(sd)
	if isSampledType(data)=='e':
		if not evts2ts:
			return selectEvents(data, chan, ran)
		dat=events2ts(data)
		return arrayGetData(dat, chan, ran)
	elif data.stype()=='ensemble':
		r=data.attrib('Reps')
		c2=[]
		if type(chan)==int:
			chan=[chan]
		for ci in chan:
			cis=range(ci*r, ci*r+r)
			c2.extend(cis)
		chan=c2	
	return data.getData(chan, ran)
			
def setSelection(data, value, sel):
	'''Inverse of getSelection'''
	sd, chan, ran = sel
	if sd:
		data=data.getSubData(sd)
	if isSampledType(data)=='e':
		assignEvents(data, value, chan, ran)
		return
	elif data.stype()=='ensemble':
		r=data.attrib('Reps')
		c2=[]
		if type(chan)==int:
			chan=[chan]
		for ci in chan:
			cis=range(ci*r, ci*r+r)
			c2.extend(cis)
		chan=c2	
	data.setData(value, chan, ran)
	
	

def deleteSelection(data, sel, compress=False):
	'''Deletes the data specified in sel if possible. If sel is (path, None, None) 
this removes the entire element, unless it has child elements. Note that if both 
channell and range are specified, deletion is possible only for event type data.'''
	if not (sel[1] or sel[2]):
		d=data.getSubData(sel[0])
		if not d.getElements('Data'):
			d.sever()
		else:
			h=d.header()
			h['Labels']=[]
			dat=zeros((0,0))
			d.datinit(dat, h)
		return 
	sd=data.getSubData(sel[0])	
	if 'events' in sd.stype():
		ran=genslice(sel[2], sd.shape()[0])
		ran=(ran.start or 0.0, ran.stop)
		dat=sd.getData()
		head=sd.header()
		if 'labeled' in sd.stype():
			chans=sel[1]
			labs=sd.getLabels()
			if chans:
				newlabs=[]
				cl=[i for i in range(dat[:,1].max()+1) if not i in chans]
				for ci in cl:
					newlabs.append(labs[ci])
					mask=logical_or(mask, dat[:,1]==ci)
				labs=newlabs
			head['Labels']=labs	
		if not compress:			
			mask=logical_or(dat[:,0]<ran[0], dat[:,0]>ran[1])	
			evts=take(dat,nonzero1d(mask), 0)
		else:
			e1=take(dat,nonzero1d(dat[:,0]<ran[0]), 0)
			e2=take(dat,nonzero1d(dat[:,0]>ran[1]), 0)
			e2-=(ran[1]-ran[0])
			evts=vstack([e1, e2])	
		sd.datinit(evts, head) 		
	else:
		dtbd=getSelection(data, sel)
		all=sd.getData()
		if dtbd.shape==all.shape:
			deleteSelection(data, (sel[0], None, None))
		elif dtbd.shape[0]==all.shape[0]:
			sd.delChans(sel[1])			
		elif dtbd.shape[1]==all.shape[1]:
			ran= genslice(sel[2], all.shape[0])
			begin=end=None
			if not ran.start:
				sd.crop(ran)
				return	
			if ran.stop<all.shape[0]:
				end=all[ran.stop:]
			else:
				end=None
			sd.crop((0, ran.start))
			if end!=None:
				sd.concat(end)
		else:
			print "can't delete 'hole'"

		
def getRangeFromSelect(data, select):
	'''Return a tuple (start, stop) for the range specified in select'''
	dat=data.getSubData(select[0])
	ran=genslice(select[2], dat.shape()[0])
	sa=ran.start or 0
	return (sa, ran.stop)
		
def getSelectionHeader(data, select):
	'''Return an appropriate header for data acquired using getSelection'''
	h={}
	if type(select)==ArrayType:
		dat=data
		select=(None, None, None)
	else:	
		dat=data.getSubData(select[0])
	h['SamplesPerSecond']=dat.fs()
	h['SampleType']=dat.stype()
	labs=dat.getLabels()
	if select[1]:
		labs=[labs[i] for i in select[1]]
	h['Labels']=labs
	if isSampledType(dat)=='s':
		sa=dat.start()
		si=getRangeFromSelect(data, select)[0]
		sa=sa+(si/dat.fs())
		h['StartTime']=sa
	return h	
		
def blankTimeSeries(shape, h={}):
	'''2Tuple, dict  => instance
return a Data instance with the indicated shape and header, containing all
Float32 zeros, if h doesn't have a key "SamplesPerSecond, that is set to
1.0'''
	default={'SamplesPerSecond':1.0, 'Labels':["c%i" % i for i in range(shape[1])], 
	'StartTime':0.0}
	for k in default:
		if not h.has_key(k):
			h[k]=default[k]
	h['SampleType']='timeseries'		
	dat=zeros(shape, Float32)
	return newData(dat, h)
	
def resample(data, fs, interp=True):
	'''Change the sampling rate of data to fs. Adjust data accordingly. For timeseries sampled data, the data is resampled using the parameter "interp". Set this to True for linear interpolation and False for sample and hold.'''
	st=data.stype()
	dat=data.getData()
	h=data.header()
	if not fs:
		if not st=='function':
			return
		else:
			dx=(dat - shift(dat, 1))[1:, 0].min()
			fs=1.0/dx
	if data.fs()==fs:
		return
	h['SamplesPerSecond']=fs
	if st=='function':
	 	dx = 1.0/fs
	 	h['SampleType']='timeseries'
 		dat = uniformsample(dat, dx, interp)
	elif isSampledType(data)=='s': 
		oldfs=data.fs()
		chans=[]
 		for i in range(dat.shape[1]):
 			chans.append(array_resample(dat[:,i], 1.0/oldfs, 1.0/fs, interp))
 		dat=transpose(array(chans))	
 	elif isSampledType(data)=='e':
 		times=round(fs*dat[:,0].astype(float64)/float(data.fs()))
 		if not dat.dtype.char in [Int64, Int32]:
 			dat=dat.astype(Int64)
 			dt=Int64
 		else:
 			dt=dat.dtype.char
 		dat[:,0]=(times).astype(dt)
	else:
		raise ValueError("Data instance is not a type that can be resampled")
	data.datinit(dat, h)
	
def pts2ts(pts, sort=True, interp=True):
	'''Convert a 2D array of explicit points to a timeseries Data element. The first column in the array is taken as the independant variable, and all subsequent columns as channels (different dependant variables). The sampling rate is set to maintain the smallest intersample increment in the dependent variable, and the whole data set is resampled to this interval. The attribute "StartTime" is set to the first sample. By default, this function sorts the samples in order of increasing independent variable. If the samples are already sorted, specifying sort=False can save some time. The interp parameter is passed downstream to the resample function.'''
	if sort:
		a=argsort(pts[:,0])
		pts=take(pts, a, 0)
	st=pts[0,0]	
	d=newData(pts, {"SampleType":'function', 'StartTime':st})	
	resample(d,None, interp)
	return d

def setstart(data, sa):
	'''Sets the start time of data to sa, and corrects the values appropriatly'''
	if not isSampledType(data):
		return
	if data.start()==sa:
		return
	osa=data.start()
	if isSampledType(data)=='s':
		dt=osa-sa
		si=int(round(dt*data.fs()))	
		if si>0:
			fill=zeros((si, data.shape()[1]), data.dtype())
			data.concat(fill, prefix=True)
		else:
			data.crop((si, ':'))
		data.setAttrib('StartTime', sa)	
		return
	elif isSampledType(data)=='e':	
		dt=sa-osa
		si=int(round(dt*data.fs()))	
		ni=data.getData([0])-si
		if all(ni>=0):
			data.setAttrib('StartTime', sa)
			data.setData(ni,[0])
		else:
			ni=take(ni, nonzero1d(ni[:,0]>=0))
			h=data.header()
			h['StartTime']=sa
			data.datinit(ni, h)

	
def channel(data, i):
	'''returns the channel (column) of data with index i, or, if i is a 
string, the column with Label i, or if i is a tuple or list, use i[0] as 
a dpath, get that sub-element, and return channel(i[1]) for it.

For events and labledevents, returns the entire data array. For 
ensembles, returns a 2D array o all the records for a given channel'''
	if type(i) in [list, tuple]:
		data=data.getSubData(i[0])
		i=i[1]
	if isSampledType(data)=='e':
		return data.getData()	
	if type(i) in [str, unicode]:
		l=data.getLabels()
		if i in l:
			i=l.index(i)
		else:
			return None
	if data.stype()=='ensemble':
		r=data.attrib('Reps')
		i=i*r
		d=data.getData()[:,i:i+r]
	else:	
		d=data.getData([i])
	return d
	
def flattenEnsembleChannels(data):
	'''If data is of sample type "ensemble", and has several channels, returns an array which contains one column for each rep in data, where each column is a concatenation of the values in each channel.'''
	if not data.stype()=='ensemble':
		raise StandardError("flattenEnsembleChannels only works with ensemble data")
	r=data.attrib('Reps')
	nsamp, nchan = data.shape()
	d=data.getData()
	nsamp=d.shape[0]
	nchan = d.shape[1]/r
	d=reshape(d, (nsamp, nchan, r))
	d=reshape(transpose(d, [1,0,2]), (nsamp*nchan,r))
	return d
		
def domain(data):
	'''Return a tuple (min, max) specifying the domain of the independent 
variable of data. If data's "fs" method returns a false value, asumes that 
the first column contains explicit measures of the independant variable.''' 	
	fs=data.fs()
	sa=data.start()
	if fs:
		sp=sa+data.shape()[0]/fs
	else:
		sp=data.getData()[:,0].max()
	return (sa, sp)
	
	
	
def yrange(data, chan, range=None):
	if type(chan) in [tuple, list]:
		data=data.getSubData(chan[0])
		chan=chan[1]
	if isSampledType(data)=='e':
		return (0.0, 1.0)	
	c=data.getData([chan], range)
	if data.stype()=='histogram':
		bin=data.attrib('BinWidth') or 20
		if bin!=1:
			rem=c.shape[0]%bin
			if rem:
				c=c[:-rem]
			c=sum(reshape(c, (-1, bin)), 1)	
		return (0, c.max())
	else:
		return (c.min(), c.max())
	
def events2ts(evts, l=None, start=None):
	'''Return a full timeseries of zeros and ones containing ones where the 
events in evts occur. If evts is of type "labeledevts" there will be as many 
columns as the largest event label, otherwise there will be one column. The 
sampling rate of evts is maintained. By default, the new array starts at 
sample zero (the first one is at exactly the smallest index listed in evts)
and runs just long enough to include the last event. If l is specified, 
the output array will have exactly l rows. If start is specified, it is 
interpreted as a time, and the first row of the array coresponds to that 
time.'''
	ed=evts.getData()	
	ed=ed.astype(Int32)
	if not ed.shape[0]:
		if l:
			return zeros((l,1))
		else:
			return zeros((1,1))			
	if start!=None:
		osa=evts.start()
		dt=start-osa
		si=round(dt/evts.fs())
		ed[:,0]-=si
	if l==None:
		l=int(ed[:,0].max()+1)	
	if not 'labled' in evts.stype():
		a=zeros((l,1))
		put(a, ed, 1)
		return a
	w=int(ed[:,1].max()+1)
	a=zeros((l,w), ed.dtype)
	for ci in range(w):
		ind=take(ed[:,0], nonzero1d(ed[:,1]==ci))
		put(a[:,ci], ind, 1)
	return a	
		

def compatLength(d1, d2):
	resample(d2, d1.fs()) 
	setstart(d2, d1.start())	
	if isSampledType(d1)=='s' and isSampledType(d2)=='s':
		ld=d1.shape()[0]-d2.shape()[0]
		if ld>0:
			fill=zeros((ld, d2.shape()[1]), d2.dtype())
			d2.concat(fill)
		elif ld<0:
			fill=zeros((abs(ld), d1.shape()[1]), d1.dtype())
			d1.concat(fill)




def combineData(d1, d2, copy=True):
	if copy:
		d2=d2.clone()
		kill=False
	else:
		kill=True
	if isSampledType(d1)=='e' and isSampledType(d2)=='e':
		compatLength(d1, d2)
		if d1.stype()=='events':
			dat=d1.getData()
			h=d1.header()
			dat=concatenate([dat, zeros(dat.shape, dat.dtype)], 1)
			h['SampleType']='labeledevents'
			d1.datinit(dat, h)
		q=d1.getData([1]).max()+1	
		if 	d2.stype()=='events':
			l=[d2.getChanName(0)]
			dat=d2.getData()
			ind=ones(dat.shape, dat.dtype)*q
			dat=concatenate([dat, ind], 1)
		else:
			l=d2.getLabels()
			dat=d2.getData()
			dat[:,1]+=q
		d1.concat(dat)
		d1.setAttrib('Labels', d1.getLabels()+l)
	elif d1.stype()!=d2.stype():
		if d1.stype=='histogram' and isSampledType(d2)=='e':
			evd=events2ts(d2, l=d1.shape()[0], start=d1.start())
			if evd.shape[1]!=d1.shape()[1]:
				evd=reshape(sum(evd, 1), (-1, 1))
				d1.setData(channel(d1, 0)+evd, [0])
			else:
				d1.setData(d1.getData()+evd)
		else:
			if isSampledType(d2)=='e':
				compatLength(d1, d2)
			d2.move(d1)
			kill=False			
	elif d1.stype()=='histogram':
		compatLength(d1, d2)
		if d2.shape()==d1.shape():
			d1.setData(d1.getData()+d2.getData())
		else:
			dat=d2.getData()
			dat=reshape(sum(dat, 1), (-1, 1))
			d1.setData(channel(d1, 0)+dat, [0])
	elif d1.stype()=='timeseries' or (d1.stype()=='ensemble' and d1.attrib('Reps')==d2.attrib('Reps')):
 		compatLength(d1, d2)
 		nl=d2.getLabels()
 		onl=d1.getLabels()
 		for i in range(len(nl)):
 			l=nl[i]
			ui=2
			bn=l
 			while l in onl:
				if not d2.name() in l:	
 					l=bn+"_"+d2.name()
				else:
					l=bn+"_"+d2.name()+"_"+str(i)
					i+=1
			nl[i]=l
		d1.addChans(d2.getData(), nl)
	elif d1.stype()=='locus' and d1.shape()[1]==d2.shape()[1]:
		d1.concat(d2.getData())
	else:
		d2.move(d1)	
		kill=False
	if kill:
		d2.sever()

def getDataList(data, types, depth, hide=["hidden"], samelength=False):
	if data==None:
		return []
	if isSampledType(data):
		length=data.shape()[0]
		fs = data.fs()
	else:
		length=None
		fs = None
	ad=data.getHierarchy(below=True, order='wide')
	chans=[]
	pref=data.dpath()
	nlev=pref.count('/')
	for dn, di in ad:
		if dn.count('/')-nlev>depth:
			continue
		if any([pat in dn for pat in hide]):
			continue	
		if not di.stype() in types:
			continue
		if isSampledType(di)=='e':
			if di.getChanName(0):
				chans.append([di.getChanName(0), di.stype(), (di.dpath(), 0)])
		elif isSampledType(di) and fs == None:
			fs = di.fs()
			length = di.shape()[0]
		elif isSampledType(di) and ((di.fs()!=fs)):
			continue
		elif samelength and isSampledType(di) and di.shape()[0]!=length:
			continue
		else:	
			for ci in range(di.shape()[1]):
				chans.append([di.getChanName(ci), di.stype(), (di.dpath(), ci)])
	names=[]
	for c in chans:
		n=c[0]
		if n in names:
			n= "%s (%s %i)" % (n, c[2][0], c[2][1])
			c[0]=n
		names.append(n)	
	return chans	
	
def alignEvents(ds, select, dpath, bpad=0, epad=0):
	'''return event indexes aligned to the data in select. Events are 
returnd as a 1D Int array.
	
This function corrects for differences in start times, sample rates,
select range offsets, etc. The returned events are indexes into the
block of data that would be returned by getSelection(ds, select). If
dpath references labledevents, _all_ the event indexes are returned in a
single 1D array (which is not guaranteed to have unique values)!

If bpad and/or epad are nonzero, return only events that are at least bpad
samples after the start of select and epad samples before the end
'''
	dat=ds.getSubData(select[0])
	evts=ds.getSubData(dpath).clone(False)
	resample(evts, dat.fs())
	sa, spi=getRangeFromSelect(ds, select)
	if not evts.start()==dat.start():
		setstart(evts, dat.start())
	evts=evts.data[:,0]
	end=spi-epad
	mask=nonzero1d(logical_and(evts>sa+bpad, evts<end))
	evts=take(evts, mask)
	return evts

def xcoord(data, index):
	'''Return the (float) value of time at the specified index'''
	sa=data.start()
	fs=data.fs()
	return sa+index/fs()
	
	
def xindex(data, coord):
	sa=data.start()
	fs=data.fs()
	return round(coord*fs - sa*fs)
	

def distribute(chans):
	d={}
	for c in chans:
		if not type(c) in [list, tuple]:
			p='/'
			i=c
		else:
			p, i=c
			if not p:
				p='/'
		if not d.has_key(p):
			d[p]=[]
		d[p].append(i)	
	return d	
	
def delChans(data, chans):
	d=distribute(chans)
	for k in d.keys():
		chans=d[k]
		if not chans:
			continue
		dat=data.getSubData(k)
		if not dat:
			continue
		if isSampledType(dat)=='e' or len(chans)==dat.shape()[1]:
			dat.sever()
		else:
			dat.delChans(chans)
				
def crop(dat, range):
	if isSampledType(dat)=='s':
		dat.crop(range)
	elif isSampledType(dat)=='e':
		ml=dat.getData([0]).max()+1
		range= genslice(range, ml)
		sa=range.start or 0
		ed=dat.getData()
		ind=nonzero1d(logical_and(ed[:,0]>=sa, ed[:,0]<=range.stop))
		ed=take(ed, ind)
		dat.datinit(ed, dat.header())
	else:
		print "Can't crop this sample type"

def makeEventData(evts, fs=1.0):
	"""Return a data element containing the events in the 1D collection evts. These events are assumed to be represented as explicit times, and are resampled to be represented with a uniform sampling rate fs"""
	evts=reshape(array(evts), (-1, 1))
	evts.sort(0)
	st=evts[0,0]
	evts-=st
	h=newHeader('events',fs, ['Events'], st)
	evts=round(fs*evts)
	return newData(evts,h)		

# 	def shiftChannels(self, chans, si, interp=False):
# 		'''Shift each specified channel by si units to the right (to
# higher values of x). Si has the same units as the (implied) x
# coordinate of the dataset. If interp is false, the shift is by the closest
# integer number of samples to the requested continuous shift. If interp is true
# linear interpolation is used to insure that the shift is by the exact amount
# requested (this may be quite slow for some combinations of si and self.fs)
# 		'''
# 		if len(chans)==self.data.shape[1]:
# 			self.start += si
# 		else:
# 			isi = si*self.fs
# 			si = int(round(isi))
# 			for ci in chans:
# 				self.data[:,ci] = shift(self.data[:,ci], si)
# 			if isi%1.0 and interp:
# 				f=isi%1.0
# 				#print f
# 				inds=arange(self.data.shape[0])+f
# 				for ci in chans:
# 					dat=concatenate([self.data[:,ci], [self.data[-1,ci]]])
# 					dat=interpolate(dat, inds)
# 					self.data[:,ci] = dat[:self.data.shape[0]] 
# 
# 					
# 	def filter(self, ds, channels='all'):
# 		'''return a DataSet generated by applying ds as a filter to
# 		self. If ds has the same number of channels as the channels argument,
# 		each channel of ds is applied to the equivalent channel of self.
# 		Otherwise, the first channel is applied to each channel in channels'''
# 		if channels=='all':
# 			channels=range(self.data.shape[1])
# 		if ds.data.shape[1]==len(channels):
# 			for i, c in enumerate(channels):
# 				filt = ds.data[:,i]
# 				if ds.fs != self.fs:
# 					filt = array_resample(filt, 1.0/ds.fs, 1.0/self.fs)
# 				filt = reverseArray(filt)
# 				#print "filtering self %i" % i
# 				self.data[:,c] = convolve(self.data[:,c], filt, mode=SAME)
# 		else:
# 			filt = ds.data[:,0]
# 			if ds.fs != self.fs:
# 				filt = array_resample(filt, 1.0/ds.fs, 1.0/self.fs)
# 			filt = reverseArray(filt)
# 			for i in channels:
# 				self.data[:,i] = convolve(self.data[:,i], filt, mode=SAME)
# 		
# 	def foldWindows(self, chans, coords, length):
# 		'''chans is a list of strings of len self.data.shape[0], coords is an array of ints,
# 		length is an int'''
# 		coords=sort(take(coords, nonzero( logical_and(coords>=0, (coords+length)<self.data.shape[0]))))
# 		nnc = 0
# 		for c in chans:
# 			if c=="Keep":
# 				nnc+=len(coords)
# 			elif c in ["Average", "Sum"]:
# 				nnc+=1		
# 			elif c=="Stats":
# 				nnc+=2		
# 		newdat = zeros((length, nnc), self.data.dtype.char)
# 		ind = 0
# 		ncn=[]
# 		for i, c in enumerate(chans):
# 			if c=="Keep":
# 				for j, c in enumerate(coords):
# 					newdat[:,ind]=self.data[i,c:c+length]
# 					ind+=1
# 					ncn.append("%s%i" % (self.labels[i], j))
# 			elif c in ["Average", "Sum"]:
# 				dat=zeros(length, self.data.dtype.char)
# 				for ci in coords:
# 					try:
# 						dat+=self.data[ci:ci+length,i]
# 					except:
# 						print ci, dat.shape, self.data[ci:ci+length,i].shape						
# 				print dat	
# 				if c == "Average":
# 					dat=dat/len(coords)
# 				ncn.append(self.labels[i])
# 				newdat[:,ind]=dat
# 				ind+=1
# 			elif c=="Stats":
# 				block=self.takeWindows(i, coords, length)
# 				newdat[:,ind]=mean(block, 1)
# 				newdat[:,ind+1]=std(block, 1)
# 				ncn.append(self.labels[i])
# 				ncn.append("%s - std" % self.labels[i])
# 				ind+=2
# 		self.labels=ncn
# 		self.data=newdat
# 
# 	def takeWindows(self, channel, coords, length):
# 		'''coords is an array of ints'''
# 		coords=sort(take(coords, nonzero( logical_and(coords>=0, (coords+length)<self.data.shape[0]))))
# 		new=zeros((length, len(coords)), self.data.dtype.char)
# 		for i, c in enumerate(coords):
# 			new[:,i]=self.data[c:c+length, channel]
# 		return new	
# 			
# 	def getInfo(self):
# 		'''returns a string describing the contents of self'''
# 		s="DataSet: %s\n" % str(self.data.shape)
# 		for k in  ["labels", "fs",'start', 'extraheaders']:
# 			a=getattr(self, k)
# 			s+="%s : %s\n" % (k, str(a))
# 		s+="special:\n"
# 		for k in self.special.keys():
# 			s+="   %s : %s" % (str(k), str(self.special[k]))
# 		return s	
# 
# 	def setRaster(self, index, a):
# 		'''index(int), a(array of floats) -> None
# 		Set the cantents of channel "index" to be binary with ones at the times 
# 		specified in "a", if index is not an integer, appends a new channel using
# 		that value as a name'''
# 		inds=[]
# 		t=self.get_x()
# 		c=zeros(t.shape[0], t.dtype.char)
# 		if len(a.shape)>1:
# 			a=a[:,0]
# 		a = sort(a)
# 		evtind = 0 
# 		for i in range(len(t)):
# 			if t[i]>=a[evtind]:
# 				c[i]=1
# 				evtind+=1
# 				if evtind>=len(a):
# 					break
# 		if type(index)==int:	
# 			self.data[:,index] = c.astype(self.data.dtype)
# 		else:
# 			self.addchannel(index, c)
# 			
# 
# 	def getEvents(self, index, thresh=None, check=False, returnTimes=True):
# 		'''index(int), thresh(float=None), check(bool=False) -> array of floats
# 		Return an array of event times extracted from the channel with 
# 		"index". These are all the times for which the channel is greater than 
# 		thresh. If thresh is None, it gets set to halfway between the minimum and maximum
# 		of the channel. If check is True, an exception is raised if the indicated channel 
# 		is not binary. if returnTimes is false, return the indexes of the events, 
# 		rather than the x values'''
# 		if check:
# 			if not isBinary(self.channel(index)):
# 				raise StandardError("DataSet.getEvents called with checking on a non-binary channel")
# 		chan=self.channel(index)
# 		if thresh==None:
# 			thresh=(chan.max()+chan.min())/2.0
# 		ind = nonzero(chan>thresh)
# 		if returnTimes:
# 			ind = take(self.get_x(), ind)
# 		return ind
# 
# def eventsToHist(ds, fs):
# 	'''return an array contaning '''
# 	chans=[]
# 	starts=[]
# 	for d in range(self.data.shape[1]):
# 		dat=self.data[:,d]
# 		dat=dat[argsort(dat)]
# 		starts.append(dat[0])
# 		dat=makeRaster(dat, 1.0/fs)
# 		chans.append(dat)
# 	self.start=min(starts)
# 	self.fs=fs
# 	for i in range(len(chans)):
# 		s=starts[i]
# 		if s>self.start:
# 			pad=int((s-self.start)*fs)
# 			pad=zeros(pad)
# 			c=concatenate([pad, chans[i]])
# 			chans[i]=c
# 	ml=max([x.shape[0] for x in chans])
# 	for i in range(len(chans)):
# 		c=chans[i]
# 		if c.shape[0]<ml:
# 			c=concatenate([c, zeros(ml-c.shape[0])])
# 			chans[i]=c
# 	self.data=transpose(array(chans))
# 		 
# #======Signal Processing Functions for "DataSet" instances ==================
# 
# def isADataSet(ds):
# 	# This is a hack. isinstance(ds DataSet) should work, but doesn't
# 	try:
# 		cl = ds.__class__
# 	except:
# 		return False
# 	return str(cl) == str(DataSet)
# 
# 
# # used by dataproc
# 
# from mien.dsp.spikeanalysis import spikefind_alg_dict
# def spikedetect(df, chan, method, args):
# 	args=[df.data[:,chan]]+args
# 	s=apply(spikefind_alg_dict[method], args)
# 	return take(df.get_x(), s)
# 
# 
# def histDF(df, chan):
# 	'''returns a wieghted distribution of the independent var
# 	based on channel chan. E.g. if chan is 6 at a given time step,
# 	that 6 copies of that time will occur in the returned vector.
# 	(if chan is float valued it will be rounded to int)'''
# 	t = df.get_x()
# 	c = roundtoint(df.data[:,chan])
# 	l = []
#  	evts = nonzero(c)
# 	for i in evts:
# 		for j in range(c[i]):
# 			l.append(t[i])
# 	l=array(l)			
# 	return l
# 
# #used by mien
# 
# def rotateDS(ds, chans, deg):
# 	dat = ds.data.take(chans, 1)
# 	dat = rotate(dat, deg)
# 	ds.data[:,chans[0]] = dat[:,0]
# 	ds.data[:,chans[1]] = dat[:,1]
# 
# def dprojectDS(ds, dir):
# 	d = get_directional_projection(ds.data[:,:2], dir)
# 	d.setshape((-1,1))
# 	ds.data=d
# 	ds.labels=["%iProjection" % int(dir)]
# 	return ds
# 
# 
# def addGWNDS(ds, std, chans=None, seed=None, band=None):
# 	'''ds (DataSet), std (float), chans (list=None), seed (int = None),
# 	band(tubple=None) => None
# 	modifies a dataset ds in place by adding gausian noise to each channel
# 	in chans (if chans is false, acts on all channels).
# 	if seed is true, it is used to seed the random number generator before
# 	each add, resulting in the same noise sequence for each channel.
# 	if band is a tuple, the noise is passed through a bandpass filter.
# 	The tuple values specify the low and high cutoffs in Hz.'''
# 	if band:
# 		band=tuple([convertfreq(ds.fs, x) for x in band])
# 	if not chans:
# 		chans = range(ds.data.shape[1])
# 	for c in chans:
# 		wn =  makeGWN(ds.data.shape[0], std, seed, band)
# 		ds.data[:,c] += wn
# 		
# 	
# 	
# 		
# 
# 		
# if __name__=="__main__":
# 	from sys import argv
# 	if len(argv)>2:
# 		start = int(argv[2])
# 		stop = int(argv[3])
# 	else:
# 		start = 0
# 		stop = None
# 	d =  readFile(argv[1], start=start, stop=stop)
# 	print d.data[1]
