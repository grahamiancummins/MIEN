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
from mien.wx.graphs.colorscales import *
import random, threading, os
from mien.wx.dialogs import askParameters, ColorBrowser
from mien.wx.base import KEYCODES
from mien.tools.identifiers import getPrefFile, loadPrefs, savePrefs
RCMENU = 1000

def getKeyFromCode(i):
	if KEYCODES.has_key(i):
		return KEYCODES[i]
	try:
		c=chr(i)
	except:
		c=i
	return c

def takeList(l, ind):
	if not l:
		return []
	nl = []
	for i in ind:
		nl.append(l[i])
	return nl	

def read_pref_file():
	p = loadPrefs("graphs")
	if p:
		return p
	if p is None:
		print "can't read config file at %s" % (getPrefFile(self.__class__.__name__).name,)
	else:
		print 'no config information'
	return	{}


DEFAULT_CONFIG={"background":(0,0,0), "grid":(100,100,150), "markers":(0,200,250),"Legend":False,"Grid Lines":0,"Grid Labels":False,"Show scale":True,"Lock aspect ratio":None, 'plots':[]}

for c in [(0,240,0), (0,0,240), (240,0,0), (240,240,0), (0,240,240), (240,0,240), (255,255,255)]:
	DEFAULT_CONFIG['plots'].append({'color':c,'dash':wx.SOLID,'width':2})


class Graph(wx.Window):
	def __init__(self,parent,id=-1, **wxOpt):
		wx.Window.__init__(self,parent,id, **wxOpt)
		self.Show(True)
		self.coords = []
		self.bg_color=wx.Colour(0,0,0)
		self.axis={"color":wx.Colour(100,100,150),
				   "font":wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL),
				   "ticks":0,
				   "yscalebar":0,
				   "xscalebar":0,
				   "ticklabels":False,
				   "scale":True}
		self.fixAR=None
		self.twoDzoom=False
		self.legend=True
		self.new_plot_colors=[]
		self.marker_color=(0,200,250)
		self.plots={}
		self.colorscale = None
		self.draw_others=[self.drawMarkers, self.drawCscale, self.drawLegend]
		self.NONSCALINGSTYLES=["FixedImage"]
		self.xmarkers=[]
		self.ymarkers=[]
		def redraw(event):
			'''redraw the screen'''
			self.DrawAll()
		self.pointstyles={
			'circle':(wx.SOLID, self._drawellipse),
			'opencircle':(wx.TRANSPARENT, self._drawellipse),
			'opencircle':(wx.TRANSPARENT, self._drawellipse),
			'square':(wx.SOLID, self._drawSquare),
			'opensquare':(wx.TRANSPARENT, self._drawSquare),
			'plus':(wx.SOLID, self._drawPlus),
			'x':(wx.SOLID, self._drawX),
		}
		self.keybindings = {'a':self.xZoomOut,
				            'A':self.yZoomOut,
				            'q':self.fullScale,
				            'z':self.zoomIn,
				            'x':self.removeXMarker,
				            'X':self.removeYMarker,
				            'k':self.clearMarkers,
				            'r':redraw,
				            'm':self.getMemZoom,
				            'f':self.relocate,
				            'up':self.panUp,
				            'down':self.panDown,
				            'right':self.panRight,
				            'left':self.panLeft}
		self.contextMenuContents = [("Save Configuration",self.saveConfig),
				                    ("Load Configuration",self.loadConfig),
				                    ("Edit Configuration", self.setOptions),
				                    ("Store Zoom Level", self.saveZoom),
				                    ("Cache Full Scale View", self.saveFSV),
				                    ("Set Default Configuration", self.defConfig),
				                    ("Set Line Colors and Dashes",self.setLineType),
				                    ("Printing (black and white) colors", self.printColors),
				                    ("Hide Plots", self.hidePlots),
				                    ("Remove plot",self.uiKillPlot),
				                    ("Bring Plot to Front", self.forground),
				                    ("Save Image", self.dumpFile),
				                    ("Save High Res", self.saveHR),
				                    ("Set Plot Drawng Style", self.setPlotStyle),
				                    ("Set Plot Limits", self.setLimits),
				                    ("Set Plot Attributes", self.setPlotAttr),
				                    ("Scale Plot", self.scalePlot),
				                    ("Autoscale All Plots", self.scaleAuto),
				                    ("Remove ColorBar",self.uiKillCB),
				                    ("Show Key Bindings", self.bindHelp)]
		self.drawingFunctions={"line":self.drawLine,
				               "points":self.drawPoints,
				               "hist":self.drawHist,
				               "yvar":self.drawYVar,
				               "envelope":self.drawEnv,
				               "raster":self.drawRast,
				               "FixedImage":self.drawFixImg,
				               "ScalingImage":self.drawMoveImg}
		self.limits=array([-1.0,1,-1,1])
		self.last_zoom_level = (1.0, 1.0, False)	
		self.full_scale_view = None
		wx.EVT_ENTER_WINDOW(self, self.OnEnter)
		wx.EVT_PAINT(self, self.OnPaint)
		wx.EVT_SIZE(self, self.OnSize)
		wx.EVT_LEFT_UP(self, self.OnLeftRelease)
		wx.EVT_LEFT_DOWN(self, self.OnLeftClick)
		wx.EVT_RIGHT_DOWN(self, self.OnRightClick)
		wx.EVT_CHAR(self, self.OnKey)
		wx.EVT_MIDDLE_UP(self, self.centerView)
		self._newsize=None
		self._dragstart=None
		s = self.GetSizeTuple()
		s=maximum(s, 10)
		self.buffer = wx.EmptyBitmap(s[0],s[1], -1)
		prefs=read_pref_file()
		if prefs.get('default') and prefs.get('configs', {}).get(prefs['default']):
			conf=prefs['configs'][prefs['default']]
		else:
			conf=DEFAULT_CONFIG
		self.applyConfig(conf, False)


	def report(self, s, of=None):
		if of:
			of(s)
		else:
			print s

## -------------------Event Handlers --------------------

	def OnEnter(self, event=None):
		self.SetFocus()
		self._dragstart=None

	def OnKey(self, event):
		c = getKeyFromCode(event.GetKeyCode())
		if self.keybindings.has_key(c):
			self.keybindings[c](event)
		else:
			print  c
			event.Skip()

	def OnWheel(self, event):
		where = event.GetWheelRotation()
		print "hi"
		print where

	def OnAltClick(self, event):
		pass

	def OnLeftClick(self, event):
		if event.AltDown():
			self._dragstart=None
			self.OnAltClick(event)
			return
		self._dragstart=[event.GetX(),event.GetY(),event.ShiftDown()]
		self.drawCrosshair(self._dragstart)

	def OnLeftRelease(self, event):
		loc = [event.GetX(),event.GetY()]
		if self._dragstart==None:
			return 
		if self._dragstart[2]:
			if abs(loc[1]-self._dragstart[1])>5:
				self.dragZoom('y', self._dragstart[1], loc[1])
			else:
				self.addYMarker(event.GetY())
		else:
			if abs(loc[0]-self._dragstart[0])>5:
				self.dragZoom('x', self._dragstart[0], loc[0])
			else:
				self.addXMarker(event.GetX())

	def OnRightClick(self, event):
		rcmenu = wx.Menu()
		for i in range(len(self.contextMenuContents)):
			rcmenu.Append(RCMENU+i, self.contextMenuContents[i][0])
			wx.EVT_MENU(self, RCMENU+i, self.contextMenuContents[i][1])
		self.PopupMenu(rcmenu, event.GetPosition())
		rcmenu.Destroy()

	def GetSizeTuple(self):
		try:
			return (self.buffer.GetWidth(),self.buffer.GetHeight()) 
		except:
			return wx.Window.GetSizeTuple(self)

	def OnSize(self, event):
		s=event.GetSize()
		w=s.GetWidth()
		if self.fixAR:
			h=w/self.fixAR
			if h>s.GetHeight():
				h=s.GetHeight()
				w=h*self.fixAR
		else:
			h=s.GetHeight()
		w=int(w)
		h=int(h)
		#self.SetSize(wx.Size(w, h))
		self.buffer = wx.EmptyBitmap(w, h, -1)
		try:
			self.DrawAll()
		except:
			print "You may need to manually refresh this graph ('r')"

	def OnPaint(self, event):
		dc = wx.PaintDC(self)
		dc.BeginDrawing()
		self.RaiseBuffer(dc)
		dc.EndDrawing()

	def RaiseBuffer(self, dc=None):
		close = 0
		if not dc:
			dc = wx.ClientDC(self)
			dc.BeginDrawing()
		dc.DrawBitmap(self.buffer, 0, 0)
		if close:
			self.closeDC(dc)


## -----------Plot Limit Control ------------------------------

	def xZoomOut(self, event=None):
		'''xZoomOut: Double the range of x coordinates in the viewable area.'''
		r= self.limits[1]-self.limits[0]
		lims=array([self.limits[0]-r/2, self.limits[1]+r/2, self.limits[2], self.limits[3]])
		self.limit(lims)
		self.DrawAll()

	def yZoomOut(self, event=None):
		'''yZoomOut: Double the range of y coordinates in the viewable area.'''
		r= self.limits[3]-self.limits[2]
		lims=array([self.limits[0], self.limits[1], self.limits[2]-r/2, self.limits[3]+r/2])
		self.limit(lims)
		self.DrawAll()

	def dragZoom(self, ax, f, t):
		limits=self.limits.copy()
		if ax=="x":
			f = self.numericalCoordinates((f,0.0))[0,0]
			t = self.numericalCoordinates((t,0.0))[0,0]
			limits[0]=min(f, t)
			limits[1]=max(f, t)
		elif ax=="y":
			f=self.numericalCoordinates((0.0,f))[0,1]
			t=self.numericalCoordinates((0.0,t))[0,1]
			limits[2]=min(f, t)
			limits[3]=max(f, t)
		self.limit(limits)
		self.DrawAll()	

	def zoomIn(self, event=None):
		'''Zoom the viewable region to the region between the last two markers. Operates in both x and y, but will not zoom an axis if there
are fewer than two markers present on that axis.'''
		limits=self.limits.copy()
		action=0
		if len(self.xmarkers)>1:
			action=1
			limits[0]=min(self.xmarkers[-2]["loc"], self.xmarkers[-1]["loc"])
			limits[1]=max(self.xmarkers[-2]["loc"], self.xmarkers[-1]["loc"])
			self.xmarkers=self.xmarkers[:-2]
		if len(self.ymarkers)>1:
			action=1
			limits[2]=min(self.ymarkers[-2]["loc"], self.ymarkers[-1]["loc"])
			limits[3]=max(self.ymarkers[-2]["loc"], self.ymarkers[-1]["loc"])
			self.ymarkers=self.ymarkers[:-2]
		if action:	
			self.limit(limits)
			self.DrawAll()
		else:
			self.QuickZoom(None)

	def	QuickZoom(self, event):
		'''Reduce the viewable limits (zoom in)  by 20% in both x and y'''
		nl = self.limits.copy()
		x = nl[1]-nl[0]
		red = x*.1
		nl[0]+=red
		nl[1]-=red
		y = nl[3]-nl[2]
		red = y*.1
		nl[2]+=red
		nl[3]-=red
		self.limit(nl)
		self.DrawAll()

	def	centerView(self, event):
		x,y  = [float(c) for c in [event.GetX(),event.GetY()]]
		x,y = self.numericalCoordinates((x, y))[0]
		nl = self.limits.copy()
		if self.twoDzoom or not event.ShiftDown():
			xr = .5*(nl[1]-nl[0])
			nl[0] = x-xr
			nl[1] = x+xr
		if self.twoDzoom or event.ShiftDown():
			yr = .5*(nl[3]-nl[2])
			nl[2]= y - yr
			nl[3]= y+yr
		self.limit(nl)
		self.DrawAll()

	def panUp(self, event=None):
		'''Pan viewable area up'''
		fac=2.0
		try:
			if event.ShiftDown():
				fac=10.0
		except:
			pass	
		r= self.limits[3]-self.limits[2]
		lims=[self.limits[0], self.limits[1], self.limits[2]+r/fac, self.limits[3]+r/fac]
		self.limit(array(lims))
		self.DrawAll()

	def panDown(self, event=None):
		'''Pan viewable area down'''
		fac=2.0
		try:
			if event.ShiftDown():
				fac=10.0
		except:
			pass
		r= self.limits[3]-self.limits[2]
		lims=[self.limits[0], self.limits[1], self.limits[2]-r/fac, self.limits[3]-r/fac]
		self.limit(array(lims))
		self.DrawAll()

	def panLeft(self, event=None):
		'''Pan viewable area left'''
		fac=2.0
		try:
			if event.ShiftDown():
				fac=10.0
		except:
			pass
		r= self.limits[1]-self.limits[0]
		lims=[self.limits[0]-r/fac, self.limits[1]-r/fac, self.limits[2], self.limits[3]]
		self.limit(array(lims))
		self.DrawAll()

	def panRight(self, event=None):
		'''Pan viewable area right'''
		fac=2.0
		try:
			if event.ShiftDown():
				fac=10.0
		except:
			pass
		r= self.limits[1]-self.limits[0]
		lims=[self.limits[0]+r/fac, self.limits[1]+r/fac, self.limits[2], self.limits[3]]
		self.limit(array(lims))
		self.DrawAll()

	def getDataRange(self):
		data = array([])
		for p in self.plots.values():
			if p["style"] in self.NONSCALINGSTYLES:
				continue
			if not len(p["data"]):
				continue
			if p.has_key("limits"):
				d = p["limits"]
			else:	
				d = p["data"][:,:2]
			if not len(data):
				data = d
			else:
				data = concatenate([data, d])
		return data


	def getMemZoom(self, event=None):
		'''Set the x zoom level to the last stored zoom level, if there is one '''
		x=self.limits[0]
		y=self.limits[2]
		self.limit(array((x, x+self.last_zoom_level[0], y, y+self.last_zoom_level[1])))
		self.DrawAll()

	def ignorEvent(self, event):
		event.Skip()	

	def relocate(self, event=None):
		'''Store the current zoom level, zoom out to full scale view, and set a mouse binding so the the next left click will center the view on the clicked location and zoom back in to the saved size '''
		self.last_zoom_level = (self.limits[1]-self.limits[0], self.limits[3]-self.limits[2], True)
		self.last_ymin = self.limits[2]
		self.fullScale(True)
		wx.EVT_LEFT_DOWN(self, self.ignorEvent)
		wx.EVT_LEFT_UP(self, self.doRelocate)

	def doRelocate(self, event=None):
		x = self.numericalCoordinates((event.GetX(),0.0))[0,0]
		if event.ShiftDown():
			y=self.numericalCoordinates((0.0,event.GetY()))[0,1]
		else:
			y=self.last_ymin
		self.limit(array((x, x+self.last_zoom_level[0], y, y+self.last_zoom_level[1])))
		self.DrawAll()
		wx.EVT_LEFT_DOWN(self, self.OnLeftClick)
		wx.EVT_LEFT_UP(self, self.OnLeftRelease)

	def fullScale(self, event=None, data=None, pad=40):
		'''Set the limits of the viewable area so as to display all plots'''
		if not self.last_zoom_level[2]:
			self.last_zoom_level = (self.limits[1]-self.limits[0], self.limits[3]-self.limits[2], False)	
		if self.full_scale_view:
			self.limit(self.full_scale_view[0])
			self.buffer=self.full_scale_view[1].ConvertToBitmap()
			self.RaiseBuffer()
			return 
		if data == None:
			data = self.getDataRange()
		if not data.shape[0]:
			return		
		xmin = data[:,0].min()
		xmax = data[:,0].max()
		ymin = data[:,1:].min()
		ymax = data[:,1:].max()
		self.limit(array((xmin, xmax, ymin, ymax), Float32), pad)
		if event:
			self.DrawAll()

	def limit(self, a, pad=None):
		if not self.fixAR:
			self.limits = a.astype(Float32)
		else:
			xc = (a[1]+a[0])/2
			yc = (a[2]+a[3])/2
			eyd = (self.limits[3] - self.limits[2])/2
			exd = (self.limits[1] - self.limits[0])/2
			xd =  (a[1]-a[0])/2
			yd = (a[3]-a[2])/2
			if abs(eyd-yd)>abs(exd-xd):
				xd = yd*self.fixAR
			else:
				yd = xd/self.fixAR
			self.limits=array([xc-xd, xc+xd, yc-yd,yc+yd], Float32)
		if pad:
			xpad = (self.limits[1] - self.limits[0])/pad
			ypad = (self.limits[3] - self.limits[2])/pad
			self.limits = self.limits.astype(Float32)+array([-xpad, +xpad, -ypad, +ypad], Float32)
		if self.limits[0]==self.limits[1]:
			self.limits=self.limits.astype(Float32)+ array([-.01, .01, 0, 0])	
		if self.limits[2]==self.limits[3]:
			self.limits=self.limits.astype(Float32)+array([0, 0, -0.01, .01])

##--------------- Markers --------------------------------------

	def addXMarker(self, loc, color=None):
		if color==None:
			color=self.marker_color
		color = wx.Colour(*color)
		self.xmarkers.append({"loc":self.numericalCoordinates((loc,0.0))[0,0], "color":color})
		self.drawMarkers()

	def addYMarker(self, loc, color=None):
		if color==None:
			color=self.marker_color
		color = wx.Colour(*color)
		self.ymarkers.append({"loc":self.numericalCoordinates((0.0,loc))[0,1], "color":color})
		self.drawMarkers()

	def removeXMarker(self, event=None, index=-1):
		'''delete the most indexed x marker (index defaults to the most recently placed marker - this default is used by GUI "x" events)'''
		try:
			c=self.xmarkers.pop(index)
			self.DrawAll()
		except:
			return

	def removeYMarker(self, event=None, index=-1):
		'''delete the most indexed y marker (index defaults to the most recently placed marker - this default is used by GUI "X" events)'''
		try:
			c=self.ymarkers.pop(index)
			self.DrawAll()
		except:
			return

	def clearMarkers(self, Event=None):
		'''Remove all markers from both axes'''
		self.xmarkers=[]
		self.ymarkers=[]
		self.DrawAll()		


## -------------Coordinates --------------------------------

	def numericalCoordinates(self, a):
		if not type(a)==ArrayType:
			a=array(a)
		if len(a.shape)==1:
			a=array([a])
		if a.shape[1]!=2:
			a=a[:,:2]	
		size = array(self.GetSizeTuple())	
		size = resize(size, a.shape)
		lims =  resize(array([self.limits[0], self.limits[3]]), a.shape)
		wts = resize(array([self.limits[1]-self.limits[0], self.limits[2]-self.limits[3]]), a.shape)
		return lims+(wts*(a/size))

	def graphCoords(self, x):
		'''x (array) => array
convert an Nx2 array of numerical coordinates to graph coordinates'''
		if not type(x)==ArrayType:
			x=array(x)
		if len(x.shape)==1:
			x=array([x])
		if x.shape[1]!=2:
			x=x[:,:2]
		w, h = self.GetSizeTuple()
		xs=float(w)/(self.limits[1]-self.limits[0])
		ys=float(h)/(self.limits[2]-self.limits[3])
		lims = resize(take(self.limits, (0,2)), (x.shape[0], 2))
		scales = resize(array((xs,ys)), (x.shape[0], 2))
		x = (x-lims)*scales
		x[:,1] += ones(x.shape[0])*float(h)
		x = roundtoint(x)
		return x

	def graphDist(self, a):
		if not type(a)==ArrayType:
			a=array(a)
		w, h = self.GetSizeTuple()
		xscale=float(w)/(self.limits[1]-self.limits[0])
		yscale=float(h)/(self.limits[3]-self.limits[2])
		return roundtoint(transpose(array([a*xscale, a*yscale])))


	def inWindow(self, x, rmask=False):
		'''x(float array) => array)'''
		try:
			lowlims = resize(take(self.limits, (0,2)), (x.shape[0], 2))
			uplims = resize(take(self.limits, (1,3)), (x.shape[0], 2))
			mask=nonzero1d(alltrue((x>lowlims)*(x<uplims), 1))
		except:
			return zeros(0)
		if rmask:
			return mask
		else:
			new=take(x, mask, 0)
			return new

	def reduceSamples(self, x, mask=False):
		'''x(int array) => array'''
		unique=concatenate([[[1,1]], x[1:]-x[:-1]])
		unique=nonzero1d(sometrue(unique, 1))
		if mask:
			return unique
		else:
			new=take(x, unique, 0)
			return new

## ------------ Drawing --------------------------------

	def sortPlots(self, k1, k2):
		if self.plots[k1].has_key("order"):
			if  self.plots[k2].has_key("order"):
				return -1*cmp(self.plots[k1]["order"],self.plots[k2]["order"])
			else:
				return 1
		elif self.plots[k2].has_key("order"):
			return -1
		else:
			return -1*cmp(k1, k2)

	def plotOrder(self):
		keys = self.plots.keys()
		keys.sort(self.sortPlots)
		return keys

	def closeDC(self, dc):
		dc.EndDrawing()
		self.RaiseBuffer()
		if wx.Platform == "__WXMSW__":
			self.Refresh()

	def DrawAll(self, dc=None):
		size = array(self.GetSizeTuple())
		if not any(size):
			return
		close=0
		if not dc:
			dc = wx.MemoryDC()
			dc.SelectObject(self.buffer)
			close = 1
		dc.BeginDrawing()
		dc.SetBackground(wx.Brush(self.bg_color, wx.SOLID))
		dc.Clear()
		self.drawAxis(dc)
		for i in self.plotOrder():
			self.Draw(i, dc)
		for f in self.draw_others:
			f(dc)
		if close:
			self.closeDC(dc)


	def drawCscale(self, dc=None):
		if not self.colorscale:
			return
		colors = self.colorscale['colors']
		close=0
		if not dc:
			dc = wx.MemoryDC()
			dc.SelectObject(self.buffer)
			dc.BeginDrawing()
			close=1
		w,h=self.GetSizeTuple()
		tick=h/len(colors)
		loc=h-tick
		step=((h-tick)-(h/2))/len(colors)
		dc.SetTextBackground(self.bg_color)
		dc.SetFont(self.axis["font"])
		dc.SetTextForeground(wx.Colour(0,200,250))
		s = dc.GetTextExtent(self.colorscale['range'][0])
		dc.DrawText(self.colorscale['range'][0],w-tick-s[0], loc)
		s = dc.GetTextExtent(self.colorscale['range'][1])
		dc.DrawText(self.colorscale['range'][1],w-tick-s[0], loc-len(colors)*step-s[1])

		for i in range(len(colors)):
			dc.SetPen(wx.Pen(colors[i], tick))
			dc.DrawLine(w-int(tick/2), loc-step*i, w-int(tick/2), loc-step*(i+1))
		if close:
			self.closeDC(dc)

	def drawAxis(self, dc=None):
		close = None
		if not dc:
			dc = wx.MemoryDC()
			dc.SelectObject(self.buffer)
			dc.BeginDrawing()
			close=1
		if self.axis['ticklabels'] or self.axis['scale'] or self.axis['xscalebar'] or self.axis['yscalebar']:
			dc.SetFont(self.axis["font"])
			dc.SetTextBackground(self.bg_color)
			dc.SetTextForeground(self.axis['color'])
		if self.axis["ticks"]:
			if not self.axis["scale"]:
				ytop = 0
			else:
				ytop = self.GetTextExtent("W")[1]
			w,h=self.GetSizeTuple()
			tick=int(h/20.0)
			space=(h-2*tick)/self.axis["ticks"]
			loc=space
			dc.SetFont(self.axis["font"])
			dc.SetTextBackground(self.bg_color)
			dc.SetPen(wx.Pen(self.axis["color"], 1))
			dc.SetTextForeground(self.axis['color'])
			while loc<h:
				dc.DrawLine(0, loc, w, loc)
				if self.axis['ticklabels']:
					dc.DrawText("%.2f" % self.numericalCoordinates((0.0,loc))[0,1], tick/2, loc+4)
				loc+=space
			loc=space
			while loc<w:
				dc.DrawLine(loc, ytop, loc, h)
				if self.axis['ticklabels']:
					dc.DrawText("%.2f" % self.numericalCoordinates((loc, 0.0))[0,0], loc+4, tick/2)
				loc+=space
		if self.axis["scale"]:
			if self.axis["ticks"]:
				zero = self.numericalCoordinates((0.0,0.0))[0]
				one = self.numericalCoordinates((space,0.0))[0,0]
				xspace = one-zero[0]
				one = self.numericalCoordinates((0.0, space))[0,1]
				yspace = one-zero[1]
				stext = "x:%.2g, to % .2g (%.2g/div), y:%.2g to %.2g (%.2g/div)" % (self.limits[0],
								                                                    self.limits[1],
								                                                    xspace,
								                                                    self.limits[2],
								                                                    self.limits[3],
								                                                    yspace)
			else:
				stext = "x:%.2g to % .2g, y:%.2g to %.2g" % tuple(self.limits)



			#dc.SetPen(wx.Pen(self.bg_color, 1))
			#dc.SetBrush(wx.Brush(wx.Colour(128,128,128), wx.SOLID))
			#tw, th = self.GetTextExtent(stext)
			#dc.DrawRectangle(0, 0, tick+tw, th+3)
			dc.DrawText(stext, 0, 0)
		if self.axis['xscalebar']:
			w,h=self.GetSizeTuple()
			pixlength = int(round((w*self.axis['xscalebar']/100.0)))
			reallength = (self.limits[1]-self.limits[0])*self.axis['xscalebar']/100.0
			lab = "%.2g" % reallength
			tw, th = self.GetTextExtent(lab)
			yoff = int( h /30.0)
			xoff = int( w /30.0)
			dc.SetBrush(wx.Brush(self.bg_color, wx.SOLID))
			dc.SetPen(wx.Pen(self.bg_color, 1))
			dc.DrawRectangle(w-xoff-tw-5, h-yoff-th-2, tw+5, th+2)
			dc.DrawText(lab, w-xoff-tw-2, h-yoff-th-1)
			dc.SetPen(wx.Pen(self.axis["color"], 4))
			dc.DrawLine(w-xoff-tw-7 - yoff - pixlength , h-yoff-int ((th+2)/2.0), w-xoff-tw-7 - yoff, h-yoff-int ((th+3)/2.0))			
		if self.axis['yscalebar']:
			w,h=self.GetSizeTuple()
			pixlength = int(round((h*self.axis['xscalebar']/100.0)))
			reallength = (self.limits[3]-self.limits[2])*self.axis['xscalebar']/100.0
			lab = "%.2g" % reallength
			tw, th = self.GetTextExtent(lab)
			yoff = int( h /30.0)
			xoff = int( w /30.0)
			dc.SetBrush(wx.Brush(self.bg_color, wx.SOLID))
			dc.SetPen(wx.Pen(self.bg_color, 1))
			dc.DrawRectangle(w-xoff-tw, yoff+int(pixlength/2.0), tw+5, th+2)
			dc.DrawText(lab, w-xoff-tw+2, yoff++int(pixlength/2.0)+1)
			dc.SetPen(wx.Pen(self.axis["color"], 4))
			dc.DrawLine(w-xoff-tw-4 , yoff, w-xoff-tw-4, yoff+pixlength)	
			pass

		if close:
			self.closeDC(dc)

	def drawCrosshair(self, loc, col=None, dc=None):
		close=False
		if not dc:
			dc = wx.MemoryDC()
			dc.SelectObject(self.buffer)
			dc.BeginDrawing()
			close=1
		if col==None:
			col = wx.Colour(220,220,0)
		dc.SetPen(wx.Pen(col, 1))
		w,h=self.GetSizeTuple()
		if type(loc[2])==str:
			self.drawTaggedLocation(loc[0], loc[1], loc[2], col, True, dc)
		elif loc[2]==2:
			dc.CrossHair(loc[0], loc[1])
		elif loc[2]:
			dc.DrawLine(0, loc[1], w, loc[1])
		else:
			dc.DrawLine(loc[0], 0, loc[0], h)
		if close:
			self.closeDC(dc)			

	def drawTaggedLocation(self, x, y, t, color=None, pixel=False, dc=None):
		close=False
		if not dc:
			dc = wx.MemoryDC()
			dc.SelectObject(self.buffer)
			dc.BeginDrawing()
			close=1
		if not pixel:
			x,y=self.graphCoords((x, y))[0,:]	
		w,h=self.GetSizeTuple()
		tick=h/20
		dc.SetFont(self.axis["font"])
		# dc.SetTextBackground(self.bg_color)
		# dc.SetBrush(wx.Brush(self.bg_color, wx.SOLID))
		dc.SetPen(wx.Pen(color, 1))
		#print x, y, tick
		dc.DrawLine(x-tick, y, x+tick, y)
		dc.DrawLine(x, y-tick, x, y+tick)
		dc.SetTextForeground(color)
		tw, th = self.GetTextExtent(t)
		#dc.DrawRectangle(x+2, y+2, tw+5, th+3)
		dc.DrawText(t, x+4, y+4)
		if close:
			self.closeDC(dc)			


	def drawMarkers(self, dc=None):
		close=False
		if not dc:
			dc = wx.MemoryDC()
			dc.SelectObject(self.buffer)
			dc.BeginDrawing()
			close=1
		w,h=self.GetSizeTuple()
		tick=h/20
		dc.SetTextBackground(self.bg_color)
		dc.SetFont(self.axis["font"])
		labely = (tick/3, h - (tick/3 + self.GetTextExtent("W")[1]))
		whichside = 0
		dc.SetBrush(wx.Brush(self.bg_color, wx.SOLID))
		for i in self.xmarkers:
			x,y=self.graphCoords((i["loc"], 0.0))[0,:]
			dc.SetPen(wx.Pen(i['color'], 1))
			dc.DrawLine(x, 0, x, h)
			dc.SetTextForeground(i['color'])
			lab = "%.5g " % i['loc']
			tw, th = self.GetTextExtent(lab)
			dc.DrawRectangle(x+2, labely[whichside], tw+5, th+3)
			dc.DrawText(lab, x+4, labely[whichside])
			whichside= not whichside
		whichside = 0
		for i in self.ymarkers:
			x,y=self.graphCoords((0.0, i["loc"]))[0,:]
			dc.SetPen(wx.Pen(i['color'], 1))
			dc.DrawLine(0, y, w, y)
			dc.SetTextForeground(i['color'])
			lab = "%.5g " % i['loc']
			tw, th = self.GetTextExtent(lab)
			dc.DrawRectangle(tick/3-2, y+2, tw+4, th+5)
			dc.DrawText(lab,tick/3 , y+4)
			whichside= not whichside
		if close:
			self.closeDC(dc)			

	def drawLegend(self, dc=None):
		if not self.legend:
			return
		close=False
		if not dc:
			dc = wx.MemoryDC()
			dc.SelectObject(self.buffer)
			dc.BeginDrawing()
			close=1
		dc.SetFont(self.axis["font"])
		dc.SetTextBackground(self.bg_color)
		w,h=self.GetSizeTuple()
		tick=max(h/40, 4)
		ly = 5
		plots=self.plotOrder()
		plots.reverse()
		bgpen = wx.Pen(self.bg_color, 1)
		bgbrush = wx.Brush(self.bg_color, wx.SOLID)
		mtw=tick
		tth = 0
		for name in plots:	
			if 'namelist' in self.plots[name]:
				nl = self.plots[name]['namelist']
			else:
				nl = [name]
			for n in nl:
				tw, th = self.GetTextExtent(n)
				mtw = max(mtw, tw)
				tth+=th+4						
		dc.SetPen(bgpen)
		dc.SetBrush(bgbrush)
		dc.DrawRectangle(w-(mtw+2*tick+3), ly, w-tick, tth)
		for name in plots:
			pl = self.plots[name]
			if 'namelist' in pl:
				nl = pl['namelist']
			else:
				nl = [name]
			c = self.plots[name]['color']
			if type(c)!=list:
				c=[c]*len(nl)
			if 'dashStyle' in pl:
				dl = pl['dashStyle']
			else:
				dl = wx.SOLID
			if type(dl)!=list:
				dl = [dl]*len(nl)
			for i, n in enumerate(nl):
				dc.SetTextForeground(c[i])
				tw, th = self.GetTextExtent(n)
				dc.SetPen(wx.Pen(c[i], 1, dl[i]))
				lh = ly + int(round(th/2.0))			
				dc.DrawLine(w - (mtw+2*tick), lh, w - (tw+tick+3), lh)
				dc.DrawText(n, w-(tw+tick), ly)
				ly += th+4
		if close:
			self.closeDC(dc)			



	def Draw(self, name, dc=None):
		if  self.plots[name].get('hidden'):
			return
		try:
			style=self.plots[name]['style']
			df=self.drawingFunctions[style]
		except:
			self.report("can't draw plot %s" % name)
			self.report("%s not one of %s" % (self.plots[name].get("style"), str(self.drawingFunctions.keys())))
			return	
		close = None
		data = self.plots[name].get("data")
		if data == None or len(data)<1:
			return
		if not dc:
			dc = wx.MemoryDC()
			dc.SelectObject(self.buffer)
			dc.BeginDrawing()
			close=1
		df(name, data, dc)	
		if close:
			self.closeDC(dc)

	def drawLine(self, name, data, dc):
		if not len(data)>1:
			return	
		data = self.inWindow(data)
		if not len(data)>1:
			return
		points = self.graphCoords(data)
		points = self.reduceSamples(points)
		ds=self.plots[name].get("dashStyle", wx.SOLID)
		dc.SetPen(wx.Pen(self.plots[name]['color'],self.plots[name]['width'], style=ds))
		dc.DrawLines(points)

	def drawYVar(self, name, data, dc):
		data = self.plots[name].get("data")
		if not len(data)>1:
			return
		mean = data[:,:2].copy()
		top = data[:,:2].copy()
		bot = data[:,:2].copy()
		top[:,1]=top[:,1]+data[:,2]
		bot[:,1]=bot[:,1]-data[:,2]
		dc.SetPen(wx.Pen(self.plots[name]['color'],self.plots[name]['width']))
		for d in [bot, mean, top]:
			d = self.inWindow(d)
			if not len(d)>2:
				continue
			points = self.graphCoords(d)
			points = self.reduceSamples(points)
			dc.DrawLines(points)

	def drawEnv(self, name, data, dc):
		if not len(data)>1:
			return
		mask=nonzero1d((data[:,0]>self.limits[0])*(data[:,0]<self.limits[1]))
		x=take(data, mask)
		envpts = self.plots[name].get("envpts", int(self.GetSizeTuple()[0]/2.0))
		samples = divmod(x.shape[0], envpts)[0]
		if samples<=2:
			self.drawLine(name, data, dc)
			return
		envpts = int(x.shape[0]/samples)
		x=x[:envpts*samples]
		y = reshape(x[:,1], (envpts, -1))
		x = reshape(x[:,0], (envpts, -1))
		x = sum(x, 1)/x.shape[1]
		ymax = maximum.reduce(y, 1)
		ymin = minimum.reduce(y, 1)
		upper = self.graphCoords(transpose(concatenate([[x], [ymax]])))
		lower = self.graphCoords(transpose(concatenate([[x], [ymin]])))
		dc.SetPen(wx.Pen(self.plots[name]['color'],self.plots[name]['width']))
		dc.DrawLines(upper)
		dc.DrawLines(lower)

	def drawRast(self, name, data, dc):
		data=take(data, nonzero1d(data[:,1]))
		y = self.plots[name].get("y", 0.0)
		data[:,1]=ones(data[:,1].shape,data.dtype.char)*y
		self.drawPoints(name, data, dc)

	def _drawellipse(self, dc, data, width, pen, brush):
		ellipse = concatenate([data-.5*width, ones(data.shape)*width], 1)
		dc.DrawEllipseList(ellipse, pen, brush)			

	def _drawPlus(self, dc, data, width, pen, brush):
		xm=ones(data.shape)*.5
		xm[:,1]=0
		ym=ones(data.shape)*.5
		ym[:,0]=0
		hor = concatenate([data-xm*width, data+xm*width], 1)
		dc.DrawLineList(hor, pen)	
		ver = concatenate([data-ym*width, data+ym*width], 1)
		dc.DrawLineList(ver, pen)

	def _drawX(self, dc, data, width, pen, brush):
		xm=ones(data.shape)*.5
		hor = concatenate([data-xm*width, data+xm*width], 1)
		xm[:,1]*=-1
		dc.DrawLineList(hor, pen)	
		ver = concatenate([data-xm*width, data+xm*width], 1)
		dc.DrawLineList(ver, pen)	

	def _drawSquare(self, dc, data, width, pen, brush):
		data = concatenate([data-.5*width, ones(data.shape)*width], 1)
		dc.DrawRectangleList(data, pen, brush)	

	def drawPoints(self, name, data, dc):
		if self.plots[name].has_key("Labels"):
			labels = self.plots[name]["Labels"]
		else:
			labels = []
		if self.plots[name].get("colorlist"):
			colors = self.plots[name]["colorlist"]
		else:
			colors = []
		mask = self.inWindow(data, True)
		if not len(mask):
			return
		data = take(data, mask, 0)
		labels = takeList(labels, mask)
		colors = takeList(colors, mask)
		data = self.graphCoords(data)
		if len(data)>50:
			mask = self.reduceSamples(data, True)
			data = take(data, mask, 0)
			labels = takeList(labels, mask)
			colors = takeList(colors, mask)
		color = self.plots[name]['color']		
		pointstyle=self.plots[name].get("symbolStyle", 'circle')
		brushtype, dfunction=self.pointstyles[pointstyle]
		if colors:
			color = colors[-1]
			pen = map(lambda x:wx.Pen(x, 1), colors)
			brush = map(lambda x:wx.Brush(x, brushtype), colors)
		else:
			pen=wx.Pen(color,1)
			brush = wx.Brush(color, brushtype)		
		if self.plots[name]['width']==1 and self.plots[name].get('widthlist')==None:
			dc.DrawPointList(data, pen)
		else:
			if self.plots[name].get('widthlist')!=None:
				w=array(self.plots[name]['widthlist'])[:,newaxis]
			else:
				w=self.plots[name]['width']	
			dfunction(dc, data, w, pen, brush)
		if labels:
			dc.SetFont(self.axis["font"])
			dc.SetTextBackground(self.bg_color)
			dc.SetTextForeground(color)
			dc.DrawTextList(labels, data+self.plots[name]['width'])

	def drawHist(self, name, x, dc):
		if not len(x)>1:
			return	
		rbw=self.plots[name].get('binwidth')
		if not rbw:
			rbw=x[0,1]-x[0,0]
		w, h = self.GetSizeTuple()
		xscale=float(w)/(self.limits[1]-self.limits[0])	
		bw=int(round(xscale*rbw))
		off=self.plots[name].get('offset',0)	
		data = self.inWindow(x)
		if not len(data)>1:
			return	
		z=zeros_like(data)
		z[:,1]=off
		top=data+z
		z[:,0]=data[:,0]
		top=self.graphCoords(top)
		z=self.graphCoords(z)
		dc.SetPen(wx.Pen(self.plots[name]['color'],1))
		dc.SetBrush(wx.Brush(self.plots[name]['color'], wx.SOLID))
		for i in range(z.shape[0]):
			if self.plots[name].get('dashes'):
				dc.DrawLine(z[i,0], z[i,1], z[i,0]+bw, z[i,1])
				if z[i,1]!=top[i, 1]:
					dc.DrawLine(top[i,0], top[i,1], top[i,0]+bw, top[i,1])
			else:
				if z[i,1]==top[i, 1]:
					dc.DrawLine(z[i,0], z[i,1], z[i,0]+bw, z[i,1])
				else:
					dc.DrawRectangle(z[i,0], z[i,1], bw, top[i,1]-z[i,1])	
		self.plots[name]['limits']=array([[min(x[:,0]),off-1], [max(x[:,0])+rbw,max(x[:,1])+off+1]])

	def drawFixImg(self,name,a,dc):
		w,h =self.GetSizeTuple()
		img=array_to_image(a, self.plots[name].get("colorrange"), self.plots[name].get('pcolor'), wx)
		bbox=self.plots[name].get('boundingbox') or [0, 0, w, h]
		img.Rescale(bbox[2]-bbox[0], bbox[3]-bbox[1])	
		img=wx.BitmapFromImage(img)
		dc.DrawBitmap(img, bbox[0], bbox[1])

	def drawMoveImg(self, name, x, dc):
		w,h =self.GetSizeTuple()
		wscale=float(w)/(self.limits[1]-self.limits[0])
		hscale=float(h)/(self.limits[3]-self.limits[2])
		bbox=[0, 0, w, h]
		if not self.plots[name].has_key("limits"):
			self.plots[name]['limits']=array([[0.0,0.0],[x.shape[0],x.shape[1]]])
		lims=self.plots[name]['limits']
		he=lims[1,0]-lims[0,0]
		hppi=x.shape[0]/he
		hmi=self.limits[0]-lims[0,0]
		if hmi<0:
			bbox[0]=int(abs(hmi)*wscale)
		elif hmi>0:
			if hmi>=he:
				return	
			xsi=int(hmi*hppi)
			x=x[xsi:,:]
		hma=self.limits[1]-lims[1,0]	
		if hma>0:
			bbox[2]-=int(wscale*hma)
			if bbox[2]<bbox[0]+1:
				return
		elif hma<0:
			xpi=int(round(hma*hppi))
			if abs(xpi)>=x.shape[0]-1:
				return 
			x=x[:xpi,:]
		ve=lims[1,1]-lims[0,1]
		vppi=x.shape[1]/ve
		vmi=self.limits[2]-lims[0,1]
		if vmi<0:
			bbox[3]-=int(abs(vmi)*hscale)
			if bbox[3]<=1:
				return
		elif vmi>0:
			ysi=int(abs(vmi)*vppi)
			if ysi>=x.shape[1]-1:
				return
			x=x[:,:-ysi]
		vma=self.limits[3]-lims[1,1]
		if vma>0:
			bbox[1]=int(vma*hscale)
			if bbox[3]<=bbox[1]+1:
				return
		elif vma<0:
			ypi=int(vma*vppi)
			if ypi>=x.shape[1]-1:
				return
			x=x[:,-ypi:]
		self.plots[name]['boundingbox']=bbox 
		self.drawFixImg(name, x, dc)	


## ------------------ Making/Controling plots --------------		

	def killAll(self):
		self.plots={}
		self.DrawAll()


	def kill(self, name):
		del(self.plots[name])
		self.DrawAll()	


	def clear(self, plot):
		self.plots[plot]['data']=None
		self.DrawAll()


	def nextcolor(self, n=None):
		colors=self.new_plot_colors
		if type(colors)==type(wx.Colour(0,0,0)):
			if n:
				return [(colors, wx.SOLID)]*n
			else:
				return (colors, wx.SOLID)
		used=[]
		for c in self.plots.values():
			co=c.get("color")
			ds=c.get('dashStyle')
			if type(co)==list:
				if type(ds)!=list:
					ds=[ds]*len(co)
				used.extend(zip(co, ds))
			else:
				used.append((co, ds))
		i=0
		cl=[]
		itn=n or 1
		for j in range(itn):
			#print j, i, len(colors)
			if i<len(colors):
				c, d=colors[i]	
				i+=1
			else:
				c=wx.Colour(int(random.uniform(30,220)), int(random.uniform(30,220)),int(random.uniform(20,220)))
				d=wx.SOLID
			while (c,d) in used:
				if i<len(colors):
					c, d=colors[i]
					i+=1
				else:
					c=wx.Colour(int(random.uniform(30,220)), int(random.uniform(30,220)),int(random.uniform(20,220)))
			used.append((c,d))
			cl.append((c,d))
		if not n:
			return cl[0]
		else:	
			return cl


	def addPlot(self, data=None, name="plot", sampr=1.0, **opts):
		'''data (Array or False), name(str="plot"),
		sampr(float=1.0), opts (dict={}) => str
generates a new plot. if data is false, this plot will be
dynamic (see addpoint). Otherwise, it will be a plot of an array
that has sequential samples in rows (first index), and x,y data in columns.
Alternately, data may be a vector, and sampr will specify the uniform
period between data samples in this vector. Options are:
		style (str): "points", "line", "hist" : plot style
		[default: "line"] 
		color (str): a Tk color string. If a 3Tuple is specified
		it will be automatically converted to a color string.
				 [default: choose the next unused "reasonable" color]
		width (int): Width of a line, or diameter of a point, in pixels
		["default:2]
		hidden (bool)
		name (str)
		order (int)

return value is the key into self.plots that references the new plot.
if "name" is not already used by another plot, it will be the key.
If it is used, a unique suffix will be added.
'''
		options ={'width':2,
				  'style':'line',
				  'nodraw':False}
		options['order']=len(self.plots.keys())
		options.update(opts)
		if data == None:
			data = array([])
		else:
			if len(data.shape)==1 and sampr:
				x=arange(len(data)).astype(data.dtype.char)*sampr
				data=transpose(array([x, data]))
		if not options.get('color'):
			options["color"], options["dashStyle"]=self.nextcolor()
		else:
			color = options['color']
			if type(color)==type(' '):
				color=wx.NamedColor(color)
			elif type(color)==type(wx.Colour(0,0,0)):
				pass
			else:
				color=apply(wx.Colour, color)
			options["color"]=color	
		index=1
		basename=name
		while  self.plots.has_key(name):
			index+=1
			name = "%s_%i" % (basename, index)
		options["data"]=data
		self.plots[name] = options
		return name


	def set_color(self, name, a, cs='hot', r=None):
		'''name(str), a(array), cs(str="hot"), r(2tuple=None)'''
		if len(a)<1:
			return
		if cs == "fade":
			self.plots[name]['colorlist'] = gradecolor(self.plots[name]['color'], a, r)
		else:										  
			self.plots[name]['colorlist']=colorscale(a, cs, r)
		self.Draw(name)

	def addCscale(self, a, cs='hot', r=None):	
		self.colorscale={}
		sample = arange(min(a), max(a), (max(a)-min(a))/20.0)
		self.colorscale['colors']=colorscale(sample, cs, r)
		self.colorscale['range']=[str(min(a)), str(max(a))]
		self.drawCscale()	

	def addpoint(self, name, p, plot=1):
		if not type(p)==ArrayType:
			p=array(p)
		if len(p.shape)==1:
			p = array([p])
		if not self.plots[name]['data']:
			self.plots[name]['data'] = p
		else:
			self.plots[name]['data'] = concatenate([self.plots[name]['data'], p])
		if plot:
			if self.plots[name]['data'].shape[0]>1:
				change = abs(self.plots[name]['data'][-2]-self.plots[name]['data'][-2])
				d =  self.graphDist(change)
				if d[0,0]==0.0 and d[1,1]==0.0:
					return		
			cx,cy = self.graphCoords(p)[0]
			w=self.plots[name]['width']
			dc = wx.ClientDC(self)
			dc.BeginDrawing()
			dc.SetPen(wx.Pen(self.plots[name]['color'],self.plots[name]['width']))
			dc.SetBrush(wx.Brush(self.plots[name]['color'], wx.SOLID))		   
			self.DrawEllipse(cx-w,cy-w, cx+w, cy+w)
			dc.EndDrawing()




## --------------- Context Menu Functions -------------------

	def printColors(self, event=None):
		self.bg_color=wx.Colour(255,255,255)
		self.axis["color"]=wx.Colour(0,0,0)
		for m in self.xmarkers+self.ymarkers:
			m["color"]=wx.Colour(128,128,128)
		for p in self.plots.values():
			if type(p["color"])==list:
				p['color']=[wx.Colour(0,0,0)]*len(p['color'])
			else:
				p["color"]=wx.Colour(0,0,0)
			p["colorlist"]=[]
		self.DrawAll()	

	def setPlotStyle(self, event=None):

		l=askParameters(self, [{"Name":"Plot",
				                "Type":"List",
				                "Value":self.plotOrder()},
				               {"Name":"Style",
				                "Type":"List",
				                "Value":self.drawingFunctions.keys()}])
		if not l:
			return
		c = self.plots[l[0]]['color']
		self.plots[l[0]]['color']=self.bg_color
		self.Draw(l[0])
		self.plots[l[0]]['style']=l[1]
		self.plots[l[0]]['color']=c
		self.Draw(l[0])


	def expandCompoundPlots(self):
		k=self.plotOrder()
		pt=[]
		pd={}
		for key in k:
			if type(self.plots[key]['color'])==list:
				for j in range(len(self.plots[key]['color'])):
					n="%s.%i" % (key, j)
					pt.append(n)
					pd[n]=(self.plots[key], j)
			else:
				pt.append(key)
		return (pt, pd)

	def setLineType(self, event=None):
		pt, pd = self.expandCompoundPlots()
		ls={"Solid":wx.SOLID,
			"dot":wx.DOT,
			"long dash":wx.LONG_DASH,
			"short dash":wx.SHORT_DASH,
			"dot dash":wx.DOT_DASH}
		l=askParameters(self, [{"Name":"Plot",
				                "Type":"Select",
				                "Value":pt},
				               {"Name":"Color",
				                "Type":tuple,
				                "Value":(0,0,0),
				                "Browser":ColorBrowser},
				               {"Name":"Width",
				                "Value":2},
				               {"Name":"Line Style",
				                "Type":"List",
				                "Value":ls.keys()}])

		if not l:
			return

		pns=l[0]			
		for pn in pns:
			if pd.has_key(pn):
				p, j = pd[pn]
				p["dashStyle"][j]=ls[l[3]]
				p["color"][j]=apply(wx.Colour, l[1])
				p["width"]=l[2]
			else:
				self.plots[pn]["dashStyle"]=ls[l[3]]
				self.plots[pn]["color"]=apply(wx.Colour, l[1])
				self.plots[pn]["width"]=l[2]
		if pns:
			self.DrawAll()

	def saveConfig(self, event=None, name=None):

		d=read_pref_file()
		gcd=d.get('configs', {})
		if not name:
			l=askParameters(self, [{"Name":"Configuration Name",
						            "Type":"Prompt",
						            "Value":gcd.keys()}])
			if not l:
				return
			name=l[0]
		gopts={"background":self.bg_color.Get(), "grid":self.axis["color"].Get(), "markers":self.marker_color,"Legend":self.legend,"Grid Lines":self.axis["ticks"],"Grid Labels":self.axis['ticklabels'],"Show scale":self.axis['scale'],"Lock aspect ratio":self.fixAR, 'plots':[]}
		for k in self.plotOrder():
			p=self.plots[k]
			if type(p['color'])==list:
				l=len(p['color'])
				ds=p.get('dashStyle', [None]*l)
				for j in range(l):
					ps={'color':p['color'][j].Get(),'dash':ds[j], 'width':p.get('width',1)}
					gopts['plots'].append(ps)
				pass
			else:
				ps={'color':p['color'].Get(),'dash':p.get('dashStyle'),'width':p.get('width',1)}
				gopts['plots'].append(ps)

		gcd[name]=gopts
		d['configs']=gcd
		savePrefs("graphs", d)	

	def applyConfig(self, conf, draw=True):
		self.bg_color=apply(wx.Colour, conf['background'])
		self.axis["color"]=apply(wx.Colour, conf['grid'])
		self.marker_color=conf['markers']
		mc=apply(wx.Colour, conf['markers'])
		for m in self.xmarkers+self.ymarkers:
			m["color"]=mc
		self.legend=conf["Legend"]
		self.axis["ticks"]=conf["Grid Lines"]
		self.axis['ticklabels']=conf["Grid Labels"]
		self.axis['scale']=conf["Show scale"]
		self.fixAR=conf["Lock aspect ratio"]
		self.new_plot_colors=[(apply(wx.Colour, c['color']), c['dash']) for c in conf['plots']]
		pt, pd = self.expandCompoundPlots()
		for i,k in enumerate(pt):
			if i>=len(conf['plots']):
				break
			if not pd.has_key(k):
				self.plots[k]['color']=apply(wx.Colour, conf['plots'][i]['color'])	
				self.plots[k]['width']=conf['plots'][i]['width']
				if conf['plots'][i]['dash']:
					self.plots[k]['dashStyle']=conf['plots'][i]['dash']
			else:
				p, j =pd[k]
				p['color'][j]=apply(wx.Colour, conf['plots'][i]['color'])	
				p['width']=conf['plots'][i]['width']
				if conf['plots'][i]['dash']:
					if not p.get('dashStyle'):
						p['dashStyle']=[wx.SOLID]*len(p['color'])
					p['dashStyle'][j]=conf['plots'][i]['dash']	
		if draw:
			self.DrawAll()


	def loadConfig(self, event=None, name=None):
		d=read_pref_file()
		gcd=d.get('configs', {})
		gcd['default']=DEFAULT_CONFIG
		if not name:
			l=askParameters(self, [{"Name":"Configuration Name",
						            "Type":"List",
						            "Value":gcd.keys()}])
			if not l:
				return
			conf=gcd[l[0]]
		else:
			if not gcd.has_key(name):
				return
			conf=gcd['name']
		self.applyConfig(conf)


	def defConfig(self, event=None):
		d=read_pref_file()
		gcd=d.get('configs', {})
		gcd['default']=DEFAULT_CONFIG
		l=askParameters(self, [{"Name":"Configuration Name",
				                "Type":"List",
				                "Value":gcd.keys()}])
		if not l:
			return
		conf=gcd[l[0]]
		d['default']=l[0]
		savePrefs("graphs", d)
		self.applyConfig(conf)

	def uiKillPlot(self, event=None):
		l=askParameters(self, [{"Name":"Remove Plot",
				                "Type":"List",
				                "Value":self.plotOrder()}])
		if not l:
			return
		self.kill(l[0])

	def uiKillCB(self, event=None):
		self.colorscale={}
		self.DrawAll()

	def setPlotAttr(self, event=None):

		l=askParameters(self, [{"Name":"Plot",
				                "Type":"List",
				                "Value":['All Plots']+self.plotOrder()}])

		if not l:
			return
		pn = l[0]
		if pn == 'All Plots':
			d=askParameters(self, [{"Name":"Attribute",
						            "Value":""},
						           {"Name":"Value",
						            "Value":""}])
			if not d:
				return
			val=eval(d[1])
			if type(val)==int:
				val = float(val)	
			for p in self.plots.values():
				p[d[0]]=val
			self.DrawAll()
			return
		plots = [pn]
		p = self.plots[pn]
		d = []
		attr_names = []
		for k in p:
			if type(p[k]) in SIMPLE_TYPES:
				attr_names.append(k)
				d.append({"Name":k,
						  "Value":p[k]})
		d.append({"Name":"New",
				  "Value":"Name:Value"})
		l=askParameters(self, d)
		if not l:
			return
		for pn in plots:
			n = l[-1]
			if not n.startswith("Name:Value"):
				name, val  = n.split(":")
				try:
					val = eval(val)
					if type(val)==type(1):
						val = float(val)
				except:
					pass
				self.plots[pn][name]=val
			for i, a  in enumerate(attr_names):
				self.plots[pn][a] = l[i]
		self.DrawAll()

	def scalePlot(self, event=None):
		l=askParameters(self, [{"Name":"Plot",
				                "Type":"List",
				                "Value":self.plotOrder()},
				               {"Name":"Offset",
				                "Value":0.0},
				               {"Name":"Scale",
				                "Value":1.0}])

		if not l:
			return
		dat = self.plots[l[0]]['data'][:,1]
		dat = dat*l[2]+l[1]
		self.plots[l[0]]['data'][:,1]= dat
		self.DrawAll()

	def scaleAuto(self, event=None):
		d = self.plotOrder()[0]
		d = self.plots[d]['data']
		ma = max(d[:,1])
		mi = min(d[:,1])
		me = sum(d[:,1])/d.shape[0]
		div = ((ma-me)+(me-mi))/2.0
		for p in self.plotOrder()[1:]:
			d = self.plots[p]['data'][:,1]
			pma = max(d)
			pmi = min(d)
			pme = sum(d)/d.shape[0]
			pdiv = ((pma-pme)+(pme-pmi))/2.0
			off = me - pme
			if pdiv==0:
				sca =1
			else:
				sca = div/pdiv
			d = d*sca+off
			self.plots[p]['data'][:,1]=d
		self.DrawAll()

	def hidePlots(self, event=None):
		l=askParameters(self, [{"Name":"Hide Which Plots",
				                "Type":"Select",
				                "Value":self.plots.keys()}]
				        )
		if not l:
			return
		for k in self.plots.keys():
			if k in l[0]:
				self.plots[k]["hidden"]=True
			else:
				self.plots[k]["hidden"]=False
		self.DrawAll()

	def forground(self, event=None, plot=None):
		if not plot:
			l=askParameters(self, [{"Name":"Which Plot",
						            "Type":"List",
						            "Value":self.plots.keys()}]
						    )
			if not l:
				return
			plot=l[0]
		if not self.plots[plot].has_key("order"):
			self.plots[plot]["order"]=1
		for k in self.plots.keys():
			if self.plots[k].has_key("order") and self.plots[k]["order"]<=self.plots[plot]["order"]:
				self.plots[k]["order"]+=1
		self.plots[plot]["order"]=0
		self.DrawAll()

	def saveZoom(self, event=None):
		self.last_zoom_level = (self.limits[1]-self.limits[0], self.limits[3]-self.limits[2], True)	
		self.report('cached zoom level %s' % (str(self.last_zoom_level),))		

	def saveFSV(self, event=None):
		if self.full_scale_view:
			self.full_scale_view = None
			self.report('cleared cached view')
		else:
			self.full_scale_view = (self.limits.copy(), self.buffer.ConvertToImage())
			self.report('cached view. Note that you will have to clear this cache manually if you resize or change the data!')


	def dumpFile(self, event=None, fname=None):
		if not fname:
			dlg=wx.FileDialog(self, message="Select file name", style=wx.SAVE)
			if dlg.ShowModal() == wx.ID_OK:
				fname=dlg.GetPath()
			else:
				return
		formats={
			'.bmp':wx.BITMAP_TYPE_BMP,
			'.jpg':wx.BITMAP_TYPE_JPEG,
			'.png':wx.BITMAP_TYPE_PNG,
			'.tif':wx.BITMAP_TYPE_TIF}
		fn, e= os.path.splitext(fname)
		if not formats.has_key(e):
			f=wx.BITMAP_TYPE_PNG
			fname=fname+'.png'
		else:
			f=formats[e]
		i=self.buffer.ConvertToImage()
		self.buffer.SaveFile(fname, f)


	def saveHR(self, event=None):
		par = askParameters(self,  [{'Name':'fname', 'Value':'HRimage.tif'},
				                    {'Name':'resolution (horizontal)', 'Value':2000}])
		if not par:
			return
		buf = self.buffer
		w, h = self.GetSizeTuple()
		ar = float(h)/w
		nw = par[1]
		nh=int(ar*nw)
		nb = wx.EmptyBitmap(nw, nh, -1)		
		self.buffer = nb
		self.DrawAll()
		self.buffer=buf
		fn=par[0]
		if not fn.endswith('.tif'):
			fn=fn+'.tif'
		nb.SaveFile(fn,wx.BITMAP_TYPE_TIF)




	def setLimits(self, event=None):
		l = askParameters(self, [{"Name":"X Min",
				                  "Value":float(self.limits[0])},
				                 {"Name":"X Max",
				                  "Value":float(self.limits[1])},
				                 {"Name":"Y Min",
				                  "Value":float(self.limits[2])},
				                 {"Name":"Y Max",
				                  "Value":float(self.limits[3])}])
		if not l:
			return
		self.limit(array(l))
		self.DrawAll()

	def setOptions(self, event=None):		
		l = askParameters(self, [{"Name":"Show Legend",
				                  "Type":"List",
				                  "Value":["Yes", "No"]},
				                 {"Name":"Number of grid lines",
				                  "Value":self.axis["ticks"]},
				                 {"Name":"Show grid line labels",
				                  "Type":"List",
				                  "Value":["No", "Yes"]},
				                 {"Name":"Show scale",
				                  "Type":"List",
				                  "Value":["Yes", "No"]},
				                 {"Name":"Lock aspect ratio",
				                  "Type":"List",
				                  "Value":["No", "Yes"]},
				                 {"Name":"Background Color",
				                  "Value":self.bg_color.Get(),
				                  "Browser":ColorBrowser},
				                 {"Name":"Grid Color",
				                  "Value":self.axis["color"].Get(),
				                  "Browser":ColorBrowser},
				                 {"Name":"Marker Color",
				                  "Value":self.marker_color,
				                  "Browser":ColorBrowser},
				                 {"Name":"X scale bar",
				                  "Value":self.axis["xscalebar"]},
				                 {"Name":"Y scale bar",
				                  "Value":self.axis["yscalebar"]},
				                 ])
		if not l:
			return
		if l[0]=="Yes":
			self.legend=True
		else:
			self.legend=None
		self.axis["ticks"]=l[1]
		if l[2]=="Yes":
			self.axis['ticklabels']=True
		else:
			self.axis['ticklabels']=False
		if l[3]=="Yes":
			self.axis['scale']=True
		else:
			self.axis['scale']=False
		if l[4]=="Yes":
			self.fixAR = float(self.limits[3]-self.limits[2])/(self.limits[1]-self.limits[0])
		else:
			self.fixAR=None
		self.axis["xscalebar"]=l[8]
		self.axis["yscalebar"]=l[9]
		self.bg_color=wx.Colour(*l[5])
		self.axis["color"]=wx.Colour(*l[6])
		self.marker_color=l[7]
		for m in self.xmarkers+self.ymarkers:
			m["color"]=wx.Colour(*l[7])
		self.DrawAll()	

	def bindHelp(self, event=None):
		s='Left Click: Add X Marker\Shift Left: Add Y Marker\nMiddle Click: Center view\nRight Click: Context Menu\n--------------------\n'
		for k in self.keybindings.keys():
			s+="%s   => %s\n--------------------\n" % (k, self.keybindings[k].__doc__)
		if not event:
			return s
		self.report(s)
		dlg = wx.MessageDialog(self, s, 'Help Text', wx.OK)
		dlg.CenterOnParent()
		dlg.Show()


def quickgraph():
	app = wx.PySimpleApp()
	bar = {'size':(600,600), 'style':wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE}
	frame = wx.Frame(None, -1, "Output Graph", **bar)
	frame.g = Graph(frame, -1)
	frame.Show(True)
	frame.g.DrawAll()
	t = threading.Thread(target=app.MainLoop)
	t.start()
	return frame.g	

if __name__=='__main__':
	from mien.math.sigtools import uniform
	app = wx.PySimpleApp()
	bar = {'size':(600,600), 'style':wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE}
	frame = wx.Frame(None, -1, "Output Graph", **bar)
	frame.g = Graph(frame, -1)
	#frame.g.fixAR=1.0
	frame.Show(True)
	#frame.g.addPlot(uniform(0,1, 700), style="line")
	#n1=frame.g.addPlot(array([[1.0,4], [1,0], [2,4], [6,1]]), style="points", width=5, Labels = ["foo", "bar", "baz", "spam"], widthlist=arange(5,9))
	from numpy import random
	a=random.uniform(0, 1000, (10,10))
	a[:,0]=0

	import mien.parsers.fileIO as io
	d=io.read('/Users/gic/sync/fibr/bozemanpassDEM.mdat') # 960, 1360
	a=d.elements[-1].getData()
	a=a[:, arange(a.shape[1]-1, -1, -1)]
	a-=a.min()
	a/=(a.max()/255)
	a=256-a
	a=a[:, arange(a.shape[1]-1, -1, -1)]	
	n2=frame.g.addPlot(a, style="ScalingImage")
	#frame.g.set_color(n1, array([1,2,4,6]), cs = 'fade', r=(0,7)) 
	#frame.g.set_color(n2, array([1,2,4,6]), cs = 'hot', r=(0,7)) 
	#frame.g.addPlot(a, style="hist")
	#frame.g.addPlot(array([[1.0,-1, 1], [2,2,4], [3,2,1], [4,0,3]]), style="yvar")
	#frame.g.addPlot(a, style="ScalingImage")
	#frame.g.limit(array([0,150,0,100]))
	frame.g.DrawAll()


	frame.g.fullScale()
	frame.g.DrawAll()
	app.MainLoop()