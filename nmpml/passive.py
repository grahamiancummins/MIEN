
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

def writeRangeVals(vn, vals, of):
	if type(vals) in [int, float, long]:
		of.write("    %s = %.5f\n" % (vn, float(vals)))	
	elif len(vals)==1:
		of.write("    %s = %.5f\n" % (vn, vals[0]))
	elif len(vals)==2:
		of.write("    %s(0:1) = %.5f:%.5f\n" % (vn, vals[0], vals[1]))
	else:
		print "%s value %s Not yet supported" % (vn,str(vals)) 
 	
	

class RangeVar(NmpmlObject):
	'''Class to represent values that varry along the length of a Section.
	Should Be a child of a Section

	Attributes:

	Name

	Values: Comma seperated floats.

	Units
	'''
	_allowedChildren = ["Comments"]
	_requiredAttributes	= ['Name', 'Values']
	
	def writeHoc(self, of, objref=None):
		vals = self.attrib("Values")
		writeRangeVals(self.name(), vals, of)


ELEMENTS={"RangeVar":RangeVar}
