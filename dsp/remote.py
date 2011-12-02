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
import mien.dsp.modules

class RemoteDsp:
	def __init__(self, modules, data, retval=None):
		'''modules is a slice of a dsp chain (this probably should not use any file IO).
		data is a DataSet that is the initial data for the model. retval indicates what 
		is returned by the "eval" method after running the dsp chain. It can have the 
		values: None (or any false. The default) - return the final DataSet, 
		"data" - Return only the data member of this DataSet, 
		or any other string - attempt to return whatever is stored in ds.special[retval].
		This class assumes all components in the slice are active (if you want a component
		not to run, remove it from the slice)'''
		self.modules=modules
		self.functions=[]
		self.arguments=[]
		for m in modules:
			f=mien.dsp.modules.FUNCTIONS[m[0]]
			self.functions.append(f)
			self.arguments.append(m[1])
		self.data=data
		self.retval=retval

	def run(self):
		i=0
		upto=len(self.modules)-1
		data=self.data.copy()
		while i<=upto:
			data=self.runComponent(i, data)
			if data.special.has_key("feedback"):
				i=data.special["feedback"]
				del(data.special["feedback"])
			else:
				i+=1
		return data	

	def runComponent(self, index, data):
		func=self.functions[index]
		args=self.arguments[index]	
		dat=func(data, **args)
		return dat	

	def assignArgs(self, dict):
		'''takes a dict with tuple keys (I, n)->v. Assigns self.arguments[I][n]=v'''
		for k in dict.keys():
			i,n=k
			self.arguments[i][n]=dict[k]
		
	def eval(self, dict):
		self.assignArgs(dict)
		data=self.run()
		if not self.retval:
			return data
		elif self.retval=='data':
			return data.data
		else:
			return data.special[self.retval]


