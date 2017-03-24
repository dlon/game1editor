from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QColor, QPainter, QImage, QDrag, QPixmap
from PyQt5.QtCore import Qt, QMimeData

class QTilesetSurface(QFrame):
	def __init__(self, parent):
		super().__init__(parent)
		self.image = QImage()
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