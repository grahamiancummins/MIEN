
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
from mien.nmpml.pointcontainer import PointContainer
from mien.nmpml.basic_tools import NmpmlObject
from mien.math.array import *
import os


class Synapse(NmpmlObject):
	'''Class describing channels with variable conductance driven by an
	event (e.g. a synapse). These are contained in a Cell.
	
	Attributes:

	Type : name of the synaptic channel object in Neuron

	Id : integer Id of this particular channel (unique amoung
	     channels of this type).
	
	Point	 
	
	'''
		
	_allowedChildren = ["Comments","Parameters", "Data"]
	_requiredAttributes = ["Name", "Type", "Point"]
	_guiConstructorInfo = {} 
	_xmlHandler = None
	_hasCdata = False
	

	def xyz(self):
		pt = self.container.points[int(self.attrib("Point")),:3]
		return pt

	def rel(self):
		sec = str(self.container.name())
		rel = self.container.relLocOfPtN(int(self.attrib("Point")))
		return (sec, rel)
	
	def writeHoc(self, of, objref):
		name="%s[%i]" % (objref[0], objref[1])
		objref[1]+=1
		self._hocID=name
		rel = self.container.relLocOfPtN(int(self.attrib("Point")))
		of.write("%s = new %s(%.3f)\n" % (name,self.attrib("Type"), rel))

class IClamp(NmpmlObject):
	'''Class describing a current injecting electrode. The class takes an 
	ElementReference child pointing to a Section instance. The Data attribute
	of this ElementReference should be the relative location allong that Section
	
	Attributes:

	Start

	Stop

	Amp

	Id

	File

	Samp
	
	'''
	_allowedChildren =["Comments", "Data", "ElementReference"]
	_requiredAttributes = ["Name"]
	_specialAttributes = ["Start", "Stop", "Amp", "Id"]
	_guiConstructorInfo = {} 
	_xmlHandler = None
	_hasCdata = False
	
	def __str__(self):
		s = "IClamp:"  
		for at in ["Start", "Stop", "Amp"]:
			if self.attrib(at):
				s+=" "+str(self.attrib(at))
		return s

	def writeVector(self, path, data):
		s = data[:,0].astype(Float64)
		l = data.shape[0]
		open(path, 'wb').write(s.tostring())
		open('testvec', 'wb').write(s.tostring())
		return l
		
	def writeHoc(self, of, objref):
		name="%s[%i]" % (objref[0], objref[1])
		objref[1]+=1
		self._hocID=name
		data = self.getElementOrRef("Data")
		er=self.getTypeRef("Section")[0]
		sec=er.target()._hocID
		rel=float(er.attrib("Data"))
		of.write("%s {%s = new IClamp(%.3f)}\n" % (sec, name, rel))

		of.write("%s.del=%s\n" % (name, self.attrib("Start")))
		of.write("%s.dur=%.4f\n" % (name,float(self.attrib("Stop")) - float(self.attrib("Start"))))
		if not data or data.getData()==None:
			of.write("%s.amp=%s\n" % (name, self.attrib("Amp")))
		else:
			i = 0
			path = "iclampVector%i" % i
			while os.path.isfile(path):
				i+=1
				path = "iclampVector%i" % i
			dmv=max(abs(data.getData()))[0]	
			l = self.writeVector(path, data.getData())	
			fn = "%s[%i]" %  (objref[0], objref[1])
			objref[1]+=1
			self._hocFileID=fn	
			vn = "%s[%i]" %  (objref[0], objref[1])
			objref[1]+=1
			self._hocVectorID=fn
			of.write("%s= new File(\"%s\")\n" % (fn, path))
			of.write("%s= new Vector()\n" % (vn,))
			of.write("%s.ropen()\n" % fn)
			of.write("%s.fread(%s, %i)\n" % (vn, fn, l))
			of.write("%s.close()\n" % fn)
			amp=self.attrib("Amp")
			amp=amp/dmv
			of.write("%s = %s.mul(%.6f)\n" % (vn, vn, amp))
			of.write("print %s.max()\n" % (vn,))
			samp = 1000.0/float(data.attrib("SamplesPerSecond"))
			of.write("%s.play(&%s.amp, %f)\n" % (vn, name, samp))
				 
ELEMENTS={"Synapse":Synapse,
		  "IClamp":IClamp}
