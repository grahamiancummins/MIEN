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

from numpy import *
from sys import byteorder
import re, time, struct, os
from zlib import decompress

if byteorder=='little':
	sfmt=">"
	local_byte_indicator="IM"
	local_version=("\x00\x01")
else:
	sfmt="<"
	local_byte_indicator="MI"
	local_version=("\x01\x00")

def utf16code(swap):
	if byteorder=='little':
		if swap:
			return 'utf_16_be'
		else:
			return 'utf_16_le'
	else:
		if swap:
			return 'utf_16_le'
		else:
			return 'utf_16_be'

def read_from_string(s, typ , bs=0):
	unsigned=0
	s=fromstring(s, typ)
	if bs:
		s=s.byteswap()
	if unsigned:
		n=sizeoftype(typ)[2]
		s=s+n*(s<0)
	return s

element_types=[None, 'b','B','h','H', 'i',
	   'I', 'f', None, 'd', None, None,
	   'q', 'Q', "Matlab", "Compressed", "UTF8", "UTF16", "UTF32"]


#F -> complex64, D-> complex 32
convert_types={'l':'i'}

complex_types=['F', 'D']

array_types=[None, "Cell", "Struct", "Object", 'Char', "Sparse",
	'd', 'f', 'b','B', 'h','H', 'i','I']

def binread(format, f, swap=False):
	if swap:
		format=sfmt+format
	if not type(f) in (str, unicode): 	
		n=struct.calcsize(format)
		f=f.read(n)
	v=struct.unpack(format, f)
	if len(v)==1:
		v=v[0]
	return v

def readelement(el, swap):
	dt=element_types[el[0]]
	name=None
	if not dt or dt=="UTF32":
		print "can't handle this element type"
		el[1]=None
	elif dt=="Matlab":
		name, el[1] = read_marray(el, swap)
	elif dt=="Compressed":
		name, el[1] = read_mcompr(el, swap)	
	elif type(dt)==str and dt.startswith('UTF'):
		if '8' in dt:
			el[1]=unicode(el[1], 'utf8')
		else:
			ucs=utf16code(swap)
			el[1]=unicode(el[1], usc)
	else:
		try:
			el[1]= read_from_string(el[1], dt, swap)
		except:
			print "failed to read element"
			print repr(el[1]), dt, len(el[1])
			raise
			el[1]=zeros(0, dt)
	return [name, el[1]]

def getelementlist(data, swap):
	elems=[]
	while len(data)>4:
		check = binread('I', data[:4], swap)
		if check >> 16:
			#if small
			#nb=binread('H', data[:2], swap)
			#dt=binread('H', data[2:4], swap)
			#if swap:
			#	nb, dt = dt, nb
			dt=check & 32767
			nb=check >> 16
			ed=data[4:4+nb]
			data=data[8:]
		else:
			dt=check
			size=binread('I', data[4:8], swap)
			ed=data[8:8+size]
			cut=8+size
			if cut%8 and dt!=15:
				cut+=(8-(cut%8))
			data=data[cut:]
		elems.append([dt, ed])
	return elems
		
def read_mcompr(data, swap):
	data[1] = getelementlist(decompress(data[1]), swap)
	if len(data[1])>1:
		print "yikes, there's more than one tag in this compressed element!!"
	return readelement(data[1][0], swap)

def read_cell(elems, shape, swap):
	cells=[]
	for e in elems:
		cells.append(readelement(e,swap)[1])
	return cells

def read_struct(elems, shape, swap):
	fl=readelement(elems[0], swap)[1]
	fn=readelement(elems[1], swap)[1]
	fn=reshape(fn, (-1, fl))
	names=[]
	for i in range(fn.shape[0]):
		n=fn[i].tostring().replace("\x00", "")
		names.append(n)
	ner =( len(elems) -2) / len(names)
	eind = 2
	struct = []
	for i in range(ner):
		this_struct={}
		for j in range(len(names)):
			dat=readelement(elems[eind],swap)[1]
			eind +=1
			this_struct[names[j]] = dat
		struct.append(this_struct)
	if len(struct) ==1:
		struct = struct[0]
	return struct

def read_char(elems, shape, swap):
	data =  readelement(elems[0], swap)[1]
	if not type(data) in (str, unicode):	
		data=''.join(map(chr, ravel(data)))	
	data=data.replace("\x00", "")
	return data

array_readers={"Cell":read_cell, "Struct":read_struct, "Object":None, 
	"Sparse":None, "Char":read_char}

def read_aflags(e, swap):
	name, value=readelement(e, swap)	
	flags=value[0]
	sparse=value[1]
	fd={'sparse':sparse}
	cla = flags & 255
	fd['class']=array_types[int(cla)]
	fd['complex']=flags & 2056
	fd['global']=flags & 1024
	fd['logical']=flags & 512
	return fd
	
def read_marray(data, swap):
	data[1]=getelementlist(data[1], swap)
	flags=read_aflags(data[1][0], swap)
	character=False
	cla=flags['class']
	shape=readelement(data[1][1], swap)[1]
	name = readelement(data[1][2], swap)[1]
	name=name.tostring().replace("\x00", "")
	if type(cla)==str and len(cla)>1:
		if array_readers[cla]:
			data[1]=array_readers[cla](data[1][3:], shape, swap)
		else:
			raise IOError("Matlab array type %s isn't supported yet" % cla)
	else:
		if flags['complex'] and len(data[1])>4:
			img = readelement(data[1][4], swap)[1]
		else:
			img=None
		data[1] =  readelement(data[1][3], swap)[1]
		if img!=None:
			data[1]=data[1]+img*1j
		else:
			try:
				data[1]=data[1].astype(cla)
			except:
				pass	
		shape = take(shape, arange(shape.shape[0]-1, -1, -1))
		data[1]=reshape(data[1], shape)
		data[1] = transpose(data[1])		
	return [name, data[1]]

def read(fname):
	'''Return a dictionary of name:array pairs representing the variables stored in the open file like object f'''
	if hasattr(fname, 'read'):
		f = fname
	else:
		f=file(fname, 'rb')
	comment = f.read(116)
	subspec=f.read(8)
	if subspec==' '*8 or struct.unpack('l', subspec)[0]==0:
		#no subspec
		pass
	else:	
		print 'EEK. Subsystem data. What do I do with this?'
		subspec=binread('I')
	v=f.read(2)
	swap=False
	bo=f.read(2)
	if bo!=local_byte_indicator:
		swap=True
	elems=getelementlist(f.read(), swap)
	objects={}
	for i, e in enumerate(elems):
		name, obj= readelement(e, swap)
		if not name:
			name= "Channel %i" % i
		objects[name]=obj
	f.close()
	return objects
	


def write_array(name, data):
	#print i, data, type(data)
	if len(data.shape)==1:
		data=data.reshape((1,-1))	
 	cflag=data.dtype.char in complex_types
	if cflag:
		complex=data.imag	
		data=data.real
	if data.dtype.str[1]=='i':
		dt=int32
		if int(data.dtype.str[2])>4:
			mv=abs(data).max()
			if mv>2147483648:
				print "WARNING: Int values outside the range of MATLAB int. MIEN will represent as double and hope for the best"
				dt=float64
		data=data.astype(dt)
		if cflag:
			complex=complex.astype(dt)
	dt=data.dtype.char
	if dt=='L':
		dt='I'
	elif dt=='l':
		dt='i'
	try:
		tc=array_types.index(dt)
	except:
		print "don't know matlab type for python array"
		print data.dtype.char, array_types
		return ''
	st=write_matrix_header(tc, cflag, data.shape, name)
	st=st+write_element(None, data)
	if cflag:
		st=st+write_element(None, complex)
	return st	
	
def write_char_array(name, data):
	#data=unicode(data, 'utf8')
	st=write_matrix_header(4, False, (1, len(data)), name)
	lv=len(data)	
	if lv%8:
		pad=8-(lv%8)
		data=data+('\x00'*pad)
	st+=struct.pack("II", 16, lv)
	st=st+data
	return st
	
def write_matrix_header(tc, complex, shape, name):
	s=struct.pack("II", 6, 8)
	fl=0
	if complex:
		fl=8
	if byteorder=='little':
		s+=struct.pack("BBBBI",tc,fl,0,0, 0)
	else:
		s+=struct.pack("BBBBI",0,0,fl,tc, 0)
	shape=array(shape).astype(uint32)
	#shape=take(shape, arange(shape.shape[0]-1, -1, -1))
	s+=write_element(None, shape)
	s+=write_element(None, name)
	return s

def write_cell(name, value):
	st=write_matrix_header(1, False, (1, len(value)), name)
	for i, v in enumerate(value):
		name="cell%i" % i
		st+=write_element(name, v)
	return st

def write_struct(name, value):
	st=write_matrix_header(2, False, (1, 1), name)
	fns=value.keys()
	lm=max([len(n) for n in fns])
	lm=min(lm, 31)
	st+=struct.pack("ii",262149,lm+1)
	# 262149 is a bitmask for dt=5, nb=4
	fns=value.keys()
	q=zeros((len(fns), lm+1), int8)
	for i, n in enumerate(fns):
		if len(n)>lm:
			n=n[:lm]
		q[i, :len(n)]=fromstring(n, int8)
	q=q.tostring()
	st+=struct.pack("II",1,len(q))
	if len(q)%8:
		pad=8-(len(q)%8)
		q=q+('\x00'*pad)
	st+=q
	for k in fns:
		v=value[k]
		if type(v) in (int, float, long):
			v=array([v])
		elif type(v) in [list, tuple]:
			n=[type(x) in [float, int, long] for x in v]
			if all(n):
				v=array(v)
		st+=write_element(k, v)
	return st

def write_element(name, value):
	if name and not name[0].isalpha():
		name = "e" + name
	tc=14
	if type(value) in [int, float]:
		value=array([value])
	if type(value)==ndarray:
		if not name:
			#if byteorder=='big':
			#	value=value.byteswap()
			dt=value.dtype.char
			if dt=='L':
				dt='i'
			elif dt=='l':
				dt='i'
			elif dt=='q':
				dt='i'
			try:
				tc=element_types.index(dt)
			except:
				print name
				print value.dtype.char
				print value.dtype.str
				raise	
			value=transpose(value)
			dat=ravel(value).tostring()
		else:
			dat=write_array(name, value)
	elif type(value) in (list, tuple): 
		dat=write_cell(name, value)
	elif type(value)==dict:
		dat=write_struct(name, value)
	elif type(value) in (str, unicode):
		if not name:
			tc=1
			dat=str(value)
		else:
			dat=write_char_array(name, str(value))		
	else:
		print "don't know how to write element %s of type %s" % (name, type(value))
		return ''
	lv=len(dat)	
	if lv%8:
		pad=8-(lv%8)
		dat=dat+('\x00'*pad)
	head=struct.pack("II", tc, lv)
	try:
		return head+dat
	except:
		print name, value, type(dat), len(dat)
		return head+str(dat)



	
def write(fname, d):
	'''write a dictionary (d) of name:array pairs in mat 7 format to an open file-like object (f)'''
	from time import strftime
	if hasattr(fname, 'write'):
		f = fname
	else:
		f=file(fname, 'wb')
	date=strftime('%m-%d-%Y')
	top="MATLAB 5.0 MAT-file, Platform: PYTHON, Created on:"+date+(" "*116)
	f.write(top[:116])
	f.write(" "*8)
	f.write(local_version)
	f.write(local_byte_indicator)
	#f.write('\x00\x01')
	#f.write('IM')	
	d=d.copy()
	fixValues(d)
	for k in d.keys():
		f.write(write_element(k, d[k]))
	f.close()

def fixValues(d):
	keys=d.keys()
	for k in keys:
		if d[k]==None:
			del(d[k])
		elif type(d[k]) in [ndarray, matrix]:
			if type(d[k]) == matrix:
				d[k] = array(d[k])
			if d[k].shape[0]==0:
				del(d[k])
			elif not d[k].dtype.char in element_types:
				if d[k].dtype.char in complex_types:
					pass
				elif d[k].dtype.char in convert_types:
					print "converting array '%s' to type '%s'" % (k, convert_types[d[k].dtype.char])
					d[k]=d[k].astype(convert_types[d[k].dtype.char])
				else:	
					print "warning, array %s has unknown type %s" % (k, d[k].dtype.char)
					del(d[k])
		elif type(d[k]) in [tuple, list, dict]:
			if len(d[k])==0:
				del(d[k])
			else:	
				try:
					l=array(d[k])
					if l.dtype.char in ['l', 'd']:
						d[k]=l
					elif l.dtype.char=='i':
						d[k]=l.astype('l')
					elif l.dtype.char=='f':
						d[k]=l.astype('d')						
				except:
					pass
		elif type(d[k])==bool:
			if d[k]:
				d[k]=1
			else:
				d[k]=0
		elif type(d[k]) in [float64, float32]:
			d[k]=float(d[k])
		elif type(d[k]) in [int64, int32]:
			d[k]=int(d[k])
		elif type(d[k])==str:
			if any(array(map(ord, d[k]))>127):
				print "Warning, string type of %s can't be saved to mat" % d[k]
				del(d[k])


if __name__ == '__main__':
	from numpy.random import randn
	z = randn(4, 3, 2)
	write('test.mat', {'z':z})
	d = read('test.mat')
	z2 = d['z']
	print z.shape, z2.shape
	if any(z != z2):
		print(z-z2)
	else:
		print "OK"
		print z[:,:,0]
