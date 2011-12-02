
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

	
def testSelect(func, n=1000, minfit=0, maxfit=100):
	fit = uniform(minfit, maxfit, 100)
	select = []
	for i in range(n):
		c = func(fit)
		select.extend(list(c))
	res = []
	for i in range(len(fit)):
		res.append((fit[i], float(select.count(i))/len(select)))
	res.sort(lambda x,y:cmp(x[0], y[0]))	
	for i in res:
		print "%.3f => %.3f" % i
	return res	

def OrdSelect(fit, mini=False):
	'''ordinal(array)=> (int1, int2)
Chooses 2 indexes from an array of fitness values. These indexes are suitable
choices for parents in order to maximize fitness with ordinal selection.
No selfing is allowed (e.g. int1 != int2).'''
	if mini:
		order=argsort(fit)
	else:
		order = take(argsort(fit), arange(len(fit)-1,-1,-1))
	chance=2*cumsum(arange(len(order),0,-1))
	index=random.randint(chance[-1]+1)
	return order[nonzero1d(greater_equal(chance, index))[0]]

def PropSelect(fit, mini):
	if mini:
		fit=1/(fit.astype(float64)+1)
	regions=cumsum(fit)
	index=random.uniform(0, regions[-1])
	p1=nonzero1d(greater_equal(regions, index))[0]
	return p1
	

SELECTION_FUNCTIONS={"Ordinal":OrdSelect,
					 "Proportional":PropSelect}

class Breeder:
	def __init__(self, alg):
		self.ga=alg
		self.maxrate=alg.attrib('MinimumBreedInterval') or 0
		self.maxrate*=2
		self.lastbreed=[]
		self.crossp=alg.attrib('CrossoverProbability') or .7
		self.mutp=alg.attrib('MutationProbability') or  .1					
		self.ranges=alg._params._bins
		mr=alg.attrib('MutationRange',) or  0
		mstep=round(self.ranges*mr)
		self.msteps=maximum(mstep, 1)
		self.transp=alg.attrib('TransposeProbability') or 1
		try:
			self.selectbase=SELECTION_FUNCTIONS[alg.attrib('SelectionMethod')]
		except:
			self.selectbase=OrdSelect
			print "Unknow selection method %s. Using ordinal selection" % repr(alg.attrib('SelectionMethod'))
		
		
	def selectbase(self, fit, invert):
		pass
		
	def select(self, mask=None, invert=False):
		'''Wrapper around self.selectbase functions. Returns an index into self.ga.fit representing the selection. This function automatically rejects any negative fitness values before selection. In addition, it will reject any idexes specified in an array "mask". If invert is True the sense of the selection is reversed (so if the algorithm is a Maximizer, small values will be favored). 
		This function will throw an IndexError if there is not at least one viable choice.'''
		lf=nonzero1d(self.ga.fit>=0)
		if mask:
			lf=setdiff1d(lf, mask)
		if len(lf)<2:
			return lf[0]	
		fit=take(self.ga.fit, lf)
		if invert:
			mini=self.ga.attrib("Maximize")
		else:
			mini= not self.ga.attrib("Maximize")
		ind=self.selectbase(fit, mini)
		return lf[ind]
		
	def kill(self):
		'''Return a single index of a weak unit (generated by calling select with the oposite of self.mini)'''
		return self.select(None, True)
			
	def newUnit(self):
		'''Return a new unit (array of uint16)'''
		try:
			(mom, dad)=self.parents()
		except:
			print "parent selection failed. new unit will be generated randomly"
			return self.ga.randind()
		kid=self.crossover(mom,dad)
		kid=self.mutate(kid)
		if self.transp:
			kid=self.transpose(kid)
		return kid

	def parents(self):
		self.ga.lock.acquire()
		try:
			p1=self.select(self.lastbreed)
			self.lastbreed.append(p1)
			p2=self.select(self.lastbreed)
			if self.maxrate > 0 :
				self.lastbreed.append(p2)
				self.lastbreed=self.lastbreed[-self.maxrate:]
			else:
				self.lastbreed=[]
			p1=self.ga.chroms[p1,:]
			p2=self.ga.chroms[p2,:]
		except:
			self.ga.lock.release()
			raise
		self.ga.lock.release()	
		return [p1,p2]

	def crossover(self, p1,p2):
		'''crossover(array, array) => array
takes two chromosome arrays and returns an array representing the random one
point crossover of these two chromosomes. Reads opts.cross to determine the
chance of crossover. Randomly returns one of the parents if there
is no crossover event.'''
		if random.random()>self.crossp:
			return p1.copy()
		loc=random.randint(1,p1.shape[0])
		child=zeros(p1.shape[0], p1.dtype)
		child[:loc]=p1[:loc]
		child[loc:]=p2[loc:]
		return child

	def mutate(self, c):
		'''mutate(array)=> array
		Reads self.mutate for chance of mutation, and generates a new array in which each element is a copy of the same element in the input array if no mutation, or the result self.newvalue() on the element if there is mutation. The new array is always of the same type as the input array.
		Mutations are determined sequentially. If no mutation occurs, the function returns. If a mutation occurs, it occurs at a random locus, and the chance of mutation is rechecked. It is thus (remotely) possible to mutate an unlimited number of loci, or the same locus several times'''
		p=uniform(0,1)
		while p<self.mutp:
			loc=random.randint(0,c.shape[0])
			c[loc]=self.newvalue(c[loc], loc)
			p=uniform(0,1)
		return c

	def newvalue(self, number, ind=None):
		'''returns an int that is a new, appropriately mutated, value for locus ind, generated from starting value number.'''
		bins=self.ranges[ind]
		if number==0:
			sign=1
			bound=bins-1
		elif number==bins-1:
			sign=-1
			bound=bins-1
		else:
			sign=random.randint(0,2)
			if sign:
				bound=bins-1-number
			else:	
				sign=-1
				bound=number		
		mstep=min(self.msteps[ind], bound)
		change=random.randint(1, bound+1)
		res=number+sign*change
		return res

	def transpose(self, chrom):
		'''Checks the transpose probability, and possibly implements a transpose operation. At most one transpose can occur'''
		p=uniform(0,1)
		if p>self.transp:
			return chrom
		inds=random.permutation(chrom.shape[0])[:2]
		v1=chrom[inds[0]]
		v2=chrom[inds[1]]
		r1=self.ranges[inds[0]]
		r2=self.ranges[inds[1]]
		v1=float(v1)/r1
		v1=round(v1*r2)
		v2=float(v2)/r2
		v1=round(v2*r1)		
		chrom[inds[0]]=v2
		chrom[inds[1]]=v1
		return chrom
			

