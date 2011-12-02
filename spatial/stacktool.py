#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2008-06-23.

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

import cPickle, re
from mien.image.arrayops import image_to_array, array_to_image
from mien.wx.dialogs import wx, makeEntryWidget
from mien.wx.graphs.graphGL import *


class AlignmentTool(wx.Dialog):
	def __init__(self, master):
		wx.Dialog.__init__(self, master)
		self.st=master
		self.imcenter=None
		self.SetTitle("Image Stack Alignment")
		sizer = wx.BoxSizer(wx.VERTICAL)
		tw = self.GetTextExtent("W")[0]*30
		
		#anchor, pixelwidth, pixelheight, stackspacing, rotate
		self.vals={}
		for foo in ['Anchor X', 'Anchor Y', 'Anchor Z', 'PixelWidth', 'PixelHeight', 'StackSpacing', 'Rotation (Deg CCW)']:
			d={'Name':foo}
			if foo =='Anchor X':
				d['Value']=float(self.st.stack.attrib('SpatialAnchor')[0])
			elif foo =='Anchor Y':
				d['Value']=float(self.st.stack.attrib('SpatialAnchor')[1])
			elif foo =='Anchor Z':
				d['Value']=float(self.st.stack.attrib('SpatialAnchor')[2])		
			elif foo.startswith('Rotation'):
				d['Value']=self.getRotation()
			else:
				d['Value']=float(self.st.stack.attrib(foo))
			box = makeEntryWidget(self, d)
			self.vals[foo]=d
			sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER|wx.ALL, 5)
		#apply
		btn = wx.Button(self, -1, " Apply New Parameters ")
		wx.EVT_BUTTON(self, btn.GetId(), self.apply)
		btn.SetDefault()
		sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)						
		#Reset center
		btn = wx.Button(self, -1, " Set Center ")
		wx.EVT_BUTTON(self, btn.GetId(), self.setcent)
		sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)						
		#quit
		btn = wx.Button(self, -1, " Close ")
		wx.EVT_BUTTON(self, btn.GetId(), lambda x:self.Destroy())
		sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		sizer.Fit(self)
	
	def getRotation(self):
		w=self.st.getSpatial()[1,:]
		a=correctedArctan(w[0], w[1], 'deg')
		return a
	
	def setcent(self, event):
		p=self.st.cv
		g=p.graph
		if not dot(g.forward, [0,0,-1])>.99:
			p.report("You can only pick a center in plan view (e.g. z axis=[0,0,1])")
			return 
		ulg,wg,hg=g.frontPlane()
		a=self.st.getSpatial()
		ul, down, w, h= a[0,:], a[3,:], a[1,:], a[2,:]
		h=-h
		size=self.st.stack.shape()
		frame=0
		while ulg[2]<ul[2]:
			ul+=down
			frame+=1
		if frame>=size[3]:
			p.report("No frames in view.")
			return 
		cp=ulg+wg/2.0+hg/2.0
		dfc=cp-ul
		dfcx=dot(dfc, w)/sum(w**2)
		dfcy=dot(dfc, h)/sum(h**2)
		if max(dfcy, dfcx)>1.0 or min(dfcy, dfcx)<0.0:
			p.report("View center isn't in a image")
			return 
		w=round(size[0]*dfcx)
		h=round(size[1]*dfcy)
		self.imcenter=array([w, h, frame]).astype(int32)
		p.report('setting center to voxel %i %i %i' % (self.imcenter[0], self.imcenter[1],self.imcenter[2]))
		self.apply(None)

	def apply(self, event):
		if self.Validate() and self.TransferDataFromWindow():
			ul=array( (self.vals['Anchor X']['Value'],
			 			self.vals['Anchor Y']['Value'],
			 			self.vals['Anchor Z']['Value'])
					)
			rot=self.vals['Rotation (Deg CCW)']['Value']
			pw=self.vals['PixelWidth']['Value']
			ph=self.vals['PixelHeight']['Value']
			ss=self.vals['StackSpacing']['Value']
			rot= rot % 360
			rr=rot*pi/180
			x=array((cos(rr), sin(rr), 0))
			z=array((0.0, 0.0, -1.0))
			y=cross(x, z)
			size=self.st.stack.shape()[:2]
			w=x*size[0]*pw
			h=y*size[1]*ph
			if self.imcenter!=None:
				offset=array([pw*self.imcenter[0], -ph*self.imcenter[1], ss*self.imcenter[2]])
				if rot:
					offset=rotate3D(array([offset]), (0,0,rot))[0,:]
				#ul=2*self.imcenter-offset
				ul-=offset
				
	
			down=z*ss
			dat=vstack([ul, w, h, down])
			self.st.setSpatial(dat)

	

class StackTool(wx.Dialog):
	def __init__(self, master, stack):
		wx.Dialog.__init__(self, master)
		self.cv=master
		self.stack=stack
		self.condition(stack)
		self.showalllines=0
		self.frame=-1
		self.SetTitle("Image Stack Tool")
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		btn = wx.Button(self, -1, " Align Stack ")
		wx.EVT_BUTTON(self, btn.GetId(), self.align)
		sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		btn = wx.Button(self, -1, " Edit Stack ")
		wx.EVT_BUTTON(self, btn.GetId(), self.editor)
		sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		#nav
		box = wx.BoxSizer(wx.HORIZONTAL)
		btn = wx.Button(self, -1, " prev ")
		wx.EVT_BUTTON(self, btn.GetId(), self.prev)
		box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)						
		btn = wx.Button(self, -1, " next ")
		wx.EVT_BUTTON(self, btn.GetId(), self.next)
		box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)						
		sizer.Add(box, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		self.atZlevel= wx.TextCtrl(self, -1, "0", style=wx.TE_PROCESS_ENTER, size=(12,-1))
		wx.EVT_TEXT_ENTER(self, self.atZlevel.GetId(), self.setZlevel)
		sizer.Add(self.atZlevel, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		#show all lines
		btn = wx.Button(self, -1, " Toggle Show all Line Fiducials ")
		wx.EVT_BUTTON(self, btn.GetId(), self.toglines)
		sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		btn = wx.Button(self, -1, " Toggle Stack Transparency ")
		wx.EVT_BUTTON(self, btn.GetId(), self.togtrans)
		sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		#animate
		btn = wx.Button(self, -1, " Animate Stack ")
		wx.EVT_BUTTON(self, btn.GetId(), self.animate)
		sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		btn = wx.Button(self, -1, " Close ")
		wx.EVT_BUTTON(self, btn.GetId(), lambda x:self.Destroy())
		sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		sizer.Fit(self)
		self.Show(True)

		
	def editor(self, event):
		from mien.image.viewer import ImageViewer
		i=ImageViewer(self.cv)
		i.Show(True)
		i.select(self.stack)
		
	def report(self, s):
		self.cv.report(s)

	def condition(self, stack):
		if not stack.attrib('SpatialAnchor'):
			stack.setAttrib('SpatialAnchor', (0.0,0.0,0.0))
		if not stack.attrib('SpatialVertical'):
			stack.setAttrib('SpatialVertical', (0.0,1.0,0.0))
		if not stack.attrib('SpatialDepth'):
			stack.setAttrib('SpatialDepth', (0.0,0.0,-1.0))
		if not stack.attrib('PixelWidth'):
			stack.setAttrib('PixelWidth', 1.0)
		if not stack.attrib('PixelHeight'):
			stack.setAttrib('PixelHeight', stack.attrib('PixelWidth'))
		if not stack.attrib('StackSpacing'):
			stack.setAttrib('StackSpacing', 1.0)
		pn= self.cv.getPlotName(stack)
		if not pn:
			pn=self.cv.graph.plotXML(stack)
			self.cv.graph.OnDraw()
		self.plotname=pn	

	def align(self, event):
		foo=AlignmentTool(self)
		foo.Show(True)
		
	def prev(self, event):
		self.frame-=1
		self.displayzlevel(self.frame)

	def next(self, event):
		self.frame+=1
		self.displayzlevel(self.frame)

	def setZlevel(self, event):
		l=int(self.atZlevel.GetValue())
		self.displayzlevel(l)

	def getSpatial(self):		
		ul=array(self.stack.attrib('SpatialAnchor'))
		y=array(self.stack.attrib('SpatialVertical'))
		z=array(self.stack.attrib('SpatialDepth'))
		x=cross(z, y)
		pw=self.stack.attrib('PixelWidth')
		ph=self.stack.attrib('PixelHeight')
		pd=self.stack.attrib('StackSpacing')
		size=self.stack.getData().shape[:2]
		down=z*pd
		w=pw*x*size[0]
		h=ph*y*size[1]
		dat=vstack([ul, w, h, down])
		return dat
		
	def setSpatial(self, dat, draw=True):
		self.stack.setAttrib('SpatialAnchor', tuple(dat[0,:]))
		th=sqrt((dat[2,:]**2).sum())
		vert=dat[2,:]/th
		self.stack.setAttrib('SpatialVertical', tuple(vert))
		ss=sqrt((dat[3,:]**2).sum())
		dep=dat[3,:]/ss
		self.stack.setAttrib('SpatialDepth', tuple(dep))
		tw=sqrt((dat[1,:]**2).sum())
		size=self.stack.getData().shape[:2]
		self.stack.setAttrib('PixelWidth', tw/size[0])
		self.stack.setAttrib('PixelHeight', th/size[1])
		self.stack.setAttrib('StackSpacing', ss)
		self.cv.graph.plots[self.plotname]['data']=dat
		self.cv.graph.recalc(self.plotname)
		if draw:
			self.cv.graph.OnDraw()

	def displayzlevel(self, z):	
		self.atZlevel.SetValue(str(z))
		self.frame = z
		a=self.getSpatial()
		ul, down, w, h= a[0,:], a[3,:], a[1,:], a[2,:]
		cp=ul+w/2+h/2				
		cp=cp+z*down+.0001*down
		self.cv.graph.viewpoint[2]=cp[2]
		self.cv.graph.forward=array([0.0,0,-1])
		self.cv.graph.OnDraw()
			
	def toglines(self, event):
		g=self.cv.graph
		if self.showalllines:
			self.showalllines=False
			for p in g.plots.keys():
				pl=g.plots[p]
				if pl['style']=='contour':
					pl['lineprojection']=0
					g.recalc(p)	
		else:	
			self.showalllines=True
			a=self.getSpatial()
			av=a[0,1]
			mv=av
			for p in g.plots.keys():
				pl=g.plots[p]
				if pl['style']=='contour':
					pl['lineprojection']=1
					g.recalc(p)		
			mv=av-mv	
		g.OnDraw()
		
	def togtrans(self, event):
		if self.stack.attrib('transparent'):
			self.stack.setAttrib('transparent', '')
			self.cv.graph.plots[self.plotname]['transparent']=False
		else:
			self.stack.setAttrib('transparent', 1)
			self.cv.graph.plots[self.plotname]['transparent']=True
		self.cv.graph.recalc(self.plotname)
		self.cv.graph.OnDraw()
	
	
	def animate(self, event):
		dir='StackAnimation'
		if os.path.isdir(dir):
			os.system("rm -rf %s" % dir)
		os.mkdir(dir)
		for i in range(self.stack.shape()[3]):
			self.displayzlevel(i)
			g=self.cv.graph
			fname=os.path.join(dir, "frame%05i.bmp" % i)
			g.screenShot(fname=fname)
			print fname
		self.cv.report("Saved Images")
		
def launchStackTool(cv):
	stacks = cv.document.getElements('Data', {'SampleType':'image'})
	if not stacks:
		cv.report("There are no image stacks in this document. Load some images using the normal MIEN file load or append functions.")
		return
	if len(stacks)==1:
		StackTool(cv, stacks[0])
		return
	sd={}
	for i in stacks:
		si="%s %s" % (i.upath(), str(i.shape()))
		sd[si]=i
	d=cv.askParam([{'Name':"Which Stack?", "Type":"List", "Value":sd.keys()}])
	if not d:
		return
	StackTool(cv, sd[d[0]])
	