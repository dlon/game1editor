from uiResizeDialog import Ui_ResizeDialog
from PyQt5 import QtGui, QtWidgets

class ResizeDialog(QtWidgets.QDialog):
    def __init__(self, editorWindow):
        super().__init__(editorWindow)
        resizeDlg = Ui_ResizeDialog()
        resizeDlg.setupUi(self)
        resizeDlg.widthEdit.setText(
            str(editorWindow.mapSurface.surfaceWidth)
        )
        resizeDlg.heightEdit.setText(
            str(editorWindow.mapSurface.surfaceHeight)
        )
        resizeDlg.widthEdit.selectAll()