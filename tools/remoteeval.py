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
import os, re, socket, select, struct, threading, time, cPickle
from SocketServer import ThreadingTCPServer,StreamRequestHandler,BaseServer
from string import join
from sys import exc_info, stdout, stderr
from time import sleep
import mien.parsers.mzip as mzip
from mien.math.array import array

HOSTNAME = socket.gethostname()
BASEPORT =8008 
DIRECTORY=os.path.expanduser("~/rexec")
ADDR=socket.gethostbyname(HOSTNAME)
NCPUS=1

if ADDR == "127.0.0.1":
	inetadd=re.compile(r"\d+.\d+\.\d+\.\d+")
	try:
		ADDR = os.popen("host %s" % HOSTNAME).read()
		m=inetadd.search(ADDR)
		if not m:
			raise StandardError('no address in output')
		ADDR=m.group()
		if ADDR=="127.0.0.1":
			raise StandardError('local address in output')
	except:
		ADDR = "127.0.0.1"
		print "Warning: Net id is 127.0.0.1 and 'host' fails. Using 127.0.0.1, but it is likely that network requests will fail"

try:	
	NCPUS=int(os.environ['NUMBER_OF_PROCESSORS'])
except:
	try:
		NCPUS=os.sysconf('SC_NPROC_ONLN')
	except:
		try:
			NCPUS=os.sysconf('SC_NPROCESSORS_ONLN')
		except:
			try:
				NCPUS=int(os.popen('sysctl -n hw.ncpu').read())
			except:
				print "can't set number of cpus. Using 1"
	
def stringToInt(s):
	return len(s)

class QueueHandler(StreamRequestHandler):
	def handle(self):
		data=self.rfile.read()
		if data=='get object':
			self.server.registerClient(self.client_address[0])
			reply=self.server.sendDoc()
		elif data=='request job':
			jid, dat = self.server.nextRequest(self.client_address[0])
			reply=str(jid)+':'+dat
		elif data.startswith('job done'):
			ind=data.find(':')
			ctype=data[:ind]
			jid=int(ctype.split()[-1])
			data=data[ind+1:]
			self.server.finish(jid, data, self.client_address[0])
			reply="OK"
		else:
			reply="Huh?"
		self.wfile.write(reply)
			
class EServer(ThreadingTCPServer):
	
	request_queue_size = 50
	
	def __init__(self, doc, port, requeue=True):
		self.doc=doc
		self.requeue=requeue
		self.port=port
		self.addr = ADDR
		self.abort=False
		self.lock=threading.Lock()
		self.jindex=0
		self.nprocs=0
		BaseServer.__init__(self, (self.addr, self.port), QueueHandler)

	def __del__(self):
		self.doc=None
		del(self.lock)
		del(self.jobs)
		try:
			self.socket.close()
		except:
			pass
		del(self.socket)
		
	def start(self):
		self.queue=[]
		self.assigned = []
 		self.clients={}
		self.jobs={}
		self.socket = socket.socket(self.address_family,
                                    self.socket_type)
		self.server_bind()
		self.server_activate()
		self.serveThread=threading.Thread(target=self.serve_forever)
		self.serveThread.setDaemon(True)
		self.serveThread.start()
		if self.requeue:
			self.qThread=threading.Thread(target=self.reQueueJob)
			self.qThread.setDaemon(True)
			self.qThread.start()
		

	def stop(self):
		self.lock.acquire()
		self.abort=True
		for j in self.jobs.keys():
			try:
				print j
				self.jobs[j]['result']='aborted'
				self.jobs[j]['done'].set()
			except:
				pass
		self.lock.release()
		try:
			self.serveThread.join(40)
			self.qThread.join(40)
		except:
			pass
		self.socket.close()
		
	def serve_forever(self):
		print "starting server on %s:%i" % (self.addr, self.port)
		while not self.abort:
			self.handle_request()
			stdout.flush()
			stderr.flush()
		
		print "server done"	

	def report(self,s):
		print s

	def sendDoc(self):
		return mzip.serialize(None, self.doc)

	def reQueueJob(self):
		while not self.abort:
			time.sleep(10)
			if len(self.assigned)>0:
				self.lock.acquire()
				jid=self.assigned.pop(0)
				if self.jobs.has_key(jid) and not self.jobs[jid]['done'].isSet():
					self.queue.append(jid)
				self.lock.release()
					
	
	def registerClient(self, addr):
		self.lock.acquire()
		self.nprocs+=1
		if self.clients.has_key(addr):
			self.clients[addr]['procs']+=1
		else:
			self.clients[addr]={'assigned':0,
								'completed':0,
								'last':time.time(),
								'procs':1}
		self.lock.release()
		return self.clients[addr]
	
	def addToQueue(self, path, method, args):
		self.lock.acquire()
		if self.abort:
			t.threading.Event()
			t.set()
			self.jobs[jid]={'done':t,
							'result':'aborted'}
			self.lock.release()
			return
		jid=self.jindex
		self.jindex+=1
		self.jobs[jid]={'object':path,'method':method,
						'args':args, 'done':threading.Event(),
						'submitted':time.time()}
		self.queue.append(jid)
		self.lock.release()
		return jid

	def eval(self, path, method, args):
		jid = self.addToQueue(path, method, args)
		self.jobs[jid]['done'].wait()
		output = self.jobs[jid]['result']
		self.lock.acquire()
		del self.jobs[jid]
		self.lock.release()
		return output
			
	def busy(self):
		if len(self.queue)<self.nprocs+2:
			return 0
		else:
			return 1

	def eval2list(self, l, ind, path, method, args):
		out=self.eval(path, method, args)
		l[ind]=out

	def batch(self, path, method, args):
		out= [None]*len(args)
		wait=[]
		for i, tup in enumerate(args):
			while self.busy():
				sleep(1)
			t = threading.Thread(target=self.eval2list, args=(out, i, path,method, tup))
			wait.append(t)
			t.setDeamon(True)
			t.start()
			sleep(1)
		for t in wait:
			t.join()
		return out	
		
	def finish(self, jid, dat, client):
		if not self.jobs.has_key(jid):
			return
		if self.jobs[jid].get('result'):
			return
		try:
			#dat=cPickle.loads(dat)
			dat=eval(dat)
		except:
			self.report('invalid result recieved for job %i' % jid)
			return
		self.lock.acquire()
		try:
			self.jobs[jid]['result']=dat
			self.jobs[jid]['finished']=time.time()
			self.jobs[jid]['done'].set()
			self.clients[client]['last']==time.time()
			self.clients[client]['completed']+=1			
		except:
			pass
		try:
			if jid in self.queue:
				self.queue.remove(jid)
			elif jid in self.assigned:
				self.assigned.remove(jid)
		except:
			pass
		
		self.lock.release()

	def killClient(self, client):
		self.lock.acquire()
		self.nprocs-=1
		try:
			if self.clients[client]['procs']>1:
				self.clients[client]['procs']-=1
			else:
				del(self.clients[client])
		except:
			pass
		self.lock.release()
		
	def nextRequest(self, client):
		if self.abort:
			self.killClient(client)
			return (-2, 'stop')
		self.lock.acquire()
		if len(self.queue)==0:
			self.lock.release()	
			return (-1, 'idle')
		jid=self.queue.pop(0)
		if self.requeue:
			self.assigned.append(jid)
		if not self.jobs[jid].has_key('sent'):
			self.jobs[jid]['sent']=time.time()
		self.clients[client]['assigned']+=1
		self.clients[client]['last']==time.time()
		self.lock.release()	
		dat={}
		for k in ['object','method','args']:
			dat[k]=self.jobs[jid][k]
		#dat=cPickle.dumps(dat,-1)
		dat=repr(dat)
		return (jid,dat) 



class EClient:
	def __init__(self, addr, port):
		self.server=(addr, port)
		self.doc=None 
		self.job=None
		self.failed=0
		self.ncpus=NCPUS
		self.abort=False
		print 'started client' 

	def busy(self):
		return False
		try:
			la=os.getloadavg()[0]
		except OSError:
			la=0
		if la-self.ncpus>-.3:
			return 1
		else:
			return 0

	def send(self, dat):
		soc=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		soc.connect(self.server)
		soc.send(dat)
		soc.shutdown(1)
		v=[]
		m=0
		while m<3:
			r=soc.recv(100)
			if len(r)==0:
				m+=1
			v.append(r)
		soc.close()	
		v=join(v,'')
		return v
	
	def getJob(self):
		try:
			dat=self.send('request job')
		except:
			print 'failed to get job'
			self.failed+=1
			if self.failed>2:
				self.abort=True
			else:	
				time.sleep(5)
			return None
		self.failed=0
		ind=dat.find(':')
		jid=int(dat[:ind])
		if jid==-1:
			#print 'server is idle'
			time.sleep(3)
			return None
		elif jid==-2:
			print 'server stopped'
			self.abort=True
			return None
		dat=dat[ind+1:]
		#dat=cPickle.loads(dat)
		dat=eval(dat)
		self.job = jid
		return dat

	def eval(self, job):
		try:
			o = self.doc.getInstance(job['object'])
			m = getattr(o, job['method'])
			r=apply(m, job['args'])
		except:
			r=[-1, exc_info()[1]]
		return r

	def reportJob(self, r):
		#s = cPickle.dumps(r, -1)
		s = repr(r)
		try:
			self.send('job done %i:%s' % (self.job,s))
		except:
			print "could not return job result!"
			self.failed+=1
			if self.failed>2:
				self.abort=True
		self.job=None

	def doJob(self):
		j=self.getJob()	
		if j:
			while self.busy():
				time.sleep(5)
			r=self.eval(j)
			self.reportJob(r)
		stdout.flush()
		stderr.flush()
						
	def run(self):
		doc=self.send('get object')
		self.doc=mzip.deserialize(doc)
		print 'client registered' 		
		while not self.abort:
			self.doJob()
		

def startClient(es, add):
	if add.startswith('localhost') or add=='127.0.0.1' or add == ADDR:
		command = "startRE.py %s %i < /dev/null >/dev/null 2&>1 &" % (es.addr, es.port)
		command = "startRE.py %s %i &" % (ADDR, es.port)
	else:
		command = "ssh %s startRE.py %s %i < /dev/null >/dev/null 2&>1 &" % (add, es.addr, es.port)
	print command
	os.system(command)


def startClients(es, cl):
	for add in cl:
		t=threading.Thread(target=startClient, args=(es,add))
		t.setDaemon(True)
		t.start()



		

