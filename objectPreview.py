from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QColor, QPainter, QImage
from PyQt5.QtCore import Qt

class QObjectPreview(QFrame):
	def __init__(self, parent):
		super().__init__(parent)
		self.image = QImage()
	def setImage(self, treeItem):
		image = treeItem.data(0, Qt.UserRole)
		if not image:
			return
		# TODO: handle subimages correctly
		if type(image) == dict:
			image = image['file']
		self.image.load(image)
		self.repaint()
	def paintEvent(self, event):
		painter = QPainter(self)
		rect = self.contentsRect()
		painter.drawImage(
			rect.left() + rect.width()/2 - self.image.width()/2,
			rect.top() + rect.height()/2 - self.image.height()/2,
			self.image
		)