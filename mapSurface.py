from PyQt5.QtWidgets import QWidget, QApplication, QMenu, QDialog, QColorDialog
from PyQt5.QtGui import QPainter, QImage, QBrush, QColor, QImage
from PyQt5.QtCore import pyqtSignal, QPoint, QRect, QSize, Qt
import sys
from uiCodeEditor import Ui_CodeEditor

class MapObject:
	init = False
	def __init__(self, type, position, image):
		self.type = type
		self.rect = QRect(
			position,
			QSize(
				image.width(),
				image.height(),
			),
		)
		self.image = image
		self.creationCode = ""
	def dump(self):
		o = {
			'type': self.type,
			'x': self.position.x(),
			'y': self.position.y(),
		}
		if self.creationCode:
			o['creationCode'] = self.creationCode
		return o
class MapTile:
	def __init__(self,
		tilesetPath,
		tilesetImage,
		subImageRect,
		position,
		solid=True):
		self.tileset = tilesetPath
		self.image = tilesetImage.copy(subImageRect)
		self.rect = QRect(
			position,
			QSize(
				subImageRect.width(),
				subImageRect.height(),
			),
		)
		self.subImageRect = subImageRect
		self.solid = solid
	def dump(self):
		return {
			'tileset': self.tileset,
			'x': self.rect.x(),
			'y': self.rect.y(),
			'w': self.rect.width(),
			'h': self.rect.height(),
			'tx': self.subImageRect.x(),
			'ty': self.subImageRect.y(),
			'tw': self.subImageRect.width(),
			'th': self.subImageRect.height(),
			'solid': self.solid,
		}

class MapSurface(QWidget):
	clicked = pyqtSignal([object, QPoint, object])
	def __init__(self, parent):
		QWidget.__init__(self, parent)
		#self.setGeometry(5, 5, 200, 1000)
		#self.show()
		self.resize(1000,10)
		self.backgroundColor = QColor(255,255,255)
		self.tiles = []
		self.objects = []
		self.selectedObject = None
	def setBackgroundColor(self, color):
		self.backgroundColor = color
		self.repaint()
	def setWidth(self, width):
		try:
			self.setMinimumSize(int(width), self.height())
			self.setMaximumSize(int(width), self.height())
		except ValueError:
			pass
	def setHeight(self, height):
		try:
			self.setMinimumSize(self.width(), int(height))
			self.setMaximumSize(self.width(), int(height))
		except ValueError:
			pass
	def addTile(self, tile):
		self.tiles.append(tile)
		self.selectedObject = tile
		self.repaint()
	def addObject(self, obj):
		self.objects.append(obj)
		self.selectedObject = obj
		self.repaint()
	def paintEvent(self, event):
		super().paintEvent(event)
		qp = QPainter()
		qp.begin(self)
		qp.fillRect(0,0,self.width(),self.height(), self.backgroundColor)
		for object in self.objects:
			qp.drawImage(
				object.rect.topLeft(),
				object.image
			)
		for tile in self.tiles:
			qp.drawImage(
				tile.rect.topLeft(),
				tile.image,
			)
		if self.selectedObject:
			qp.setPen(QColor(255,0,0))
			qp.drawRect(self.selectedObject.rect)
		qp.end()
	def mouseMoveEvent(self, e):
		if not (e.buttons() & Qt.LeftButton) or \
			not self.selectedObject:
			return
		position = e.pos() - self.dragOffset
		if not (e.modifiers() & Qt.ShiftModifier) and \
			self.window().ui.actionSnap.isChecked():
			position = QPoint(
				16*int(position.x() / 16),
				16*int(position.y() / 16),
			)
		self.selectedObject.rect.moveTo(position)
		self.update()
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
		if not self.selectedObject:
			return
		menu = QMenu(self)
		if isinstance(self.selectedObject, MapTile):
			solidAction = menu.addAction("&Solid")
			solidAction.setCheckable(True)
			solidAction.setChecked(self.selectedObject.solid)
		elif isinstance(self.selectedObject, MapObject):
			creationCodeAction = menu.addAction("&Creation code")
		menu.addSeparator()
		deleteAction = menu.addAction("&Delete")
		action = menu.exec_(pos)
		if action == deleteAction:
			self.deleteSelected()
		if isinstance(self.selectedObject, MapTile):
			if action == solidAction:
				self.selectedObject.solid = action.isChecked()
		elif isinstance(self.selectedObject, MapObject):
			if action == creationCodeAction:
				self.editCode()
	def mousePressEvent(self, e):
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
		if self.selectedObject and e.button() == Qt.RightButton:
			self.showContextMenu(e.globalPos())
		if self.selectedObject:
			self.dragOffset = e.pos() - self.selectedObject.rect.topLeft()
	def deleteSelected(self):
		if self.selectedObject:
			if self.selectedObject in self.objects:
				self.objects.remove(self.selectedObject)
			elif self.selectedObject in self.tiles:
				self.tiles.remove(self.selectedObject)
			self.selectedObject = None
			self.update()