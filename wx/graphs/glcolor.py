
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
from mien.math.array import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLE import *
from OpenGL.GLUT import *
import wx
from wx import glcanvas
from mien.wx.image import *

def make_hotcolorscale():
	a=arange(0,100.3, 100.0/255)
	r=convert_type(255/(1.0 + exp(-1*(a-50)/2.0)), 'B')
	g=convert_type(255*exp(-.5*(((a-45)/10)**2))+r*exp(-.4*(100-a)), 'B')
	b=convert_type(255*exp(-.5*(((a-20)/10)**2))+r*exp(-.4*(100-a)), 'B')
	cspec=transpose(array([r,g,b]))
	cspec=cspec.astype(Float32)/255
	colors=map(tuple, cspec)
	return colors

hot_cs=make_hotcolorscale()

def _linterp(pt1, pt2, ptt):
	p3= pt1+ (pt2-pt1)*ptt
	return p3

def _getAngleColor(a):
	# rcent = pi/4
	# gcent = 5*pi/4
	# bcent = 7*pi/4
	rcent = 0 + pi/6
	gcent = 2*pi/3 +pi/6
	bcent = 4*pi/3 +pi/6
	if a <= rcent or a >= bcent:
		rr = (2*pi - bcent)
		ptr = ((a+rr) % (2*pi))/(rcent+rr)
		col = _linterp( array((0.0, 0.0, 1.0)), array((1.0, 0.0, 0.0)), ptr)
	elif a<= gcent:
		a = a - rcent
		gcent = gcent - rcent
		ptg = a/gcent
		col = _linterp( array((1.0, 0.0, 0.0)), array((0.0, 1.0, 0.0)), ptg)
	else:
		a = a - gcent
		bcent = bcent - gcent
		ptb = a/bcent
		col = _linterp( array((0.0, 1.0, 0.0)), array((0.0, 0.0, 1.0)), ptb)
	col = vnorm(vnorm(col)**.6)
	#col = col/col.max()
	return tuple(col)

def make_dircolors():
	#from ccbcv.dircolors import _getAngleColor as angl
	rng = arange(0,2*pi,pi/180)
	colors = map(_getAngleColor, rng)#in radians every degree
	colors.append((.5,.5,.5))
	print 'original len=', len(colors)
	return colors

dir_cs=make_dircolors()

def make_bgrcolorscale():
	cspec = zeros( (256,3) )
	cspec[0:85,2] = linspace(10, 255, 85)
	cspec[85:145,1] = linspace(60, 255, 60)
	cspec[145:205,0] = linspace(60, 255, 60)
	cspec[205:256,:] = linspace(128,255, 51)[:, newaxis]
	cspec=cspec.astype(Float32)/255.0
	colors=map(tuple, cspec)
	return colors

bgr_cs=make_bgrcolorscale()

def make_bgcyrcolorscale():
	cspec = zeros( (256,3) )
	cspec[0:55,2] = linspace(10, 255, 55)
	cspec[55:105,1] = linspace(60, 255, 50)
	cspec[105:155,1:3] = linspace(60, 255, 50)[:, newaxis]
	cspec[155:205,0:2] = linspace(60, 255, 50)[:, newaxis]
	cspec[205:256,0] = linspace(60,255, 51)
	cspec=cspec.astype(Float32)/255.0
	colors=map(tuple, cspec)
	return colors

bgcyr_cs=make_bgcyrcolorscale()

def make_grayscale():
	a=arange(0,256)
	cspec=transpose(array([a,a,a]))
	cspec=cspec.astype(Float32)/255
	colors=map(tuple, cspec)
	return colors

gray_cs=make_grayscale()

def make_indexedcolorscale():
	a=arange(0,256)
	incr=7
	a=a+1
	b = array([x % incr for x in a])
	rem = (a/7).astype(Int16)
	g=array([x % incr for x in rem])
	rem = (rem/7).astype(Int16)
	r = array([x % incr for x in rem])
	level=int(255.0/(incr-1))
	r=(r)*level
	g=(g)*level
	b=(b)*level
	cspec=transpose(array([r,g,b]))
	cspec=cspec.astype(Float32)/255
	colors=map(tuple, cspec)
	return colors

ind_cs=make_indexedcolorscale()

#classid = 0-15
# Left Long 225, 315, 45, 135, Med 225, 315, 45, 135, Right long 135,45,315,225,  med 135,45,315,225

#

def makeFade(rgb):
	a=arange(0,1.0003, 1.0/255)
	r=(rgb[0]*a).astype('B')
	g=(rgb[1]*a).astype('B')
	b=(rgb[2]*a).astype('B')
	cspec=transpose(array([r,g,b]))
	cspec=cspec.astype(Float32)/255
	colors=map(tuple, cspec)
	return colors


colorscales={"hot":hot_cs, "indexed":ind_cs, "gray":gray_cs, "bgr":bgr_cs, "bgcyr":bgcyr_cs, "dir":dir_cs}

def gradecolor(rgb, a, r=None):
	m = max(rgb)
	br = 255 - m
	rgb = map(lambda x: x+br, rgb)
	cs = makeFade(rgb)
	a=convert_type(a,'B', r)
	z=[cs[int(x)] for x in a]
	return z

def colorscale(a, scale="hot",  r=None):
	if type(r)==ArrayType or r!="absolute":
		a=convert_type(a,'B', r)
	cs=colorscales[scale]
	z=[cs[int(x)] for x in a]
	return z

def fadecolor(loc, degree=2.0):
	nc=[]
	for c in loc:
		r,g,b=c[0]/degree, c[1]/degree, c[2]/degree
		c2=(r,g,b)
		nc.append(c2)
	return nc	

def iverseCol(col):
	r = 1.0 - col[0]
	g = 1.0 - col[1]
	b = 1.0 - col[2]
	if (r,g,b)==(0.0,0.0,0.0):
		return (0,0,.7)
	return (r,g,b)

def materialColor(c):
	a=array(c)
	amb=a/4.0
	dif=a/2.0
	glMaterial(GL_FRONT_AND_BACK, GL_AMBIENT, amb.tolist()+[1.0])
	glMaterial(GL_FRONT_AND_BACK, GL_DIFFUSE, dif.tolist()+[1.0])
	glMaterial(GL_FRONT_AND_BACK, GL_SPECULAR, a.tolist()+[1.0])
	glMaterial(GL_FRONT_AND_BACK, GL_SHININESS, 10.0)


def alphaColor(c, ap):
	a=array(c)
	l=list(c)
	z=[0,0,0]
	glMaterial(GL_FRONT_AND_BACK, GL_AMBIENT, l+[ap])
	glMaterial(GL_FRONT_AND_BACK, GL_DIFFUSE, z+[ap])
	glMaterial(GL_FRONT_AND_BACK, GL_SPECULAR, z+[ap])
	glMaterial(GL_FRONT_AND_BACK, GL_SHININESS, 0.0)



def GLColorBrowser(master, dict, control):
	dlg=wx.ColourDialog(master)
	dlg.GetColourData().SetChooseFull(True)
	if dlg.ShowModal() == wx.ID_OK:
		data = dlg.GetColourData()
		tup = data.GetColour().Get()
		tup =tuple([x/255.0 for x in tup])
		dict["Value"]=tup
		control.SetValue(str(tup))	
	dlg.Destroy()


def glcolor2wxcolor(c):
	r,g,b=c
	r=int(round(r*255))
	g=int(round(g*255))
	b=int(round(b*255))
	return wx.Colour(r,g,b)


def makeTextImage(text, font, fgc=(1.0,1.0,1.0), bgc=(0,0,0), bor=True):
	bgc=glcolor2wxcolor(bgc)
	fgc=glcolor2wxcolor(fgc)
	im=wx.EmptyBitmap(100, 100)
	dc = wx.MemoryDC()
	dc.SelectObject(im)
	font=wx.Font(font, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
	dc.BeginDrawing()
	dc.SetFont(font)
	tw, th = dc.GetTextExtent(text)
	if bor:
		pad=4
	else:
		pad=1
	im=wx.EmptyBitmap(tw+2*pad, th+2*pad)
	dc.SelectObject(im)
	dc.SetBackground(wx.Brush(bgc, wx.SOLID))
	dc.SetTextBackground(bgc)
	dc.SetBrush(wx.Brush(bgc, wx.SOLID))
	dc.SetPen(wx.Pen(fgc, 1))
	dc.SetTextForeground(fgc)
	dc.Clear()
	if bor:
		dc.DrawRectangle(0, 0, tw+2*pad, th+2*pad)
	dc.DrawText(text, pad, pad)
	dc.EndDrawing()
	return wx.ImageFromBitmap(im)


def makeCscale(labels, colors, h, bgc=(0,0,0)):
	bgc=glcolor2wxcolor(bgc)
	ran=["%.4g" % (min(labels),), "%.4g" % (max(labels),)]
	tick=h/len(colors)
	loc=h
	step=h/len(colors)
	im=wx.EmptyBitmap(100, 100)
	dc = wx.MemoryDC()
	dc.SelectObject(im)
	font=wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
	dc.BeginDrawing()
	dc.SetFont(font)
	tw, th = dc.GetTextExtent(ran[0])
	tw2, th = dc.GetTextExtent(ran[1])
	tw=max(tw, tw2)
	w=tw+4+tick
	im=wx.EmptyBitmap(w, h)
	dc.SelectObject(im)
	dc.SetBackground(wx.Brush(bgc, wx.SOLID))
	dc.SetTextBackground(bgc)
	dc.SetTextForeground(wx.Colour(0,200,250))
	dc.Clear()
	dc.DrawText(ran[0],0, loc-th-2)
	dc.DrawText(ran[1],0, 2)
	for i in range(len(colors)):
		c=glcolor2wxcolor(colors[i])
		dc.SetPen(wx.Pen(c, 1))
		dc.SetBrush(wx.Brush(c, wx.SOLID))
		dc.DrawRectangle(w-tick, loc-step*i, tick, step)
	dc.EndDrawing()
	return wx.ImageFromBitmap(im)

c=wx.Colour(0,245,0)
ColorType=type(c)

def convertColor(c, mode='py'):
	try:
		if type(c)==ColorType:
			pass
		elif type(c) in [str, unicode]:
			c=apply(wx.Colour, c)
		elif type(c) in [tuple, list]:
			c=array(c)
			if all(c>=0.0) and all(c<=1.0):
				c=c*255
			c=apply(wx.Colour, c)
	except:
		print c
		raise
		print "can't identify color"
		c=wx.Colour(255,255,255)
	if mode=='gl':
		c=c.Get()
		c=tuple(array(c)/255.0)
	elif mode=='py':	
		c=c.Get()
	return c

if __name__=="__main__":
	app=wx.PySimpleApp()
	im=makeCscale(array([-1,2.4]), 300)
	im.SaveFile('test.bmp', wx.BITMAP_TYPE_BMP)