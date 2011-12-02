#!/usr/bin/env python

import sys, os, time


def timeit(cmd):
	print cmd
	st=time.time()
	os.system(cmd)
	print time.time()-st


if len(sys.argv)>1:
	cmd=sys.argv[1]
	if cmd.endswith('.py'):
		cmd="python %s" % cmd
	timeit(cmd)
else:
	cmds=["python mapseek.py", "./mapc", "./mapd", "./mapf", "./mapo", "./mapcl"]
	for c in cmds:
		timeit(c)
		
	