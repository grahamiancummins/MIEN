
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
from mien.wx.graphs.graph import *
from numpy.random import randint


def makeRaster(evts, bin):
	'''1D array, float => 1D array'''
	evts = evts - evts.min()
	t = arange(0, evts.max()+bin, bin)
	rast = zeros(t.shape[0], t.dtype.char)
	if evts.shape[0]>t.shape[0]:
		#print "method 1"
		for i in range(t.shape[0]-1):
			#print t[i], t[i+1], where(logical_and(evts>= t[i], evts<t[i+1]), 1,0).sum()
			rast[i] = where(logical_and(evts>= t[i], evts<t[i+1]), 1,0).sum()
	else:
		evts = (evts/bin).astype(Int32)
		for i in range( evts.shape[0]):
			rast[evts[i]]+=1
	return rast



class GraphFSR(Graph):
	def __init__(self,parent, id=-1, **wxOpt):
		Graph.__init__(self, parent, id, **wxOpt)
		self.fs = 1.0
		self.drawingFunctions={"line":self.drawLine,
				               "points":self.drawPoints,
				               "raster":self.drawRast,
				               "hist":self.drawHist,
				               "bars":self.drawBars,
				               "envelope":self.drawEnv,
				               "polyline":self.drawPoly,
				               "evts":self.drawEvtMarks,
				               "image":self.drawImage}
		self.keybindings['Z']=self.xZoomInCentered
		self.axis['ticks']=0
		self.__cache={}
		self.linked_graphs=[]
		self._update_link=False


	def xZoomInCentered(self, event):
		r= self.limits[1]-self.limits[0]
		lims=array([self.limits[0]+r/4, self.limits[1]-r/4, self.limits[2], self.limits[3]])
		self.limit(lims)
		self.DrawAll()

	def ycoords(self, a):
		h = self.GetSizeTuple()[1]
		ys=float(h)/(self.limits[3]-self.limits[2])
		a = (a - self.limits[2])*ys
		a = around(a).astype(Int16)
		a = where(a>0, a, 0) 
		a = where(a<h, a, h)
		a = h-a
		return a

	def xcoords(self, n, start, stop):
		x = linspace(start, stop, n)*self.GetSizeTuple()[0]
		x = around(x).astype(Int16)
		return x

	def getDataRange(self):
		data = None
		for p in self.plots.values():
			if p.get('cached_range')!=None:
				ran=p['cached_range']
			else:	
				if p['style']=='evts':
					continue
				if p['style']=='raster':
					xmin=p['start']+p['data'][:,0].min()/self.fs
					xmax=p['start']+p['data'][:,0].max()/self.fs
				else:	
					xmin = p['start']
					xmax = xmin  + (p['data'].shape[0]-1)/float(self.fs)
				if p['style']=='polyline':
					ymin, ymax=p["data"].min(), p["data"].max()
					offsets=p.get('offsets')
					if offsets!=None:
						s=max(offsets[:,1])
						ymin*=s
						ymax*=s
						ymin+=min(offsets[:,0])
						ymax+=max(offsets[:,0])
				elif  p['style']=='hist':
					ymin=p.get('offset',0.0)
					bin=p.get('binwidth', 1)
					xmin-=bin
					xmax+=.1*bin
					dat=p['data']
					if type(bin)==float:
						bin=min(round(bin*self.fs), 1)
					if bin==1:
						ymax=dat.max()
					else:
						rem=dat.shape[0]%bin
						if rem:
							dat=dat[:-rem]
						dat=sum(reshape(dat, (-1, bin)), 1)
						ymax=dat.max()
				else:
					if p.has_key('offset'):
						ymin=p["offset"]
					else:
						ymin=p['data'].min()
					if p.has_key('height'):
						ymax= ymin+p["height"]
					else:
						ymax= p["data"].max()
				ran = array([[xmin, ymin],[xmax, ymax]])
				p['cached_range']=ran
			if data == None:
				data = ran
			else:
				data = concatenate([data, ran])
		if data == None:
			data = array([[0,0],[1,1]])
		return data

	def limit(self, a, pad=None, link=True):
		self.limits = a.astype(Float32)
		if pad:
			ypad = (self.limits[3] - self.limits[2])/pad
			self.limits = self.limits.astype(Float32)+array([0, 0, -ypad, +ypad], Float32)
		if self.limits[0]==self.limits[1]:
			self.limits[1]+=.01
		if self.limits[2]==self.limits[3]:
			self.limits[3]+=.01
			self.limits[2]-=.01
		if link:
			self._update_link=True
			for g in self.linked_graphs[:]:
				try:
					l=g.limits[:]
					l[:2]=self.limits[:2]
					g.limit(l, pad, link=False)
				except wx._core.PyDeadObjectError:
					print "removing graph link"
					self.linked_graphs.remove(g)
				except:
					print "failed linked graph limit"
					pass

	def DrawAll(self, dc=None, link=True):
		Graph.DrawAll(self, dc)
		if link and self._update_link and not dc:
			for g in self.linked_graphs[:]:
				try:
					g.DrawAll(None, link=False)
				except wx._core.PyDeadObjectError:
					print "removing graph link"
					self.linked_graphs.remove(g)
				except:
					print "failed linked graph redraw"
					pass
		self._update_link=False			

	def inWindow(self, name):
		grange = self.limits[1]-self.limits[0]
		dat  = self.plots[name]['data']
		st = self.plots[name]['start']
		end = st + (dat.shape[0]-1)*(1.0/self.fs)
		start = 0.0
		stop = 1.0
		if st>self.limits[1] or end<self.limits[0]:
			return (zeros((0, 1)), 0.0, 1.0)
		if st>self.limits[0]:
			start = (st - self.limits[0])/grange
		elif st<self.limits[0]:
			adj = (self.limits[0] - st)*self.fs
			sti = int(adj)
			sl = adj % 1
			start = -sl/(grange*self.fs)
			if sti:
				dat = dat[sti:]
		if end < self.limits[1]:
			stop = 	(end - self.limits[0])/grange
		elif end > self.limits[1]:
			adj = (end - self.limits[1])*self.fs
			sti = int(adj)
			sl = (adj % 1)
			stop = 1.0 + (sl/(grange*self.fs))
			if sti:
				dat = dat[:-sti]
		return (dat, start, stop)

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
			x=i['loc']
			if x<self.limits[0] or x>self.limits[1]:
				continue
			x-=self.limits[0]
			x=x/(self.limits[1]-self.limits[0])
			x=int(round(x*w))
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

	def Draw(self, name, dc=None):
		#import time; st = time.time()
		if  self.plots[name].get('hidden'):
			return
		try:
			style=self.plots[name]['style']
			df=self.drawingFunctions[style]
		except KeyError:
			self.report("plot %s has unknown style" % name)
			return
		if not style in ['raster','evts']:
			data, start, stop = self.inWindow(name)
			if data.shape[0]<1:
				return
		close = None
		if not dc:
			dc = wx.MemoryDC()
			dc.SelectObject(self.buffer)
			dc.BeginDrawing()
			close = True
		if style in['raster','evts']:
			df(name, dc)
		elif style in ['image', "polyline"]:
			df(name, data, start, stop, dc)
		else:	
			for i in range(data.shape[1]):
				df(name, data[:,i], start, stop, dc)
		if close:
			self.closeDC(dc)
		#print time.time() - st

	def drawSimple(self, name, data,start, stop, dc):
		if data.shape[0] > 4*self.GetSizeTuple()[0]/self.plots[name]['width']:
			return False
		data = self.ycoords(data)
		x = self.xcoords(data.shape[0], start, stop)
		ds=self.plots[name].get("dashStyle", wx.SOLID)
		c = self.plots[name]['color']
		if type(c) == list:
			c = c[0]
		dc.SetPen(wx.Pen(c,self.plots[name]['width'], style=ds))
		points = concatenate([x[:,NewAxis], data[:,NewAxis]],1)
		dc.DrawLines(points)
		return True

	def drawLine(self, name, data,start, stop, dc):
		if self.drawSimple(name, data,start, stop, dc):
			return
		w = self.GetSizeTuple()[0]*(stop - start)
		n = int(w/float(self.plots[name]['width']))
		if n==0:
			return
		x = arange(n) * (data.shape[0]/float(n))
		x = around(x).astype(Int32)
		data = self.ycoords(take(data, x))
		x = self.xcoords(data.shape[0],start, stop)
		ds=self.plots[name].get("dashStyle", wx.SOLID)
		c = self.plots[name]['color']
		if type(c) ==list:
			c = c[0]
		dc.SetPen(wx.Pen(c,self.plots[name]['width'], style=ds))
		points = concatenate([x[:,NewAxis], data[:,NewAxis]],1)
		dc.DrawLines(points)

	def drawEnv(self, name, data, start, stop, dc):
		if self.drawSimple(name, data, start, stop, dc):
			return		
		w,h =self.GetSizeTuple()
		bbox=[int(round(start*w)), 0, int(round(stop*w)), h]
		npix=bbox[2]-bbox[0]
		if npix<2:
			self.report("plot %s is too small to draw at this zoom level" % name)
			return
		ppp = floor(data.shape[0]/npix)
		clip=data.shape[0]%ppp
		if clip:
			npts = ppp-clip
			data = concatenate([data, ones(npts)*data[-1]])
		clip=data.shape[0]%npix
		data=reshape(data, (-1, ppp))
		if not data.shape[0]>1:
			return
		ymax = self.ycoords(maximum.reduce(data, 1))
		data = self.ycoords(minimum.reduce(data, 1))
		x = self.xcoords(data.shape[0], start, stop)
		ds=self.plots[name].get("dashStyle", wx.SOLID)
		c = self.plots[name]['color']
		if type(c) == list:
			c = c[0]
		dc.SetPen(wx.Pen(c,self.plots[name]['width'], style=ds))
		dc.DrawLines(concatenate([x[:,NewAxis], ymax[:,NewAxis]],1))
		dc.DrawLines(concatenate([x[:,NewAxis], data[:,NewAxis]],1))

	def drawBars(self, name, data, start, stop, dc):
		pass

	def drawPoints(self, name, data, start, stop, dc):
		w,h =self.GetSizeTuple()
		datmin = False
		if len(data)>w*3:
			bbox=[int(round(start*w)), 0, int(round(stop*w)), h]
			npix=bbox[2]-bbox[0]
			clip=data.shape[0]%npix
			if clip:
				q=int(clip/2)
				data=data[clip-q:-q]
				pspp=1.0/(self.fs*(self.limits[1]-self.limits[0]))
				start+=(clip-q)*pspp
				stop-=(q)*pspp
			data=reshape(data, (npix, -1))
			datmin = data.min(1)
			data = data.max(1)
			x = self.xcoords(data.shape[0], start, stop)
			data = self.ycoords(data)
			datmin = self.ycoords(datmin)
			c = self.plots[name]['color']
			if type(c) == list:
				c = c[0]
			dc.SetPen(wx.Pen(c,1))
			data = concatenate([x[:,NewAxis], data[:,NewAxis], x[:,NewAxis], datmin[:,NewAxis],],1)
			dc.DrawLineList(data)
		else:
			x = self.xcoords(data.shape[0], start, stop)
			data = self.ycoords(data)
			data = concatenate([x[:,NewAxis], data[:,NewAxis]],1)
			c = self.plots[name]['color']
			if type(c) == list:
				c = c[0]
			dc.SetPen(wx.Pen(c,1))
			dc.SetBrush(wx.Brush(c, wx.SOLID))
			if self.plots[name]['width']==1:
				dc.DrawPointList(data)
			else:
				ellipse = concatenate([data, ones(data.shape)*self.plots[name]['width']], 1)
				dc.DrawEllipseList(ellipse)	

	def drawImage(self,name,data, start, stop, dc):
		w,h =self.GetSizeTuple()
		off=self.plots[name].get('offset', None)
		bbox=None
		if off!=None:
			hei=self.plots[name].get('height', None)
			if hei:
				off+=hei
				ymin=self.limits[2]
				ymax=self.limits[3]
				yh=h/(ymax-ymin)
				ys=int(round(yh*(ymax-off)))
				yt=ys+round(yh*hei)
				#print ymin, ymax, off, hei, ys, yt
				bbox=[int(round(start*w)), ys, int(round(stop*w)), yt]			
		if bbox==None:	
			bbox=[int(round(start*w)), 0, int(round(stop*w)), h]
		if data.shape[0]>20000:
			skip=int(floor(data.shape[0]/float(w)))
			data=data.take(arange(0, data.shape[0], skip), 0)
		if not self.plots[name].get('rawbytes'):
# 			if data.shape[0]>20000:
# 				#attempt to avoid a segv
# 				ndat=zeros((bbox[2]-bbox[0], data.shape[1]), data.dtype)
# 				for ind in range(data.shape[1]):
# 					c=self.foldSamples(name, data[:,ind], 1.0, ndat.shape[0])
# 					ndat[:,ind]=mean(c, 1)
# 				data=ndat
			if self.plots[name].has_key("colorrange"):
				if self.plots[name]['colorrange']=="global":
					if self.plots[name].get('datarange'):
						minval, maxval=self.plots[name]['datarange']
					else:	
						minval= self.plots[name]["data"].min()
						maxval= self.plots[name]["data"].max()
						self.plots[name]['datarange']=(minval, maxval)
				elif self.plots[name]['colorrange']=="local":
					minval=data.min()
					maxval=data.max()
				else:	
					minval = self.plots[name]['colorrange'][0]
					maxval = self.plots[name]['colorrange'][1]
				if minval==maxval:
					data=ones((data.shape[0],data.shape[1], 3))
					data=data*128
				else:	
					data=data-minval
					data=255*data.astype('f')/(maxval-minval)
			mav=ones(data.shape, data.dtype)*255
			a=where(data>255, mav, data)
			miv=zeros(data.shape, data.dtype)
			a=where(a<0, miv, a)
			a=a.astype('b')
		else:
			a=data
		#print bbox, a.shape
		if len(a.shape)==2:
			a=concatenate([a[:,:,NewAxis],a[:,:,NewAxis],a[:,:,NewAxis]],2)
		img=wx.EmptyImage(a.shape[0], a.shape[1])
		a=transpose(a, (1,0,2))	
		img.SetData(a.tostring())
		try:
			img.Rescale(bbox[2]-bbox[0], bbox[3]-bbox[1])	
			img=wx.BitmapFromImage(img)
			dc.DrawBitmap(img, bbox[0], bbox[1])
		except:
			self.report("warning: can't resize image")

	def drawPoly(self,name,data, start, stop, dc):
		w,h =self.GetSizeTuple()
		bbox=[int(round(start*w)), 0, int(round(stop*w)), h]
		npix=bbox[2]-bbox[0]
		colors=self.plots[name]['color']
		if not type(colors) == list:
			colors = [colors]
		ds=self.plots[name].get("dashStyle", [wx.SOLID])
		offsets=self.plots[name].get('offsets')
		if len(colors)==1 and data.shape[1]>1:
			colors=[colors[0] for i in range(data.shape[1])]
			self.plots[name]['color']=colors
		if len(ds)==1 and data.shape[1]>1:
			ds=[ds[0] for i in range(data.shape[1])]
			self.plots[name]['dashStyle']=ds
		lwid=self.plots[name]['width']
		mins=None
		if data.shape[0]>4*npix:
			if self.plots[name].get('fastdraw'):
				skip=int(floor(data.shape[0]/float(2*npix)))
				data=data.take(arange(0, data.shape[0]+1, skip), 0)
			else:
				if npix<2:
					print "data range is too small to display at this resolution"
					return
				ppp = floor(data.shape[0]/npix)
				clip=data.shape[0]%ppp
				if clip:
					npts = ppp-clip
					data = row_stack([data, resize(data[-1,:], (npts, data.shape[1]))])
				data=reshape(data, (-1, ppp, data.shape[1]))
				mins=minimum.reduce(data, 1)
				data=maximum.reduce(data, 1)
		x= self.xcoords(data.shape[0], start, stop)
		for dat in [data, mins]:
			if dat==None:
				continue
			for i in range(dat.shape[1]):

				cd = dat[:,i]
				if offsets!=None:	
					if offsets[i][1]!=1:
						cd=cd*offsets[i][1]
					if offsets[i][0]!=0:
						cd=cd+offsets[i][0]
				cd=cd-self.limits[2]
				h = self.GetSizeTuple()[1]
				ys=float(h)/(self.limits[3]-self.limits[2])
				cd = around(cd*ys).astype(Int16)
				cd = maximum(cd, 0) 
				cd = minimum(cd, h)
				cd = h-cd
				dc.SetPen(wx.Pen(colors[i],lwid, style=ds[i]))
				cd = concatenate([x[:,NewAxis], cd[:,NewAxis]],1)
				dc.DrawLines(cd)

	def mapColorValues(self, data, mode='random'):
		d={}
		ids=unique(data)
		if mode=='random':
			cvs=randint(50, 256, (ids.shape[0],3))
			for i in range(ids.shape[0]):
				d[ids[i]]=apply(wx.Colour, cvs[i,:])
		elif mode=='frequency':
			fr=histogram(data, ids.max()+1-ids.min() , [ids.min(), ids.max()+1], True)
			cs=colorscale(fr[:,1], 'hot', [0, fr[:,1].max()])
			#print ids.shape, len(cs)
			for i in range(ids.shape[0]):
				d[ids[i]]=cs[i]		
		elif mode=='value':
			cs=colorscale(ids.max()-ids, 'hot', [-1,ids.max()])
			#print ids.shape, len(cs)
			for i in range(ids.shape[0]):
				d[ids[i]]=cs[i]		
		elif mode=='periodic':
			iv=divmod(ids, 21)[1]
			colors=[(0,255,0), (0,0,255), (255,0,0), (255,255,0), (0,255,255), (255,0,255), (255,255,255), (0,200,0), (0,0,200), (200,0,0), (200,200,0), (0,200,200), (200,0,200), (200,200,200), (0,100,0), (0,0,100), (100,0,0), (100,100,0), (0,100,100), (100,0,100), (100,100,100)]
			colors=map(lambda x:apply(wx.Colour, x), colors)
			for i in range(ids.shape[0]):
				ci=colors[iv[i]]
				d[ids[i]]=ci
		return d	

	def drawRast(self, name, dc):
		data=self.plots[name]['data']
		if not data.shape[0]:
			return
		if not self.plots[name].has_key('height'):
			self.plots[name]['height']=1.0
		w,h=self.GetSizeTuple()
		off=self.plots[name].get("offset", 0.0)
		height= self.plots[name]['height']
		if off+height<self.limits[2]:
			return
		off=(off-self.limits[2])*(h/(self.limits[3]-self.limits[2]))
		if off>h:
			return
		off=round(h-off)
		st=self.plots[name].get('start', 0.0)
		fsi = (self.limits[0]-st)*self.fs
		lsi = (self.limits[1]-st)*self.fs
		mask=nonzero1d(logical_and(data[:,0]>fsi, data[:,0]<lsi))
		if not mask.shape[0]:
			return		
		pixpersample = w/((self.limits[1]-self.limits[0])*self.fs )
		wid=self.plots[name].get('width', 1)
		ys=float(h)/(self.limits[3]-self.limits[2])
		height=round(height*ys)
		elist=[]
		colors=[]
		if data.shape[1]==1:
			indexes = data[mask,0]
			indexes = indexes - fsi
			elist.append(indexes)
		else:
			indexes = data[mask,0]
			indexes = indexes - fsi
			ids=data[mask,1]
			if data.shape[1]>2:
				cvs=take(data[:,2], mask)
			if not self.plots[name].has_key('n_units'):
				self.plots[name]['n_units']=data[:,1].max()+1
			for id in range(self.plots[name]['n_units']):
				these=nonzero1d(ids==id)
				elist.append(take(indexes, these))
				if data.shape[1]>2:
					colors.append(take(cvs, these))
		if colors:
			if not self.plots[name].get('colortable'):
				self.plots[name]['colortable']=self.mapColorValues(data[:,2], self.plots[name].get('colormode', 'random'))
			ct=	self.plots[name]['colortable']
			for i in range(len(colors)):
				colors[i]=[ct[j] for j in colors[i]]
		space=self.plots[name].get("spacing", None)	
		if space==None:
			space=2*wid
		c = self.plots[name]['color']
		if type(c) == list:
			c = c[0]
		if wid*len(elist)+space*2*(len(elist)-2)<height:
			#use lines
			lh=height-2*wid*(len(elist))
			lh=round(float(lh)/len(elist))
			dc.SetPen(wx.Pen(c,wid))
			pens=None
			ysp = off-height
			for ind, ea in enumerate(elist):
				if ea.shape[0]==0:
					continue
				if ysp>h or (ysp+lh)<0:
					continue
				thisy=int(round(off-height+height*float(ind)/len(elist)))	
				nexty=int(round(off-space-height+height*float(ind+1)/len(elist)))	
				cols=round(ea*pixpersample)
				if colors:
					pens=[wx.Pen(c, wid) for c in colors[ind]]
					cols=reshape(cols, (-1, 1))					
				else:	
					cols=reshape(unique(cols), (-1, 1))					
				rows=ones(cols.shape, cols.dtype)*thisy
				rows2=ones(cols.shape, cols.dtype)*nexty
				lines=concatenate([cols, rows2, cols, rows], 1)
				dc.DrawLineList(lines, pens)
				ysp=ysp+lh+2*wid
		else:
			#use dots
			dc.SetPen(wx.Pen(c,1))
			dc.SetBrush(wx.Brush(c, wx.SOLID))
			brushes=None
			pens=None
			ysp = off-height
			for ind, ea in enumerate(elist):
				if ea.shape[0]==0:
					continue
				decr=round( height*((float(ind)+1.0)/len(elist)))
				rows=ysp+decr
				if rows<0 or rows>h:
					continue
				cols=round(ea*pixpersample)
				if colors:
					#print len(colors[ind]), 
					pens=[wx.Pen(c, 1) for c in colors[ind]]
					brushes=[wx.Brush(c, wx.SOLID) for c in colors[ind]]
					cols=reshape(cols, (-1, 1))					
				else:	
					cols=reshape(unique(cols), (-1, 1))
				rows=ones(cols.shape, cols.dtype)*rows
				rads=ones(cols.shape, cols.dtype)*wid
				ellipse = concatenate([cols, rows,rads, rads], 1)
				dc.DrawEllipseList(ellipse, pens, brushes)	

	def drawEvtMarks(self, name, dc):
		data=self.plots[name]['data']
		if not data.shape[0]:
			return
		w,h=self.GetSizeTuple()
		st=self.plots[name].get('start', 0.0)
		spc=self.fs*((self.limits[1]-self.limits[0])/w)
		lei=round((self.limits[0]-st)*self.fs)
		wis=round(spc*w)
		indexes=data[:,0]-lei
		mask=nonzero1d(logical_and(indexes>0, indexes<wis))
		if not mask.shape[0]:
			return	
		xcoord=take(indexes, mask)
		xcoord=round(xcoord/spc)
		xcoord=reshape(xcoord, (-1,1))
		top=zeros_like(xcoord)
		bot=ones_like(xcoord)*h
		c = self.plots[name]['color']
		if type(c) ==list:
			c = c[0]
		dc.SetPen(wx.Pen(c,1))
		lines=concatenate([xcoord, bot, xcoord, top], 1)
		dc.DrawLineList(lines)

	def drawHist(self, name, data, start, stop, dc):
		bin=self.plots[name].get('binwidth', 1)
		if type(bin)==float:
			bin=round(bin*self.fs)
		if bin!=1:
			rem=data.shape[0]%bin
			if rem:
				data=data[:-rem]
			data=sum(reshape(data, (-1, bin)), 1)	
		gw, gh =self.GetSizeTuple()
		cps=gw/(self.limits[1]-self.limits[0])
		cpb=round((bin/self.fs)*cps)
		start=round(start*gw)
		xcoords=start+arange(data.shape[0])*cpb
		scale= self.plots[name].get('scale', 1.0)
		off=self.plots[name].get("offset", 0.0)
		data=data*scale
		self.plots[name]['Range']= [off-scale, data.max()+off]
		data = round(data*(gh/(self.limits[3]-self.limits[2])))
		c = self.plots[name]['color']
		if type(c) ==list:
			c = c[0]
		dc.SetPen(wx.Pen(c,1))
		dc.SetBrush(wx.Brush(c, wx.SOLID))
		y0 = self.ycoords(zeros(1)+off)[0]
		ind=nonzero1d(data)
		data=reshape(take(data, ind), (-1, 1))
		xcoords=reshape(take(xcoords, ind), (-1, 1))
		y0=ones_like(data)*y0
		w=ones_like(xcoords)*cpb
		rect=concatenate([xcoords, y0, w, -data], 1)
		dc.DrawRectangleList(rect)

	def addPlot(self, data=None, name="plot", **opts):
		'''data (Array), name, options => str
generates a new plot. Array should be 1D or 2D in columns. 2D data will
automatically be plotted as many plots in the same color and style.
All samples are interpretted as having a uniform sample rate
(in Hz) equal to self.fs

Options are:
		start (float): The x value at the begining of the array (default 0.0)
		style (str): key into self.drawingFunctions [default "line"]
		color (str): a 3Tuple. [default: choose the next unused "reasonable" color]
		width (int): Width of a line, or diameter of a point, in pixels
		["default:2]
		hidden (bool) : Dont draw the plot (default False => do draw)
		order (int) : Order in which to draw the plot
		bin (int) : Width over which to calculate hist and envelope

return value is the key into self.plots that references the new plot.
if "name" is not already used by another plot, it will be the key.
If it is used, a unique suffix will be added.
'''
		options ={'width':2,
				  'style':'line',
				  'hidden':False,
				  "fast":1,
				  "order":0,
				  "start":0.0
				  }
		options['order']=len(self.plots.keys())
		options.update(opts)
		if options.get('color'):
			color = options['color']
			if type(color)==type(' '):
				color=wx.NamedColor(color)
			elif type(color)==type(wx.Colour(0,0,0)):
				pass	
			elif type(color)==list and type(color[0])==type(wx.Colour(0,0,0)):
				pass
			else:
				color=apply(wx.Colour, color)
		else:	
			options["color"], options['dashStyle']=self.nextcolor()
		index=1
		basename=name
		while  self.plots.has_key(name):
			index+=1
			name = "%s_%i" % (basename, index)
		if len(data.shape) == 1:
			data = reshape(data, (-1, 1))
		options["data"]=data
		self.plots[name] = options
		return name


if __name__=='__main__':
	from mien.math.sigtools import uniform
	from time import time
	#ds=load('test.pydat')
	app = wx.PySimpleApp()
	bar = {'size':(800,600), 'style':wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE}
	frame = wx.Frame(None, -1, "Output Graph", **bar)
	frame.g = GraphFSR(frame, -1)
	frame.g.fs=1000
	frame.Show(True)
	#dat = sin(arange(494)*.01)
	dat=arange(0,1000)
	dat=dat%801
	dat=reshape(dat, (-1, 1))
	#base=arange(-10000, 10000)/10000.0
	#dat=abs(base)
	C=frame.g.nextcolor(dat.shape[1])
	frame.g.addPlot(dat, style="polyline", name='poly', color=[x[0] for x in C])
	frame.g.addPlot(dat, style="envelope")
	color = wx.Colour(240,0,0)
	frame.g.xmarkers.append({"loc":.8, "color":color})
	#frame.g.addPlot(shift(dat, 2), style="points", start=-.1)
	#dat=1000*base[500:]**2
	#frame.g.addPlot(dat, style="points", start=-.05)
	#frame.g.limit(array([-.002, .002, -.002, .002])
	#frame.g.xmarkers.append({'loc':0.0, 'color':(200,200,0)})
	#dat=uniform(-1, 1, (1000,3))
	#evts = where(dat>.9, 1.0, 0.0)
	#dat = sin(arange(0,7, .001))
	#dat2 = cos(arange(0,7, .001))
	#dat3=concatenate([dat[:,NewAxis], dat2[:, NewAxis]], 1)
	#frame.g.addPlot(dat3, style="image", colorrange="all")
	#op={'width': 1, 'style': 'raster', 'scale': 1.0, 'offset': 0.0} 
	#frame.g.addPlot(evts, **op)
	#frame.g.addPlot(evts, style="hist", bin=2.0, offset=-1, scale=1.2)
	#st=time()
	#dat=ds.data[:,0]
	#opts= {'start': 0.0, 'style': 'envelope', 'name': 'Chan0_1'} 
	#print opts
	#name=frame.g.addPlot(ds.data, **opts)
	#name=frame.g.addPlot(ds.data[:,1], style='envelope', start=0.0)

	#frame.g.fullScale()


	frame.g.DrawAll()
	#print time()-st
	app.MainLoop()



