
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
import os
from string import join
import struct
import re
from sys import byteorder
from mien.math.array import *
from time import strftime
from cPickle import dump

def write_pydata(f, data, header) :
	header["Values"]=data
	dump(header, f, -1)
	f.close()

def write_text_file(f, data, header):
	cn=''
	for s in header:
		if s=='special':
			continue
		if s=='Labels':
			for n in header[s]:
				cn=cn+n+" "
		else:
			f.write(s+":"+str(header[s])+os.linesep)
	f.write(cn[:-1]+os.linesep)
	for l in data:
		f.write(join(map(str, l))+os.linesep)

	f.close()

def write_streamer(of, data, header):
	vtag = '1.1 N\x00\x00\x02'
	nc = data.shape[1]
	fs = header["SamplesPerSecond"]
	h = struct.pack("<iB3sI", 332, nc, "1.1", fs)
	ranges = [0.0]*64
	data = data.astype(Float64)
	for ax in range(data.shape[1]):
		cr = max( abs(min(data[:,ax])), max(data[:,ax]))
		ranges[ax]=cr
		cr = (-cr, cr)
		#print data[:10]
		a =  maptorange(data[:,ax], typecoderanges[Int16], cr)
		#print data[:10]
		#print cr 
		data[:,ax] = maptorange(data[:,ax], typecoderanges[Int16], cr)
	data=data.astype(Int16)
	if byteorder == "big":
		dat=arbyteswap(dat)
	order = range(1, nc+1) + [0]*(64-nc)
	h += apply(struct.pack, ["<64B"]+order)
	h += apply(struct.pack, ["<64f"]+ranges)
	of.write(h)
	of.write(data.tostring())
	of.close()

def write_dcl(of, a, header):
	a=a[:,:2]
	a=a.astype(Float32)
	if byteorder == "big":
		a=arbyteswap(a)
	of.write(a.tostring())
	
def write_ncl(of, a, header):
	a=a.astype(Float32)
	if byteorder == "big":
		a=arbyteswap(a)
	fs=	header["SamplesPerSecond"]
	of.write(struct.pack("<ff", a.shape[1], fs))
	of.write(a.tostring())	
	
def write_scl(of, a, header):
	a=a[:,0]
	a=a.astype(Float32)
	if byteorder == "big":
		a=arbyteswap(a)
	of.write(a.tostring())

def write_interchange(of, a, header):
	if len(a.shape)==2:
		dims=(a.shape[1], 0, 0)
	elif len(a.shape)==4:
		dims=a.shape[-3:]
	else:
		print "Can only write 2 or 4D data in interchange format!"
		print "For 1 or 3D data, use a first dimension of length 1"
		return
	ft=header.get("FileType", "")
	ft=ft[:256]
	if len(ft)<256:
		ft=ft+" "*(256-len(ft))
	bo=byteorder[0]
	datty=a.dtype.char[-1]
	dt=1.0/header.get("SamplesPerSecond", 1.0)
	dt=struct.pack("f", dt)
	dimstr=struct.pack("III", dims[0], dims[1], dims[2])
	origin=header.get("Origin", (0.0,0.0,0.0))
	resolution=header.get("VoxelSize", 0.0)
	voxinfo=struct.pack("ffff", origin[0], origin[1], origin[2], resolution)
	sid=header.get("StructureID", "No SID Available")
	pad=" "*206
	of.write(ft+bo+datty+dt+dimstr+voxinfo+sid+pad)
	data=a.tostring()
	of.write(data)
	of.close()

def write_simplearray(of, a, header):
	SR = float(header.get("SamplesPerSecond", 1.0))
	a=a.astype(Float32)
	of.write('SAF02')
	of.write( struct.pack('H', 1) )
	of.write( struct.pack('f', SR) )
	ND  = len(a.shape)
	of.write( struct.pack('H', ND) )
	of.write(apply(struct.pack, ["I"*ND]+list(a.shape)))
	of.write(a.tostring())
	of.close()

writer_codes = { "pydat":write_pydata,
				 "txt":write_text_file,
				 "dcl":write_dcl,
				 "scl":write_dcl,
				 "ncl":write_ncl,
				 "bin":write_streamer,
				 "bde":write_interchange,
				 "saf":write_simplearray}

def getWriter(fobj, format):
	w = writer_codes.get(format)
	if w:
		return w
	try:
		format=os.path.splitext(fobj.name)[1][1:]
		w = writer_codes.get(format)
		if w:
			return w
	except:
		pass
	print "can't get file format. Using default (pydat)"
	return write_pydata

def  guessHeader(data, header):
	if not header:
		header = {}
	defaults = {}	
	defaults["Columns"] = data.shape[1]
	defaults["SamplesPerSecond"] = 10000
	defaults["Date"]=strftime('%m_%d_%Y')
	defaults['Length']=data.shape[0]
	defaults["DataType"]=data.dtype.char
	defaults['Labels']=map(lambda x: "Chan%i" % x, range(data.shape[1]))
	defaults.update(header)
	return defaults
	
def writeFile(fileobj, data, header=None, format=None):
	if type(fileobj) in [str, unicode]:
		fileobj=file(fileobj, 'wb')
	header = guessHeader(data, header)
	writer = getWriter(fileobj, format)	
	writer(fileobj, data, header)
