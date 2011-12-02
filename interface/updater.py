#!/usr/bin/env python
# encoding: utf-8
#Created by  on 2008-05-15.

# Copyright (C) 2008 Graham I Cummins
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA 02111-1307 USA
#

from mien.wx.base import BaseGui, wx, AWList
from mien.tools.updater import *

class UpadteManager(BaseGui):
	def __init__(self, master=None, **kwargs):
		BaseGui.__init__(self, master, title="Mien Update Manager", menus=["File"], pycommand=False, showframe=False)
		self.preferences=getPrefs()
		self.preferenceInfo=preferenceInfo		
		fmen=self.menus['File']
		id = wx.NewId()
		fmen.Insert(0, id, "Preferences")
		wx.EVT_MENU(self, id, self.setPreferences)
		id = wx.NewId()
		fmen.Append(id, 'Quit')
		wx.EVT_MENU(self, id, lambda x:self.Destroy())
		self.mainSizer = wx.BoxSizer(wx.VERTICAL)
		self.mainSizer.Add(wx.StaticText(self.main, -1, "MIEN: %s" % getMienDir()), 1, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.repostring=wx.StaticText(self.main, -1,"Repository:  %s/%s" % (self.preferences['Repository'],self.preferences['Rev'] ))
		self.mainSizer.Add(self.repostring, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.blockpath=wx.StaticText(self.main, -1,"Installing blocks to : %s" % (self.preferences['BlockInstall'], ))
		self.mainSizer.Add(self.blockpath, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		box=wx.BoxSizer(wx.HORIZONTAL)
		self.mods=AWList(self.main, -1, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
		self.mods.InsertColumn(0, "Package")
		self.mods.InsertColumn(1, "Local Version")
		self.mods.InsertColumn(2, "Repository Version")
		self.mods.SetColumnWidth(0, 200)
		box.Add(self.mods, 3,wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		bb=wx.BoxSizer(wx.VERTICAL)
		for com in [ ('Edit Config', self.setPreferences), ('Scan Repository', self.scan), ('Select All', self.sellect), ('Show Descriptions', self.info), ('Install/Update', self.update), ('Remove', self.kill)]:
			id = wx.NewId()
			btn=wx.Button(self.main, id, com[0])
			wx.EVT_BUTTON(self.main, id, com[1])
			bb.Add(btn, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
			
		box.Add(bb, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		
		self.mainSizer.Add(box, 15, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		
		self.repo={'deps':None, 'scan':None}
		
		self.fillList()
		
		
		self.main.SetSizer(self.mainSizer)
		self.main.SetAutoLayout(True)
		self.mainSizer.Fit(self.main)
		self.baseSizer.Fit(self)

	def onSetPreferences(self):
		self.repostring.SetLabel("Repository:  %s/%s" % (self.preferences['Repository'],self.preferences['Rev'] ))
		self.blockpath.SetLabel("Installing blocks to : %s" % (self.preferences['BlockInstall'], ))	
			
	def fillList(self):
		first=False
		if not self.repo['scan']:
			first=True
			self.packages=getStatus('nocheck')
		else:
			self.packages=getStatus(self.repo['scan'])
		self.mods.DeleteAllItems()
		for i, p in enumerate(self.packages):
			self.mods.InsertStringItem(i, p[0])
			if p[1]<0:
				l="Not Installed"
			else:
				l=str(p[1])	
			self.mods.SetStringItem(i, 1, l)
			if p[2]<0:
				if first:
					l=" -- "
				else:
					l='Not Available'	
			else:
				l=str(p[2])	
			self.mods.SetStringItem(i, 2, l)		
	
	def warn(self):
		if self.preferences['Warnings']!='on':
			return
		if haveApt():
			m=APT_MESSAGE+"\n (Set 'Warnings' to 'off' in File -> Preferences to disable this message)"
			self.showText(m, t="You con use Debian APT")
		svn=haveSvn()
		if svn:
			m=SVN_MESSAGE(svn)+"\n (Set 'Warnings' to 'off' in File -> Preferences to disable this message)"
			self.showText(m, t="Use SVN!")
				
			
	def scan(self, event):
		try:
			self.report("connecting to the repository ...")
			self.repo['scan']=checkRepo()
			self.report("done")
		except:
			self.report("Connection to repository failed (maybe change the url?)")
			return
		self.fillList()	
		self.selectOld()	
	
		
	
	def selectOld(self):
		some=False
		for i in range(self.mods.GetItemCount()):
			if self.packages[i][2]>self.packages[i][1]:
				self.mods.SetItemState(i, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
				some=True
			else:	
				self.mods.SetItemState(i, 0, wx.LIST_STATE_SELECTED)
		if not some:
			self.report("All packages are up to date")
	
	def sellect(self, event):
		for i in range(self.mods.GetItemCount()):
			self.mods.SetItemState(i, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
		pass
		
	def getSel(self):
		sel=[]
		for i in range(self.mods.GetItemCount()):
			s=self.mods.GetItemState(i, wx.LIST_STATE_SELECTED)
			if s:
				sel.append(self.packages[i])
		return sel		
			
	def info(self, event):
		if not self.repo['scan']:
			self.report('No repository info. Use "Scan Repository" first')
			return
		s=self.getSel()
		if not s:
			self.report("No selected packages")
			return
		msg=""	
		for p in s:
			pn=p[0]
			pd=self.repo['scan'][pn][2]
			msg+="%s: %s\n\n" % (pn, pd)
		self.showText(msg, t="Package Descriptions")
			
	
		
	def update(self, event):
		if not self.repo['scan']:
			self.report('No repository info. Use "Scan Repository" first')
			return	
		s=self.getSel()
		inst=[p[0] for p in s if p[1]<0]
		s=[p[0] for p in s if p[2]>p[1]]
		if not s:
			self.report("No selected packages need updates")
			return
		if 'core' in s:
			r=self.askUsr("Updating the Core package requires restarting MIEN. Continue? ")	
			if not r=='Yes':
				self.report("Aborted")
				return
		ok=True		
		for p in s:
			if not p in inst:
				try:
					self.report('updating %s' % p)
					update(p, self.repo['scan'])
					self.report('done updating %s' % p)
				except:
					self.report('update of %s failed' % p)
					ok=False	
			else:				
				try:
					self.report('installing %s' % p)
					self._cpkg=p
					install(p, self.repo['scan'], self.dep_handler)
					self.report('done installing %s' % p)
				except:
					raise
					self.report('install of %s failed' % p)
					ok=False	
		self.fillList()				
		if ok:
			msg="All updates complete. \n"
			msg+='You will need to exit and restart MIEN for all changes to take effect'
			self.showText(msg, t="Updates Complete")
		else:
			msg="There were errors during updates \n"
			msg+="The most likely reason for this is that you don't have file writing permission in the target directory. You can change the block install directory to ~/mienblocks to correct this. For core updates, you may need to run the updater as root, or get your system admin to provide you with write access to Python's 'site-packages' directory on your system"
			self.showText(msg, t="Oh Noes!")	
			
	def kill(self, event):
		s=self.getSel()
		s=[p[0] for p in s if p[1]>0]
		if not s:
			self.report("No selected packages")
			return
		if 'core' in s:
			self.report("Update Manager can not delete MIEN core")
			return
		r=self.askUsr("Are you sure you want to delete %i packages " % (len(s),)) 	
		if not r=='Yes':
			self.report("Aborted")
			return
		ok=True		
		for p in s:
			try:
				self.report('deleting  %s' % p)
				remove(p)
				self.report('%s is history' % p)
			except:
				self.report('removal of %s failed' % p)
				ok=False
		self.fillList()		
		if ok:
			msg="Removal complete. \n"
			msg+='You will need to exit and restart MIEN for all changes to take effect. Untill you do this, attempts to use functions from deleted blocks may cause criptic errors.'
			self.showText(msg, t="Removal Complete")
		else:
			msg="There were errors during removal \n"
			msg+="The most likely reason for this is that you don't have file writing permission in the target directory. You can change the block install directory to ~/mienblocks to correct this. For core updates, you may need to run the updater as root, or get your system admin to provide you with write access to Python's 'site-packages' directory on your system"
			self.showText(msg, t="Oh Noes!")	
	
		
	def dep_handler(self, dc):		
		print dc
		if dc[0]==3:
			self.showText("%s : This package isn't supported on your platform. Will not install" % self._cpkg)
			return 1
		elif dc[0]==1:
			self.showText("%s : The dependancy information for this package is missing. Installing it and hoping for the best" % self._cpkg)
			return 0
			
		msg="In order for the package you are installing to work, you will need to install some third party packages to provide dependancies.\n"
		msg+="Please install the following:\n"
		nb=[]
		for dp in dc[2]:
			if not dp[1]:
				nb.append(dp[0])
			msg+="%s (%s)\n" % (dp[0], dp[2])	
		self.showText("%s : %s" % (self._cpkg, msg))
		if nb:
			if self.repo['deps'] is None:
				self.repo['deps']=listRepDeps()
				for n in nb:
					if not n in self.repo['deps']:
						nb.remove(n)
		if nb:
			msg="The dependancies: "
			for n in nb:
				msg+='%s, ' % n
			msg +="can be automatically installed from the repository. Add them?"
			v=self.askUsr(msg) 	
			if v=='Yes':
				for n in nb:
					installRepDep(n)			
		return 0	
		
	def newDoc(self, x):
		self.warn()			



	
