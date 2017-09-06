from PyQt5.QtWidgets import QWidget, QApplication, QMenu, QDialog, QColorDialog
from PyQt5.QtGui import QPainter, QImage, QBrush, QColor, QCursor, QTransform
from PyQt5.QtCore import pyqtSignal, QPoint, QRect, QSize, Qt
import sys
from uiCodeEditor import Ui_CodeEditor
import copy

from PyQt5 import QtWidgets, QtCore

import editor

class MapObject:
	init = False
	def __init__(self, type, position, image, creationCode="", customProperties={}):
		self.type = type
		self.rect = QRect(
			position,
			QSize(
				image.width(),
				image.height(),
			),
		)
		self.image = image
		self.creationCode = creationCode
		self.customProperties = customProperties.copy()
	def dump(self):
		o = {
			'type': self.type,
			'x': self.rect.x(),
			'y': self.rect.y(),
		}
		o.update(self.customProperties)
		if self.creationCode:
			o['creationCode'] = self.creationCode
		return o
	def copy(self):
		return MapObject(
			self.type,
			self.rect.topLeft(),
			self.image,
			self.creationCode,
			self.customProperties
		)
class MapTile:
	solidFlag = 0xFF
	def __init__(
			self,
			tilesetWidget,
			tilesetImage,
			subImageRect,
			position,
			layerWidget,
			solid=True,
			surfaceWidth=0,
			surfaceHeight=0):
		self.tileset = tilesetWidget
		self.image = tilesetImage.copy(subImageRect)
		self.rect = QRect(
			position,
			QSize(
				subImageRect.width() if not surfaceWidth else surfaceWidth,
				subImageRect.height() if not surfaceHeight else surfaceHeight,
			),
		)
		self.solidFlag = self.solidFlag
		self.subImageRect = subImageRect.translated(0,0)
		self.solid = solid
		self.layerWidget = layerWidget
	@property
	def depth(self):
		return int(self.layerWidget.text(1))
	@depth.setter
	def depth(self, value):
		layers = {}
		layerTree = self.layerWidget.treeWidget()
		for i in range(layerTree.topLevelItemCount()):
			widget = layerTree.topLevelItem(i)
			depth = int(widget.text(1))
			# if depth in layers:
			#	raise EditorException("layer depths must be unique")
			layers[depth] = widget
		if value in layers:
			self.layerWidget = layers[value]
		else:
			raise editor.EditorException("no such layer")
	def dump(self):
		return {
			'tileset': self.tileset.data(0, Qt.UserRole),
			'x': self.rect.x(),
			'y': self.rect.y(),
			'w': self.rect.width(),
			'h': self.rect.height(),
			'tx': self.subImageRect.x(),
			'ty': self.subImageRect.y(),
			'tw': self.subImageRect.width(),
			'th': self.subImageRect.height(),
			'solid': self.solid,
			'depth': self.depth,
		}
	def copy(self):
		return MapTile(
			self.tileset,
			self.image,
			self.subImageRect,
			self.rect.topLeft(),
			self.layerWidget,
			self.solid,
			self.rect.width(),
			self.rect.height(),
		)

class SelectionMenu(QMenu):
	class PositionDialog(QDialog):
		def __init__(self, parent):
			super().__init__(parent=parent)
			self.layout = QtWidgets.QVBoxLayout()
			self._parent = parent
			# desc
			if isinstance(parent.obj, MapObject):
				description = "#{}, {}, {}x{}".format(
					parent.mapSurface.objects.index(parent.obj),
					parent.obj.type,
					parent.obj.rect.x(), parent.obj.rect.y(),
				)
				self.setWindowTitle("Object position - {}".format(description))
			else:
				description = "#{}, {}x{}".format(
					parent.mapSurface.tiles.index(parent.obj),
					parent.obj.rect.x(), parent.obj.rect.y(),
				)
				self.setWindowTitle("Tile position - {}".format(description))
			self.label = QtWidgets.QLabel(description)
			self.label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
			self.layout.addWidget(self.label)
			# dimensions
			self.objectX = self.addOption("X", parent.obj.rect.x())
			self.objectY = self.addOption("Y", parent.obj.rect.y())
			if isinstance(parent.obj, MapTile):
				self.objectW = self.addOption("Width", parent.obj.rect.width())
				self.objectH = self.addOption("Height", parent.obj.rect.height())
				self.objectDepth = self.addOption("Depth", parent.obj.depth)
			# accept/cancel
			self.buttonBox = QtWidgets.QDialogButtonBox(
				QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
				parent = self
			)
			self.buttonBox.accepted.connect(self.accept)
			self.buttonBox.rejected.connect(self.reject)
			self.layout.addWidget(self.buttonBox)
			self.setLayout(self.layout)
			self.objectX.selectAll()  # FIXME: does not work
		def addOption(self, name, value):
			layout = QtWidgets.QHBoxLayout()
			label = QtWidgets.QLabel("{}:".format(name))
			layout.addWidget(label)
			lineEdit = QtWidgets.QLineEdit(str(value))
			layout.addWidget(lineEdit)
			self.layout.addLayout(layout)
			return lineEdit
		def accept(self):
			self._parent.obj.rect.moveTo(
				int(self.objectX.text()),
				int(self.objectY.text())
			)
			if isinstance(self._parent.obj, MapTile):
				self._parent.obj.rect.setSize(QSize(
					int(self.objectW.text()),
					int(self.objectH.text())
				))
				self._parent.obj.depth = int(self.objectDepth.text())
			super().accept()
	class PropertiesDialog(QDialog):
		def __init__(self, parent):
			super().__init__(parent=parent)
			self.layout = QtWidgets.QGridLayout()
			self._parent = parent
			description = "Object #{}, {}, {}x{}".format(
				parent.mapSurface.objects.index(parent.obj),
				parent.obj.type,
				parent.obj.rect.x(), parent.obj.rect.y(),
			)
			self.setWindowTitle("Object properties - {}".format(description))
			self.label = QtWidgets.QLabel(description)
			self.label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
			self.layout.addWidget(self.label)
			self.createTree()
			self.layout.addWidget(self.propertyTree)
			# buttons
			self.modButtons = QtWidgets.QHBoxLayout()
			self.addItemButton = QtWidgets.QPushButton("+")
			self.removeItemButton = QtWidgets.QPushButton("-")
			self.modButtons.addWidget(self.addItemButton)
			self.modButtons.addWidget(self.removeItemButton)
			self.layout.addItem(self.modButtons)
			self.addItemButton.clicked.connect(self.newItem)
			self.removeItemButton.clicked.connect(self.removeItem)
			self.buttonBox = QtWidgets.QDialogButtonBox(
				QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
				parent=self
			)
			self.buttonBox.accepted.connect(self.accept)
			self.buttonBox.rejected.connect(self.reject)
			self.layout.addWidget(self.buttonBox)
			self.setLayout(self.layout)
		def newItem(self):
			item = self.addProperty("", "")
			self.propertyTree.editItem(item, 0)
		def removeItem(self):
			item = self.propertyTree.selectedItems()[0]
			self.propertyTree.takeTopLevelItem(
				self.propertyTree.indexOfTopLevelItem(item)
			)
		def addProperty(self, k, v):
			item = QtWidgets.QTreeWidgetItem(
				self.propertyTree,
				(k, v)
			)
			item.setFlags(item.flags() | Qt.ItemIsEditable)
			return item
		def createTree(self):
			self.propertyTree = QtWidgets.QTreeWidget(self)
			self.propertyTree.setRootIsDecorated(False)
			self.propertyTree.setItemsExpandable(False)
			self.propertyTree.setHeaderLabels(["Variable", "Value"])
			self.propertyTree.setColumnCount(2)
			self.propertyTree.setSortingEnabled(True)
			# add items
			self.addProperty("type", self._parent.obj.type)
			self.addProperty("x", str(self._parent.obj.rect.x()))
			self.addProperty("y", str(self._parent.obj.rect.y()))
			for prop, val in self._parent.obj.customProperties.items():
				self.addProperty(prop, str(val))
		def accept(self):
			properties = {
				self.propertyTree.topLevelItem(i).text(0) : self.propertyTree.topLevelItem(i).text(1)
				for i in range(self.propertyTree.topLevelItemCount())
			}
			for k in properties:
				try:
					properties[k] = eval(properties[k])
				except NameError:
					properties[k] = properties[k]
			self._parent.obj.rect.moveTo(
				int(properties['x']),
				int(properties['y']),
			)
			self._parent.obj.type = properties['type']
			for k in ('x','y','type'):
				try:
					properties.pop(k)
				except KeyError:
					pass
			self._parent.obj.customProperties = properties
			super().accept()
	def __init__(self, mapSurface, obj):
		super().__init__()
		self.obj = obj
		self.mapSurface = mapSurface
		if isinstance(obj, MapTile):
			self.solidAction = self.addAction("&Solid", self.setSolid)
			self.solidAction.setCheckable(True)
			self.solidAction.setChecked(obj.solid)
			self.addAction("Set &properties", self.showPositionDialog)
		elif isinstance(obj, MapObject):
			self.addAction("&Creation code", mapSurface.editCode)
			self.addAction("&Edit properties", self.showPropertiesDialog)
			self.addAction("Set &position", self.showPositionDialog)
		self.addSeparator()
		self.addAction("&Delete", mapSurface.deleteSelected)
	def setSolid(self):
		self.obj.solid = self.solidAction.isChecked()
	def showPositionDialog(self):
		dialog = self.PositionDialog(self)
		dialog.exec()
	def showPropertiesDialog(self):
		dialog = self.PropertiesDialog(self)
		dialog.exec()

class MapSurface(QWidget):
	clicked = pyqtSignal([object, QPoint, object])
	def __init__(self, parent, editor):
		QWidget.__init__(self, parent)
		self.editor = editor
		#self.setGeometry(5, 5, 200, 1000)
		#self.show()
		self.clear()
	def clear(self):
		self.backgroundColor = QColor(255, 255, 255)
		self.tiles = []
		self.objects = []
		self.selectedObject = None
		self.copyReference = None
		self.tileResizeHover = False
		self.setMouseTracking(True)
		self.repaint()
	def setCopyReference(self):
		self.copyReference = self.selectedObject
	def copyReferenced(self):
		if self.copyReference:
			self.selectedObject = self.copyReference.copy()
			if isinstance(self.selectedObject, MapTile):
				self.tiles.append(self.selectedObject)
			else:
				self.objects.append(self.selectedObject)
			self.selectedObject.rect.translate(16,16)
			self.copyReference = self.selectedObject
			self.repaint()
	def setBackgroundColor(self, color):
		self.backgroundColor = color
		self.repaint()
	def setWidth(self, width, updateForm=False):
		try:
			self.setMinimumSize(int(width), self.height())
			self.setMaximumSize(int(width), self.height())
			if updateForm:
				self.editor.ui.widthSetting.setText(str(width))
		except ValueError:
			pass
	def setHeight(self, height, updateForm=False):
		try:
			self.setMinimumSize(self.width(), int(height))
			self.setMaximumSize(self.width(), int(height))
			if updateForm:
				self.editor.ui.heightSetting.setText(str(height))
		except ValueError:
			pass
	def addTile(self, tile):
		self.tiles.append(tile)
		self.selectedObject = tile
		self.repaint()
	def addObject(self, obj):
		self.objects.append(obj)
		self.selectedObject = obj
		self.resizeDrag = False
		self.repaint()
	def paintEvent(self, event):
		super().paintEvent(event)
		drawables = self.tiles + self.objects
		drawables.sort(key = lambda d: getattr(d, 'depth', 0))
		qp = QPainter()
		qp.begin(self)
		qp.fillRect(0,0,self.width(),self.height(), self.backgroundColor)
		for object in drawables:
			brush = QBrush(object.image)
			transform = QTransform()
			transform.translate(object.rect.left(), object.rect.top())
			brush.setTransform(transform)
			qp.fillRect(object.rect, brush)
		if self.selectedObject:
			qp.setPen(QColor(255,0,0))
			qp.drawRect(self.selectedObject.rect)
		qp.end()
	def resetCursor(self):
		if self.tileResizeHover:
			self.setCursor(QCursor(Qt.ArrowCursor))
			self.tileResizeHover = False
	def updateHoverInfo(self, position):
		hoverObject = None
		message = ""
		for i, obj in enumerate(self.objects):
			if obj.rect.contains(position):
				hoverObject = obj
				message = "Object #{} ({}, {}x{})".format(
					i,
					hoverObject.type,
					hoverObject.rect.x(), hoverObject.rect.y(),
				)
				break
		if not hoverObject:
			for i, tile in enumerate(self.tiles):
				if tile.rect.contains(position):
					hoverObject = tile
					message = "Tile #{} ({}x{}, size: {}x{})".format(
						i,
						hoverObject.rect.x(), hoverObject.rect.y(),
						hoverObject.rect.width(), hoverObject.rect.height(),
					)
					break
		self.editor.ui.statusbar.setHoverInfo(message)
	def mouseMoveEvent(self, e):
		position = e.pos()
		if not self.selectedObject or not (e.buttons() & Qt.LeftButton):
			self.editor.ui.statusbar.setPositionInfo(
				"%sx%s [%sx%s]" % (
					position.x(), position.y(),
					int(position.x()/16)*16, int(position.y()/16)*16,
				)
			)
		self.updateHoverInfo(position)
		if not self.selectedObject:
			self.resetCursor()
			return
		if not self.resizeDrag and isinstance(self.selectedObject, MapTile):
			bottomRight = QRect(
				self.selectedObject.rect.bottomRight(),
				QSize(5,5),
			)
			bottomRight.translate(-2,-2)
			if bottomRight.contains(e.pos()):
				self.setCursor(QCursor(Qt.SizeFDiagCursor))
				self.tileResizeHover = True
			elif self.tileResizeHover:
				self.resetCursor()
		if not (e.buttons() & Qt.LeftButton):
			return
		if not self.resizeDrag:
			position -= self.dragOffset
		if not (e.modifiers() & Qt.ShiftModifier) and \
			self.window().ui.actionSnap.isChecked():
			position = QPoint(
				16*int(position.x() / 16),
				16*int(position.y() / 16),
			)
		if self.resizeDrag:
			self.selectedObject.rect.setSize(QSize(
				position.x()-self.selectedObject.rect.x(),
				position.y()-self.selectedObject.rect.y(),
			))
		else:
			self.selectedObject.rect.moveTo(position)
		self.editor.ui.statusbar.setPositionInfo(
			"%sx%s [%sx%s] (selection)" % (
				position.x(), position.y(),
				int(position.x() / 16) * 16, int(position.y() / 16) * 16,
			)
		)
		self.update()
	def mouseReleaseEvent(self, e):
		self.resizeDrag = False
	def editCode(self):
		if not self.selectedObject or \
			not isinstance(self.selectedObject, MapObject):
			return
		dialog = QDialog(self.window())
		editor = Ui_CodeEditor()
		editor.setupUi(dialog)
		editor.code.setText(self.selectedObject.creationCode)
		dialog.setWindowTitle(
			"Creation code - object #{}, {}".format(
				self.objects.index(self.selectedObject),
				self.selectedObject.type,
			)
		)
		ret = dialog.exec_()
		if ret == dialog.Accepted:
			self.selectedObject.creationCode = editor.code.toPlainText()
	def showContextMenu(self, pos):
		if self.selectedObject:
			SelectionMenu(self, self.selectedObject).exec(pos)
	def mousePressEvent(self, e):
		if self.tileResizeHover:
			self.resizeDrag = True
		else:
			self.resizeDrag = False
			self.selectedObject = None
			for obj in self.objects:
				if obj.rect.contains(e.pos()):
					self.selectedObject = obj
					break
			if not self.selectedObject:
				for tile in self.tiles:
					if tile.rect.contains(e.pos()):
						self.selectedObject = tile
						break
		self.repaint()
		self.clicked.emit(
			self,
			e.pos(),
			self.selectedObject,
		)
		if self.selectedObject:
			if e.button() == Qt.RightButton:
				self.showContextMenu(e.globalPos())
			else:
				self.dragOffset = e.pos() - self.selectedObject.rect.topLeft()
	def deleteSelected(self):
		if self.selectedObject:
			if self.selectedObject in self.objects:
				self.objects.remove(self.selectedObject)
			elif self.selectedObject in self.tiles:
				self.tiles.remove(self.selectedObject)
			self.selectedObject = None
			self.update()