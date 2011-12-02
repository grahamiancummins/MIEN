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

from mien.wx.graphs.glcolor import *
from mien.wx.dialogs import askParameters
from mien.wx.base import KEYCODES
from mien.image.arrayops import images_to_stack, array_to_image


def getKeyFromCode(i):
	if KEYCODES.has_key(i):
		return KEYCODES[i]
	try:
		c=chr(i)
	except:
		c=i
	return c


def pointZat(a):
	'''execute a glRotate(theta, x, y, z) what was the z axis (0,0,1) is now 
aligned with the vector a'''	
	zaxis=array([0.0,0.0,1.0])
	a=a/sqrt(sum(a**2))
	theta=-arccos(dot(a, zaxis))
	theta=180*theta/pi
	rot=cross(a, zaxis)
	if theta and any(rot):
		glRotatef(theta,rot[0],rot[1],rot[2])

def fastArrayScale(dat, width=512, height=-1):
	if height<1:
		height=int(round(float(width)*dat.shape[1]/dat.shape[0]))
	ws=uniformSampleIndex(dat.shape[0], width)
	hs=uniformSampleIndex(dat.shape[1], height)	
	dat=dat[ws,:,:,:]
	dat=dat[:,hs,:,:]
	return dat


class GraphGL(glcanvas.GLCanvas):

	def __init__(self, parent):
		glcanvas.GLCanvas.__init__(self, parent, -1)
		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.Bind(wx.EVT_PAINT, self.OnDraw)
		self.clearcolor=[0.0,0,0]
		self.slices=6
		self.quad = None
		#self.stackhieght=.2i
		self.dontedit=['image','data', 'colorlist', 'displaylist', 'imagedata']
		self.plots={}
		self.views={}
		self._enhancedDepthCheck = False
		self.global_options=['slices', 'clearcolor', 'resolution', 'perspective']
		self.depthoffield=10.088
		self.perspective=0
		self.resolution=10.0
		self.lastclick=array([0.0,0,0])
		self.stdView(draw=False)
		self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
		wx.EVT_ENTER_WINDOW(self, self.OnEnter)
		wx.EVT_CHAR(self, self.OnKey)
		wx.EVT_RIGHT_DOWN(self, self.OnRightClick)
		wx.EVT_LEFT_DOWN(self, self.OnLeftClick)
		self.keybindings = {
			'f1':self.configure,
			'f2':self.viewEdit,
			'1':lambda x:self.stdView('z'),
			'2':lambda x:self.stdView('x'),
			'3':lambda x:self.stdView('y'),
			'4':lambda x:self.OnDraw(),
			'5':lambda x:self.presetView(None),
			'-':lambda x:self.zoom(1),
			'=':lambda x:self.zoom(-1),
			'_':lambda x:self.changeDOF(-1),
			'+':lambda x:self.changeDOF(1),
			'p':lambda x:self.zTrans(1),
			'r':lambda x:self.zTrans(1),
			'u':lambda x:self.zTrans(-1),
			'f':lambda x:self.zTrans(-1),
			'\'':lambda x:self.roll(1),
			'q':lambda x:self.roll(1),
			'.':lambda x:self.roll(-1),
			'<':lambda x: self.vPan(1),
			'W':lambda x: self.vPan(1),
			'O':lambda x: self.vPan(-1),
			'S':lambda x: self.vPan(-1),
			'A':lambda x: self.hPan(-1),
			'E':lambda x:self.hPan(1),
			'D':lambda x:self.hPan(1),
			',':lambda x: self.vOrbit(1),
			'w':lambda x: self.vOrbit(1),
			'o':lambda x: self.vOrbit(-1),
			's':lambda x: self.vOrbit(-1),
			'a':lambda x: self.hOrbit(-1),
			'e':lambda x:self.hOrbit(1),
			'd':lambda x:self.hOrbit(1),
			'left':lambda x:self.hRotate(1),
			'right':lambda x:self.hRotate(-1),
			'up':lambda x:self.vRotate(1),
			'down':lambda x:self.vRotate(-1)
		}



		self.styles={'frusta':self.makeFrustaDisplay,
				     'lines':self.makeLinesDisplay,
				     'contour':self.makeLinesDisplay,
				     'spheres':self.makeSphereDisplay,
				     'imagelayer':self.makeILayerDisplay,
				     'density':self.makeDensDisplay,
				     'custom':self.noOp,
				     'text':self.noOp,
				     'image':self.noOp,
				     'points':self.makePointCloudDisplay,
				     'mixed':self.makeMixedDisplay,
				     'imagestack':self.makeImageStackDisplay}	
		self.aspect=None		



	def noOp(self, *args, **kwargs):
		pass

	def OnEnter(self, event=None):
		self.SetFocus()

	def OnEraseBackground(self, event):
		pass # Do nothing, to avoid flashing on MSW.

	def OnKey(self, event):
		c = getKeyFromCode(event.GetKeyCode())
		if self.keybindings.has_key(c):
			self.keybindings[c](event)
		else:
			print  c
			event.Skip()

	def frontPlane(self):
		right=cross(self.forward, self.up)
		htrans=right*self.extent*self.aspect
		vtrans=self.up*self.extent
		ulc=self.viewpoint+vtrans-htrans
		return (ulc, 2*htrans, -2*vtrans)	

	def findMouse(self, x, y):
		ulc, wid, high=self.frontPlane()
		size = self.GetClientSize()
		wid=wid*(float(x)/size.width)
		high=high*(float(y)/size.height)
		return ulc+wid+high

	def size2pix(self, a, mode="xy"):
		hs = self.extent*2
		vs = hs*self.aspect
		size = self.GetClientSize()
		if mode=="y":
			return int(round(a*size.height/vs))
		elif mode=="x":
			return int(round(a*size.width/hs))
		else:
			v = a*size.height/vs
			h = a*size.width/hs
			vh = (v+h)/2.0
			vh = max(1, vh-1)
			return int(round(vh))



	def OnLeftClick(self, event):
		pt = self.findMouse(event.GetX(), event.GetY())
		print pt, self.forward, self.up, eucd(self.lastclick, pt)
		self.lastclick=pt
		self.OnDraw()

	def OnRightClick(self, event):
		pt = self.findMouse(event.GetX(), event.GetY())
		self.viewpoint=pt
		self.OnDraw()

	def centerOnPoint(self, pt):
		ptz = pt -self.forward*self.depthoffield/2
		self.viewpoint=ptz
		self.OnDraw()	

	def containSphere(self):
		plots=self.plots.values()	
		bb=None
		for nbb in [p['boundingbox'] for p in plots]:
			if nbb==None:
				continue
			if bb==None:
				bb=nbb
			else:	
				bb[0]=minimum(bb[0], nbb[0])
				bb[1]=maximum(bb[1], nbb[1])
		if bb==None:
			return [array([0,0,0.0]), 10.0]
		cent=(bb[0]+bb[1])/2.0
		rad=eucd(bb[1], cent)
		return (cent, rad)

	def stdView(self, ax='z', draw=True):
		units={'z':array([0.0,0,1]),
			   'x':array([1.0,0,0]),
			   'y':array([0.0,1,0])
			   }
		if ax!='z':
			self.up=units['z']
		else:
			self.up=units['y']
		ax=units[ax]		
		cent, rad=self.containSphere()
		self.viewpoint=cent+ax*rad
		self.forward=-1*ax
		self.extent=rad
		self.depthoffield=2*rad
		if draw:
			self.OnDraw()

	def zoom(self, sign):
		fac=1.0+sign*self.resolution/100.0
		self.extent*=fac
		self.OnDraw()

	def zTrans(self, sign):
		inc=sign*self.depthoffield*self.resolution/200.0
		self.viewpoint+=self.forward*inc
		self.OnDraw()

	def changeDOF(self, sign):
		fac=1.0+sign*self.resolution/100.0
		self.depthoffield*=fac
		self.OnDraw()

	def roll(self, sign):
		ang=sign*pi*(self.resolution/100.0)
		self.up=rotateAround(self.up, self.forward, ang)
		self.OnDraw()	

	def vPan(self, sign):
		inc=sign*self.extent*self.resolution/50.0
		self.viewpoint+=self.up*inc
		self.OnDraw()

	def hPan(self, sign):
		inc=sign*self.extent*self.resolution/50.0
		right=cross(self.forward, self.up)
		self.viewpoint+=inc*right
		self.OnDraw()

	def hOrbit(self, sign, m=None):
		if not m:
			m=self.resolution
		ang=sign*pi*(m/100.0)
		standoff=-1*self.forward*self.depthoffield/2.0
		cent=self.viewpoint-standoff
		newstandoff=rotateAround(standoff, self.up, -ang)
		trans=newstandoff-standoff
		self.viewpoint+=trans
		fw=cent-self.viewpoint
		self.forward=fw/sqrt((fw**2).sum())
		self.OnDraw()

	def vOrbit(self, sign, m=None):
		if not m:
			m=self.resolution
		ang=sign*pi*(m/100.0)
		standoff=-1*self.forward*self.depthoffield/2.0
		cent=self.viewpoint-standoff
		right=cross(self.forward, self.up)
		newstandoff=rotateAround(standoff, right, -ang)
		trans=newstandoff-standoff
		self.viewpoint+=trans
		fw=cent-self.viewpoint
		self.forward=fw/sqrt((fw**2).sum())
		self.up=cross(right, self.forward)
		self.OnDraw()


	def hRotate(self, sign):
		ang=sign*pi*(self.resolution/100.0)
		self.forward=rotateAround(self.forward, self.up, ang)
		self.OnDraw()

	def vRotate(self, sign):
		ang=sign*pi*self.resolution/100.0
		right=cross(self.forward, self.up)
		self.forward=rotateAround(self.forward, right, ang)
		self.up=rotateAround(self.up, right, ang)
		self.OnDraw()

	def OnSize(self, event=None):
		size = self.GetClientSize()
		self.aspect=size.width/float(size.height)
		if self.GetContext():
			self.SetCurrent()
			glViewport(0, 0, size.width, size.height)
		if event:
			event.Skip()

	def setView(self):
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		lookat=self.viewpoint+self.forward
		vp=self.viewpoint.tolist()+lookat.tolist()+self.up.tolist()
		apply(gluLookAt, vp)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		if not self.perspective:
			glOrtho(-self.aspect*self.extent, self.aspect*self.extent, -self.extent, self.extent, 0.0, self.depthoffield)
		else:
			glFrustum(-self.aspect*self.extent/10.0, self.aspect*self.extent/10.0, -self.extent/10.0, self.extent/10.0, .05*self.depthoffield, self.depthoffield)


	def drawCyl(self, coords):
		'''coords is an array [x,y,z, rx, ry, rz, theta, l, d1, d2]
		Theta is counterclockwise rotation around the vector rx,ry,rz'''
		x,y,z,rx,ry,rz,theta,l,d1,d2=coords
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glTranslatef(x,y,z)
		glRotatef(theta,rx,ry,rz)
		if not self.quad:
			self.quad=gluNewQuadric()
		#gluCylinder(self.quad, d1, d2, l, self.slices, max(int(round(l/self.stackhieght)), 1))
		try:
			gluCylinder(self.quad, d1, d2, l, self.slices, 1)
		except:
			print d1, d2, l
		glPopMatrix()

	def drawSphere(self, coords):
		x,y,z,r = coords
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glTranslatef(x,y,z)
		if not self.quad:
			self.quad=gluNewQuadric()
		gluSphere(self.quad, r, self.slices, self.slices)
		glPopMatrix()


	def perpendicularView(self):
		xaxis=array([1.0, 0, 0])
		yaxis=array([0,1.0,0])
		theta=0.0
		phi=0.0
		up=self.up
		right=cross(up, self.forward)
		atv=cross(xaxis, right)
		if not all(atv==0):
			atv=atv/sqrt((atv**2).sum())
			dp=min(1.0, dot(xaxis, right))
			dp=max(-1.0, dp)
			theta=arccos(dp)
			theta=180*theta/pi-180
			up=rotateAround(up, atv, -theta*pi/180)
		apv=cross(yaxis, up)
		if not all(apv==0):
			dp=min(dot(yaxis, up), 1.0)
			dp=max(dp, -1.0)
			phi=arccos(dp)
			phi=180*phi/pi
		if abs(theta)>.0001:		
			glRotatef(theta,atv[0],atv[1], atv[2])
		if abs(phi)>.0001:	
			glRotatef(phi,apv[0],apv[1], apv[2])

	def drawLabel(self, d):
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
		glEnable(GL_BLEND);
		glEnable(GL_LINE_SMOOTH);
		materialColor(d['color'])
		glLineWidth(d['width']);
		x,y,z = d['loc']
		glTranslatef(x,y,z)
		self.perpendicularView()
		h=d.get('charsize', 5.0)
		sh=2*self.extent
		#w=glutStrokeLength(GLUT_STROKE_ROMAN, s)
		#w=cs*w/119.05
		h=sh*h/100.0
		s=h/119.05
		glScalef(s,s,s)
		for c in d['text']:
			glutStrokeCharacter(GLUT_STROKE_ROMAN, ord(c))
		glDisable(GL_BLEND);	
		glPopMatrix()


	def drawImage(self, d):
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		loc=d['loc']
		size=d.get('size')
		ws=self.GetClientSize()	
		ww, wh =float(ws.width), float(ws.height)
		if d['pos'].startswith('rel'):	
			ulc, w, h=self.frontPlane()
			il=ulc+h+self.forward
			il+=loc[0]*w
			il-=loc[1]*h
		else:
			if len(loc)!=3:
				il=(loc[0], loc[1], 0)
			else:	
				il=tuple(loc)	
		glRasterPos3f(il[0], il[1], il[2])
		im=d['image']
		if d['sizemode'].startswith('rel'):
			iw = ww*size[0]
			ih= wh*size[1]
			im=im.Copy()
			im.Rescale(iw, ih)
		elif d['sizemode'].startswith('pix'):
			im=im.Copy()
			im.Rescale(size[0], size[1])
		elif d['sizemode'].startswith('coord'):
			scale=2*self.extent
			iw = size[0]*ww/scale
			ih= size[1]*wh/scale
			im=im.Copy()
			im.Rescale(iw, ih)
		w=im.GetWidth()
		h=im.GetHeight()
		glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
		id=im.GetData()
		pix=fromstring(id, 'B')
		pix= reshape(pix, (w, h, 3))
		glDrawPixelsub(GL_RGB, pix)
		glPopMatrix()

	def checkDepth(self):
		for k in self.plots:
			bb = self.plots[k]['boundingbox']
			bb= array(bb).min(0)
			x = dot(bb, -1*self.forward)
			self.plots[k]['ontop']=x

	def OnDraw(self, event=None):
		#import time; t = time.time()
		if self.aspect==None:
			self.OnSize()
		if event:
			wx.PaintDC(self)
		self.SetCurrent()
		glEnable(GL_DEPTH_TEST)
		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)
		self.setView()
		apply(glClearColor, self.clearcolor+[0])
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glShadeModel(GL_SMOOTH)
		do=self.plots.keys()
		if self._enhancedDepthCheck:
			self.checkDepth()
		do.sort(self.sortplots)
		for k in do:
			d=self.plots[k]
			h=d.get('hide')
			if h=='fade':
				glLight(GL_LIGHT0, GL_AMBIENT, [.2,.2,.2,.2])
				glLight(GL_LIGHT0, GL_DIFFUSE, [0.0, 0.0, 0.0, 0.0])
				glLight(GL_LIGHT0, GL_SPECULAR,[0.0, 0.0, 0.0, 0.0])
				glLight(GL_LIGHT0, GL_POSITION, self.viewpoint.tolist()+[0.0]);
				glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
				glLightModelfv(GL_LIGHT_MODEL_LOCAL_VIEWER, 1)
			elif h:
				continue
			else:
				glLight(GL_LIGHT0, GL_AMBIENT, [1.0, 1.0, 1.0, 1.0])
				glLight(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
				glLight(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
				glLight(GL_LIGHT0, GL_POSITION, self.viewpoint.tolist()+[0.0]);
				glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [1.0,1.0,1.0, 1.0])
				glLightModelfv(GL_LIGHT_MODEL_LOCAL_VIEWER, 1)				
			if d['style']=='text':
				self.drawLabel(d)
			elif d['style']=='image':
				self.drawImage(d)
			elif d.get('lineprojection'):
				self.drawLineProjection(d)
			else:
				if d.get("setPointSize"):
					glPointSize(self.size2pix(d["setPointSize"]))	
				glCallList(d['displaylist'])
		glFlush()
		self.SwapBuffers()
		#print "g %i" % (time.time() - t,)


	def sortplots(self, a, b):
		a=self.plots[a]
		b=self.plots[b]
		ac=a.get('ontop', 0)
		bc=b.get('ontop', 0)
		v=cmp(ac, bc)
		if v:
			return v
		ac=a.get('draworder', 0)
		bc=b.get('draworder', 0)
		return cmp(ac, bc)	

	def getNewColor(self, used=[]):
		havecolors=used+[p['color'] for p in self.plots.values()]
		colors=[(1, 1, 1.0),
				(0.0, .8, 0),
				(0, 0, .8),
				(.8, 0, 0),
				(0,.8,.8),
				(.8,0,.8),
				(.8,.8,0)
				]
		i=0
		col=colors[i]
		while col in havecolors:
			i+=1
			if i<len(colors):
				col=colors[i]
			else:
				col=tuple(uniform(0,1,3))
		return col

	def defaults(self, opts):
		if not opts.get('name'):
			name=0
			while self.plots.has_key(str(name)):
				name+=1
			name=str(name)
		else:
			name=opts['name']
			del(opts['name'])
		if not opts.get('color'):
			opts['color']=self.getNewColor()
		if not opts.has_key("width"):
			opts['width']=2.0
		if not opts.has_key('colorlist'):
			opts['colorlist']=[]
		if not opts.has_key('hide'):
			opts['hide']=False
		return name	

	### Drawing functions ===============================================

	def addFrustaPlot(self, pts, **opts):
		bb=[array([pts[:,0].min(),pts[:,1].min(),pts[:,2].min()]),		
			array([pts[:,0].max(),pts[:,1].max(),pts[:,2].max()])]		
		pts=reshape(pts, (-1,8))
		radii=take(pts, [3,7], 1)/2.0
		starts=pts[:,:3]
		shifts=pts[:,4:7]-starts
		r=sqrt(sum(shifts**2, 1))
		norms=shifts/r[:,NewAxis]
		zaxis=array([0.0,0.0,1.0])
		theta=-arccos(dot(norms, zaxis))
		theta=180*theta/pi
		rot=array([cross(v, zaxis) for v in norms])
		data=concatenate([starts, rot, theta[:,NewAxis], r[:, NewAxis], radii], 1)
		name=self.defaults(opts)
		opts['style']='frusta'
		opts['data']=data
		opts['boundingbox']=bb
		self.plots[name]=opts
		dl=self.makeFrustaDisplay(name)
		#self.stdView()
		return name

	def makeFrustaDisplay(self, name):
		self.SetCurrent()
		plot=self.plots[name]
		# if plot['colorlist']:
		# 	print len(plot['colorlist'])
		# else:
		# 	print 'no clist'
		dl=glGenLists(1)
		glNewList(dl, GL_COMPILE)
		if plot.get('ontop'):
			glDisable(GL_DEPTH_TEST)
		materialColor(plot['color'])
		for i in range(plot['data'].shape[0]):
			c=plot['data'][i]
			if plot['colorlist']:
				materialColor(plot['colorlist'][i])	
			self.drawCyl(c)
		if plot.get('ontop'):
			glEnable(GL_DEPTH_TEST)
		glEndList()
		self.plots[name]['displaylist']=dl

	def addLinesPlot(self, pts, **opts):
		bb=[array([pts[:,0].min(),pts[:,1].min(),pts[:,2].min()]),		
			array([pts[:,0].max(),pts[:,1].max(),pts[:,2].max()])]		
		name=self.defaults(opts)
		opts['boundingbox']=bb
		if not opts.has_key('style'):
			opts['style']='lines'	
		if opts['style']=='lines':
			pts=reshape(pts, (-1,6))
		else:	
			opts['style']='contour'	
		opts['data']=pts
		self.plots[name]=opts
		self.makeLinesDisplay(name)
		#self.stdView()
		return name

	def addCustomDisplayList(self, dl, **opts):
		name = self.defaults(opts)
		opts['displaylist']=dl
		opts["style"]="custom"
		self.plots[name]=opts
		return name

	def makeLinesDisplay(self, name):
		self.SetCurrent()
		plot=self.plots[name]
		dl=glGenLists(1)
		glNewList(dl, GL_COMPILE)
		if plot.get('ontop'):
			glDisable(GL_DEPTH_TEST)
		materialColor(self.plots[name]['color'])
		glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.0, 0.0, 0.0, 0.0])
		glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, list(plot['color'])+[0])
		glLineWidth(plot['width'])
		if plot['style']=='lines':
			glBegin(GL_LINES)
		else:
			glBegin(GL_LINE_STRIP)
		for i, c in enumerate(plot['data']):
			if plot['colorlist']:
				materialColor(plot['colorlist'][i])
			glVertex3fv(c[:3])
			if plot['style']=='lines':
				glVertex3fv(c[3:])
		glEnd()	
		if plot.get('ontop'):
			glEnable(GL_DEPTH_TEST)
		glEndList()
		self.plots[name]['displaylist']=dl

	def drawLineProjection(self, plot):
		materialColor(plot['color'])
		ulc, h, v = self.frontPlane()
		# print ulc
		h=h/sqrt((h**2).sum())
		v=-v/sqrt((v**2).sum())
		glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.0, 0.0, 0.0, 0.0])
		glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, list(plot['color'])+[0])
		glLineWidth(plot['width'])
		if plot['style']=='lines':
			glBegin(GL_LINES)
		else:
			glBegin(GL_LINE_STRIP)
		for i, c in enumerate(plot['data']):
			c1=ulc+h*dot(c[:3]-ulc,h)+v*dot(c[:3]-ulc, v)+.01*self.forward
			# if i==0:		
			# 	print c[:3], h, c1
			# 
			if plot['colorlist']:
				materialColor(d['colorlist'][i])
			glVertex3fv(c1)
			if plot['style']=='lines':
				c2=ulc+dot(c[3:],h)+dot(c[3:], v)
				glVertex3fv(c2)
		glEnd()	

	def addLabel(self, **opts):
		opts['boundingbox']=None
		name=self.defaults(opts)
		opts['style']='text'	
		self.plots[name]=opts
		return name

	def addImage(self, **opts):
		opts['boundingbox']=None
		name=self.defaults(opts)
		opts['style']='image'
		opts['pos']=opts.get('pos', 'relative')
		opts['loc']=opts.get('loc', (0,0))
		opts['sizemode']=opts.get('sizemode', 'raw')
		opts['size']=opts.get('size', (1.0,1.0))
		im=opts['image']
		im=im.Mirror(False)
		opts['image']=im
		self.plots[name]=opts
		return name

	def addImageLabel(self, **opts):
		opts['boundingbox']=None
		name=self.defaults(opts)
		opts['style']='image'
		opts['pos']='coords'
		opts['sizemode']='raw'
		bor=opts.get('border', True)
		im=makeTextImage(opts['text'], opts.get('size', 14), opts['color'], self.clearcolor, bor)
		im=im.Mirror(False)
		opts['image']=im
		self.plots[name]=opts
		return name

	def addColorScale(self, **opts):
		opts['boundingbox']=None
		name=self.defaults(opts)
		opts['style']='image'
		opts['pos']='rel'
		opts['isscale']='color'
		opts['loc']=(.85,.05)
		opts['sizemode']='raw'
		a = array([opts['min'], opts['max']])
		if not "colors" in opts:
			cs = opts.get('cs', 'hot')
			r = opts.get('range')
			sample = arange(min(a), max(a), (max(a)-min(a))/20.0)
			opts["colors"] = colorscale(sample, cs, r)
		im=makeCscale(a, opts['colors'], 256, self.clearcolor)
		im=im.Mirror(False)
		opts['image']=im
		for p in self.plots.keys():
			if self.plots[p].get('isscale')=='color':
				del(self.plots[p])
		self.plots[name]=opts
		return name

	def addSpherePlot(self, pts, **opts):
		bb=[array([pts[:,0].min(),pts[:,1].min(),pts[:,2].min()]),		
			array([pts[:,0].max(),pts[:,1].max(),pts[:,2].max()])]		
		opts['boundingbox']=bb
		name=self.defaults(opts)
		if pts.shape[1]<4:
			radii=ones(pts.shape[0], pts.dtype)*opts['width']
			pts=concatenate([pts, radii[:,NewAxis]], 1)
		else:
			pts[:,3]=pts[:,3]/2.0
		opts['style']='spheres'	
		opts['data']=pts
		self.plots[name]=opts
		self.makeSphereDisplay(name)
		#self.stdView()
		return name

	def makeSphereDisplay(self, name):
		self.SetCurrent()
		plot=self.plots[name]
		dl=glGenLists(1)
		glNewList(dl, GL_COMPILE)
		if plot.get('ontop'):
			glDisable(GL_DEPTH_TEST)
		materialColor(self.plots[name]['color'])
		if plot.get("Shininess")!=None:
			glMaterial(GL_FRONT_AND_BACK, GL_SHININESS, plot["Shininess"])
		for i, c in enumerate(plot['data']):
			if plot['colorlist']:
				materialColor(plot['colorlist'][i])
			self.drawSphere(c)
		if plot.get('ontop'):
			glEnable(GL_DEPTH_TEST)
		glEndList()
		self.plots[name]['displaylist']=dl

	def addPointPlot(self, pts, **opts):
		bb=[array([pts[:,0].min(),pts[:,1].min(),pts[:,2].min()]),		
			array([pts[:,0].max(),pts[:,1].max(),pts[:,2].max()])]		
		opts['boundingbox']=bb
		name=self.defaults(opts)
		opts['style']='points'	
		opts['data']=pts
		self.plots[name]=opts
		self.makePointCloudDisplay(name)
		#self.stdView()
		return name

	def makePointCloudDisplay(self, name):
		self.SetCurrent()
		plot=self.plots[name]
		dl=glGenLists(1)
		glNewList(dl, GL_COMPILE)
		materialColor(self.plots[name]['color'])
		if not plot.get('setPointSize'):
			glPointSize(plot['width'])
		glBegin(GL_POINTS)
		for i, c in enumerate(plot['data']):
			if plot['colorlist']:
				materialColor(plot['colorlist'][i])
			glVertex3fv(c[:3])
		glEnd()	
		glEndList()
		self.plots[name]['displaylist']=dl

	def conditionImageData(self, opts):
		if not opts.has_key('imagedata'):
			if opts.has_key('images'):
				imgs=opts['images']
			elif opts.has_key('image'):
				imgs=[opts['image']]
			else:
				raise StandardError('Image layer plots require on of the arguments imagedata, images, or image. None of these were passed')
			opts['imagedata']=images_to_stack(imgs)	
		dat=opts['imagedata']		
		dat=dat[:,arange(dat.shape[1]-1, -1, -1),:,:]
		dat=array_to_image(dat, opts.get('crange'), opts.get('pcolor'))	
		w=dat.shape[0]
		nw=closestPow2(w)
		if nw!=w:
			dat=fastArrayScale(dat, nw)
		dat=transpose(dat, (1,0,2,3))
		dat=reshape(dat, (dat.shape[1], dat.shape[0], dat.shape[2], dat.shape[3]))	
		return dat

	def addImageLayer(self, pts, **opts):
		'''pts is a 4x3 array of vertexes''' 
		bb=[array([pts[:,0].min(),pts[:,1].min(),pts[:,2].min()]),		
			array([pts[:,0].max(),pts[:,1].max(),pts[:,2].max()])]		
		opts['boundingbox']=bb
		name=self.defaults(opts)
		opts['style']='imagelayer'
		opts['data']=pts
		opts['imagedata']=self.conditionImageData(opts)
		self.plots[name]=opts
		self.makeILayerDisplay(name)
		return name	

	def drawImageLayer(self, pts, imagedata, frame=True):
		glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
		glTexImage2Dub(GL_TEXTURE_2D,0,GL_RGB,0,GL_RGB, imagedata)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
		glEnable(GL_TEXTURE_2D)
		glBegin(GL_POLYGON)
		#glNormal3f(0.0,0.0,1.0)
		glTexCoord2f(0,0)
		glVertex3fv(pts[0,:])
		glTexCoord2f(0,1.0)
		glVertex3fv(pts[1,:])
		glTexCoord2f(1.0,1.0)
		glVertex3fv(pts[2,:])
		glTexCoord2f(1.0,0.0)
		glVertex3fv(pts[3,:])
		glEnd()
		glDisable(GL_TEXTURE_2D)
		if frame:
			glBegin(GL_LINE_STRIP)
			materialColor((.5,.5,.5))
			glVertex3fv(pts[0,:])
			glVertex3fv(pts[1,:])
			glVertex3fv(pts[2,:])
			glVertex3fv(pts[3,:])
			glEnd()	


	def makeILayerDisplay(self, name):
		pix=self.plots[name]['imagedata']
		pts=self.plots[name]['data']
		dl=glGenLists(1)
		glNewList(dl, GL_COMPILE)
		self.drawImageLayer(pts, pix[:,:,:,0])
		glEndList()
		self.plots[name]['displaylist']=dl

	def addImageStack(self, pts, **opts):
		'''pts is a 4x3 array of vectors: anchor, width, height, depth, where anchor is the location of the upper right corner of the stack in three space, width and height are the 3-vectors specifying the width and height of the stack, and depth is a 3-vector specifying the distance between two planes of the stack. Options must include "imagedata"''' 
		name=self.defaults(opts)
		opts['style']='imagestack'
		opts['data']=pts
		opts['imagedata']=self.conditionImageData(opts)
		fulldepth=pts[3,:]*max(opts['imagedata'].shape[3],1.0)
		bb=vstack([pts[0,:], pts[0,:]+pts[1,:]-pts[2,:]+fulldepth])
		bb=[array([bb[:,0].min(),bb[:,1].min(),bb[:,2].min()]),		
			array([bb[:,0].max(),bb[:,1].max(),bb[:,2].max()])]		
		opts['boundingbox']=bb	
		self.plots[name]=opts
		self.makeImageStackDisplay(name)
		return name

	def makeImageStackDisplay(self, name):
		pix=self.plots[name]['imagedata']
		pts=self.plots[name]['data']
		trans = self.plots[name].get("transparent")
		anchor=pts[0,:]
		w=pts[1,:]
		h=pts[2,:]
		down=pts[3,:]
		dl=glGenLists(1)
		glNewList(dl, GL_COMPILE)
		if trans:
			glEnable(GL_BLEND);
			glEnable(GL_POLYGON_SMOOTH)
			glDisable(GL_LIGHTING)
			glDisable(GL_DEPTH_TEST)
			#glBlendFunc(GL_ONE_MINUS_DST_COLOR, GL_DST_COLOR)
			glBlendFunc(GL_SRC_COLOR, GL_ONE_MINUS_SRC_COLOR)
		for frame in range(pix.shape[3]):
			ul=anchor+frame*down
			ll=ul-h
			ur=ul+w
			lr=ul+w-h
			fp=vstack([ll, ul, ur, lr])
			self.drawImageLayer(fp, pix[:,:,:,frame], not trans)
		if trans:
			glDisable(GL_BLEND);
			glEnable(GL_LIGHTING)
			glEnable(GL_DEPTH_TEST)
			glDisable(GL_POLYGON_SMOOTH)		
		glEndList()
		self.plots[name]['displaylist']=dl

	def addMixedPlot(self, pts,  **opts):
		'''pts contains 2 rows of 4 values (xyzd) for each object. If the second d is 0 the
		object is drawn as a sphere (with _radius_ equal to the first d). If both d are less
		than twice opts['linerad'] the object is drawn as a line. Otherwise it is a frustum'''
		bb=[array([pts[:,0].min(),pts[:,1].min(),pts[:,2].min()]),		
			array([pts[:,0].max(),pts[:,1].max(),pts[:,2].max()])]		
		pts=reshape(pts, (-1,8))
		linerad=opts.get('linerad', 2.0)
		radii=take(pts, [3,7], 1)/2.0
		spheres=nonzero1d(radii[:,1]==0)
		lines=nonzero1d(logical_and(radii[:,1]>0, maximum(radii[:,0], radii[:,1])<=linerad))
		used=unique(concatenate([spheres, lines]))
		frusta=setdiff1d(arange(pts.shape[0]), used)
		data=zeros((pts.shape[0], 10), Float32)
		allpts=pts
		if len(frusta):
			#calc frusta
			pts=take(allpts, frusta, 0)
			radii=take(pts, [3,7], 1)/2.0
			starts=pts[:,:3]
			shifts=pts[:,4:7]-starts
			r=sqrt(sum(shifts**2, 1))
			norms=shifts/r[:,NewAxis]
			zaxis=array([0.0,0.0,1.0])
			theta=-arccos(dot(norms, zaxis))
			theta=180*theta/pi
			rot=array([cross(v, zaxis) for v in norms])
			frustdata=concatenate([starts, rot, theta[:,NewAxis], r[:, NewAxis], radii], 1)
			put(data, frusta, frustdata)
		if len(spheres):
			#calc spheres
			pts=take(allpts, spheres, 0)[:,:4]
			pts=concatenate([pts, zeros((pts.shape[0], 6), Float32)], 1)
			put(data, spheres, pts)
		if len(lines):
			pts=take(allpts, lines, 0)
			pts=concatenate([pts, zeros((pts.shape[0], 2), Float32)], 1)
			put(data, lines, pts)
		name=self.defaults(opts)
		opts['style']='mixed'
		opts['data']=data
		opts['boundingbox']=bb
		self.plots[name]=opts
		dl=self.makeMixedDisplay(name)
		#self.stdView()
		return name

	def makeMixedDisplay(self, name):
		self.SetCurrent()
		plot=self.plots[name]
		dl=glGenLists(1)
		glNewList(dl, GL_COMPILE)
		materialColor(self.plots[name]['color'])
		glLineWidth(1.0)
		for i, c in enumerate(plot['data']):
			if plot['colorlist']:
				materialColor(plot['colorlist'][i])
			if c[-1]>0:	
				self.drawCyl(c)
			elif c[7]>0:
				glBegin(GL_LINES)
				glVertex3fv(c[:3])
				glVertex3fv(c[4:7])
				glEnd()	
			else:
				self.drawSphere(c[:4])
		glEndList()
		self.plots[name]['displaylist']=dl

	def addDensPlot(self, pts, **opts):
		opts['edge']=opts.get('edge', 1.0)
		if not len(pts.shape) in [3, 4]:
			print pts.shape
			raise StandardError('Density clouds are only defined for 3 or 4 DOF array data')
		opts['anchor']=opts.get('anchor', array([0.0,0.0,0.0]))
		bb=[opts['anchor'], opts['anchor']+opts['edge']*array(pts.shape[:3])]		
		opts['boundingbox']=bb
		# print bb
		name=self.defaults(opts)
		opts['style']='density'	
		opts['pointshape']=opts.get('pointshape', 'cart')
		opts['ontop']=min(array(bb)[:,2])
		opts['data']=pts
		self.plots[name]=opts
		self.makeDensDisplay(name)
		#self.stdView()
		return name

	def makeDensDisplay(self, name):
		self.SetCurrent()
		plot=self.plots[name]
		dl=glGenLists(1)
		glNewList(dl, GL_COMPILE)
		c=self.plots[name]['color']
		glEnable(GL_BLEND);
		glEnable(GL_POLYGON_SMOOTH)
		glDisable(GL_LIGHTING)
		glDisable(GL_DEPTH_TEST)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
		dat=plot['data']
		edge=plot['edge']
		mindens=plot.get('mindensity', 0)
		maxdens=plot.get('maxdens', None)
		if plot['pointshape']=="points":
			plot["setPointSize"]=abs(edge).min()
			glBegin(GL_POINTS)
		a=plot['anchor']
		yv= plot['up']
		zv=plot['forward']
		xv=cross(zv, yv) * edge[0]
		yv=yv*edge[1]
		zv=zv*edge[2]
		if len(dat.shape) == 4:
			cscale = plot.get('colormap','hot')
			cscale = colorscales[cscale]
			cdim = plot.get('colordimension', 1)
			colors = dat[...,cdim]
			crange = plot.get('colorrange')
			colors = convert_type(colors, 'B', crange)
		if plot['pointshape']=='cart':
			xv2 = xv/2.0
			yv2 = yv/2.0
			zv2 = zv/2.0
		for i in range(dat.shape[0]):
			for j in range(dat.shape[1]):
				for k in range(dat.shape[2]):		
					#alphaColor(c, dat[i,j,k]/6.0)
					if len(dat.shape) == 3:
						dens = dat[i,j,k]
					else:
						dens = dat[i,j,k,0]
						c = cscale[int(colors[i,j,k])]
					if dens <=mindens:
						continue
					if maxdens and dens>maxdens:
						dens = maxdens
					glColor4f(c[0], c[1], c[2], dens/2.0)
					l = i*xv+j*yv-k*zv+a
					# l = array([i*edge[0], j*edge[1], k*edge[2]]) + a
					if plot['pointshape']=='cart':	
						glBegin(GL_POLYGON)
						glVertex3fv(l-xv2-yv2)
						glVertex3fv(l-xv2+yv2)
						glVertex3fv(l+xv2+yv2)
						glVertex3fv(l+xv2-yv2)
						glEnd()
						glBegin(GL_POLYGON)
						glVertex3fv(l-xv2-zv2)
						glVertex3fv(l-xv2+zv2)
						glVertex3fv(l+xv2+zv2)
						glVertex3fv(l+xv2-zv2)
						glEnd()
						glBegin(GL_POLYGON)
						glVertex3fv(l-yv2-zv2)
						glVertex3fv(l-yv2+zv2)
						glVertex3fv(l+yv2+zv2)
						glVertex3fv(l+yv2-zv2)
						glEnd()
					elif plot['pointshape']=="points":
						glVertex3fv(l)
		if plot['pointshape']=="points":
			glEnd()
		glDisable(GL_BLEND);
		glEnable(GL_LIGHTING)
		glEnable(GL_DEPTH_TEST)
		glDisable(GL_POLYGON_SMOOTH)
		glEndList()
		self.plots[name]['displaylist']=dl



	def recalc_bb(self, name):
		pl=self.plots[name]
		pts=pl.get('data')
		if pl['style'] in ['image', 'text']:
			return None
		if pl['style']=='imagestack':
			fulldepth=pts[3,:]*pl['imagedata'].shape[3]
			pts=vstack([pts[0,:], pts[0,:]+pts[1,:]-pts[2,:]+fulldepth])
		if pl['style']=='density':			
			bb=[pl['anchor'], pl['anchor']+pl['edge']*array(pts.shape)]		
			return bb
		bb=[array([pts[:,0].min(),pts[:,1].min(),pts[:,2].min()]),		
			array([pts[:,0].max(),pts[:,1].max(),pts[:,2].max()])]	
		return bb

	def recalc(self, name):	
		try:
			self.plots[name]['boundingbox']=self.recalc_bb(name)
		except:
			print("falied to calculate new bounding box for %s plot" % self.plots[name]['style'])
		try:
			dl = self.plots[name]['displaylist']
			glDeleteLists(dl, 1)
		except:
			print('failed to delete display list')
		self.styles[self.plots[name]['style']](name)


	def set_color(self,name, a, cs='hot', r=None):
		if len(a)<1:
			return
		if cs == "fade":
			self.plots[name]['colorlist'] = gradecolor(self.plots[name]['color'], a, r)
		else:										  
			self.plots[name]['colorlist']=colorscale(a, cs, r)
		self.recalc(name)


	### menu callbacks ===================================================
	def configure(self, event):
		rcmenu = wx.Menu()
		cm=[['Edit Global Options', self.editGlobals],
			['Edit Plot Options', self.editPlot],
			['Screen Shot', lambda x:self.screenShot()],
			['Save Presets', self.savePresets],
			['Load Presets', self.loadPresets],
			['Scale Bar', self.addScale],
			['Toggle Depth Check', self.swapADC],
			['Delete Plot', self.delPlot]]
		for i in range(len(cm)):
			id=wx.NewId()
			rcmenu.Append(id, cm[i][0])
			wx.EVT_MENU(self, id, cm[i][1])
		self.PopupMenu(rcmenu, (0,0))
		rcmenu.Destroy()

	def swapADC(self, event=None):
		self._enhancedDepthCheck = not self._enhancedDepthCheck
		self.report('set depth check to %s' % (str(self._enhancedDepthCheck),))




	def savePresets(self, event=None):
		l=askParameters(self, [{"Name":"File Name",
				                "Value":"viewpresets.txt"}])
		if not l:
			return
		fname=l[0]
		open(fname, 'w').write(repr(self.views))


	def loadPresets(self, event=None):
		l=askParameters(self, [{"Name":"File Name",
				                "Value":"viewpresets.txt"}])
		if not l:
			return
		fname=l[0]
		s=open(fname).read()
		self.views=eval(s)

	def selectPlot(self):
		if not self.plots:
			return None
		elif len(self.plots.keys())==1:
			return self.plots.keys()[0]
		else:
			l=askParameters(self, [{"Name":"Which Plot?",
						            "Type":"List",
						            "Value":self.plots.keys()}])
			if not l:
				return None
			return l[0]	

	def editGlobals(self, event):
		options=self.global_options
		l=askParameters(self, [{"Name":"Which Attribute?",
				                "Type":"List",
				                "Value":options}])
		if not l:
			return None
		an=l[0]	
		val=getattr(self, an)	
		l=askParameters(self, [{"Name":an,
				                "Value":repr(val)}])
		if not l:
			return
		try:
			nv=eval(l[0])
		except TypeError:
			nv = l[0]
		setattr(self, an, nv)
		for pn in self.plots.keys():
			self.styles[self.plots[pn]['style']](pn)
		self.OnDraw()

	def addScale(self, event):
		l=askParameters(self, [{"Name":"Bar Length",
				                "Value":self.extent/2.0}])
		if not l:
			return None
		ulc, hor, ver=self.frontPlane()
		start=ulc+.05*hor+.05*ver+self.forward
		hor=hor/sqrt(sum(hor**2))
		stop=start+hor*l[0]
		self.SetCurrent()
		color=[1-x for x in self.clearcolor]
		materialColor(color)
		glLineWidth(8)
		glBegin(GL_LINES)
		glVertex3fv(start)
		glVertex3fv(stop)
		glEnd()	

		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		il=(start+stop)/2-self.up
		glRasterPos3f(il[0], il[1], il[2])
		im=makeTextImage("%.4g" % l[0], 14, color, self.clearcolor, False)
		im=im.Mirror(False)
		w=im.GetWidth()
		h=im.GetHeight()
		id=im.GetData()
		pix=fromstring(id, 'B')
		pix=reshape(pix, (w, h, 3))
		glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
		glDrawPixelsub(GL_RGB, pix)
		glPopMatrix()

		glFlush()
		self.SwapBuffers()


	def editPlot(self, event):
		pn=self.selectPlot()
		if not pn:
			return
		plot=self.plots[pn]
		keys=plot.keys()
		for tag in self.dontedit:
			try:
				keys.remove(tag)
			except:
				pass
		l=askParameters(self, [{"Name":"Which Attribute?",
				                "Type":"Prompt",
				                "Value":keys}])
		if not l:
			return None
		an=l[0]	
		if plot.get(an):
			d=[{"Name":an,"Value":repr(plot[an])}]
		else:
			d=[{"Name":an,"Type":str}]		
		l=askParameters(self, d)
		if not l:
			return
		nv=eval(l[0])
		plot[an]=nv
		self.styles[plot['style']](pn)
		self.OnDraw()

	def delPlot(self, event):
		pn=self.selectPlot()
		if not pn:
			return
		del(self.plots[pn])
		self.OnDraw()

	def viewEdit(self, event=None):
		vp=self.viewpoint.tolist()
		forward=self.forward.tolist()
		up=self.up.tolist()
		size=self.extent
		depth=self.depthoffield
		l=askParameters(self, [{"Name":"Preset Name",
				                "Value":"Preset View"},
				               {"Name":"Viewpoint",						
				                "Value":vp},
				               {"Name":"Forward",
				                "Value":forward},
				               {"Name":"Up",
				                "Value":up},
				               {"Name":"View Extent",
				                "Value":size},
				               {"Name":"Depth",
				                "Value":depth}])
		if not l:
			return
		self.views[l[0]]={"vp":array(l[1]),"forward":array(l[2]), "up":array(l[3]),"ext":l[4], "depth":l[5]}
		self.presetView(l[0])

	def presetView(self, vn):
		if not self.views:
			self.report("No preset views")
			return	
		if not vn:
			if len(self.views.keys())==1:
				vn=self.views.keys()[0]
		if not vn:		
			l=askParameters(self, [{"Name":"Which View?",
						            "Type":"List",
						            "Value":self.views.keys()}])
			if not l:
				return
			vn=l[0]	
		v=self.views[vn]		
		self.viewpoint=v['vp'].copy()
		self.forward=v['forward'].copy()
		self.extent=v['ext']
		self.up=v['up'].copy()
		self.depthoffield=v['depth']
		self.OnDraw()

	def screenShot(self, fname=None):
		if not fname:
			l=askParameters(self, [{"Name":"File Name",
						            "Value":"GLScreenShot.jpg"}])
			if not l:
				return None
			fname=l[0]
		size = self.GetClientSize()
		glPixelStorei(GL_PACK_ALIGNMENT, 1)
		screen=array(glReadPixelsub(0,0, size.width, size.height, GL_RGB))
		if type(screen[0,0])!=ArrayType:
			screen=fromstring(screen.tostring(), 'B') 
			screen=reshape(screen, (size.width, size.height, 3))
		else:	
			screen=screen.astype('B')
		img=wx.EmptyImage(screen.shape[0], screen.shape[1])
		img.SetData(screen.tostring())
		img=img.Mirror(False)
		if fname.endswith('.jpg'):
			img.SaveFile(fname, wx.BITMAP_TYPE_JPEG)
		elif fname.endswith('.jpg'):
			img.SaveFile(fname, wx.BITMAP_TYPE_PNG)
		else:
			img.SaveFile(fname, wx.BITMAP_TYPE_BMP)



def testme():
	app = wx.PySimpleApp()
	bar = {'size':(600,600), 'style':wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE}
	frame = wx.Frame(None, -1, "Output Graph", **bar)
	frame.g = GraphGL(frame)
	frame.g.SetSize((600,600))
	frame.Show(True)
	im=uniform(0, 255, (60, 80, 3)).astype('B')
	#import mien.nmpml,  mien.parsers.fileIO, sys
	#fname=sys.argv[1]
	#h = mien.parsers.fileIO.get_read_type(fname)
	#doc = mien.parsers.fileIO.READERS[h](fname)
	#cell=doc.getElements("Cell")[0]
	#pts=cell.get_drawing_coords()
	t=(0,.8,0.0)
	#sec=reshape(pts, (-1, 8))
	#col=colorscale(arange(sec.shape[0]))
	a=array([[-175.61000061, -259.6000061 ,   59.65000153,    2.71000004],
		     [-137.        , -192.13000488,   53.11999893,    4.61000013],
		     [-137.        , -192.13000488,   53.11999893,    4.61000013],
		     [-144.58999634, -192.83999634,   54.34999847,    4.61000013],
		     [-137      , -189.69999695,   53.68000031,    2.98000002],
		     [-100      , -189.69999695,   53.68000031,    2.98000002],
		     [-100.41999817, -189.7,   53.22000122,    2.44000006],
		     [-80, -196.6499939 ,   53.25999832,    1.89999998]], dtype=float32)
	a[:,:3]=a[:,:3]-a[0,:3]
	frame.g.addFrustaPlot(a)
	dens=random.uniform(0,1,(2,2,2))
	#dens=array([[[.5]]])
	frame.g.addDensPlot(dens, edge=10)
	#pts2=array([[0,0,0],[4,0,0],[0,0,0],[0,4,0],[0,0,0],[0,0,4]])
	#frame.g.addPointPlot(pts2, color=t, width=5 )
	#frame.g.addLinesPlot(pts2, color=t, width=5, style="lines" )
	#col=colorscale(arange(pts.shape[0]))
	#frame.g.addSpherePlot(pts, color=t, colorlist=col )
	#frame.g.addSpherePlot(pts2, color=t, colorlist=col )
	#frame.g.addLabel(text="booga", loc=(0,0,0), charsize=10.0)
	#for s in ["foo", "1234", "12345", "123456", "1234567", "12345678", "123456789", "1234567890"]:
	#	i=float(len(s))-3
	#	n=frame.g.addImageLabel(text=s, pos='abs', border=i%2, loc=(0,i,i), size=16)
	#	print n, s
	#frame.g.addColorScale(min=-6, max=4)
	#im=makeTextImage('test2.gif', 16, (.1,.2,.3), (.8,.7,.6))
	#im=wx.Image('aff.tif')
	#im=makeCscale(array([-1.0, 2.4]), 256)
	#print im.GetWidth(), im.GetHeight()
	#frame.g.addImage(image=im, pos='abs', loc=(0,0,0), sizemode='coords', size=(50, 50.0), normal=array([1.0,0,0]))
	#pts=array([[-25, -25,0.0],[-25, 25,0.0],[25,25,0], [25, -25,0]])
	#frame.g.addImageLayer(pts, image=im)
	frame.g.OnDraw()
	app.MainLoop()

if __name__=='__main__':
	testme()