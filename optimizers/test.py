
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
from mien.optimizers.ga import GA
from mien.optimizers.evalwrap import testEval
from mien.math.array import *
from mien.optimizers.gui import GAMonitor, GAEditor, GAAnalyzer, wx 

DEFAULT_OPT_PARAMS={'Directory':'./GA_run',
					'RunTime':0.005,
					'MutationProbability':.1,
					'CrossoverProbability':.7,
					'PopulationSize':10,
					'Culling':0,
					'NewBlood':0.0,
					'ChromosomeVariance':0.0,
					'SelectionMethod':'Ordinal',
					'MinimumBreedInterval':0,
					'MaxDuplicates':5,
					'MutationRange':.5,
					'DistributerProfile':'Local'}

PARAMS=[[(0,'foo'), 0, 10, 1],
		[(0, 'bar'), 0, 50, 0],
		[(1, 'baz'), 0, 22, 3]]

e=testEval(False)


#c=array([0,0,0]).astype(Int16)
#for b in [-2**15,-2000, 10000, (2**15)-1 ]:
#	c[2]=b
#	print b
#	print ga.chrom2range(c)

def sga():
	if os.path.isdir('GA_run'):
		print "resuming"
		ga=GA('resume', 'GA_run')
	else:
		print "making new alg"
		ga=GA(e, PARAMS, DEFAULT_OPT_PARAMS)
	return ga

def bogus(dict):
	for k in dict.keys():
		print "%s -> %s" % (str(k), str(dict[k]))
import os
dir=DEFAULT_OPT_PARAMS['Directory']

def rungui():
	app = wx.PySimpleApp()
	ga=sga()
	gam=GAMonitor(None, ga, bogus)
	gam.Show(True)
	app.MainLoop() 

def editgui():
	app = wx.PySimpleApp()
	gae=GAEditor(None, 'GA_Run')
	app.MainLoop() 

def runtxt():
	ga=sga()
	ga.run()

def agui():
	app = wx.PySimpleApp()
	gae=GAAnalyzer(None, 'GA_Run')
	app.MainLoop() 
	

runtxt()

