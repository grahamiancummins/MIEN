
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
### 
from mien.xml.xmlclass import BaseXMLObject
from xml.sax.handler import ContentHandler
from xml.sax import make_parser
import StringIO, re

whitespace=re.compile(r"\s+")
linebreak=re.compile(r"\s*\n\s*")


XMLDECLARATION = '<?xml version="1.0" encoding="UTF-8"?>'
INDENT="  "

class QuickHandler(ContentHandler):
	def __init__(self):
		ContentHandler.__init__(self)
		self.elements=[]

	def startElement(self, name, attrs):
		ob={'tag':name, 'attributes':dict(attrs), 'elements':[], 'cdata':[]}
		if self.elements:
			self.elements[-1]['elements'].append(ob)
		self.elements.append(ob)	
		
	def characters(self, characters):
		'''characters(str) =>None
If self.object.cdata is a string, append charaters to it'''
		self.elements[-1]['cdata'].append(characters)

	def endElement(self, name):
		'''name(str) => None
if self.tag==name, call cleanUp, then change the handler back self.handler'''
		if len(self.elements)>1:
			self.elements.pop()

def readTree(fname):
	'''returns a tree structure for the document (made of dicts)'''
	if type(fname) in [str, unicode]:
		fname = open(fname, 'rb')
	sp = make_parser()
	ch =  QuickHandler()
	sp.setContentHandler(ch)
	sp.parse(fname)
	
	return ch.elements[0]

def assignClasses(tree, taginfo):
	'''looks through the tree of xmlclass.Node instances for tags 
	matching keys in taginfo. For tags that are found, creates an instance
	of the class stored in taginfo, using the Node as the initial condition.
	If there is a key "default class" this will be used for any tags that are
	not found. If not, BaseXMLObject is used for unknown tags The replacement 
	is top-down, so a class may choose to alter the tree below it, before this
	method searches that portion of the tree.'''
	dc=taginfo.get("default class", BaseXMLObject)
	tt=taginfo.get(tree['tag'], dc)
	#print tree['tag']
	new=tt(tree)
	els=[]
	for d in tree['elements']:
		se=assignClasses(d, taginfo)
		els.append(se)	
	new.setElements(els)
	return new	
		
def readXML(f, taginfo={}):
	'''f(str), taginfo (dict={}) => XMLObject (instance)
generate a toplevel handler, setting taginfo, and parse the file "file".
The highest level XML object is returned.
If no tags are parsed, raise IOError.'''
	doc=readTree(f)
	doc=assignClasses(doc, taginfo)
	if type(f) in [str, unicode]:
		doc.fileinformation['filename']=f
	return doc


def wrap_lines(s, width=72, breakwords=False):
	'''wrap (insert newlines) the string s to the specified width.
Replaces all consecutive whitespace with a single space. breakwords
may be False (only wrap on spaces), "auto" (wrap on spaces if possible)
or "always" (just break the lines to exactly width)'''
	s=whitespace.sub(s, ' ')
	lines=[]	
	if breakwords=='always':
		while len(s)>width:
			f,s=s[:width], s[width:]
			lines.append(f)
	else:
		while len(s)>width:
			test=s[:width]
			bi=test.rfind(' ')
			if bi==-1:
				if breakwords:
					bi=width
				else:
					bi=s.find[' ', width]
					if bi==-1:
						break
			f,s=s[:bi], s[bi:].rstrip(' ')	
	lines.append(s)
	return '\n'.join(lines)	

def do_format(cdata, format, depth):
	'''Helper for writeNode'''
	if not format:
		return cdata
	if format>1:
		b=False
		if format==3:
			b='auto'
		if fomat==4:
			b='always'
		wrap_lines(s, width=72, breakwords=b)
	if format<3:
		cdata=linebreak.sub(cdata, '\n'+INDENT*depth)
	return cdata
	
def writeNode(d, pretty = False, formatCData=False, depth=0):
	'''Helper for writeXML. See the definition of that function
for the effect of the arguments.'''
	d['cdata']=d['cdata'].strip()
	open = "<"+d["tag"]
	for a in d['attributes'].keys():
		try:
			open+=' %s="%s"' % (a, d['attributes'][a])
		except:
			print a, d['attributes'][a]
	if not (d['elements'] or d['cdata']):
		open += "/>"
		if pretty and depth:
			open=INDENT+open
		return [open]
	elif not d['elements'] and len(d['cdata'])<40:
		open+='>'+d['cdata']+"</"+d["tag"]+">"
		if pretty and depth:
			open=INDENT+open
		return [open]
	open+=">"
	xml=[open]		
	for e in d['elements']:
		childxml = writeNode(e, pretty, formatCData, depth+1)
		xml.extend(childxml)
	xml.append("</"+d["tag"]+">")
	if pretty and depth:
		xml=[INDENT+l for l in xml]
	if d['cdata']:
		xml.insert(1, do_format(d['cdata'], formatCData, depth))	
	return xml

def writeXML(fname, obj, style={}, pretty=False, formatCData=False):
	'''fname(str or file),obj (instance), style(dict={}), pretty (Bool=False) formatCData=False=> None

Write xml document to named file. If style is a dict of attributes
(eg namespace or dtd) it is added to the attributes of the top level
tag before the write.

Obj may be a tree dictionary, or a subclass of of BaseXMLObject (that 
supports the getTree method). If "pretty" is set, tags will be placed on 
separate indented lines. If "formatCData" is true, long cdata (greater than 
72 charachters, or containing newlines) will also be formatted. (this will 
change the whitespace content of the cdata!). Values for this flag, and 
there effects are as follows:

if "pretty" is True, but formatCData is False:
  strip whitespace from the start and end of the cdata, insert one
  leading and one trailing  newline, and one trailing indent (this
  results in the cdata appearing in an unaltered block on the left
  margin, with the opening and closing tags on separate, indented,
  lines).
1 indent mulitline cdata, keeping existing linebreaks (although
  these will be converted to "\n" - mien supports reading windoze line
  breaks, but will not propogate the attrocity. All format levels
  greater than 1 will replace windows line breaks with unix line breaks)
2 Indent, plus wrap cdata to 72 column (or shorter) lines, by breaking lines 
  on white space. Blocks that contain more than 72 consecutive non-space
  characters will be left intact. 
3 Wrap to 72 column (or shorter) lines, breaking on space if possible, but 
  on the 72 character if not. (This may break words in text cdata). No 
  indent
4 Convert cdata to a justified 72 column block (eg. totally 
  mangle formatting and word structure). This is usefull for, e.g., binhex
  binary data streams). No indent.
  
Format levels greater than 1 replace all consecutive whitespace with a
single space character   
'''
	if type(obj)!=dict:
		tree=obj.getTree()
	else:
		tree=obj
		if type(tree['cdata'])==list:
			tree['cdata']=''.join(tree['cdata'])
	tree['attributes'].update(style)
	xml=[XMLDECLARATION]+writeNode(tree, pretty, formatCData)
	if type(fname) in [str, unicode]:
		fname = open(fname, 'w')	
	if pretty:
		xml='\n'.join(xml)
	else:
		xml=''.join(xml)
	fname.write(xml)
	if not fname.__class__==StringIO.StringIO:
		fname.close()
 
if __name__=='__main__':
	from sys import argv
	from time import time
	start = time()
	e=readTree(argv[1])
	#print e
	split = time()
	e=assignClasses(e,{"default class":BaseXMLObject})
	#print e
	split2 = time()
	writeXML('test.xml', e, style={}, pretty=True, formatCData=1)
	stop=time()
	print split-start, split2-split, stop - split2
	
	
	

