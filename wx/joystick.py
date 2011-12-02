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

from time import sleep
import threading, wx

class JSMonitor:
	def __init__(self, function, bevents=None, time=.1, dz=5, jsid=wx.JOYSTICK1):
		'''function, bevents=None, time=.1, dz=5, jsid=0 -> object
		Returns an object that monitors joystick state. The monitor
		tread (see method "start") runs once every "time" seconds, 
		determines the joystick state, and passes it (as a dictionary) 
		to "function". dz determines the "dead zone" of the x/y axes.
		if bevents is true, it should be a tuple of (wxWindow, function).
		In this case, the joystick events will be bound to that window, and 
		each button-down type event will call the specified function.
		jsid specifies which joystick to monitor (usually wx.JOYSTICK1, 
		aka 0, but can also be 1)'''
		
		self.do=function
		self.js=wx.Joystick(jsid)
		if self.js.GetNumberJoysticks()<1:
			del(self.js)
			raise StandardError("No Joystick")
		self.abort=False
		self.dt=time
		self.dz=dz
		self.jstats=self.profile()
		if bevents:
			(win, f)=bevents
			self.js.SetCapture(win)		
			wx.EVT_JOY_BUTTON_DOWN(win, f)

	def start(self):
		self.monitorThread=threading.Thread(target=self.monitor)
		self.monitorThread.start()

	def stop(self):
		self.abort=True

	def monitor(self):
		while not self.abort:
			sleep(self.dt)
			s=self.getState()
			self.do(s)

	def profile(self):
		stats={}
		stats['nb']=self.js.GetNumberButtons()
		stats['pov']=self.js.HasPOV()
		stats['xyrange']=(self.js.GetXMin(), self.js.GetXMax())
		if not self.js.HasRudder():
			stats['r']=False
		else:
			stats['r']=(self.js.GetRudderMin(), self.js.GetRudderMax())
		if not self.js.HasU():
			stats['u']=False
		else:
			stats['u']=(self.js.GetUMin(), self.js.GetUMax())
		if not self.js.HasV():
			stats['v']=False
		else:
			stats['v']=(self.js.GetVMin(), self.js.GetVMax())
		if not self.js.HasZ():
			stats['z']=False
		else:
			stats['z']=(self.js.GetZMin(), self.js.GetZMax())
		return stats	
		
	def getState(self):
		state={}
		p=self.js.GetPosition()
		mp=self.jstats['xyrange']
		mp=(mp[1]-mp[0])/2
		xp=p[0]-mp
		if abs(xp)<self.dz:
			xp=0.0
		else:
			xp=xp/float(mp+1)
		yp=p[1]-mp
		if abs(yp)<self.dz:
			yp=0.0
		else:
			yp=yp/float(mp+1)
		state['xy']=(xp, yp)
		b=[]
		bs=self.js.GetButtonState()
		state['b']=[bool(2**i & bs) for i in range(self.jstats['nb'])]
		if self.jstats['pov']:
			state['pov']=self.js.GetPOVPosition()
		if self.jstats['r']:
			r=self.js.GetRudderPosition()
			(rmi, rma)=self.jstats['r']
			state['r']=float(r-rmi)/(rma-rmi)
		if self.jstats['u']:
			r=self.js.GetUPosition()
			(rmi, rma)=self.jstats['u']
			state['u']=float(r-rmi)/(rma-rmi)
		if self.jstats['v']:
			r=self.js.GetVPosition()
			(rmi, rma)=self.jstats['v']
			state['v']=float(r-rmi)/(rma-rmi)
		if self.jstats['z']:
			r=self.js.GetZPosition()
			(rmi, rma)=self.jstats['z']
			state['z']=float(r-rmi)/(rma-rmi)
		return state				
		
def testFunc(jstate):
	print jstate
			
if __name__=="__main__":
	a=wx.PySimpleApp()
	j=JSMonitor(testFunc, time=2.5, jsid=0)
	print j.jstats
	#print j.getState()
	j.start()
	a.MainLoop()
