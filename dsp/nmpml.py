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
import os, tempfile

def sendData(ds, upath, dpath='/', recurse=False):
	'''Sets the data element indicated by upath to have the data and header 
values of ds (or specified subdata element, if dpath is not /). upath is
an nmpml unique path in the document containing ds, _not_ a dpath within
ds. upath obeys the behavior of NmpmlObject.getInstance, so if it begins
with a '/' it is absolute in the document, and if it does not, it is
relative to ds, but in either case it is a upath (using /tag:name
components/), not a dpath (which would use only /name/ components)

This will not alter the values in ds, or allow side effects between ds
and the new element. The new element will be created if it does not
exist, but if its container does not exist, this will raise an error.

If recurse is true, clones of any subelements of the specified data will be 
added as subelemnts of the target, and also any pre-existing subdata of the
target will be deleted.

SWITCHVALUES(recurse)=[False, True]
'''
	if dpath and dpath!='/':
		ds=ds.getSubData(dpath)
	d2=ds.getInstance(upath)
	d2.mirror(ds, recurse)
	

def receiveData(ds, upath, dpath='/', recurse=True):
	'''Sets the data and header of ds to be the same as those of the data 
element at the specified upath. If dpath is specified (and not / or None),
this function will initialize the specified subdata instead (creating it 
if needed). As with sendData, upath is not a dpath. If recuse is true, 
subdata will also be imported.

SWITCHVALUES(recurse)=[False, True]'''
	if dpath and dpath!='/':
		n=ds.getSubData(dpath)
		if not n:
			n=ds.createSubData(dpath)
		ds=n	
	d2=ds.getInstance(upath)
	ds.mirror(d2, recurse)

def saveData(ds, fname, format='mdat', dpath='/', recurse=True):
	'''Saves the data in ds (or the specified subelemnt if dpath is not /)
to the file fname, using the specified format. This will not alter values in 
ds.

SWITCHVALUES(recurse)=[False, True]'''
	if dpath and dpath!='/':
		ds=ds.getSubData(dpath)
	if not recurse:
		ds=ds.clone(False)
	from mien.parsers.fileIO import write
	write(ds, fname, format=format, newdoc=1)	
		

	
	
def clearAllData(ds):
	'''Delete all data and subdata, also sets the sample type of ds to "group". Other header attributes of ds are maintained'''
	ds.clearAll(True)
		

def loadData(ds, fname, format=None, upath=None, dpath='/', recurse=True):
	'''loads data from fname, and places it in ds (or specified 
subelement. If format is None, attempts to guess the format (usually 
this works, but sometimes it requires user interaction)

If upath is specified, attempt to find the sub-data element keyed by
upath in a complex document. If this is None (default), and fname reffers
to a complex document, this function will use the first Data instance 
returned by that documents getElements('Data') method.

SWITCHVALUES(recurse)=[False, True]'''
	import mien.parsers.fileIO
	doc=mien.parsers.fileIO.read(fname)
	if upath:
		dat=doc.getInstance(upath)
	else:
		dat=doc.getElements('Data')[0]
	if dpath and dpath!='/':
		d=ds.getSubData(dpath)
		if not d:
			ds.createSubData(dpath)
			d=ds.getSubData(dpath)
		ds=d		
	ds.mirror(dat, recurse)	
	
def setAttribute(ds, dpath='/', attrib='SamplesPerSecond', value=1.0):
	'''set an attribute on ds or the specified subdata'''
	ds=ds.getSubData(dpath)
	ds.setAttrib(attrib, value)

def callMethod(ds, upath, method='run', args=(), sendData=False, getData=False):
	'''Calls the method "method" of the nmpml element with upath, 
passing it args (method defaults to "run" and args to (), so calls 
to an nmpml run method need only specify the upath).

Args may be a tuple or a dictionary.

If sendData is True, ds is added as the first element of args if args is a tuple, or as the keyword argument "data" if args is a dictionary. 

if getData is True, the return value of the method is used to reset the data in ds. In this case the method should return one of the following: 1) a Data instance - ds will be recursively mirrored from this instance 2) a tuple of (array, dictionary) - these will be used as arguments for ds.datinit 3) a single array or list of floats - This will be used as the first argument to ds.datinit, and the header of ds will remain unchanged.
'''
	el=ds.getInstance(upath)
	meth=getattr(el, method)
	if type(args)==dict:
		if sendData:
			args['data']=ds
		o=meth(**args)
	else:
		if sendData:
			args=(ds,)+args
		o=apply(meth, args)	
	if getData:
		if type(o)==tuple:
			apply(ds.datinit, o)
		elif type(o)==ndarray:
			ds.datinit(o, ds.header())
		elif type(o)==type(ds):
			ds.mirror(o, True)
		else:
			print "Can't get data from return value %s" % (str(o),)
		
def spatialBlock(ds, sFunction='', elems=[], args=()):
	'''Calls a function from mien.spatial on the document containing ds. sFunction is a key into miien.spatial.modules.FUNCTIONS, specifying which function to call. elems is the list of upaths that is an obligatory argument for all spatial functions. args is a tuple containing the remaining arguments, if any. This must list arguments in the order expected by the spatial function. The DSP gui will provide a custom interface for setting up this tuple, which may be tricky to do by hand.'''
	doc=ds.xpath(True)[0]
	import mien.spatial.modules
	fn=mien.spatial.modules.FUNCTIONS[fn]
	args=(doc, elems)+args
	apply(fn, args)

	
def systemCall(ds, cmd='', args={}, placeholder='', fileFormat='.mat', dpath='/', recurse=True, newpath='/'):
	'''Makes a system call to cmd. Comunication with the system call is usually done by writing a temp file. If fileFormat is a False value, no file is written, cmd is called exactly as it is specified, and no change is made to ds (this can be used to configure system environment, start remote servers, or by freeks who want to use mien as a general system control framework). In the more normal case, where fileFormat is a format known to Mien (represented as a file name extension), this function operates in this way:
	1 - get the data specified by dpath and recurse
	2 - If the dictionary "args" is non-empty, assign each key as an attribute of the data (this modifies a clone of the data, not the original) 
	3 - open a secure temp file. Save the data to this tempfile. The data element will be renamed "data" and saved in fileFormat
	4 - If placeholder is a False value, append whitespace followed by the tempfile name to command. If it is any  non-empty string, replace the occurences of placeholder in cmd with the name of the temp file. 
	5 - call cmd
	6 - load a dcument from the tempfile (presumably changed by cmd), and extract the first Data element
	7 - assign the loaded element to ds at newpath
	
In general, some effort is needed to wrap your external function appropriately so that it expects to read the temp file, make correct use of the "arguments" attribute, and write it's output back to the same temp file.

SWITCHVALUES(recurse)=[True, False]
'''
	if not fileFormat:
		os.system(cmd)
		return	
	dat=ds.getSubData(dpath)
	np=ds.getSubData(newpath)
	if not np:
		ds.createSubData(newpath)
		np=ds.getSubData(newpath)
	dat=dat.clone(recurse)
	dat.setName('data')
	for k in args:
		dat.setAttrib(k, args[k])
	id, fname=tempfile.mkstemp(fileFormat)
	fobj=os.fdopen(id, 'w')
	import mien.parsers.fileIO as io
	io.write(dat, fobj, format=fileFormat, newdoc=1)	
	fobj.close()
	if placeholder:
		cmd=cmd.replace(placeholder, fname)
	else:
		cmd=cmd+" "+fname	
	print cmd	
	os.system(cmd)
	doc=io.read(fname)
	os.unlink(fname)
	dat=doc.getElements('Data')[0]
	np.mirror(dat, recurse)	

def matlabCall(ds, mfile='testmien', args={} ,dpath='/', recurse=True, newpath='/', safe=True, mfiledir=''):
	'''This is a thin wrapper around the "systemCall" block (from this module), designed for calling Matlab functions. It assumes fileFormat is ".mat", and "cmd" is constructed as "matlab --nojvm --nosplash -r mfile(fname)" where mfile is the argument to this function with that name, and fname is the name of the temporary file. If safe is True, the command is also wrapped such that Matlab will always exit (and return control to MIEN) even if the mfile fails. This is recommended, but it may be useful to set safe to False for some debugging purposes. If safe is False, the mfile must call Matlab "quit" explicitly, or you must do so interactively. If mfiledir is a non-empty string, it is prepended to the matlab path before attempting to execute "mfile" (thus, if it is the directory containing mfile, this allows execution even when this directory isn't known to matlab by default)

SWITCHVALUES(recurse)=[True, False]
SWITCHVALUES(safe)=[True, False]
	'''
	cmd='%s(\'FNAME\')' % (mfile,)
	if mfiledir:
		s = "path('%s', path);" % mfiledir
		cmd = s + cmd
	if safe:
		cmd='try,' + cmd + ',catch,quit,end;quit'
	cmd='matlab -nojvm -nosplash -r "' + cmd + '"'
	systemCall(ds, cmd , args, "FNAME", '.mat', dpath, recurse, newpath)
	
