#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2008-02-27.

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

from HTMLParser import HTMLParser
import StringIO, re, urllib
from mien.xml.xmlhandler import assignClasses

whitespace=re.compile(r"\s+")
linebreak=re.compile(r"\s*\n\s*")
INDENT="  "

class QuickParser(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.elements=[]
		self.closed=False

	def	handle_startendtag(self, tag, attrs):
		# print 'startend %s' % tag
		ob={'tag':tag, 'attributes':dict(attrs), 'elements':[], 'cdata':''}
		self.elements[-1]['elements'].append(ob)
		

	def handle_starttag(self, name, attrs):	
		name=name.lower()
		# print "open %s - " % name
		# print [x['tag'] for x in self.elements]
		ob={'tag':name, 'attributes':dict(attrs), 'elements':[], 'cdata':[]}
		if self.elements:
			self.elements[-1]['elements'].append(ob)
		self.elements.append(ob)	
		self.closed=False
		
	def handle_data(self, characters):
		'''characters(str) =>None
If self.object.cdata is a string, append charaters to it'''
		if self.elements and not self.closed:
			self.elements[-1]['cdata'].append(characters)

	def  handle_endtag(self, name):
		'''name(str) => None
if self.tag==name, call cleanUp, then change the handler back self.handler'''
		name=name.lower()
		while not self.elements[-1]['tag']==name:
			tags= [x['tag'] for x in self.elements]
			if not name in tags:
				print "WARNING: tag %s can't be closed correctly" % name
				print tags
				print "Ignoring close tag"
				return
			self.handle_endtag( self.elements[-1]['tag'])
		# print "close %s" % name
		self.elements[-1]['cdata']=''.join(self.elements[-1]['cdata']).strip()
		if len(self.elements)>1:
			self.elements.pop()
		else:
			self.closed=True	


def checkdata(el):
	if type(el['cdata']) in [list, tuple]:
		print "WARNING: element %s has bad cdata" % el['tag']
		el['cdata']=''.join(el['cdata'])
	for e in el['elements']:
		checkdata(e)

def read(fname, toObject=False):
	'''returns a tree structure for the document (made of dicts)'''
	if type(fname) in [str, unicode]:
		fname = urllib.urlopen(fname)
	sp = QuickParser()
	sp.feed(fname.read())
	sp.close()
	# checkdata(sp.elements[0])
	# print len(sp.elements)
	if not toObject:
		return sp.elements[0]
	return assignClasses(sp.elements[0], {})

def parseString(s, toObject=False):
	f=StringIO.StringIO(s)
	return read(f, toObject)
	

def url2object(url):
	s=urllib.urlopen(url).read()
	s=parseString(s, True)
	return s

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
	if type(d['cdata'])==list:
		d['cdata']=''.join(d['cdata'])
	d['cdata']=d['cdata'].strip()
	open = "<"+d["tag"]
	for a in d['attributes'].keys():
		open+=' %s="%s"' % (a, d['attributes'][a])
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

def write(fname, tree, style={}, pretty=True, formatCData=False):
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
	tree['attributes'].update(style)
	xml=writeNode(tree, pretty, formatCData)
	if type(fname) in [str, unicode]:
		fname = open(fname, 'w')
	if pretty:
		xml='\n'.join(xml)
	else:
		xml=''.join(xml)
	fname.write(xml)
	if not fname.__class__==StringIO.StringIO:
		fname.close()
 

	
	

