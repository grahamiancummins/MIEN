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
from mien.nmpml.passive import NmpmlObject, writeRangeVals

class Channel(NmpmlObject):
	'''Class describing channels with fixed or state dependant
	(not event triggered) conductance. Allways
	a child of "Section" (or equivalent).

	Attributes:

	Ion: A single ion name, or the string "Leak". (Future: Implement sets
	     of Ions)

	Density: Comma seperated list of floats

	Units: Usually units for channel density are in mhos/centimeter**2.

	Name : Name of the channel. Should corespond to the name of a modl
	       mechanism if Neuron is used for simulation.

	VarName:

	Reversal:
'''
	_allowedChildren =["Comments","Parameters"]
	_requiredAttributes = ["Name"]
	_specialAttributes = ['Ion', 'Density', 'VarName','Reversal' ]
	
	def __str__(self):
		s = "Channel"
		if self.name():
			s+=" "+self.name()
		if self.attrib("Ion"):
			s+=" "+self.attrib("Ion")
		return s	
		
	def get_rp(self):
		rp=self.attrib("Reversal")
		if not rp:
			pass
		return rp

	def writeHoc(self, of, objref=None):
		if self.attrib("Ion")=="Leak":
			n = "pas"
			dv = "g_pas"
			evn = "e_pas"
		else:
			n =self.name()
			dv = self.attrib("VarName")
			evn = "e%s" % self.attrib("Ion").lower()
			if not dv:
				dv = "g%sbar_%s" % (self.attrib("Ion").lower(), self.name())
		of.write("    insert %s\n" % n)
		
		vals = self.attrib("Density")
		writeRangeVals(dv, vals, of)
		rp=self.get_rp()
		if 	rp:
			writeRangeVals(evn, rp, of)
			
ELEMENTS = {"Channel":Channel}
