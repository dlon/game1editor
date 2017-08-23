# -*- coding: utf-8 -*-
import copy
import sys
import json
import os
import subprocess

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5 import QtGui

from uiEditor import Ui_EditorWindow
from mapSurface import MapSurface, MapObject, MapTile
from uiCodeEditor import Ui_CodeEditor
import entities
import icons_rc
from objectPreview import QObjectPreview
import pprint

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

		self.mapFile = ''
		self.creationCode = ''
		self.setWindowTitle('untitled[*] - game1 editor')

		# add window surface
		#self.mapSurfaceGrid = QGridLayout(self.ui.mapSurfaceFrame)
		#self.mapSurfaceGrid.setObjectName("mapSurfaceGrid")
		#self.mapSurface = MapSurface(self.ui.mapSurfaceFrame)
		#self.mapSurface.setObjectName("mapSurface")
		#self.mapSurfaceGrid.addWidget(self.mapSurface)
		self.mapSurface = MapSurface(None)
		self.ui.scrollArea.setWidget(self.mapSurface)

		# s
		#self.editStates = [EditState(self)] # list of edit states
		# an edit state contains options that can be undone (Ctrl-Z)

		#self.currentState = self.editStates[0]
		#self.lastSavedState = self.editStates[0]

		self.ui.objectTree.currentItemChanged.connect(self.ui.objectPreviewFrame.setImage)
		self.ui.tilesetTree.currentItemChanged.connect(self.ui.tilePreviewFrame.setImage)
		self.ui.widthSetting.textChanged.connect(self.mapSurface.setWidth)
		self.ui.heightSetting.textChanged.connect(self.mapSurface.setHeight)
		self.ui.widthSetting.setText("640")
		self.ui.heightSetting.setText("480")
		self.mapSurface.clicked.connect(self.ui.tilePreviewFrame.handleMapSurfaceClick)
		self.mapSurface.clicked.connect(self.ui.objectPreviewFrame.handleMapSurfaceClick)

		self.ui.buttonBackgroundColor.clicked.connect(self.setBackgroundColor)
		self.ui.buttonCreationCode.clicked.connect(self.setCreationCode)

		self._initSignals()
	def setBackgroundColor(self):
		dialog = QColorDialog()
		if dialog.exec_() == dialog.Accepted:
			self.mapSurface.setBackgroundColor(dialog.selectedColor())
	def setCreationCode(self):
		dialog = QDialog(self.window())
		editor = Ui_CodeEditor()
		editor.setupUi(dialog)
		editor.code.setText(self.creationCode)
		dialog.setWindowTitle("Map creation code")
		ret = dialog.exec_()
		if ret == dialog.Accepted:
			self.creationCode = editor.code.toPlainText()
	def generateData(self):
		return {
			"settings": {
				"width": self.mapSurface.width(),
				"height": self.mapSurface.height(),
				"background": (
					self.mapSurface.backgroundColor.red(),
					self.mapSurface.backgroundColor.green(),
					self.mapSurface.backgroundColor.blue(),
				),
			},
			"objects": [obj.dump() for obj in self.mapSurface.objects],
			"tiles": [tile.dump() for tile in self.mapSurface.tiles],
		}
	def editData(self):
		dialog = QDialog(self)
		editor = Ui_CodeEditor()
		editor.setupUi(dialog)
		# TODO: add settings
		'''pp = pprint.PrettyPrinter(compact=False, width=1)
		editor.code.setText(
			pp.pformat(self.generateData())
		)'''
		editor.code.setText(
			json.dumps(self.generateData(), indent=4)
		)
		dialog.setWindowTitle("Map data")
		ret = dialog.exec_()
		if ret == dialog.Accepted:
			print("TODO: rebuild data based on input")
	def run(self):
		os.chdir("..")
		subprocess.Popen([
			"python3","main.py",
			"-data",json.dumps(self.generateData()),
		])
		os.chdir("editor")
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
		self.ui.actionData.triggered.connect(self.editData)
		self.ui.actionRun.triggered.connect(self.run)
		self.ui.actionCopy.triggered.connect(self.mapSurface.setCopyReference)
		self.ui.actionPaste.triggered.connect(self.mapSurface.copyReferenced)
	def keyPressEvent(self, e):
		super().keyPressEvent(e)
		if e.key() == Qt.Key_Delete:
			self.mapSurface.deleteSelected()
	def _addObjectTreeDir(self, dir, parent=None):
		if not parent:
			parent = self.ui.objectTree
		for object in dir['objects']:
			item = QTreeWidgetItem(parent,
				[object, dir['objects'][object]['script']])
			if type(dir['objects'][object]['image']) == str:
				if dir['objects'][object]['image']:
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
			item = QTreeWidgetItem(self.ui.tilesetTree,
				[tilesetTree[tileset]])
			item.setData(0, Qt.UserRole, tileset)
		self.ui.tilesetTree.expandAll()
	def mapTitle(self):
		return self.mapFile if self.mapFile else 'untitled'
	def new(self):
		if self.saveIfWants():
			# create new project
			self.mapFile = ''
			self.setWindowModified(False)
			self.mapSurface.clear()
	def open(self):
		if self.saveIfWants():
			path, _ = QFileDialog.getOpenFileName(caption = "Open map", filter = "game1 maps (*.json)")
			if path:
				return self.loadFile(path)
		return False
	def save(self):
		if self.mapFile:
			return self.saveFile(self.mapFile)
		return self.saveAs()
	def saveAs(self):
		file, _ = QFileDialog.getSaveFileName(caption = "Save map", filter = "game1 maps (*.json)")
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
			json.dump(self.generateData(), f, indent=4)
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