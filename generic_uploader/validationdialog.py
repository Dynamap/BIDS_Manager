# -*- coding: utf-8 -*-

#     BIDS Uploader collect, creates the data2import requires by BIDS Manager
#     and transfer data if in sFTP mode.
#     Copyright © 2018-2020 Aix-Marseille University, INSERM, INS
#
#     This file is part of BIDS Uploader.
#
#     BIDS Manager is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     any later version
#
#     BIDS Manager is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with BIDS Manager.  If not, see <https://www.gnu.org/licenses/>
#
#     Authors: Samuel Medina, 2018-2020

# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Validation dialog"))
        Dialog.resize(500, 300)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(200, 240, 161, 32))
        self.buttonBox.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.lineEdit_uploaderlastname = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_uploaderlastname.setEnabled(False)
        self.lineEdit_uploaderlastname.setGeometry(QtCore.QRect(30, 130, 161, 20))
        self.lineEdit_uploaderlastname.setObjectName(_fromUtf8("lineEdit_uploaderlastname"))
        self.lineEdit_uploaderfirstname = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_uploaderfirstname.setEnabled(False)
        self.lineEdit_uploaderfirstname.setGeometry(QtCore.QRect(30, 160, 161, 20))
        self.lineEdit_uploaderfirstname.setObjectName(_fromUtf8("lineEdit_uploaderfirstname"))
        self.lineEdit_uploaderdate = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_uploaderdate.setEnabled(False)
        self.lineEdit_uploaderdate.setGeometry(QtCore.QRect(30, 190, 161, 20))
        self.lineEdit_uploaderdate.setObjectName(_fromUtf8("lineEdit_uploaderdate"))
        self.lineEdit_filelastname = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_filelastname.setEnabled(False)
        self.lineEdit_filelastname.setGeometry(QtCore.QRect(220, 130, 161, 20))
        self.lineEdit_filelastname.setObjectName(_fromUtf8("lineEdit_filelastname"))
        self.lineEdit_filefirstname = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_filefirstname.setEnabled(False)
        self.lineEdit_filefirstname.setGeometry(QtCore.QRect(220, 160, 161, 20))
        self.lineEdit_filefirstname.setObjectName(_fromUtf8("lineEdit_filefirstname"))
        self.lineEdit_filebirthdate = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_filebirthdate.setEnabled(False)
        self.lineEdit_filebirthdate.setGeometry(QtCore.QRect(220, 190, 161, 20))
        self.lineEdit_filebirthdate.setObjectName(_fromUtf8("lineEdit_filebirthdate"))
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(20, 20, 361, 20))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(30, 100, 161, 20))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setGeometry(QtCore.QRect(220, 100, 161, 20))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.label_4 = QtWidgets.QLabel(Dialog)
        self.label_4.setGeometry(QtCore.QRect(50, 239, 141, 31))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.label_4.setFont(font)
        self.label_4.setObjectName(_fromUtf8("label_4"))

        self.retranslateUi(Dialog)
        # QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
        # QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.label.setText(_translate("Dialog", "Patient Name different from those in file", None))
        self.label_2.setText(_translate("Dialog", "Generic uploader information", None))
        self.label_3.setText(_translate("Dialog", "File information", None))
        self.label_4.setText(_translate("Dialog", "Force and continue?", None))

