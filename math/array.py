
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
from types import *
from time import time
from numpy import *
from numpy.random import normal, uniform, randint, seed	
from numpy import round

arraytype=type(zeros(1))

def nonzero1d(a):
	return nonzero(a)[0]
		
def armax(a):
	if NUMARRAY:
		return a.max()
	else:
		return max(ravel(a))

def armin(a):	
	return a.min()

def arsum(a):	
	return a.sum()
	
def armean(a):
	return a.mean()

def arbyteswap(a):	
	return a.byteswap()

SetType = type(set)

ArrayType=type(zeros(1))

SIMPLE_TYPES = [StringType, UnicodeType, FloatType, IntType]
LIST_TYPES = [ArrayType, ListType, TupleType, SliceType, XRangeType,SetType]


for q in ['UInt8','Int8','Int16','UInt16', 'Int32', 'UInt32','Int64','UInt64','Float32','Float64']:
	exec("%s = %s" % (q, q.lower()))

Complex32=complex64
Complex64=complex128
NewAxis=newaxis

typecoderanges={UInt8:(0,255),
				Int8:(-128, 127),
				Int16:(-32768, 32767),
				Int32:(-2147483648,2147483647),
				Int64:(-9223372036854775808,9223372036854775807),
				Float32:(-3.4e38, 3.4e38),
				Float64:(-1.7976931e308, 1.7976931e308),
				Complex32:(-3e38, 3e38),
				Complex64:(-1.7976931e308, 1.7976931e308),
				'B':(0,255),
				'1':(-128, 127),
				's':(-32768, 32767),
				'i':(-2147483648,2147483647),
				'l':(-9223372036854775808,9223372036854775807),
				'f':(-3.4e38, 3.4e38),
				'd':(-1.7976931e308, 1.7976931e308),
				'F':(-3e38, 3e38),
				'D':(-1.7976931e308, 1.7976931e308),
				}

precisionlimits={Float32:1e-43,
				 Float64:1e-323,
				 Complex32:1e-43,
				 Complex64:1e-323
				 }

# double values of>= 3e-324 return nonzero, but are not reliable below
# 1e-323. e.g. 3e-324 is represented as  4.94065646e-324
# float32 has a similar (but worse) problem below 1e-43
# but returns nonzero down to 1.40129846e-45


def reverseArray(a):
	return take(a, arange(len(a)-1, -1, -1))
	
 
def mean(a, axis=0):
	return sum(a, axis)/a.shape[axis]

def stddev1(a):
	m=mean(a, 1)
	return sqrt(sum((a-m[:,NewAxis])**2, 1)/(a.shape[1]-1))

def sizeoftype(typecode):
	l=len(zeros(1,typecode).tostring())
	min, max = typecoderanges[typecode]
	return [l, min, max] 
		  
def maptorange(a, r, r2=None):
	'''maptorange(a, r,r2=None)
maps the array a onto the range r. If r2 is specified, maps from the range
r2 onto r, clipping a if needed'''
	a=a.astype(Float32)
	if r2!=None:
		maxi=r2[1]
		mini=r2[0]
		a=clip(a, mini, maxi)
	else:
		maxi=a.max()
		mini=a.min()
		
	if abs(mini-maxi)<(r[1]-r[0])/100000.0:
		a=ones_like(a)*mini+(r[1]-r[0])/2
		return a
	a=(a-mini)/(maxi-mini)
	
	a=a*(r[1]-r[0])
	a=a+r[0]
	a = a.astype(Float32)
	return a.astype(Float32)

def cdiff(a, fs =1.0):
	''' average discrete difference approximation to the derivative of the 1D array a. If fs is specified it is the sampling frequency of a in Hz. By default, fs is one, so the unmodified differences of a are returned. The algorithm assumes that the differences "off the ends" of the data set are 0'''
	diff = concatenate([array([0], a.dtype), a[1:]-a[:-1],array([0], a.dtype)])
	diff = (diff[:-1]+diff[1:])/2.0
	if fs != 1.0:
		diff = diff*fs
	return diff

def cdiff2(a, fs=1.0):
	'''second order derivative of the 1D array a, using centered differences. fs is as for cdiff'''
	diff = cdiff(a, fs)
	diff = concatenate([array([0], a.dtype), diff[1:]-diff[:-1],array([0], a.dtype)])
	diff = (diff[:-1]+diff[1:])/2.0
	return diff
	

def interpolate(a, d):
	'''a(1D array), d(1D array) => array (of type a and shape d)
evaluate the array a at indices specified in d. These may be fractional,
in which case linear interpolation is applied. The indices may not
exceed the dimensions of a (so if a has length 15, interpolate(a, [2.3,4.6])
is ok, but interpolate(a, [1,16.1]) is an error. If d is of integer
type, interpolate(a,d) is equivalent to take(a, d) but slightly slower
(so use take instead)'''
	z=take(a, d.astype(int32))
	z=z.astype(d.dtype.char)
	rems=d%1
	for i in nonzero1d(rems):
		ind=int(d[i])
		last=a[ind]
		if ind+1 >=len(a):
			next=a[-1]+(a[-1]-a[-2])
		else:
			next=a[ind+1]
		percent=rems[i]
		z[i]=percent*(next-last)+last
	return z
	
# def array_resample(a, from_samp, to_samp, interp=True):
# 	''' a (1D array), from_samp(float), to_samp(float) => 1D array
# Assuming a has sampling interval(not rate) from_samp, sample a with sampling
# interval to_samp, using linear interpolation if needed when interp is True, otherwise, use sample and hold.'''
# 	samp_r = float(to_samp)/from_samp
# 	if not (float(to_samp)/from_samp) % 1:
# 		#even downsample:
# 		samp_r=int(samp_r)
# 		domain=arange(0, len(a), samp_r)
# 		return take(a, domain)
# 	else:
# 		domain=arange(0, len(a), samp_r)
# 		if interp:
# 			return interpolate(a, domain)
# 		else:
# 			return a[domain.astype(int32)]

def array_resample(a, from_samp, to_samp, interp=True):
	''' a (1D array), from_samp(float), to_samp(float) => 1D array
Assuming a has sampling interval(not rate) from_samp, sample a with sampling
interval to_samp, using linear interpolation if needed when interp is True, otherwise, use sample and hold.'''
	samp_r = to_samp/from_samp
	domain=arange(0, len(a)-1+.5*samp_r, samp_r)
	if domain[-1]>=len(a):
		domain=domain[:-1]
	#nsamps = int(round(  a.shape[0]*(from_samp/float(to_samp)) ))
	#domain = linspace(0, a.shape[0]-1, nsamps)
	if samp_r % 1 and 1/samp_r % 1 and interp:
		return interpolate(a, domain)
	else:
		return a[domain.astype(int32)]			
	

def timestretch(a, fac, anchor=0):
	'''a (1D array), fac (float), anchor (int=0)=> 1D array
returns an array the same length as a that has been stretched or compressed in 
time according to fac (values less than 1 are compressions, values greater than 
1 are stretches.). If anchor is 0, the middle sample of a remains unchanged. If
anchor is negative, the first sample remains unchanged, and if anchor is possitive,
the last sample. In the event of compression, a is extended by duplicating the 
first and last sample as needed before compression'''
	if fac==1.0:
		return a.copy()
	b=array_resample(a, fac, 1.0)
	if len(b)<len(a):
		pad=len(a)-len(b)
		if anchor==0:
			b=concatenate([ones(pad/2)*b[0], b])
			b=concatenate([b, ones(len(a)-len(b))*b[-1]])
		elif anchor>0:
			b=concatenate([ones(pad)*b[0], b])
		else:
			b=concatenate([b,ones(pad)*b[-1]])
	elif len(b)>len(a):
		if anchor==0:
			si=(len(b)-len(a))/2
		elif anchor<0:
			si=0
		else:
			si=len(b)-len(a)
		b=b[si:si+len(a)]
	return b	

def clip(a, mi=None, ma=None):
	a = a.copy()
	if not mi == None:
		a = where(a<mi, mi, a)
	if not ma == None:
		a = where(a>ma, ma, a)
	return a	
		

def shift(a, i, axis=0):
	'''array, int, axis=0 => array
shift the array int places right along axis "axis". The value at a[0] is
duplicated. If i is negative, shift to the left.'''
	if i==0:
		return a
	if axis!=0:
		z=range(len(a.shape))
		z[0]=axis
		z[axis]=0
		z=tuple(z)
	else:
		z=None
	if z:	
		a=transpose(a, z)
	s=list(a.shape)
	s[0]=abs(i)
	s=tuple(s)
	if i>0:
		fill = ones(s, a.dtype.char) * a[0]
		a=concatenate((fill, a[:-1*i]))
	elif i<0:
		fill = ones(s, a.dtype.char) * a[-1]
		a=concatenate((a[-1*i:], fill))
	if z:
		a=transpose(a, z)
	return a
	
def shiftND(a, v):
	'''Return a new array. Construct it by shifting the N D array a using the N vector v such that the shift allong the ith axis of a is specified by the ith element of v. Padding is done using the mean value of a'''
	q=ones_like(a)*a.mean()
	sslice=[]
	tslice=[]
	for i,s in enumerate(a.shape):
		if v[i]==0:
			sl=slice(0, s)
			sslice.append(sl)
			tslice.append(sl)
		elif v[i]>0:
			sslice.append(slice(0, -v[i]))
			tslice.append(slice(v[i], s))
		else:
			sslice.append(slice(-v[i], s))
			tslice.append(slice(0, v[i]))
	q[tslice]=a[sslice]
	return q
	
	
def bracket(a, val):
	'''array, float => int | (int, float)
if array is a monotonic sequence, returns the index at which array equals float.
the return value can have two forms: ints occur if the array is exactly
equal to the value, and is the first index of the value. The ints -1 and
-len(a) occur if the value falls outside the range of the array. Tuples
occur if two array values bracket the target value. The int is the index
before crossing, and the float is the fraction of the distance to the next
value at which the crossing occurs'''
	if val>max(a):
		if a[0]<a[-1]:
			return -1
		else:
			return -len(a)
	elif val<min(a): 
		if a[0]<a[-1]:
			return -len(a)
		else:
			return -1
	elif len(nonzero1d(a == val))>0:
		return nonzero1d(a == val)[0]
	else:
		if a[0]<a[-1]:
			i = max(nonzero1d(a<val))
		else:
			i = max(nonzero1d(a>val))
		s = a[i+1] - a[i]
		x = val - a[i]
		p = x/s
		return (i, p)
			
def uniformsample(a, dt, interp=True):
	'''(N,Q) |Q>=2 array, float => (M,Q-1) array
convert an array of x/y pairs to a 1D array that uniformly samples the represented function with interval dt. Uses linear interpolation if interp is True, otherwise uses sample and hold. If there are more than 2 columns, all are sampled using the first column as x'''
	a = take(a, argsort(a[:,0]), 0)
	xa = arange(a[0,0], a[-1,0]+.5*dt,dt)
	ya= zeros((len(xa),a.shape[1]-1)).astype(a.dtype)
	if not interp:
		ins=a[:,0].searchsorted(xa, side='left')
		ya=a[ins,1:]	
	else:
		ins=a[:,0].searchsorted(xa)
		ins=where(ins<a.shape[0], ins, a.shape[0]-1)
		hit=a[ins,0]==xa
		hi=nonzero1d(hit)
		ya[hi,:]=a[ins[hi], 1:]
		m=nonzero1d(logical_not(hit))
		mi=ins[m]
		ub=a[mi,0]
		lb=a[mi-1,0]
		v=xa[m]
		p=(v-lb)/(ub-lb)
		p=reshape(p, (-1,1))
		ub=a[mi,1:]
		lb=a[mi-1,1:]
		ya[m,:]=lb+(ub-lb)*p
	return ya	

def sequential_windows(a, L):
	'''array, float => 2D array'''
	N=len(a)
	if N<=L:
		raise StandardError("Must have more samples to window than window width!")
	windind=arange(N-L)
	out=zeros((N-L, L), a.dtype.char)
	for i in windind:
		out[i]=a[i:i+L]
	return out
	
def convert_type(a, typecode, r=None):
	if typecode=="f" or typecode=="d":
		return a.astype(typecode)
	a=maptorange(a, sizeoftype(typecode)[1:], r)
	return a.astype(typecode)

def read_from_string(s, typ , bs=0):
	unsigned=0
	s=fromstring(s, typ)
	if bs:
		s=arbyteswap(s)
	if unsigned:
		n=sizeoftype(typ)[2]
		s=s+n*(s<0)
	return s

def castToArray(pnt):
	'''if pnt is not an array, try to make it into one'''
	if type(pnt)!=ArrayType:
		pnt=array(pnt)
	return pnt	

def eucd(pnt, pnt2):
	'''pt1, pt2 => dist
returns the euclidean distance between points. Points may be  vectors (one D
arrays) of 1 or more floats, or arrays of Nxd floats. If both values are 2D,
they must have the same shape, and an array of N pairwise distances is
returned. If both are 1D, they must have the same length, a single float
is returned. If the first is 1D, and the second is an Nxd array, the vector
must have length d, and an array of N distances (the distance from the first
point to each point in the array) is returned.'''
	pnt, pnt2 = map(castToArray, [pnt, pnt2])
	if len(pnt.shape)>1:
		diff=(pnt2-pnt)**2
		return sqrt(sum(diff, 1))
	elif len(pnt2.shape)>1:
		pnt = resize(array(pnt), (pnt2.shape[0], len(pnt)))
		diff=(pnt2-pnt)**2
		return sqrt(sum(diff, 1))		
	else:
		pnt = array(pnt)
		pnt2= array(pnt2)
		diff = (pnt2-pnt)**2
		return sqrt(sum(diff))

def isConstant(a):
	'''a (1D array)  => bool
if a contains only one value, return True, else False.'''
	v1 = a[0]
	others = take(a, nonzero1d(a!=v1))
	if others:
		return False
	return True
	
def isBinary(a, axis=0):
	'''a (1D array)  => 2tuple or None
if a contains only two values, return a tuple of these.
Otherwise, return None'''
	v1 = a[0]
	others = take(a, nonzero1d(a!=v1))
	if not len(others):
		return None
	v2 = others[0]
	more = nonzero1d(others!=v2)
	if len(more)>0:
		return None
	else:
		return (v1,v2)

def text_to_array(file):
	l = open(file).readlines()
	i = 0
	while 1:
		if len(l[i].strip())==0:
			i+=1
			continue
		try:
			f = map(float, l[i].split())
			l = l[i:]
			break
		except:
			i+=1
			if i>len(l)-1:
				raise StandardError("file is not a list of numerical values")
			else:
				pass
	return  array(map(lambda x:map(float, x.split()), l))

def array_to_text(a, file, p=6):
	of = open(file, "w")
	for i in a:
		l = len(i)
		f = "%.6f " * l % tuple(i.tolist())
		f+= "\n"
		of.write(f)
	of.close()
	
def roundtoint(d):
	#return (d+.5).astype(Int32)
	return round(d).astype(int32)

def arraysplit(a, bounds):
	splits=[a[:bounds[0]]]
	for i in range(bounds.shape[0]-1):
		splits.append(a[bounds[i]:bounds[i+1]])
	splits.append(a[bounds[-1]:])
	return splits

def get_directional_projection(a, dir):
	'''Nx2array, direction(degrees) =>nx1 array
warning Left Handed Coordinates!!'''
	if dir==None:
		# get magnitude instead
		a= sqrt(a[:,0]**2 + a[:,1]**2)
	else:
		dir=2*pi*dir/360
		thet2=dir-pi/2
		yproj=a[:,0]*cos(dir)
		xproj=a[:,1]*cos(thet2)
		a=yproj+xproj
	return a	

def rotate(a, dir):
	'''Nx2 array, float => Nx2 array
convert a 2 col array to another representing the same stimulus rotated
dir degrees clockwise. 0-180 should be in the 0 column and  L-R in the 1
column.'''
	dir=2*pi*dir/360
	newy=a[:, 0]*cos(dir) - a[:, 1]*sin(dir)
	newx=a[:, 0]*sin(dir) + a[:,1]*cos(dir)
	return transpose(array([newy, newx]))
	# ang=-2*pi*dir/360
	# ra=array([[cos(ang), -sin(ang)],[sin(ang), cos(ang)]])
	# return dot(a, ra)

def toRadians(a):
	'''a (array of angles in degrees)=>array of angles in radians'''
	if not type(a) == ArrayType:
		a = array(a)
	return pi*a/180.0

def toDegrees(a):
	if not type(a) == ArrayType:
		a = array(a)
	return 180*a/pi
	

def rotate3D(a, ang):
	'''a (Nx3 array), ang (3tuple) => Nx3 array
rotate a through angles specified in tup. angles are in degrees,
counterclockwise, around the x, y, and z axis respectively'''
	out = a.copy()
	ang = toRadians(ang)
	out = rotateArrayAround(array([1.0, 0, 0]), ang[0], a)
	out = rotateArrayAround(array([0.0, 1, 0]), ang[1], out)
	out = rotateArrayAround(array([0.0, 0, 1]), ang[2], out)
	return out	

def rotateArrayAround(ax, ang, pts=None):
	'''rotate the 3D pts around the 3 vector ax, counterclockwise, by ang radians. If pts is None, return a rotation matrix rotmat, such that dot(pts, rotmat) implements the rotation. If pts is an array, apply the rotation and return the rotated points'''
	if ang % (2*pi) == 0.0:
		if pts==None:
			return identity(3)
		else:
			return pts.copy()
	ax=vnorm(ax.astype(float32))
	c = cos(ang)
	s = sin(ang)
	x, y, z = ax
	rotmat =array([[x**2+(1-x**2)*c, x*y*(1-c)-z*s, x*z*(1-c)+y*s],
			 		[x*y*(1-c)+z*s, y**2+(1-y**2)*c, y*z*(1-c)-x*s],
		 	 		[x*z*(1-c)-y*s, y*z*(1-c)+x*s, z**2+(1-z**2)*c]]).transpose()
	if pts == None:
		return rotmat
	return dot(pts, rotmat)	
			
def vnorm(v, applied=True):
	norm = sqrt((v**2).sum())
	if applied:
		return v/norm
	else:
		return norm

def vector_components(a, dir):
	'''1D array, float => Nx2 array
calculate the 0-180 and L-R components of a one-d array a oriented along dir.'''
	dir=2*pi*dir/360
	y=a*cos(dir)
	x=a*sin(dir)
	return transpose(array([y, x]))

def rotateAround(v, p, ang):
	'''rotate the 3 vector v around the 3 vector p, counterclockwise, by ang radians'''
	zax=p
	yax=cross(v,zax)
	xax=cross(yax, zax)
	zcomp=dot(v,zax)
	ortho=dot(v,xax)
	ycomp=ortho*sin(ang)
	xcomp=ortho*cos(ang)
	out=xcomp*xax+ycomp*yax+zcomp*zax
	out=out/sqrt((out**2).sum())
	out=out*sqrt((v**2).sum())
	return out
	
	

def rotate_kernel(w, dir):
	'''dict, dir
rotate a 2D wiener kernel represented by "dict" clockwise dir degrees'''
	rw={}
	rw.update(w)
	dir=dir*pi/180
	
	R=array([[cos(dir), sin(dir)], [-1*sin(dir), cos(dir)]])
	h1=transpose(reshape(w["h1"], (2, -1)))
	L=h1.shape[0]
	z= matrixmultiply(h1, transpose(R))
	rw["h1"]=reshape(transpose(z), (-1,))
	
	h2=array([[ravel(w["h2"][:L,:L]),ravel(w["h2"][:L,L:])],
			  [ravel(w["h2"][L:,:L]),ravel(w["h2"][L:,L:])]])
	h2r=zeros((2, 2, L**2), w["h2"].dtype.char)
	for i in range(L**2):
		h2r[:,:,i]=matrixmultiply(matrixmultiply(R, h2[:,:,i]), transpose(R))
	t=concatenate((reshape(h2r[0,0], (L,L)), reshape(h2r[0,1], (L,L))), 1)
	b=concatenate((reshape(h2r[1,0], (L,L)), reshape(h2r[1,1], (L,L))), 1)
	a=concatenate((t, b))
	rw["h2"]=a
	return rw

def magnitude(vec):
	'''magnitude of a vector'''
	return sqrt(sum(vec**2))

def getAngle(pt1, pt2, pt3):
	''' pt1, pt2, pt3 => float
returns the angle between three points. (in radians)'''	
	v1=pt1-pt2
	v2=pt3-pt2
	dp = dot(v1, v2)
	if magnitude(v1)*magnitude(v2) ==0:
		return 0.0
	#if abs(dp)>abs(magnitude(v1)*magnitude(v2)):
	#	print "huh?"
	#	print dp, magnitude(v1), magnitude(v2)
	cosTh = dp/(magnitude(v1)*magnitude(v2))
	if cosTh>1.0:
		cosTh=1.0
	if cosTh<-1.0:
		cosTh=-1.0
	return arccos(cosTh)

def projectToLine(pt, ls, le):
	''' pt ls le => (distance, offline)
arguments are all tuples of three (x,y,z) floats.
Return values are both floats.
Return value distance is the possition on the line between ls and le of the
perpendicular plane containing pt. The value is relative to ls, with positive 
values in the direction of le.  The return value offline is the perpendicular
distance from pt to the line. This value is in the same units as the points.
For example, if pt == le, the return is (eucd(ls, le), 0.0)'''
	pt, ls, le = map(castToArray, [pt, ls, le])
	if all(pt==ls):
		return (0,0)
	elif all(pt==le):
		return (eucd(ls, le), 0)
	rad = eucd(pt, ls)
	thet = getAngle(pt, ls, le)
	return (rad*cos(thet), rad*sin(thet))

def inManifold(m, p):
	'''m (Nx4 array), p (len 3 array) => float
	returns the relative length along the axis of a varriable diameter
	cylindrical manifold specified by m that comes crosest to point p.
	If p lies outside the manifold, returns -1'''
	mr=m[:,3].max()/2.0
	oor=False
	for i in range(3):
		if not m[:,i].min()-mr<=p[i]<=m[:,i].max()+mr:
			oor=True
			break
	if oor:
		return -1
	if  any(alltrue(abs(m[:,:3]-p)<=1e-9, 1)):
		ptind=argmax(alltrue(abs(m[:,:3]-p)<=1e-9, 1))
		pathl = cumsum(eucd(m, shift(m, 1)))
		return pathl[ptind]/pathl[-1]		
	path_ls = eucd(m[:,:3], shift(m[:,:3], 1))
	lines=concatenate([m, m],1)
	lines = reshape(lines, (-1, 4))[1:-1]
	lines=reshape(lines, (-1, 8))
	diams=take(lines, [3, 7], 1)
	lines=take(lines, [0,1,2,4,5,6], 1)
	proj=[]
	for i in range(lines.shape[0]):
		ls=lines[i,:3]
		le=lines[i,3:]
		ed=eucd(ls,le)
		U=sum((p-ls)*(le-ls))
		U=U/ed**2
		if U<0 or U>1.0:
			proj.append([-1, mr*10])
			continue
		tp=ls+U*(le-ls)
		rd=eucd(tp, p)
		proj.append([U, rd])
	proj=array(proj)	
	if all(proj[:,0]==-1):
		return -1	   
	bestind=argmin(proj[:,1])
	best=proj[bestind, :]
	diam=diams[bestind,0]+(diams[bestind,1]-diams[bestind,0])*best[0]
	if best[1]>diam:
		return -1		
	path = sum(path_ls[:bestind+1]) + best[0]*path_ls[bestind+1]
	return path/sum(path_ls)


def contiguous_nonzero(a, n=5):
	'''return the indexes for which a in true at that index, and each of
	the subsequent n indecies'''
	l=[]
	nz = nonzero1d(a)
	for ind in nz[:-n+1]:
		if all(a[ind:ind+n]):
			l.append(ind)
	return array(l)
	
def reverse(a):
	return take(a, arange(a.shape[0]-1, -1, -1))

def lock2step(value, start, step):
	'''value(float or array), start(float or array), step(float or int) => float or array
	returns value (or an array of values) rounded such that the returns
	are equal to start +n*step for n an integer
	'''
	v1=value-start
	v1=floor(v1/step)+step*(v1%step>(.5*step))
	value=v1+start
	return value

def findCrossing(a, t):
	if a[0]>a[-1]:
		a=-a
		t=-t
	above=nonzero1d(a<t)[-1]
	below=nonzero1d(a>t)[0]
	return int((above+below)/2.0)


def correctedArctan(x, y, mode='radians'):
	'''returns the angle specified by opposite=y, adjacent=x.
	This is arctan (y/x), except that the result is corrected for 
	quadrant (so x=-1, y=0 yield a result of pi, rather than 0). This
	function will also work (aproximately) where x is 0. Mode 
	may be radians or degrees, and determines the output units.'''
	if (x==0).sum():
		x=where(x==0, 1e-15, x)
	ang=arctan(y/x)
	ang+=pi*(x<0)
	ang+=2*pi*(ang<0)
	if mode.startswith('d'):
		ang=ang*180.0/pi
	return ang

# def cross3(v,w):
# 	'''if v and w are 3 element vectors, returns their cross product. Obsolete. Just calls numpy.cross now'''
# 	q=outer(v,w)
# 	return array([q[1,2]-q[2,1], q[2,0]-q[0,2], q[0,1]-q[1,0]])

def histogram(samps, bins=60, ran='auto',returnX=True):
	'''samps(1D array),  bins (int =60), ran (tuple or "auto" ="auto"),
	returnX (bool=True) -> 1D or 2D array
Samps is a float array of events (eg. 0.1, 2.1, 2.1, 2.1, 5, 6.8). Returns
a histogram expressing the counts of samps that fall in bins. The domain
expressed by "ran" is covered by a number of equal sized bins. "ran" 
may be a tuple (min, max) or the string "auto". In the latter case, the 
min and max of the data are used. If returnX is true, the return value is a 
shape (2,bins) array, with the first column containg the coordinates of the 
bin centers, and the second column containing the counts. Otherwise, only the 
counts are returned.'''
	if ran=='auto':
		ran=(samps.min(), samps.max())
	bb=ran[0]+arange(bins)*(ran[1]-ran[0])/float(bins)
	hist=zeros(bb.shape)
	past=0
	for i in range(bb.shape[0]-1, -1, -1):
		ng=(samps>=bb[i]).sum()
		hist[i]=ng-past
		past=ng
	if returnX:
		bb+=(bb[1]-bb[0])/2.0
		hist=concatenate([bb[:,NewAxis],hist[:,NewAxis]], 1)
	return hist	
		
def hist2(samps, binwidth, start, nbins=None):
	'''Much faster, slightly less flexible histogram function. Binwidth is the size of each bin, and start is the location of the first bin. If nbins is specified, the return vector will be forced to have that length (by cropping or zero padding as needed)'''
	samps=(samps-start)/binwidth
	samps=samps.astype(int32)
	hist=bincount(samps).astype(int32)
	if nbins:
		if hist.shape[0]>nbins:
			hist=hist[:nbins]
		elif hist.shape[0]<nbins:
			pad=nbins-hist.shape[0]
			pad=zeros(pad, hist.dtype)
			hist=concatenate([hist, pad])
	return hist		

def combinations(loa):
	'''Take a list of 1D arrays. Return an array of shape NxM where N is the cumulative product of the lengths of the input arrays and M is the number of input arrays. The return array contains all possible points created by combining the coordinates in the inputs'''
	na=len(loa)
	shapes=[x.shape[0] for x in loa]
	nc=multiply.reduce(shapes)
	stride=cumproduct(shapes)
	oa=zeros((nc, na), loa[0].dtype)
	oa[:,0]=resize(loa[0], nc)
	for i in range(1, na):
		dl=stride[i-1]
		dr=nc/dl
		oa[:,i]=ravel(transpose(resize(loa[i], (dl, dr))))	
	return oa
	


def uniformSampleIndex(s, n):
	'''returns a 1D array of integers, sampling n times roughly evenly into an array of size s'''
	ind=(s-1)*arange(n).astype(float32)/n
	ind=roundtoint(ind)
	return ind

def closestPow2(x):
	i=1
	while 2**i<x/2.0:
		i+=1
	if x-2**i>2**(i-1):
		i+=1
	return 2**i	
	
def fact(x):
	return multiply.reduce(arange(1, x+1))
	
def combin(x, y):
	return fact(x)/(fact(y)*fact(x-y))

def nDindex(dims):
	'''return an array of shape(multiply.reduce(dims), len(dims)) specifying the set of all indexes into a space of len(dims) deminsions, where each dimension ranges from 0 to the coresponding value of dims. This is the same as the set of all indexs into an ndarry with shape=dims. Also, this array is in the same order as numpys flat indexing, so if A is an ndarray with dimensionality D, shape S and size N, and F is a function that maps a DxM array of points onto a length M array of values, then A.flat=F(nDindex(S)) will assign every point in A to the value of F computed on the (length D) index of that point'''
	rs = tuple(take(dims, arange(len(dims)-1,-1,-1)))
	strides=concatenate([[1], cumprod(rs)[:-1]])
	strides=strides[arange(strides.shape[0]-1, -1, -1)]
	N = multiply.reduce(dims)
	ind = arange(N)
	op=zeros((N, len(dims)), int64)
	for c in range(len(dims)):
		co, ind = divmod(ind, strides[c])
		op[:,c]=co.astype(op.dtype)
	return op
