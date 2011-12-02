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
'''
Specialized alternative to shelve. provides a class that stores a list of
arrays.All arrays are of type Float32, 1D, and of the same length. File format
is simple binary, always littlendian, with the first 4 bytes encoding the width
as an unsigned int ("<I")

'''

import struct, os, tempfile
from sys import byteorder
from mien.math.array import array, float32, fromstring, reshape, zeros

def verify(fname, width, minlength=0):
	'''returns true if fname exists and appears to be an arraystore with the indicated 
	width. If minlength is a positive integer, also require that the length of the arraystore
	is at least this large'''
	try:
		f=open(fname, 'rb')
		w=struct.unpack('<I', f.read(4))[0]
		f.seek(0, 2)
		fl=f.tell()
		f.close()
	except:
		return False
	if w!=width:
		return False
	if minlength:
		l=(fl/4)-1
		n=l/w
		if n<minlength:
			return False
	return True		
		
def empty(fname, width, safe=False):
	'''Creates an empty arraystore in fname  with the indicated width. If safe is False, this will overwrite an exisitng file. If safe is True, the file is created by a call to mkstemp with the indicated path as dir and prefix. This prevents overwriting any files, but changes the file name. In both cases ther function returns the file name (although if safe is False this will always be the same as the fname argument).'''
	s=struct.pack('<I', width)
	if not safe:
		if os.path.isfile(fname):
			os.unlink(fname)
		f=open(fname, 'wb')
		f.write(s)
		f.close()
	else:
		dir, fname= os.path.split(fname)
		fh, fname=tempfile.mkstemp('.astore', fname, dir)
		os.write(fh, s)
		os.close(fh)
	return fname

class ArrayStore:
	dtype=float32

	def __init__(self, fname, mode='r'):
		'''fname is the name of a file (string), and mode is one of "w" or "r" for 
		read/write or read only access. Init requires that a file already exist 
		(use verify and empty to make new files).'''
		if mode!='r':
			mode='r+b'
		else:
			mode='rb'	
		self.file=file(fname, mode)
		self.file.seek(0)
		self.width=struct.unpack('<I', self.file.read(4))[0]
		self.invert=byteorder=='big'

	def __del__(self):
		self.file.close()

	def close(self):
		self.file.close()

	def __len__(self):
		self.file.seek(0, 2)
		fl=self.file.tell()
		l=(fl/4)-1
		n=l/self.width
		return int(n)

	def __getitem__(self, key):
		l=len(self)
		if type(key)==slice:
			st=key.start
			if st<0:
				st=l+st
				if st<0:
					st=0
			elif st>l-1:
				return zeros((0, self.width), self.dtype)
			sp=	key.stop
			if sp<0:
				sp=l+sp
				if sp<1:
					return zeros((0, self.width), self.dtype)				
			ne=min(sp, l)
			ne=ne-st
			self.file.seek(4+4*self.width*st)
			a=fromstring(self.file.read(self.width*4*ne), self.dtype)
			if self.invert:
				a.byteswap()
			a=reshape(a, (ne, self.width))	
		else:
			if key<0:
				key=l+key
			self.file.seek(4+4*self.width*key)
			s=self.file.read(self.width*4)
			a=fromstring(s, self.dtype)
			if self.invert:
				a.byteswap()
		return a	

	def append(self, a):
		if len(a.shape)!=1:
			raise IOError("Can only add 1D arrays to arraystore")
		if a.shape[0]!=self.width:
			raise IOError("Attempt to add array of wrong size ")
		if a.dtype!=self.dtype:
			a=a.astype(self.dtype)
		if self.invert:
			a=a.copy()
			a.byteswap()
		s=a.tostring()
		self.file.seek(0,2)
		self.file.write(s)
		self.file.flush()
		return len(self)
		
	def toarray(self):
		self.file.seek(4)
		a=fromstring(self.file.read(), self.dtype)
		if self.invert:
			a.byteswap()
		return reshape(a, (-1, self.width))
		
	def setarray(self, a):
		'''Sets the stored values to the array a (must be of the correct width)'''
		if a.shape[1]!=self.width:
			raise IOError("Attempt to add array of wrong size ")	
		if a.dtype!=self.dtype:
			a=a.astype(self.dtype)
		if self.invert:
			a=a.copy()
			a.byteswap()
		self.file.truncate(4)
		self.file.seek(4)
		self.file.write(a.tostring())
		self.file.flush()
		
	def tail(self, n):
		'''Return the last n rows of self. If n>len(self) return the whole arry (shape[0] will be less than n). This should be exactly equivalent to self[-n:] except that Python 2.5 applies an annoying modulo operation during automatic slice construction. This function is in fact exactly the same as self[slice(-n, 2147483647, None)]'''
		return self[slice(-n, 2147483647, None)]
	
	def getColumn(self, i):
		if i>=self.width:
			raise IndexError("Column index exceeds width")
		self.file.seek(0, 2)
		fl=self.file.tell()	
		c=[]
		adv=self.width*4
		pos=4+i*4
		while pos<fl-4:
			self.file.seek(pos)
			c.append(self.file.read(4))
			pos+=adv
		a=fromstring(''.join(c), self.dtype)
		if self.invert:
			a.byteswap()
		return a					

	def take(self, ai):
		'''Return an array containing all the rows specified in the index array ai. Ai may specify multiple occurances of the same index. This function is probably slower than numpy.take(self.toarray(), ai), but will use much less memory if ai is short and len(self) is large.'''
		ret=zeros((ai.shape[0],self.width), self.dtype)
		for i in ai:
			self.file.seek(4+4*self.width*i)
			s=self.file.read(self.width*4)
			ret[i,:]=fromstring(s, self.dtype)
		if self.invert:
			ret.byteswap()
		return ret	
			
		
