# -*- coding: utf-8 -*-
import copy
import sys
import json
import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5 import QtGui

from uiEditor import Ui_EditorWindow
from mapSurface import MapSurface, MapObject, MapTile
import entities
import icons_rc
from objectPreview import QObjectPreview

class EditorException(Exception):
	pass

class TrackedStruct:
	def __init__(self, ds, observer):
		self._ds = ds
		self._observer = observer
	def __len__(self):
		return len(self._ds)
	def __contains__(self, i):
		return i in self._ds
	def __getitem__(self, k):
		return self._ds[k]
	def __setitem__(self, k, v):
		oldds = self._ds.copy()
		self._ds[k] = v
		self._observer.onChange(self._ds, oldds)
	def __delitem__(self, k):
		oldds = self._ds.copy()
		del self._ds[k]
		self._observer.onChange(self._ds, oldds)
	def append(self, item):
		oldds = self._ds.copy()
		self._ds.append(item)
		self._observer.onChange(self._ds, oldds)

class Map:
	def __init__(self):
		tiles = TrackedStruct([], self)
		objects = TrackedStruct([], self)
		settings = TrackedStruct({
			'width':100,
			'height':100,
		}, self)
	def onChange(self, ds, oldds):
		print('change observed!', ds, oldds)
	def onchange(self, obj):
		print('onchange')
	def addTile(self, tile):
		pass
	def export(self):
		return {
			'settings': {},
		}

class MapTrackable:
	map = None
	def __init__(self, map, *args):
		for k in args:
			setattr(self, k, args[k])
		self.map = map
	def __setattr__(self, k, v):
		self.__dict__[k] = v
		if self.map:
			self.map.onchange(self)

#mt = MapTrackable(Map(), x=0,y=0, w=16,h=16, xOffset=0,yOffset=0)
#mt.w = 10

editState = {
	'settings': {
		'width': 100,
		'height': 100,
	},
	'objects': [],
	'tiles': [],
}

class EditorWindow(QMainWindow):
	def __init__(self):
		# set up UI window
		super(EditorWindow, self).__init__()
		self.ui = Ui_EditorWindow()
		self.ui.setupUi(self)

		self._initTrees()
		self._initSignals()

		self.mapFile = ''
		self.setWindowTitle('untitled[*] - game1 editor')

		# add window surface
		self.mapSurfaceGrid = QGridLayout(self.ui.mapSurfaceFrame)
		self.mapSurfaceGrid.setObjectName("mapSurfaceGrid")
		self.mapSurface = MapSurface(self.ui.mapSurfaceFrame)
		self.mapSurface.setObjectName("mapSurface")
		self.mapSurfaceGrid.addWidget(self.mapSurface)

		# s
		#self.editStates = [EditState(self)] # list of edit states
		# an edit state contains options that can be undone (Ctrl-Z)

		#self.currentState = self.editStates[0]
		#self.lastSavedState = self.editStates[0]

		self.ui.objectTree.currentItemChanged.connect(self.ui.objectPreviewFrame.setImage)
		self.ui.tilesetTree.currentItemChanged.connect(self.ui.tilePreviewFrame.setImage)
		self.mapSurface.clicked.connect(self.ui.tilePreviewFrame.handleMapSurfaceClick)
	def closeEvent(self, event):
		if self.saveIfWants():
			event.accept()
		else:
			event.ignore()
	def _initSignals(self):
		self.ui.actionNew.triggered.connect(self.new)
		self.ui.actionOpen.triggered.connect(self.open)
		self.ui.actionSave.triggered.connect(self.save)
		self.ui.actionSaveAs.triggered.connect(self.saveAs)
		#self.ui.actionQuit.triggered.connect(self.quitIfWants)
	def _addObjectTreeDir(self, dir, parent=None):
		if not parent:
			parent = self.ui.objectTree
		for object in dir['objects']:
			item = QTreeWidgetItem(parent,
				[object, dir['objects'][object]['script']])
			if type(dir['objects'][object]['image']) == str:
				dir['objects'][object]['image'] = '../%s' % dir['objects'][object]['image']
			else:
				dir['objects'][object]['image']['file'] = '../%s' % dir['objects'][object]['image']['file']
			item.setData(0, Qt.UserRole, dir['objects'][object]['image'])
		for subdir in dir['subdirs']:
			subNode = QTreeWidgetItem(parent, [subdir])
			self._addObjectTreeDir(dir['subdirs'][subdir],
				subNode)
	def _initTrees(self):
		with open("entities.json") as f:
			objectTree = json.load(f)
		self._addObjectTreeDir(objectTree)
		self.ui.objectTree.expandAll()
		with open("tilesets.json") as f:
			tilesetTree = json.load(f)
		for tileset in tilesetTree:
			QTreeWidgetItem(self.ui.tilesetTree,
				[tilesetTree[tileset]])
		self.ui.tilesetTree.expandAll()
	def mapTitle(self):
		return self.mapFile if self.mapFile else 'untitled'
	def new(self):
		if self.saveIfWants():
			# create new project
			self.mapFile = ''
			self.setWindowModified(False)
	def open(self):
		if self.saveIfWants():
			path, _ = QFileDialog.getOpenFileName(caption = "Open map", filter = "game1 maps (*.map)")
			if path:
				return self.loadFile(path)
		return False
	def save(self):
		if self.mapFile:
			return self.saveFile(self.mapFile)
		return self.saveAs()
	def saveAs(self):
		file, _ = QFileDialog.getSaveFileName(caption = "Save map", filter = "game1 maps (*.map)")
		if not file:
			return False
		return self.saveFile(file)
	def saveIfWants(self):
		# False: cancelled
		if self.isWindowModified():
			ret = QMessageBox.warning(self, "Save",
				"Save %s?" % self.mapTitle(),
				QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
			if ret == QMessageBox.Save:
				return self.save()
			elif ret == QMessageBox.Cancel:
				return False
		return True
	def setPath(self, path):
		self.mapFile = path
		self.setWindowTitle('%s[*] - game1 editor' % path)
		self.setWindowModified(False)
	def loadFile(self, path):
		print("open data here")
		self.setPath(path)
		return True
	def saveFile(self, path):
		with open(path,'w') as f:
			json.put({
				'objects': objects,
				
			}, f)
		self.setPath(path)
		return True
	def isModified(self):
		return not self.currentState.equals(self.lastSavedState)
	#def canRedo(self):
	#	return self.editStates[-1] != self.currentState
	def stateBeforeChange(self, editState, name, val):
		print("recorded change (EditState):", name, '=', val)
		if editState != self.currentState:
			raise EditorException("trying to edit a non-current state")
		# keep a copy of the current state
		copy.deepcopy(editState)

# create Qt application
if __name__ == '__main__':
	app = QApplication(sys.argv)
	editor = EditorWindow()
	editor.show()
	sys.exit(app.exec_())