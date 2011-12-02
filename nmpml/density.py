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

from mien.nmpml.basic_tools import NmpmlObject
from mien.math.array import cumsum, ravel, uniform, zeros, Float32, nonzero1d, take, array, rotate3D, row_stack


class SpatialField(NmpmlObject):
	'''Class for representing density or probability clouds in 3D space.'''
	
	_allowedChildren = ["Comments", "Data", "AbstractModel"]
	_requiredAttributes = ["Name", "Origin", "Edge"]
	_specialAttributes = []

	def getData(self):
		de = self.getElements("Data")
		if de:
			return de[0]
		else:
			print "Can't find a data element. Making an empty one"
			from mien.nmpml.data import newData
			attrs = {"Type":"sfield", "Edge":self.attrib("Edge"), "Origin":self.attrib("Origin")}
			a=array([[[]]])
			d = newData(a, attrs)
			self.newElement(d)
			return d

	def doAlignment(self, conv):
		d=self.getElements("Data")
		a=self.getElements("AbstractModel")
		if a:
			#FIXME: analytical fields aren't supported yet
			raise StandardError('No support of analytical fields yet')
		trans = [conv.get("Trans_x", 0.0), conv.get("Trans_y", 0.0), conv.get("Trans_z", 0.0)]
		scale = array([conv.get("Scale_x", 1.0), conv.get("Scale_y", 1.0), conv.get("Scale_z", 1.0)])
		rot = array([conv.get("Rot_x", 0.0), conv.get("Rot_y", 0.0), conv.get("Rot_z", 0.0)])
		if d:
			if any(rot):
				vects = row_stack([self.attributes.get("Vertical", (0,1,0.0)), 
					self.attributes.get("Depth", (0,0,-1.0)),
					self.attrib("Origin")
					])
				vects=rotate3D(vects, rot)
				self.setAttrib("Vertical", vects[0,:].tolist())
				self.setAttrib("Depth", vects[1,:].tolist())
				self.setAttrib("Origin", vects[2,:].tolist())
			if any(scale!=1.0):
				e=array(self.attrib("Edge"))*scale
				o=array(self.attrib("Origin"))*scale
				self.setAttrib('Origin', o.tolist())	
				self.setAttrib('Edge', e.tolist())	
			if any(trans):
				o=array(self.attrib("Origin"))+trans
				self.setAttrib('Origin', o.tolist())

	
	def setAttrib(self, a, v, inherit=False):
		'''set attributes key a to v, with cast to python datatypes'''
		NmpmlObject.setAttrib(self, a, v, inherit)
		if a in ["Origin", "Edge"]:
			d=self.getElements("Data")
			d[0].setAttrib(a, v)
		

	def uniformSample(self):
		d=self.getElements("Data")
		if d:
			return d[0].getData()
		a=self.getElments("AbstractModel")
		if a:
			#FIXME: analytical fields aren't supported yet
			raise StandardError('No support of analytical fields yet')


ELEMENTS={"SpatialField":SpatialField}

'''This module provides functions for calculating density estimates for neural varicosity data,
for converting these estimates into discreet representiantions, and for extracting statistics 
from the representations. The algorithms used here are reimplementations of those published in 
Jacobs and Theunissen, J. Neuroscience, 1996

Usage:

densityTools command [arg1 arg2 ...] 

Allowed commands:

help - print this message (args ignored)

collect - write a mat file named arg1 containing an Nx4 array "affdata" specifying all the 
	varicosities defined in the neuroleucida files named in the remaining arguments

mat2dens - convert every mat file named as an arg to a Theunissen-style .denstiy file, these
	mat files must contain an (x,y,z) three D array (not the similar to those
	written by "map", not those written by "mat"

estimate - write a mat file named arg1 containing samples from a DensityEstimate 
	(defined in this module, using the Theunissen 96 estimator) instance for
	the varicosities defined by the remaining arguments, which may be a list af
	asc files, or a single mat file (written by the "mat" command of this
	module). In the latter case, the file name must end with ".mat" The samples
	are taken for a a 100x100x100 voxel cube, with voxel edge length 4.2
	microns, and most negative corner at [-161.89,-298.07,-131.32]
	(Theunissen's default values, used in CCB comp density files). The samples
	are stored in a 3D array named "density"

stats - arg1 should be a mat file containing a 100^3 array (e.g. written by "estimate"
	or by Alex D's GMM code. This function prints the max, center of mass,
	and integral of the density function. The same edge length and origin mentioned 
	for "estimate" are used here.

compare - arg1 and arg2 should be mat files (of the same type as for "stats"). This 
	function prints the distance between their centers of mass, and their overlap 
	(again using Theunissen's method of calculation)


add - arg1 is the name of a file to write to. The remaining args should be mat files 
	written by "estimate". Writes data to the new file that is the sum of the listed 
	datafiles.

subtract - arg1 is a filname for writing the result. Arg2 and arg3 are mat files 
	written by "estimate". Writes data to the new file that is arg2-arg3. Densities
	less than zero are truncated at zero.

norm - arg1 is a number specifying the desired max density. Arg2 is a file name
	writes a new file with "norm(arg1)" added to the name, in which the density is scaled 
	so that the maximum has the indicated value

normi - arg1 is a number specifying the desired total (integrated) density. 
	arg2 is a file name. Like norm, but scales the total density

'''

#from sys import argv, exit
#import os, re, mien.nmpml
#from gicMath.array import *
#from datafiles.filewriters import hash2mat
#from datafiles.filereaders import readmat
#
#EDGE=4.2
#EXTENT=(100,100,100)
#ORIGIN=array((-161.89,-298.07,-131.32))
#
#def dContrib(dat, pt, gw):
#	dist=eucd(dat[:,:3], pt)
#	dens=dat[:,3]
#	dc=(dens/(gw**3*15.7496))*exp((-1*dist**2)/(2*gw**2))
#	return dc.sum()
#	
#def densityEstimate(dat, gw=7.0):
#	'''dat (Nx4 array), gw (float=7.0) -> array (of size EXTENT) of floats)
#Estimate the density of points in dat, using the Theunissen 1996 method with a fixed gaussian width 
#of gw (in microns). Sample this estimate in a grid of (extent) voxels with side length (edge) microns
#anchored at (origin). Return an array of the samples'''
#	est=zeros(EXTENT, Float64)
#	for xi in range(EXTENT[0]):
#		print xi
#		for yi in range(EXTENT[1]):
#			for zi in range(EXTENT[2]):
#				x=EDGE*xi+ORIGIN[0]
#				y=EDGE*yi+ORIGIN[1]
#				z=EDGE*zi+ORIGIN[2]
#				pt=array([x,y,z])
#				est[xi,yi,zi]=dContrib(dat, pt, gw)
#	print est.max()			
#	return est			
#				
#
#def matArray(fn):
#	[note, date, objects]=readmat(fn)
#	a=objects.values()[0]
#	return a
#
#def varicFromFile(fname):
#	d=readNL(fname)
#	fid=d.getElements("Fiducial")
#	pts=[x for x in fid if x.attrib("Style") in ["spheres", "points"] and not x.point_labels and x.attrib("MarkerType") in [None, "OpenCircle"]]
#
#	if len(pts)!=1:
#		print "Warning: got %i varicosity lists for %s" % (len(pts), fname)
#	fid=pts[0]
#	name=os.path.splitext(os.path.split(fname)[-1])[0]
#	fid.attributes["Name"]=name
#	return fid
#
#def getVaricosities(files):
#	'''files (list of strings) -> Nx4 array
#Extracts the x,y,z,d data representing varicosities from each file in the list 
#These should be Neuroleucida .asc files. THe data are returned in an array''' 
#	allpts=None
#	for f in files:
#		fid=varicFromFile(f)
#		pts=fid.getPoints()
#		print "got %i points for %s" % (pts.shape[0], f)
#		if allpts==None:
#			allpts=pts
#		else:
#			allpts=concatenate([allpts, pts])
#	return allpts
#
#def writeMatFile(files):
#	if os.path.exists(files[0]):
#		print "Refusing to overwrite %s" % files[0]
#		exit()
#	pts=getVaricosities(files[1:])
#	hash2mat(files[0],  {"affdata":pts})
#
#
#def getHelp(args):
#	print __doc__
#
#def writeDensityFile(fn, a, thresh=.000001, norm=None):
#	of = open(fn, 'w')
#	of.write("%.6g  #Max Density\n" % a.max())
#	of.write("0  #Directional tuning (meaningless)\n")
#	if norm:
#		a=a*norm*(1.0/a.max())
#	if thresh:
#		nz=nonzero1d(a>thresh*a.max())
#		#print nz[0].min(), nz[0].max()
#		#print nz[1].min(), nz[1].max()
#		#print nz[2].min(), nz[2].max()
#		xr=range(nz[0].min(), nz[0].max())
#		yr=range(nz[1].min(), nz[1].max())
#		zr=range(nz[2].min(), nz[2].max())
#	else:
#		size=a.shape
#		xr=range(size[0])
#		yr=range(size[1])
#		zr=range(size[2])
#	for x in xr:
#		for y in yr:
#			for z in zr:
#				v=a[x,y,z]
#				of.write("%i %i %i %.6g 0 0\n" % (x,y,z,v))
#	of.close()			
#
#def mat2dens(files):
#	for fname in files:
#		[note, date, objects]=readmat(fname)
#		fname=os.path.splitext(fname)[0]+".density"
#		a=objects.values()[0]
#		writeDensityFile(fname, a)
#
#def makeEstimate(files):
#	efn=files[0]
#	if os.path.exists(efn):
#		print "Refusing to overwrite %s" % efn
#		exit()
#	if files[1].endswith('.mat'):
#		fc=readmat(files[1])
#		dat=fc[-1]["affdata"]
#	else:
#		dat=getVaricosities(files[1:])
#	est=densityEstimate(dat)
#	hash2mat(efn,  {"density":est})
#
#
#def getCM(a):
#	i=indices(a.shape)
#	tw=a.sum()
#	dw=a*i
#	x=dw[0].sum()/tw
#	y=dw[1].sum()/tw
#	z=dw[2].sum()/tw
#	loc=array([x,y,z])*EDGE+ORIGIN
#	return tuple(loc)
# 
#def getStats(fn):
#	a=matArray(fn[0])
#	if not a.shape==EXTENT:
#		print "Only arrays of shape %s will work with this function" % EXTENT
#		exit()
#	print "Max voxel value = %.6g" % a.max()
#	print "Total density = %.6g" % a.sum()
#	print "Center of mass at %s" % (str(getCM(a)),)
#
#
#def measureOverlap(fn):
#	a=matArray(fn[0])
#	b=matArray(fn[1])
#	if a.shape!=EXTENT or b.shape!=EXTENT:
#		print "Only arrays of shape %s will work with this function" % EXTENT
#		exit()
#	cm1=getCM(a)
#	cm2=getCM(b)
#	cmd=eucd(cm1, cm2)
#	print "Center of mass 1 at %s" % (str(cm1),)
#	print "Center of mass 2 at %s" % (str(cm2),)
#	print "Distance between centers of mass %.4g microns" % cmd
#	join=maximum(a,b)
#	over=minimum(a,b)
#	ol=over.sum()/join.sum()
#	print "Overlap is %.3f perecent" % (ol*100,)
#
#def addFiles(fns):
#	efn=fns[0]
#	if os.path.exists(efn):
#		print "Refusing to overwrite %s" % efn
#		exit()
#	a=matArray(fns[1])
#	for fn in fns[2:]:
#		b=matArray(fn)
#		a=a+b
#	hash2mat(efn,  {"density":a})
#
#		
#
#def subtractFiles(fns):
#	efn=fns[0]
#	if os.path.exists(efn):
#		print "Refusing to overwrite %s" % efn
#		exit()
#	a=matArray(fns[1])
#	b=matArray(fns[2])
#	a=a-b
#	a=maximum(a, zeros(a.shape))
#	hash2mat(efn,  {"density":a})
#
#		
#def normalizeMax(fns):
#	nmax=float(fns[0])
#	a=matArray(fns[1])
#	nfn=os.path.splitext(fns[1])[0]+'.norm%.4f.mat' % nmax
#	omax=a.max()
#	a=a*nmax/omax
#	hash2mat(nfn,  {"density":a})
#
#
#		
#def normalizeAll(fns):
#	nmax=float(fns[0])
#	a=matArray(fns[1])
#	nfn=os.path.splitext(fns[1])[0]+'.normi%.4f.mat' % nmax
#	omax=a.sum()
#	a=a*nmax/omax
#	hash2mat(nfn,  {"density":a})
#
#COMMANDS={'help':getHelp,
#			'collect':writeMatFile,
#			'estimate':makeEstimate,
#			'mat2dens':mat2dens,
#			'stats':getStats,
#			'compare':measureOverlap,
#			'add':addFiles,
#			'subtract':subtractFiles,
#			'norm':normalizeMax,
#			'normi':normalizeAll}
#
#if __name__=='__main__':
#	try:
#		com=sys.argv[1]
#		args=sys.argv[2:]
#		if not COMMANDS.has_key(com):
#			raise
#	except:
#		com="help"
#		args=[]
#	COMMANDS[com](args)
#
