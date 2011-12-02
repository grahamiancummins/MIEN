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

import re

def autoWrap(s, col):
	l=[]
	while len(s)>col:
		spid=s[:col].rfind(" ")
		if spid==-1:
			l.append(s[:col-1]+'-')
			s=s[col-1:]
		else:
			l.append(s[:spid])
			s=s[spid+1:]
	l.append(s)
	return l

def blockIndent(s, nspace, col=70):
	s=re.sub("\s+", " ", s)
	lead=nspace*" "
	lines=autoWrap(s, col)
	lines=[lead+x for x in lines]
	return "\n".join(lines)

	
	
