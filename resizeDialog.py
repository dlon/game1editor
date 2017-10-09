from uiResizeDialog import Ui_ResizeDialog
from PyQt5 import QtGui, QtWidgets

class ResizeDialog(QtWidgets.QDialog):
    def __init__(self, editorWindow):
        super().__init__(editorWindow)
        self.editorWindow = editorWindow
        self.resizeDlg = Ui_ResizeDialog()
        self.resizeDlg.setupUi(self)
        self.resizeDlg.widthEdit.setText(
            str(editorWindow.mapSurface.surfaceWidth)
        )
        self.resizeDlg.heightEdit.setText(
            str(editorWindow.mapSurface.surfaceHeight)
        )
        self.resizeDlg.widthEdit.selectAll()

    def accept(self):
        self.editorWindow.mapSurface.setWidth(
            int(self.resizeDlg.widthEdit.text()), True
        )
        self.editorWindow.mapSurface.setHeight(
            int(self.resizeDlg.heightEdit.text()), True
        )
        super().accept()
