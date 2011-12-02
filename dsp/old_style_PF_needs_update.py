#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2008-05-07.

# Copyright (C) 2008 Graham I Cummins
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA 02111-1307 USA
#
from mien.math.sigtools import *


def makeSwirl(sr, dur, rate, direction):
	'''sr (rate in Hz), dur (time in seconds), rate (rate in Hz) 
	direction (-1 or 1)-> DataSet
returns a dataset containing instructions (usable by patternInput_PF) that 
specifies a rotating stimulus (peak direction for the stimulus changes constantly
in time). The stimulus rates are updated at the rate set by "sr". The peak direction
makes a full cycle "rate" times per second, and the stimulus lasts for "dur" seconds.
If "direction" is negative the rotation is counterclockwise. Otherwise it is clockwise.
The stimulus affects both cerci. The resulting dataset specifies [time direction cercus rate].
The stimulus starts at 0 degrees at time 0, so to start later or at a different angle you 
will need to add a value to column 0 or 1 of the returned data, respectively. The peak 
rate is 80 Hz by default, so you may also want to multiply this (column 3) by some
factor'''
	dir=(direction>0)*2-1
	sp=1.0/sr
	times=arange(0, dur, sp)
	ndegrees=360*rate*dur
	dpsamp=ndegrees/times.shape[0]
	deg=arange(times.shape[0])*dpsamp*dir
	deg=deg%360
	cercus=ones(times.shape, times.dtype.char)*2
	rate=ones(times.shape, times.dtype.char)*60
	out=concatenate([times[:,NewAxis], deg[:,NewAxis], cercus[:,NewAxis], rate[:,NewAxis]], 1)
	ds=DataSet(out, {'Labels':['time', 'direction', 'cercus', 'rate'], 'SamplesPerSecond':sr})
	return ds

def setPars(ds, st, sa, amp):
	'''ds (DataSet), st (time), sa (angle in degrees), amp (peak rate in Hz)-> DataSet'''
	mr=ds.data[:,3].max()
	ds.data[:,3]=ds.data[:,3]*(amp/mr)
	ost=ds.data[0,0]
	ds.data[:,0]=ds.data[:,0]+st-ost
	osa=ds.data[0,1]
	ds.data[:,1]=ds.data[:,1]+sa-osa
	ds.data[:,1]=ds.data[:,1]%360
	return ds

def getPars(ds):
	ost=ds.data[:,0].min()
	mr=ds.data[:,3].max()
	osa=ds.data[0,1]
	if ds.data[1,1]>ds.data[0,1]:
		dir='clockwise'
	else:
		dir='counterclockwise'
	dur=ds.data[:,0].max()-ost	
	sr=ds.data[1,0]-ds.data[0,0]
	sr=1.0/sr
	rate=abs(ds.data[1,1]-ds.data[1,0])
	rate=rate*sr/360.0
	print "start time %.5g, start angle %.3f, amplitude %.3f\ndur %.5g, sr %.1f, rate %.3f, %s" % (ost, osa, mr, dur, sr, rate, dir)	
		

def load(fn):
	ds=fromFile(fn)
	return ds

import mien.math.sigtools
reload(mien.math.sigtools)
from mien.math.sigtools import *
from mien.dsp.spikeanalysis import getSpikeError, getIntraSpikeStats
from mien.datafiles.dataset import isADataSet
import os

modules = []

for m in modules:
	exec "import %s" % m
	exec "reload(%s)" % m
	exec "pyfuncs = filter(lambda x: x.endswith('_PF'), dir(%s))" % m
	for p in pyfuncs:
		exec("from %s import %s" % (m,p))

######### testing =========

def testFit_PF(i, l, s):
	'''Input:
	l[0] must be an array with at least two rows
	Output:
	returns 2*l[0][0]*l[1][0]/(l[0][0]**2+l[1][0]**2)
	'''
	x = l[0].data[0,0]
	y = l[0].data[1,0]
	fit = 2*x*y/(x**2+y**2)
	return [fit]

def testParamFit_PF(i, l, s):
	'''Input:
	l[0] must be a dict with keys "X" and "Y"
	Output:
	returns 2*XY/(X**2 +Y**2)
	'''
	x = l[0]['X']
	y = l[0]["Y"]
	fit = 2*x*y/(x**2+y**2)
	return [fit]

def readParameters_PF(i, l, s):
	'''Input:
	i must have a params child
	Output:
	appends the parameter dictionary to l
	'''
	pd = i.getParams()
	l.append(pd)
	return l

def makeHeat_PF(i,l,s):
	'''Input:
	Any
	Output:
	no change to imput (but does a large matrix multiply to waste
	cpu cycles
	'''
	n = uniform(0,200.0,(1000,1000)).astype(Float64)
	n = dot(n, n)
	return l

#General =======================

def returnError_PF(i,l,s):
	'''Input:
        s contains a key "Error", and optionally "Data"
	Output:
	    return l= [s["Error"], s["Data"]] (or just [s["Error"]] if data
		is false or undefined)
	'''
	return [s[x] for x in ["Error","Data"] if s.has_key(x)]

def returnErrorFromDSP_PF(i,l,s):
	'''Input:
		l[0] is a dataset, with a "special" key "Error", and optionally
		"Data".
	Output:
		return [Error, Data], or just [Error]
	'''
	return [l[0].special[x] for x in ["Error","Data"] if l[0].special.has_key(x)]
	

def runProcedure_PF(i,l,s):
	'''Input:
        i has a child ElementReference pointing to an object, it must also
		have param "method", naming a method of the referenced object. This
		method must require no arguments. It may have a return value, but
		this will be ignored by the AbstractModel.
    Output:
	    return l unmodified. Calls object.method()
	'''
	el=i.getElements("ElementReference")[0].target()
	pd = i.getParams()
	m=pd["method"]
	m=getattr(el, m)
	m()
	return l


#Spikes =====================================================

def spikeInfo_PF(i,l,s):
	'''Input:
	    l contains datasets with one channel
    Output:
	    Replace each 1 channel DS with a list of dicts (one for each spike)
		containing 
		"t":time of occurence of the max of the spike (float)
		"width":width at threshold (in seconds)
		"height":max-rest
		"depth":rest-min of AHP
		"attack":the slope of a best fit line through the rising
		         threshold crossing
		"decay":the slope of a best fit line through the falling
		         threshold crossing
		"zc1":time of the first zero crossing after the peak
		"tmin":time of the AHP minimum
		"ahprec":potential 1 ms after the min
		"wave":the spike waveform, resampled to 20KHz, with the
		       rest potential set to a value of 0. The wave is
			   80 samples (4 ms) long with the max of the spike at
			   sample 20.

		Assumes the rest potential is the value at .9ms into the dataset.	   
	    Detects spikes using a simple schmidt trigger with thresholds
		of rp+20 and rp+40
	
	'''
	out=[]
	for o in l:
		if isADataSet(o) and o.data.shape[1]==1:
			try:
				rp=o.data[int(.0009*o.fs),0]
				out.append(getIntraSpikeStats(o.data[:,0], o.fs, rp, rp+20, rp+40))
			except:
				out.append([BLANKSPIKE])
		else:
			out.append(o)
	return out


def spikeAverage_PF(i,l,s):
	'''Input:
	    l contains output from spikeInfo (ond no other list type entries)
	Output:
	    replace the list of dicts from spikeInfo with a single dict
		containing the additional key "N" (number of spikes) and all
		other keys the average of the keys in each dict
	'''
	l2=[]
	for o in l:
		if type(o)!=list:
			l2.append(o)
			continue
		out={"N":0}
		for d in o:
			try:
				if out['N']==0:
					out.update(d)
					out['N']=1
				else:
					for k in d.keys():
						av=(out[k]*out["N"]+d[k])/(out["N"]+1)
						out[k]=av
						out["N"]+=1
			except:
				continue
		l2.append(out)
	return l2		

def spikeError_PF(i,l,s):
	'''Input:
	    l contains dicts generated by  spikeAverage or spikeInfo
	Output:
	    returns l unchanged. Adds a key "Error" to s, containing the
		difference between the spike info in l and the internal reference
		SPIKE (hardcoded in mien.tools.optimizer_tools). If the
		key Error is already in s, this error value is added to it.
		Stores the values of "wave" in s["Data"] (list of arrays)
	'''
	error=0
	if not s.has_key("Error"):
		s["Error"]=0
	if not s.has_key("Data"):
		s["Data"]=[]	
	for o in l:
		if type(o)==list:
			for d in o:
				error+=getSpikeError(d)
				s["Data"].append(d["wave"])
			s["Error"]+=error		
		elif type(o)==dict:
			try:
				error+=getSpikeError(o)
				s["Data"].append(o.get("wave", zeros(80, Float32)))
				s["Error"]+=error
			except:
				print "failed eval"
				s["Data"].append(zeros(80, Float32))
				s["Error"]+=1000000
				
	return l



#=========GMM

def hairIDs_PF(i,l,s):
	'''Input:
	    Any
    Output:
	    returns [("L", 1),("M", 1),("S", 1), ("L", 2)...]
	'''
	l=[]
	for id in range(14):
		for t in ["L", "M", "S"]:
			l.append((t, id))
	return l

def makeVaricData_PF(i,l,s):
	'''Input:
	    l[0] is a tuple (length, id)
	Output:
	    If there is not a file
		Length.Id.10.all.l.mat in /rigs/gic/aff, creates this
		file, containing a matlab array named affdata
		returns [filename]
	'''
	sfn="/rigs/gic/aff/%s.%i.10.all.l.xml" % (l[0][0], l[0][1])
	tfn="/rigs/gic/aff/%s.%i.10.all.l.mat" % (l[0][0], l[0][1])
	modfn="/rigs/gic/aff/%s.%i.10.all.l_model.mat" % (l[0][0], l[0][1])
	if os.path.isfile(modfn):
		s["Abort"]=True
		return [modfn]
	if not os.path.isfile(sfn):
		s["Abort"]=True
		return ["no data"]
	import mien.nmpml
	from mien.datafiles.filewriters import hash2mat
	doc=mien.nmpml.readXML(sfn)
	pts=None
	for f in doc.getElements("Fiducial"):
		npts=f.points
		if pts==None:
			pts=npts[:,:4]
		else:
			pts=concatenate([pts, npts[:,:4]])
	hash2mat(tfn, {"affdata":pts})
	print "writing %s" % tfn
	return [tfn]

#=========channel density


def linroll(start, dist, rate, center=None):
	val=start-(dist*rate)
	return max(val, 0.0)

def logroll(start, dist, rate, center=None):
	if dist>=rate:
		return(0.0)
	return start*(log((rate+1)-dist)/log(rate+1))

def exproll(start, dist, rate, center=None):
	return start*exp(-1*(dist/rate))

def sigroll(start, dist, rate, center):
	return start/(1.0+exp((dist-center)*rate))

ROLLOFFFUNCTIONS={"Lin":linroll,
				  "Log":logroll,
				  "Exp":exproll,
				  "Sig":sigroll}

def rollOff_PF(i,l,s):
	'''Input:
	    i has an ElementReference to a Section, RangeVar, or Channel,
		and params Function, Rate, Center.

		Function ranges from 0 to 4 such that [0, 1)=>Lin,
		[1, 2)=>Log,[2, 3)=>Exp,[3, 4]=>Sig
		
		Rate and Center are parameters passed to the Function
		(Only Sig uses Center)
		l[0] is (section instance, float)
    Output:
	    Calculates a density (d)
	    returns [d]
 	'''
	rsec=i.getElements("ElementReference")[0].target()
	if rsec.__tag__=='Section':
		svalue=[float(rsec.attrib("Ra"))]
	else:
		if rsec.__tag__=='RangeVar':
			svalue=rsec.attrib("Values")
		else:
			svalue=rsec.attrib("Density")	
		rsec=rsec.container
		svalue=map(float, svalue.split(','))	
	rsn=rsec.name()
	sec=l[0][0]
	loc=l[0][1]
	ssn=sec.name()
	cell=sec.container
	par, path=cell.getPath(rsn,ssn)
	if par == rsn:
		rsn=(rsn,1.0)
		svalue=svalue[-1]
	elif par == ssn:
		rsn=(rsn,0.0)
		svalue=svalue[0]
	else:
		rsn=(rsn,0.0)
		svalue=svalue[0]
	r=cell.pathLength(rsn,(ssn,loc))
	pd = i.getParams()
	func = float(pd["Function"])
	if func>=3:
		func='Sig'
	elif func>=2:
		func='Exp'
	elif func>=1:	
		func='Log'
	else:
		func="Lin"
	
	sv = ROLLOFFFUNCTIONS[func](svalue, r, pd["Rate"], pd.get("Center"))
	print func, pd["Rate"], pd["Center"], sec, loc, svalue, r,  sv
	return [sv]


def constantDensity_PF(i,l,s):
	'''Input:
        l is [(X ,Y, Z)]
		i has a param "Value"
	Output:
   	    return [Value]
	'''
	pd = i.getParams()
	val=pd["Value"]
	return [val]

	
######### Actvation =========

def integratedDepolarization_PF(i,l,s):
	'''Input:
	l contains a dataset
Output:
	sets state keys "Error" and "Data"'''
	ds=l[0]
	dat=ds.data
	fs=ds.fs
	dat-=dat[0]
	err=dat.sum()/fs
	s['Data']=dat
	s['Error']=err
	return l

from mien.math.sigtools import *
import os, time
from mien.tools.dataGenerators import makeSwirl, setPars 

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

def getSynapses_PF(i, l, state):
	'''Input:
	i must have a a child ElementReference pointing to SynapticEvents  
Output:
	Appends to l a list of 2Lists containing (discription, index) for each 
	synapse referenced by the SynapticEvents object (except those with a current 
	synaptic weight of zero). The discription is a dictionary with keys including
	"Length, Direction, and "Cercus"'''
	syn = i.getTypeRef('SynapticEvents')[0]
	syn = syn.target()
	synapses=syn.synapses(True)
	new=[]
	for ind in synapses.keys():
		if not synapses[ind][1]:
			continue
		si=synapses[ind][0]
		disc={}
		try:
			disc["Length"] = float(si.attrib("Length"))
			disc["Direction"] = float(si.attrib("Direction"))
			disc["Cercus"] = si.attrib("Cercus")
		except:
			continue
		new.append([disc, ind])
	l.extend(new)
	return l
	
def groupSynapses_PF(i, l, state):
	'''Input:
	l must contain synapse lists (as generated by getSynapses)
	i must have params specifying: 
		Directions:int Number of directional slices 
					(e.g. 8=>8 45 deg regions)
					0 indicates not to group directions
		Lengths:tuple Lengths at which to split groups
				(e.g. (650, 1000) generates three groups
				<650, >650 <1000, >1000). Any false value 
				indicates to group all lengths
Output:
	replaces l with a list of NLists containing
	(discription, ind, ind, ind...) The indexes indicate which 
	synapses fall into a ginen class. Classes without at least one ind
	will not be reported'''
	pars = i.getParams()
	nd=float(pars['Directions'])
	if not nd:
		classes=l[:]
	elif nd==1:
		md=array([s[0]["Direction"] for s in l]).mean()
		classes=[[md, [], []]]
		for s in l:
			classes[0][1].append(s[0])
			classes[0][2].append(s[1])
	else:	
		dirs = arange(0,360, 360.0/nd)
		classes=[[d, [],[]] for d in dirs]
		for s in l:
			ind=argmin(abs(s[0]["Direction"]-dirs))
			classes[ind][1].append(s[0])
			classes[ind][2].append(s[1])
	classes=[c for c in classes if c[2]]		
	nl=pars.get("Lengths", "False")	
	if not nl:
		for j in range(len(classes)):
			c=classes[j]
			ml=array(c[1]).mean()
			classes[j]=[{'Direction':c[0], 'Length':ml, "Cercus":'B'}]
			classes[j].extend(c[2])
	else:
		nl=array(nl)
		nl.sort()
		mls=concatenate([0, nl, 1600])
		mls=(mls[1:]-mls[:-1])/2.0
		newclasses=[]
		for j in range(len(classes)):
			c=classes[j]
			ncs=[[{"Direction":c[0], "Length":ml, "Cercus":"B"}] for ml in mls]
			for le in c[1]:
				ind=nonzero1d(nl>le)
				if not ind:
					ind=len(nl)
				else:
					ind=ind[0]
				ncs[ind].append(c[2])
		classes=[c for c in newclasses if len(c)>1]
	#print classes	
	return classes

def setSynapses_PF(i, l, state):
	'''Input:
	l must contain lists of event tuples (index, array of event times)
	i must have an ElementReference to a SynapticEvents objectn
Output:
	assigns the events in l to the SynapticEvents elements.
	Returns a list containing one element: the number of events'''
	syn = i.getTypeRef('SynapticEvents')[0]
	syn=syn.target()
	syn.clearEvents()
	nevts=0
	for se in l:
		syn.setEvents(se[1], se[0])
		nevts+=len(se[1])		
	return [nevts]

def splitDriverPotential_PF(inst, l, state):
	'''Input:
	l[0] must be a synaptic class list ([dir, len, ind1 ...]).
	l[1] must be a dataset containing the driver potential in the first
	column
Output:
	returns a list with out[0]=l[0][2:] and out[1:] containing copies of l[1]
	(one for each index in l[0])
	'''
	inds=l[0][2:]
	dat=[inds, l[1]]
	for i in range(len(inds)-1):
		dat.append(l[-1].copy())
	return dat	

def randomEvents_PF(inst, data, state):
	'''Input:
	All items in data must be lists containing [discription, index ....]
	(e.g. generated by getSynapses or groupSynapses)
	i must have a params child specifying "Rate"  (in Hz), Stop (Seconds) and 
	Start (Seconds, optional, defaults to 0)
Output:
	return l => list of 2-lists  containing [index, array of event times]
	The events are distributed uniformly between Start and Stop, with enough
	events so that the average event rate is "Rate"'''
	pd = inst.getParams()
	Rate=pd["Rate"]
	Start=pd.get("Start", 0)
	Stop=pd["Stop"]
	Num= int((Stop-Start)*Rate)
	evts = []
	for cl in data:
		inds=cl[1:]
		for ind in inds:
			nea = uniform(Start, Stop, Num)
			nea.sort()
			evts.append([ind, nea])
	return evts

def getPatternEvents(syn, inst):
	'''used by patternInput_PF. Syn is a list of [id, dir] pairs, inst is
an array of [time direction rate]'''
	evts=[[s[0], zeros(0, Float32)] for s in syn]
	eids=[s[0] for s in syn]
	for i in range(len(inst)-1):
		evt=inst[i,:]
		dur=inst[i+1,0]-evt[0]
		for s in syn:
			proj=cos(pi*evt[1]/180.0-pi*s[1]/180.0)
			rt=proj*evt[2]
			num=rt*dur
			if num<=0:
				continue
			num, rem=divmod(num, 1)
			if rem>uniform(0,1,1)[0]:
				num+=1
			if num<1:
				continue
			new=uniform(evt[0], evt[0]+dur, int(num))
			eid=eids.index(s[0])
			evts[eid][1]=concatenate([evts[eid][1], new])
	return evts		
	
def makeInputPattern(dat, syns):
	'''Used by patternInput, swirlInput and friends'''
	rsyn=[]
	lsyn=[]
	for l in syns:
		dir=l[0]['Direction']
		syns=[[id, dir] for id in l[1:]]
		if l[0]['Cercus']=='R':
			rsyn.extend(syns)
		else:
			lsyn.extend(syns)
	linst=take(dat, nonzero1d(dat[:,2]%2==0))
	linst=take(linst, argsort(linst[:,0]))
	linst=take(linst, [0,1,3], 1)
	rinst=take(dat, nonzero1d(dat[:,2]>0))
	rinst=take(rinst, argsort(rinst[:,0]))
	rinst=take(rinst, [0,1,3], 1)
	out=getPatternEvents(lsyn, linst)
	out.extend(getPatternEvents(rsyn, rinst))
	return out


def patternInput_PF(inst, data, state):
	'''Input:
	All items in data must be lists containing [discription, index ....] (e.g.
	generated by getSynapses or groupSynapses) i must have a data child
	containing a 4 column array. The first column is interpreted as times
	(sec), the second as directions (deg), the third as the id of the cercus (0
	is left, 1 is right, 2 is both), and the last as instantaneous firing rate
	(in Hz). For each line, this means "at (time) the firing rate of afferents
	from (direction) on (cerucs) becomes (rate)". The rate remains the same
	until the time of the next line that effects that cerucs.  Afferents from
	other directions on the same cercus are also set to a new rate, determined
	by the projection of the preffered direction of these afferents onto the
	indicated direction (negative rates are not allaowed, so afferents with
	negative projections are assigned a 0 rate). No events will occur after 
	the last instruction, so the rate specified for this instruction 
	is ignored.
Output:
	return l => list of 2-lists  containing [index, array of event times]'''

	dat=inst.getData().values()[0].data
	return makeInputPattern(dat, data)

def swirlInput_PF(inst, data, state):
	'''Input:
	inst must have params: SampleRate, Duration, SwirlRate, Direction
	StartTime, StartAngle, PeakFiringRate
Output:
	generates a "patternInput" by calling makeSwirl and setPars 
	from the dataGenerators module'''
	pars = inst.getParams()
	if pars['Direction'].lower().startswith("counter"):
		dir=-1
	else:
		dir=1
	ds=makeSwirl(pars['SampleRate'], pars['Duration'],pars['SwirlRate'],dir)
	setPars(ds, pars['StartTime'], pars['StartAngle'], pars['PeakFiringRate'])
	dat=ds.data
	return makeInputPattern(dat, data)

def simpleSwirl_PF(inst, data, state):
	'''Input:
	inst must have params: Duration, SwirlRate, Direction, Jitter
	Duration is in seconds, Swirlrate is HZ, Direction is 
	"clockwise" or "counterclockwise". Jitter is a fraction of a 
	single cycle
	
Output:
	
	'''
	pars = inst.getParams()
	ncycles=int(round(pars['Duration']*pars['SwirlRate']))
	cyclet=1.0/pars['SwirlRate']
	jitter=pars['Jitter']*cyclet
	zt=arange(ncycles)*cyclet
	revdir=pars['Direction'].lower().startswith("counter")
	out=[]
	for syn in data:
		index=syn[1]
		dir=syn[0]['Direction']
		if revdir:
			dir=360-dir
		phase=cyclet*(dir/360.0)
		st=zt+phase
		if pars['Jitter']:
			jit=normal(0, jitter, st.shape)
			ind=nonzero1d(jit<2*jitter)
			#print jit.shape, ind.shape
			jit=take(jit, ind)
			st=take(st,ind)
			st+=jit
		out.append((index, st))
	return out


def refractoryThreshold_PF(inst, data, state):
	'''Input:
	l[0] must be a list of synapse indexes
	l[1:] must contain datasets specifying driver potential. It must have the
		same length as l[0]   
	i must have a params child specifying "Threshold", "Refract",
	    "RStd" and "Tao" (Tao in sec., all other parameters in amplitude units) 
Output:
	return l => list of 2-lists  containing [id, array of event times]
	'''
	pars = inst.getParams()
	evts = []
	indexes=data[0]
	for inde, ds in enumerate(data[1:]):
		ndp = ds.data[:,0]
		Fs = ds.fs
		Start = ds.start
		Tao = pars["Tao"]*Fs
		maxndp = nonzero1d(ndp==ndp.max())[0]
		#print maxndp, maxndp/Fs + Start
		nei = nonzero1d(ndp>pars["Threshold"])
		if nei.shape[0]<2:
			evts.append((nei/Fs)+Start)
			continue
		prnei = array([[nei[0],pars["Refract"]+normal(0, pars["RStd"])]])
		for i in nei[1:]:
			prev = compress(i-prnei[:,0]>3*Tao,prnei)
			refmod = prnei[:,1]*exp((prnei[:,0]-i)/Tao)
			refmod = refmod.sum()
			if ndp[i] - refmod>=pars["Threshold"]:
				evt = array([[i,pars["Refract"]+normal(0, pars["RStd"])]])
				prnei = concatenate([prnei, evt])	

		delays=prnei[1:,0]-prnei[:-1,0]
		print len(prnei), delays.min()/Fs, 1.0/(delays.mean()/Fs)
		
		evts.append([indexes[inde], (prnei[:,0]/Fs)+Start])
	return evts


def deterministicEvents_PF(inst, data, state):
	'''Input:
	i must have a Data child  with two columns. THe first column will be cast to 
	int, and treated as the unit ID, the second column contains floats, and
	is treated as the time of occurence
	data and state are ignored.
Output:
	returns a list of 2-lists containing [id, array of times]
	all the times associated to a given id will be compiled into a single array
	'''
	dat=inst.getData().values()[0].data
	evts={}
	for i in range(dat.shape[0]):
		id=int(dat[i,0])
		if not evts.has_key(id):
			evts[id]=[]
		evts[id].append(dat[i,1])
	out=[]
	for id in evts.keys():
		out.append([id, array(evts[id])])
	return out


def leakyIntegrateAndFire_PF(inst, data, state):
	'''Input:
	l[0] must be a list of synapse indexes
	l[1:] must contain datasets specifying driver potential. It must have the
	same length as l[0]
	i must have a params child specifying "Refract", "Leak", "Threshold"
	and optionally "RStd".
		Refract: The amount to reduce the driver potential when an event
			occurs
		Leak: The "current" which returns the accumulated potential to
			0. Units are in exitation units per dP per second
		Threshold: The potential at which events trigger
		RStd: The stdev of the distribution of Refract (default 0) 
	Output:
	   return l => list of 2lists containing [id, array of event times]
	'''
	pars = inst.getParams()
	rstd = pars.get("RStd", 0.0)
	thresh = pars["Threshold"]
	refr = pars["Refract"]
	evts = []
	indexes=data[0]
	for inde, ds in enumerate(data[1:]):
		leak = pars["Leak"]/ds.fs
		nei = []
		v=0
		vdp = ds.data[:,0]/ds.fs
		storev = []
		for i in range(vdp.shape[0]):
			v+= vdp[i]
			v-= v*leak
			storev.append(v)
			if v>= thresh:
				nei.append(i)
				ref = refr
				if 	rstd:
					ref += normal(0, rstd)
				v-=ref	
		if len(nei)==0:
			storev = array(storev)
			print "No Events", storev.max(),  storev.mean()
		else:
			nei=(array(nei)/ds.fs)+ds.start
			if len(nei)>1:
				delays=nei[1:]-nei[:-1]
			else:
				delays=array([0.0,1])
		evts.append([indexes[inde], nei])
		print len(nei), delays.min(), 1.0/delays.mean()
	#state["plotme"]=DataSet(reshape(storev, (-1,1)), {"SamplesPerSecond":ds.fs})	
	#print evts
	return evts
	
def addEventJitter_PF(i, l, s):
	'''Input:
	l must contain only event times (lists of the form [id, array])
	i must have a params child specifying "Std" (in seconds)
	Output:
	adds gaussian noise to each event time  
	'''
	std = i.getParams()["Std"]
	out = []
	for s in enumerate(l):
		jitter = normal(0, std, s[1].shape)
		s[1]+=jitter
	return l	
	
def eventsToRaster_PF(i, l, s):
	'''Input:
	l must contain only  event times ([id, array])
	i must have a params child specifying "dt" (in seconds)
Output:
	converts each event entry to a DataSet containing rasters, with the
	key ds.special["Index"] set to the value of id
	'''
	dt = i.getParams()["dt"]
	out = []
	for s in l:
		et=s[1]
		if et.shape[0]==0:
			st = 0.0
			et = zeros(10, Float32)
		else:	
			st = et.min()
			et = take(et, argsort(et))
			et = makeRaster(et, dt)
		et.setshape(-1,1)
		h = {"Labels":["Events"],
			 "SamplesPerSecond":1.0/dt,
			 "StartTime":st}
		ds = DataSet(et, h)
		ds.special["Index"]=s[0]
		out.append(ds)
	return out	
	

if __name__=='__main__':
 	from sys import argv
	if argv[1] == "test":
		selftest(argv[2:])
	else:
		predictFile(argv[1], argv[2])

