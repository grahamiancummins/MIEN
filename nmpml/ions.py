
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
#needs a rewrite of the mask behavior!

CHARGES = {"K":1,
		   "Na":1,
		   "Ca":2,
		   "Cl":-1}

class Ion(NmpmlObject):
	'''Class to represent the concentration of an ion
Attributes:
    Name (str): "K", "Na", "Ca", "Cl"
	IC (internal concentration) float, or name
	ConcentrationUnits:  str
	EC (external concentration) float, or name
	ReversalPotential: Float or name
	                   If specified, IC and EC are ignored by the
					   reversal method, and this value is returned
					   instead.
	PotentialUnits: str				   
	Dynamic (Bool): If True, simulators should allow the concetrations
	to change. Defaults to 0

IC, EC, and ReversalPotential may be strings (that do not eval to
floats). In this case the strings reference Mask objects, which are used
instead of constant values. If Masks are used, the Units attributes
should be omitted (sine the mask will have its own units).

'''
	_allowedChildren = ["Comments", "ElementReference"]
	_requiredAttributes = ["Name"]
	_specialAttributes = ["IC",
						  "ConcentrationUnits",
						  "EC", "ReversalPotential",
						  "PotentialUnits",
						  "Dynamic"]
	

	def ic(self, point):
		'''point => float
Return IC, by first trying to cast self.attrib("IC") to a float,
and next trying to resolve it as a mask reference and evalate that
mask at point (with mask.getValue)'''
		try:
			ic = float(self.attrib("IC"))
		except:
			m=self.getInstance(self.attrib("IC"), "Data")
			ic = m.getValue(point)
		return ic

	def ec(self, point):
		'''point => float
Like IC, but for external concentration.'''
		try:
			ic = float(self.attrib("EC"))
		except:
			m=self.getInstance(self.attrib("EC"), "Data")
			ic = m.getValue(point)
		return ic
		

	def reversal(self, point, temp=293):
		''' point, temp = 293 => float
returns the attribute ReversalPotential, if it is specified.
Otherwise it caluculates reversal from the concentrations.
Currently this excpects concetration in millimolar, and ignores
Units tags. temp is the temperature in Kelvin, and defaults to 293
(20 C)'''
		if self.attrib("ReversalPotential"):
			try:
				rp = float(self.attrib("ReversalPotential"))
			except:
				m=self.getInstance(self.attrib("ReversalPotential"), "Mask")
				rp = m.getValue(point)
			return rp
		else:
			
			c = 2.303*(8.314472*temp)/(CHARGES[self.attribs["Name"]]*96485.3415)
			return c*log(self.ec()/self.ic())

	
ELEMENTS={"Ion":Ion}
