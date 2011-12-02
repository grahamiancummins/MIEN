#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2008-06-19.

# Copyright (C) 2008 Graham I Cummins
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

import os, re
from mien.image.arrayops import concatenate, image_to_array, array_to_image
import mien.parsers.nmpml

wxbitmaptypes={'ANI': 27,
 'ANY': 50,
 'BMP': 1,
 'CUR': 5,
 'GIF': 13,
 'ICO': 3,
 'ICON': 25,
 'IFF': 28,
 'INVALID': 0,
 'JPEG': 17,
 'MACCURSOR': 30,
 'PCX': 21,
 'PICT': 23,
 'PNG': 15,
 'PNM': 19,
 'TGA': 29,
 'TIF': 11,
 'XBM': 7,
 'XBM_DATA': 8,
 'XPM': 9,
 'XPM_DATA': 10}

FORMAT_INFO={'Bitmap':('BMP', ['.bmp']), 
	'Tagged Image File':('TIF', ['.tif', '.tiff']),
	'Portable Network Graphic':('PNG', ['.png']), 
	'Joint Photographic Experts Group (JPEG) Image':('JPEG', ['.jpg', '.jpeg'])}


				 
snumber=re.compile("(\d+)$")
leica_series=re.compile(r"_z(\d+)_ch\d+$") #leica multichannel extension

def image_init():
	try:
		import wx
	except:
		raise IOError("Image file formats are only supported if wxWidgets is installed (and running)")	
	a=wx.GetApp()
	if not a:
		print("WARNING: Image file support requires a wxWidgets application, but you are running in text mode. Starting a wxApp now. This may fail nastily on some systems")
		a=wx.PySimpleApp()
	return wx	



def next_sequence_name(fname):
	bn, e=os.path.splitext(fname)
	m=leica_series.search(bn)       
	if m:
		ti=m.group(1)
		l=len(ti)
		fs="%0"+str(l)+"i"
		ti=fs % (int(ti)+1,)
		fname=bn[:m.start()+2]+ti+bn[m.start()+2+l:]+e
		return fname
	m=snumber.search(bn)
	if m:
		ti=m.group(1)
		l=len(ti)
		fs="%0"+str(l)+"i"
		ti=fs % (int(ti)+1,)
		fname=bn[:m.start()]+ti+e
		return fname
	return bn+"0000"+e
		


def read(fileobj, **kwargs):
	try:
		fname=fileobj.name
		attr={"Url":fname}
	except:
		fname=None
		print("Image loaded from stream or url. Will not attempt to detect image stacks. If this is a stack, load it from a file")
	header={}
	wx=image_init()
	if fname:
		im=wx.Image(fname)
		a=[image_to_array(im)]
		BandW= a[0].shape[2]==1
		fname=next_sequence_name(fname)
		while os.path.isfile(fname):
			print("adding %s to image stack" % fname)
			im=wx.Image(fname)
			na=image_to_array(im, BandW)
			a.append(na)
			fname=next_sequence_name(fname)
		if len(a)==1:
			a=a[0]
		else:
			a=concatenate(a,3)
	else:
		im=wx.EmptyImage()
		im.LoadStream(fileobj)
		a=image_to_array(im)
	header['SampleType']='image'
	header['Bytes']=True
	de=mien.parsers.nmpml.createElement('Data', {'Url':kwargs['unparsed_url']})
	de.datinit(a, header)
	n = mien.parsers.nmpml.blankDocument()
	n.newElement(de)
	return n


def _udir(bname):
	dname = bname
	if os.path.exists(dname):
		dname = bname+"_imagestack"
	i=2
	while os.path.exists(dname):
		dname = bname+"_imagestack%i" % i
		i+=1
	os.mkdir(dname)
	#print "called, returning %s" % dname
	return dname

def write(fileobj, doc, **kwargs):
	fmt = kwargs.get('format', "Tagged Image File")
	fcode=wxbitmaptypes[FORMAT_INFO[fmt][0]]
	images=doc.getElements('Data', {'SampleType':'image'})
	wx=image_init()
	if len(images)==1:
		dat=images[0].getData()
		if len(dat.shape)<4 or dat.shape[3]==1:
			im=array_to_image(dat, images[0].attrib('ColorRange'), images[0].attrib('pseudocolor'), wx)
			im.SaveStream(fileobj, fcode)
			return
	if not type(fileobj)==file:	
		raise IOError('writing multipart data to image formats is only supported for local files')
	fname=fileobj.name	
	bname, ext = os.path.splitext(fname)
	fileobj.close()	
	os.unlink(fname)
	for im in images:
		dname = _udir(bname)
		if len(dat.shape)<4 or dat.shape[3]==1:
			img=array_to_image(im.getData(), im.attrib('ColorRange'), im.attrib('pseudocolor'), wx)
			img.SaveFile(os.path.join(dname, "image")+ext, fcode)
		else:
			dat = im.getData()
			for i in range(dat.shape[3]):
				d = dat[:,:,:,i]
				fname = os.path.join(dname, "frame%04i" % (i,)) +ext
				img=array_to_image(d, im.attrib('ColorRange'), im.attrib('pseudocolor'), wx)
				img.SaveFile(fname, fcode)
	
	
	

filetypes={}	

for name in FORMAT_INFO.keys():			 
	filetypes[name]={'notes':"image format",
					'read':read,
					'write':write,
					'data type':'numerical/image',
					'elements':['Data'],
					'extensions':FORMAT_INFO[name][1]}
		