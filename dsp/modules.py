
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


'''This module specifies the list of modules that defin DSP functions. In addition, 
functions interacting with data on disk are defined here. For compatibility with other
programs, all such functions should be defined in this module'''


import mien.blocks

MODULES=['mien.dsp.channelops', 'mien.dsp.frequency', 'mien.dsp.generators', 'mien.dsp.nmpml', 'mien.dsp.signal', 'mien.dsp.subdata']

FUNCTIONS={}

for mn in MODULES:
	FUNCTIONS.update(mien.blocks.functionIndex(mn))

CORE=FUNCTIONS.keys()

FUNCTIONS.update(mien.blocks.getBlock('DSP'))
	
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
  	funcs=mien.blocks.getBlock('DSP')
  	args=mien.blocks.getArguments(funcs)
  	FUNCTIONS.update(funcs)
  	ARGUMENTS.update(args)
  	return mien.blocks.FAILED_LOAD.keys()
	