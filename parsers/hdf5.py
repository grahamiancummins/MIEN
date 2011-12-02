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

import os
#from string import join
#from tables import *
	
def makeH5Group(hf, g):
	if g.startswith("/"):
		g = g[1:]
	if not g:
		return
	gs = g.split("/")
	path = "/"
	for i in range(len(gs)):
		try:
			g =  hf.getNode(path, name = gs[i], classname = "Group")
		except LookupError:
			#print path, gs[i]
			hf.createGroup(path, gs[i], 'h5support group')
		path += gs[i]+"/"
	

def writeH5a(fname, a, header):
	try:
		group = header['h5group']
		name = header['Name']
	except KeyError:
		try:
			from mien.datafiles.h5browser import browseH5
			group, name = browseH5(fname, header.get("gui"))
			if not group:
				raise
		except:	
			print "No group info. save aborted"
			return
	group = group.replace(" ", "")
	name = name.replace(" ", "")
	if not group.startswith("/"):
		group = "/"+group
	h5file = openFile(fname, 'a')
	makeH5Group(h5file, group)
	com = header.get("Comment", "")
	try:
		ar = h5file.getNode(group, name=name)
		ar.remove()
	except:
		pass
	ar=h5file.createArray(group, name, a, com)
	for k in  header:
		if k in ["Name", "h5group", "Comment", "gui"]:
			continue
		exec("ar.attrs.%s = header[k]" % (k,))
	#print "wrote node %s in group %s in file %s" %(name, group, fname)	
	h5file.close()	


class h5File:
	def __init__(self, fname):
		self.file =  openFile(fname, 'a')
		self.format = 'h5'

	def __del__(self):
		self.file.close()

	def objects(self):
		return [i._v_pathname for i in self.file('/', 'Leaf')]

	def read(self, path=None):
		if not path:
			path = self.objects()[0]
		elif not path.startswith('/'):
			path = '/'+path
		return self.file.getNode(path).read()

	def header(self, path=None):
		if not path:
			path = self.objects()[0]
		elif not path.startswith('/'):
			path = '/'+path
		n = self.file.getNode(path)
		head = {}
		for an in n.attrs._f_list(attrset='user'):
			exec("head['%s'] = n.attrs.%s" % (an, an))
		if not head.has_key("Labels"):
			if head.has_key("Columns"):
				cols = int(head["Columns"])
			else:
				d = self.read(path)
				cols = d.shape[1]
				head["Length"] = d.shape[0]
			head["Labels"] = ["Chan%i" % i for i in range(cols)]
		if not head.has_key("Length"):
			d = self.read(path)
			head["Length"] = d.shape[0]
		return head


filetypes={}
		
if __name__ == '__main__':
	app = wx.PySimpleApp()
	f = h5Gui("foo.h5", None)
	f.Show(True)
	app.MainLoop()
	
