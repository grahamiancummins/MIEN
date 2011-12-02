
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

'''This module specifies the list of modules that define functions that operate on spatial data'''


import mien.blocks

MODULES=['mien.spatial.align', 'mien.spatial.measure', 'mien.spatial.density', 'mien.spatial.edit']

FUNCTIONS={}

for mn in MODULES:
	FUNCTIONS.update(mien.blocks.functionIndex(mn))

FUNCTIONS.update(mien.blocks.getBlock('SPATIAL'))

CORE=FUNCTIONS.keys()
	
ARGUMENTS=mien.blocks.getArguments(FUNCTIONS)

def refresh(clear=True):
	if clear:
 		mien.blocks.clear()
 	for k in FUNCTIONS.keys():
 		if not k in CORE:
			FUNCTIONS.pop(k)
 			# del(FUNCTIONS, k) - causes FUNCTIONS to be a local varriable
  	for k in ARGUMENTS.keys():
  	 	if not k in CORE:
  	 		ARGUMENTS.pop(k)
  	funcs=mien.blocks.getBlock('SPATIAL')
  	args=mien.blocks.getArguments(funcs)
  	FUNCTIONS.update(funcs)
  	ARGUMENTS.update(args)
  	return mien.blocks.FAILED_LOAD.keys()
