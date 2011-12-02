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

from mien.nmpml.basic_tools import NmpmlObject
from mien.math.array import *


class Stimulus(NmpmlObject):
	'''Container for IClamps, VClamps, Synaptic events, etc.'''

	_allowedChildren = ["Comments","Parameters",
						"SynapticEvents", "IClamp",
						"AbstractModel"]
	
	def getData(self):
		'''return None if there are no data-driven sub elements,
		otherwise, return a DataSet containing all the stim channels'''
		## FIXME this uses old style datasets. It won't work in the new world
		datlist=[]
		for ic in self.getElements("IClamp", {}, 1):
			icd= ic.getElements("Data", {}, 1)
			if icd:
				ds = icd[0].makeDataSet()
				on = float(ic.attrib("Start"))/1000.0
				off= float(ic.attrib("Stop"))/1000.0
				ds.crop(0, off)
				ds.data*=float(ic.attrib("Amp"))
				filt=ds.get_x()
				filt=filt>=on
				ds.data*=filt[:,NewAxis]
				datlist.append(ds)
		for abs in self.getElements("AbstractModel", {}, 1):
			rds=abs.getElements("PythonFunction",{"Function":"readData_PF"})
			for rd in rds:
				dat=rd.getElements("Data", {}, 1)
				for datum in dat:
					ds=datum.makeDataSet()
					pars = rd.getParams()
					Start = pars.get("Start", 0)
					Stop = pars.get("Stop", -1)
					if Start!=0 or Stop!=-1:
						ds.data = dat.data[int(Start):int(Stop)]
					datlist.append(ds)
		evts=None
		for syn in self.getElements("SynapticEvents", {}, 1):
			for i in range(len(syn.getElements("ElementReference"))):
				et = syn.event_times(i)
				if et==None or  len(et)==0:
					continue
				if evts == None:
					evts=syn.getElements('Data')[0].makeDataSet()
					evts.labels=["Synaptic Events"]
				else:
					evts.data=concatenate([evts.data, et[:,NewAxis]])
		if evts!=None:
			evts.eventsToHist(20000)
			datlist.append(evts)
		return datlist		
				
	def writeHoc(self, of):
		objrefloc=of.tell()
		objrefs=["%s_stimobj" % self.name(), 0]
		pad=len("objref %s[%i]" % (objrefs[0], 10000000))
		of.write(" "*pad+"\n")
		comps=self.getElements([], {}, 1)
		for c in comps:
			if "writeHoc" in dir(c):
				of.write("\n")	
				c.writeHoc(of, objrefs)		
		if objrefs[1]:
			cur=of.tell()
			of.seek(objrefloc)
			of.write("objref %s[%i]" % (objrefs[0], objrefs[1]))
			of.seek(cur)


	def hocPostInit(self, of, time):
		comps=self.getElements([], {}, 1)
		for c in comps:
			if "hocPostInit" in dir(c):
				of.write("\n")	
				c.hocPostInit(of, time)

class SynapticEvents(NmpmlObject):
	'''Class to represent events in set of a presynaptic axons
This class acts a a container for one or more ElementReferences
pointing to Synapse instances, and a Data instance for storing the 
events.

If there is a single ElementReference, then the data should be of SampleType "events", and represents the events in that single synapse.

If there are multiple ElementReferences, then the data should be of SampleType "labeledevents", and each ElementReference must have an "Index" attribute coresponding to one of the labels in the event set. 

ElementReferences must also have a "Data" attribute specifying the synaptic weight. If a synapse has no events, or a weight of "0" it is  "turned off", and it will not be written in simulator instructions or exported by data export methods
'''

	_allowedChildren = ["Comments", 'Data', "ElementReference"]
	_requiredAttributes = ["Name"]


	def synRefs(self):
		'''No args => list
Return a list of ElementReference instances containing each synaptic connection'''
		return self.getTypeRef("Synapse")

	def synapses(self, active=False):
		'''active(Bool=False) => dict
Return a dict with integer keys and tuple values. The keys correspond to labels in the event data (or -1 if there is only one event type), and the values are (instance, float) containing the referenced Synapse, and the weight. If active is True, don't include 0 weight synapses.'''
		syns={}
		sr=self.synRefs()
		for e in sr:
			if len(sr)==1:
				i=-1
			else:
				i=int(e.attrib("Index"))
			wt=float(e.attrib("Data"))
			if active and not wt:
				continue
			s=e.target()
			syns[i]=(s,wt)
		return syns
		
	def findDataElement(self):
		de = self.getElements("Data")
		if de:
			self.data = de[0]
		else:
			from mien.nmpml.data import newData
			self.data = newData(zeros((0,2)),{"SampleType":"labeledevents", "SamplesPerSecond":20000})
			self.newElement(self.data)
			
	def refresh(self):
		self._instance_references = {}
		self.findDataElement()

	def clearEvents(self):
		'''No Args. Removes all events and initializes the data array
to a single row of -1s with a number of columns equal to the number of 
synapse references'''
		self.findDataElement()
		if self.data.shape()[0]:
			self.data.datinit(zeros((0,2)), self.data.header())

	def event_times(self, ind=-1):
		'''ind (int) => 1 D array
Returns the array of event times for a synapse. If there are more than one event types, ind must specify the label for an event type.
If there are no events, returns a len 0 array. 
Will return an array of events even if the synaptic weight is zero
'''
		a=self.data.getData()
		et=self.data.start()+a[:,0]/float(self.data.fs())
		if self.data.attrib('SampleType')=='events':
			et=et.copy()
		else:
			et=take(et, nonzero1d(a[:,1]==ind))
		et.sort()	
		return et

	def synapseIndex(self, syn):
		'''syn (instance of class Synapse) -> int
Returns the index associated to a given synapse, None if it is not referenced, or -1 if it is referenced without an Index (which will be true if it is the only synapse in the group)'''
		for sr in self.synRefs():
			if syn.upath()==sr.attrib("Target"):
				return int(sr.attributes.get("Index", -1))
		return None		
		

	def synapseTimeSeries(self, syns, start, stop, step):
		'''Returns an array containing one column for each element in the list "syns". Each column is a histogram of events for the corresponding synapse object, sampled with the indicated start stop and step (1/fs) times (in seconds)'''
		nsteps=int(round((stop-start)/float(step)))
		rd=zeros((nsteps, len(syns)))
		for i, s in enumerate(syns):
			et=self.event_times(self.synapseIndex(s))
			rd[:,i]=hist2(et, step, start, nsteps)
		return rd	

	def setEvents(self, a, ind):
		'''a (1 D array), ind (int) => None
Set the synapse specified by ind to have events at the times 
in a. If a is None or an empty arry, deletes events for that index.''' 
		self.findDataElement()
		ti=round(a*self.data.fs())
		if self.data.attrib('SampleType')=='events':
			self.data.datinit(ti, self.data.header())
		else:
			dat=self.data.getData()
			others=dat[nonzero1d(dat[:,1]!=ind), :]
			ti=column_stack([ti, ones_like(ti)*ind])
			dat=row_stack([others, ti])
			self.data.datinit(dat, self.data.header())
	
	def addEvents(self, t, ind=-1):
		'''t (array of floats), ind (int) => None
Adds events at times specified in t to the event list for synapse index ind'''
		t=array(t)
		ti=round(t*self.data.fs())
		if self.data.attrib('SampleType')=='events':
			ti=reshape(ti, (-1,1))
		else:
			ti=column_stack([ti, ones_like(ti)*ind])
		self.data.concat(ti)

	def writeHoc(self, of, objref):
		self.findDataElement()
		syn=self.synapses()
		self._syncache=[]
		for ind in syn.keys():
			wt= syn[ind][1]
			if not wt:
				continue
			if self.data.getData().shape[1]>1 and not any(self.data.getData()[:,1]==ind):
				continue	
			name="%s[%i]" % (objref[0], objref[1])
			objref[1]+=1
			self._syncache.append((name, ind))
			target=syn[ind][0]._hocID
			of.write("%s  = new NetCon(NULL, %s)\n" % (name,target))
			of.write("%s.weight = %.6f\n" % (name, wt))

	def hocPostInit(self, of, time):
		for s in self._syncache:
			name, ind = s
			#experiments, unlike all other mien objects, measure time in ms 
			evtms = self.event_times(ind) * 1000.0
			ind=nonzero1d(evtms<time)
			evtms=take(evtms,ind)
			for et in evtms:
				of.write("%s.event(%.4f)\n" % (name, et))
		del self._syncache


ELEMENTS={"Stimulus": Stimulus,
		  "SynapticEvents":SynapticEvents}

