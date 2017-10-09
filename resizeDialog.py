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

        self.buttons = [
            self.resizeDlg.buttonTopLeft,
            self.resizeDlg.buttonTop,
            self.resizeDlg.buttonTopRight,
            self.resizeDlg.buttonLeft,
            self.resizeDlg.buttonCenter,
            self.resizeDlg.buttonRight,
            self.resizeDlg.buttonBottomLeft,
            self.resizeDlg.buttonBottom,
            self.resizeDlg.buttonBottomRight,
        ]
        for button in self.buttons:
            button.released.connect(self.handleAlignmentButton)
        self.resizeDlg.buttonTopLeft.setChecked(True)

    def handleAlignmentButton(self):
        for button in self.buttons:
            if button != self.sender():
                button.setChecked(False)

    def accept(self):
        self.editorWindow.mapSurface.setWidth(
            int(self.resizeDlg.widthEdit.text()), True
        )
        self.editorWindow.mapSurface.setHeight(
            int(self.resizeDlg.heightEdit.text()), True
        )
        super().accept()
