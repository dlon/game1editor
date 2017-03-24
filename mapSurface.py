from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QImage, QBrush, QColor
from PyQt5.QtCore import pyqtSignal, QPoint
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
	def __init__(self,
		tilesetPath,
		tilesetImage,
		subImageRect,
		position,
		solid=True):
		self.tileset = tilesetPath
		self.image = tilesetImage
		self.position = position
		self.subImageRect = subImageRect
		self.solid = solid
	def dump(self):
		return {
			'tileset': self.tileset,
			'x': self.x,
			'y': self.y,
			'w': self.w,
			'h': self.h,
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
	def addTile(self, tile):
		self.tiles.append(tile)
		self.repaint()
	def paintEvent(self, event):
		super().paintEvent(event)
		qp = QPainter()
		qp.begin(self)
		qp.fillRect(0,0,self.width(),self.height(), self.backgroundColor)
		for object in self.objects:
			qp.drawImage(0, 0, object.image)
		for tile in self.tiles:
			qp.drawImage(
				tile.position,
				tile.image,
				tile.subImageRect,
			)
		qp.end()
	def mousePressEvent(self, e):
		self.clicked.emit(
			self,
			e.pos(),
			None,
		)