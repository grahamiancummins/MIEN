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


usage='''mien [-h|v|t|p|a app|r method|s depth|c format]  [-f format] [-i] [file [file ...]]

This command provides the user interface entry point for the MIEN python 
package the basic invocation opens the toplevel xml-browser GUI. Command switches provide access to other component GUIs and CLIs. 

One or more file paths may be passed as arguments. In this case the
interface that opens will attempt to load (and concatenate) all of these
files.

-v visualize. In this mode, mien will attempt to automatically detect
the type of the input files and open the simplest GUI that will provide
a visual image of the data. Type detection is based on the type of the
first file, and all files in the argument list will need to be of the
same type.


-t (Text) Open the interactive text-based (command line) ui

-a app (Application) Open a particular component application. 
   legitimate values for "app" are:
        "cell" - the display GUI for anatomical data (CellViewer)
	    "data" - the display GUI for time series data (DataViewer)
	    "image"- the Display GUI for image data (ImageViewer)
		"wave" - the stimulus and waveform synthesizer (Waveform)    
		"dsp"  - the Dsp toolchain generator (Dsp)
		
	Note: setting app to "cell2d" will force execution of the (depricated)
	2D cell viewer. This viewer uses only than library, rather than the
	OpenGL library. It is slower, uglier, and less capable than the GL 
	version, and is no longer supported, so you usually don't want to run 
	it unless your system doesn't support PyOpenGL. In this case, using 
	app="cell" will fall back to the 2D viewer after the 3D viewer fails, 
	so the only reason to use "cell2d" is for debugging the 2d app on a 
	PyOpenGL capable system. 
	
-s depth (Scan) Prints a scan of the file to the indicated depth and exits.

-r method (Run) Find and run a method of one of the objects in the first
   specified data file (this file must exist, and it must contain an nmpml
   model structure). There are several syntaxes for "method"

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

-c type (Convert) Don't open any interface. Instead convert the input files to
   the specified type (which should be a file name extension). Note that if
   '-c' is specified on time -series data files, the file subset selection
   dialog (command line version) will still appear, which can be useful for
   cropping files. to over-ride this us -cf

-i  (Interact) Prompt for selection of sub-components while loading files. This 
	allows you to import brances of an xml tree, part of a binary file, etc.
	This can greatly speed loading times, and allow you to scan huge files, but 
	requires extra user interaction. 

-f  format (Format) Force mien to use the specified format. 
	This can be important for xml files that are not in the nmpml dialect
	By default, the specialized nmpml classes are used to represent
	corresponding nmpml tags. This offers advanced features (for
	editing, display, and simulation of models), but may cause errors 
	when loading non-nmpml xml.
	
	If you know the input file is xml, but not nmpml, use this switch 
	with format "xml" if you want to be sure that the file is un-altered,
	or use format "tonmp" to force the document into nmpml (which will
	enable all the capabilites of the guis, but may cause the document to
	be altered if you save it (even if you don't make any modifications
	by hand)
	
	Legal arguments for "format" are any key in the mien.fileIO.filetypes
	dictionary. You can get a list with "-f list", you can also get a list of the 
	extensions associated to each file type with "-f listext"

-h help.

-p permissive. Set the environment variable MIEN_NO_VERIFY_XML, which prevents
	the mien xml dialect parsers form raising exceptions if they are asked to
	read xml that doesn't obey the DTD

'''

import sys, os, getopt
import time
import os.path
import mien.tools.identifiers

# all these imports are here to help py2app find all the
# right dependencies, as these routines are imported dynamically
# and not referenced in import statements that a static compile can find.

import mien.nmpml.abstract
import mien.nmpml.basic_tools
import mien.nmpml.cell
import mien.nmpml.channels
import mien.nmpml.data
import mien.nmpml.density
import mien.nmpml.evalserver
import mien.nmpml.experiments
import mien.nmpml.fiducial
import mien.nmpml.ions
import mien.nmpml.optimizer
import mien.nmpml.parameters
import mien.nmpml.passive
import mien.nmpml.pointcontainer
import mien.nmpml.pprocs
import mien.nmpml.recording
import mien.nmpml.reference
import mien.nmpml.section
import mien.nmpml.stimulus
import mien.nmpml.table

import mien.spatial.align
import numpy
import OpenGL
import wx

##FIXME: main entry point should just provide for these imports

def findextensions():
	ed=os.environ.get('MIEN_EXTENSION_DIR')
	if not ed:
                print 'Home exists:',os.environ.has_key('HOME')
		ed=os.path.join(os.environ['HOME'], 'mienblocks')
	if not os.path.isdir(ed):
		return
	os.environ['MIEN_EXTENSION_DIR']=ed
	sys.path.append(ed)

		
if __name__=='__main__':
	try:
		options, files = getopt.getopt(sys.argv[1:], "ipvtha:r:s:c:f:")
	except getopt.error:
		print usage
		sys.exit()
	switches={}
	mien.tools.identifiers.setConfigFile()
	findextensions()
	for o in options:
		switches[o[0].lstrip('-')]=o[1]
	if switches.has_key('h'):
		print usage
		sys.exit()
	if switches.get('p'):
		try:
			os.system("export MIEN_NO_VERIFY_XML=1")
		except:
			pass
	if switches.get('f', '').startswith('list'):
		import mien.parsers.fileIO as io
		formats=io.filetypes.keys()
		print "The following file types are supported"
		if switches['f']=='listext':
			for f in formats:
				el=", ".join(io.filetypes[f]['extensions'])
				print "%s - %s" % (f, el)
		else:	
			for f in formats:
				s=io.formatinfo(f)
				print " %s - %s  " % (f, s)
		sys.exit()
	if not set(['c', 't', 'r', 's']).intersection(switches.keys()):
		gui=True
                #sys.path.append('/Users/orser/mien_python')
		from mien.wx.base import wx
		wxapp = wx.PySimpleApp()			
	else:
		gui=False
	if files:
		ma=time.time()
		kwargs={'gui':gui}
		if 'f' in switches:
			if switches['f']=="tonmp":
				kwargs["convertxml"]=True
			else:	
				kwargs['format']=switches['f']
		if 'i' in switches:
			kwargs['select']=True
		import mien.parsers.fileIO as io
		doc=io.readall(files, **kwargs)
		print time.time()-ma 
	else:
		doc=None	
	if gui:
		if switches.has_key('v'):
			if not doc:
				print "No files specified to view. Exiting"
				sys.exit()
			a=io.getViewerApp(doc)
			if a:
				switches['a']=a
		if switches.has_key('a'):
			app=switches['a'].lower()
			if app.startswith('i'):
				from mien.image.viewer import ImageViewer
				x = ImageViewer()
			elif app.startswith('c'):
				from mien.interface.cellview3D import CellViewer
				print "using OpenGL"
				x = CellViewer()
			elif app.startswith('da'):
				from mien.datafiles.viewer import Dataviewer
				x = Dataviewer()
			elif app.startswith('w'):
				from mien.sound.synth import WFGui
				x = WFGui()
			elif app.startswith('ds'):
				#dsp
				from mien.dsp.gui import DspGui
				x = DspGui()
			else:
				print "don't know about an app called %s" % app
				sys.exit()
		else:
			#mien main
			from mien.interface.mainapp import MienGuiApp
			x = MienGuiApp()
		x.Show(True)
		x.newDoc(doc)
		wxapp.MainLoop()
	else:
		import mien.interface.cli as cli
		if switches.has_key('t'):
			cli.startCli(doc)
		elif switches.has_key('s'):
			cli.scan(doc, int(switches['s']))
		elif switches.has_key('r'):
			from mien.interface.cli import runmethod
			runmethod(doc, switches['r'])
		elif switches.has_key('c'):
			format=switches['c']
			if not io.filetypes.has_key(format):
				try:
					if not format.startswith('.'):
						format='.'+format
					format=io.match_extension(format)[0]
				except:
					print "Can't determine format (use mien -f list to see formats)"
					format=None
			if format:
				fname, ex=os.path.splitext(files[0])
				ex=ex[1:]
				if ex.isdigit():
					fname=fname+"-"+ex
				ma=time.time()
				io.write(doc, fname, format=format, forceext=True)
				print time.time()-ma 
sys.exit()
		
		
