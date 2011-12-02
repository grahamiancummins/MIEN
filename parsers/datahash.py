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

__doc__=='''This module defines IO for a binary file type that stores python pickles in a hash like structure keyed by strings. Yes, this is exactly
what "shelve" ought to do, but shelve is totally FUBAR, so this is a
reimplementation. It is not thread/multiprocess safe, but is otherwise
reliable. Uses Network (bigendian) byte order'''

import  cPickle, os, struct, mien.parsers.nmpml, sys
from mien.math.array import ArrayType, reshape, fromstring, ones, any, ravel, dtype, array

def rmdashrf(dir):
	if not os.path.exists(dir):
		return
	if os.path.isfile(dir):
		os.unlink(dir)
	elif os.path.isdir(dir):
		cont=[os.path.join(dir, x) for x in os.listdir(dir)]
		for q in cont:
			rmdashrf(q)
		os.unlink(dir)
			
def uniqueName(base, used):
	i=0
	name='%s%i' % (base, i)
	while name in used:
		i+=1
		name='%s%i' % (base, i)
	return name 	
			

DTS=ones(1).dtype.str[0]	

class DirDataHash:
	def __init__(self, fn):
		self.checkFile(fn)
		
	def checkFile(self, fn):
		if fn.endswith("index.datahash"):
			self.indexfile=fn
			self.dir=os.path.split(fn)[0]
		else:	
			self.dir=fn
			self.indexfile=os.path.join(fn, "index.datahash")
		self.index=None
		if not os.path.exists(self.dir):
			os.mkdir(self.dir)
			file(self.indexfile, 'wb').write("")
		elif not os.path.isdir(self.dir):
			raise IOError("%s exists, but is not a directory" % self.dir)
		else:
			if not os.path.isfile(self.indexfile):
				if len(os.listdir(self.dir))>0:
					raise IOError("%s exists, has contents, but has no datahash index. Choosing not to overwrite" % self.dir)
				else:
					file(self.indexfile, 'wb').write("")			
		self.readIndex()
				
	def readIndex(self):
		self.index={}
		f=file(self.indexfile, 'rb')
		ed=f.read(8)
		while len(ed)==8:
			kl, vl=struct.unpack("!ii", ed)
			k=f.read(kl)
			v=f.read(vl)
			self.index[k]=v
			ed=f.read(8)
		f.close()	
	
	def writeIndex(self):
		if self.index==None:
			self.readIndex()
		f=file(self.indexfile, 'wb')
		for k in self.index.keys():
			kd=struct.pack("!ii", len(k), len(self.index[k])) 
			f.write(kd)
			f.write(k)
			f.write(self.index[k])
		f.close()	
			
	def nextName(self):
		i=0
		b='d'
		files=os.listdir(self.dir)
		return uniqueName('d', files)
			
	def add(self, key, object):
		fn=self.nextName()
		fullfn=os.path.join(self.dir, fn)
		cPickle.dump(object, file(fullfn, 'wb'))
		if self.index==None:
			self.readIndex()		
		self.index[key]=fn
		f=file(self.indexfile, 'ab')
		kd=struct.pack("!ii", len(key), len(self.index[key])) 
		f.seek(0, 2)
		f.write(kd)
		f.write(key)
		f.write(self.index[key])
		f.close()
		
	def keys(self):
		if self.index==None:
			self.readIndex()
		return self.index.keys()
		
	def __getitem__(self, key):
		k=self.keys()
		if not key in k:
			raise KeyError("%s not in index" % key)
		fn=self.index[key]
		fn=os.path.join(self.dir, fn)
		return cPickle.load(file(fn, 'rb'))
		
	def __setitem__(self, key, object):
		k=self.keys()
		if not key in k:
			self.add(key, object)
		else:
			fullfn=os.path.join(self.dir, self.index[key])
			cPickle.dump(object, file(fullfn, 'wb'))
			
	def __delitem__(self, key):
		k=self.keys()
		if not key in k:
			raise KeyError("%s not in index" % key)
		fullfn=os.path.join(self.dir, self.index[key])
		os.unlink(fullfn)
		del(self.index[key])
		self.writeIndex()


def nestData(dats):
	tops={}
	k=dats.keys()
	k.sort(lambda x,y:cmp(len(x), len(y))) 
	for key in k:
		ks=key.rstrip('/')
		ks=ks.split('/')
		pk='/'.join(ks[:-1]) 
		if not pk:
			tops[key]=dats[key]
		elif not pk in k:
			if pk+'/' in k:
				pk=pk+'/'
			else:
				tops[key]=dats[key]
		if pk in k:
			dats[pk].newElement(dats[key])
	return tops.values()		
	
def hash2doc(h, url=None):
	dats={}
	for k in h.keys():
		data, head = h[k]
		name=k.split(':')[-1]
		name=name.strip()
		name=name.rstrip('/')		
		attributes={'Name':name}
		if url:
			attributes['Url']="%s?%s" % (url, k)
		de=mien.parsers.nmpml.createElement('Data', attributes)
		de.datinit(data, head)
		dats[k]=de
	dats=nestData(dats)	
	n = mien.parsers.nmpml.blankDocument()
	for de in dats:
		n.newElement(de)
	return n

def readDir(f, **kwargs):
	if not type(f)==file:	
		raise IOError('DirDataHash only supports local directories!')
	fname=f.name	
	f.close()
	h=DirDataHash(fname)
	url="file://%s" % (fname,)
	return hash2doc(h, url)
			
def writeDir(f, doc, **kwargs):
	if not type(f)==file:	
		raise IOError('DirDataHash only supports local directories!')
	fname=f.name	
	f.close()
	dats=doc.getElements('Data')
	rmdashrf(fname)
	h=DirDataHash(fname)
	for d in dats:
		h[d.upath()]=(d.data, d.header())
	
def readPickle(f, **kwargs):
	h=cPickle.load(f)
	try:
		url="file://%s" % (f.name,)
	except:
		try:
			url=f.geturl()
		except:
			url=None
	d=hash2doc(h, url)		
	return 	d
	
def writePickle(f, doc, **kwargs):
	dats=doc.getElements('Data')
	h={}
	for d in dats:
		h[d.upath()]=(d.data, d.header())
	cPickle.dump(h, f)
	
def readMD(f, **kwargs):
	dats={}
	cat=f.read(16)
	while len(cat)==16:
		pl, hl, dl = struct.unpack("<IIQ", cat)
		path=f.read(pl)
		head=eval(f.read(hl))
		dat=None
		if dl:
			ct=f.read(1)
			if ct in ['<', '>', '|', "{"]:
				ct=ct+f.read(6)
				dti, nd = struct.unpack("<3sI", ct)
				if dti.startswith("{"):
					dti=dti[1:]
				dti=dtype(dti)
			else:
				print "warning, old mdat. May not be platform portable"
				nd = struct.unpack("<I", f.read(4))[0]
				dti=dtype("<"+ct)				
			sh=struct.unpack("<"+"Q"*nd, f.read(8*nd))
			dat=f.read(dl)
			dat=fromstring(dat, dti)
			dti=dti.str
			if DTS!=dti[0]:
				dtil=dtype(DTS+dti[1:])
				dat=dat.astype(dtil)
			dat=reshape(dat, sh)
		dats[path]=(dat, head)	
		cat=f.read(16)	
	try:
		url="file://%s" % (f.name,)
	except:
		try:
			url=f.geturl()
		except:
			url=None		
	if kwargs.get('return_raw_hash'):
		return dats	
	else:
		return hash2doc(dats, url)		
	
def writeMDElement(f, path, data, header):
	h=repr(header)
	if data==None or type(data)!=ArrayType or len(data.shape)==0 or not any(data.shape):
		#print type(data)
		dlen=0
	else:
		dat=data
		dti=dat.dtype.str
		if len(dti)!=3:
			dti="{"+dti[0]+dat.dtype.char
		sh=dat.shape
		dat=ravel(dat).tostring()
		dlen=len(dat)
	cat=struct.pack("<IIQ", len(path), len(h), dlen)
	f.write(cat)
	f.write(str(path))
	f.write(h)
	if not dlen:
		return
	pc="<3sI"+"Q"*len(sh)
	pc=[pc, dti, len(sh)]
	pc.extend(list(sh))
	dh=apply(struct.pack, pc)
	f.write(dh)		
	f.write(dat)


def hash2MD(f, hash):
	for path in hash.keys():
		data, head = hash[path] 
		writeMDElement(f, path, data, head)
	
def writeMD(f, doc, **kwargs):
	dats=doc.getElements('Data')
	for d in dats:
		path=d.upath()
		head=d.header()
		data=d.data
		writeMDElement(f, path, data, head)
	
filetypes={}			
				
filetypes['Data Directory']={'notes':'In principal, this type can store any python object, but it was designed for use on numerical data',
							'read':readDir,
							'write':writeDir,
							'data type':'numerical',
				'elements':'all',
				'extensions':['.datahash'],
				'isdir':True}

filetypes['Data Hash']={'notes':'In principal, this type can store any python object, but it was designed for use on numerical data',
							'read':readPickle,
							'write':writePickle,
							'data type':'numerical',
				'elements':['Data'],
				'extensions':['.data.pickle','.mdh']}

filetypes['Mien Data']={'notes':'In principal, this type can store any python object, but it was designed for use on numerical data',
							'read':readMD,
							'write':writeMD,
							'data type':'numerical',
				'elements':['Data'],
				'extensions':['.mdat', '.data']}
