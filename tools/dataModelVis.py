#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2008-04-11.

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


import os

if __name__=='__main__':
	import sys, getopt
	usage='''
		d display
		l list (list all used tags)
		r recursive directory list
		v verbose
		B disable blocks
		c show classes
	'''
	try:
		options, files = getopt.getopt(sys.argv[1:], "cdlrvB", ["version"])
	except getopt.error:
		print usage
		sys.exit()	
	switches={}
	for o in options:
		switches[o[0].lstrip('-')]=o[1]
	if switches.has_key("B"):
		os.environ['MIEN_EXTENSION_DISABLE']='1'
	
from mien.tools.tagtool import flist, alltags, elements, mread

def allParents(c, d, roots=(object,)):
	if d.has_key(c.__name__):
		return
	d[c.__name__]=[c2.__name__ for c2 in c.__bases__ if not c2 in roots]
	for pc in c.__bases__:
		if not pc in roots:
			allParents(pc, d)
	

def depth(cn, d):
	if not d[cn]:
		return 1
	pd=max([depth(pn, d) for pn in d[cn]  if not pn==cn])	
	return pd+1	
	
def classHierarchy(t=None):
	ch={}
	for e in elements.values():
		allParents(e, ch)
	if not t:	
		return ch
	return pgraph(ch, t)
	
	
	
def findsig(e, ch):
	kids=[el for el in ch.keys() if e in ch[el]]
	return (tuple(ch[e]), tuple(kids))
	
def findequiv(ch, depths):
	equivs={}
	ndepths=[]
	nch={}
	for dl in depths:
		lequivs={}
		sigs={}
		for e in dl:
			s=findsig(e, ch)
			for ec in lequivs.keys():
				if s==sigs[ec]:
					lequivs[ec].append(e)
					break
			else:
				lequivs[e]=[]
				sigs[e]=s
		equivs.update(lequivs)
		ndepths.append(lequivs.keys())
		for ec in lequivs.keys():
			nch[ec]=ch[ec]
	return (nch, ndepths, equivs)
	
		
def displaydot(dot, fn='mien_viz'):
	if not fn.endswith('dot'):
		fn=os.path.splitext(fn)[0]+'.dot'
	open(fn,'w').write(dot)
	os.system("dot -Tpng -O %s" % fn)
	os.system("open %s.png" % fn)
	return dot	
	
def pgraph(ch, t='dot'):
	depths=[]
	for e in ch.keys():
		ed=depth(e, ch)
		while len(depths)<ed:
			depths.append([])
		depths[ed-1].append(e)
	if t=='depth':
		return depths
	ch, depths, equivs = findequiv(ch, depths)	
	dot=["digraph G {",
		'graph [center=1, rankdir="LR"];']
	sgl=1	
	for dl in depths:
		dot.append("subgraph lev_%i {" % (sgl,))
		dot.append("rank = same;")
		sgl+=1
		for cn in dl:
			if not equivs[cn]:
				dot.append("%s;" % cn)
			else:
				cl=[cn]+equivs[cn]
				cl.sort()
				if len(cl)>10:
					nv=min(int(round(len(cl)/8)), 5)
					print nv
					while len(cl) % (nv-1) > len(cl) % nv:
						nv-=1
					print nv
					iii=0
					ncl=[]
					item=cl.pop()
					while item:
						if not iii%nv:
							ncl.append([])
						iii+=1	
						ncl[-1].append(item)
						try:
							item=cl.pop()
						except:
							item=None
					print ncl
					cl=[','.join(l) for l in ncl]
				dot.append('%s [label="%s" shape="record"];' % (cn, "|".join(cl)))
					
		dot.append("}")
	dot.append("subgraph inheritance {")
	for cn in ch.keys():
		for pn in ch[cn]:
			dot.append("%s->%s;" % (pn, cn))
	dot.append("}")
	dot.append("}")
	dot="\n".join(dot)
	if t=='dot':
		return dot
	displaydot(dot)	
		



def _xpathd(el, path=""):
	nd={}
	for k in el.keys():
		nk="/".join([path, k])
		ncd={}
		if el[k]:
			ncd=_xpathd(el[k], nk)
		nd[nk]=ncd
	return nd

def _uidd(el, nd=None, uid=0):
	if not nd:
		nd={}
	nel={}
	for k in el.keys():
		nk="node%i" % uid
		nd[nk]=k
		uid+=1
		ncd={}
		if el[k]:
			ncd, nd, uid=_uidd(el[k], nd, uid)
		nel[nk]=ncd
	return (nel, nd, uid)

def _d2lc(el):
	#{doc.__tag__:[1, {}]}
	el, nd, nnodes=_uidd(el)
	l=[]
	c=[]
	while el.keys():
		ll=[]
		nel={}
		for k in el.keys():
			ll.append((k,  nd[k]))
			for kk in el[k].keys():
				c.append((k, kk))
				nel[kk]=el[k][kk]
		l.append(ll)
		el=nel
	return (l, c)

def lgraph(layers, connections, t=None):
	dot=["digraph G {",
		'graph [center=1, rankdir="LR"];']
	cgraph=["subgraph connections {"]	
	sgl=0
	for i, l in enumerate(layers):
		dot.append("subgraph lev_%i {" % (i,))
		dot.append("rank = same;")
		for n in l:
			dot.append('%s [label="%s"];' % (n[0], n[1]))
		dot.append("}")
	dot.append("subgraph connections {")
	for c in connections:
		dot.append("%s->%s;" % (c[0], c[1]))		
	dot.append("}")
	dot.append("}")
	dot="\n".join(dot)
	if t=='dot':
		return dot
	displaydot(dot)	


def xmlStructure(doc, t='dot'):
	par={doc.__tag__:[]}
	for e in doc.getElements():
		t=e.__tag__
		pt=e.container.__tag__
		if not par.has_key(t):
			par[t]=[]
		if not pt in par[t]:
			par[t].append(pt)
	#print par
	return pgraph(par, t)
			
			
def _combineDict(d1, d2):
	for k in d2.keys():
		if not d1.has_key(k):
			d1[k]=d2[k]
		else:
			d1[k][0]+=d2[k][0]
			_combineDict(d1[k][1], d2[k][1])

def _num2name(el):
	nel={}
	for k in el.keys():
		if el[k][0]>1:
			nk="%s (%i)" % (k, el[k][0])
		else:
			nk="%s" % (k,)
		ncd=_num2name(el[k][1])
		nel[nk]=ncd
	return nel


def xmlFullStructure(el, t='dot'):
	eld={el.__tag__:[1, {}]}
	ed=eld[el.__tag__][1]
	for e in el.elements:
		xs=xmlFullStructure(e, t='dict')
		_combineDict(ed, xs)
	if t=='dict':
		return eld
	eld=_num2name(eld)	
	l, c=_d2lc(eld)
	return lgraph(l, c, t)

		
def mod2dot(fname, display=False, detail='high'):
	print detail
	doc=mread(fname)
	if detail=='low':
		d=xmlStructure(doc, 'dot')
	else:
		d=xmlFullStructure(doc, 'dot')
	if not display:
		return d
	displaydot(d, fname)
	

if __name__=='__main__':
	
	os.environ['MIEN_NO_VERIFY_XML']='1'
	disp=switches.has_key('d')	
	if switches.has_key('c'):
		if disp:
			classHierarchy('plot')
		else:
			classHierarchy('dot')
		sys.exit()
	if switches.has_key('r'):
		files=flist(os.getcwd())
	tags={}
	if switches.has_key('c'):
		if switches.has_key('l'):
			k=elements.keys()
			k.sort()
			for c in k:
				print c
		else:
			classHierarchy(disp)
		sys.exit()
	for fname in files:
		print fname
		if switches.has_key('l'):
			lt=alltags(fname)
			for t in lt:
				if not tags.has_key(t):
					tags[t]=[]
				if switches.has_key('v'):
					tags[t].append(fname)
					
		else:
			mod2dot(fname, disp)
	print '----'		
	for t in tags.keys():
		print t
		for fn in tags[t]:
			print "    %s" % fn
			
		