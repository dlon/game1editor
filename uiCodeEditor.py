# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'codeEditor.ui'
#
# Created by: PyQt5 UI code generator 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CodeEditor(object):
    def setupUi(self, CodeEditor):
        CodeEditor.setObjectName("CodeEditor")
        CodeEditor.resize(484, 465)
        self.gridLayout = QtWidgets.QGridLayout(CodeEditor)
        self.gridLayout.setObjectName("gridLayout")
        self.code = QtWidgets.QTextEdit(CodeEditor)
        self.code.setObjectName("code")
        self.gridLayout.addWidget(self.code, 0, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(CodeEditor)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(CodeEditor)
        self.buttonBox.accepted.connect(CodeEditor.accept)
        self.buttonBox.rejected.connect(CodeEditor.reject)
        QtCore.QMetaObject.connectSlotsByName(CodeEditor)

    def retranslateUi(self, CodeEditor):
        _translate = QtCore.QCoreApplication.translate
        CodeEditor.setWindowTitle(_translate("CodeEditor", "Dialog"))

