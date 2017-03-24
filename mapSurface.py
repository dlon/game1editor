from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QImage, QBrush, QColor
import sys

class MapObject:
	init = False
	def __init__(self, **kwargs):
		self.editor = kwargs['editor']
		self.x = kwargs['x']
		self.y = kwargs['y']
		self.creationCode = kwargs['creationCode']
		self.type = kwargs["type"]
		self.init = True
	def __setattr__(self, k, v):
		if self.init:
			super().__setattr__(k, v)
			#self.editor.changed()
			print('MapObject changed')
		else:
			super().__setattr__(k, v)
	def dump(self):
		o = {
			'x': self.x,
			'y': self.y,
		}
		if self.creationCode:
			o['creationCode'] = self.creationCode
		return o
class MapTile:
	def __init__(self, **kwargs):
		for k,v in kwargs.items():
			self.__dict__[k] = v
	def dump(self):
		return {
			'x': self.x,
			'y': self.y,
			'w': self.w,
			'h': self.h,
			'xOffset': self.xOffset,
			'yOffset': self.yOffset,
		}

class MapSurface(QWidget):
	def __init__(self, parent):
		QWidget.__init__(self, parent)
		#self.setGeometry(300, 300, 200, 200)
		#self.show()
		self.image = QImage("player_run.bmp")
		self.tiles = []
		self.objects = []
	def paintEvent(self, event):
		qp = QPainter()
		qp.begin(self)
		qp.fillRect(0,0,self.width(),self.height(), QColor(255,255,255))
		for object in self.objects:
			qp.drawImage(0, 0, object.image)
		qp.end()