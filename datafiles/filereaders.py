#Simcon support functions for reading various files

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

from mien.math.array import *
from string import join
from sys import byteorder
import cPickle
import re, time, struct, os
import struct


## Functions used by the reader classes =========================

def binread(format, f):
	n=struct.calcsize(format)
	v=struct.unpack(format, f.read(n))
	if len(v)==1:
		v=v[0]
	return v

def autoLabel(n):
	return map(lambda x: "Chan%i" % x, range(n))

def readvec(s):
	'''string => (array, string)
Reads a vector written by the neuron vwrite command from the input string
into an array. Returns a tuple containing this array, and any part of the
string left over after reading the vector.'''
	codes={3:Float32, 4:Float64, 5:Int32}
	n, t = struct.unpack("<ii", s[:8])
	bs = "little"
	fc = "<"
	if t >1000:
		bs = "big"
		fc = ">"
		n, t = struct.unpack(">ii", s[:8])
	#print n, t
	end=0
	if codes.has_key(t):
		bytes=len(ones(1, codes[t]).tostring())
		end=(8+bytes*n)
		a=fromstring(s[8:end], codes[t])
		if byteorder != bs:
			a=arbyteswap(a)
	elif t==2:
		end=24+2*n
		sp, mini = struct.unpack(fc + "dd", s[8:24])
		a=fromstring(s[24:end], Int16)
		if byteorder != "bs":
			a=arbyteswap(a)
		a=a+(a<0)*65536
		a=a/sp + mini
	elif t==1:
		end=24+n
		sp, mini = struct.unpack(fc+"dd", s[8:24])
		a=fromstring(s[24:end], Int8)
		if byteorder != "bs":
			a=arbyteswap(a)
		a=a+(a<0)*256
		a=(a+128)/sp + mini
	return  (a, s[end:])	


## function to read kernel files (from matlab) ========================

def read_kernel(filename):
	try:
		a=readmat(file(filename, 'rb'))
	except:
		raise
		os.system("matlab -nojvm -r \"writekern('%s', 'temp.kern'); exit\"" % filename)
		a=readmat(file('temp.kern', 'rb'))
	k=a[2]
	for z in k:
		while type(k[z])==ArrayType and len(k[z])==1:
			k[z]=k[z][0]
	return k

## ===========Classes to read simple binary formats ======================

class binary_data:
	def __init__(self, f, datat, chans, hl=0):
		self.format=datat
		self.file=f
		self.header_length=hl
		self.datatype=datat
		self.nchans=chans
		self.samplesize=len(zeros(1, datat).tostring())
		length=self.getsize()/(self.samplesize*self.nchans)
		self.header={"Labels":autoLabel(self.nchans), "Length":length, "ByteOrder":byteorder}

	def __len__(self):
		return int(self.header["Length"])
	
	def getsize(self):
		q=self.file.tell()
		self.file.seek(0,2)
		e=self.file.tell()-self.header_length
		self.file.seek(q)
		return e
	
	def read(self, start=0, stop=None, chans=None):
		self.file.seek(self.header_length+start*self.samplesize*self.nchans)
		if not stop:
			a=fromstring(self.file.read(), self.datatype)
		else:
			b=(stop-start)*self.samplesize*self.nchans
			a=fromstring(self.file.read(b), self.datatype)
		if byteorder!=	self.header["ByteOrder"]:
			a=arbyteswap(a)
		a=reshape(a, (-1,self.nchans))
		if chans:
			a=take(a, chans, 1)
		return a

class nclfile(binary_data):
	def __init__(self, f):
		nchans, fs = binread("<ff", f)
		binary_data.__init__(self, f, Float32, int(nchans), 8)
		self.format="ncl"
		self.header["ByteOrder"]="little"
		self.header["SamplesPerSecond"]=fs
	
class dclfile(binary_data):
	def __init__(self, f):
		binary_data.__init__(self, f, Float32, 2,)
		self.format="dcl"
		self.header["Labels"]=["0to180", "RtoL"]
		self.header["ByteOrder"]="little"
		
class sclfile(binary_data):
	def __init__(self, f):
		binary_data.__init__(self, f, Float32, 1)
		self.format="scl"
		self.header["Labels"]=["0to180"]
		self.header["ByteOrder"]="little"

## Class to read Neuron vector files ==============================

class nrnvecfile:
	def __init__(self, f):
		self.format="vec"
		self.file=f
		self.header={}
		self.scan_file()

	def __len__(self):
		return int(self.header["Length"])
	
	def scan_file(self):
		s=self.file.read()
		vecs=[]
		while s:
			v, s = readvec(s)
			vecs.append(v)
		self.header['Labels']=autoLabel(len(vecs))
		self.header["DataType"]=vecs[0].dtype.char
		
		l=max(map(len, vecs))
		self.header['Length']=l
		a=zeros((l, len(vecs)), vecs[0].dtype.char)
		for v in range(len(vecs)):
			a[:len(vecs[v]),v]=vecs[v]
		self.data=a
	
	def read(self, start=0, stop=None, chans=None):
		if not stop:
			stop=self.data.shape[0]
		a=self.data[start:stop, :]
		if chans:
			a=take(a, chans, 1)
		return a

## Class to read text files ==============================		
		
class textdatafile:
	def __init__(self, f):
		self.format="txt"
		self.file=f
		self.header={}
		self.scan_file()

	def __len__(self):
		return int(self.header["Length"])
	
	def scan_file(self):
		hlines=[]
		dat=[]
		nls=re.compile("[\s,|]+")
		for s in self.file.readlines():
			if not s.strip():
				continue
			try:
				dat.append([float(s1) for s1 in nls.split(s) if s1])
			except:
				hlines.append(s)
		if not dat:
			raise IOError('No numerical data in file')
		d=array(dat)	
		self.data=d
		self.header['Labels']=autoLabel(d.shape[1])
		self.header["DataType"]=d.dtype.char
		self.header['Length']=d.shape[0]
		
		if len(hlines)>0:
			l=hlines[-1].split()
			if len(l)==d.shape[1]:
				self.header['Labels']=l
				hlines=hlines[:-1]
			self.header["Note"]=re.sub(r"\s+", " ",join(l))
		for l in hlines:
			if ":" in l:
				try:
					lab, val = s.split(':')
					val=float(val)
				except:
					continue
				lab=lab.lower()	
				srl=["samplespersecond", "sampling", "rate", "hz"]
				if any([s in lab for s in srl]):
					self.header["SamplesPerSecond"]=val
					break
				dtl=["dt", "spacing", "interval"]
				if any([s in lab for s in srl]):
					self.header["SamplesPerSecond"]=1.0/val
					break
					
	def read(self, start=0, stop=None, chans=None):
		if not stop:
			stop=self.data.shape[0]
		a=self.data[start:stop, :]
		if chans:
			a=take(a, chans, 1)
		return a


class nrnbatchfile(textdatafile):
	def scan_file(self):
		hlines=[]
		while 1:
			s=self.file.readline()
			if not s.strip():
				continue
			try:
				d=map(float, s.split())
				break
			except:
				hlines.append(s)
		s=[s]+self.file.readlines()
		d=array(map(lambda x: map(float, x.split()), s))
		self.data=d
		self.header['Labels']=autoLabel(d.shape[1])
		self.header["DataType"]=d.dtype.char
		self.header['Length']=d.shape[0]
		bl=hlines[-1]
		try:
			i=bl.find("steps of")
			if i==-1:
				raise StandarError
			sr=float(bl[i:].split()[2])
			sr=1000.0/sr
			self.header["SamplesPerSecond"]=sr
		except:
			self.header["SamplesPerSecond"]=1.0
		
#===========================Class to Read Streamer Files=========================
class streamerfile:
	def __init__(self, f):
		self.file, self.hdrstop, self.nchans, self.samp, self.ranges = self.getinfo(f)

		self.datatype="h"
		self.arraytype="<i2"
		self.samplesize=struct.calcsize(self.datatype)
		self.header={"SamplesPerSecond": self.samp,
					 'Labels':autoLabel(self.nchans),
					 "Length":len(self)}
		self.format="bin"
		

	def __len__(self):
		self.file.seek(0,2)
		lb=self.file.tell()
		ns=int((lb-self.hdrstop)/(self.samplesize*self.nchans))
		return ns
	
	def getinfo(self, f):
		hdrlen=binread("<i", f)
		chans=binread("<B", f)
		f.seek(8)
		samp=binread("<I", f)
		order=binread("<"+"B"*64, f)
		ranges = binread("<"+"f"*chans, f)
		return (f, hdrlen, chans, samp, ranges)
	
	def set(self, n):
		self.file.seek(self.hdrstop+(n*self.nchans*self.samplesize))

	def singleread(self, n, channel=None):
		self.set(n)
		if channel!=None:
			self.file.seek(channel*self.samplesize, 1)
			return struct.unpack("<"+self.datatype, self.file.read(self.samplesize))[0]		
		else:
			return struct.unpack("<"+self.datatype*self.nchans, self.file.read(self.samplesize*self.nchans))

	def read(self, start=0, stop=None, chans=None):
		self.set(start)
		if stop:
			s=self.file.read((stop-start)*self.samplesize*self.nchans)
		else:
			s=self.file.read()
		a=fromstring(s, self.arraytype)
		# if byteorder == "big":
		# 	a=arbyteswap(a)
		a=reshape(a, (-1, self.nchans))
		a = a.astype(Float32)
		for ax in range(self.nchans):		
			a[:,ax] = a[:,ax]*(self.ranges[ax]/2**11)
			#print min(a[:,ax]), max(a[:,ax])
		if chans:
			a=take(a, chans, 1)
		return a


#===========================Class to Read Datamax Files=========================

class dmfile:
	def __init__(self, f):
		self.file, self.hdrstop, self.Fs, note, date, self.nswipes, self.active, self.scanorder = self.getinfo(f)
		self.nchans=len(self.active)
		names= map(lambda x: x["label"].replace("\x00", ""), self.active)
		comments=map(lambda x: x["comment"].replace("\x00", ""), self.active)
		names=map(lambda x: "%s (%s)" % (names[x], comments[x]), range(len(names)))
		#d=list(date)+[0]
		date=time.strftime("%m-%d-%Y", time.localtime())
		note=note.replace("\x00", "")
		note=re.sub(r"\s+", " ", note)
		self.header={"SamplesPerSecond":self.Fs , "Columns":len(self.active),"Labels":names,  "Date":date, "Length":len(self), "DataType":'i2'}
		if note:
			self.header["Note"]=note			
		self.format="dm"
			
	def __len__(self):
		self.file.seek(0,2)
		lb=self.file.tell()
		ns=int((lb-self.hdrstop)/(2*len(self.active)))
		return ns
	
	def getinfo(self, f):
		s=binread("8s", f)
		if s[:7]!="DATAMAX":
			raise IOError("Not a datamax file")
		version,nboards,nchans,nswipes= binread("<4I", f)
		f.seek(580,1)
		date= binread("<8H", f)
		nnc=binread("<I", f)
		note=binread("1280s", f)
		note=note[:nnc]
		active=[]
		boards=[]
		sequence=[["board", "<I"], ["chan","<I"], ["bandwidth", "<I"],
				  ["Fs", "<I"], ["range", "<I"], ["scale", "<f"],
				  ["unit", "8s"], ["label", "32s"], ["comment", "80s"],
				  ["status", "<I"], ["offset", "<f"], ["pretest", "<I"],
				  ["pretest_value", "<f"], ["extra", "40s"]]
		ranges={0:40, 1:10, 2:4, 3:1 , 4:.4}
		if nboards > 100:
			raise
		for i in range(nboards):
			boards.append({})
			boards[-1]['serial']=binread("<I", f)
			boards[-1]['totalchans']=binread("<I", f)
			boards[-1]['chans']=[]
			for j in range(8):
				boards[-1]['chans'].append({})
				for l in sequence:
					boards[-1]['chans'][-1][l[0]]=binread(l[1], f)
				if boards[-1]['chans'][-1]["status"]:
					d=boards[-1]['chans'][-1]
					d['range']=ranges[d['range']]
					active.append(d)		  
		fs=boards[0]['chans'][0]["Fs"]
		endhdr=((f.tell()/65536)+1)*65536
		s=map(lambda x: x['board'], active)
		order=filter(None, map(lambda x:s.count(x), range(nboards)))
		return (f, endhdr, fs, note, date, nswipes, active, order)

	
	def swipeinfo(self, start, stop):
		swipelen=int(round(self.Fs/10.0))
		startind=start
		if not stop:
			stop=int32(swipelen*self.nswipes)
		else:
			stop=min(int32(swipelen*self.nswipes), stop)
		stopind=stop-start
		start=int(start/swipelen)
		startind=startind%swipelen
		stopind=startind+stopind
		if stop%swipelen:
			stop=int(round(stop/swipelen))+1
		else:
			stop=int(stop/swipelen)
			stop=max(stop, start+1)
		stop=min(stop, self.nswipes)
		return (start, stop, startind, stopind, swipelen)
		
	
	def read(self,  start=0, stop=None, tofloat=True):
		#print 'here1', start, stop
		start, stop, startind, stopind, swipelen=self.swipeinfo(start, stop)
		#print 'here', start, stop, startind, stopind, swipelen, len(self.active)
		data=zeros(((stop-start)*swipelen, len(self.active)), Int16)
		swipesize = 0
		for s in self.scanorder:
			swipesize+=swipelen*2*s
		self.file.seek(start*swipesize+self.hdrstop)
		c=0
		#import time; st=time.time()
		for i in range(start, stop):
			r=0
			for s in self.scanorder:
				datalen=2*swipelen*s
				a=fromstring(self.file.read(datalen), Int16)
				if byteorder == "big":
					a=arbyteswap(a)
				a=reshape(a, (swipelen, s))
				data[c:c+swipelen,r:r+s]=a
				r+=s
			c+=swipelen
		#print time.time()-st; st=time.time()
		data=data[startind:stopind,:]
		#tofloat=False
		if tofloat:
			data=data.astype(Float32)
			ran=[q['range'] for q in self.active]
			ran=array(ran, Float32)/32768
			data*=ran
		#print time.time()-st; st=time.time()
		return data


## Class to read PYDATAFILEs ==============================	
	
class pyfile:
	def __init__(self, f):
		self.header = cPickle.load(f)
		f.close()
		self.data = self.header["Values"]
		del(self.header["Values"])
		self.header["DataType"]=self.data.dtype.char
		self.header["Columns"] = self.data.shape[1]
		self.header['Length']=self.data.shape[0]
		self.format="pydat"
		
	def __len__(self):
		return self.header['Length']
	
	def samplesize(self):
		return self.data.itemsize()
		
	def read(self, start=0, stop=None):
		return self.data[start:stop, :]



class bdinterchangefile:
	def __init__(self, f):
		self.format="bde"
		self.file= f
		self.header = self.parse_header(self.file)
		self.data=None
				
	def __len__(self):
		return self.header['Length']
	
	def parse_header(self, inf):
		header={}
		header["FileType"]=inf.read(256).strip()
		self.endian=inf.read(1)
		if self.endian=="l":
			fc="<"
		else:
			fc=">"
		self.datty=inf.read(1)
		header["SamplesPerSecond"]=1.0/binread(fc+"f", inf)
		self.shape=binread(fc+"III", inf)
		if self.shape[1]==0:
			self.shape=self.shape[:1]
			header["Columns"]=self.shape[0]
			header["Labels"]=["v%i" % x for x in range(self.shape[0])]
		header["Origin"]=binread(fc+"fff", inf)
		header["VoxelSize"]=binread(fc+"f", inf)
		header["StructureID"]=inf.read(16)
		inf.seek(0, 2)
		dats=inf.tell()-512
		nums=zeros(1, self.datty).itemsize()
		sampsize=nums*reduce(multiply, self.shape)
		header['Length']=int(dats/sampsize)
		return header
			
	def read(self, start=0, stop=None):
		if self.data==None:
			self.file.seek(512)
			data=self.file.read()
			data=fromstring(data, self.datty)
			if byteorder[0]!=self.endian:
				data=arbyteswap(data)
			s=tuple([-1]+list(self.shape))
			self.data=reshape(data, s)	
			self.file.close()
			
		return self.data[start:stop, :]


## Class to read simplearray ==============================	

class simplearray:
	def __init__(self, f):
		self.format="saf"
		self.file= f
		self.header = self.parse_header(self.file)
		self.data=None
				
	def __len__(self):
		return self.header['Length']
	
	def parse_header(self, inf):
		id=inf.read(3)
		if not id=='SAF':
			raise IOError('not an saf file')
		ver=int(inf.read(2))
		header={}
		ee=binread("@H", inf)
		if ee == 1:
			self.bswap = False
			fc = "@"
		else:
			self.bswap = True
			if byteorder[0] == "l":
				fc = ">"
			else:
				fc = "<"
		header["SamplesPerSecond"]=binread(fc+"f", inf)
		ND = binread(fc+"H", inf)
		shape = binread(fc+"I"*ND, inf)
		header["Shape"]=shape
		header["Columns"]=shape[1]
		self.endheader=inf.tell()
		header["Labels"]=["y%i" % x for x in range(header["Columns"])]
		header['Length']=shape[0]
		return header
			
	def read(self, start=0, stop=None):
		if self.data==None:
			self.file.seek(self.endheader)
			data=self.file.read()
			self.file.close()
			data=fromstring(data, Float32)
			if self.bswap:
				data=arbyteswap(data)
			self.data=reshape(data, (self.header["Shape"]))

			
		return self.data[start:stop, :]


#===============Generic Datafile Read Function===========================


format_codes = { "dm":dmfile,
				 "pydat":pyfile,
				 "bin":streamerfile,
				 "dcl":dclfile,
				 "scl":sclfile,
				 "ncl":nclfile,
				 "bat":nrnbatchfile,
				 "f": lambda x : binary_data(x, Float32, 1),
				 "vec":nrnvecfile,
				 "d":lambda x : binary_data(x, Float64, 1),
				 "txt":textdatafile,
				 "bde":bdinterchangefile,
				 "saf":simplearray}
				 
mien_file_types={ 'DataMAX':"dm",
				 'Python Data':"pydat",
				 'Data Streamer':"bin",
				 'Dual Channel 32':"dcl",
				'Interleaved Binary':"ncl",
				 'Single Channel 32':"scl",
				 'Neuron Batch':"bat",
				 'Float 32':"f",
				 'Neuron Vector':"vec",
				 'Float 64':"d",
				 'Delimited ascii numerical':"txt",
				 'Binary Interchange':"bde",
				 'Simple Array':"saf"}

 				 
guess_order=[streamerfile,dmfile, simplearray, pyfile]

def get_data_file_source(fobj, format=None):	
	if type(fobj) in [str, unicode]:
		fobj=file(fobj, 'rb')
	if format_codes.get(format):
		source=format_codes[format](fobj)
	else:
		try:
			filename=fobj.name
		except:
			try:
				filename=fobj.geturl()
			except:
				filename='unknown'
		base, ext = os.path.splitext(filename)
		ext=ext[1:]
		if format_codes.get(ext):
			source=format_codes[ext](fobj)
		else:
			for c in guess_order:
				try:
					source=c(fobj)
					break
				except:
					fobj.seek(0)
			else:
				raise IOError("Can't Determine Format")
	return source

def read_datafile(filename, h5path=None):
	try:
		s=get_data_file_source(filename)
	except:
		return [None, None]
	if h5path or s.format=='h5':
		data=s.read(h5path)
		h=s.header(h5path)
	else:
		data=s.read()
		h=s.header
	h["Type"]=s.format
	return [data, h]

def scanFile(filename, format=None):
	'''filname(str), format(str=None) => (string, dict)
returns the format type and header of the named file. If format is not
specified (default). It is automatically identified if possible'''
	source=get_data_file_source(filename, format)
	format=source.format
	if format == 'h5':
		header=source
	else:
		header=source.header
	return (format, header)
	
	
if __name__=="__main__":
	from sys import argv
	if len(argv)>2:
		start = int(argv[2])
		stop = int(argv[3])
	else:
		start = 0
		stop = None
	s=get_data_file_source(argv[1])
	data =  s.read(start=start, stop=stop)
	n = 15000 - start
	print data[n]
