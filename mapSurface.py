from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QImage
import sys

class MapSurface(QWidget):
	def __init__(self, parent):
		QWidget.__init__(self, parent)
		#self.setGeometry(300, 300, 200, 200)
		#self.show()
		self.image = QImage("player_run.bmp")
	def showEvent(self, event):
		pass
	def paintEvent(self, event):
		qp = QPainter()
		qp.begin(self)
		qp.drawImage(0, 0, self.image)
		qp.end()
