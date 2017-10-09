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

    def checkedButton(self):
        for button in self.buttons:
            if button.isChecked():
                return button

    def accept(self):
        button = self.checkedButton()
        if button in (self.resizeDlg.buttonTopLeft, self.resizeDlg.buttonLeft, self.resizeDlg.buttonBottomLeft):
            horizontalAlignment = self.editorWindow.mapSurface.Left
        elif button in (self.resizeDlg.buttonTop, self.resizeDlg.buttonCenter, self.resizeDlg.buttonBottom):
            horizontalAlignment = self.editorWindow.mapSurface.Center
        elif button in (self.resizeDlg.buttonTopRight, self.resizeDlg.buttonRight, self.resizeDlg.buttonBottomRight):
            horizontalAlignment = self.editorWindow.mapSurface.Right
        self.editorWindow.mapSurface.setWidth(
            int(self.resizeDlg.widthEdit.text()),
            True,
            horizontalAlignment,
        )

        if button in (self.resizeDlg.buttonTopLeft, self.resizeDlg.buttonTop, self.resizeDlg.buttonTopRight):
            verticalAlignment = self.editorWindow.mapSurface.Top
        elif button in (self.resizeDlg.buttonLeft, self.resizeDlg.buttonCenter, self.resizeDlg.buttonRight):
            verticalAlignment = self.editorWindow.mapSurface.Center
        elif button in (self.resizeDlg.buttonBottomLeft, self.resizeDlg.buttonBottom, self.resizeDlg.buttonBottomRight):
            verticalAlignment = self.editorWindow.mapSurface.Bottom
        self.editorWindow.mapSurface.setHeight(
            int(self.resizeDlg.heightEdit.text()),
            True,
            verticalAlignment,
        )
        super().accept()
