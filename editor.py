# -*- coding: utf-8 -*-
import copy
import sys
import json
import os
import subprocess

from PyQt5.QtCore import Qt
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5 import QtGui

from uiEditor import Ui_EditorWindow
import uiSolidDirections
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

class EditorStatusBar(QStatusBar):
	def __init__(self, parent):
		super().__init__(parent)
		self.mousePositionLabel = QLabel()
		self.objectInfoLabel = QLabel()
		self.addPermanentWidget(self.mousePositionLabel, 1)
		self.addPermanentWidget(self.objectInfoLabel)
	def setPositionInfo(self, text):
		self.mousePositionLabel.setText(text)
	def setHoverInfo(self, text):
		self.objectInfoLabel.setText(text)

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

		self._initSettings()

		# add window surface
		self.mapSurface = MapSurface(None, self)
		self.ui.scrollArea.setWidget(self.mapSurface)

		# s
		#self.editStates = [EditState(self)] # list of edit states
		# an edit state contains options that can be undone (Ctrl-Z)
		#self.currentState = self.editStates[0]
		#self.lastSavedState = self.editStates[0]

		self._initSignals()
		self.updateSolidDirectionsLabel()
	def _initSettings(self):
		QtCore.QCoreApplication.setOrganizationName("dlon")
		QtCore.QCoreApplication.setOrganizationDomain("dlon.github.io")
		QtCore.QCoreApplication.setApplicationName("game1editor")
		self.settings = QtCore.QSettings()
		self.openDirectory = self.settings.value("openDirectory", "")
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
		editor.code.setText(
			json.dumps(self.generateData(), indent=4)
		)
		dialog.setWindowTitle("Map data")
		ret = dialog.exec()
		if ret == dialog.Accepted:
			print("TODO: rebuild data based on input")
	def updateSolidDirectionsLabel(self):
		strs = []
		if MapTile.solidFlag & 0x04:
			strs += ["U"]
		if MapTile.solidFlag & 0x08:
			strs += ["D"]
		if MapTile.solidFlag & 0x01:
			strs += ["L"]
		if MapTile.solidFlag & 0x02:
			strs += ["R"]
		self.ui.solidLabel.setText(
			" | ".join(strs)
		)
		if not strs or not self.ui.solidCheckbox.isChecked():
			self.ui.solidLabel.setVisible(False)
		else:
			self.ui.solidLabel.setVisible(True)
	def setSolidDirections(self):
		dialog = QDialog(self, Qt.Tool)
		solidDlg = uiSolidDirections.Ui_Dialog()
		solidDlg.setupUi(dialog)
		dialog.setWindowTitle("Solid directions")
		solidDlg.leftCheck.setChecked(MapTile.solidFlag & 0x01)
		solidDlg.rightCheck.setChecked(MapTile.solidFlag & 0x02)
		solidDlg.upCheck.setChecked(MapTile.solidFlag & 0x04)
		solidDlg.downCheck.setChecked(MapTile.solidFlag & 0x08)
		dialog.exec()
		MapTile.solidFlag = (0x01 if solidDlg.leftCheck.isChecked() else 0) | \
			(0x02 if solidDlg.rightCheck.isChecked() else 0) | \
			(0x04 if solidDlg.upCheck.isChecked() else 0) | \
			(0x08 if solidDlg.downCheck.isChecked() else 0)
		self.updateSolidDirectionsLabel()
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
	def _updateScrollPosition(self, zoom, delta, mousePos):
		hsb = self.ui.scrollArea.horizontalScrollBar()
		vsb = self.ui.scrollArea.verticalScrollBar()
		#hsb.setValue(
		#	hsb.minimum() + mousePos.x() / self.mapSurface.rect().width() * (hsb.maximum() - hsb.minimum())
		#)
		#vsb.setValue(
		#	vsb.minimum() + mousePos.y() / self.mapSurface.rect().height() * (vsb.maximum() - vsb.minimum())
		#)
		pass
	def _initSignals(self):
		self.ui.objectTree.currentItemChanged.connect(self.ui.objectPreviewFrame.setImage)
		self.ui.tilesetTree.currentItemChanged.connect(self.ui.tilePreviewFrame.setImage)
		self.ui.widthSetting.textChanged.connect(self.mapSurface.setWidth)
		self.ui.heightSetting.textChanged.connect(self.mapSurface.setHeight)
		self.ui.widthSetting.setText("640")
		self.ui.heightSetting.setText("480")
		self.mapSurface.clicked.connect(self.ui.tilePreviewFrame.handleMapSurfaceClick)
		self.mapSurface.clicked.connect(self.ui.objectPreviewFrame.handleMapSurfaceClick)
		self.mapSurface.zoomed.connect(self._updateScrollPosition)

		self.ui.buttonBackgroundColor.clicked.connect(self.setBackgroundColor)
		self.ui.buttonCreationCode.clicked.connect(self.setCreationCode)
		self.ui.solidDirectionsButton.clicked.connect(self.setSolidDirections)
		self.ui.solidCheckbox.toggled.connect(self.updateSolidDirectionsLabel)

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
			path, _ = QFileDialog.getOpenFileName(
				caption = "Open map",
				filter = "game1 maps (*.json)",
				directory = self.openDirectory,
			)
			if path:
				dir = QtCore.QFileInfo(path)
				self.settings.setValue("openDirectory", dir.absolutePath())
				self.openDirectory = ''
				return self.loadFile(path)
		return False
	def save(self):
		if self.mapFile:
			return self.saveFile(self.mapFile)
		return self.saveAs()
	def saveAs(self):
		file, _ = QFileDialog.getSaveFileName(
			caption = "Save map",
			filter = "game1 maps (*.json)",
			directory=self.openDirectory,
		)
		if not file:
			dir = QtCore.QFileInfo(file)
			self.settings.setValue("openDirectory", dir.absolutePath())
			self.openDirectory = ''
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
		with open(path) as f:
			data = json.load(f)
		self.mapSurface.clear()
		MapTile.solidFlag = 0xFF
		# settings
		self.mapSurface.setWidth(data["settings"]["width"], updateForm=True)
		self.mapSurface.setHeight(data["settings"]["height"], updateForm=True)
		self.mapSurface.setBackgroundColor(
			QtGui.QColor(*data["settings"]["background"])
		)
		# objects
		for obj in data["objects"]:
			customProp = obj.copy()
			for k in ('x','y','type','creationCode'):
				try:
					customProp.pop(k)
				except KeyError:
					pass
			self.mapSurface.addObject(MapObject(
				type=obj['type'],
				position=QtCore.QPoint(obj['x'], obj['y']),
				image=self.ui.objectPreviewFrame.unknownImage, # TODO: load appropriate image
				creationCode=obj.get("creationCode") or '',
				customProperties=customProp,
			))
		# tiles
		tilesets = {}
		for i in range(self.ui.tilesetTree.topLevelItemCount()):
			widget = self.ui.tilesetTree.topLevelItem(i)
			tilesets[widget.data(0, Qt.UserRole)] = {
				"treeItem": widget,
				"image": QtGui.QImage("../data/%s" % widget.text(0)),
			}
		layers = {}
		for i in range(self.ui.layerTree.topLevelItemCount()):
			widget = self.ui.layerTree.topLevelItem(i)
			depth = int(widget.text(1))
			#if depth in layers:
			#	raise EditorException("layer depths must be unique")
			layers[depth] = widget
		for tile in data["tiles"]:
			position = QtCore.QPoint(tile['x'], tile['y'])
			subimageRect = QtCore.QRect(
				QtCore.QPoint(tile['tx'], tile['ty']),
				QtCore.QSize(tile['tw'], tile['th']),
			)
			if tile['depth'] not in layers:
				# TODO: add new layer more properly
				widget = QTreeWidgetItem(
					self.ui.layerTree,
					(
						"Layer{}".format(tile['depth']),
						str(tile['depth']),
						"1",
					 )
				)
				layers[tile['depth']] = widget
				widget.setFlags(widget.flags() | Qt.ItemIsEditable)
			mapTile = MapTile(
				tilesets[tile["tileset"]]["treeItem"],
				tilesets[tile["tileset"]]["image"],
				subimageRect,
				position,
				layers[tile['depth']],
				tile['solid'],
				solidFlag=tile.get('solidDirections') or -1,
			)
			mapTile.rect.setSize(QtCore.QSize(tile['w'], tile['h']))
			self.mapSurface.addTile(mapTile)
		self.mapSurface.selectedObject = None
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

import traceback

class QTracebackDialog(QDialog):
	def __init__(self, type, val, tb):
		super().__init__()
		self.tbExcept = traceback.TracebackException(type, val, tb)
		errorStr = ''.join(line for line in self.tbExcept.format())
		self.layout = QVBoxLayout()
		self.tbArea = QTextEdit()
		self.tbArea.setText(errorStr)
		self.tbArea.setReadOnly(True)
		self.layout.addWidget(self.tbArea)
		self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Abort)
		self.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.accept)
		self.buttonBox.button(QDialogButtonBox.Abort).clicked.connect(
			lambda: sys.exit(1)
		)
		self.layout.addWidget(self.buttonBox)
		self.setWindowTitle("Exception")
		self.setSizeGripEnabled(True)
		self.setLayout(self.layout)
	def accept(self):
		super().accept()

def handleErrors(type, val, tb):
	# print traceback
	traceback.print_exception(type, val, tb)
	# display stacktrace in dialog
	QTracebackDialog(type, val, tb).exec()

# create Qt application
if __name__ == '__main__':
	app = QApplication(sys.argv)
	sys.excepthook = handleErrors
	editor = EditorWindow()
	editor.show()
	sys.exit(app.exec_())