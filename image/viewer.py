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
from mien.wx.base import *
from mien.wx.graphs.graph import Graph
import mien.image.imextend as ime
from numpy import array, int32, maximum, minimum, sqrt

class ImageViewer(BaseGui):

	def __init__(self, master=None,returnData=None ):
		BaseGui.__init__(self, master, title="Image Viewer", menus=["File", "Controls", "Tools"], pycommand=True,height=4)
		
		self._current_display=[-1, 0]
		self._framecache=None
		self.images=[]
		
		controls=[["File", "New Viewer", self.newView],
					 ["File", "profile", self.prof],
					 ["File", "Save Measurements", self.saveMeasure],
				  ["Controls","Marker Locations",self.markInfo],
					["Controls", "Toggle pseudocolor", self.pcolor],
					["Controls", "Set Contrast Range", self.setRange],
					["Controls", "Show Contrast Range", self.getRange],
					["Controls", "Remove Contrast Range", self.remRange],
					["Controls", "Maximize Contrast", self.maxRange],
					["Controls", "Calibrate Measurements", self.calibM],
					["Controls", "Goto Frame", self.showFrame]]	
		
		self.mainSizer = wx.BoxSizer(wx.VERTICAL)
		self.main.SetSizer(self.mainSizer)
		self.main.SetAutoLayout(True)
		
		self.graph=Graph(self.main, -1)
		self.graph.axis["ticks"] = 0
		self.graph.legend = False
		#self.graph.fixAR=1.0
	
		psize = wx.BoxSizer(wx.HORIZONTAL)
		psize.Add(self.graph, 3, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		self.imlist = AWList(self.main, -1, style=wx.LC_REPORT
							 | wx.SUNKEN_BORDER | wx.WANTS_CHARS)
		self.imlist.InsertColumn(0, "Images")
		wx.EVT_LEFT_DCLICK(self.imlist, self.OnItemClick)
		psize.Add(self.imlist, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		self.mainSizer.Add(psize, 10, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		
		if master:
			self.xm = master
			self.document = self.xm.document
			self.images=self.document.getElements('Data', {'SampleType':'image'})
			for d in self.images:
				self.addItem(d)
			controls.append(["File", "Close", lambda x: self.Destroy()])
			self.fillMenus(controls)
		else:
			controls.append(['Controls', 'Launch Data Editor', self.launchDE])
			self.fillMenus(controls)
			self.stdFileMenu()
		
		# id=wx.NewId()
		# self.menus["Controls"].AppendCheckItem(id, "Measure")
		# wx.EVT_MENU(self, id, self.measureMode)
		self._inMeasureMode = False
		self.measurements=[]
		self.measureCalib = None
		
		cbox = wx.BoxSizer(wx.HORIZONTAL)
		self.tmeasure = wx.ToggleButton(self.main, -1, " Measure ")
		cbox.Add(self.tmeasure, 0, wx.ALIGN_BOTTOM|wx.ALL, 5)
		wx.EVT_TOGGLEBUTTON(self.main, self.tmeasure.GetId(), self.measureMode)
		btn = wx.Button(self.main, -1, " Previous ")
		cbox.Add(btn, 0, wx.ALIGN_BOTTOM|wx.ALL, 5)
		wx.EVT_BUTTON(self.main, btn.GetId (), self.previous)
		btn = wx.Button(self.main, -1, " Next ")
		cbox.Add(btn, 0, wx.ALIGN_BOTTOM|wx.ALL, 5)
		wx.EVT_BUTTON(self.main, btn.GetId(), self.next)
		self.imageInfo=wx.StaticText(self.main, -1, "No Image")
		cbox.Add(self.imageInfo, 1, wx.ALIGN_BOTTOM|wx.ALL, 5)
		
		self.mainSizer.Add(cbox, 0, wx.GROW|wx.ALIGN_BOTTOM|wx.ALL, 5)		
			
		self.graph.keybindings['space']=self.next
		self.graph.keybindings['backspace']=self.previous	
			
		gfdt=FileDropLoad(self)
		self.imlist.SetDropTarget(gfdt)
		self.graph.twoDzoom=True
		self.graph.Show(True)
		self.extmod=ime.IVExtMod(self)
		self.extmod.makeMenus()
		self.mainSizer.Fit(self)
		self.SetSize(wx.Size(1000,700))

	def prof(self, event):
		import profile
		profile.runctx("self.display(0,0)", globals(), locals())
		
	def launchDE(self, event=None):
		'''Launch a MIEN XML Editor window '''
		from mien.interface.main import MienGui
		d=MienGui(self)
		d.newDoc(self.document)	
		
	def newView(self, event=None):
		'''Make another image viewer as a child of the current one (viewing the same document) '''
		i=ImageViewer(self)
		i.Show(True)
		i.onNewDoc()
		
	def select(self, data):
		'''Display (and select in the image list) the image contained in element data. Data is an instance, but it is used to select from the list self.images, so it must be an instance in the current document.'''
		self.display(self.images.index(data))
		
	def getSelected(self, mode='instances'):
		'''Returns a list of the currently selected images. Mode may be "indexes" (returns integer indexes into the image list), "instances" (returns the objects themselves), or "paths" (returns the upaths of the objects).'''
		sel=[]
		for i in range(self.imlist.GetItemCount()):
			s=self.imlist.GetItemState(i, wx.LIST_STATE_SELECTED)
			if s:
				sel.append(i)
		if mode=='indexes':
			return sel
		images=[self.images[i] for i in sel]
		if mode=='instances':
			return images
		return [i.upath() for i in images]
		
	def onNewDoc(self):
		'''Internal method. Update the image list when the document changes'''
		cdi=None
		self._framecache=None
		if self._current_display[0]>=0:
			cdi=self.images[self._current_display[0]].upath()
		self.images=self.document.getElements('Data', {'SampleType':'image'})
		self.imlist.DeleteAllItems()
		for d in self.images:
			self.addItem(d)
		if cdi:	
			try:
				self.document.getInstance(cdi)
				self.display(-1)
			except StandardError:
				self.display(None)
		elif self.images:
			self.display(0)	
			
			
	def getCurrentImage(self):	
		'''Returns the instance of the currently displayed image if there is one, or the first image in the selection list, or None if there is no display and no selection '''	
		if self._current_display[0] > -1:
			return self.images[self._current_display[0]]
		else:
			try:
				i=self.getSelected('instances')[0]
				return i
			except IndexError:
				return None		
		
		
		
	def imageCoords(self, a, horiz=True, crop=True):
		'''a is a 1D array. Returns an array of the same shape converted to image coordinates for the indicated axis (horizontal if horiz is True, vertical otherwise), using the current image. Image coordinates are integer (of type int32), (0,0) is the upper right, and larger Y values are closer to the bottom of the screen. This is the reverse of Y coordinates returned by most MIEN graphs, including the labels on the Y markers. If there is no currently selected image, Y value conversion will assume an image size of 600x400px. If crop is True (default), coordinates are are constrained to never be smaller than 4 pixels of selected area, and never be larger than the size of the image. '''	
		a=array(a).astype(int32)
		im = self.getCurrentImage()
		if im:
			x=im.getData().shape[0]
			y=im.getData().shape[1]
		else:
			x=600
			y=400
		if horiz:
			s=x
		else:
			a=y-a
			s=y
		if crop:
			a=maximum(a, 0)
			a=minimum(a, s)
		return a
			
			
	def getBoundaries(self, crop=True):
		'''Return a 2x2 array, containing the bounding box of the current view ((xmin, ymin), (xmax, ymax)). Note that the values are in image coordinates, as described in self.imageCoords. '''
		l=self.graph.limits.astype(int32)
		l[2:]=self.imageCoords(l[2:], False, crop)
		l[:2]=self.imageCoords(l[:2], True, crop)
		b=array([[l[0], l[3]],[l[1], l[2]]])
		return b
		
	def getMarkers(self, crop=True):
		'''Returns a 2tuple of 1D arrays (x, y), where x contains the coordinates of all vertical markers, and y contains the coordinates of all horizontal markers. Coordinates and the behavior of the "crop" flag are as described in self.imageCoords.'''
		x=self.imageCoords([m['loc'] for m in self.graph.xmarkers], True, crop)
		y=self.imageCoords([m['loc'] for m in self.graph.xmarkers], False, crop)
		return (x, y)

	def update_self(self, **kwargs):
		'''Internal state maintenance method. This implementation calls self.onNewDoc'''
		self.onNewDoc()

	def OnItemClick(self, event=None):
		pt = event.GetPosition();
		item, flags = self.imlist.HitTest(pt)
		try:
			self.display(item)
		except:
			self.report("can't display %s" % (str(item),))
			return
	
	def addItem(self, dat):
		ind=self.imlist.GetItemCount()
		if not dat.attrib('Url'):
			dat.setAttrib('Url', "Unknown")
		name="%s (%s)" % (dat.upath(), dat.attrib('Url') )
		if len(name)>30:
			name=dat.upath()
			
		ind=self.imlist.InsertStringItem(ind, name)
		return ind

	def display(self, ind, frame=0, contrange=0):
		if ind is None:
			self._current_display=[-1, 0]
			self.graph.killAll()
			self.graph.DrawAll()
			self.imageInfo.SetLabel(' No Image ')
			return
		elif ind==-1:
			ind=self._current_display[0]
			frame=self._current_display[1]
		else:
			self._current_display=[ind, frame]
		self.imlist.SetItemState(ind, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)	
		image=self.images[ind]
		dat=image.getData()
		dshape=dat.shape
		if len(dat.shape)<3:
			ncolors=1
		else:
			ncolors=dat.shape[2]
		if len(dat.shape)<4:
			stack=0
		else:	
			stack=dat.shape[3]
			dat=dat[:,:,:,frame]
		self.graph.killAll()
		lim=array([[0.0,0.0],[dat.shape[0],dat.shape[1]]])
		self.graph.addPlot(dat, style="ScalingImage", limits=lim, colorrange=image.attrib('ColorRange'), pcolor=image.attrib('pseudocolor'))
		pw=image.attrib("PixelWidth") or 1.0
		ph=image.attrib("PixelHeight") or pw
		ar=float((pw*dat.shape[0]))/(ph*dat.shape[1])
		if self.graph.fixAR!=ar:
			self.graph.fixAR=ar
			self.graph.fullScale()
		self.graph.DrawAll()
		info = self.imlist.GetItemText(ind)
		info += " %Gx%G" % (dshape[0], dshape[1])
		if ncolors == 1:
			info+=", Grey"
		elif ncolors ==3:
			info+= ", RGB"
		else:
			info+=", %i color channels" % ncolors
		if contrange:
			info+=", levels %G to %G" % (dat.min(), dat.max())
		if stack>1:
			info+=", stack of %i frames. Showing frame %i" % (stack, frame)	
		self.imageInfo.SetLabel(info)
		if self._inMeasureMode and self.measurements:
			self.showMeasure(False)
			
	def getRange(self, event):
		ind, frame=self._current_display
		dat=self.images[ind].getData()
		info = self.imlist.GetItemText(ind)
		info += " %Gx%G" % (dat.shape[0], dat.shape[1])
		if len(dat.shape)<3 or dat.shape[2]==1:
			info+=", Grey"
		elif dat.shape[2] ==3:
			info+= ", RGB"
		else:
			info+=", %i color channels" % dat.shape[2]
		info+=", levels %G to %G" % (dat.min(), dat.max())
		if len(dat.shape)>3 and dat.shape[3]>1:
			info+=", stack of %i frames. Showing frame %i" % (dat.shape[3], frame)	
		self.imageInfo.SetLabel(info)		
		
	def showFrame(self, event):
		if not self._current_display:
			return
		try:
			dat=self.images[self._current_display[0]].getData()
			nf=dat.shape[3]
			if nf==1:
				raise
		except:
			self.report("Current image isn't a stack")
			return
		if type(event)==int:
			i=event
		else:	
			d=self.askParam([{"Name":"Frame Index (0 - %i)" % (nf-1,),
				"Type":int, "Value":self._current_display[1]}])
			if not d:
				return
			i=d[0]
		if i<0:
			i=nf+i
		if i<0 or i>nf-1:
			self.report("Current stack  doesn't have a frame index %i" % i)
			return
		self.display(self._current_display[0], i)
			

	def build_framecache(self):
		self._framecache=[]
		for i, im in enumerate(self.images):
			s=im.getData().shape
			if len(s)<4:
				nf=1
			else:
				nf=s[3]
			for j in range(nf):
				self._framecache.append((i,j))
	
	def increment(self, inc):
		if not self.images:
			return
		if not self._current_display:
			self._current_display=[0, 0]
		if not self._framecache:
			self.build_framecache()
		i=self._framecache.index(tuple(self._current_display))
		i+=inc
		if i<0:
			i=len(self._framecache)+i
		i=i % len(self._framecache)
		d=self._framecache[i]
		self.display(d[0], d[1])
		
	def previous(self, event=None):
		self.increment(-1)	
	
	def next(self, event=None):
		self.increment(+1)	
			
	def pcolor(self, event):
		try:
			im=self.images[self._current_display[0]]
		except:
			self.report('no image displayed')
			return
		if im.attrib('pseudocolor'):
			im.setAttrib('pseudocolor', None)
		else:
			im.setAttrib('pseudocolor', 'hot')
		self.display(-1)
		
	def setRange(self, event):
		d=self.askParam([{'Name':'Minimum', 'Value':0.0}, {'Name':'Maximum', 'Value':255.0}])
		if not d:
			return
		for i in self.getSelected():
			i.setAttrib('ColorRange', (d[0], d[1]))
		self.display(-1)
			
	def remRange(self, event):	
		for i in self.getSelected():
			i.setAttrib('ColorRange', None)
		self.display(-1)

	def maxRange(self, event):	
		for i in self.getSelected():
			d=i.getData()
			i.setAttrib('ColorRange', (d.min(), d.max()))
		self.display(-1)		
			
	def calibM(self, event):
		im = self.getCurrentImage()
		xmin = 0
		ymin = 0
		xpix = 100
		ypix = 100
		if len(self.measurements)>1:
			m = array(self.measurements)
			xpix = m[:,0].max() - m[:,0].min()
			ypix = m[:,1].max() - m[:,1].min()
			xmin = m[:,0].min()
			ymin = m[:,1].max()
		elif im:
			d = im.getData()
			xpix = d.shape[0]
			ypix = d.shape[1]
			
		d = self.askParam([{"Name":"X Pixels", 
			"Value":xpix},{"Name":"X Distance", 
			"Value":1.0},{"Name":"X Origin", 
			"Value":xmin},{"Name":"Y Pixels", 
			"Value":ypix},{"Name":"Y Distance", 
			"Value":1.0},{"Name":"Y Origin", 
			"Value":ymin}
			])
		if not d:
			return
		xdpp = float(d[1])/d[0]
		ydpp = float(d[4])/d[3]
		xor = d[2]
		yor = d[5]
		self.measureCalib = (xor, xdpp, yor, ydpp)
		self.showMeasure()
		
	def saveMeasure(self, event):
		im = self.getCurrentImage()
		if not self.measurements:
			self.report("No measurements")
			return
		d = self.askParam([{"Name":"file name", "Value":"image_measurements.txt"}])
		if not d:
			return
		f = open(d[0], 'w')
		for m in self.measurements:
			if self.measureCalib:
				xmm = (m[0]-self.measureCalib[0])*self.measureCalib[1]
				ymm = (-m[1]+self.measureCalib[2])*self.measureCalib[3]
				s = "%.5g %.5g" % (xmm, ymm)
			else:
				s= "%i %i" % (m[0], m[1])
			try:
				d=im.getData()[m[0], m[1], :, self._current_display[1]]
				ts = " %G"* len(d)
				d = tuple(d)
				s+= ts % d
			except:
				pass
			s+="\n"
			f.write(s)
		f.close()
		self.report("wrote measurement file")
	
		
	def doMeasure(self, event):
		im = self.getCurrentImage()
		if not im:
			self.report("You must have a displayed image to measure it!")
			return
		x=event.GetX()
		y=event.GetY()
		rx, ry = self.graph.numericalCoordinates((float(x),float(y)))[0,:]
		yh=im.getData().shape[1]
		ry=yh-ry
		self.measurements.append((int(round(rx)), int(round(ry))))
		self.showMeasure()
	
	def showMeasure(self, report=True):
		pl=0
		im = self.getCurrentImage()
		yh=im.getData().shape[1]
		rsl=['Measurements:']
		for i, m in enumerate(self.measurements):
			l="%i" % i	
			y=yh-m[1]
			self.graph.drawTaggedLocation(m[0], yh-m[1], '%i' % i, wx.Colour(128,0,128))
			s = "%i : (%i, %i)" % (i, m[0], m[1])
			if self.measureCalib:
				xmm = (m[0]-self.measureCalib[0])*self.measureCalib[1]
				ymm = (-m[1]+self.measureCalib[2])*self.measureCalib[3]
				s = "%i : (%i:%.4g, %i:%.4g)" % (i, m[0], xmm, m[1], ymm)
			else:
				s = "%i : (%i, %i)" % (i, m[0], m[1])
			if im:
				try:
					d=im.getData()[m[0], m[1], :, self._current_display[1]]
					if len(d)==1:
						s+=" = %G" % (float(d[0]),)
					else:
						s+=" = %s" % (str(list(d)))
				except:
					pass
			if i>0:
				lm=self.measurements[i-1]
				d=sqrt( (m[0] - lm[0])**2+(m[1]-lm[1])**2 )
				s+=" dist: %G" % d
				if pl:
					s+=" path: %G" % (d+pl,)
				pl+=d
			rsl.append(s)
		if report:
			self.report("\n".join(rsl))
		else:
			return rsl
			
	def measureMode(self, event):
		self._inMeasureMode = not self._inMeasureMode
		print self._inMeasureMode
		if self._inMeasureMode:
			self.measurements=[]
			wx.EVT_LEFT_UP(self.graph, lambda x:0)
			wx.EVT_LEFT_DOWN(self.graph, self.doMeasure)
			self.graph.DrawAll()
		else:
			wx.EVT_LEFT_UP(self.graph, self.graph.OnLeftRelease)
			wx.EVT_LEFT_DOWN(self.graph, self.graph.OnLeftClick)
	


	def markInfo(self, event=None):
		rep = "Markers\n"
		last=None
		xlocs=[m['loc'] for m in self.graph.xmarkers]
		xlocs.sort()
		for t in xlocs:
			rep+= "X Mark at %G" % t
			if last:
				rep+=" dx = %G" % (t-last,)
			last=t
		last=None
		ylocs=[m['loc'] for m in self.graph.ymarkers]
		ylocs.sort()
		for t in ylocs:
			rep+= "Y Mark at %G" % t
			if last:
				rep+=" dx = %G" % (t-last,)
			last=t
		self.report(rep)
		