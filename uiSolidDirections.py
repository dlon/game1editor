# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'solidDirections.ui'
#
# Created by: PyQt5 UI code generator 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(203, 51)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.upCheck = QtWidgets.QCheckBox(Dialog)
        self.upCheck.setObjectName("upCheck")
        self.horizontalLayout.addWidget(self.upCheck)
        self.downCheck = QtWidgets.QCheckBox(Dialog)
        self.downCheck.setObjectName("downCheck")
        self.horizontalLayout.addWidget(self.downCheck)
        self.rightCheck = QtWidgets.QCheckBox(Dialog)
        self.rightCheck.setObjectName("rightCheck")
        self.horizontalLayout.addWidget(self.rightCheck)
        self.leftCheck = QtWidgets.QCheckBox(Dialog)
        self.leftCheck.setObjectName("leftCheck")
        self.horizontalLayout.addWidget(self.leftCheck)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.upCheck.setText(_translate("Dialog", "U"))
        self.downCheck.setText(_translate("Dialog", "D"))
        self.rightCheck.setText(_translate("Dialog", "R"))
        self.leftCheck.setText(_translate("Dialog", "L"))

