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

'''module providing the toplevel interface for reading files of any type.
client code should use the entry points "read", "readall", and
"write", (see docstrings for those function).

to add support for a file type, add a module to mien.parsers. This module
must define a dictionary named "filetypes" with one key for each supported
format. Each key should reference a dictionary describing the format. 
This dictionary looks like this:

'notes' - armitrary string tellirg end users about the format
'read' - a function that can read files of this type. It should take 
       arguments (file, **kwargs), even if it doesn't use any
       keyword arguments, and should return an nmpml document object
       (instance of mien.nmpml.basic_tools.NmpmlObject)
       An exception to this is that xml dialects may simply set this
       key to "True"
       'file' will be a file like object, opened for reading, not a 
       file name.
'write' - a function that writes to the specified format. It should take
       arguments (object, file, **kwargs). Object will be an instance 
       of  mien.nmpml.basic_tools.NmpmlObject. Again, xml dialects may
       simply set this to True. File will be an open file like object.
'data type' - a string that describes the type of data that can be saved
       in this format. Eventually, these may be mime-type identifiers, 
       so if your data have a mime type, use that string here. At the
       moment, however, this is simply a descriptive string for the 
       edification of end users
'elements' - this is a list of strings specifying the nmpml tags that 
       can be written to this format. It may be the string 'all' to 
       indicate all elements. xml dialects should _always_ set this 
       to the "keys()" list of their "xml dialect"  dictionary.
'extensions' - list of strings specifying filename extensions that are
       attached to files of this format. Ideally, this list should have
       a single member, that isn't used by any other mien-supported 
       format, but this property is not required. All the strings should
       explicitly begin with "."
'xml dialect' - only define this key if your file type is a dialect of xml
       This means that a standard xml parser can read the file, but that 
       you wousd like to define special functions for instatiated examples
       of your xml tags (mien will already read any xml, but will provide
       default behavior for classes not specified in nmpml).
       This key should point to a dictionary of tag names onto classes. 
       See documentation on "extending/replacing nmpml" for information 
       on how to construct this dictionary.
'''
from  os.path import split
import mien.xml.xmlhandler as xm
import re, os, sys
from urlparse import urlparse, urlunparse
from urllib import urlopen
from tempfile import mkstemp

windriveid=re.compile(r"^(\w:\\)(.*)")

def parseurl(s):
	if sys.platform!='win32':
		return urlparse(s)
	m=windriveid.match(s)
	if not m:
		return urlparse(s)
	return ('', '', s, '', '', '')

def openurlread(url):
	parts=parseurl(url)
	if not parts[0] or parts[0]=='file':
		f=file(parts[2], 'rb')
		cl=lambda: f.close()
	elif url[0]=='sftp':
		url=parts[2].lstrip('/')
		comp=url.split('/')
		server=comp[0]
		path='/'.join(comp[1:])
		if not path[0] in ['~', '.']:
			path='/'+path
		targ=mkstemp()
		com="sftp %s:%s %s" % (server, path, targ[1])
		print "executing %s" % com
		os.system(com)
		os.close(targ[0])
		f=open(targ[1], 'rb')
		cl=lambda:os.unlink(targ[1])
	else:
		f=urlopen(url)
		cl=lambda:f.close()
	return(f, cl)

def sftpSend(file, server, serverpath):
	com="sftp %s %s:%s" % (file, server, serverpath)
	print "executing %s" % com
	os.system(com)
	os.unlink(file)

def openurlwrite(url):
	parts=parseurl(url)
	if not parts[0] or parts[0]=='file':
		f=file(parts[2], 'wb')
		cl=lambda: f.close()
	elif url[0]=='sftp':
		url=parts[2].lstrip('/')
		comp=url.split('/')
		server=comp[0]
		path='/'.join(comp[1:])
		if not path[0] in ['~', '.']:
			path='/'+path
		targ=mkstemp()
		os.close(targ[0])
		f=open(targ[1], 'wb')
		cl=lambda:sftpSend(targ[1], server, path)
	else:
		raise IOError("http urls are not writable")
	return(f, cl)
	

PARSERS=['bbt', 'datahash', 'density', 'hoc','matfile','mzip','neurolucida', 'nmpml','numerical','stagecoords', 'swc', 'wav', 'csv', 'image', 'gicdat']
def getFileTypes():
	ft={}
	for m in PARSERS:
		try:
			exec('import %s as mod' % m)
			for k in mod.filetypes:
				ft[k]=mod.filetypes[k]
		except:
			#raise
			print("Unable to load parser module '%s'. Some file types will not be available" % m)
	return ft
	
filetypes=getFileTypes()	
import mien.blocks
userft=mien.blocks.getBlock('PARSERS')
filetypes.update(userft)

def writeGenericXML(f, doc, **kwargs):
	pr=kwargs.get('pretty', True)	
	st=kwargs.get('style', {})
	fc=kwargs.get('formatCData', 1)	
	return xm.writeXML(f, doc, st,  pr, fc)

filetypes['xml']={'notes':'May lose links to binary data',
					'read':True,
					'write':True,
					'data type':'any',
					'elements':'all',
					'xml dialect':{},
					'extensions':['.xml']}

def user_choice(choose, fname, gui):
	answer = None
	if gui:
		from mien.interface.widgets import optionPanel
		o=optionPanel("Can't determine type of  %s. Please select:" % fname, choose, gui)
	else:
		from mien.interface.cli import optionPanel
		o=optionPanel("Can't determine type of  %s. Please select:" % (fname,), choose)
	return o
	
	
def getViewerForTag(el):
	if el.__tag__ in ['Cell', 'Fiducial']:
		return 'cell'
	elif el.__tag__ == "Data":
		if el.stype()=='image':
			return 'image'
		else:
			return 'data'
	elif el.__tag__ in ['Comment', 'Comments']:
		return None
	else:
		return "xml"
	
def getViewerApp(doc):
	tlt=[getViewerForTag(x) for x in doc.elements]
	counts=[(x, tlt.count(x)) for x in tlt if x]
	app, count= counts[0]
	for c in counts[1:]:
		if c[1]>count:
			app, count=c
	return app

def legal_formats(doc):
	tags=set([q.__tag__ for q in doc.getElements()])
	formats=[]
	for k in filetypes.keys():
		if filetypes[k].get('elements', 'all')=='all':
			formats.append(k)
		elif tags.intersection(filetypes[k]['elements']):
			formats.append(k)
	return formats		

def match_extension(ext):
	fts=filetypes.keys()
	match=[]
	ext=ext.lstrip('.').lower()
	for t in fts:
		tel=[e.lstrip('.') for e in filetypes[t]['extensions']]
		if ext in tel:
			match.append(t)
		else:
			for p in filetypes[t].get("extension patterns", []):
				if re.match(p, ext):
					match.append(t)
					break
	return match

def select_elements(doc, **kwargs):
	#make sure this preserves doc.fileinformation
	if kwargs.get('gui'):
		from mien.interface.widgets import select
	else:
		from mien.interface.cli import select
	finf=doc.fileinformation	
	doc=select(doc, **kwargs)
	doc.fileinformation=finf
	return doc
	
def formatinfo(f):
	if not filetypes.has_key(f):
		return "Unknown format"
	f=filetypes[f]
	if f.get('read') and f.get('write'):
		s="read/write, "
	elif f.get('read'):
		s="read only, "
	else:
		s='write only, '
	s=s+"%s data (%s)\n" % (f["data type"], f.get("notes", 'no description'))
	return s


def sort_xml_formats(f1, f2):
	return cmp(len(filetypes[f1]['xml dialect'].keys()),len(filetypes[f2]['xml dialect'].keys()))
	

def get_xml_dialect(tree):
	if type(tree)==dict:
		tlt=[d['tag'] for d in tree['elements']]
	else:	
		tlt=[d.__tag__ for d in tree.elements]
	xmlformats=[f for f in filetypes.keys() if filetypes[f].has_key('xml dialect')]
	xmlformats.sort(sort_xml_formats)
	for f in xmlformats:
		tags=filetypes[f]['xml dialect'].keys()
		if set(tags).issuperset(tlt):
			return f
	return 'xml'

def get_file_format(fname, gui=None):
	fn, ext=os.path.splitext(fname)
	choose=match_extension(ext)
	if len(choose)==1:
		return choose[0]
	if len(choose)==0:
		choose = filetypes.keys()
	xmld=[f for f in choose if filetypes[f].has_key('xml dialect')]
	if len(xmld)==len(choose):
		return "unknown xml"
	return user_choice(choose, fname, gui)

def read(fname, **kwargs):
	'''reads from file fname. This function will attempt to automatically 
identify the format of the file, and will ask the user for confirmation
if it can't make a unique ID. To override this behavior use the keyword
argument "format". This function will return None if it fails, or an 
NmpmlObject if it succeeds.

fname may be the name of a local file, or it may be a url. 

Key word arguments:

"format" - set this to a key of "filetypes" to force the format of the input 
	file to be treated as a particular format.
"gui" - Set this to a mien.wx.base.BaseGui instance to use that GUI's methods
	for user interaction during the load. Set it to True to cause this 
	function to make its own GUI for interaction (otherwise, you will get
	text-mode interaction)
"select" - ifTrue, ask the user to select subsets of a document to load 
	(by default, the whole document is automatically loaded)
"convertxml" - if True, cast generic xml to a simplified version of the
	nmpml dialect. This will cause some advanced function of the interfaces
	to work. On the other hand, this will may cause the xml to be modified. 
	Tags without an attribute "Name" will be given one, and the value of the  
	"Name" tag will be rendered sibling-unique. This may mean that if the 
	resulting xml is saved back to a file, other parsers will not read it
	correctly.
	By default, a compatibility class is used for generic XML that enables
	most of the features of the Nmpml interfaces without modifying the xml.S
	Note that this flag will only convert "generic" xml, so if there is a
	user-defined xml dialect that is non-empty, but not nmpml-compliant, 
	this flag will not make it functional.
'''	
	url=fname
	parts=parseurl(url)
	fname=parts[2]
	kwargs['unparsed_url']=url
	kwargs['parsed_url']=parts
	format=kwargs.get('format')
	if not format:
		format=get_file_format(fname, kwargs.get('gui'))
		kwargs['format']=format
	if format=="unknown xml":
		ft={'xml dialect':'automatic', 'read':True}
	elif not filetypes.has_key(format):
		fl=match_extension(format)
		if not fl:
			print "Unknown format %s" % format
			return
		kwargs['format']=fl[0]
		ft=filetypes[fl[0]]
	else:	
		ft=filetypes[format]
	if not ft["read"]:
		print "format %s is write only" % format
		return	
	fileobj, cleanup=openurlread(url)
	if not ft.has_key('xml dialect'):		
		doc=ft["read"](fileobj, **kwargs)
		cleanup()
	else:
		doc=xm.readTree(fileobj)
		cleanup()
		if ft['xml dialect']=='automatic':
			format = get_xml_dialect(doc)
			kwargs['format']=format
			ft=filetypes[format]
		dialect=ft['xml dialect']
		if dialect=={}:
			if kwargs.get("convertxml"):
				dialect={'default class':filetypes['nmpml']['xml dialect']['default class']}
			else:
				from mien.nmpml.basic_tools import NmpmlCompat
				dialect={'default class':NmpmlCompat}
		doc=xm.assignClasses(doc, dialect)	
	if kwargs.get('select'):
		if doc.fileinformation.get('select_done'):
			del(doc.fileinformation['select_done'])
		else:	
 			doc=select_elements(doc, **kwargs)
	doc.fileinformation["filename"]=url
	doc.fileinformation["type"]=format
	if not ft.get('autoload'):
		doc.onLoad()
	return doc
		
def readall(files, **kwargs):
	'''Call the read function (with the specified keyword arguments) for 
each file  in the list "files". At the end, concatenate all the elements 
into the first document.
''' 
	doc=read(files[0], **kwargs)
	for f in files[1:]:
		d2=read(f, **kwargs)
		if d2:
			doc.addDocument(d2)
		else:
			print "Warning: can't read %s" % f		
	return doc	
	
def checkSaveElements(obj, elements, fname):
	if not elements or elements=='any':	
		return True
	ok=[e for e in obj.elements if e.__tag__ in elements]
	if len(ok)>0:
		return True
	else:
		return False
	
def write(obj, fname, **kwargs):
	'''Writes an NmpmlObject to the named file. This function will attempt
to automatically identify the format of the file, using the "fileinformation"
member of the NmpmlObject, and, failing that, the extension of the file name.
To override this behavior use the keyword argument "format". This function will return False if it fails, or True if it succeeds. 

Key word arguments:

"format" - set this to a key of "filetypes" to force the format of the output 
	to a particular format.
"gui" - Set this to a mien.wx.base.BaseGui instance to use that GUI's methods
	for user interaction during the load. Set it to True to cause this 
	function to make its own GUI for interaction (otherwise, you will get
	text-mode interaction)
"forceext" - set this to True to cause this function to alter the provided
	file name to gaurantee that it has the extension that mien associates to
	the format that it was written in.
"newdoc" - Write a copy of the object, placed in a new xml document container. The container will contain no other elements, but the copy is recursive, so the objects children will also be written.
	
	
'''	
	if kwargs.get('newdoc'):
		from mien.parsers.nmpml import blankDocument
		doc=blankDocument()
		doc.newElement(obj.clone())
		obj=doc
	if hasattr(fname, 'write'):	
		fileobj=fname
		openme=False	
	else:	
		url=fname
		parts=parseurl(url)
		fname=parts[2]
		kwargs['parsed_url']=parts
		openme=True	
	format=kwargs.get('format')
	if not format:
		format=obj.fileinformation["type"]
	if not format or format=='guess':
		if openme:
			format=get_file_format(fname, kwargs.get('gui'))
		if format=="unknown xml":
			format = get_xml_dialect(obj)
		if not format:
			print "aborting write"
			return
	if not filetypes.has_key(format):
		fl=match_extension(format)
		if not fl:
			print format
			print "can't find format for file %s using default (nmpml)" % str(fname) 
			format='nmpml'
		format=fl[0]
		kwargs['format']=fl[0]
	kwargs['format']=format
	ft=filetypes[format]
	if not ft["write"]:
		print "format %s is read only" % format
		return False
	if kwargs.get('forceext') and openme:
		ext=ft['extensions'][0]
		if not fname.endswith(ext):
			q=list(parseurl(url))
			q[2]=os.path.splitext(fname)[0]+ext
			url=urlunparse(tuple(q))
	#prep=checkSaveElements(obj, ft.get("elements", "any"), fname)
	#if not prep:
	#	print "format %s can't be used to write any of the objects in this document" % format
	#	return False
	if openme:
		fileobj, cleanup=openurlwrite(url)
		kwargs['wrotetourl']=url
	if ft.has_key('xml dialect'):
		writeGenericXML(fileobj, obj, **kwargs)
		obj.onSave(url)
	else:	
		ft["write"](fileobj, obj, **kwargs)
	if openme:	
		cleanup()	
	return True	
	
