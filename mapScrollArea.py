from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtCore import Qt
from PyQt5 import QtCore


class QMapScrollArea(QScrollArea):
    middleScrollSpeed = 1.05

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initialDrag = None

    def setWidget(self, QWidget):
        if self.widget():
            self.removeEventFilter(self.widget())
        super().setWidget(QWidget)
        self.installEventFilter(QWidget)

    def eventFilter(self, QObject, QEvent):
        if isinstance(QEvent, QMouseEvent):
            if QEvent.button() == Qt.MiddleButton:
                if not self.initialDrag:
                    self.initialDrag = QEvent.pos()
                    hsb = self.horizontalScrollBar()
                    vsb = self.verticalScrollBar()
                    self.initialScrollPos = QtCore.QPointF(
                        hsb.value(),
                        vsb.value(),
                    )
                else:
                    self.initialDrag = None
                QEvent.accept()
                return True
            elif self.initialDrag and QEvent.button() == 0:
                newSPos = -self.middleScrollSpeed * (QEvent.pos() - self.initialDrag) +\
                          self.initialScrollPos
                hsb = self.horizontalScrollBar()
                vsb = self.verticalScrollBar()
                hsb.setValue(newSPos.x())
                vsb.setValue(newSPos.y())
                QEvent.accept()
                return True
        return False
