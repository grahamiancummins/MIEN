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
'''This module wraps several numerical data formats that were supported by the 
pre-mien "DataViewer" project in the mien standard file IO form. Future support 
for numerical data types should use standard modules in mien.parsers, as do g
other mien data types.'''

import mien.parsers.nmpml
import os
from mien.datafiles.filereaders import get_data_file_source, mien_file_types
import mien.datafiles.filewriters as W
from urlparse import urlparse
from mien.math.array import take
import mien.optimizers.arraystore as ast 

def ast2dat(fileobj, **kwargs):
	if type(fileobj) in [str, unicode]:
		fname=fileobj
	else:	
		try:
			fname=fileobj.name
		except:
			fname=fileobj.geturl()
	a=ast.ArrayStore(fname)
	data=a.toarray()
	header={'SampleType':'generic'}
	de=mien.parsers.nmpml.createElement('Data', {'Url':fname, 'Name':'ArrayStore'})
	de.datinit(data, header)
	n = mien.parsers.nmpml.blankDocument()
	if kwargs.get('select'):
		n.fileinformation['select_done']=True
	n.newElement(de)
	return n

def read(fileobj, **kwargs):
	try:
		fname=fileobj.name
	except:
		try:
			fname=fileobj.geturl()
		except:
			fname="Unknown"
	attributes={'Url':fname, 'Name':'DataFile'}
	format=kwargs.get('format')
	if format:
		attributes['Format']=format
		format=mien_file_types[format]
	source=get_data_file_source(fileobj, format)
	if kwargs.get('select'):
		gui=kwargs.get('gui')
		if gui:
			from mien.interface.widgets import selectDvData
			args=selectDvData(source, **kwargs)
		else:
			from mien.interface.cli import selectDvData
			args=selectDvData(source, **kwargs)
		if args.get('abort'):
			return 	mien.parsers.nmpml.blankDocument()
		for a in args.keys():
			if args[a]:
				attributes[a]=args[a]
		chans, start, stop, SR, down=[args[f] for f in ['Channels', 'Start', 'Stop', 'SamplesPerSecond', 'Downsample']]
	elif kwargs.get('readchunk'):
		start = kwargs['readchunk'][0]
		stop = kwargs['readchunk'][1]
		chans=SR=down=None
	else:
		chans=stop=SR=down=None
		start=0
	print start, stop
	data=source.read(start, stop)
	header = source.header
	if SR:	
		header["SamplesPerSecond"] = SR
	elif header.has_key("SamplesPerSecond"):
		SR = float(header["SamplesPerSecond"])
	else:
		SR = 1.0
		header["SamplesPerSecond"] = SR
	header["StartTime"] = start/SR
	if chans:
		chans.sort()	
		data=take(data, chans, 1)	
		header['Labels']=[header['Labels'][i] for i in chans]
	if down:
		data=data[slice(0, data.shape[0], 2)]
		header["SamplesPerSecond"] = header["SamplesPerSecond"]/float(down)
	de=mien.parsers.nmpml.createElement('Data', attributes)
	de.datinit(data, header)
	n = mien.parsers.nmpml.blankDocument()
	if kwargs.get('select'):
		n.fileinformation['select_done']=True
	n.newElement(de)
	return n

def sterilize(s):
	ns=''
	for c in s:
		if c=='/':
			ns+='_'
		elif c.isalnum():
			ns+=c
	return ns		

def write(fileobj, doc, **kwargs):
	data=doc.getElements("Data", heads=True)
	format=kwargs.get('format')
	if format in filetypes:
		format = filetypes[format]['extensions'][0][1:]
	if len(data)==1 and len(data[0].getElements("Data"))==0:
		#simple
		d=data[0]
		W.writeFile(fileobj, d.data, d.header(), format)
	else:
		if not type(fileobj)==file:	
			raise IOError('writing multipart data to simple numerical formats is only supported for local files')
		fname=fileobj.name	
		fileobj.close()
		base, ext=os.path.splitext(fname)
		used=[]
		for d in data:
			n=d.name()
			i=2
			while n in used:
				n=data.name()+str(i)
				i+=i
			used.append(n)
			bfn=base+"_"+n
			names=d.getHierarchy()
			for n in names:
				if n=='/':
					f=bfn
				else:
					f=bfn+sterilize(n)
				f+=ext
				W.writeFile(f, names[n].data, names[n].header(), format)
				print "wrote file %s" % f


filetypes={}
				 
filetypes['DataMAX']={'notes':"Format for RCE DAQ cards",
					'read':read,
					'write':write,
					'data type':'numerical timeseries',
					'elements':['Data'],
					'extensions':['.dm'],
					"extension patterns":[r"\d\d\d"]}
					
filetypes['Python Data']={'notes':"Internal format for storing numerical data, using python's 'pickle' module",
					'read':read,
					'write':write,
					'data type':'any numerical',
					'elements':['Data'],
					'extensions':['.pydat']}


filetypes['Data Streamer']={'notes':"Format generated by NI data streamer",
					'read':read,
					'write':write,
					'data type':'numerical timeseries',
					'elements':['Data'],
					'extensions':['.bin']}

filetypes['Dual Channel 32']={'notes':"Raw littleendian float 32 with 2 channels interleaved",
					'read':read,
					'write':write,
					'data type':'2 channel numerical timeseries',
					'elements':['Data'],
					'extensions':['.dcl']}

filetypes['Single Channel 32']={'notes':"Raw littleendian float 32",
					'read':read,
					'write':write,
					'data type':'1 channel numerical timeseries',
					'elements':['Data'],
					'extensions':['.scl']}
					
filetypes['Interleaved Binary']={'notes':"Raw littleendian float 32",
					'read':read,
					'write':write,
					'data type':'N channel numerical timeseries (stored interleaved)',
					'elements':['Data'],
					'extensions':['.ncl']}					

filetypes['Neuron Batch']={'notes':"Text format written by the Neuron simulator",
					'read':read,
					'write':False,
					'data type':'numerical timeseries',
					'elements':['Data'],
					'extensions':['.bat']}

filetypes['Float 32']={'notes':"littlendian float 32",
					'read':read,
					'write':False,
					'data type':'1 channel numerical timeseries',
					'elements':['Data'],
					'extensions':['.f']}

filetypes['Neuron Vector']={'notes':"Binary format written by the Neuron simulator",
					'read':read,
					'write':write,
					'data type':'1 channel numerical timeseries',
					'elements':['Data'],
					'extensions':['.vec']}

filetypes['Float 64']={'notes':"littleendian float 64",
					'read':read,
					'write':False,
					'data type':'1 channel numerical timeseries',
					'elements':['Data'],
					'extensions':['.d']}
					
filetypes['Delimited ascii numerical']={'notes':"Space/newline delimited ascii text specifying a 2D numerical array",
					'read':read,
					'write':write,
					'data type':'numerical',
					'elements':['Data'],
					'extensions':['.txt', '.dlm']}
					
filetypes['Optimizer ArrayStore']={'notes':"persistent parameter array created by MIEN optimizers. Limited read support (data are read as an a-semantic generic data array). Using the optimizer tools to convert astore to MIEN data will provide better support.",
					'read':ast2dat,
					'data type':'2D numerical',
					'elements':['Data'],
					'extensions':['.astore']}
					
					
filetypes['Binary Interchange']={'notes':"ALViewer format",
					'read':read,
					'write':write,
					'data type':'any numerical',
					'elements':['Data'],
					'extensions':['.bde']}
					
filetypes['Simple Array']={'notes':"an OCaml-based binary format",
					'read':read,
					'write':write,
					'data type':'1 channel numerical timeseries',
					'elements':['Data'],
					'extensions':['.saf']}
