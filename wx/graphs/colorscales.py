
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
from mien.image.arrayops import array_to_image

import wx



def make_hotcolorscale():
	a=arange(0,100.3, 100.0/255)
	r=convert_type(255/(1.0 + exp(-1*(a-50)/2.0)), 'B')
	g=convert_type(255*exp(-.5*(((a-45)/10)**2))+r*exp(-.4*(100-a)), 'B')
	b=convert_type(255*exp(-.5*(((a-20)/10)**2))+r*exp(-.4*(100-a)), 'B')
	cspec=transpose(array([r,g,b]))
	colors=map(tuple, cspec)
	colors = map(lambda x: wx.Colour(*x), colors)
	return colors

hot_cs=make_hotcolorscale()

def make_grayscale():
	a=arange(0,256)
	cspec=transpose(array([a,a,a]))
	colors=map(lambda x: wx.Colour(*tuple(x)), cspec)
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
	colors=map(lambda x: wx.Colour(*tuple(x)), cspec)
	return colors

ind_cs=make_indexedcolorscale()

#classid = 0-15
# Left Long 225, 315, 45, 135, Med 225, 315, 45, 135, Right long 135,45,315,225,  med 135,45,315,225

#
dircolors={315:(255,40,0),45:(55, 255, 0),135:(0,255,215), 225:(200,0,230)}

classids=[[225,"Left", "long"],
          [315,"Left", "long"],
          [45,"Left", "long"],
          [135,"Left", "long"],
          [225,"Left", "medium"],
          [315,"Left", "medium"],
          [45,"Left", "medium"],
          [135,"Left", "medium"],
          [135,"Right", "long"],
          [45,"Right", "long"],
          [315,"Right", "long"],
          [225,"Right", "long"],
          [135,"Right", "medium"],
          [45,"Right", "medium"],
          [315,"Right", "medium"],
          [225,"Right", "medium"]]

def make_dircolors():
	from ccbcv.dircolors import _getAngleColor as angl
	#wx.Colours?
	#import the directional map from elsewhere
		#check which color is which and try out in python 	
	rng = arange(0,2*pi,pi/180)
	colors = map(angl, rng)#in radians every degree
	colors = [(int(255*t[0]),int(255*t[1]),int(255*t[2])) for t in colors]
	colors = map(lambda x: wx.Colour(*x), colors)
	return colors

dir_cs=make_dircolors()

def make_classcolorscale():	  

	colors=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
	for i in range(16):
		c=classids[i]
		base=dircolors[c[0]]
		if c[2]=="medium":
			colors[i]=(int(2.0*base[0]/3), int(2.0*base[1]/3), int(2.0*base[2]/3))
		else:
			colors[i]=base

	colors[16]=(40,40,40)
	colors=map(lambda x: wx.Colour(*tuple(x)), colors)
	return colors

def makeFade(rgb):
	a=arange(0,1.0003, 1.0/255)
	r=(rgb[0]*a).astype('b')
	g=(rgb[1]*a).astype('b')
	b=(rgb[2]*a).astype('b')
	cspec=transpose(array([r,g,b]))
	colors=map(tuple, cspec)
	colors = map(lambda x: wx.Colour(*x), colors)
	return colors

class_cs=make_classcolorscale()

def linterp(fr, to, vals, rmin, rmax):
	vals = vals - rmin
	vals = vals/(rmax-rmin)
	out = fr + (to - fr)*vals
	return out

def make_rgbcs():
	a=linspace(0, 400, 256)
	r = zeros_like(a)
	g = zeros_like(a)
	b = zeros_like(a)
	bmask = logical_and(a<=100, a>0)
	b[bmask] = linterp(30, 255, a[bmask], 0, 100)
	bgmask = logical_and(a>100, a<=200)
	b[bgmask] = linterp(255, 0, a[bgmask], 100, 200)
	g[bgmask] = linterp(0, 255, a[bgmask], 100, 200)
	grmask = logical_and(a>200, a<=300)
	g[grmask] = linterp(255, 0, a[grmask], 200, 300)
	r[grmask] = linterp(0, 255, a[grmask], 200, 300)
	rwmask = a>300
	r[rwmask] = 255
	v = linterp(0, 255, a[rwmask], 300, 400)
	g[rwmask] = v
	b[rwmask] = v
	cspec=transpose(array([r,g,b]))
	colors=map(tuple, cspec)
	colors = map(lambda x: wx.Colour(*x), colors)
	return colors


rgb_cs = make_rgbcs()	

colorscales={"hot":hot_cs, "rgb":rgb_cs, "indexed":ind_cs, "gray":gray_cs, "class":class_cs, "dir":dir_cs}



def gradecolor(c, a, r=None):
	rgb = (c.Red(), c.Green(), c.Blue())
	#print rgb
	m = max(rgb)
	br = 255 - m
	rgb = map(lambda x: x+br, rgb)
	cs = makeFade(rgb)
	a=convert_type(a,'b', r)
	z=[cs[x] for x in a]
	return z

def colorscale(a, scale="hot",  r=None):
	if type(r)==ArrayType or r!="absolute":
		a=convert_type(a,'B', r)
	cs=colorscales[scale]
	#print a
	z=[cs[x] for x in a]
	return z

def fadecolor(loc, degree=2.0):
	nc=[]
	for c in loc:
		r,g,b=int(c.Red()/degree), int(c.Green()/degree), int(c.Blue()/degree)
		c2=wx.Colour(r,g,b)
		nc.append(c2)
	return nc	

def iverseCol(col):
	r = 255 - col.Red()
	g = 255 - col.Green()
	b = 255 - col.Blue()
	return wx.Colour(r,g,b)
