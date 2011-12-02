
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
import os
from mien.math.sigtools import *
from string import join
import random, mien.parsers
from mien.wx.base import wx, BaseGui
from mien.nmpml.data import newData
from mien.parsers.nmpml import forceGetPath

def nameHash(objs):
	d = {}
	for o in objs:
		d[str(o)]=o
	return d

def renameSection(sec, newname):
	print "renaming", str(sec), "=>", newname
	op = sec.upath()
	cell=sec.container
	kids=[cell._sections[s] for s in cell.getChildren(sec.name())]
	for k in kids:
		print  str(k), " Parent => ", newname
		k.setAttrib("Parent",newname)
	sec.setAttrib("Name",newname)
	cell.refresh()
	doc = sec.xpath(True)[0]
	np=sec.upath()
	refs=doc.getElements("ElementReference")
	for r in refs:
		s=r.attrib("Target")
		if s and s.startswith(op):
			print "%s references the renamed object. Adjusting target path" % str(r)
			r.setAttrib("Target", s.replace(op, np))

SYNPROP={
	'AfferentClass01':{"Length":1200, "Direction":225, "Cercus":'L', 'Latency':4.0},
	'AfferentClass02':{"Length":1200, "Direction":315, "Cercus":'L', 'Latency':4.0},
	'AfferentClass03':{"Length":1200, "Direction":45 , "Cercus":'L', 'Latency':4.0},
	'AfferentClass04':{"Length":1200, "Direction":135, "Cercus":'L', 'Latency':4.0},
	'AfferentClass05':{"Length":800, "Direction":225, "Cercus":'L' , 'Latency':4.0},
	'AfferentClass06':{"Length":800, "Direction":315, "Cercus":'L' , 'Latency':4.0},
	'AfferentClass07':{"Length":800, "Direction":45 , "Cercus":'L' , 'Latency':4.0},
	'AfferentClass08':{"Length":800, "Direction":135, "Cercus":'L' , 'Latency':4.0},
	'AfferentClass09':{"Length":1200, "Direction":135, "Cercus":'R', 'Latency':4.0},
	'AfferentClass10':{"Length":1200, "Direction":45 , "Cercus":'R', 'Latency':4.0},
	'AfferentClass11':{"Length":1200, "Direction":315, "Cercus":'R', 'Latency':4.0},
	'AfferentClass12':{"Length":1200, "Direction":225, "Cercus":'R', 'Latency':4.0},
	'AfferentClass13':{"Length":800, "Direction":135, "Cercus":'R' , 'Latency':4.0},
	'AfferentClass14':{"Length":800, "Direction":45 , "Cercus":'R' , 'Latency':4.0},
	'AfferentClass15':{"Length":800, "Direction":315, "Cercus":'R' , 'Latency':4.0},
	'AfferentClass16':{"Length":800, "Direction":225, "Cercus":'R' , 'Latency':4.0},
	'AfferentClass17':{"Length":1200, "Direction":45, "Cercus":'L' , 'Latency':8.0},
	'AfferentClass18':{"Length":1200, "Direction":315 , "Cercus":'R' , 'Latency':8.0},
}

def getSynapseProperties(type, Mean=False, String=False):
	lenstddev=100
	dirstddev=10
	d={}
	d.update(SYNPROP[type])
	if not Mean:
		d['Direction']=round(normal(d['Direction'], dirstddev))
		d['Direction'] = d['Direction']%360
		d['Length'] = round(normal(d['Length'], lenstddev))
	if String:
		ln="S"
		if d['Length']>600:
			ln="M"
		if d['Length']>1000:
			ln="L"
		return "%s%i%s" % (d['Cercus'], d['Direction'], ln)
	else:
		return d



def synapseFree(section, cell):
	l=[section]
	if not section.getElements("Synapse"):
		for k in cell.getChildren(section.name()):
			l.extend(synapseFree(cell._sections[k], cell))
	return l

def getSynapseClasses(atr):
	l=array([225, 315, 45, 135])
	clid=argmin(abs(l-float(atr["Direction"])))
	if float(atr["Length"]) < 1000:
		clid+=4
	if atr["Cercus"]=="R":
		clid+=8
	return clid

class CellEditor(BaseGui):
	def __init__(self, gui, cell):
		self.gui=gui
		self.cell=cell
		self.selectedSections = self.cell._sections.values()
		
		
		BaseGui.__init__(self, gui, title="Edit Cell %s" % cell.name(), menus=["File", "Selection", "Synapse", "Mechanism","Measurements", "Morphology"], pycommand=True,height=4)
		commands=[["File", "Quit", lambda x: self.Destroy()],
				  ["Selection", "Select Sections", self.makeSel],
				  ['Selection', 'Select Spatial Region', self.selectLocation],
				  ["Selection", "Export Selection", self.exportSel],
				  ["Selection", "Import Selection", self.importSel],
				  ["Selection", "Clear Selection", self.killSel],
				  ["Synapse", "Synapse Info", self.synapseInfo],
				  ["Synapse", "Make Masks", self.makeMasks],
				  ["Synapse", "Mask Selected Sections", self.makeUniformMask],
				  ["Synapse", "Make Synapses", self.makeSyn],
				  ["Synapse", "Remove Synapses", self.delSyn],
				  ["Synapse", "Scramble Synapses", self.randomSyn],
				  ["Synapse", "Edit Synapses", self.editSyn],
				  ["Mechanism", "Set Mechanism Density", self.setProperty],
				  ["Mechanism", "Copy Mechanisms", self.dupMech],
				  ["Mechanism", "Insert Mechanism", self.addMech],
				  ["Mechanism", "Remove Mechanism", self.delMech],
				  ["Mechanism", "Strip All Mechanisms", self.nukeMech],
				  ["Mechanism", "Set passive properties", self.setPass],
				  ["Measurements", "Input Impedance", self.getRin],
				  ["Morphology", "Random Connectivity", self.fuzzBall],
				  ["Morphology", "Cut tips", self.antiFuzzBall],
				  ["Morphology", "Uniform Sections", self.splitCell],
				  ["Morphology", "Human Readable Names", self.assignNames],
				  ["Morphology", "Simple Names", self.simpleNames],
				  ["Morphology", "Load Morphology", self.getCellMorph]]
		
		self.fillMenus(commands)
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(wx.StaticText(self.main, -1, "%s" % str(self.cell)), 0, wx.ALIGN_CENTRE|wx.ALL, 5)
		self.info=wx.StaticText(self.main, -1, "00000 Sections, 00000 Synapses, 00 Channel Types")
		sizer.Add(self.info, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		self.nsel=wx.StaticText(self.main, -1,"%i (All) Sections Selected" % len(self.selectedSections))
		sizer.Add(self.nsel, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
		
		self.main.SetSizer(sizer)
		self.main.SetAutoLayout(True)
		sizer.Fit(self)
		
		self.setInfo()
		self.SetSize(wx.Size(600,300))
		
	
	def selectLocation(self, event=None):
		d=self.askParam([{'Name':'X min','Value':-1000000.0},
						{'Name':'X max','Value':1000000.0},
						{'Name':'Y min','Value':-1000000.0},
						{'Name':'Y max','Value':1000000.0},
						{'Name':'z min','Value':-1000000.0},
						{'Name':'z max','Value':1000000.0}
						])
		if not d:
			return
		hits=[]
		for sec in self.cell._sections.values():
			pts=sec.getPoints()
			if pts[:,0].min()<d[0]:
				continue
			if pts[:,0].max()>d[1]:
				continue
			if pts[:,1].min()<d[2]:
				continue
			if pts[:,1].max()>d[3]:
				continue
			if pts[:,2].min()<d[4]:
				continue
			if pts[:,2].max()>d[5]:
				continue
			hits.append(sec)
		self.selectedSections=hits
		self.setInfo()
	
	def makeSel(self, event=None):
		cell=self.cell
		sections = cell._sections.keys()
		d = [{"Name":"Name Contains",
			  "Value":"ANY PATTERN"}]
		reg = cell.getElements("NamedRegion")
		for r in reg:
			d.append({"Name":"Region %s" % r.name(),
					  "Type":"List",
					  "Value":["Ignore", "And", "Or", "And Not", "Or Not"]})
		d=self.askParam(d)
		if not d:
			return
		if d[0]!='ANY PATTERN':
			sections = filter(lambda x: d[0] in x.name(), sections)
		d = d[1:]
		first = 1
		allsections=set(sections)
		for i, v in enumerate(d):
			if v == 'Ignore':
				continue
			s = set(reg[i].getSectionNames())
			if v.endswith("Not"):
				s=allsections-s
			if first:
				first = 0
				sections = s.copy()
			else:
				if v.startswith("Or"):
					sections=sections.union(s)   #[c for c in sections]+[c for c in s if not c in sections]
				else:
					sections = sections.intersection(s)
		sections=[cell._sections[s] for s in sections]
		self.selectedSections=sections
		self.setInfo()
	
	def setInfo(self):
		nsec=len(self.cell._sections.values())
		syn=len(self.cell.getElements("Synapse"))
		chan=[]
		for s in self.cell._sections.values():
			ell=s.getElements(["Channel", "RangeVar"])
			for e in ell:
				n="%s:%s" % (e.__tag__, e.name())
				if not n in chan:
					chan.append(n)
		chan=len(chan)
		self.info.SetLabel("%i Sections, %i Synapses, %i Channel Types" % (nsec, syn, chan))
		self.nsel.SetLabel("%i Sections Selected" % len(self.selectedSections))
	
	def exportSel(self, event):
		self.gui.contextMenuSelect=[]
		try:
			self.gui.objecttree.UnselectAll()
		except:
			pass
		for si in self.selectedSections:
			self.gui.objecttree.SelectItem(si._guiinfo["treeid"])
			self.gui.objecttree.EnsureVisible(si._guiinfo["treeid"])
			self.gui.contextMenuSelect.append(si._guiinfo["treeid"])
		self.report("Exported %i selected sections to nmpml. They may not all appear highlighted depending on the Wx library version" % len(self.selectedSections) )
	
	def importSel(self, event=None):
		self.selectedSections= [self.gui.objecttree.GetPyData(s) for s in self.gui.contextMenuSelect]
		self.report("imported %i section selection" % len(self.selectedSections))
		self.setInfo()
	
	def killSel(self, event):
		self.selectedSections = []
		self.setInfo()
	
	def synapseInfo(self, event):
		cell =  self.cell
		syn = cell.getElements("Synapse")
		classes ={}
		for s in syn:
			c= getSynapseClasses(s.attributes)
			cds=getSynapseProperties(c, True, True)
			if not classes.has_key(cds):
				classes[cds]=0
			classes[cds]+=1
		self.report( str(classes) )
		
	
	def sectionMask(self, inverse=False):
		inds=self.cell.sec_draw_indexes([s.name() for s in set(self.selectedSections)])
		inds=array(inds).astype(int32)
		points = self.cell.get_drawing_coords()
		m=zeros(points.shape[0], float32)
		put(m, inds, 1.0)
		if inverse:
			m=logical_not(m)
		m=reshape(m, (-1, 2))[:,0]
		if not any(m):
			self.report("Selection is empty. Will not cerate Mask")
			return None
		return m
	
	def makeUniformMask(self, event):
		d=self.askParam([{"Name":"Density",
							  "Value":.1},
							 {"Name":"Name",
							  "Value":"AfferentClassXX"},
							 {"Name":"Which Sections",
							  "Type":"List",
							  "Value":["All", "Only selected sections",
									   "Only non-selected sections"]}])
		if not d:
			return
		points = self.cell.get_drawing_coords()
		nc=reshape(points, (-1, 8)).shape[0]
		maskdat=ones(nc, float32)*d[0]
		if d[2]!="All":
			m=self.sectionMask(("non" in d[2]))
			if m==None:
				return
			maskdat=maskdat*m
		d = newData(reshape(maskdat, (-1,1)),  {'Name':d[1],'SampleType':'mask'})
		self.cell.newElement(d)
		self.gui.update_all(object=d, event="Create")
	
	def makeMasks(self, event):
		c = self.cell
		points = reshape(c.get_drawing_coords(), (-1, 8))
		diams = (points[:,3]+points[:,7])/2
		of = open('modeltemplate.txt', 'w')
		for p in points:
			of.write("%.3f %.3f %.3f %.3f %.3f %.3f %.3f %.3f\n" % tuple(p))
		of.close()
		check=os.system("matlab -nojvm -nosplash -r \"maskalldata('modeltemplate.txt'); quit\"")
		if check:
			self.report("system call to matlab maskalldata failed")
			return
		
		lines=open("masked_modeltemplate.txt").readlines()
		tags = array(map(lambda l:map(float, l.split()),lines))
		filt = diams < 8.5
		tags = tags*filt[:,NewAxis]
		for i in range(tags.shape[1]):
			n = "AfferentClass%02d" % (i+1,)
			d = newData(tags[:,i:i+1],  {'Name':n,'SampleType':'mask'})
			c.newElement(d)
		self.gui.update_all(object=c, event="Rebuild")
	
	def makeSyn(self, event=None):
		cell =  self.cell
		masks=cell.getElements("Data", {"SampleType":"mask"}, depth=1)
		if not masks:
			self.report("No masks")
			return
		md=dict([(n.name(), n) for n in masks])
		masks=md.keys()
		masks.sort()
		d=self.askParam([{"Name":"How Many",
							  "Value":10},
							 {"Name":"Type",
							  "Value":"GSyn"},
							 {"Name":"Exclude Sections",
							  "Type":"List",
							  "Value":["No", "Only in selected sections",
									   "Never in selectied sections"]},
							 {"Name": "Which Masks",
							  "Type":"Select",
							  "Value":masks}])
		if not d:
			return
		if d[-1]:
			masks=[md[k] for k in d[-1]]
		else:
			masks=md.values()
		if not masks:
			self.report("No masks")
			return
		howmany=d[0]
		modeltype = d[1]
		tags = hstack([m.getData() for m in masks])
		if d[2]!="No":
			m=self.sectionMask(d[2].startswith("Never"))
			if m==None:
				return
			print tags.shape, m.shape
			tags=tags*reshape(m, (-1,1))
		nclasses=tags.shape[1]
		synapse_prob=cumsum(ravel(tags))
		rands=uniform(0,synapse_prob[-1], howmany)
		cents = []
		types = []
		for i in range(rands.shape[0]):
			p=rands[i]
			ind=nonzero1d(synapse_prob>=p)[0]
			c,t = divmod(ind,nclasses)
			n=masks[t].name()
			atr= getSynapseProperties(n)
			try:
				sec, loc = cell.nthCenter(c)
				sec = cell.getSection(sec)
				print "Adding synapse in %s" % str(sec)
			except:
				print "Center %i not found. nthCenter sez %s" % (c, str(exc_info()[1]))
				continue
			atr.update({"Type":modeltype, "Id":i, "Afferent":
			n, 'Name':"%s%s" % (n, modeltype),
					'Point':str(sec.ptAtRel(loc))})
			self.gui.makeElem("Synapse", atr, sec, update=False)
		self.gui.update_all(object=cell, event="Rebuild")
		self.report("Generated Synapses")
		self.setInfo()
	
	def delSyn(self, event=None):
		syns = self.cell.getElements("Synapse")
		if not syns:
			return
		tn=list(set([foo.attrib('Afferent') for foo in syns]))
		tn.sort()
		if len(tn)>1:
			d=self.askParam([{'Name':'Delete which inputs?',
							  'Type':'Select',
							  'Value':tn}])
			if not d:
				return
			if d[0]:
				syns=[s for s in syns if str(s.attrib('Afferent')) in d[0]]
		for s in syns:
			s.sever()
		self.gui.update_all(object=self.cell, event="Rebuild")
		self.setInfo()
	
	def randomSyn(self, event):
		secs = self.selectedSections
		if not secs:
			return
		syns = []
		for s in secs:
			syns.extend(s.getElements("Synapse"))
		self.report("moving %i syns" % len(syns))
		for s in syns:
			newo = random.choice(secs)
			if newo!=s.container:
				newo.newElement(s)
			newi = random.randint(0, newo.getPoints().shape[0]-1)
			s.setAttrib("Point", newi)
	
	def editSyn(self, event=None):
		syns = self.cell.getElements("Synapse")
		self.report("%i total synapses" % len(syns))
		SynapsePars = ["Type"]
		spd = []
		for p in SynapsePars:
			spd.append({"Name":p,
						"Type":str,
						"Optional":1})
		d = self.askParam(spd)
		if not d:
			return
		for s in syns:
			for i, p  in enumerate(SynapsePars):
				s.setAttrib(p, d[i])
	
	def fuzzBall(self, event):
		secs = self.selectedSections
		if not secs:
			return
		d=self.askParam([{"Name":"Root Section",
			"Value":"section[4]"}])
		if not d:
		    return
		root=self.cell._sections[d[0]]
		newroot=[x for x in secs if not x.parent()]
		if newroot:
			self.report("New root assigned")
			root.setAttrib("Parent", None)
		else:
			self.report("Keeping old root. Selected section will be parent for new sections")
		tp = root.getPoints()[-1][:3]
		for s in secs:
			s.setAttrib("Parent",root.name())
			apoints = s.getPoints()
			trans = tp - apoints[0,:3]
			apoints[:,:3] = apoints[:,:3]+trans
			s.setPoints(apoints)
		self.cell.refresh()
		self.report("fuzz complete")

	
	def antiFuzzBall(self, event):
		r=self.cell.root()
		keep=synapseFree(self.cell._sections[r], self.cell)
		syns = self.cell.getElements("Synapse")
		for s in syns:
			if s.container in keep:
				continue
			newo=s.container
			while not newo in keep:
				newo=self.cell._sections[newo.parent()]
			newo.newElement(s)
			newi = newo.getPoints().shape[0]-1
			s.setAttrib("Point", newi)
		secs=self.cell._sections.values()
		for s in secs:
			if not s in keep:
				self.gui.update_all(object=s, event="Delete")
		self.cell.refresh()
		self.setInfo()
	
	def splitCell(self, event=None):
		mlen=min([x.stats()[0] for x in self.cell._sections.values()])
		d=self.askParam([{"Name":"Target Length",
							  "Value":mlen}])
		if not d:
			return
		self.cell.uniformSectionLength(d[0])
		self.report("Done. Now have %i sections" % len(self.cell._sections.keys()))
		self.setInfo()
	
	def getCellMorph(self, event):
		cell =  self.cell
		dlg=wx.FileDialog(self.gui, message="Select file", style=wx.OPEN)
		dlg.CenterOnParent()
		if dlg.ShowModal() == wx.ID_OK:
			fname=dlg.GetPath()
		else:
			self.report("Canceled File Load.")
			return
		doc = mien.parsers.fileIO.read(fname)
		c = doc.getElements("Cell")
		if len(c)==0:
			self.report("No cells in this document")
			return
		elif len(c)>1:
			wc=self.askUsr("Which Cell", map(str, c))
			if not wc:
				return
			c=[cell for cell in c if str(cell)==wc]
		c=c[0]
		ts=cell._sections.values()[0]
		cell.elements=[e for e in cell.elements if e.__tag__!='Section']
		for sec in c._sections.values():
			sec.elements=[]
			for k in ["Ra"]:
				if ts.attrib(k):
					sec.setAttrib(k,ts.attrib(k))
			for e in ts.elements:
				if  e.__tag__ in ["Synapse"]:
					continue
				try:
					newe = e.__class__(e.attributes)
					sec.newElement(newe)
				except:
					self.report("Warning: could not duplicate element %s" % str(e))
			sec.refresh()
			cell.elements.append(sec)
		cell.refresh()
		self.gui.update_all(object=cell, event="Move")
		self.setInfo()
	
	def nukeMech(self, evt):
		for s in self.selectedSections:
			s.elements=[]
		self.gui.update_all(object=self.cell, event="rebuild")

	
	def dupMech(self, event):
		d=self.askParam([{"Name":"Duplicate Which Section?","Value":self.cell.root()}])
		if not d:
			return
		rs=self.cell._sections[d[0]]
		for s in self.selectedSections:
			if s==rs:
				continue
			s.setAttrib('Ra',rs.attrib('Ra'))
			for c in s.getElements(['Channel', 'RangeVar']):
				self.gui.update_all(object=c, event="Delete")
			for c in rs.getElements(['Channel', 'RangeVar']):
				newobj = c.clone()
				s.newElement(newobj)
				self.gui.update_all(object=newobj, event="Create")
		self.report("Set Mechanisms")
	
	def assignNames(self, event):
		roots={}
		names={}
		newstarts=0
		for r in self.cell.getElements("NamedRegion"):
			root=r.getOrder()[0]
			roots[root.name()]=r.name()
		for secname in self.cell.branch():
			if roots.has_key(secname):
				names[secname]=roots[secname]+"_1"
			else:
				parent=self.cell._sections[secname].parent()
				if not parent:
					nn="root_1"
				elif names.has_key(parent):
					kids=self.cell.getChildren(parent)
					bn=names[parent]
					pnp=bn.split("_")
					pi=int(pnp[-1])
					bn=join(pnp[:-1], "_")
					nkids=0
					for n in kids:
						if n==secname:
							continue
						if not names.has_key(n):
							continue
						if names[n].startswith(bn):
							nkids+=1
					if nkids==0:
						nn=bn+"_"+str(pi+1)
					else:
						nn=names[parent]+"_%i" % nkids
				else:
					nn="sec%i_1" % newstarts
					newstarts+=1
				if nn in names.values():
					print "name %s is a duplicate" % nn
					print nkids
					return
				names[secname]=nn
		for on in names.keys():
			renameSection(self.cell._sections[on], names[on])
		self.gui.update_all(object=self.cell, event='move')
	
	def simpleNames(self, event):
		names={}
		for ind, name in enumerate(self.cell.branch()):
			names[name]="sec[%i]" % ind
		for on in names.keys():
			sec=self.cell._sections[on]
			sec.setName(names[on])
		self.gui.update_all(object=self.cell, event='Rebuild')
	
	def setProperty(self, event):
		setProperty(self.gui, self.selectedSections)
	
	def addMech(self, event):
		addChan(self.gui, self.selectedSections)
	
	def delMech(self, event):
		delChan(self.gui, self.selectedSections)
	
	def setPass(self, event):
		pass
	
	def getRin(self, event):
		if len(self.selectedSections)==1:
			target = self.selectedSections[0]
		else:
			d = self.askParam([{"Name":"Which Section", "Type":str}])
			if not d:
				return
			target = self.cell.getSection(d[0])
		doc = self.gui.document
		stim = forceGetPath(doc, "/Stimulus:ModelBuilderStimulus")
		for e in stim.getElements(depth=1):
			e.sever()
		ic = forceGetPath(doc, "/Stimulus:ModelBuilderStimulus/IClamp:inject")
		exp.setAttrib("Start", 5)
		exp.setAttrib("Amp", 5)
		exp.setAttrib("Stop", 10)
		exp.setAttrib("Id", 1)
		ref = forceGetPath(doc, "/Stimulus:ModelBuilderStimulus/IClamp:inject/ElementReference:Section")
		ref.setAttrib('Target', target.upath())
		ref.setAttrib('Data', 0.5)
		exp=forceGetPath(doc, "/Experiment:ModelBuilderExperiment")
		exp.setAttrib('secondorder', 2)
		exp.setAttrib('Simulator', 'Neuron')
		exp.setAttrib('celsius', 20)
		exp.setAttrib('time', 20)
		exp.setAttrib('dt', 0.05)
		for e in exp.getElements(depth=1):
			e.sever()
		ref = forceGetPath(doc, "/Experiment:ModelBuilderExperiment/ElementReference:Cell")
		ref.setAttrib('Target', self.cell.upath())
		ref = forceGetPath(doc, "/Experiment:ModelBuilderExperiment/ElementReference:Stimulus")
		ref.setAttrib(doc, "Target", "/Stimulus:ModelBuilderStimulus")
		rec=forceGetPath(doc, "/Experiment:ModelBuilderExperiment/Recording:v")
		rec.setAttrib("Variable", 'v')
		rec.setAttrib("DataType", "d")
		rec.setAttrib("SamplesPerSecond", 10000.0)
		ref = forceGetPath(doc, "/Experiment:ModelBuilderExperiment/Recording:v/ElementReference:Section")
		ref.setAttrib('Target', target.upath())
		ref.setAttrib('Data', 0.5)




ME={}

def areSections(l):
	if set(l)==set(['Section']):
		return True
	return False


def cellEdit(gui, elems):
	cell=elems[0]
	c=CellEditor(gui, cell)

def newRegion(gui, secs):
	gui.report("Making region containing %i sections" % len(secs))
	atr = gui.getElemAttribs("NamedRegion")
	reg = gui.makeElem("NamedRegion", atr, secs[0].container)
	for i, s in enumerate(secs):
		gui.makeElem('ElementReference', {"Name":"el%i" % i, "Target":s.upath()}, reg, update=False)
	gui.update_all(object=reg, event="Rebuild")

def regSel(gui,elems):
	reg=elems[0]
	selectedSections = reg.getSections()
	gui.objecttree.UnselectAll()
	gui.contextMenuSelect=[]
	for si in selectedSections:
		gui.objecttree.EnsureVisible(si._guiinfo["treeid"])
		gui.contextMenuSelect.append(si._guiinfo["treeid"])
		#gui.gui.objecttree.ToggleItemSelection(si._guiinfo["treeid"])
		gui.objecttree.SelectItem(si._guiinfo["treeid"])
	gui.report("%i sections selected (but they may not all be highlighted!)" % len(selectedSections))

def setProperty(gui, secs):
	gui.report("Operating on %i sections" % len(secs))
	mechanisms=["Ra"]
	for s in secs:
		ell=s.getElements(["Channel", "RangeVar"])
		for e in ell:
			n="%s:%s" % (e.__tag__, e.name())
			if not n in mechanisms:
				mechanisms.append(n)
	d = gui.askParam([{"Name":"Mechanism",
							"Type":"List",
							"Value":mechanisms},
						   {"Name":"Value",
							"Value":0.0}])
	if not d:
		return
	value=str(d[1])
	d=d[0].split(':')
	if len(d)>1:
		tag, name=d[:2]
	else:
		tag=d[0]
		name=None
	if tag=="Ra":
		for s in secs:
			s.setAttrib("Ra",value)
	else:
		propnames={"RangeVar":"Values",
				   "Channel":"Density"}
		
		for s in secs:
			var = s.getElements(tag, name)
			if not var:
				continue
			var=var[0]
			var.setAttrib(propnames[tag], value)
	gui.report("Set value in %i sections" % len(secs))


def addChan(gui, secs):
	gui.report("Operating on %i sections" % len(secs))
	d = gui.askParam([{"Name":'Tag',
							"Type":"Choice",
							"Value":{"Channel":[{"Name":"Ion",
												 "Type":"List",
												 "Value": ["Na", "K", "Ca", "Cl", "Leak"]},
												{"Name":"Reversal",
												 "Type":str}],
									 "RangeVar":[]}},
							{"Name":"Name",
							"Type":str},
							{"Name":"Density",
							 "Type":str}]
							)
	if not d:
		return
	for s in secs:
		if d[0][0]=="Channel":
			gui.makeElem("Channel", {"Name":d[1], "Ion":d[0][1], "Density":d[2], "Reversal":d[0][2]}, s, update=False)
		else:
			gui.makeElem("RangeVar", {"Name":d[1], "Values":d[2]}, s, update=False)
	if secs:
		gui.update_all(object=secs[0].container, event="Rebuild")
	gui.report("Added mechanism in %i sections" % len(secs))

def delChan(gui,secs):
	gui.report("Operating on %i sections" % len(secs))
	mechanisms=[]
	for s in secs:
		ell=s.getElements(["Channel", "RangeVar"])
		for e in ell:
			n="%s:%s" % (e.__tag__, e.name())
			if not n in mechanisms:
				mechanisms.append(n)
	d = gui.askParam([{"Name":"Name",
							"Type":"List",
							"Value":mechanisms}])
	if not d:
		return
	kill = 0
	d=d[0].split(':')
	tag, name=d[:2]
	for s in secs:
		var = s.getElements(tag, name)
		if not var:
			continue
		for c in var:
			gui.update_all(object=c, elems="Delete")
			kill+=1
	gui.report("Deleted %i mechanisms" % kill)

def maskPoint(gui, elems):
	mask =  elems[0]
	cell=mask.container
	d=gui.askParam([{"Name":"Section",
						  "Type":"List",
						  "Value":cell._sections.keys()},
						 {"Name":"Location",
						  "Value":0.5}])
	if not d:
		return
	loc=(cell._sections[d[0]], d[1])
	gui.report(str(mask[loc]))

def maskAssign(gui, elems):
	mask = elems[0]
	mask.assign()
	gui.report("set values")


MECM={"Set Mechanism Density":(setProperty, "Section"),
	'Remove Mechanism':(delChan, "Section"),
	"Insert Mechanism":(addChan, "Section"),
	#"Launch Cell Editor":(cellEdit, "Cell"),
	"Evaluate at point":(maskPoint, "Mask"),
	"Assign density":(maskAssign, "Mask"),
	"Select Sections":(regSel, "NamedRegion"),
	"Make Region":(newRegion, areSections)
	}