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
import os
##from popen2 import Popen4
from mien.math.array import *
import tempfile
from time import time

SIMULATOR_COMMANDS = {"Neuron":"neuron"}


def getDir(name):
	if os.path.isdir("/scratch"):
		dir="/scratch/"
	else:
		dir=os.getcwd()
	d=tempfile.mkdtemp(prefix=name,dir=dir)
	return d

class Experiment(NmpmlObject):
	'''Subclass for representing simulation experiments

	attributes:

	dt
	simulator
	model
	celsius
	secondorder
	time
	name
	'''
	_allowedChildren = ["Comments","Recording", "ElementReference"]
	_requiredAttributes = ["Name","dt", "time"]
	_specialAttributes = ["Simulator","celsius", "secondorder"]
			
	def prepRecordings(self, of, recs):
		of.write("batch_save()\n")
		self._recordings=[]
		self._recdt=100000000.0
		for e in recs:
			var = e.attrib("Variable")
			rsr =  float(e.attrib("SamplesPerSecond"))
			rsr = 1000.0/rsr
			if 	rsr<float(self.attrib("dt")):
				self.report("Warning: %s samples too fast for the simulation. Reducing the sampling rate" % str(e))
				e.attributes["SamplesPerSecond"]=str(1000.0/float(self.attrib("dt")))
				rsr=float(self.attrib("dt"))
			self._recdt=min(self._recdt, rsr)
			pts = e.getPoints()
			if not pts:
				self._recordings.append([var, e, 0])
				of.write("batch_save(&%s)\n" % var)
			else:
				for i in range(len(pts)):
					sec,rel=pts[i]
					n = "%s.%s(%.3f)" % (sec._hocID, var, rel)
					of.write("batch_save(&%s)\n" %  n)
					self._recordings.append([n, e, i])
			e.clearValues()
			
			
	def readSimulatorOutput(self):
		inf = open("output.bat", 'rb')
		l = inf.readlines()[2:]
		output = array(map(lambda x:map(float, x.split()), l))
		#output = array([[float(x) for x in s.split()] for s in open("output.bat", 'rb').readlines()[2:]]
		recsps = str(1000.0/self._recdt)
		recs={}
		for i, r in enumerate(self._recordings):
			rec=r[1]
			rn=rec.upath()
			if not recs.has_key(rn):
				recs[rn]=[rec, [], [],[]]
			recs[rn][1].append(str(r[0]))	
			recs[rn][2].append(i)
			recs[rn][3].append(r[2])
		for rn in recs.keys():
			rec=recs[rn][0]
			rec.attributes["SamplesPerSecond"]=recsps			
			dat=take(output, recs[rn][2], 1)
			dat=take(dat, recs[rn][3], 1)
			rec.setAllData(dat, recs[rn][1])
			
	def writeModel(self, cfn):
		inst = self.getComponents()
		if type(cfn) in [str, unicode]:
			cf=open(cfn, 'w')
		else:
			cf=cfn
		cf.write("objref NULL\n")
		cf.write("objref cvode\n")
		cf.write("cvode = new CVode()\n\n")
		for mod in inst["mods"]:
			mod.writeHoc(cf)
			cf.write("\n")
		for stim in inst["stims"]:
			stim.writeHoc(cf)
			cf.write("\n")
		for p in ["celsius","secondorder", "dt"]:
			cf.write("%s=%s\n" %(p, self.attrib(p)))
		cf.write("finitialize(%.3f)\n" % inst["mods"][0].getEquilibriumVm())
		cf.write("\n")
		for stim in inst["stims"]:
			stim.hocPostInit(cf,float(self.attrib("time")))
		cf.write("\n")
		self.prepRecordings(cf, inst["recs"])
		cf.write("\n")
		cf.write("batch_run(%s, %.6f, \"output.bat\")\n" % (self.attrib('time'),self._recdt))
		cf.close()
				
	def run(self):
		'''execute the simulation'''
		st=time()
		format=self.attributes.get("Simulator","Neuron")
		if not format in SIMULATOR_COMMANDS.keys():
			self.report("This simulator is not supported")
			return
		dname = getDir(self.name())
		wdir = os.getcwd()
		os.chdir(dname) 
		cfn = "model.hoc"
		try:
			self.writeModel(cfn)
			if not self.attrib('RemoteHost'):
				print "Running Neuron"
				print dname
				os.system("neuron model.hoc > ~/neuronlog.txt")
				print "Done Running Neuron"
			else:
				rh=self.attrib('RemoteHost')
				print "attempting remote eval"
				os.system('scp model.hoc %s:' % rh)
				os.system('ssh %s neuron model.hoc' % rh)
				os.system('scp %s:output.bat .' % rh)
			self.readSimulatorOutput()
			os.chdir(wdir)
			if dname.endswith("/"):
				dname=dname[:-1]
			os.system("rm -rf %s" % dname)
		except:
			self.report("Simulation Run Failed")
			os.chdir(wdir)
			if dname.endswith("/"):
				dname=dname[:-1]
			os.system("rm -rf %s" % dname)
			raise
		print "ran model in %.2f sec" % (time()-st,)	

	##def systemcall(self, cmd):
	##	self.child = Popen4(cmd)
	##	try:
	##		self.child.wait()
	##		out = self.child.fromchild.read()
	##	except:
	##		print "wait for child failed"
	##		out = ""
	##	self.child = None
	##	return out

	def getComponents(self):
		models = ["Cell"]
		ptrs = self.getElements("ElementReference",{},1)
		stims = []
		mods = []
		for c in ptrs:
			i = c.target()
			if i.__tag__ in models:
				mods.append(i)
			else:
				stims.append(i)
		rec = self.getElements("Recording")	
		return {"stims":stims,
				"mods":mods,
				"recs":rec}

ELEMENTS = {"Experiment":Experiment}
