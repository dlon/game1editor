from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QColor, QPainter, QImage, QDrag, QPixmap
from PyQt5.QtCore import Qt, QMimeData, QRect

class QTilesetSurface(QFrame):
	def __init__(self, parent):
		super().__init__(parent)
		self.image = QImage()
		self.selection = QRect()
	def setImage(self, treeItem):
		self.image.load("../data/%s" % treeItem.text(0))
		self.repaint()
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
	def mousePressEvent(self, e):
		if self.image.isNull():
			return
		self.selection.setWidth(min(
			16+16*int(e.x()/16),
			self.image.width(),
		))
		self.selection.setHeight(min(
			16+16*int(e.y()/16),
			self.image.height(),
		))
		self.update()