from PyQt5.QtWidgets import QFrame, QMessageBox
from PyQt5.QtGui import QColor, QPainter, QImage, QDrag, QPixmap
from PyQt5.QtCore import Qt, QMimeData, QRect, QPoint

from mapSurface import MapTile

class QTilesetSurface(QFrame):
	def __init__(self, parent):
		super().__init__(parent)
		self.image = QImage()
		self.tileset = ''
		self.tilesetWidget = None
		self.selection = QRect()
	def setImage(self, treeItem):
		self.selection = QRect()
		self.image = QImage("../data/%s" % treeItem.text(0))
		self.tileset = treeItem.text(0)
		self.tilesetWidget = treeItem
		self.repaint()
	def handleMapSurfaceClick(self, mapSurface, position, selectedObject, button):
		if button != Qt.LeftButton:
			return
		if self.image.isNull() or self.selection.isNull():
			return
		if self.window().ui.tabWidget.currentIndex() != 1:
			return
		if mapSurface.tileResizeHover:
			return
		tile = self.createTile(position)
		if not selectedObject and tile:
			print("tilesetSurface: adding tile to map surface")
			mapSurface.addTile(tile)
	def createTile(self, position):
		if self.image.isNull() or self.selection.isNull():
			return None
		layerWidget = self.window().ui.layerTree.currentItem()
		if not layerWidget:
			msg = QMessageBox(
				QMessageBox.Information,
				"Tile layer",
				"You must select a layer",
				QMessageBox.Ok,
				self,
			)
			msg.show()
			return None
		if self.window().ui.actionSnap.isChecked():
			position = QPoint(
				16*int(position.x() / 16),
				16*int(position.y() / 16),
			)
		return MapTile(
			tilesetWidget=self.tilesetWidget,
			tilesetImage=self.image,
			subImageRect=self.selection,
			position=position,
			solid=self.window().ui.actionSolidTile.isChecked(),
			layerWidget=layerWidget,
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