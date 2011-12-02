#!/usr/local/bin/python

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

import sys, os, re
from mien.math.array import *

def eucd(pnt, pnt2):
	return ( (pnt2[0]-pnt[0])**2+(pnt2[1]-pnt[1])**2+(pnt2[2]-pnt[2])**2 )**.5

def readbbt(fn):
	lines=open(fn).readlines()
	data=re.compile(r"\s*\d+\s+(\w)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+")
	branches=[]
	term=1
	branch=0
	fiducial=0
	varicosity=0
	ts=0
	bs=0
	lcb=0
	skew=0
	sections=[]
	for lineno, line in enumerate(lines):
		m=data.match(line)
		if not m:
			continue
		type=m.group(1)
		point=tuple(map(float, m.groups()[1:]))
		if type.lower()=="v":			
			if not varicosity:
				varicosity=point
		elif varicosity and type=="T":
			point=varicosity
			varicosity=0
		else:
			varicosity=0	
		if type=='F':
			fiducial=1
			continue
		elif type=="f":
			if not fiducial:
				fiducial=1
				type="T"
			else:
				continue
		elif type=="c":
			if fiducial:
				fiducial=0
				continue
		elif term and fiducial and type in ['t', 'T']:
			fiducial=0
			continue
		else:
			fiducial=0
		if type=="b":
			lcb+=1
			type="C"	
		type=type.lower()
		if not type in ["c", "t", "b", "s"]:
			continue
		if term:
			term=0
			if branches:
				parent=branches.pop()
			else:	
				if not sections:
					parent=None
				else:
					print "WARN: unattached branch at %i" % lineno
					parent=0
					
			sections.append({'parent':parent,'startpt':point, 
				'startline':lineno, 'children':[], 'skew':0, 'npts':0})
			if parent:
				sections[parent]['children'].append(len(sections)-1)
				pep=sections[parent]['endpt']
				sections[-1]['pendpt']=pep
				d1=eucd(pep, point)
				sections[-1]['skew']=d1
				skew+=d1
		if branch:
			branch=0
			parent=len(sections)-1
			branches.append(parent)
			sections.append({'parent':parent,'startpt':point, 
				'startline':lineno, 'children':[], 'skew':0, 'npts':0})
			sections[parent]['children'].append(len(sections)-1)
			pep=sections[parent]['endpt']
			sections[-1]['pendpt']=pep
			d1=eucd(pep, point)
			sections[-1]['skew']=d1
			skew+=d1
		if type=="b":
			bs+=1
			branch=1
			sections[-1]['endpt']=point
			sections[-1]['endline']=lineno
		if type=="t":
			ts+=1
			term=1
			sections[-1]['endpt']=point
			sections[-1]['endline']=lineno
		sections[-1]['npts']+=1
	return sections, bs, ts, skew, lcb



def scanBBT(fn):
	secs,b,t,s, lcb=readbbt(fn)
	print "found %i lower case b tags" % lcb
	minskew=s
	print "skew is %f" % minskew
	print "%i branches and %i terminations" % (b, t)
	if t==b+1:
		print "all branches terminate"
	else:
		print "file contains %i missing terminations (or extra branches)" % (b-t+1)
	for s in secs:
		if s['skew']>10:
			print 'section defined on lines %i-%i has high skew (%.1f)' % (s['startline'], s['endline'], s['skew'])
		l = eucd(s['startpt'], s['endpt'])
		if l > 20:
			print 'section defined on lines %i-%i is long (%.1f microns in %i pts)' % (s['startline'], s['endline'], l, s['npts'])
			
def correctBBT(fn):			
	location=0
	for i in range(len(lines)):
		testlines=lines[:]
		spl= testlines[i].split()
		if len(spl)<6:
			continue
		if spl[1].lower()=="b":
			spl[1]="C"
			testlines[i]=''.join(spl)
		elif spl[1].lower()=="c":
			spl[1]="T"
			testlines[i]=''.join(spl)
		else:
			continue
		n,b,t,s, lcb=readbbt(testlines)
		if s<minskew:
			location=i
			minskew=s
		if i%50==0:
			print "at line %i, got %f by changing %i" % (i, minskew, location)
	print "minimal skew of %f obtained by modifying line %i" % (minskew,location) 
		


if __name__=='__main__':
	fn=	sys.argv[1]
	scanBBT(fn)


		
	
