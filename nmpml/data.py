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

import basic_tools
from mien.math.array import *
from string import join, split
import os



def getDataServer(doc):
	'''check the document for a DataServ generate a DataServe class for a
DataServer stored as doc._dataserver. If it is found, return it. if not, 
create it and then return it'''
	if not doc.__dict__.has_key('_dataserver'):
		from mien.tools.dataserver import DataServer
		fn=doc.fileinformation["filename"]
		doc._dataserver=DataServer(fn, doc)
	return doc._dataserver
		
def genslice(s, ml):
	'''make a python slice object from a sequence s. See Data.getData
for the rules of interpretation. ml is the maximum length, used to substitute
real indexes for the string ":" '''
	if not s:
		return slice(0,ml)
	if type(s)==slice:
		return s
	s=list(s)
	if len(s)==1:
		if s[0]==":":
			s=[0, ml]
		else:
			s=[0, s[0]]
	elif s[1]==':':
		s=[s[0], ml]
	return apply(slice, s)		

def list2slice(l):
	l.sort()
	if l==range(l[0], l[-1]+1):
		return slice(l[0],l[-1]+1)
	else:
		return None

def checkSampleType(dat, head):
	t=head.get("SampleType")
	fs=head.get("SamplesPerSecond")
	try:
		fs=float(fs)
	except:
		fs=None
	if not t:
		if len(dat.shape)>2:
			return 'locus'
		if dat.shape[1]==1 and dat.dtype in [Int64, Int32]:
			if all( (dat - shift(dat, 1))[1:]>0 ):
				return 'events'	
			else:
				return 'histogram'
		if dat.shape[1]>=2 and dat.dtype in [Int64, Int32]:
			return 'labeledevents'
		if dat.dtype in [Int64, Int32] and fs:
			return 'histogram'
		if fs:
			if head.get('Reps'):
				return 'ensemble'
			else:	
				return "timeseries"
		return "function"
	else:
		t=str(t)
		if not t in ["timeseries", "ensemble", "events", "labeledevents", "histogram", "function"]:
			return t
		if len(dat.shape)==2:
			if t=='timeseries' and fs:
				return t
			if t=='events' and dat.shape[1]==1:
				return t
			if t=='labeledevents' and dat.shape[1]>=2:
				return t
			if t=='ensemble' and fs and head.get('Reps'):
				return t
			if t=='function':
				return t
			if t=='histogram':
				if dat.dtype in [int64, int32]:
					return t
				else:
					print dat.dtype
					print "warning, histogram is not integer type?"
					return t
		print dat.shape, head
		raise StandardError('SampleType %s not compatible with this data and header' % t)

def newHeader(st='timeseries', fs=1.0, l=None, start=0.0):
	'''Generate a new data header containing the most common attributes: SampleType, SamplesPerSecond, Labels, and StartTime. The arguments of this function are a tuple of those values in that order. If unspecified, they default to "timeseries", 1.0, None, and 0.0 respectively. If you want to specify keyword arguments, use st, fs, l, and start'''
	return {'SampleType':st, 'SamplesPerSecond':fs, 'Labels':l, 'StartTime':start}

def newData(d, h):	
	ob={'tag':'Data', 'attributes':{}, 'elements':[], 'cdata':[]}
	di=Data(ob)
	di.datinit(d, h)
	return di

class Data(basic_tools.NmpmlObject):
	'''This tag is used for refferring to externally stored binary data

Methods provided by this class relate to accessing, setting, and storing 
data. See the module mien.datafiles.DataSet for methods used to manipulate 
specific aspects of the data.

Url Attribute

The location of the data is determined by the attribute Url. In general this
is a standard http, ftp, or file url. In addition, the types auto:// and 
sftp are supported, and the syntax for parameters has been 
extended to allow access to particular paths within hierarchial data files.

BTW: if you are having trouble with file urls, note that a local file must 
be refferenced with three slashes "file:///foo/bar" -> /foo/bar. To 
get a local relative path (if for some reason you must :) don't use 
file://. Just use the path by itself "foo/bar". 

Hierarchial data files: A typical url looks like this:
scheme://netloc/path;parameters?query#fragment. For Data urls other than 
http (which can be used to access specialized database servers that 
define their own url specs for parameters and querry) the only components 
specified will be scheme://netloc/path?querry. If querry is specified 
in this way, it is used to access a particular data record inside a 
hierarchial data file, shelf, or dbm. file:///path/to/file?/path/to/data
will return the element stored in the key or path "/path/to/data" inside the 
hierarchial data file "/path/to/file".;;

Url Type "file": The file url may contain a colon after the path: 
file:///path/to/file:/path/to/data
In this case, the data returned is the element stored in the key or path 
"/path/to/data" inside the hierarchial data file "/path/to/file". This 
url type works for shelves, anydbms, hdf 5 files, etc.

Url type "auto": This means that the data is stored in a hierachial
archive with the samoe base name as the xml file containing the data tag. This 
name will change if, for example, the end user saves the xml under a new
name. The document's DataServer instance will track this change automatically,
so you will newer need to provide a file name. This is the recommended mode
for storeing data that is output by parametric or interactive models that 
are frequently modified. The entire string after the "auto://" acts as a key
for the data. Currently DataServer uses shelve to store data, so this can be
any string, and resemblence to a path is strictly for human convienience. 
In the future DataServer may use HDF 5, in which case having this be a true 
hierarchial path is usefull. Using Paths may also allow scripts to reconstruct 
the data hierarchy if the data store is retained but the corresponding xml is 
lost. As a further shortcut, the url "auto://upath" is replaced at access time
with the upath of the Data instance. This provides a nice unique key that  
tracks user changes to the object, and is recommended. 

Url type "sftp": This looks just like an "ftp" url, but uses ssh/sftp for 
retrieval. 

Spatial Attribute

If set, this specifies that some columns in the numerical data represent 
spatial coordinates. The attribute should be a list of three ints, specifying 
the column index for the x, y, and z coordinate respectively. This attribute may 
be used by external functions. Internally, it is used by the doAlignment method

# TODO Implement Spatial attribute

SampleType attribute

This attribute determines how the data are interpreted. In additon, Data 
elements with different SampleType may have different accessor methods, be
displayed differently by GUIs, etc. The methods "addData" and "extendData"
will act differently depending on the values of this attribute for the two 
Data elements (In general, both methods will only work if the SampleTypes are
the same, and will otherwise nest the data). SampleType is not a required 	
attribute, but if it is omitted, the function "datinit" will attempt to guess
it. It is possibel to have a Data insance with no sample type, which may have 
any dimension or (numerical) type. In this case, no special data access and 
processing methods will be function as expected, but core methods will still 
work. If you intend to do this, and want to avoid having mien guess a sample 
type for you, set SampleType to "generic" (actually, any True value not 
listed below works, but "generic" will never be used for a defined type in 
a future version).

Supported sample types are as follows:

group - There are no data. This element simply serves to group other Data 
elements. This can be used,for example, to collect 10 different sets of
"events" type data, since these can't all be stored in the same element, 
but may be semantically related. 

timeseries - The data are a 2D array, with sequential, evenly spaced, samples
in time presented in each row. The columns are reffered to as "channels" by 
analogy to the channels of a DAQ device. The attribute "SamplesPerSecond" is 
required for timeseries. Most "analog" data in neuroscience are timeseries. 
(This type can be used to represent any data that are uniformly sampled in the
independant variable. Mien GUIs and method names will call this "time", but 
the methods will work the same if it is in fact space, frequency, etc. In
general, Mien will use the words "time" and "independent variable" 
interchangably, but if you use some other independant variable, don't be 
concerned by the nomenclature. All the functions should still work as expected)

ensemble - Like a timeseries, but each distinct dimension (channel) contains
many samples, so the number of channels is smaller than the number of columns 
in the array. The attribute "Reps" indicates the number of columns per channel
(which must be the same for all channels). Data in an ensemble are arranged such 
that the first "Reps" columns of the data array are the repetitions of the first
channel, and the first repetition of the second channel occurs at channel index
"Reps".

events - The data are an Nx1 array, and represent sequential, binary, events
(e.g. action potentials). "SamplesPerSecond" must be specified, and
the values are the indexes of the sample row on which the event occurs. 

histogram - The data are an NxM integer array, representing the number of 
some event that fall in equally spaced sequential bins in the independent
variable. Usually M==1 and separate instances are used for 
different events, but multichannel histograms will work as expected.

labeledevents - The data are an Nx>=2 array. The first column is interpretted
as for "events" type, but need not be sequential. The second column is the
"label" of the event (e.g. the id of the unit that generated a spike). Optional third and further columns may provide additional label information (intensity, stimulus that elicited the event, etc.). The Data element will handle these  "multilabeledevevts" correctly (although the shape method will still return the number of units based on the first label), but not all of the extension functions in the dsp and datafiles modules are certain to handle them correctly..

function - The data are a 2D array, similar to a timeseries, but the values
of the idependent variable are explicitly listed in the first column. These 
must be unique and monotonic. The datafiles.dataset "resample" function can 
convert "function" type data to timeseries. (Dataviewer will automatically
resample a function if you try to display one)

locus - The data are an NxM array representing N points in R-M. As a 
result the values in any column may be non-monotonic and non-unique. 
(Note that the Dataviewer GUI can't deal with locus data. It will try to 
spawn a simple graph to display 2 or 3D loci. Higher dimensional loci can't 
be displayed at all).

image - The data represent the intensity level of an image. Data must be at least 2D (X and Y pixels). If there is a third dimension, it represents the color channels of a color or alpha masked image. If there is a fourth dimension, it represents sequential images in an image sequence or stack. Images can use the special header values "PixelWidth", "PixelHeight", "IntensityRange". Stacks may also specify "StackSpacing".

mask - The data are an Nx1 array or NxM array. The values are "density" values 
	associated to values stored in the container. The container is usaually a 
	PointContainer (or subclass) or another Data element. Data elements of
	sampletype "Image" may have NxM masks representing alpha channels or 
	other similar information. PointContainers and Data of most other 
	sampletypes (Timeseries, Function, Locus, etc.) should use Nx1 masks.
	If there is more than one mask value, use more than one mask type Data 
	element nested in the same container. Do not use an NxM mask where the 
	columns represent multiple mask values. This was done in early versions 
	of the depricated class nmpml.Table, but will no longer be correctly
	interpretted. Note that masks may become "stale" if the number of points 
	or pixels in the container is changed by the user. User functions are 
	responsible for their own maintenance of mask/container corespondance. 

table - The data are an NxM array. Rows in the data represent database records
	or other collections of related numbers. The "tableLookup" and "tableInterp"
	methods provide access to table elements.

sfield and v field - Scalar and Vector fields. Data are NXxNYxNZ arrays for sfields,
	and NXxNYxNZxO fields for vector fields of order O. The N(XYZ) are a number of samples
	in the x,y,and z dimensions. In principal fields in any R**m can be used, and the data 
	shape is then m N entries (for an sfield), or m Ns followed by O for a vfield. Fields
	should define attributes "Edge" - the length between sample points, and "Origin" - the
	location of sample 0,0,0. Origin is a list of length m. In future implementations, "Edge"
	may also be a list of length m, but it is currently a scalar.
	
	Currently there is very limited special support for fields, except as used by 
	the CellViewer and the SpatialField tag. Both of these support sfields with m=3 only.
	External extensions may make more use of field data in the future.
'''
	_allowedChildren = ["Comments", "Data"]
	_requiredAttributes = ["Name", "Url"]
	_specialAttributes = ['Labels', 'Start', 'Stop', 'SamplesPerSecond', 'SampleType', 
		'StartTime', 'Spatial']
	
	_guiConstructorInfo = {'Url':{"Name":"Url",
								  "Value":""
								  }}
	_hasCdata = False

	def __init__(self, node, container=None):
		''' values(array=None), **args =>instance'''
		if not node['attributes'].has_key('Url'):
			node['attributes']['Url']='auto://upath'
		#cl=self.__class__.__bases__[0]
		basic_tools.NmpmlObject.__init__(self, node, container)
		self.data=None
		self._autonymous=False
		self.undolist=[]
		self.redolist=[]
		self.undolength=0
		self.info={}
		self.logflags={'undoCheckpoints':False}
	
		
	def clipUndoList(self):
		if not self.undolength:
			self.undolist=[]	
		elif self.undolength<len(self.undolist):
			if not self.logflags['undoCheckpoints']:
				self.undolist=self.undolist[-self.undolength:]
			else:
				l=self.undolist.count('checkpoint')
				if self.undolength<l:
					i=self.undolist.index('checkpoint')
					self.undolist=self.undolist[i+1:]
		
	def log_change(self, action, args=[], path=None):
		'''Used to record actions for undo. The general use is that "action" is
the name of a method (a string), args is a sequence of arguments to that
method, and path is the dpath of the changed instance. Executing that
method of that instance on those arguments should undo the change that
is being logged.

This method always calls "up" to the "getTop" data instance, to avoid
maintaining undo state for the same data tree in more than one place
(but as a result, if a Data element is moved out of its containing tree,
it will have no undo history of its own)

There are several extended uses, indicated by using special values of
"action":

checkpoint - set an undo checkpoint (used if 
self.logflags['undoCheckpoints'] is True). This is the most common form of 
external call to this function.

start - start recording a compound action (where a single undo step will
need to make several method calls). It can also be used to aid exception 
handling for an otherwise simple action 
done - end a compound action 
abort - remove any steps recorded since the last "start" (use this if a 
method fails partway through)

The arguments path is used by internal calls to this function,
and probably shouldn't be set by external callers.
'''
		state=self.logflags.get('state')
		if self.logflags.get('disable'):
			return		
		if not self.isTop():
			self.getTop().log_change( action, args, path=self.dpath() )
		if not self.undolength or not self.attrib('SampleType'):
			return
		if action=='checkpoint':
			if not self.logflags['undoCheckpoints']:
				print "Ignoring checkpoint"
				return
			else:	
				self.logflags['recording']=None
				if state:
					pass
				else:
					self.undolist.append('checkpoint')
					self.clipUndoList()
				return
		if not state:
			self.redolist=[]
		if action=='start':
			self.logflags['recording']=[]
			return
		if action=='abort':
			self.logflags['recording']=None
			return
		if action=='done':
			l=self.logflags['recording']
			self.logflags['recording']=None
			if not l:			
				return
			log=l
		elif type(self.logflags.get('recording'))==list:
			self.logflags['recording'].append([action, args, path])
			return
		else:
			log=[[action, args, path]]
		if state=='undo':
			q=self.logflags.get('lastundo', [])
			q.extend(log)
			self.logflags['lastundo']=q
		elif state=='redo':
			q=self.logflags.get('lastredo', [])
			q.extend(log)
			self.logflags['lastredo']=q
		else:	
			self.undolist.append(log)

	def undo(self):
		'''Step back one block of actions in self undolist (if it exisits).
If self.logflags['undoCheckpoints'], step back to the last checkpoint.'''
		if not self.undolist:
			return
		if not self.logflags['undoCheckpoints']:
			actions=self.undolist.pop()
		else:
			while self.undolist and self.undolist[-1]=='checkpoint':
				self.undolist.pop()
			actions=[]	
			while self.undolist:
				a=self.undolist.pop()
				if a=='checkpoint':
					break
				actions.extend(a)
			if not actions:
				return
		actions.reverse()
		self.logflags['state']='undo'
		try:
			for a in actions:
				print a
				e=self.getSubData(a[2])
				m=getattr(e, a[0])
				apply(m, a[1])
			self.redolist.append(self.logflags['lastundo'])
		except:
			self.report('Undo failed')
			raise
		self.logflags['state']=None
		try:
			del(self.logflags['lastundo'])
		except:
			pass
			
	def redo(self):
		''' '''
		if not self.redolist:
			return
		actions=self.redolist.pop()
		actions.reverse()
		self.logflags['state']='redo'
		try:
			for a in actions:
				e=self.getSubData(a[2])
				m=getattr(e, a[0])
				apply(m, a[1])
			if self.logflags['undoCheckpoints']:
				if self.undolist and self.undolist[-1]!='checkpoint':
					self.undolist.append('checkpoint')
			self.undolist.append(self.logflags['lastredo'])
			if self.logflags['undoCheckpoints']:
				self.undolist.append('checkpoint')
		except:
			self.report('Redo failed')
			raise
		self.logflags['state']=None
		del(self.logflags['lastredo'])

	def setAttrib(self, a, v, inherit=False, log=True):
		'''Subclassed from parent method to allow undo'''
		ov=self.attrib(a)	
		basic_tools.NmpmlObject.setAttrib(self, a, v, inherit)
		if log:
			self.log_change('setAttrib', (a, ov, inherit))
		
	def removeElement(self, e):
		'''Subclassed from parent method to allow undo'''
		basic_tools.NmpmlObject.removeElement(self, e)
		self.log_change('newElement', (e,))
		
	def newElement(self, e):
		'''Subclassed from parent method to allow undo'''
		#basic_tools.NmpmlObject.newElement(self, e)
		self.__class__.__bases__[0].newElement(self, e)
		self.log_change('removeElement', (e,))		

	def setUndoLength(self, n, cp=False):
		'''recursively set the length of the undo length for the whole
data tree, and purge the contents of the undo lists if needed. Setting
n=0 will disable undo completely, and may reslut in substantially
improved speed of operations, as well as reduced memory use.

If "cp" is True, then the flag self.logflags['undoCheckpoints'] is set.
This means that the undo and redo commands step between "checkpoint"
entries stored in the undo list, and the length of the list is
interpreted as the number of checkpoints, not the number of actions
(basically, the list will be bigger, and if the calling app isn't
careful about setting its own checkpoints, it may grow without bound)
''' 
		if not self.isTop():
			self.getTop().setUndoLength(n)
		self.undolength=n
		self.logflags['undoCheckpoints']=cp
		self.clipUndoList()
		dats=self.getElements("Data")
		for q in dats:
			q.undolength=n
			q.undolist=[]
			if n==0:
				q.logflags['disable']=True 
			else:
				q.logflags['disable']=False 
			
	def setData(self, dat, chans=None, range=None):
		'''Assigns data to self.data. This using this method allows "undo" to 
recover the old data. This uses slice assignment, so there are no side effects. 
chans and range are interpreted as in getData.

If dat is 1D, it is upcast to 2D, with 1 column. If dat is not an array, it is 
cast to array.
'''
		if not type(dat)==arraytype:
			dat=array(dat)
		if len(dat.shape)==1:
			dat=reshape(dat, (-1, 1))	
		if range:
			range=genslice(range, self.data.shape[0])
		else:
			if not chans:
				if dat.shape!=self.data.shape:
					raise IndexError("Wrong size data. (Perhaps you need addChans, delChans, concat, or crop)")					
			range=slice(0, self.data.shape[0])
		if not dat.dtype==self.data.dtype:
			dat=dat.astype(self.data.dtype)
		if not chans:
			chans=slice(0, self.data.shape[1])
		elif type(chans)==list:
			chans=list2slice(chans) or chans
		if type(chans)==list and dat.shape[0]==1:
			#avoid a bus error in numpy
			s=(range.stop - (range.start or 0), len(chans))
			dat=dat[0,0]*ones(s,self.data.dtype) 
		self.log_change('start')	
		self.log_change('setData', (self.data[range,chans].copy(), chans, range))
		try:
			self.data[range,chans]=dat
			self.log_change('done')
		except:
			self.log_change('abort')
			raise
	
	def getChanName(self, i, prefix=True):
		'''Returns the name of the ith channel. This is constructed as follows:
If prefix, return "url - channame", unless url is uspecified or contains "auto". Then use self.dpath() instead of url.
If prefix is false, return just channame

To get channame, use the first of these methods to return a true value:		
		
Self.attrib('Labels')[i]. 
If there is only one channel, return self.name()
return the string "c%i" % i
'''
		try:
			cn= str(self.attrib('Labels')[i])
		except:
			if self.data==None or self.data.shape[1] == 0:
				return ''
			if self.data.shape[1]==1:
				cn= self.name()
			else:	
				cn = "c%i" % i
		if prefix:
			dn=self.attrib('Url')
			if not dn or self.attrib("Type")=="Auto" or dn.startswith('auto://'):
				dn=self.dpath()
			if not cn.startswith(dn):	
				cn = "%s - %s" % (dn, cn)
		return cn	
			
	def setChanName(self, n, i):
		'''Sets the label of channel i to n'''
		l=self.getLabels()
		l[i]=n
		self.setAttrib('Labels', l)
		
	def getLabels(self, prefix=False):
		'''returns [self.getChanName(i) for i in range(self.shape()[1])]'''
		return [self.getChanName(i, prefix) for i in range(int(self.shape()[1]))]
	
	def fs(self):
		'''returns SamplesPerSecond, or None if not uniformly sampled'''
		s=self.attrib('SamplesPerSecond')
		try:
			s=float(s)
		except:
			s=None
		return s	
	
	def start(self):
		'''Return the start time of a time series, or the smallest x of a function'''
		if self.fs():
			s=self.attrib('StartTime') 
			if not s:
				s=0.0
		else:
			s=self.getData()[:,0].min()
		return s	
			
	def crop(self, range):
		'''Reduce the range of self.data to the slice "range", which 
is specified as described for getData
'''
		range= genslice(range, self.shape()[0]+1.)
		ld=rd=None
		if range.start:
			ld=self.data[:range.start,:]
		if range.stop and range.stop<self.data.shape[0]:
			rd=self.data[range.stop:,:]
		self.data=self.data[range]
		if ld!=None:
			self.log_change('start')
			if self.attrib('StartTime')!=None and self.fs():
				nst=self.attrib('StartTime')+ld.shape[0]/self.fs()
				self.setAttrib('StartTime', nst, log=False)
			self.log_change('concat', (ld, True))
			if rd!=None:
				self.log_change('concat', (rd, False))
			self.log_change('done')
		elif rd!=None:
			self.log_change('concat', (rd, False))
	
	def concat(self, dat, prefix=False):
		'''Add the data in the array dat to the data in self, concatenating 
along the first dimension (rows). dat must have the same number of
columns as self.data. If prefix is true, add dat before self data (and
change fix self.attrib("Start") if it is specified)'''

		if prefix:
			self.data=concatenate([dat, self.data])
			self.log_change('crop', ((dat.shape[0], ':'),))		
			if self.attrib('StartTime')!=None and self.fs():
				nst=self.attrib('StartTime')-dat.shape[0]/self.fs()
 				self.setAttrib('StartTime', nst, log=False)

		else:
			l=self.data.shape[0]
			self.data=concatenate([self.data, dat])
			self.log_change('crop', ((l,),))		
		
	def addChans(self, dat, names=None, indexes=None):
		'''Adds the channels in dat to self.data. This function concatenates 
along the second dimension (columns), such that the columns of dat are 
appended to the columns of data. If indexes is specified, inserts at the 
indicated indexes.

If names is specified, this also assigns to self.attrib("Labels")'''
		if len(dat.shape)==1:
			dat=reshape(dat, (-1, 1))		
		if self.attrib('Labels') and not names:
			names=['new%i'%i for i in range(dat.shape[1])] 
		if names:
			labels=self.getLabels()
			if not indexes:
				labels=labels+names
			else:
				new=[]
				j=0
				for i in range(self.data.shape[1]):
					if i in indexes:
						k=indexes.index(i)
						new.append(names[k])
					else:
						new.append(labels[j])
						j+=1
				labels=new		
		else:
			labels=None
		if indexes!=None:
			indexes=list(indexes)
			new=zeros((self.data.shape[0], self.data.shape[1]+dat.shape[1]), self.data.dtype)
			j=0
			for i in range(new.shape[1]):
				if i in indexes:
					k=indexes.index(i)
					new[:,i]=dat[:,k]
				else:
					new[:,i]=self.data[:,j]
					j+=1
			self.data=new		
		else:
			self.data=concatenate([self.data, dat], 1)
		if not indexes:
			indexes=range(self.data.shape[1]-dat.shape[1], self.data.shape[1])
		if labels:
			self.log_change('start')
			self.setAttrib('Labels',labels)
			self.log_change('delChans', (indexes,))
			self.log_change('done')
		else:
			self.log_change('delChans', (indexes,))
		
	def delChans(self, indexes):
		'''Deletes the channels at the indicated indexes'''
		l=self.getLabels()
		newl=[l[x] for x in range(len(l)) if not x in indexes]
		dl=[l[x] for x in indexes]
		if self.stype()=='ensemble':
			allchans=[]
			r=self.attrib('Reps')
			for ci in indexes:
				ci=ci*r
				cr=range(ci,ci+r)
				allchans.extend(cr)		
			indexes=allchans	
		mask=setdiff1d(arange(self.data.shape[1]), unique(indexes))
		newd=take(self.data, mask, 1)
		oldd=take(self.data, array(indexes), 1)
		self.data=newd
		self.setAttrib('Labels', newl, log=False)
		self.log_change('addChans', (oldd, dl, indexes))
	
	def datinit(self, dat, head={}, copy=False):
		'''Used to set, or reset, the data and header for the instance at once.
If "copy" is True, the array "dat" will be copied (avoiding side effects, but 
using more time and memory). Dat is automatically cast to array if needed.  
This method is useful for initially importing data, or of assigning data generated 
by an external source. It's also a good idea to use this method if you want to change 
SampleType. Other changes should use setData, setAttrib, etc. 

'''
		if dat!=None and copy:
			dat=dat.copy()
		h=self.header()
		for k in head.keys():
			basic_tools.NmpmlObject.setAttrib(self, k, head[k])
		if not dat == None:
			if not type(dat)==arraytype:
				dat=array(dat)
			elif copy:
				dat=dat.copy()
			if len(dat.shape)==1:
				dat=reshape(dat, (-1, 1))
			self.attributes['SampleType']=checkSampleType(dat, self.attributes)
		self.log_change('datinit', (self.data, h))
		self.data=dat
		
	def getData(self, chans=None, range=None, copy=False):
		'''return the data stored in this object. This function will try to 
load data if it hasn't loaded yet, so it is more reliable than mucking with the 
attribute "data" directly. The default is to return a reference to the entire 
array self.data. Arguments, if they are specified and true, act as follows:
chans - a 1D sequence type. Return only the channels (columns) listed in the 
	sequence from the data
range - a python slice instance, or a 1D sequence with 1, 2, or 3 members. Slice
	the data (return a subset of the rows). If this is a slice, it is applied 
	directly. If it is a sequence, a slice is constructed using the following 
	rules: 
		If there is one element, it is used as the stop index, with start at 0
		If the stop index is the string ":", use the sequence length. 
		If a third index is specified, this is used as a step
copy - return a copy, not a reference (costs more, and avoids side effects)		
'''	
		if self.data==None:
			try:
				self.onLoad()
			except:
				pass
		if self.data==None:	
			return zeros((0,1))
		dat=self.data
		if chans:
			if type(chans)==int:
				chans=[chans]
			dat=take(dat, chans, 1)
		if range:
			s=genslice(range, dat.shape[0])
			dat=dat[s]
		if copy:
			dat=dat.copy()
		return dat	
	
	def mirror(self, ds, recurse=False):
		'''Causes self to contain the same data and header values as ds (another 
Data instance). There are no side effects (e.g. self.data is an equal copy of ds.data,
not a pointer to the same array). If recurse is True, self will recieve recursive 
clones of any sub-data elements of ds as well. 

(This is 'mirror' in the WWW sense, not the optical sense. No reflections or 
inversions occur in the data).
'''
		dat=ds.getData(copy=True)
		head=ds.header()
		self.datinit(dat, head)
		if recurse:
			for cd in self.getElements('Data', depth=1):
				cd.sever()
			for cd in ds.getElements('Data', depth=1):
				self.newElement(cd.clone())
	
	def stype(self):
		'''Get self.attrib("SampleType") or "generic"'''
		st=self.attrib("SampleType")
		if not st:
			st='generic'
		return st	
		
	def shape(self):
		'''return the shape of self.getData()'''
		st=self.stype()
		fs=self.fs()
		if st=='group':
			try:
				d=self.getElements('Data')[0]
				return d.shape()
			except:
				return (0,0)
		elif self.data==None:
			return (0,0)
		elif st in ['events', 'labeledevents']:
			d=self.getData()
			n=d[:,0].max()
			if st==	'events':
				w=1
			else:
				w=d[:,1].max()+1
			return (n,w)
		elif st=='ensemble':
			n, w = self.getData().shape
			w=w/self.attrib('Reps')
			return (n,w)
		else:	
			return self.getData().shape
		
	def dtype(self):
		'''return self.getData().dtype.char'''
		return self.getData().dtype.char
	
	def header(self):
		'''return a dictionary of attributes. This is mostly the same as 
		a deepcopy of self.attributes, but the "Name" key is removed, and 
		some sanity and type checking is done'''
		h={}
		for a in self.attributes.keys():
			if a=="Name":
				continue
			v=self.attrib(a)
			if type(v)==unicode:
				v=str(v)
			if a=='Labels' and type(v) in ['List','Tuple']:
				v=map(str, v)
			if a=="DataType":
				try:
					if not self.noData:
						v=self.dtype()
					else:
						pass
				except:
					continue
			try:
				x=eval(repr(v))
			except:
				continue
			h[str(a)]=v
		
		return h	
	
	def onLoad(self):
		'''internal method used to import data'''
		if self.data==None and not self.stype()=='group':
			dat, head= self.getFromUrl()
			self.datinit(dat, head)
		basic_tools.NmpmlObject.onLoad(self)

	def __str__(self):
		n =  "%s (%s data) - " % (self.name(), self.stype())
		if self.data!=None:
			n+=str(self.data.shape)
		else:
			n+=self.attrib("Url")
		return n 

	def getUrlAndServer(self):
		'''internal method used to import and export data'''
		url=self.attrib('Url')
		if not url or url=="auto://upath":
			url="auto://"+self.upath()
		doc=self.getInstance('/')
		dstore=getDataServer(doc)
		return (url, dstore)		

	def getFromUrl(self):
		'''internal method used to import data'''
		url, dstore= self.getUrlAndServer()
		d, h = dstore.get(url, self.attributes)
		if (d==None or len(d)==0) and self.attrib("Type")=="Auto":
			print "Trying to load with 'auto://' ..."
			self.attributes['Url']='auto://upath'
			url="auto://"+self.upath()
			d, h = dstore.get(url, self.attributes)
		return (d,h)
		
	def dpath(self):
		'''returns a hierarchial path specific to nested data objects. This
path will always be "/" if the current instance is not contained in another 
data instance, and will otherwise be relative to the containing "data" (no
matter where that object resides in the overall xml tree). This path is 
composed solely of name attributes (since all tags will be "data").
dpaths _always_ begin with a /'''
		p=''
		c=self
		while not c.isTop():
			p='/'+c.name()+p
			c=c.container
		if not p:
			p='/'
		return p
	
	def isTop(self):
		'''return True if self.container is not a data instance'''
		if self._autonymous:
			return True
		if (self.container and self.container.__tag__=='Data'):
			return False
		return True	
	
	def getTop(self):
		'''Return the instance that is the top of the current data tree (e.g. 
its container is not a Data instance'''		
		c=self
		while not c.isTop():
			c=c.container
		return c
		
	def createSubData(self, path, data=None, head=None, delete=False):
		'''Creates a new data element with the listed dpath, and initializes it 
with data and head (if these are unspecified, the data is initialized as a Group). 
Data of type "group" will be created if needed in order to provide the whole specified 
path. Returns the new Data instance.

If delete is True, remove any existing data element with the specified path (this 
ensures that the new element has the given name, not an modified, unique, name).'''
		if path.startswith('/') and not self.isTop():
			self.getTop().createSubData(path, data, head, delete)
		if delete:
			sd=self.getSubData(path)
			if sd ==self:
				self.datinit(data, head)
				return
			elif sd:
				print 'Selected Path Exists. Deleting it'
 				sd.sever()
		path=path.strip('/').split('/')
		path, new=path[:-1], path[-1]
		tde=self
		for e in path:
			ce=tde.getElements('Data', e, depth=1)
			if ce:
				tde=ce[0]
			else:
				tde=tde.createSubData(e, None, {'SampleType':'group'})		
		if head==None:
			head={'SampleType':'group'}
		head['Name']=new
		node={'tag':'Data', 'attributes':head, 'elements':[], 'cdata':''}
		new=Data(node)
		if not head.get('SampleType')=='group':
			if data==None:
				data=zeros((0,1), Float32)
			new.datinit(data, head)	
		tde.newElement(new)
		return new
		
	def noData(self, data="self"):
		if type(data)==str and data=='self':
			data=self.data
		try:
			if type(data)==ArrayType:
				if len(data.shape)==0 or not all(data.shape):
					return True
				else:
					return False
			elif data:
				return False
			else:
				return True
		except:
			return False
		
	def getSubData(self, path):
		'''Return the member of the Data tree containing self that has the
indicated dpath. "/" references the top Data element. Returns None if the 
referenced path is not found.'''
		if not path:
			return self
		if path.startswith('/'):
			return (self.getTop().getSubData(path.lstrip('/')))
		h=self
		path=path.rstrip('/')
		for n in path.split('/'):
			c=h.getElements('Data', n, depth=1)
			if not c:
				return None
			h=c[0]
		return h 	

	def getHierarchy(self, below=False, order=False):
		'''If order is False, return a dictionary of dpath:instance for the data tree containing self. If below is true, only show the tree below self (inclusive). Alternately, order may be specified as "deep" or "wide". In this case, return the hierarchy as a list of (path, instance) tuples, rather than a dictionary. The ordered listing is depth first search, or breadth first search depending on the value of the order parameter.'''
		if not below and not self.isTop():
			return self.getTop().getHierarchy(order=order)
		if not order:	
			h={self.dpath():self}
			for q in self.getElements('Data'):
				h[q.dpath()]=q
		elif order=='wide':
			h=[(self.dpath(), self)]
			els=[e for e in self.elements if e.__tag__=='Data']
			while els:
				e=els.pop(0)
				h.append((e.dpath(), e))
				ce=[x for x in e.elements if x.__tag__=='Data']
				if ce:
					els.extend(ce)
		elif order=='deep':
			h=[(self.dpath(), self)]
			for e in self.elements:
				if e.__tag__=='Data':
					h.extend(e.getHierarchy(True, 'deep'))
		return h	
		
	def clearAll(self, keepheader=False):
		'''removes all data and subdata. Sets SampleType to "group"'''
		sdats=self.getElements('Data', depth=1)
		for d in sdats:
			d.sever()	
		if keepheader:
			h=self.header()
			h['SampleType']='group'	
		else:
			h={'SampleType':'group'}	
		self.datinit(None, h)	
		
	def cloneData(self, clone):
		'''Internal method that makes clones have copies of (not references to ) 
the same data as the original'''
		if self.data!=None:
			clone.datinit(self.data, self.header(), copy=True)

	def onSave(self, fname):
		'''Internal event hook for auto saving data''' 
		if self.attrib('Url').startswith('auto') or self.attrib("AutoSave"):
			url, dstore= self.getUrlAndServer()
			dstore.setStore(fname)
			dstore.put(url, self.data, self.header())
		basic_tools.NmpmlObject.onSave(self, fname)	
		
	def tableLookup(self, indexCol, indexVal, getCol, precision=0.0):
		'''indexCol should be a 1D sequence of ints. indexVal should be a sequence of the same data type stored in this element, and with the same shape as indexCol. getCol should be another sequence of ints. ints in getCol and indexCol must be less than self.data.shape[1]. Returns a sequence with the same length as getCol, containing the elements of self.data in the columns listed in getCol that occur on the first row where the values in the columns listed in indexCol are equal to the values in indexVal. If precision is nonzero, a match is included if the euclidean distance between the index array in the data an indexVal is less than precision. Returns None if there are no matches'''
		dat=self.getData()
		inds = take(dat, indexCol, 1)
		vals = take(dat, getCol, 1)
		indexVal=array(indexVal)
		dist=eucd(inds, array(indexVal))
		ind = nonzero1d(dist<=precision)
		if not len(ind):
			return None
		else:
			return vals[ind[0], :]

	def tableInterp(self, indexCol, indexVal, getCol):
		'''Acts as tableLookup, but always returs a result based on linear interpolation from the closest values in the table.'''
		pass
		## TODO Implement tableInterp
		
		
		
		
ELEMENTS = {"Data":Data}
