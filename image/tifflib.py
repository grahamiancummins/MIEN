#!/home/gic/bin/python

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
from types import StringType, IntType, LongType, FloatType
import sys, struct
from copy import deepcopy

bytepref="@"

entrytypes=[{"NAME":"BYTE", "SIZE":1, "FORMAT":"B"},
			{"NAME":"ASCII", "SIZE":1, "FORMAT":"c"},
			{"NAME":"SHORT", "SIZE":2, "FORMAT":"H"},
			{"NAME":"INT", "SIZE":4, "FORMAT":"I"},
			{"NAME":"FRACTION", "SIZE":8, "FORMAT":"II"},
			{"NAME":"SBYTE", "SIZE":1, "FORMAT":"b"},
			{"NAME":"UNDEF", "SIZE":1, "FORMAT":"b"},
			{"NAME":"SSHORT", "SIZE":2, "FORMAT":"h"},
			{"NAME":"SLONG", "SIZE":4, "FORMAT":"i"},
			{"NAME":"SFRACTION", "SIZE":8, "FORMAT":"ii"},
			{"NAME":"FLOAT", "SIZE":4, "FORMAT":"f"},
			{"NAME":"DOUBLE", "SIZE":8, "FORMAT":"d"}]

knowntags={254:"NewSubFileType",
		   255:"SubFileType",
		   256:"Width",
		   257:"Length",
		   258:"BitsPerSample",
		   259:"Compression",
		   262:"PhotoInterp",
		   263:"Thresholding",
		   264:"CellWidth",
		   265:"CellLength",
		   266:"FillOrder",
		   270:"Description",
		   271:"Make",
		   272:"Model",
		   273:"StripOffsets",
		   274:"Orientation",
		   277:"SamplesPerPixel",
		   278:"RowsPerStrip",
		   279:"StripByteCounts",
		   280:"Min",
		   281:"Max",
		   282:"XRes",
		   283:"YRes",
		   284:"PlanarConfig",
		   288:"FreeOffsets",
		   289:"FreeBytes",
		   290:"GrayResponseUnit",
		   291:"GrayResponse",
		   296:"ResUnit",
		   305:"Software",
		   306:"Date",
		   315:"Artist",
		   316:"Computer",
		   317:"LZWPredictor",
		   320:"ColorMap",
		   338:"ExtraSamples",
		   33432:"Copyright",
		   33628:"MetamorphUIC1"}

rationaltypes=[282,283]

requiredtags=[256,257,259,262,273,279,282,283]

tagdefaults={296:2,258:1,266:1, 259:1, 274:1, 278:2**32-1}

tagtypes={315:2,258:3,265:3,264:3, 320:3, 259:3,33432:2,
		  306:2,338:3,266:3,289:4,288:4,291:3,290:3,316:2,
		  270:2,257:"SL", 256:"SL",271:2,281:3,280:3,
		  272:2,254:4, 274:3,262:3,284:3,296:3,278:"SL",
		  277:3,305:2,279:"SL",273:"SL",255:3,263:3,
		  282:5,283:5, 317:3, 33628:4}

#Compression (259) 1=None 2=Huffman 32773=PackBits
#PhotoInterp (262) 0=WhiteIsZero, 1=BlackIsZero", 2=RGB, 3=Paletted, 4=Mask
#ResUnit 1=None, 2=Inch, 3=Centimeter

def superset(l1, l2):
	for i in l2:
		if not i in l1:
			return 0
		return 1

def binread(format, f):
	n=struct.calcsize(format)
	v=struct.unpack(format, f.read(n))
	if len(v)==1:
		v=v[0]
	return v

def decompress_huffman(dat, interp):
	raise IOError("Compression not yet supported (because tiflib is incomplete)") 
	
def decampress_packbits(dat):
	raise IOError("Compression not yet supported (because tiflib is incomplete)")

def getstrips(tags, file):
	offsets=tags[273]
	bytecounts=tags[279]
	strips=[]
	for i in range(len(offsets)):
		file.seek(offsets[i])
		dat=file.read(bytecounts[i])
		if tags[259]==1:
			pass
		elif tags[259]==2 and tags[258]==1:
			dat=decompress_huffman(dat, tags[262])
		elif tags[259]==32773:
			dat=decampress_packbits(dat)
		else:
			raise IOError("Can't determine compression type")
		strips.append(dat)
	return strips

def readrgb(tags, file):
	raise IOError("RGB images not yet supported (because tiflib is incomplete)") 

def readpaletted(tags, file):
	raise IOError("Paletted images not yet supported (because tiflib is incomplete)") 
def readgrayscale(tags, file):
	convert=None
	if tags[258]==16:
		dt=UnsignedInt16
		size=2
	elif tags[258]==32:
		dt=UnsignedInt32
		size=4
	else:
		dt='b'
		size=1
		if tags[258]!=8:
			convert=tags[258]
			print "Warning: Annoying data width. Conversion may be slow"
	bs=0
	if bytepref == '<' and sys.byteorder=="big":
		bs=1
	elif bytepref == '>' and sys.byteorder=="little":
		bs=1
	strips=getstrips(tags, file)
	image=[]
	bpr= size*tags[256]
	for s in strips:
		for r in range(tags[278]):
			if len(s)<(r+1)*bpr:
				print "stripe is truncated"
				break
			row=fromstring(s[r*bpr:(r+1)*bpr], dt)
			if bs:
				row=arbyteswap(row)
			image.append(row)
	image=array(image)
	if convert:
		raise IOError("Wierd widths not yet supported (because tiflib is incomplete)")
	if tags[262]==0:
		image=max(ravel(image))-image
	return image


def readimage(tags, f):
	if not superset(tags.keys(), requiredtags):
		raise IOError("File doesn't define the minimal required set of tags")
	for k in tagdefaults:
		if not tags.has_key(k):
			tags[k]=tagdefaults[k]
	if tags[262]==2 and tags.has_key(277):
		image = readrgb(tags, f)
	elif tags[262]==3 and tags.has_key(320):
		image =readpaletted(tags, f)
	elif tags[262]<2:
		#grayscale reader also reads bilevel
		image = readgrayscale(tags, f)
	elif tags[262]==4:
		raise IOError("Mask images are not supported")
	else:
		raise IOError("Can't identify image type")
	out={"data":image}
	for tag in tags:
		if tag in [338,291,290]:
			print "Warning: should handle tag %i, but don't yet." % tag
		elif not knowntags.has_key(tag):
			print "unknown tag %i" % tag
		out[tag]=tags[tag]
	return out

def copyimage(im):
	new = {}
	for k in im:
		if type(im[k])==ArrayType:
			new[k] = im[k].copy()
		else:
			new[k] = deepcopy(im[k])
		new[k] = deepcopy(im[k])
	return new

def cloneimage(im, data):
	new = {}
	for k in im:
		if k == "data":
			continue
		elif type(im[k])==ArrayType:
			new[k] = im[k].copy()
		else:
			new[k] = deepcopy(im[k])
	new['data']=data
	return new

def istiff(fname):
	try:
		s=open(fname, 'rb').read(4)
		s=struct.unpack("ccH", s)
	except:
		return 0
	if s==("I", "I", 42):
		return "LittleEndianTiff"
	elif s==("M", "M", 42):
		return "BigEndianTiff"
	else:
		return 0
	
def readfile(fname):
	f=open(fname, 'rb')
	ftype=f.read(2)
	if ftype=="II":
		bytepref="<"
	elif ftype=="MM":
		bytepref=">"
	else:
		raise IOError("%s is not a tiff file" % fname)
	id=binread(bytepref+"H", f)
	if id!=42:
		raise IOError("%s is not a tiff file (and the mice are mad!)" % fname)
	ifd=binread(bytepref+"I", f)
	ifds=[]
	while ifd:
		dirinfo={}
		f.seek(ifd)
		n=binread(bytepref+"H", f)
		for i in range(n):
 			field={}
			dat=f.read(12)
			TAG=struct.unpack(bytepref+"H", dat[:2])[0]
 			try:
				ind=struct.unpack(bytepref+"H", dat[2:4])[0]
 				field["TYPE"]=entrytypes[ind-1]
				#print ind, field["TYPE"]
 			except:
 				print "unknown type encountered"
 				continue
			field["COUNT"]=struct.unpack(bytepref+"I", dat[4:8])[0]
			field["VALUE"]=dat[8:]
			if dirinfo.has_key(TAG):
				print "warning, redundant tag %i" % TAG
			dirinfo[TAG]=field	
		ifds.append(dirinfo)	
		ifd=binread(bytepref+"L", f)
	images=[]
	for dir in ifds:
		for tag in dir:
			field=dir[tag]
			bytes= field["COUNT"] * field["TYPE"]["SIZE"]
			if bytes<5:
				v=field["VALUE"][:bytes]
			else:
				l=struct.unpack(bytepref+"I", field["VALUE"])[0]
				f.seek(l)
				v=f.read(bytes)
			fstr=bytepref+(field["COUNT"]*field["TYPE"]["FORMAT"])
			v=struct.unpack(fstr, v)
			if field["TYPE"]["FORMAT"]=='c':
				v=map(ord, v)
			v=array(v)
			if field["TYPE"]["NAME"][-8:]=="FRACTION":
				#print tag,field["TYPE"]["NAME"] , v
				v=reshape(v, (-1,2))
				v=v[:,0].astype('d')/v[:,1]
			if len(v)==1:
				if not tag in [273,279]:
					v=v[0]
			elif field["TYPE"]["NAME"]=="ASCII":
				v=sum(v)
			dir[tag]=v
		images.append(readimage(dir, f))
	f.close()
	return images


def writeimage(data, tags, f):
	maxel=max(ravel(data))
	if maxel<256:
		tags[258]=8
		data=data.astype(UnsignedInt8)
	elif maxel<65536:
		tags[258]=16
		data=data.astype(UnsignedInt16)
	else:
		tags[258]=32
		data=data.astype(UnsignedInt32)
	if len(data.shape)==3:
		data=reshape(data, (data.shape[0], data.shape[1]*data.shape[2]))
	rs = data.shape[1]*tags[258]
	if not tags.has_key(278):
		tags[278]=int(max(1, 100000/rs))
	nstrips=int(tags[257]/tags[278])
	if tags[257] % tags[278]:
		nstrips+=1
	tags[273]=zeros(nstrips)
	tags[279]=zeros(nstrips)
	r=0
	for s in range(nstrips):
		tags[273][s]=f.tell()
		sdat=data[r:r+tags[278]]
		sdat=sdat.tostring()
		tags[279][s]=len(sdat)
		f.write(sdat)
		r+=tags[278]


def guessfieldtype(value):
	tv=max(value)
	if type(tv)==StringType:
		typ=2
	elif type(tv)==FloatType:
		if abs(tv)>3.4e38 or min(map(abs, value))<1e-43:
			typ=11
		else:
			typ=10
	elif type(tv) in [IntType, LongType]:
		if min(value)<0:
			if tv<256:
				typ=1
			elif tv<65536:
				typ=3
			else:
				typ=4
		else:
			tv=max(map(abs, value))
			if tv<128:
				typ=6
			elif tv<32768:
				typ=8
			else:
				typ=9
	else:
		typ=6
	return typ

def makeIFDentry(tag, value, writeat):
	if type(value)!=type([]):
		try:
			value=list(value)
		except:
			value=[value]
	if tagtypes.has_key(tag):
		typ=tagtypes[tag]
		if typ=="SL":
			if max(value)<65536:
				typ=3
			else:
				typ=4	
	else:
		print "Guessing datatype for tag %i" % tag
		typ=guessfieldtype(value)

	format=entrytypes[typ-1]["FORMAT"]
	entry=struct.pack('H', tag)
	entry+=struct.pack('H', typ)
	entry+=struct.pack('I', len(value))
	if typ in [5,10]:
		nvs=[]
		format=format[0]
		for v in value:
			per=1
			n, mod = divmod(v*per, 1)
			while mod>.001:
				per=per*10
				n, mod = divmod(v*per, 1)
				if per>=10000:
					mod=0
			nvs.append(int(n))
			nvs.append(int(per))
		value=nvs
	value=["%i%s" % (len(value), format)]+value
	value=apply(struct.pack, value)
	if len(value)<4:
		value=value+"\0"*(4-len(value))
	if len(value)==4:
		entry+=value
		val=None
	else:
		entry+=struct.pack('I', writeat)
		val=value
	return (entry, val)


def writefile(image, fname):
	if type(image)==ArrayType:
		tags = {}
		data = image
	else:
		data = image['data']
		tags = {}
		tags.update(image)
		del(tags['data'])
	tags[256]=data.shape[1]
	tags[257]=data.shape[0]
	tags[259]=1   #implement compression some day
	if not tags.has_key(262):
		if len(data.shape)==3:
			tags[262]=2
			tags[277]=data.shape[2]
		else:
			tags[262]=1
	if not tags.has_key(282):
		tags[282]=72.0
	if not tags.has_key(283):
		tags[283]=72.0
	f=open(fname, 'wb')
	if sys.byteorder=="big":
		f.write("MM")
	else:
		f.write("II")
	f.write(struct.pack('H', 42))
	f.write(struct.pack('I', 8))
	writeimage(data, tags, f)
	loc=f.tell()
	f.seek(4)
	f.write(struct.pack('I', loc))
	f.seek(loc)
	tks=tags.keys()
	tks.sort()
	writeat=loc+6+12*len(tks)
	f.write(struct.pack('H', len(tks)))
	values=[]
	for k in tks:
		entry, val = makeIFDentry(k, tags[k], writeat)
		f.write(entry)
		if val:
			writeat+=len(val)
			values.append(val)
	f.write(struct.pack('I', 0))
	for v in values:
		f.write(v)

	
		
	
	
		
	
