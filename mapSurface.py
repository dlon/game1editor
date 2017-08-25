from PyQt5.QtWidgets import QWidget, QApplication, QMenu, QDialog, QColorDialog
from PyQt5.QtGui import QPainter, QImage, QBrush, QColor, QCursor, QTransform
from PyQt5.QtCore import pyqtSignal, QPoint, QRect, QSize, Qt
import sys
from uiCodeEditor import Ui_CodeEditor
import copy

class MapObject:
	init = False
	def __init__(self, type, position, image, creationCode=""):
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
	def dump(self):
		o = {
			'type': self.type,
			'x': self.rect.x(),
			'y': self.rect.y(),
		}
		if self.creationCode:
			o['creationCode'] = self.creationCode
		return o
	def copy(self):
		return MapObject(
			self.type,
			self.rect.topLeft(),
			self.image,
			self.creationCode,
		)
class MapTile:
	def __init__(self,
		tilesetWidget,
		tilesetImage,
		subImageRect,
		position,
		layerWidget,
		solid=True,):
		self.tileset = tilesetWidget
		self.image = tilesetImage.copy(subImageRect)
		self.rect = QRect(
			position,
			QSize(
				subImageRect.width(),
				subImageRect.height(),
			),
		)
		self.subImageRect = subImageRect.translated(0,0)
		self.solid = solid
		self.layerWidget = layerWidget
	@property
	def depth(self):
		return int(self.layerWidget.text(1))
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
		)

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
	def mouseMoveEvent(self, e):
		position = e.pos()
		if not self.selectedObject or not (e.buttons() & Qt.LeftButton):
			self.editor.ui.statusbar.showMessage(
				"%sx%s [%sx%s]" % (
					position.x(), position.y(),
					int(position.x()/16)*16, int(position.y()/16)*16,
				)
			)
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
		self.editor.ui.statusbar.showMessage(
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