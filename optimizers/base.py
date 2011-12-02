
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
from mien.math.array import randint, argmin, concatenate, array, ones, zeros
import mien.optimizers.arraystore as ast
import time, threading
import os

class Optimizer(NmpmlObject):
	'''Base class for building various types of optimizers. This class provides the functionality for setting up the cost function and the parameters to be optimized.
	This class requires a child of type ElementReference to AbstractModel and another of type ParameterSet. It may optionally include an ElementReference to a Distributer. If present, this class will be used to distribute elvauation load to other computers or cpus. 
	The philosophy of this class and its subclasses is to concentrate on optimization and leave other details to referenced classes. Consequently encoding/decoding is handled by the ParameterSet and all details of the evaluation (selection of data, horizontal method calls, conditional execution, etc) are left to the AbstractModel. Distributed evaluation is left to the Distributer whens possible, though some subclasses will require knowlege of the distributer's internal structure. Consequently, it is the responsibility of the user to construct a consistant object hierarchy. Many possible hierachy's will fail to execute, and some will generate logic bugs. Building optimization algorithms from scratch simply requires care, and amounts to a programming task, no matter how detailed an interface it is wrapped in. Use of Optimizer subclasses is therefor not for the "casual" GUI user. 
	This class provides the basic functions common to a wide variety of optimization schemes, but can't be executed directly. Subclasses need to redefine at mimimum the "evaluate" and "next" methods. 
	
	attributes:
		Fitness - string (required) - This is the name of an attribute. The top level Data instance passed through the target abstract model should should return with this attribute set to a non-negative floating point number. The optimizer will use this result as a cost function or fitness value to optimize. It is the responsibility of the AbstractModel to set this attribute. 
		File - string (required) - Optimizers will open a file at runtime to store evaluation results. This string indicates the path to that file. In order to allow thread safety, calls to init may change this attribute by adding random suffixes. 
		Maximize - bool - If True, the optimizer will seek to maximize the value of the Fitness variable. By default, the fitness is treated as an error, and is minimized.  
		TargetFitness - float - Abort running if a fitness at least this good is discovered. If Maximize is not set, this value is always at least 0 (since zero is a natuarl lower bound for an error). For a maximizer, if this value is not set explicitly it is positive infinity (the algorithm will run forever, or until MaxTime).
		MaxTime - float - This is a maximum amount of real time in hours that the algorithm will run for. By default, it is possitive infinity (the algorithm will run forever, or until it attains TargetFitness).
		ThreadSafe - bool - Make sure that multiple instances of this algorithm can run on the same system image. 
		EvalConditions - Int - If this is set, and non-zero, the AbstractModel should set an attribute in the top-level Data instance named "EvalConditions". The content of this attribute must be a tuple of 32bit numbers with the same length as the specified int (these will be stored as float32, but the AbstractModel can use any internal code to interpret it). This value is used to represent variable conditions that occur during evaluation. Using it is an advanced topic, and should be documented by the Blocks that enable it. A simple example is a parametric fitness function, where the optimizer is seeking a general optimum. The fitness of a given parameter set will depend on some metaparameters, so this parameter needs to be returned and stored along with the fitness.  
	'''
	_requiredAttributes = ["Name", "Fitness", "File"]
	_specialAttributes = ["TargetFitness",
						  "Maximize",
						  "MaxTime",
						  "ThreadSafe",
						  "EvalConditions"
						]
	
	_allowedChildren = ["ParameterSet", "Comments", "ElementReference"]
	
	def model(self):
		'''return an instance reference to the model that is used for evaluation'''
		return self.getTypeRef('AbstractModel', True)[0]
		
	def params(self, fc=False):
		'''Return the parameter set. Also calls the cache method of the set, so the returned instance will have working methods.'''
		ps=self.getElements('ParameterSet', depth=1)[0]
		if fc or not ps._pars:
			ps.cache()
		return ps
		
	def better(self, a, b):
		'''Returns True if a is more optimal than b (this depends on the value of Maximize)'''
		if a<0:
			return False
		elif b<0:
			return True
		if self.attrib('Maximize'):
			return a>b
		return a<b

	def random(self):
		'''return a random set of parameter values as a 1D array. (Although the values are random, they are within the allowed ranges and precisions)'''
		q=randint(-32768, 32768, self._np)
		q=self._params.code16toPar(q)	
		return q

					
	def test(self):
		'''Generate a random parameter set and evaluate it.  Returns a tuple (1D array, float, tuple). The array is the random set of parameters. The float is the fitness, and the tuple contains EvalConditions parameters, or (). Resets the parameters to their starting values on completion'''
		self._params=self.params(True)
		vals=self._params._values.copy()
		self._model=self.model()
		self._np=len(self._params._pars)
		rc=self.random()
		fit, ec=self.local_eval(rc)
		return (rc, fit, ec)
		
	def codingtest(self):
		self.prep()
		q=ones(self._np)*-32768
		print q
		print self._params.code16toPar(q)	
		q=ones(self._np)*32767
		print q
		print self._params.code16toPar(q)	
		q=zeros(self._np)
		print q
		print self._params.code16toPar(q)
		print self._params.indextoPar(q)
		q=ones(self._np)*self._params._bins
		q-=1
		print q
		print self._params.indextoPar(q)	
		
		
	def initialize_vars(self):
		'''Sets a bunch of internal variables. This is called by prep and resume'''
		self._params=self.params(True)
		self._np=len(self._params._pars)
		self._storesize=self._np+1
		if self.attrib('EvalConditions'):
			self._storesize+=int(self.attrib('EvalConditions'))
		self._distrib=None
		ds=self.getTypeRef('Distributer')
		if ds:
			self._distrib=ds[0].target()
		self._abort=False
		self._store=None
		self._best=(-1,-1)
		self._model=self.model()
		self._start=None
		self._nunits=0
		self._units=None
		self.lock=threading.Lock()
		self.init_local_vars()
					
	def prep(self):
		'''Set up the optimization run. This includes setting up any initial conditions opening files, making directories, setting hidden attributes, etc. Subclasses must overload this method. It is required to call prep or resume before calling methods that run or test the algorithm or access data.'''
		self.initialize_vars()
		if self.attrib("BaseFileName"):
			self.setAttrib('File', self.attrib("BaseFileName"))
		fn=ast.empty(self.attrib("File"), self._storesize, self.attrib("ThreadSafe"))
		if fn != self.attrib("File"):
			self.setAttrib("BaseFileName", self.attrib("File"))
			self.setAttrib('File', fn)
		self._store=ast.ArrayStore(fn, 'w')
		self.report("prep complete")

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
		self.report("Resume complete. %i units. Best %.4f, Mean %.4f" % (self._nunits, self._best[0], self.fit.mean()))
		self.setAttrib('File', fname)
					
	def getParams(self, i):
		'''return the parameter set stored as unit index i'''
		return self._store[i]
		
	def assignBest(self):
		'''assign the set of parameters with the best fitness to the ParameterSet'''
		self.lock.acquire()
		try:
			c=self.getParams(self._best[1])
			self._params.quickset(c)
			self._params.flush()	
		except:
			self.report("Parameter retrieval and/or assignment failed")
		self.lock.release()	
		
			
	def threadcall(self, method, args):
		'''Spawn a thread to run the given method with the given arguments. Strat the tread, and return it.'''
		t = threading.Thread(target=method, args=args)
		t.setDaemon(True)
		t.start()
		return t
				
	def lockcall(self, method, args):
		'''Attempt to acquire self.lock, execute the indicated method with the indicated arguments, and release the lock. The method call is wrapped in a general try/except, gauranteeing that the lock is always released (but making failed method calls hard to debug)'''
		self.lock.acquire()
		try:
			apply(method, args)
		except:
			self.report("Call to %s%s failed" % (str(method), str(args)))
		self.lock.release()	
		
	
	def resumerun(self):
		'''Shortcut function to resume from self.attrib('File') and run. Used mostly as "mien -r Optimizer.resumerun"'''
		self.resume()
		self.run()
		
	def localrun(self):
		'''Shortcut function to resume from self.attrib('File') (if possible) and run. Disables the distributer, if one is present.'''
		self.resume()
		self._distrib=None
		self.run()
		
	
	def run(self, background=False):
		'''Run the optimizer. If background is True, run in a thread.'''
		if background:
			self.threadcall(self.run, (False,))
			return
		if not hasattr(self, "_params"):
			print "Warning - alg not prepped. Prepping automatically"
			self.prep()
		self.prerun()	
		self._start=time.time()
		self._abort=False
		self.report("Starting Run (pid=%s)" % (str(os.getpid(),)))
		if self._distrib:
			self._distrib.start()
		try:
			while not self.done():
				self.search()
		except KeyboardInterrupt:
			self.report('Manual abort. Shutting down.')
			
		if self._distrib:
			self._distrib.stop()
		self.cleanup()
		self.assignBest()
		self._store.close()
		self.report("Run Completed")


	def search(self):
		'''This is the main loop called by run (sometimes in a thread). By default it calls next and evaluate.'''
		ps=self.next()
		self.evaluate(ps)
		

	def runtime(self):
		try:
			return (time.time()-self._start)/3600.0
		except:
			return 0
	
	def done(self):
		'''return True if the conditions for completing a run are met.'''
		if self._abort:
			return True
		q=self.attrib('MaxTime')
		if q and self.runtime()>=q:
			return True
		if not self.attrib("Maximize") and self._best[0]==0:
			return True
		tf=self.attrib('TargetFitness')
		if tf and self.better(self._best[0], tf):
			return True
		return False
		
	def local_eval(self, c):
		'''Assign and evaluate the parameter set c locally. Return a 2 tuple. The first element is the fitness value. The second element is the set of EvalConditions, or ()'''
		try:
			#print 'evaluating', c
			self._params.quickset(c)
			dat=self._model.run()
		except AttributeError:
			self._params=self.params()
			self._model=self.model()
			self._params.quickset(c)
			dat=self._model.run()
		#print "mod return"
		fit=dat.attrib(self.attrib("Fitness")) or -1.0
		#print 'got', fit
		if self.attrib("EvalConditions"):
			ec=dat.attrib("EvalConditions")
			if type(ec) in [int, float]:
				ec=(ec,)
		else:
			ec=()
		return (fit, ec)	
		
	def _eval_and_handle(self, c, func):
		'''Internal function used by general_eval to make theaded calls'''
		f=self._distrib.eval(self.upath(), 'local_eval', (c,))
		#print "got distrib response", f, c
		func(c, f)
		 
	def general_eval(self, c, meth):
		'''Evaluates a parameter set c, and passes the resulting arguments (c, evalresult) to the passed Method "meth". If there is no distributer, this is the same as calling meth(c, self.local_eval(c)). If there is a distributer, the evaluation call will be made in a thread, so meth sholud be thread safe.
		The return value is the return value is None'''
		if not self._distrib:
			meth(c, self.local_eval(c))
		else:
			while self._distrib.busy():
				time.sleep(1)
			self.threadcall(self._eval_and_handle,  (c,meth))
		
	def record(self, c, f):
		'''Writes a chromosome and the fitness value to the arraystore. Not thread safe! (self.lockcall(self.record, (c,f)) is thread safe). f should be a tuple (fit, evalconditions) as returned by general_eval. Return value is the new size of the data store'''
		if self.attrib('EvalConditions'):
			evc = int(self.attrib('EvalConditions'))
			evc=zeros((evc, 1))
			if f[1] and type(f[1])==type(evc):
				c=concatenate([[f[0]], f[1], c])
			else:
				c=concatenate([[f[0]], evc, c])
		else:
			c=concatenate([[f[0]], c])
		if self._storesize!=c.shape[0]:
			raise IOError("Attempt to record a parameter set of the wrong length")
		n=self._store.append(c)
		#print self._store[n-1]
		if self.better(f[0], self._best[0]):
			print "New best %.3f (%s)" % (f[0], str(c))
			self._best=(f[0], n-1)
		return n
		
	def init_local_vars(self):
		'''Called at end of initialize_vars. This is a stub method to simplify subclassing (If all a subclass needs to do is set a few extra state variables for use at run time, it can define this method and won't need to overload prep or resume)'''
		pass

	def prerun(self):
		'''Take actions required just before a run. Subclass specific'''

	def cleanup(self):
		'''Take actions required on terminiation of a run. Subclass specific'''
		
	def evaluate(self, c):
		'''Evaluate a set of parameters (in the 1D float array c). This is really a procedure with no return value, so it must also handle recording the unit and modifying the state of the optimizer if needed. Subclass specific'''
		pass
	
	def next(self):
		'''Return the next set of parameters to be evaluated. Subclass specific''' 
		pass
