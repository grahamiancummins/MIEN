#!/usr/bin/env python
# encoding: utf-8
#Created by Graham Cummins on 2007-06-05.

# Copyright (C) 2007 Graham I Cummins
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
import mien.nmpml.data as mdat
from mien.math.array import *
import re

def read(f):
	if type(f) in [str, unicode]:
		f=file(f, 'rb')
	l=f.read()
	l=re.split("[\r\n]+", l)
	dat = []
	ls = l[0].split(',')
	try:
		dat.append(map(float, ls))
		lab=None
	except:
		lab=ls
	llen = len(ls)
	l=l[1:]	
	for line in l:	
		ls = line.split(',')
		if len(ls)!=llen:
			print('Warning: encountered csv line of wrong length. Skipping line')
			continue
		try:
			dat.append(map(float, ls))
		except:
			lls =[]
			for x in ls:
				try:
					lls.append(float(x))
				except:
					lls.append(nan)
			dat.append(lls)
	dat=array(dat)
	return lab, dat
	


def csvRead(f, **kwargs):
	labs, dat=read(f)
	data=[]
	node={'tag':"Data", 'attributes':{'Name':'csv'}, 'elements':[], 'cdata':''}
	node['attributes']['SampleType']='timeseries'
	node['attributes']['SamplesPerSecond']=1.0
	if labs:
		node['attributes']['Labels']=labs
	dc=mdat.Data(node)
	dc.data=dat
	node={'tag':"Nmpml", 'attributes':{'Name':'0'}, 'elements':[], 'cdata':''}
	document = mdat.basic_tools.NmpmlObject(node)
	document.newElement(dc)
	return document

filetypes={}	
					
filetypes['Comma Separated Values']={'read':csvRead,
					'notes':'ascii format encoding a 2D array as a comma/newline delimited list',

					'data type':'simple numerical',
					'extensions':['.csv']}
					
if __name__=='__main__':
	xl2lists('btest.xls')