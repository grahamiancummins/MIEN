#/usr/bin/env python

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
import sys, os, re, getopt, mien.nmpml, code, inspect
import mien.parsers.fileIO as io
#from mien.math.sigtools import *
from mien.datafiles.dataset import * 

'''
This module provides a command line interface to mien. The entry point 
for the interface is provided by mien/frontends/mien. (use "mien -t [files]")
'''

class Browser:
	'''Class for text based browsing of xml. Use the "browse" funciton 
	as an entry point.'''
	def __init__(self, doc, out, mask=False):
		self.output=out
		self.doc=doc
		self.cur=None
		self.mask=mask
	
	def contents(self, el):
		cids=[]
		if self.mask and el in self.output:
			return cids
		kids=el.getElements([],{},1)
		ktags={}
		for k in kids:
			t=k.__tag__
			if not ktags.has_key(t):
				ktags[t]=[]
			ktags[t].append(k)
		ktk=ktags.keys()
		ktk.sort()
		for k in ktk:
			if len(ktags[k])>5:
				print"(%i) %i %s" % (len(cids),len(ktags[k]), k)
				cids.append(ktags[k])
			else:
				for el in ktags[k]:
					print "(%i) %s:%s" % (len(cids), el.__tag__, el.name())
					cids.append(el.upath())
		return cids		

	def choosefrom(self, l):
		print "There are %i elements in this group." % len(l)
		gotid=None
		while not gotid:
			id=raw_input("Which index? > ")
			try:
				id=int(id)
				el=l[id]
				gotid=True
			except:
				print "Need an int between 0 and %i" % (len(l)-1,)
		self.show(el.upath())		
	
	def show(self, path):
		self.cur=self.doc.getInstance(path)
		print "****  "+self.cur.upath()+"  ****"
		kids=self.contents(self.cur)
		print "****  "+self.cur.upath()+"  ****"
		print "(q)uit, (u)p, (e)xport, (p)ath, (t)op, number to descend "
		act=raw_input("choice> ")
		if act=="q":
			return
		if act=="u":
			cont=self.cur.container
			if not cont:
				print "already at top level"
				self.show('/')
			else:	
				self.show(cont.upath())
		elif act=='t':
			self.show('/')
		elif act=='e':
			self.output.append(self.cur)
			print "Instance added to output queue"
			self.show(self.cur.upath())
		elif act=='p':
			self.output.append(self.cur.upath())
			print "Path added to output queue"
			self.show(self.cur.upath())
		else:
			try:
				id=int(act)
				cid=kids[id]
				if type(cid) in [str, unicode]:
					self.show(cid)
				else:	
					self.choosefrom(cid)
			except:
				print "Didn't understand command"
				self.show(self.cur.upath())
		

def browse():
	'''open a text-based browser for the current document tree'''
	b=Browser(doc, els)
	b.show("/")

def select(doc, **kwargs):
	'''choose a subset of the document'''
	if len(doc.getElements())<2:
		return doc
	elements=[]
	b=Browser(doc, elements, True)
	b.show("/")
	if not elements:
		return doc
	unique=[]
	for e in elements:
		par=e.xpath(True)[:-1]
		for pe in par:
			if pe in elements:
				break
		else:
			unique.append(e)
	doc.elements=[]		
	for e in unique:
		e.container=None
		doc.newElement(e)
	return doc
	
def selectDvData(source, **kwargs):
	'''Choose a subset of a numerical data element'''
	h=source.header
	cols, samps, SR =h["Columns"],h["Length"],h["SamplesPerSecond"] 
	chans=None
	start=0
	stop=None
	set_sr=None
	down=0
	def menu(c, s, r):
		print "Data contains %i samples on %i channels, sampled at %.2f Hz" % (s, c, r)
		print "Enter to accept"
		print "c to select channels"
		print "l to list channel names"
		print "r to change sample range"
		print "s to change sampling rate"
		print "d to downsample"
		r=raw_input("> ")
		return r.lower()
	doit=menu(cols, samps, SR)
	while doit:
		if doit=='c':
			print "enter channels to select. Separate entries with white space. You may use colons to indicate ranges. 'Enter' selects all"
			r=raw_input("> ")
			if not r:
				chans=None
				cols=h["Columns"]
			else:
				vals=r.split()
				chans=[]
				for v in vals:
					if ":" in v:
						sa, sp=v.split(':')
						chans.extend(range(int(sa), int(sp)))
					else:
						chans.append(int(v))
		elif doit=='l':
			for i, k in enumerate(h['Labels']):
				print "%i) %s" % (i,k)
		elif doit=='r':
			sa=raw_input('First sample > ')
			sp=raw_input('Last sample (length %i) > ' % h["Length"])
			start=int(sa)
			stop=int(sp)
			samps=stop-start
		elif doit=='s':
			sa=raw_input('Sampling Rate (%.2f)> ' % SR)
			SR=float(sa)
			set_sr=SR
		elif doit=='d':
			sa=raw_input('Subsample Interval (%i)> ' % down)
			down=int(sa)
		else:
			print "unknown command"
		doit=menu(cols, samps, SR)
	return 	{'Channels':chans, 'Start':start, 'Stop':stop, 'SamplesPerSecond':set_sr, 'Downsample':down}

	
def optionPanel(title, choose):
	print title
	answer=None
	while not answer:
		print "Choices are:"
		for i in range(len(choose)):
			print "  %i ) %s" %(i, choose[i])
		ext = raw_input("enter number:").strip()
		try:
			ext=int(ext)
			answer = choose[ext]
		except:
			pass
	return answer
	
	
els=[]

def bounce():
	'''Reload the modules in the "mods" list and the current document'''
	mods=["mien.nmpml.%s" % mn for mn in mien.nmpml.__all__]+['mien.nmpml',  'mien.optimizers.base','mien.optimizers.brute','mien.optimizers.ga','mien.nmpml.optimizer', 'mien.parsers.nmpml','mien.parsers.fileIO']
	for m in mods:
		exec("import %s" %m)
		exec("reload(%s)" % m)
	io=mien.parsers.fileIO
	try:
		l=globals()
		doc=l['doc']
		els=l['els']
		fn=doc.fileinformation.get('filename', 'miendoc.nmpml')
		doc=io.read(fn)
		l['doc']=doc
		l['io']=io
	except:
		print "unable to reload document"
		raise
		return None
	for i,e  in enumerate(els):
		if type(e)!=str:
			e=e.upath()
		try:
			ne=doc.getInstance(e)
		except:
			ne=None
			print "Can't reference element at %s" % e
		els[i]=ne	
	l['els']=els

def get(mod):
	'''import a module and add it to "mods"'''
	exec("import %s" % mod)
	mods.append(mod)

def clear():
	'''remove all elements from the "els" list'''
	while els:
		els.pop()

def save(fn=None, format='guess'):
	'''write the current document to a file. If fn is not specified, and the 
	document was concatenated from multiple files, it will save to the first of
	these files (overwriting data)''' 
	if not fn:
		fn=doc.fileinformation.get('filename', 'miendoc.nmpml')
	io.write(doc, fn, format=format)
	

def scan(d, depth=5):
	'''scan the tag structure of the document d to the specified depth'''
	try:
		i=d.tagScan(depth)
		print '\n'.join(i)
	except:
		raise
		print "doesn't support scanning"

def runmethod(doc, element):
	'''Find and run a method of one of the objects in the specified 
Document. There are several syntaxes for "element"

The most complete syntax is an nmpml upath, joined by a "." to the name
of a method (e.g. "/NmpmlDocument:MyDoc/Experiment:MyExperiment1.run) If
the path doesn't begin with a "/" but does contain a ":" the toplevel
document element is automatically matched, and the seach begins below
it. This syntax exactly specifies a particular element and method, which
must exist of the command fails immeadiately.

Alternatively, the path may be only an nmpml tag, joined to a method by
a '.' (eg "Experiment.run"). In this case mien will find the first
instance of that tag (using a bredth first search) and call the method

The method name may be ommitted, in which case it is assumed to be
"run", so "-r Experiment" is equivalent to the other examples above, if
called on a document that only defines one Experiment tag
'''
	if '.' in element:
		element, method=element.split('.')
	else:
		method="run"
	
	if ":" in element:
		element=doc.getInstance(element)
	else:
		els=doc.getElements(element, depth=1)
		if len(els)==0:
			print "no top level elements of type %s" % element
			return
		elif len(els)>1:
			print "Warning, found %i toplevel elements of type %s. Using the first one (%s)" % (len(els),element,str(els[0]))
		element=els[0]	
	r=getattr(element, method)
	st=time.time()
	out = r()
	print "Run complete in %.2f seconds" % (time.time()-st)
	if out:
		print "Result - %s" % (repr(out),)
	else:
		print "No Output"
	st=time.time()
	fname=doc.fileinformation.get("filename", 'clidoc.mien')
	fname, ext=os.path.splitext(fname)
	fname=fname+"_batchrun"+ext
	io.write(doc, fname)
	print "Saved model to %s in %.2f seconds" % (fname, time.time()-st)	

def batchrun(doc, fname):
	'''Used to call AbstractModels that take variable file input. 
   fname is the Url of a file containing input data. Mien will call the first
   AbstractModel in the document, passing it data from the file at fname. The 
   output will be stored in a file of the same type and extension as fname with
   _mien_batch added to the name.'''
   
	els=doc.getElements("AbstractModel", depth=1)
	if len(els)==0:
		print "no top level elements of type AbstractModel"
		return
	elif len(els)>1:
		print "Warning, found %i toplevel elements of type AbstractModel. Using the first one (%s)" % (len(els),str(els[0]))
	if not fname or fname in ['def', 'auto', 'default']:
		fname=els[0].attrib('defaultBatchFile')	
	r=getattr(els[0], 'run')
	st=time.time()
	dat=apply(r, (fname,))
	nname, ext=os.path.splitext(fname)
	nname=nname+"_mien_batch.mdat"
	io.write(dat, nname, newdoc=1)	
	print "Run complete in %.2f seconds" % (time.time()-st)
	
def updater():
	'''Run the interactive command line update manager. This can configure your network repository settings and install, update, or remove packages'''
	import mien.tools.updater
	c=mien.tools.updater.CLI()	
	
def h():
	'''help'''
	print '''This is a python command line, and will act like interactive 
python, with the following additions:

The following names are bound to data members:

els - a list of elements, empty by default, for saving element references 
	from the browser
mods- a list of modules, which will be reloaded by the "bounce" function
doc - The current document instance (usually an nmpml document)
io  - the mien.parsers.fileIO module (io.read and io.write are of most 
	interest)

sys, os, re, getopt, mien.nmpml, code, inspect are imported 

all names from mien.math.sigtools (which includes most of Numeric) are imported

The following helper functions are defined:

'''
	l=globals()
	l.update(locals())
	funcs=[]	 
	for name in l:
		fun=eval(name)
		if inspect.isfunction(fun):
			if fun.__module__=='mien.interface.cli':
				funcs.append(fun)
	for fun in funcs:
		fn=fun.func_name
		doc=inspect.getdoc(fun)
		define=inspect.getsourcelines(fun)[0][0]
		define=re.sub(r"^\s*def\s*", "", define)
		define=re.sub(r":\s*$", "", define)
		
# 		args, vargs, vkargs, defs=inspect.getargspec(fun)
# 		if not defs:
# 			defs=()
# 		argstring=""
# 		for i, a in enumerate(args):
# 			an=args[i]
# 			if i<len(defs):
# 				an="%s=%s" % (an, defs[i])
# 			argstring=argstring+(', ')+an
# 		if vargs:
# 			argstring=argstring+', *'+vargs
# 		if vkargs:
# 			argstring=argstring+', **'+vkargs
# 		if argstring:
# 			argstring=[2:]
# 		argstring='('+argstring+')'	
		print define
		print doc
		print 

def askParametersCLI(lod, gui=None):
	if gui:
		if gui is True:
			gui=None
		from mien.wx.dialogs import askParameters
		return askParameters(gui, lod)
	pars=[]
	for dic in lod: 
		if dic["Type"] == "Label":
			print(dic['Value'])
			continue
		if dic["Type"]=="Choice":
			raise StandardError('"choice" dialog type is not supported in cli')
		if not dic.get("Type", "Foo") in ["List", "Prompt", "Select"]:
			if dic.get("Default"):
				if not dic.get("Value"):
					dic["Value"]=dic["Default"]
			if not dic.has_key("Type"):
				dic["Type"]=type(dic["Value"])
			val = raw_input("%s (%s) > " % (dic['Name'], dic.get['Value']))
			try:
				val=dic["Type"](val)
			except:
				print("Couldn't cast value to required type. Hope for the best.")
		else:
			val=askFromList(dic['Name'], dic['Value'], dic['Type']=="Select")
		pars.append(val)
	names=[dic['Name'] for dic in lod if not dic['Type']=='Label']
	ps=','.join(["%s:%s" % (names[i], str(pars[i])) for i in range(len(pars))])
	print("Parameter values are: %s" % ps)
	ok=raw_input("Are these OK? (o)k/(r)eenter/(a)bort > ")
	if ok.lower.startswith('n'):
		return askParametersCLI(lod)
	elif ok.lower.startswith('a'):
		return None
	return pars

def startCli(doc, ns={}):
	'''start and interactive interpreter'''
	l=globals()
	l.update(locals())
	l.update(ns)
	if doc:
		l['doc']=doc
		el=[e for e in doc.elements if not e.__tag__=="Comments"]
		if len(el)==1:
			l['el']=el[0]
	try:
		from IPython.Shell import IPShellEmbed
		ipshell = IPShellEmbed(argv=[])
		ipshell(local_ns=l)
	except:
		code.interact("Mien cli (type 'h()' for help)", local=l)

