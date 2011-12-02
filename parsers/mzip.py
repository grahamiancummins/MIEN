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
from zipfile import ZipFile
from StringIO import StringIO
from mien.math.array import zeros, ArrayType, reshape, fromstring, any, ravel
import  struct, sys, zlib, time 
import mien.xml.xmlhandler as xm


def readZip(f, **kwargs):
	from mien.parsers.nmpml import elements as dialect
	f=ZipFile(f, 'r')
	xml=f.read('xml')
	xml=StringIO(xml)
	doc=xm.readTree(xml)
	xml.close()
	doc=xm.assignClasses(doc, dialect)	
	try:
		dat=f.read('data')
	except:
		print "No data archive in zip file"
		return doc
	from mien.parsers.datahash import readMD	
	dat=StringIO(dat)
	dat=readMD(dat, return_raw_hash=True)
	des=doc.getElements('Data')
	for de in des:
		try:
			d, h=dat[de.upath()]
		except:
			print "can't find data for element %s" % (de.upath(),)
			d, h=(zeros(0), {})
		de.datinit(d, h)
	f.close()	
	return doc		

def writeZip(f, doc, **kwargs):
	f=ZipFile(f, 'w')
	xml=StringIO()
	xm.writeXML(xml, doc)
	xml=xml.getvalue()
	f.writestr('xml', xml)
	dat=StringIO()
	from mien.parsers.datahash import writeMD	
	writeMD(dat, doc)
	dat=dat.getvalue()
	if dat:
		f.writestr('data', dat)
	f.close()	


def serialize(f, doc, **kwargs):
	xml=StringIO()
	xm.writeXML(xml, doc)
	tree=xml.getvalue()
	tree=zlib.compress(tree)
	l=len(tree)
	l=struct.pack('<I', l)
	dat=StringIO()
	from mien.parsers.datahash import writeMD	
	writeMD(dat, doc)
	dat=dat.getvalue()
	if dat and kwargs.get("compress"):
		dat=zlib.compress(dat)
	s=str(l)+tree+dat
	if f!=None:
		f.write(s)
	else:
		return s


def deserialize(f, **kwargs):
	#st=time.time()
	if not type(f) in [str, unicode]:
		f=f.read()
	l=struct.unpack('<I', f[:4])[0]
	doc=zlib.decompress(f[4:l+4])
	doc=StringIO(doc)
	doc=xm.readTree(doc)
	from mien.parsers.nmpml import elements as dialect
	doc=xm.assignClasses(doc, dialect)	
	f=f[l+4:]
	try:
		if f:
			from mien.parsers.datahash import readMD	
			try:
				f2=StringIO(f)
				f=readMD(f2, return_raw_hash=True)
			except:
				f=zlib.decompress(f)		
				f2=StringIO(f)
				f=readMD(f2, return_raw_hash=True)
			del(f2)
			des=doc.getElements('Data')
			for de in des:
				try:
					d, h=f[de.upath()]
				except:
					print "can't find data for element %s" % (de.upath(),)
					d, h=(zeros(0), {})
				de.datinit(d, h)
	except:
		print "cant load data"
					
	#print time.time()-st;st=time.time()

	return doc		

		
filetypes={}			
				
filetypes['Mien Zipped']={'notes':'Stores an nmpml file and its associated data in a single compressed archive',
							'read':readZip,
							'write':writeZip,
							'data type':'any',
				'elements':'all',
				'extensions':['.mzip', '.zip'],
				'autoload':True}

filetypes['Mien']={'notes':'Stores an nmpml file and its associated data in a  serialized format',
							'read':deserialize,
							'write':serialize,
							'data type':'any',
				'elements':'all',
				'extensions':['.mien', '.mgz'],
				'autoload':True}
