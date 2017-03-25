from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QColor, QPainter, QImage, QDrag, QPixmap
from PyQt5.QtCore import Qt, QMimeData, QRect, QPoint
from mapSurface import MapObject

class QObjectPreview(QFrame):
	def __init__(self, parent):
		super().__init__(parent)
		self.image = QImage()
		self.type = ''
		self.unknownImage = QImage(":/editor/unknown.png")
	def setImage(self, treeItem):
		image = treeItem.data(0, Qt.UserRole)
		if not image:
			self.image = self.unknownImage
		else:
			# TODO: handle subimages correctly
			if type(image) == dict:
				image = image['file']
			self.image = QImage(image)
		self.type = treeItem.text(0)
		self.repaint()
	def paintEvent(self, event):
		super().paintEvent(event)
		painter = QPainter(self)
		rect = self.contentsRect()
		painter.drawImage(
			rect.left() + rect.width()/2 - self.image.width()/2,
			rect.top() + rect.height()/2 - self.image.height()/2,
			self.image
		)
	def mousePressEvent(self, ev):
		if not self.type:
			return
		mimeData = QMimeData()
		mimeData.setData('application/x-game1dndobject', self.type.encode('latin1'))
		drag = QDrag(self)
		drag.setMimeData(mimeData)
		drag.setPixmap(QPixmap.fromImage(self.image))
		drag.setHotSpot(self.image.rect().bottomRight()/2)
		drag.exec(Qt.MoveAction)
	def dragEnterEvent(self, ev):
		print('amhere1')
		if ev.source() == self:
			ev.setDropAction(Qt.MoveAction)
		else:
			ev.ignore()
	def dragMoveEvent(self, ev):
		#if ev.mimeData().hasFormat('application/x-game1dndobject')
		print('amhere')
		if ev.source() == self:
			ev.setDropAction(Qt.MoveAction)
		else:
			ev.ignore()
	def handleMapSurfaceClick(self, mapSurface, position, selectedObject):
		if not self.type:
			return
		if self.window().ui.tabWidget.currentIndex() != 0:
			return
		if not selectedObject:
			print("objectPreview: adding object to map surface")
			mapSurface.addObject(self.createObject(position))
	def createObject(self, position):
		if not self.type:
			return None
		if self.window().ui.actionSnap.isChecked():
			position = QPoint(
				16*int(position.x() / 16),
				16*int(position.y() / 16),
			)
		return MapObject(
			type=self.type,
			position=position,
			image=self.image,
		)