
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
from math import pi
import mien.math.sigtools
from mien.datafiles.filereaders import read_datafile

envfuncdict={"Exponential":[{"Name":"start",
							 "Type":float},
							 {"Name":"tau",
							  "Type":float}],
			 "Gaussian":[{"Name":"mid",
						  "Type":float},
						 {"Name":"var",
						  "Type":float},
						 {"Name":"offset",
						  "Type":float},
						 {"Name":"amp",
						  "Type":float}],
			 "Start/Stop":[{"Name":"turn on",
							"Type":float},
						   {"Name":"turn off",
							"Type":float},
						   {"Name":"smooth points",
							"Value":0}],
			 "Linear":[{"Name":"X0",
						"Type":float},
					   {"Name":"Y0",
						"Type":float},
					   {"Name":"X1",
						"Type":float},
					   {"Name":"Y1",
						"Type":float}],
			 "Filter":[{"Name":"File",
						"Type":str},
					   {"Name":"Hz",
						"Type":float}],
			 "Sine":[{"Name":"amp",
					  "Value":1.0},
					 {"Name":"freq",
					  "Value":(50.0,)},
					 {"Name":"phase",
					  "Value":0.0},
					 {"Name":"offset",
					  "Value":0.0}],
			 "Square":[{"Name":"amp",
						"Value":1.0},
					   {"Name":"freq",
						"Value":(50.0,)},
					   {"Name":"phase",
						"Value":0.0},
					   {"Name":"offset",
						"Value":0.0}],
			 "Triangle":[{"Name":"amp",
						  "Value":1.0},
						 {"Name":"freq",
						  "Value":(50.0,)},
						 {"Name":"phase",
						  "Value":0.0},
						 {"Name":"offset",
						  "Value":0.0}]}


def applyFilter(sig, env, dt):
	if env.has_key("filt"):
		filt = env["filt"]
	else:
		filen = env["File"]
		fs = env["Hz"]
		# fs in Hz, dt in seconds
		filt = read_datafile(filen)[0]
		if len(filt.shape)>1:
			if filt.shape[1]>filt.shape[0]:
				filt = transpose(filt)
			filt = filt[:,0]
		fdt = 1.0/fs
		if fdt != dt:
			filt = array_resample(filt, fdt, dt)
		env["filt"] = filt
	filt = reverseArray(filt)	
	z=convolve(sig, filt, 0)
	if len(z) < len(sig):
		dl = len(sig) - len(z)
		z = concatenate([zeros(dl, z.dtype.char), z])
	elif len(z)> len(sig):
		print "Warning: this method won't work well for inputs this short"
	return z.astype(Float32)

smooth=mien.math.sigtools.smooth

class Funcgen:
	def __init__(self, r):
		self.smoothing=0
		self.envelopes={}
		self.waves=[]
		self.functions={"Sine":self.make_sinewave, "Square":self.make_squarewave,
						"Triangle":self.make_trianglewave, "GWN": self.make_wn}
		self.envelope_functions={"Exponential":self.exp,
								 "Gaussian":self.gauss,
								 "Start/Stop":self.band,
								 "Linear":self.line
								 }
		self.envelope_functions.update(self.functions)
		self.set_domain(r)

	def report(self, s):
		print s

	def set_domain(self, r):
		self.domain=arange(r[0], r[1], r[2], Float32)
		self.dt=r[2]
		self.generate()

	def generate(self):
		self.function = zeros(len(self.domain), Float32)
		for c in self.waves[:]:
			try:
				self.function+=self.compute_wave(c)
			except:
				raise
				print "bad values. wave ignored"
		if self.smoothing:
			self.function=smooth(self.function, self.smoothing)
		return self.function

	def compute_wave(self, c):
		d=self.get_domain(c["FM"])
		s=self.functions[c["type"]](c, d)
		for env in c["AM"]:
			if self.envelopes[env]["type"] == "Filter":
				s = applyFilter(s,self.envelopes[env], self.dt)
			else:	
				s*=self.get_envelope(env)
		return s

	def apply_fm(self, d, e):
		start=d[0]
		diffs=mien.math.sigtools.deriv(d, 1)
		diffs=diffs*e
		return cumsum(diffs)

	def get_domain(self, fm):
		d=self.domain.copy()
		for e in fm:
			if self.envelopes[e]["type"] == "Filter":
				self.report("FM Filters not yet supported")
				continue
			env=self.get_envelope(e)
			d=self.apply_fm(d, env)
		return d

	def get_envelope(self, i):
		env = self.envelopes[i]
		if env["type"]=="Array":
			return env["array"]
		elif env["type"]=="Function":
			return env["function"](env)
		elif self.envelope_functions.has_key(env["type"]):
			e = self.envelope_functions[env["type"]](env)
			return e.astype(Float32)
		else:
			self.report("Can't compute envelope. Type is unknown.")
			return ones(len(self.domain)).astype(Float32)

	def add_wave(self, c):
		#c keys are "amp","freq","phase","offset","type","seed", "FM","AM"
		self.waves.append(c)
		self.generate()
		return len(self.waves)-1

	def add_envelope(self, env, applyto=[]):
		i=0
		while self.envelopes.has_key(i):
			i+=1
		self.envelopes[i]=env
		if len(applyto):
			self.bind_envelope(i, applyto)
		return i

	def unbind_envelope(self, i):
		for w in self.waves:
			if i in w["AM"]:
				w["AM"].remove(i)
			if i in w["FM"]:
				w["FM"].remove(i)
		
	def bind_envelope(self, i, applyto):
		self.unbind_envelope(i)
		for pair in applyto:
			self.waves[pair[0]][pair[1]].append(i)
		self.generate()

	def kill_wave(self, i):
		c=self.waves.pop(i)
		self.generate()

	def kill_envelope(self, i):
		self.unbind_envelope(i)
		del(self.envelopes[i])			
		self.generate()

## =================== Wave generation functions =========================
		
	def make_sinewave(self, pars, d=None):
		if d == None:
			d=self.domain.copy()
		omega=2*pi*pars['freq'][0]
		phi=2*pi*pars['phase']/360
		s=pars['amp']*sin(omega*d+phi)
		s=s.astype(Float32)+pars['offset']
		return s.astype(Float32)

	def make_wn(self, pars, d=None):
		if d == None:
			d=self.domain.copy()
		if pars.has_key("seed"):
			if type(pars['seed']) == tuple:
				pars['seed']= pars['seed'][-1]
		if pars['seed']>0:		
			mien.math.sigtools.seed(1,int(pars['seed']))
		if pars['phase']:
			lseg = int(pars['phase']/self.dt)
			wnu = mien.math.sigtools.normal(0, pars['amp'], lseg)
			wn = wnu.copy()
			while len(wn)<len(d):
				wn = concatenate([wn, wnu])
			wn = wn[:d.shape[0]]	
		else:	
			wn = mien.math.sigtools.normal(0, pars['amp'], d.shape)
		lb = pars['freq'][0]
		bw = 1.0/self.dt
		if len(pars['freq'])>1:
			ub = pars['freq'][1]
		else:
			ub = 1.0	
		if lb>0.0 or ub < (bw/2.0):
			wn = mien.math.sigtools.bandpass(wn, lb, ub, bw)	
		wn=wn+pars['offset']
		return wn.astype(Float32)
		
	
	def prepcycle(self, d, freq, phase):
		if len(freq)>1:
			per=freq[0]+freq[1]
			per=per/1000.0
			thresh=freq[0]/1000.0
		else:
			per=1.0/freq[0]
			thresh=per/2
		phase= per*(phase/360.0)
		d=d+phase
		d=d%per
		return(d, thresh)
		

	def make_squarewave(self, pars, d=None):
		if d == None:
			d=self.domain.copy()
		d, thresh = self.prepcycle(d,pars['freq'],pars['phase'])
		s=pars['amp']*(d<thresh)
		s=s.astype(Float32)+pars['offset']
		return s.astype(Float32)


	def make_trianglewave(self, pars, d=None):
		if d == None:
			d=self.domain.copy()
		d, thresh = self.prepcycle(d,pars['freq'],pars['phase'])
		f=(-1+(2/thresh)*d)*(d<thresh)
		f2=(1-(2/(max(d)-thresh))*(d-thresh))*(d>=thresh)
		f=f+f2
		f=f*pars['amp']
		s=f.astype(Float32)+pars['offset']
		return s.astype(Float32)


## =============== Envelope generation functions ====================
		
	def exp(self, env):
		zero = env["start"]
		tau = env["tau"]
		return exp((self.domain-zero)/tau)
		
	def gauss(self, env):
		midpoint = env["mid"]
		sigma = env["var"]
		offset= env.get("offset", 0)
		amp=env.get("amp", 1)
		return amp*exp(-.5*( ((self.domain-midpoint)/sigma)**2 ) )+offset

	def band(self, env):
		start= env["turn on"]
		stop=env['turn off']
		smooth_points=env.get('smooth points',0)
		f=ones(len(self.domain))*greater_equal(self.domain, start)*less_equal(self.domain, stop)
		if smooth_points:
			s=nonzero1d(f)
			v=ones(len(s), Float32)
			v=smooth(v, smooth_points)
			f=f.astype(Float32)
			put(f,s,v)
		return f
	
	def line(self, env):
		x0 = float(env['X0'])
		y0 = float(env['Y0'])
		x1 = float(env ['X1'])
		y1 = float(env ['Y1'])
		ind=nonzero1d(logical_and(self.domain>=x0, self.domain<=x1))
		if len(ind)<2:
			return ones(len(self.domain), Float32)
		x1=ind[-1]
		n=len(ind)
		rise=y1-y0
		f=arange(n).astype(Float32)*(rise/(n-1))
		f=f+y0
		pad=ones(ind[0], Float32)
		f=concatenate([pad, f])
		pad=ones(len(self.domain)-ind[-1], Float32)
		pad=pad[:-1]
		f=concatenate([f,pad])
		return f
		
