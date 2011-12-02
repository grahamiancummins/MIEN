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

from mien.optimizers.base import *
from mien.optimizers.breeders import Breeder
from mien.math.array import *
from time import sleep

class GeneticAlgorithm(Optimizer):
	'''Optimizer subclass that searches parameter space using a continuous replacement genetic algorithm with crossover, mutation and transposition operators.
	
		MutationProbability: Mutation probability for breeding (Default .1)

		CrossoverProbability: Crossover probablitiy (.7)

		TrnasposeProbability: (default 0)

		PopulationSize: number of units in the population (100)

		Cull: if true, units with fitness values worse than this value
				"die at birth". (False)

		NewBlood : A percentage chance that any given new unit is generated randomly. (Default 0)

		ChromosomeVariance: Determines the distribution of values in a new
							chromosome. If 0 the distribution is uniform.
							Otherwise it is normal with mean 0 and this
							variance. (Default 0)		   

		SelectionMethod: Method of parent selection. May be
						 "Proportional" or "Ordinal" (Default ordinal)

		MinimumBreedInterval: The number of breeding events that must occur before
							  a given parent can be re-selected. (Default 0)

		DistributerProfile: The port number for distributed evaluation. 
						default: "Local" - this (and any non-int value) 
						result in serial local evaluation)
		
		MaxDuplicates: The maximum number of chromosomes in the population that 
					are allowed to be the same (5)

		MutationRange: The fraction of the chromosome range that can be reached 
					via mutation. A value of 1.0 means that a mutation can lead to any 
					possible value. 0 always means that only single step mutations 
					are allowed. (default .5) 

		These algorithms always use continuous replacement, with the worst errors 
		"dying" first to allow room for new members of the population.

		Alternately, if eval is the string "resume" and params is the name of a 
		directory, resume a GA stored in the indicated directory.
		'''


	_requiredAttributes = Optimizer._requiredAttributes+['MutationProbability', 'CrossoverProbability', 'PopulationSize']
	_specialAttributes = Optimizer._specialAttributes+['Cull',
						  'CompeteToReplace',
						  'Death',
						  'NewBlood',
						  'TransposeProbability',
						  'SelectionMethod',
						  'MaxDuplicates',
						  'MutationRange',
						  'MinimumBreedInterval']

	_guiConstructorInfo = {'CompeteToReplace':{'Name':'CompeteToReplace',
										  'Type':'List',
										  'Value':[True,
												   False]},
						   'SelectionMethod':{'Name':'SelectionMethod',
										  'Type':'List',
										  'Default':"Ordinal",
										  'Value':["Proportional",
												   "Ordinal"]},
						   'Death':{'Name':'Death',
										  'Type':'List',
										  'Default':"Worst",
										  'Value':['Worst',
												   'Select']}}


				
	def init_local_vars(self):
		''' '''
		self._popsize=self.attrib('PopulationSize')
		self.fit=ones(self._popsize)*-2
		self.chroms=zeros((self._popsize, self._np), uint16)
		self.breeder=Breeder(self)
		self._npts=0
	
	def resume(self, fname=None):
		'''Resume a run from stored data. This is an alternative to self.prep. If fname isn't specified it defaults to self.attrib("File").'''
		self.initialize_vars()
		if not fname:
			fname=self.attrib("File")
		if not ast.verify(fname, self._storesize):
			self.report("can't resume. %s is not an appropriate storage file" % fname)
			self.prep()
			return 
		self._store=ast.ArrayStore(fname, 'w') 
		self._nunits = len(self._store)
		fit=self._store.getColumn(0)
		if self.attrib('Maximize'):
			bid=argmin(fit)	
		else:
			bid=argmin(fit)	
		self._best=(fit[bid], bid)
		dat=self._store.tail(self._popsize)
		self.fit[:dat.shape[0]]=dat[:,0]
		for i in range(dat.shape[0]):
			self.chroms[i, :]=self._params.getIndex(dat[i,-self._np:])
		self.report("Resume complete. %i units. Best %.4f, Mean %.4f" % (self._nunits, self._best[0], self.fit.mean()))			
		#print self.fit, self.chroms		
			
	def cleanup(self):
		'''Write the current population to the end of the arraystore (required for correct resume behavior. This results in duplicate records that analysers may need to delete).'''
		for i in range(self._popsize):
			c=self._params.indextoPar(self.chroms[i,:])
			self.record(c, (self.fit[i], (), ))


	def randind(self):
		'''Return a random chromosome. This is not the same as the random parameter set returned by self.random because it is a uint16 array of indexes into the parameter space, not a vector of actual parameter values'''
		q=random.uniform(0, 1, self._np)
		q=q*self._params._bins
		q=minimum(q.astype(uint16), self._params._bins-1) 
		return q		
				
	def next(self):
		'''Return the next set of parameters to be evaluated. If the initial population isn't established, or if the "NewBlood" probability occurs, returns random. Othewise, calls "breed" to generate new values. Note the the values returned by this function are indexes (ints) not raw parameters.'''
		rc=False
		if any(self.fit==-2):
			rc=True
		elif self.attrib('NewBlood') and random.uniform(0,1)<self.attrib('NewBlood'):
			rc=True
		if rc:
			c=self.randind()
		else:
			c=self.breeder.newUnit()
		return c
		

	def evaluate(self, c):
		dup=alltrue(self.chroms==c, 1)
		fit=None
		if any(dup):
			fit=take(self.fit, nonzero1d(dup))
			fit=compress(fit>-2, fit)
			if self.attrib('MaxDuplicates') and fit.shape[0]>self.attrib('MaxDuplicates'):
				return
			elif fit.shape[0]>0:	
				fit=(fit[0], None)
		c=self._params.indextoPar(c)
		if fit==None:
			self.general_eval(c, self.insertUnit)
		else:
			self.insertUnit(c, fit)

	def insertUnit(self, chrom, fit):
		'''Add a new unit to the population. Thread safe.'''
		#print fit
		try:
			fv=fit[0]
		except IndexError:
			print "got eval error: %s" % (str(fit),)
			return
		try:
			fv=float(fit[0])
		except ValueError:
			print "got eval error: %s" % (str(fit),)
			return
		self.lock.acquire()		
		
		try:
			self._npts+=1
			if not self._npts%200:
				print "tried %i, %i viable, %.3f mean fit" % (self._npts, self._nunits, self.fit.mean())
			ind=self.compete(fit[0])
			if ind>=0:
				self.fit[ind]=fit[0]
				self.chroms[ind]=self._params.getIndex(chrom)
				self._nunits=self.record(chrom, fit)
			self.lock.release()	
		except:
			self.lock.release()
			#raise
			self.report("Record failed")


	def compete(self, fit):
		'''Determine which unit is replaced by a new unit with fitness "fit". Return value is the index of the unit to "kill". If this value is <0, the new unit is killed and doesn't replace any existing unit. Not locally thread safe (usually called in a thread safe way from insertUnit).'''  
		if any(self.fit<0):
			return argmin(self.fit)	
		elif fit<0:
			return -1
		elif self.attrib("Cull") and self.better(self.attrib("Cull"), fit):
			return -1
		if self.attrib("Death")=='Select':
			ind=self.breeder.kill()
		else:
			if self.attrib('Maximize'):
				ind=argmin(self.fit)
			else:
				ind=argmax(self.fit)
		if self.attrib('CompeteToReplace'):
			if self.better(self.fit[ind], fit):
				ind=-1
		return ind		
		
