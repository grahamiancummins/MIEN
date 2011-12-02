
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
WHITESPACE = {" ":{},
			  "\r":{},
			  "\t":{},
			  "\f":{},
			  "\v":{}}
			
class Tokenizer:
	'''generic file tokenizer'''
	def __init__(self, fileobj, instructions, space=1):
		'''fname(str), instructions (dict), space (int=1) => instance
fname is a file name. Instructions is a hash of strings  onto
subhashes. Subhashes may contain:
They may contain:
readto (str):- read characters (ignoring other instructions) until the
        closing string is encountered. (returns the entire segment
		including the opening and closing strings)		
return (int): If not zero, eturn the delimiter itself.
         (default is to throw away delimiters and return only what
		 falls between them)

if space is true instructions to add " \r\t\f\v" (non-newline whitespace)
as non-returning delimiters are automatically added to the instruction
hash.'''
		self.file=fileobj
		self.inst=instructions
		if space:
			self.inst.update(WHITESPACE)
		self.queue=None


	def handle_match(self, delim):
		if self.inst[delim].get("return"):
			return delim
		else:
			rt =  self.inst[delim].get("readto")
		if not rt:
			return ""
		content = ""
		c=''
		while 1:
			if not c:
				c= self.file.read(1)
			if not c:
				raise StandardError("EOF occured while waiting for closing delimiter")
			if rt==c:
				return delim+content+c
			elif rt.startswith(c):
				c+= self.file.read(1)
			else:
				content+=c[0]
				c=c[1:]
					
			
	def next(self):
		if self.queue:
			r = self.handle_match(self.queue)
			self.queue=None
			return r
		token=""
		delim=""
		c=""
		p=self.inst.keys()
		while 1:
			if not c:
				c = self.file.read(1)
			if not c:
				if token:
					return token
				else:
					return "EOF"	
			p=self.check(c, p)
			if type(p)!=type([]):
				if token:
					if self.inst[p]:
						self.queue = p
					return token
				elif self.inst[p]:
					return self.handle_match(p)
				else:
					c = ""
					p=self.inst.keys()
			elif len(p)>0:
				c+=self.file.read(1)
			else:
				token+=c[0]
				c=c[1:]
				p=self.inst.keys()

	def check(self, delim, instrs):
		possible=[]
		for i in instrs:
			if i==delim:
				return i
			elif i.startswith(delim):
				possible.append(i)
		return possible
