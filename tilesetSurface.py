from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QColor, QPainter, QImage, QDrag, QPixmap
from PyQt5.QtCore import Qt, QMimeData, QRect, QPoint

from mapSurface import MapTile

class QTilesetSurface(QFrame):
	def __init__(self, parent):
		super().__init__(parent)
		self.image = QImage()
		self.tileset = ''
		self.selection = QRect()
	def setImage(self, treeItem):
		self.selection = QRect()
		self.image.load("../data/%s" % treeItem.text(0))
		self.tileset = treeItem.text(0)
		self.repaint()
	def handleMapSurfaceClick(self, mapSurface, position, selectedObject):
		if self.image.isNull() or self.selection.isNull():
			return
		if not selectedObject:
			print("tilesetSurface: adding tile to map surface")
			mapSurface.addTile(self.createTile(position))
	def createTile(self, position):
		if self.image.isNull() or self.selection.isNull():
			return None
		if self.window().ui.actionSnap.isChecked():
			position = QPoint(
				16*int(position.x() / 16),
				16*int(position.y() / 16),
			)
		return MapTile(
			tilesetPath=self.tileset,
			tilesetImage=self.image,
			subImageRect=self.selection,
			position=position,
		)
	def paintEvent(self, event):
		super().paintEvent(event)
		painter = QPainter(self)
		rect = self.contentsRect()
		painter.drawImage(
			rect.left(),
			rect.top(),
			self.image,
		)
		painter.setPen(QColor(255,0,0))
		painter.drawRect(self.selection)
	def mouseMoveEvent(self, e):
		if not (e.buttons() & Qt.LeftButton):
			return
		self.selection.setWidth(min(max(
			16+16*int(e.x()/16) - self.selection.x(),
			16,
		), self.image.width()))
		self.selection.setHeight(min(max(
			16+16*int(e.y()/16) - self.selection.y(),
			16,
		), self.image.height()))
		self.update()
	def mousePressEvent(self, e):
		if self.image.isNull():
			return
		self.selection.setX(16*int(e.x()/16))
		self.selection.setY(16*int(e.y()/16))
		self.selection.setWidth(min(
			self.image.width() - 16*int(e.x()/16),
			16,
		))
		self.selection.setHeight(min(
			self.image.height() - 16*int(e.y()/16),
			16,
		))
		self.update()