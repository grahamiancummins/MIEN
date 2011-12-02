
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

import re
from mien.wx.graphs.graphGL import *
from mien.wx.base import BaseGui
from string import join
import mien.spatial.cvextend as cve
from mien.spatial.viewpoints import showDefault
import os.path

def get_source_file(o, chop=False):
	while 1:
		try:
			f=o.fileinformation['filename']
		except:
			f=None
		if f:
			if chop:
				f=os.path.split(f)[-1]
				f=os.path.splitext(f)[0]
			return f
		elif not o.container:
			return None
		else:	
			o=o.container

def nameHash(objs):
	d = {}
	for o in objs:
		d[str(o)]=o
	return d


class CellGraph(GraphGL):
	def __init__(self, master, cv=None):
		GraphGL.__init__(self, master)
		self.modelRefs={}
		self.cv=cv
		self.keybindings['m']=self.drawhbar
		self.keybindings['M']=self.drawvbar
		self.keybindings['b']=self.doBlink
		self.blink=None
		self.rulerticks=0


	def doBlink(self, event):
		if not self.blink:
			return
		#print "blink", self.blink
		for name in self.plots.keys():
			blink = False
			try:
				mr=self.modelRefs[name].get('mien.nmpml')
				if mr in self.blink:
					blink=True
			except:
				pass
			if blink:
				if self.cv.preferences["Blink Mode"] =='Highlight':
					if "blinked_color" in self.plots[name]:
						self.plots[name]['color']=self.plots[name]['blinked_color']
						del(self.plots[name]['blinked_color'])
					else:
						self.plots[name]['blinked_color']=self.plots[name]['color']
						self.plots[name]['color']=self.cv.preferences["Highlight Color"]
					self.recalc(name)
				else:	
					self.plots[name]["hide"]=not self.plots[name].get('hide')
		self.OnDraw()	
		
	def OnLeftClick(self, event):
		if event.ShiftDown():
			self.OnShiftClick(event)
		else:	
			pt = self.findMouse(event.GetX(), event.GetY())
			self.report(str(pt)+str(self.forward)+str(self.up)+"\nDistance from last click: %.4f microns" % (eucd(self.lastclick, pt), ))
			self.lastclick=pt
			self.highlightPoint(pt+self.forward)

	def OnShiftClick(self, event):
		pass

	def OnRightClick(self, event):
		if event.ShiftDown():
			self.OnShiftRight(event)
		else:		
			pt = self.findMouse(event.GetX(), event.GetY())
			self.viewpoint=pt
			self.OnDraw()


	def OnShiftRight(self, event):
		pass
			
	def highlightPoint(self, pt, color=(1.0,0,1)):
		self.SetCurrent()
		materialColor(color)
		glPointSize(6)
		glBegin(GL_POINTS)
		glVertex3fv(pt)
		glEnd()	
		glFlush()
		self.SwapBuffers()
	
	
	def drawhbar(self, event=None, color=(0,1.0,1)):
		pt = self.lastclick+self.forward
		right=cross(self.forward, self.up)
		htrans=2*right*self.extent*self.aspect
		le = pt - htrans
		re=pt+htrans
		materialColor(color)
		glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.0, 0.0, 0.0, 0.0])
		glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, list(color)+[0])
		glLineWidth(1)
		glBegin(GL_LINES)
		glVertex3fv(le)
		glVertex3fv(re)
		if self.rulerticks:
			th = self.up*self.extent*.01
			glVertex3fv(pt-th)
			glVertex3fv(pt+th)
			mht = sqrt(htrans**2).sum()
			tr = 0
			rpt=pt
			lpt=pt
			while tr<mht:
				rpt = rpt+self.rulerticks*right
				lpt = lpt-self.rulerticks*right
				glVertex3fv(rpt-th)
				glVertex3fv(rpt+th)
				glVertex3fv(lpt-th)
				glVertex3fv(lpt+th)
				tr += self.rulerticks
		glEnd()	
		glFlush()
		self.SwapBuffers()
		
	def drawvbar(self, event=None, color=(0,1.0,1)):
		pt = self.lastclick+self.forward
		vtrans=2*self.up*self.extent
		le = pt - vtrans
		ue=pt+vtrans
		materialColor(color)
		glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.0, 0.0, 0.0, 0.0])
		glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, list(color)+[0])
		glLineWidth(1)
		glBegin(GL_LINES)
		glVertex3fv(le)
		glVertex3fv(ue)
		if self.rulerticks:
			right=cross(self.forward, self.up)
			th = right*self.extent*.01
			glVertex3fv(pt-th)
			glVertex3fv(pt+th)
			mht = sqrt(vtrans**2).sum()
			tr = 0
			rpt=pt
			lpt=pt
			while tr<mht:
				rpt = rpt+self.rulerticks*self.up
				lpt = lpt-self.rulerticks*self.up
				glVertex3fv(rpt-th)
				glVertex3fv(rpt+th)
				glVertex3fv(lpt-th)
				glVertex3fv(lpt+th)
				tr += self.rulerticks
		glEnd()	
		glFlush()
		self.SwapBuffers()
	

	def	highlightSections(self, name, secs, parent=None):
		try:
			secind = self.modelRefs[name]['sections']
		except:
			self.report("Can't highlight sections in plot %s because it has no section index" % name)
			return
		inds = [i for i, x in enumerate(secind) if x[0] in secs]
		if 'permacolor' in self.__dict__.keys() and self.permacolor:
				
			col = self.plots[name]['colorlist']
			if not col:
				print 'No colors to preserve for {0}, setting to default color'.format(name)
				col = [self.plots[name]['color']] * self.plots[name]['data'].shape[0]
			if not inds:
				hlt = self.plots[name]['color']
			else:
				hlt = parent._manuallySelectColor()
		else:
			if not inds:
				col=None
			else:
				col = [self.plots[name]['color']] * self.plots[name]['data'].shape[0]
				hlt = iverseCol(self.plots[name]['color'])
		for i in inds:
			col[i]=hlt				
		self.plots[name]['colorlist'] = col
		self.recalc(name)
		self.OnDraw()
		
	def highlightcolor(self):
		return [1.0-c for c in self.clearcolor]

	def plotXML(self, object, **opts):
		defaults = {'cellstyle':self.cv.getCellStyle(), 
					'spherestyle':self.cv.preferences["Sphere Plot Style"],
					 'pointshape':self.cv.preferences["Density Plot Mode"], 			
					'showpointlabels':self.cv.preferences["Show Point Labels"], 
					'defaultpointsize':self.cv.preferences["Default Point Size"]}
		for k in defaults:
			if not k in opts:
				opts[k]=defaults[k]
		sf=get_source_file(object, chop=True)
		if not opts.has_key("name"): 
			opts['name'] = re.sub("\W", "_", object.name())
			if sf:
				opts['name']+='_'+sf
			if opts['name'] in self.plots:
				bn = opts['name']
				i = 2
				n = bn + "_%i" % i
				while n in self.plots:
					i += 1
					n = bn + "_%i" % i
				opts['name']=n
					
		if not opts.get("color"):
			col=object.attrib('color', True)			
			if col:
				col=convertColor(col, 'gl')
			else:
				col=self.getNewColor()
			opts['color']=col
		if object.__tag__=="Fiducial":
			data = object.getPoints()
			if object.attrib('displayHighlight'):
				col = self.highlightcolor()
				data=data.copy()
				data[:,3]*=3
			style = object.attrib("Style")
			if style=="line":
				opts['style']='contour'
				name=self.addLinesPlot(data[:,:3], **opts)
			else:
				if style=="points":
					w = object.attrib('width') or opts.get('defaultpointsize', 1)
					name=self.addPointPlot(data, width=w, **opts)				
				else:
					ss=opts.get("spherestyle", "spheres")
					if ss == "Fixed Points":
						name=self.addPointPlot(data, width=1, **opts)
					elif ss == 'Scaled Points':
						name=self.addPointPlot(data, width=1, setPointSize=data[:,3].mean(), **opts)
					else:
						name=self.addSpherePlot(data[:,:4], **opts)
				if object.point_labels and opts.get('showpointlabels'):
					for k in object.point_labels.keys():
						lab=object.point_labels[k]
						loc=data[k,:3]
						#n=self.addLabel(text=lab, loc=loc, charsize=2.0, color=opts['color'])
						n=self.addImageLabel(text=lab, loc=loc, border=False, size=10, color=opts['color'])
				#print data[:,3].min(), data[:,3].max(),data[:,3].mean()
			self.modelRefs[name]={'mien.nmpml':object}		
		elif object.__tag__=='Cell':
			cellStyle=opts.get('cellstyle', {"plot":"frustum",
							"min":0.0,
							"linerad":1.0})
			if cellStyle['plot']=='mixed':
				pts=object.get_drawing_coords(spheres=True)
				dci=object.drawingCoordIndex(spheres=True)
				opts['linerad']=cellStyle['linerad']
			else:	
				pts=object.get_drawing_coords(spheres=False)	
				dci=object.drawingCoordIndex(spheres=False)
				opts['width']=cellStyle['linerad']
			if object.attrib('displayHighlight'):
				col = self.highlightcolor()
				pts = pts.copy()
				pts[:,3]*=3
			dci=[x for i, x in enumerate(dci) if not i%2] 
			if cellStyle['min']:
				m=cellStyle['min']
				pts[:,3]=where(logical_and(pts[:,3]!=0, pts[:,3]<m), m, pts[:,3])
			if cellStyle['plot']=='mixed':
				name=self.addMixedPlot(pts, **opts)
			elif cellStyle['plot']=='line':
				opts['style']="lines" 
				name=self.addLinesPlot(pts[:,:3], **opts)
			else:
				name=self.addFrustaPlot(pts, **opts)
			self.modelRefs[name]={'mien.nmpml':object,'sections':dci}
		elif object.__tag__=="SpatialField":
			pts=object.uniformSample()
			if not opts.get('pointshape'):
				#opts['pointshape']='cart'
				opts['pointshape']='points'
			e = object.attrib("Edge")
			if type(e) in [tuple, list]:
				e=array(e)
			elif type(e) == ndarray:
				pass
			else:
				e=ones(3)*e
			opts['edge']=e
			opts['mindensity']=object.attrib('mindensity')
			opts['maxdensity']=object.attrib('maxdensity')
			opts['anchor']=object.attrib("Origin")
			opts['up'] = array(object.attrib("Vertical") or (0.0,1.0,0.0))
			opts['forward']=array(object.attrib("Depth") or (0.0,0.0,-1.0))
			name=self.addDensPlot(pts, **opts	)
			self.modelRefs[name]={'mien.nmpml':object,'weight':opts['maxdensity']}
		elif object.__tag__=='Data' and object.stype()=='image':
			ul=array(object.attrib('SpatialAnchor') or (0,0,0))
			y=array(object.attrib('SpatialVertical') or (0,1,0))
			z=array(object.attrib('SpatialDepth') or (0,0,-1))
			x=cross(z, y)
			pw=object.attrib('PixelWidth') or 1.0
			ph=object.attrib('PixelHeight') or pw
			pd=object.attrib('StackSpacing') or 1.0
			size=object.getData().shape[:2]
			down=z*pd
			w=pw*x*size[0]
			h=ph*y*size[1]
			dat=vstack([ul, w, h, down])
			opts['imagedata']=object.getData()
			opts['crange']=object.attrib('ColorRange')
			opts['pcolor']=object.attrib('pseudocolor')
			opts['transparent']=object.attrib("transparent")
			if opts['transparent']:
				opts['ontop']=5
			opts['transparent_mode']=object.attrib("transparent_mode")
			name=self.addImageStack(dat, **opts)
			self.modelRefs[name]={'mien.nmpml':object}
		else:
			self.report("Don't know how to plot %s" % object.__tag__)
			return None
		return name	
			
	def update_self(self, **kwargs):
		event=kwargs.get('event', 'modify').lower()
		for object in self.getObjectsFromKWArgs(kwargs):
			for k in self.modelRefs.keys():
				if self.modelRefs[k].get('mien.nmpml')==object:
					if event == "Delete":
						self.delPlot(pn=k)
					elif event == "Modify":
						self.delPlot(pn=k)
						self.plotXML(object, name=k)
	

	
	def showTimeSeries(self, t, ind=False):
		for pn in self.modelRefs.keys():
			if not self.modelRefs[pn].has_key("TimeSeries"):
				continue
			alldat=self.modelRefs[pn]["TimeSeries"]
			if alldat==None:
				continue
			if ind:
				step=t
			else:	
				step=int(t/self.modelRefs[pn].get("TimeSeriesStep"))
			if not 0<=step<len(alldat):
				continue
			self.plots[pn]['colorlist']=alldat[step][:]
			self.recalc(pn)
		self.OnDraw()

	def colorGroup(self, gn, col, hide=False, draw=True):
		#print gn, col, hide
		col=convertColor(col, 'gl')
		cn=convertColor(col, 'py')
		for name in self.plots.keys():
			try:
				mr=self.modelRefs[name].get('mien.nmpml')
			except:
				continue
			if gn in cve.getDisplayGroup(mr, False):
				self.plots[name]['color']=col
				mr.setAttrib('color', cn, True)
				self.recalc(name)
				self.plots[name]["hide"]=hide
		if draw:	
			self.OnDraw()	

		

	def delPlot(self, event=None, pn=None, draw=True):
		if not pn:
			pn=self.selectPlot()
			if not pn:
				return
		del(self.plots[pn])
		del(self.modelRefs[pn])
		if draw:
			self.OnDraw()

	def clearAll(self):
		self.plots={}
		self.modelRefs={}
		self.OnDraw()


def isOfDisplayType(el, dt):
	if el.__tag__=='Cell':
		if dt=='Cells':
			return True
	elif el.__tag__=='Data':
		if dt=='Images':
			if el.stype()=='image':
				return True
	elif el.__tag__=='SpatialField':
		if dt=='Fields':
			return True
	elif dt == "Spheres":
		if el.attrib("Style")=='spheres':
			return True		
		elif el.attrib("Style")=='points' and not el.point_labels:
			return True
	elif dt=="Named Points":
		if el.point_labels:
			return True
	elif dt=="Lines":
		if el.attrib("Style")=='line':
			return True
 	return False

class CellViewer(BaseGui):
	def __init__(self, master=None, **kwargs):
		if master:
			pc=False
		else:
			pc=True
		BaseGui.__init__(self, master, title="Cell Viewer", menus=["File", "Display", "Selection","Extensions", "Spatial"], pycommand=pc,height=4, showframe=False)
		
		controls=[
				  ["File", "Apply Filter to File", self.pruneFile],
				  ["Display", "Select Plots", self.selPlots],
				  ["Display", "Group Plots", self.groupPlots],
				  ["Display", "Hide/Color Groups", self.groupOpts],
				  ["Display", "Set View Toggle", self.setBlink],
				  ["Display", "Change Background Color", self.setClearColor],
				  ["Display", "Replot", self.addAll],
				  ["Display", "Filter", self.setFilter],
				  ['Selection',"Clear Selection", self.selectNone],
				  ['Selection',"Show Selection", self.showSelection],
				  ['Selection',"Export Point", self.exportPoint],
				  ['Selection',"Import Point", self.importPoint],
				  ['Selection',"Select Section", self.selectSec],
				  ['Selection',"Select Radius", self.selectSphere],
				  ['Selection',"Select Distal", self.selectDistal],
				  ['Selection',"Select Proximal", self.selectProx],
				  ['Selection',"Invert Selection", self.selectInverse],
				  ['Selection',"Select Path", self.selectPath],
				  ['Selection',"Center View on Point", self.centerOnPoint],
				  ['Selection',"Select Distal", self.selectDistal],
				  ['Selection',"Keep Select Colors", self.keepSelectionColors],
				  ]
		
		self.preferenceInfo=[
			{"Name":"Cell Plot Style",
			'Type':'List',
			'Value':['frustum', 'mixed', 'line']},	
			{"Name":"Sphere Plot Style",
			'Type':'List',
			'Value':['Spheres', 'Fixed Points', 'Scaled Points']},		
			{"Name":"Always Reload Extensions",
			"Type":"List",
			"Value":[True, False]},		
			{"Name":"Show Point Labels",
			"Type":"List",
			"Value":[False, True]},	
			{"Name":"Blink Mode",
			"Type":"List",
			"Value":['Hide', 'Highlight']},		
			{"Name":"Density Plot Mode",
			"Type":"List",
			"Value":["cart", "points"]},
			{"Name":"Non-Selected Plots",
			'Type':'List',
			'Value':['Hidden', 'Faded']}]
		
		self.preferences = {"Cell Plot Style":'frustum',
				"Min Diameter":0.0,
				"Ruler Ticks":100.0,
				"Blink Mode":"Hide",
				"Highlight Color":(1.0, 1.0, 1.0),
				"Show Point Labels":False,
				"Sphere Plot Style":'Spheres',
				"Always Reload Extensions":False,
				"Density Plot Mode":"points",
				"Line Width":1,
				"Default Point Size":1,
				'Non-Selected Plots':'Hidden'}

		self.xm=None
		self.document = None
		if master:
			self.xm = master
			controls.insert(0, ["Selection", "Import Selection", self.impSel])
			controls.insert(0, ["Selection", "Export Selection", self.expSel])
			self.document = self.xm.document
			controls.append(["File", "Close", lambda x: self.Destroy()])
			self.fillMenus(controls)
		else:
			controls.append(['Display', 'Data Editor', self.launchDE])
			self.fillMenus(controls)
			self.stdFileMenu()
		self.displayfilter=None	

				
		self.mainSizer = wx.BoxSizer(wx.VERTICAL)
		self.main.SetSizer(self.mainSizer)
		self.main.SetAutoLayout(True)
		self.graph=CellGraph(self.main, self)
		self.graph.report=self.report
		self.graph.OnShiftClick=self.selectObj
		self.graph.OnShiftRight=self.selectNearest
		self.graph.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))

		
		self.mainSizer.Add(self.graph, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)
		self.graph.Show(True)
		self.graph.SetDropTarget(self.dropLoader)

		self.mainSizer.Fit(self.main)
		self.SetSize(wx.Size(600,700))
		
		for s in self.graph.global_options:
			lpn="graph - %s" % (s,)
			val=getattr(self.graph, s)	
			self.preferences[lpn]=val
		self.loaddir=""
		self.savedir=""
		self.selected=[]
		self._foundLastPoint = []
		self._foundSpatialPoint = []
		self.extmod=cve.CVExtMod(self)
		self.extmod.makeMenus()
		self.load_saved_prefs()
		self.graph.rulerticks = self.preferences["Ruler Ticks"]
	
	def launchDE(self, event=None):
		from mien.interface.main import MienGui
		d=MienGui(self)
		d.newDoc(self.document)
	
	def setBlink(self, event):
		self.graph.blink = self.getElements()
	
	def onSetPreferences(self):
		self.graph.rulerticks = self.preferences["Ruler Ticks"]
		for s in self.preferences.keys():
			if s.startswith('graph - '):
				gpn=s[8:]
				setattr(self.graph, gpn, self.preferences[s])
		self.addAll()
			
	def groupPlots(self, event=None):
		e = self.getPlotTargets()
		els=nameHash(e)
		l = self.askParam([{"Name":"Group Name",
							"Value":"Group"},
							{"Name":"Which Objects",
							"Type":"Select",
							"Value":els.keys()}])
		if not l:
			return []
		gn=l[0]
		grp = self.document.getElements('Group', gn)
		if grp:
			grp = grp[0]
		else:
			col=self.graph.getNewColor()
			grp = self.createElement("Group", {"Name":gn, 'color':col})
			self.document.newElement(grp)
		for k in l[1]:
			o=els[k]
			if "DisplayGroup" in o.attributes:
				del(o.attributes["DisplayGroup"])
			o.move(grp)
		self.graph.colorGroup(gn, grp.attrib('color'))	

	def getGroup(self, name=None):
		e = self.getPlotTargets()
		g={}
		for x in e:
			gns=cve.getDisplayGroup(x,False)
			for gn in gns:
				if not g.has_key(gn):
					g[gn]=[]
				g[gn].append(x)
		if name:
			return g.get(name)
		if not g:
			self.report("No Groups")
			gn=None
		elif len(g)==1:
			gn=g.keys()[0]
		else:
			l = self.askParam([{"Name":"Which Group",
							"Type":"List",
							"Value":g.keys()}])
			if l:
				gn=l[0]
			else:
				gn=None
		return gn
		
	def groupOpts(self, event=None):
		gn=self.getGroup()
		if not gn:
			return
		gm=self.getGroup(gn)
		col=(.5,.5,.5)
		if gm:
			c=gm[0].attrib('color')
			if c:
				col = convertColor(c, 'gl')
		l = self.askParam([{"Name":"Color",
							"Browser":GLColorBrowser,
							"Value":col},
							{"Name":"Visible?",
							"Type":"List",
							"Value":["Yes", "No"]}])
		if not l:
			return []
		if l[1]=="Yes":
			hide=False
		else:
			hide=True
		self.graph.colorGroup(gn, l[0], hide)	


	def setClearColor(self, event=None):
		l = self.askParam([{"Name":"Color",
							"Browser":GLColorBrowser,
							"Value":self.graph.clearcolor}])
		if not l:
			return []
		self.graph.clearcolor=list(l[0])
		self.graph.OnDraw()


	def setFilter(self, event=None):
		d=self.askParam([{"Name":"Display",
							"Type":"Select",
							"Value":["Cells", "Spheres", "Fields","Named Points", "Lines", "Images"]}])
		if d==None:
			return
		self.displayfilter=d[0]
		self.report('filter set to %s' %(str(d[0] or None),)) 
		self.refreshPlots()

	def pruneFile(self, event=None):
		els=self.getVisible()
		for e in self.getPlotTargets(False):
			if not e in els:
				e.sever()
		self.refreshPlots()

	def getPlotName(self, obj):
		for k in self.graph.modelRefs.keys():
			if not self.graph.modelRefs[k].get('aux') and self.graph.modelRefs[k].get('mien.nmpml')==obj:
				return k
		return None
			
	def update_self(self, **kwargs):
		self.extmod.update_self(**kwargs)
		event=kwargs.get('event', 'modify').lower()
		if event=='rebuild':
			self.addAll()
		else:	
			plotted=set([v['mien.nmpml'] for v in self.graph.modelRefs.values()])
			changed = plotted.intersection(self.getObjectsFromKWArgs(kwargs))
			self.refreshPlots(changed)	
			
			

	def getPlotTargets(self, usefilter=True):
		e=self.document.getElements(["Fiducial", "Cell", "SpatialField"])
		images=self.document.getElements('Data', {'SampleType':'image'})
		e.extend([i for i in images if i.attrib('SpatialAnchor')])
		if usefilter and self.displayfilter:
			matches=[]
			for et in self.displayfilter:
				matches.extend([x for x in e if isOfDisplayType(x, et)])
			e=matches	
		return e
	
	def getCell(self):
		cells = [e for e in self.getVisible() if e.__tag__=="Cell"]
		if len(cells)==0:
			self.report("No cells found!")
			return None
		elif len(cells)==1:
			return cells[0]
		else:
			cells=nameHash(cells)
			d=self.askParam([{"Name":"Choose Cell",
							  "Type":"List",
							  "Value":cells.keys()}])
			if not d:
				return None
			return cells[d[0]]
	
	def getCellStyle(self):
		cs={}
		cs["plot"]=self.preferences["Cell Plot Style"]
		cs["min"]=self.preferences["Min Diameter"]
		cs["linerad"]=self.preferences["Line Width"]
		return cs
	
	def addAll(self, event=None):
		#import time; t = time.time()
		if not self.document:
			return
		self.graph.clearAll()
		e=self.getPlotTargets()
		for o in e:
			n=self.graph.plotXML(o)
			#print o, n, len(self.graph.plots)
		self.extmod.addAll()
		self.graph.OnDraw()
		#print time.time() - t
		

	def refreshPlots(self, event=None, changed=[]):
		add=self.getPlotTargets()
		for k in self.graph.plots.keys():
			try:
				ke = self.graph.modelRefs[k]['mien.nmpml']
				if ke in add and not ke in changed:
					add.remove(ke)
					continue
			except:
				pass
			self.graph.delPlot(None, k, False)
		for e in add:
			self.graph.plotXML(e)
		self.graph.OnDraw()


	def onNewDoc(self):
		e = self.getPlotTargets(False)
		gcol={}
		for el in e:
			dg=cve.getDisplayGroup(el)
			if dg and not el.attrib('color', True):
				if not gcol.has_key(dg):
					gcol[dg]=self.graph.getNewColor(used=gcol.values())
				col=convertColor(gcol[dg], 'py')
				grp = self.document.getElements("Group", dg)
				if grp:
					grp[0].setAttrib('color', col)
				else:
					el.setAttrib('color', col)
		self.addAll()
		self.graph.stdView()	
		showDefault(self)
		
		
	def getVisible(self):
		els=[]
		for k in self.graph.plots.keys():
			if self.graph.plots[k].get('hide'):
				continue
			try:
				els.append(self.graph.modelRefs[k]['mien.nmpml'])
			except:
				self.report('Plot %s has no associated model' % k)
			
		return list(set(els))
			


	def getOneElement(self):
		e = self.getPlotTargets()
		if len(e)>45:
			return e[0]
		els=nameHash(e)			
		l = self.askParam([{"Name":"Which Objects",
							"Type":"List",
							"Value":sorted(els)}])
		if not l:
			return None
		return els[l[0]]
		
		
	def getElements(self, multi=True):
		if not multi:
			self.getOneElement()			
		targets = self.getPlotTargets()
		dgroups = {}
		for el in targets:
			dgs = cve.getDisplayGroup(el, False)
			for dg in dgs:
				if not dg in dgroups:
					dgroups[dg]=[]
				dgroups[dg].append(el)
		dgn = {}
		for k in dgroups:
			n = len(dgroups[k])
			if n > 1:
				gn = "%s (%i)" % (k, n)
				dgn[gn] = k
		if len(targets)>45 and not dgn:
			self.report("Too many unclassified elements for interactive selection")
			return targets
		els=nameHash(targets)
		keys =  sorted(dgn)+sorted(els)
		l = self.askParam([{"Name":"Which Objects",
							"Type":"Select",
							"Value":keys}])
		if not l:
			return []
		select = []
		for name in l[0]:
			if name in dgn:
				select.extend(dgroups[dgn[name]])
			else:
				el = els[name]
				select.append(el)
		select = list(set(select))
		return select	

	def selPlots(self, event=None):
		els= self.getElements()
		for pn in self.graph.plots.keys():
			hide = True
			try:
				if self.graph.modelRefs[pn]['mien.nmpml'] in els:
					hide=False
			except:
				pass
			if not hide:
				self.graph.plots[pn]["hide"]=False
			else:
				if self.preferences['Non-Selected Plots']=='Hidden':
					self.graph.plots[pn]["hide"]=True
				else:
					self.graph.plots[pn]["hide"]='fade'
					#self.graph.recalc(pn)
		self.graph.OnDraw()

	def selectNone(self, event=None):
		self._foundLastPoint = []
		self._foundSpatialPoint=[]
		self.selected=[]
		self.showSelection()

	def _manuallySelectColor(self, event=None):
		l = self.askParam([{"Name":"Color",
						"Browser":GLColorBrowser,
							"Value":self.graph.clearcolor}])
		if not l:
			return []
		else:
			return tuple(l[0])

	def showSelection(self, event=None):
		self.report("%i objects selected" % len(self.selected))
		if not self._foundLastPoint:
			pts="None"
		else:
			pts=""
			for p in self._foundLastPoint:
				pts+="%s.%s(%.3f) " % (p[0].name(), p[1], p[2])		
		self.report("pts selected: %s" % pts)
		secsel={}
		cids={}
		for c in self.document.getElements("Cell"):
			name=self.getPlotName(c)
			cids[c.upath()]=name
			secsel[name]=[]
		for sec in self.selected:
			name=cids[sec.container.upath()]
			secsel[name].append(sec.name())	
		for path in secsel.keys():
			self.graph.highlightSections(path, secsel[path], self)
		for p in self._foundLastPoint:
			cell, sec, rel=p[:3]
			pt=cell.absoluteLocation((sec, rel))
			self.graph.highlightPoint(pt[:3]-self.graph.forward*1.1*pt[3])
	
	def centerOnPoint(self, event=None):
		if not self._foundSpatialPoint:
			self.report("No selected point.")
			return
		pt = self._foundSpatialPoint[0]
		self.graph.centerOnPoint(pt)
		
	
	def selectObj(self, event=None):
		pt=self.graph.findMouse(event.GetX(), event.GetY())
		cell=self.getCell()
		pts=cell.getPoints()
		diams=pts[:,3]
		pts=pts[:,:3]-pt
		depths=dot(pts, self.graph.forward)
		inrange=nonzero1d(logical_and(depths>0, depths<self.graph.depthoffield))
		depths=take(depths, inrange)
		dists=eucd(take(pts, inrange, 0), array([0,0,0.0]))-depths
		top=argmin(dists)
		top=inrange[top]
		sec, rel = cell.nthPoint(top)
		pt=cell.absoluteLocation((sec, rel))
		name=self.getPlotName(cell)
		s = " %.3f, %.3f, %.3f, [%.3f] (%s.%s(%.3f)) " % (pt[0], pt[1], pt[2],2*pt[3],name, sec,rel)
		self.report(s)
		self.graph.highlightPoint(pt[:3]-1.1*pt[3]*self.graph.forward)
		self._foundLastPoint.insert(0, [cell, sec, rel, name])
		self._foundLastPoint=self._foundLastPoint[:2]
		self._foundSpatialPoint.insert(0, pt[:3])
		self._foundSpatialPoint=self._foundSpatialPoint[:2]

	def selectNearest(self, event=None):
		#fids=[e for e in self.getVisible() if e.__tag__=='Fiducial']
		fids=[e for e in self.getVisible()]
		closest=None
		pt=self.graph.findMouse(event.GetX(), event.GetY())
		for fid in fids:
			pts=fid.getPoints()
			diams=pts[:,3]
			pts=pts[:,:3]-pt
			depths=dot(pts, self.graph.forward)
			inrange=nonzero1d(logical_and(depths>0, depths<self.graph.depthoffield))
			if inrange.shape[0]==0:
				continue
			depths=take(depths, inrange, 0)
			dists=eucd(take(pts, inrange, 0), array([0,0,0.0]))-depths
			top=argmin(dists)
			dmin=dists[top]
			top=inrange[top]
			if not closest:
				closest=[fid, top, dmin]
			elif dmin<closest[2]:
				closest=[fid, top, dmin]
		name=closest[0].name()
		pt=closest[0].getPoints()[closest[1]]
		try:
			dia=pt[3]
		except:
			dia=.5
		s = " %.3f, %.3f, %.3f, [%.3f] (%s[%i]) " % (pt[0], pt[1], pt[2],2*dia,name, closest[1])
		dg=cve.getDisplayGroup(closest[0], False)
		if dg:
			s+= "(group - %s)" % ("/".join(dg),)
		self.report(s)
		self.graph.highlightPoint(pt[:3]-1.1*dia*self.graph.forward)
		
		self._foundLastPoint.insert(0, (closest[0], closest[1]))
		self._foundLastPoint=self._foundSpatialPoint[:2]
		self._foundSpatialPoint.insert(0, pt[:3])
		self._foundSpatialPoint=self._foundSpatialPoint[:2]
		if len(self._foundSpatialPoint)>1:
			lp=self._foundSpatialPoint[1]
			pt=self._foundSpatialPoint[0]
			dist=eucd(lp, pt)
			self.report("Distance from last point: %.4f" % dist)
	
 
	def exportPoint(self, event=None):
		if not self._foundLastPoint:
			self.report("No points selected")
			return
		cell, sec, loc=self._foundLastPoint[0][:3]
		si = cell.getSection(sec)
		pind = si.ptAtRel(loc)
		pcs = self.document.getElements(["Recording", "IClamp"])
		pcd = {}
		for e in pcs:
			pcd[str(e)]=e
		d = self.askParam([{"Name":"Where",
							"Type":"List",
							"Value":pcd.keys()}])
		if not d:
			return
		
		targ = pcd[d[0]]
		sec=cell._sections[sec]
		rel=sec.relLocOfPtN(pind)
		nelems=len(targ.getTypeRef("Section"))
		self.xm.makeElem("ElementReference", {"Name":"Location",
							"Target":sec.upath(),
							"Data":str(rel),
							"Index":str(nelems)},
							targ)


	def importPoint(self, event):
		pcs = self.document.getElements(["Recording", "IClamp"])
		pcd = {}
		for e in pcs:
			pcd[str(e)]=e
		d = self.askParam([{"Name":"From Where",
							"Type":"List",
							"Value":pcd.keys()}])
		if not d:
			return
		#FIXME	
		


	def splitSec(self, event=None):
		cell, sec, loc=self._foundLastPoint[0][:3]
		si = cell.getSection(sec)
		si.splitAtRel(loc)
		if self.xm:
			self.update_all(object=si)
		
	def selectSec(self, event=None):
		cell, sec, loc=self._foundLastPoint[0][:3]
		si = cell.getSection(sec)
		self.selected.append(si)
		self.showSelection()

	def selectSphere(self, event=None):
		cell, sec, loc=self._foundLastPoint[0][:3]
		d=self.askParam([{"Name":"Length (microns)",
						  "Value":100.0},
						 {"Name":"Direction",
						  "Type":"List",
						  "Value":["All", "Proximal", "Distal"]}])
		if not d:
			return
		secs = cell.getWithinPathLength((sec, loc), d[0], d[1])
		self.selected.extend([cell.getSection(s) for s in secs])
		self.showSelection()
	
	def keepSelectionColors(self, event=None):
		l = self.askParam([{"Name":"Keep highlighted selections \nhighlighted?  You will need \nto keep track of which \ncolor coresponds to the\ncurrent selection.",
							"Type":"List",
							"Value":[True, False]}])
		if not l:
			return []	
		self.graph.permacolor= l[0]

	def selectDistal(self, event=None):
		cell, sec, loc=self._foundLastPoint[0][:3]
		secs = [cell.getSection(n) for n in cell.branch(sec)]
		self.selected.extend(secs)
		self.showSelection()

	def selectProx(self, event=None):
		cell, sec, loc=self._foundLastPoint[0][:3]
		si = cell.getSection(sec)
		secs = [si]
		while 1:
			si = si.parent()
			if not si:
				break
			si = cell.getSection(si)
			secs.append(si)
		self.selected.extend(secs)
		self.showSelection()

	def selectInverse(self, event=None):
		try:	
			cell, sec, loc=self._foundLastPoint[0][:3]
		except:	
			cell=self.getCell()
		a=set(cell._sections.values())
		ns=a-set(self.selected)
		self.selected=list(ns)
		self.showSelection()
		
	def selectPath(self, cell,event=None):
		if not len(self._foundLastPoint)>1:
			self.report("Need two selected points to build path")
			return
		cell, sec, loc=self._foundLastPoint[0][:3]
		cell2, sec2, loc2=self._foundLastPoint[1][:3]
		if  cell!=cell2:
			self.report("The selected points are not in the same cell. There is no path between them.")
			return
		secs = cell.getPath(sec, sec2)[1]
		secs.extend([sec, sec2]) 
		secs = [cell.getSection(n) for n in secs]
		self.selected.extend(secs)
		self.showSelection()


	def impSel(self, event=None):
		self._foundLastPoint = []
		self.selected= [self.xm.objecttree.GetPyData(s) for s in self.xm.contextMenuSelect]
		self.report("imported %i section selection" % len(self.selected))
		self.showSelection()

	def expSel(self, event=None):
		self.xm.contextMenuSelect=[]
		try:
			self.xm.objecttree.UnselectAll()
		except:
			pass
		for si in self.selected:
			self.xm.objecttree.SelectItem(si._guiinfo["treeid"])
			self.xm.objecttree.EnsureVisible(si._guiinfo["treeid"])
			self.xm.contextMenuSelect.append(si._guiinfo["treeid"])
		self.report("Exported %i selected sections to mien.nmpml." % len(self.selected) )	

