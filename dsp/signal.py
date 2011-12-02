
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
from mien.math.sigtools import bandpass as sbandp
import operator

def bandpass(ds, maxFreq=4000.0, minFreq=500.0, select=(None, None, None)):
	'''applies a bandpass filter to each channel of data
	indexed in chans. minFreq and maxFreq are in Hz'''
	dat=getSelection(ds, select)
	dat=dat.copy()
	if select[0]:
		sds=ds.getSubData(select[0])
		fs=sds.fs()
	else:
		fs=ds.fs()
	for index in range(dat.shape[1]):
		q=sbandp(dat[:,index],minFreq, maxFreq, fs)
		dat[:,index]=q.astype(dat.dtype)
	setSelection(ds, dat, select)

def resamp(ds, dpath='/', newfs=None):
	'''Change the sampling rate of the data element at dpath. 
If newfs is None' us the sampling rate of ds.'''
	if not newfs:
		newfs=ds.fs()
	resample(ds.getSubData(dpath), newfs)

def blank(ds, select=(None, None, None)):
	'''Set the selected data to zeros'''
	if select[1] == None and select[2] == None:
		ds = ds.getSubData(select[0])
		ds.datainit(zeros_like(ds.data))
	else:
		setSelection(ds, 0.0, select)

def multiply(ds, factor=-1.0, select=(None, None, None)):
	'''multiply the selected data by factor'''
	dat=getSelection(ds, select)
	dat=dat*factor
	setSelection(ds, dat, select)
	
def add(ds, factor=1.0, select=(None, None, None)):	
	'''Add factor to the selected data'''
	dat=getSelection(ds, select)
	dat=dat+factor
	setSelection(ds, dat, select)

def zeromean(ds, select=(None, None, None), applyToAll=True):
	'''Remove the channel means from each channel in the selected data.
The means are calculated for samples within the selection. If applyToall
is True, the subtraction is performed on the whole channels (otherwise the 
subtraction is also performed on the selection).
SWITCHVALUES(applyToAll)=[True, False]
'''
	dat=getSelection(ds, select)
	means=zeros(dat.shape[1], Float32)
	for i in range(dat.shape[1]):
		means[i]=dat[:,i].mean()
	if applyToAll:
		select=(select[0], select[1], None)
		dat=getSelection(ds, select)
	dat=dat-means
	setSelection(ds, dat, select)

def normalize(ds, selectSearch=(None, None, None), selectApply=(None, None, None), mode='range', newpathTemplate=False, normVal=1.0):
	'''Scale the region selectApply with coefficients that wauld cause the channels in the region selectSearch to have the same amplitude (==normVal, mode determines how the amplitude is measured). selectSearch specifies the data to determine the normalization template from (for a typical normalization this is the same as selectApply). 
	
	Mode determines what statistic is normalized, and may be max, min, std, or range (std normalizes the standard deviations).

	If newpathTemplate has a true value, the norm template will be saved to that dpath. If there is already a data elemnt there, it will be ammended (it's values will be multiplied by the new template)

	SWITCHVALUES(mode)=['max', 'min','range', 'std']
'''
	dat=getSelection(ds, selectSearch)
	norm=zeros((dat.shape[1],1), Float32)
	for i in range(dat.shape[1]):
		if mode=='min':
			mv=abs(dat[:,i].min())
		elif mode=='max':
			mv=abs(dat[:,i].max())
		elif mode=='std':
			mv=abs(dat[:,i].std())
		else:
			mv=dat[:,i].max()-dat[:,i].min()
		#print i, normVal, mv
		if mv:
			norm[i]=normVal/mv	
		#print norm[i].max()
	#print norm	
	if newpathTemplate:
		tem=ds.getSubData(newpathTemplate)
		try:
			od=tem.getData()
			print 'updating template' 
			norm=reshape(norm, od.shape)
			tem.setData(od*norm)
		except:
			if tem:
				tem.sever()
			h={'SampleType':'generic', 'mode':repr(mode), 'selectApply':repr(selectApply),'selectSearch':repr(selectSearch)}
			n=ds.createSubData(newpathTemplate, norm, h)
	dat=getSelection(ds, selectApply)
	dat=dat*transpose(norm)	
	setSelection(ds, dat, selectApply)

def mapToRange(ds, select=(None, None, None), mini=0, maxi=1):
	'''Smoothly map the selection so that it has the indicated minimum and maximum values'''
	dat=getSelection(ds, select)
	dat=dat-dat.min()
	dat=dat/dat.max()
	r=maxi-mini	
	if r!=1:
		dat=dat*r
	if mini!=0:
		dat=dat+mini
	setSelection(ds, dat, select)

def normMeanMax(ds, select=(None, None, None)):
	'''Cause the selected data to have mean 0 max 1'''
	dat=getSelection(ds, select)
	dat=dat-dat.mean()
	dat=dat/dat.max()
	setSelection(ds, dat, select)		
		
def applyTemplate(ds, select=(None, None, None), dpath='/templ', mode='scale', invert=True):
	'''Applies a scaling template (generated by functions like "normalize") 
stored in dpath to the data specified by select. Mode may be "scale" 
(multiply), "offset" (add), or "shift" (move in time). If invert is
True, the template is applied "backwards" (so as to undue the operation
it origionally did - for scaling this means devide instead of multiply, 
for adding, it means subtract, and for shifting it means shift left
instead of right)
SWITCHVALUES(mode)=['scale', 'offset','shift']
SWITCHVALUES(invert)=[True, False]
'''
	if type(dpath) in [str, unicode]:
		template=ds.getSubData(dpath)		
	else:
		template=dpath
	temp=template.getData()
	if len(temp.shape)==2 and temp.shape[1]==1:
		temp=temp[:,0]
	dat=getSelection(ds, select)
	if mode=='scale':
		if invert:
			dat=dat/temp
		else:
			dat=dat*temp
	elif mode=='offset':
		if invert:
			dat=dat-temp
		else:
			dat=dat+temp
	else:
		if template.attrib('ValuesAreTimes'):
			targ=ds.getSubData(select[0])
			temp=round(temp*targ.fs())
		if invert:
			temp=-1*temp
		q=dat.copy()
		for i in range(temp.shape[0]):
			q[:,i]=shift(dat[:,i], temp[i])
		dat=q
	setSelection(ds, dat, select)	
		
def clip(ds, select=(None, None, None), ycoordMin=None, ycoordMax=None):
	'''clip the selcted data so that it is never less than ycoordMin and 
never greater than ycoordMax. If the values are None, don't clip in that 
direction'''
	dat=getSelection(ds, select).copy()
	for i in range(dat.shape[1]):
		if ycoordMin!=None:
			dat[:,i]=where(dat[:,i]<ycoordMin, ycoordMin,dat[:,i]) 
		if ycoordMax!=None:
			dat[:,i]=where(dat[:,i]>ycoordMax, ycoordMax,dat[:,i])
	setSelection(ds, dat, select)		
	
def sumChannels(ds, select=(None, None, None), newpath="/superposition"):
	dat=getSelection(ds, select).copy()
	dat=sum(dat, 1)
	if ds.getSubData(newpath):
		print 'Selected Path Exists. Deleting it'
		sd=ds.getSubData(newpath)
		sd.sever()
	h=getSelectionHeader(ds, select)	
	ds.createSubData(newpath, dat,h)


def stripNaN(ds, dpath="/", castNaNto=-1):
	d = ds.getSubData(dpath)
	dat = d.getData()
	dat = where(isnan(dat), castNaNto, dat)
	ds.datinit(dat)

def sigmoid(ds, select=(None, None, None), midpoint=.5, amp=1.0, slope=10.0, normalize=False):
	'''Passes the selection through a sigmoid function with the indicated parameters. If normalize is True, each channel is mapped onto the range 0 to 1 before applying the sigmoid (this can reduce uncertainty in the choice of sigmoid midpoint)
	
	SWITCHVALUES(normalize)=[True, False]
	'''
	dat=getSelection(ds, select)
	for i in range(dat.shape[1]):
		if normalize:
			dat[:,i]=dat[:,i]-dat[:,i].min()
			dat[:,i]=dat[:,i]/dat[:,i].max()			
		dat[:,i] = amp/(1.0+exp( (-1*(dat[:,i]-midpoint))*slope))
	setSelection(ds, dat, select)
	return ds	
	
def makeYHistogram(ds, select=(None, None, None), binwidth=.1, newpath='/hist'):
	'''Create a histogram across the dependent variable of timeseries data in "select". The histogram with have the indicated binwidth (in numerical value, not sample points). Select should specify only one channel. If it specifies more, only the first one will be used.'''
	dat=getSelection(ds, select)[:,0]
	rs=dat.min()
	dat=hist2(dat, binwidth, rs)
	h=getSelectionHeader(ds, select)
	h['SampleType']='histogram'
	h['SamplesPerSecond']=binwidth
	h['BinWidth']=binwidth	
	h['Start']=rs
	dat=dat.astype(int64)
	ds.createSubData(newpath, data=dat, head=h, delete=True)
	return ds 
	

# def Filter(ds, selectFilter=("filter", 0, None), channels='all'):
# 	'''extracts a kernel from the indicated sub data and applies it as a filter
# 	to the indicated channels of the input ds'''
# 	filt=ds.special[sKey]
# 	ds.filter(filt, channels)
# 	return ds
# 		
# def Derivative(ds, channels='all'):
# 	'''take the (discrete diference aproximation to the) derivative of the
# 	indicated channels dataset'''
# 	if channels=='all':
# 		channels=range(ds.data.shape[1])
# 	for index in channels:
# 		ds.data[:,index]=deriv(ds.data[:,index], ds.fs)
# 	return ds
# 		
# def Integral(ds, channels='all'):
# 	'''Take the discrete integral of the indicated channels''' 
# 	if channels=='all':
# 		channels=range(ds.data.shape[1])
# 	for index in channels:
# 		ds.data[:,index]=cumsum(ds.data[:,index])/ds.fs
# 	return ds
# 
# def TimeStretch(ds, factor, anchor=0, channels='all'):
# 	'''Calls gicMath.array.timestretch'''
# 	if channels=='all':
# 		channels=range(ds.data.shape[1])
# 	for i in channels:
# 		ds.assignChannel(i, timestretch(ds.channel(i),factor, anchor))
# 	return ds
# 
# def AverageWindows(ds):
# 	ds.foldWindows(["Average"]*ds.data.shape[1])
# 	return ds
# 
# def	ChannelSuperPossition(ds, channels='all', mode='append'):
# 	'''adds the indicated channels togeather to form a single channel.
# mode may be "append" (default): adds the new channel to the end of ds, or
# "replace": replace ds.data with a single channel array containing the sum'''
# 	if channels=='all':
# 		channels=range(ds.data.shape[1])
# 
# 	d=zeros(ds.data.shape[0], ds.data.dtype.char)
# 	for c in channels:
# 		d = d+ds.data[:,c]
# 	if mode=='append':
# 		ds.addchannel("Superpossition", d)
# 	else:
# 		ds.labels=["Superpossition"]
# 		ds.data=reshape(d, (-1,1))
# 	return ds
# 
# 
# def ChannelDifference(dat, channels, channelsToSubtract):
# 	'''Subtract all the channels in channelsToSubtract from
# 	each channel in channels'''
# 	for i in channels:
# 		for j in channelsToSubtract:
# 			dat.data[:,i] -= dat.data[:,j]
# 	return dat
# 
# 								
# 			
# def InjectGWN(ds, channels='all', stddev=1.0, minFreq=5, maxFreq=200):
# 	'''add gausian white noise with the indicated std dev, bandpassed with
# the indicated minimum and maximum frequencies'''
# 	if channels=='all':
# 		channels=range(ds.data.shape[1])
# 	for i in channels:
# 		ch=ds.channel(i)
# 		noise=normal(0, stddev, ch.shape)
# 		noise=bandpass(noise,minFreq, maxFreq, ds.fs)
# 		ds.assignChannel(i, ch+noise)
# 	return ds
# 	
# 		
# def ZeroOutsideWindow(ds, xcoord1, xcoord2, channels='all'):
# 	'''set the channels to zero before xcood1 and after xcoord2'''
# 	if channels=='all':
# 		channels=range(ds.data.shape[1])
# 	t = ds.get_x()
# 	sti = nonzero(t>xcoord1)[0]
# 	spi =  nonzero(t>xcoord2)[0]
# 	m = zeros(t.shape, t.dtype.char)
# 	m[sti:spi]=ones(spi-sti, m.dtype.char)
# 	for c in channels:
# 		ds.data[:,c]*=m
# 	return ds
# 
# def ZeroInsideWindow(ds, xcoord1, xcoord2, channels='all'):
# 	'''set the channels to zero after xcood1 and before xcoord2'''
# 	if channels=='all':
# 		channels=range(ds.data.shape[1])
# 	t = ds.get_x()
# 	sti = nonzero(t>xcoord1)[0]
# 	spi =  nonzero(t>xcoord2)[0]
# 	for c in channels:
# 		ds.data[sti:spi,c]*=0
# 	return ds
# 
# 
# def StoreData(ds, sKey='backup', channels='all'):
# 	'''Stores a copy of self in self.special[sKey]. If channels
# is not all, deletes all the unlisted channels from the copy.'''
# 	ds2=ds.copy()
# 	if channels!="all":
# 		for c in [i for i in range(ds.data.shape[1]-1,-1,-1) if i not in channels]:
# 			ds2.killchannel(c)
# 	ds.special[sKey]=ds2
# 	return ds
# 
# def KillChannels(ds, channels=[0,1]):
# 	'''Removes channels from ds'''
# 	nonstim=[i for i in range(ds.data.shape[1]) if not i in channels]
# 	ds.data=take(ds.data, nonstim, 1)
# 	ds.labels=[ds.labels[x] for x in nonstim]
# 	return ds
# 
# def AssignChannel(ds, cindexFrom=1, cindexTo=1, cname="Prediction"):
# 	'''Takes the channel in cindexFrom and copies it to cindexTo 
# 	(overwriting any data currently in that channel). Sets the name 
# 	of the assigned channel to cname. Mostly useful in optimization 
# 	routines, so always casts the cindexs to int'''
# 	chan = ds.getChannel(int(cindexFrom))
# 	i=ds.setChannel(int(cindexTo), chan)
# 	ds.labels[i]=cname
# 	return ds
# 
# def RecallData(ds, sKey='backup', mode='replace'):
# 	'''Gets a dataset from ds.special[sKey] (e.g. one written by
# StoreData). If mode is replace, makes ds a copy of this dataset
# (wont work as an in place modification!),
# if mode is append, adds the channels in the stored dataset to ds'''
# 	ds2=ds.special[sKey]
# 	if mode=='append':
# 		ds.addData(ds2)
# 	else:
# 		ds=ds2.copy()
# 	return ds
# 		
# def NameChannels(ds, names, channels):
# 	'''Assigns names to channels'''
# 	for i, c in enumerate(channels):
# 		ds.labels[c]=names[i]
# 	return ds	
# 

# 
# def combineChannels(ds, cindexIn1=0, cindexIn2=1, cindexOut=-1, mode='add'):
# 	'''calculate  function on the two input channels and store the result
# 	in the output channel. mode may be: add, subtract, multiply, divide, min,
# 	max, mean'''
# 	ops={'add':operator.add, 'subtract':operator.sub, 'multiply':operator.mul,
# 		'divide':operator.div, 'min':minimum, 'max':maximum, 'mean':lambda x, y:(x+y)/2.0}
# 	c1=ds.getChannel(cindexIn1)
# 	c2=ds.getChannel(cindexIn2)	
# 	c3=ops[mode](c1, c2)
# 	ds.setChannel(cindexOut, c3)
# 	return ds
# 
# 
# def blur(ds, channels=[0], sigma=.001, mode='guass'):
# 	'''convolve the indicated channels with a guassian having the indicated sigma
# 	(if mode is 'gauss') or an exponential with the indicated tau (if mode is "exp")'''
# 	sig=int(round(sigma*ds.fs))
# 	if sig<1:
# 		print "warning, sigma is too small. No smoothing will occur"
# 		return ds
# 	if mode=='exp':
# 		filt=arange(sig*4)
# 		filt=filt.astype(Float32)
# 		filt=exp(-filt/sig)
# 	else:	
# 		filt=arange(-3*sig, 3*sig)
# 		filt=filt.astype(Float32)
# 		filt=(1/(2.5066*sig))*exp((-1*filt**2)/(2*sig**2))
# 	if channels=='all':
# 		channels=range(ds.data.shape[1])
# 	for c in channels:	
# 		cd=ds.getChannel(c)
# 		cd=convolve(cd, filt, mode=SAME)
# 		if mode=='exp':
# 			cd=shift(cd, len(filt)/2)
# 		ds.setChannel(c, cd)
# 	return ds
# 
# def downSample(ds, factor=10, channelsSum=[], channelsMax=[]):
# 	'''Reduce the sampling rate of the data by factor (which must be an integer).
# 	All channels are downsampled. The default behavior is to average the data 
# 	in each new bin to get the value, but channels listed in the argument lists
# 	channelsSum, channelsMax, and channelsMin are treated differently. These channels
# 	calculate the sum (apropriate for histogram data) ar max (apropriate for threshold or 
# 	event data). For this function the entries in the "channels" lists must be integers.
# 	Warning: this function does NOT downsample data stored is special keys, so it 
# 	may cause unintended results if those data include filters or similar structures that 
# 	don't have an explicitly recorded sampling rate.'''
# 	nl, rem=divmod(ds.data.shape[0], factor)
# 	dat=ds.data[:-rem, :]
# 	new=zeros((nl, dat.shape[1]), dat.dtype.char)
# 	for c in range(dat.shape[1]):
# 		chan=reshape(dat[:,c], (nl, factor))
# 		if c in channelsSum:
# 			new[:,c]=sum(chan, 1)
# 		elif c in channelsMax:
# 			new[:,c]=maximum.reduce(chan, 1)
# 		else:
# 			new[:,c]=sum(chan, 1)
# 			new[:,c]=new[:,c]/factor
# 	ds.data=new
# 	ds.fs=ds.fs/factor
# 	return ds
# 
# def histogramFromSamples(ds, channels='all', bins=60, ran='auto', sKey="Histograms"):
# 	'''Convert channels to histograms, assuming that each point on a channel is a 
# 	sample. Range may be a tuple, in which case the histogram covers the range from the 
# 	first value to the last value. It may also be "auto", which sets the range to cover 
# 	the smallest sample to the largest (across all channels). Bins determines the number of 
# 	bins to separate the data into.'''
# 	if channels=='all':
# 		channels=range(ds.data.shape[1])
# 	dat=take(ds.data, channels, 1)
# 	out=zeros((bins, dat.shape[1]), Int32)
# 	if ran=='auto':
# 		ran=(dat.min(), dat.max())
# 	for c in range(dat.shape[1]):
# 		cd=dat[:,c]
# 		out[:,c]=histogram(cd, bins, ran, False)
# 	h={'StartTime':ran[0], 'SamplesPerSecond':1/((ran[1]-ran[0])/float(bins))}
# 	ds2=DataSet(out, h)
# 	ds.special[sKey]=ds2	
# 	return ds
