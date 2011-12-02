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
import os, cPickle
from mien.math.array import zeros
from mien.datafiles.filereaders import get_data_file_source, mien_file_types
from mien.parsers.fileIO import parseurl
from mien.parsers.datahash import readMD, hash2MD

class DataServer:
	def __init__(self, fn=None, doc=None, keep=False):
		self.doc=doc
		self.store={}
		self.saving=None
		self.keepstore=keep
		if fn:
			self.readStore(fn)

	def __del__(self):
		try:
			self.detachStore()
		except:
			pass

	def readStore(self, fn):
		base=os.path.splitext(fn)[0]
		n=base+'.mdat'
		if not os.path.isfile(n):
			print "No data store for %s" % base
			return
		self.store=readMD(file(n, 'rb'), return_raw_hash=True)
		print "connected data store %s" % n
		#print self.store
		
	def setStore(self, fn):
		if not fn.endswith('.mdat'):
			fn=os.path.splitext(fn)[0]+'.mdat'
		if self.saving:
			if self.saving[0]==fn:
				return
			else:
				print "Warning, changing file name during save!"
				self.saving[0]=fn
		else:
			nde=len(self.doc.getElements('Data'))
			self.saving=[fn, 0, nde]
			self.store={}
			
	def writeStore(self, key, data, header):
		if not self.saving:
			raise IOError('dataserver got a writeStore request while no save is in progress. Use "setStore" to initiate save')
		self.store[key]=(data, header)
		self.saving[1]+=1
		if self.saving[1]>=self.saving[2]:
			self.flushStore()
		
	def flushStore(self):
		if not self.saving:
			return
		hash2MD(file(self.saving[0], 'wb'), self.store)
		self.saving=None
	
	def clearStore(self):
		self.store={}
		self.saving=None
	
	def get(self, url, sub={}):
		prot, serv, path, par, q, f = parseurl(url)
		if not prot:
			prot='file'
		if prot=='auto':
			v="/"+path.lstrip('/')
			v=str(v)
			if self.store.has_key(v):
				d=self.store[v]
			else:	
				print "no file %s in storage" % v
				return (zeros(0), {})
			if not self.keepstore:
				del(self.store[v])
			return d
		elif prot=='file':
			if os.path.isfile(path):
				if q:
					return self.readHDF(path, q, sub)
				else:	
					return self.readLocalFile(path, sub)
			elif sub.get("Type")=="Auto":	
				print "referenced local file url %s not found" % path
				print "The Data tag specifies the depricated attribute Type:Auto"
				print "this could be do to a bug in the pre-version 1.0 url system. Try to load the file using 'auto://upath'"
			else:	
				print "referenced local file url %s not found" % path
			return (zeros(0), {})
		else:
			print "no support for url type %s yet" % t
			return (zeros(0), {})
			
	def readLocalFile(self, fn, sub={}):
		format=sub.get('format')
		if format:
			attributes['Format']=format
			format=mien_file_types[format]
		source=get_data_file_source(fn, format)	
		chans, start, stop, SR=[sub.get(f) for f in ['Channels', 'Start', 'Stop', 'SamplesPerSecond']]
		if not start:
			start=0
		data=source.read(start, stop)
		header = source.header
		if SR:	
			header["SamplesPerSecond"] = SR
		if chans:
			chans.sort()	
			data=take(data, chans, 1)	
			header['Labels']=[header['Labels'][i] for i in chans]
		return (data, header)		

	def put(self, url, data, header):
		prot, serv, path, par, q, f = parseurl(url)
		if not prot:
			prot='file'
		if prot=='auto':
			v="/"+path.lstrip('/')
			v=str(v)
			self.writeStore(v, data, header)
		elif prot=='file':
			if q:
				self.writeHDF(path, q, data, header)
			else:	
				self.writeLocalFile(path, data, header)
		else:
			raise IOError("no support for url type %s yet" % t)

	def readHDF(self, path, key, sub):
		pass
	
	def writeHDF(self, path, key, data, header):
		pass
		
	def writeLocalFile(self, path, data, header):
		pass
