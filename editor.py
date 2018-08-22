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
from resizeDialog import ResizeDialog
import icons_rc
from objectPreview import QObjectPreview
import pprint

sys.path.insert(
	0,
	os.path.dirname(os.path.dirname(__file__))
)
import game
import map
import entities
import generateMetadata
import importlib
import random

class EditorException(Exception):
	pass

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
		self._pollSetup()
	def _pollSetup(self):
		#self.pollTimer = QtCore.QTimer(self)
		#self.pollTimer.setInterval(1000)
		self.metaWatcher = QtCore.QFileSystemWatcher(["../entities", "../map", "../data"], self)
		self.metaWatcher.directoryChanged.connect(self._initTrees)
	def _initSettings(self):
		QtCore.QCoreApplication.setOrganizationName("dlon")
		QtCore.QCoreApplication.setOrganizationDomain("dlon.github.io")
		QtCore.QCoreApplication.setApplicationName("game1editor")
		self.settings = QtCore.QSettings()
		self.openDirectory = self.settings.value("openDirectory", "")
	def setBackgroundColor(self):
		dialog = QColorDialog(self.mapSurface.backgroundColor)
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
		layers = {}
		for i in range(self.ui.layerTree.topLevelItemCount()):
			widget = self.ui.layerTree.topLevelItem(i)
			depth = int(widget.text(1))
			layers[widget.text(0)] = {
				'depth': depth,
				'tiles': [],
			}
		for tile in self.mapSurface.tiles:
			layers[tile.layerWidget.text(0)]['tiles'].append(
				tile.dump()
			)
		ret = {
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
			"layers": layers,
		}
		if self.creationCode:
			ret["settings"].update({
				"creationCode": self.creationCode
			})
		return ret
	def editData(self):
		dialog = QDialog(self)
		editor = Ui_CodeEditor()
		editor.setupUi(dialog)
		editor.code.setText(
			json.dumps(self.generateData(), indent=4, sort_keys=True)
		)
		dialog.setWindowTitle("Map data")
		ret = dialog.exec()
		if ret == dialog.Accepted:
			# TODO: revert if an exception is thrown
			self.loadData(json.loads(editor.code.toPlainText()))
	def setSize(self):
		dialog = ResizeDialog(self)
		ret = dialog.exec()
		if ret == dialog.Accepted:
			pass
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
		try:
			p = subprocess.Popen(["python3","main.py","-data"], stdin=subprocess.PIPE)
			# input, err = p.communicate(input=json.dumps(self.generateData()).encode())
			p.stdin.write(json.dumps(self.generateData()).encode())
			p.stdin.close()
		except:
			#traceback.print_exc()
			handleErrors(*sys.exc_info())
		os.chdir("editor")
	def closeEvent(self, event):
		if self.saveIfWants():
			event.accept()
		else:
			event.ignore()
	def _initSignals(self):
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

		self.ui.buttonResize.clicked.connect(self.setSize)

		def addNewLayer():
			widget = self.createLayer('Layer' + str(random.random()))
			self.ui.layerTree.editItem(widget)
		self.ui.actionAddLayer.triggered.connect(addNewLayer)
		def deleteLayer():
			msg = QMessageBox.question(
				self,
				"Confirm",
				"Delete layer?",
				QMessageBox.Yes | QMessageBox.No,
			)
			if msg == QMessageBox.Yes:
				self.deleteLayerWidget()
		self.ui.actionDeleteLayer.triggered.connect(deleteLayer)
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
		try:
			importlib.reload(map)
			importlib.reload(entities)
			for m in sys.modules:
				if m.startswith('entities.'):
					importlib.reload(sys.modules[m])
		except:
			return
		self.ui.objectTree.clear()
		self._addObjectTreeDir(generateMetadata.generateEntityTable())
		self.ui.objectTree.expandAll()
		tilesetWidgets = {}
		for i in range(self.ui.tilesetTree.topLevelItemCount()):
			widget = self.ui.tilesetTree.topLevelItem(i)
			tilesetWidgets[widget.data(0, Qt.UserRole)] = widget
		for tileset in map.Map.tilesets:
			if tileset not in tilesetWidgets:
				item = QTreeWidgetItem(
					self.ui.tilesetTree,
					[map.Map.tilesets[tileset]]
				)
				item.setData(0, Qt.UserRole, tileset)
		self.ui.tilesetTree.expandAll()
	def mapTitle(self):
		return self.mapFile if self.mapFile else 'untitled'
	def new(self):
		if self.saveIfWants():
			# create new project
			self.setPath('')
			self.setWindowModified(False)
			self.mapSurface.clear()
			self.creationCode = ''
			self.mapSurface.setWidth(320, updateForm=True)
			self.mapSurface.setHeight(240, updateForm=True)
			self.mapSurface.setBackgroundColor(
				QtGui.QColor(255, 255, 255, 255)
			)
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
		self.setWindowTitle('%s[*] - game1 editor' % self.mapTitle())
		self.setWindowModified(False)
	def loadFile(self, path):
		with open(path) as f:
			self.loadData(json.load(f))
			self.setPath(path)
	def _processTileData(self,
						 tiles,
						 tilesets,
						 layersDepthWidgets,
						 layerWidget=None,
						 tileDefaults={}):
		if not tiles:
			return
		tile = {
			'tileset': 'happy',
			'tx': 0, 'ty': 0,
			'tw': 16, 'th': 16,
			'x': 0, 'y': 0,
			'w': 16, 'h': 16,
			'solid': True,
			'depth': 0,
		}
		tile.update(tileDefaults)
		for tileCurrent in tiles:
			tile.update(tileCurrent)
			position = QtCore.QPoint(tile['x'], tile['y'])
			subimageRect = QtCore.QRect(
				QtCore.QPoint(tile['tx'], tile['ty']),
				QtCore.QSize(tile['tw'], tile['th']),
			)
			if not layerWidget and tile['depth'] not in layersDepthWidgets:
				# TODO: add new layer more properly
				widget = self.createLayer("Layer{}".format(tile['depth']), tile['depth'])
				layersDepthWidgets[tile['depth']] = widget
				widget.setFlags(widget.flags() | Qt.ItemIsEditable)
			mapTile = MapTile(
				tilesets[tile["tileset"]]["treeItem"],
				tilesets[tile["tileset"]]["image"],
				subimageRect,
				position,
				layerWidget or layersDepthWidgets[tile['depth']],
				tile['solid'],
				solidFlag=tile.get('solidDirections') or -1,
				breakable=tile.get('breakable', False),
				shootable=tile.get('shootable', False),
			)
			mapTile.rect.setSize(QtCore.QSize(tile['w'], tile['h']))
			self.mapSurface.addTile(mapTile)
	def createLayer(self, name, depth=0):
		widget = QTreeWidgetItem(
			self.ui.layerTree,
			(
				name,
				str(depth),
				"1",
			)
		)
		widget.setFlags(widget.flags() | Qt.ItemIsEditable)
		return widget
	def deleteLayerWidget(self, widget = None):
		if not widget:
			widgets = self.ui.layerTree.selectedItems()
			if not widgets:
				return
			widget = widgets[0]
		for tile in reversed(self.mapSurface.tiles):
			if widget == tile.layerWidget:
				self.mapSurface.deleteObject(tile)
		i = self.ui.layerTree.indexOfTopLevelItem(widget)
		self.ui.layerTree.takeTopLevelItem(i)
	def deleteLayer(self, name = None):
		for i in range(self.ui.layerTree.topLevelItemCount()):
			widget = self.ui.layerTree.topLevelItem(i)
			if widget.text(0) == name:
				self.deleteLayerWidget(widget)
				break
	def loadData(self, data):
		self.mapSurface.clear()
		MapTile.solidFlag = 0xFF
		# settings
		self.mapSurface.setWidth(data["settings"]["width"], updateForm=True)
		self.mapSurface.setHeight(data["settings"]["height"], updateForm=True)
		self.mapSurface.setBackgroundColor(
			QtGui.QColor(*data["settings"]["background"])
		)
		self.creationCode = data["settings"].get("creationCode", None)
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
		self.ui.layerTree.clear()
		tilesets = {}
		for i in range(self.ui.tilesetTree.topLevelItemCount()):
			widget = self.ui.tilesetTree.topLevelItem(i)
			tilesets[widget.data(0, Qt.UserRole)] = {
				"treeItem": widget,
				"image": QtGui.QImage("../data/%s" % widget.text(0)),
			}

		layersDepthWidgets = {}
		for i in range(self.ui.layerTree.topLevelItemCount()):
			widget = self.ui.layerTree.topLevelItem(i)
			depth = int(widget.text(1))
			#if depth in layers:
			#	raise EditorException("layer depths must be unique")
			layersDepthWidgets[depth] = widget
		self._processTileData(data.get('tiles'), tilesets, layersDepthWidgets)

		# layers
		layers = data.get('layers') or []
		for layer in layers:
			tile = {
				'depth': layers[layer]['depth'],
			}
			layerWidget = self.createLayer(
				layer,
				layers[layer]['depth'],
			)
			self._processTileData(
				layers[layer]['tiles'],
				tilesets,
				None,
				layerWidget,
				tile,
			)

		self.mapSurface.selectedObject = None
		return True
	def saveFile(self, path):
		with open(path,'w') as f:
			json.dump(self.generateData(), f, indent=4, sort_keys=True)
		self.setPath(path)
		return True
	def isModified(self):
		return not self.currentState.equals(self.lastSavedState)

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