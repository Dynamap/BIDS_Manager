# -*- coding: utf-8 -*-
#     BIDS Manager collect, organise and manage data in BIDS format.
#     Copyright © 2018-2020 Aix-Marseille University, INSERM, INS
#
#     This file is part of BIDS Manager. It generates the Generic Uploader
#     interface.
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

# Form implementation generated from reading ui file 'generic_uploaderUI.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from generic_uploader.groupbox_modalite import GroupboxModalite

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


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        sizeObject = QtWidgets.QDesktopWidget().screenGeometry(-1)
        #MainWindow.resize(994, 912)
        #Aude: Determine the size of the monitor and do everything according to it
        if sizeObject.width() > 800 and sizeObject.width() < 2000:
            mainwidth = round((sizeObject.width()*3)/4)
        elif sizeObject.width() > 2000:
            mainwidth = round((sizeObject.width() * 2) / 4)
        else:
            mainwidth = sizeObject.width()
        mainheight = round((sizeObject.height()*5)/6)
        MainWindow.resize(mainwidth, mainheight)
        MainWindow.setAutoFillBackground(False)
        height_box = round(mainheight/4)
        width_box = round(mainwidth/5)
        row_size = round(height_box/2)
        req = [item for item in MainWindow.requirements['Requirements'].keys() if item != "Subject"]
        #window_box_nb_vert = ceil(len(req)/2) + 2 + 2# 2 du sujet, 2 de la validation
        window_box_nb_vert = round((height_box*2)/row_size) + 4
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout_10 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_10.setObjectName(_fromUtf8("gridLayout_10"))
        self.groupBox_identite = QtWidgets.QGroupBox(self.centralwidget)
        #self.groupBox_identite.setMinimumSize(QtCore.QSize(400, 200))
        #self.groupBox_identite.setMaximumSize(QtCore.QSize(361, 16777215))
        self.groupBox_identite.setMinimumSize(QtCore.QSize((width_box*2)-20, 16777215))
        ## modif sam 10/09/2020 --------------
        #Aude: determine the size of everything for the group identity box
        ## 10pt means 13px and 8pt means 11px
        box_height = round(height_box/5)
        max_box_height = 51
        if box_height >= 13:
            ptFont = 10
        else:
            ptFont = 8
        box_width = round(((width_box*2)/6)*3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        self.groupBox_identite.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        font.setPointSize(ptFont)
        self.groupBox_identite.setFont(font)
        self.groupBox_identite.setObjectName(_fromUtf8("groupBox_identite"))
        self.gridLayout_5 = QtWidgets.QGridLayout(self.groupBox_identite)
        self.gridLayout_5.setObjectName(_fromUtf8("gridLayout_5"))
        self.labelName = QtWidgets.QLabel(self.groupBox_identite)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        font.setPointSize(ptFont)
        self.labelName.setFont(font)
        self.labelName.setObjectName(_fromUtf8("labelName"))
        self.gridLayout_5.addWidget(self.labelName, 0, 0, 1, 2)
        self.TextName = QtWidgets.QPlainTextEdit(self.groupBox_identite)
        self.TextName.setEnabled(True)
        self.TextName.setMaximumSize(QtCore.QSize(391, 45))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        font.setPointSize(ptFont)
        self.TextName.setFont(font)
        self.TextName.setTabChangesFocus(True)
        self.TextName.setReadOnly(False)
        self.TextName.setObjectName(_fromUtf8("TextName"))
        self.gridLayout_5.addWidget(self.TextName, 0, 3, 1, 3)
        self.labelFirstname = QtWidgets.QLabel(self.groupBox_identite)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        font.setPointSize(ptFont)
        self.labelFirstname.setFont(font)
        self.labelFirstname.setObjectName(_fromUtf8("labelFirstname"))
        self.gridLayout_5.addWidget(self.labelFirstname, 1, 0, 1, 2)
        #spacerItem = QtWidgets.QSpacerItem(68, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        #self.gridLayout_5.addItem(spacerItem, 1, 1, 1, 2)
        self.TextPrenom = QtWidgets.QPlainTextEdit(self.groupBox_identite)
        self.TextPrenom.setEnabled(True)
        self.TextPrenom.setMaximumSize(QtCore.QSize(391, 45))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        font.setPointSize(ptFont)
        self.TextPrenom.setFont(font)
        self.TextPrenom.setTabChangesFocus(True)
        self.TextPrenom.setObjectName(_fromUtf8("TextPrenom"))
        self.gridLayout_5.addWidget(self.TextPrenom, 1, 3, 1, 3)
        self.labelBirthdate = QtWidgets.QLabel(self.groupBox_identite)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        font.setPointSize(ptFont)
        self.labelBirthdate.setFont(font)
        self.labelBirthdate.setObjectName(_fromUtf8("labelBirthdate"))
        self.gridLayout_5.addWidget(self.labelBirthdate, 2, 0, 1, 2)
        self.dateEdit = QtWidgets.QDateEdit(self.groupBox_identite)
        self.dateEdit.setEnabled(True)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        font.setPointSize(ptFont)
        self.dateEdit.setFont(font)
        self.dateEdit.setDateTime(QtCore.QDateTime(QtCore.QDate(1752, 9, 14), QtCore.QTime(0, 0, 0)))
        self.dateEdit.setObjectName(_fromUtf8("dateEdit"))
        self.gridLayout_5.addWidget(self.dateEdit, 2, 3, 1, 3)
        # spacerItem1 = QtWidgets.QSpacerItem(128, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        # self.gridLayout_5.addItem(spacerItem1, 2, 4, 1, 2)
        self.anonymize_patient_checkBox = QtWidgets.QCheckBox(self.groupBox_identite)
        font = QtGui.QFont()
        font.setPointSize(ptFont)
        self.anonymize_patient_checkBox.setFont(font)
        self.anonymize_patient_checkBox.setChecked(True)
        self.anonymize_patient_checkBox.setObjectName(_fromUtf8("anonymize"))
        self.gridLayout_5.addWidget(self.anonymize_patient_checkBox, 3, 0, 1, 2)
        # ajout du champ pour alias si non anonymisé
        self.id_textinfo = QtWidgets.QLabel(self.groupBox_identite)
        self.id_textinfo.setVisible(False)
        self.id_textinfo.setMaximumSize(QtCore.QSize(300, 31))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        # font.setBold(True)
        font.setPointSize(ptFont)
        self.id_textinfo.setFont(font)
        self.id_textinfo.setObjectName(_fromUtf8("id_info"))
        self.id_textinfo.setText("alternative ID")
        self.gridLayout_5.addWidget(self.id_textinfo, 3, 2, 1, 2)
        self.id_textbox = QtWidgets.QPlainTextEdit(self.groupBox_identite)
        self.id_textbox.setVisible(False)
        self.id_textbox.setMaximumSize(QtCore.QSize(350, 41))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        font.setPointSize(ptFont)
        self.id_textbox.setFont(font)
        self.id_textbox.setObjectName(_fromUtf8("id_textbox"))
        self.gridLayout_5.addWidget(self.id_textbox, 3, 4, 1, 2)
        self.labelSexe = QtWidgets.QLabel(self.groupBox_identite)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        font.setPointSize(ptFont)
        self.labelSexe.setFont(font)
        self.labelSexe.setObjectName(_fromUtf8("labelSexe"))
        self.gridLayout_5.addWidget(self.labelSexe, 4, 0, 1, 1)
        self.radioButtonM = QtWidgets.QRadioButton(self.groupBox_identite)
        self.radioButtonM.setEnabled(True)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        font.setPointSize(ptFont)
        self.radioButtonM.setFont(font)
        self.radioButtonM.setObjectName(_fromUtf8("radioButtonM"))
        self.gridLayout_5.addWidget(self.radioButtonM, 4, 2, 1, 1)
        self.radioButtonF = QtWidgets.QRadioButton(self.groupBox_identite)
        self.radioButtonF.setEnabled(True)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        font.setPointSize(ptFont)
        self.radioButtonF.setFont(font)
        self.radioButtonF.setObjectName(_fromUtf8("radioButtonF"))
        self.gridLayout_5.addWidget(self.radioButtonF, 4, 3, 1, 1)
        # spacerItem2 = QtWidgets.QSpacerItem(137, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        # self.gridLayout_5.addItem(spacerItem2, 4, 4, 1, 1)
        self.scroll_identity = QtWidgets.QScrollArea()
        self.scroll_identity.setWidget(self.groupBox_identite)
        self.scroll_identity.setFixedHeight(height_box)
        self.scroll_identity.setFixedWidth(round(width_box*2))
        self.layout_identity = QtWidgets.QVBoxLayout(MainWindow)
        self.layout_identity.addWidget(self.scroll_identity)
        self.gridLayout_10.addWidget(self.scroll_identity, 0, 3, 2, 2)
        #spacerItem20 = QtWidgets.QSpacerItem(378, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        #self.gridLayout_10.addItem(spacerItem20, 7, 0, 1, 2)
        self.groupBox_log = QtWidgets.QGroupBox(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        self.groupBox_log.setFont(font)
        self.groupBox_log.setTitle(_fromUtf8(""))
        self.groupBox_log.setObjectName(_fromUtf8("groupBox_log"))
        self.gridLayout_7 = QtWidgets.QGridLayout(self.groupBox_log)
        self.gridLayout_7.setObjectName(_fromUtf8("gridLayout_7"))
        spacerItem21 = QtWidgets.QSpacerItem(512, 17, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_7.addItem(spacerItem21, 0, 0, 1, 1)
        self.listWidget = QtWidgets.QListWidget(self.groupBox_log)
        self.listWidget.setMinimumSize(QtCore.QSize(0, 0))
        self.listWidget.setMaximumSize(QtCore.QSize(width_box*3, height_box*3))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.listWidget.setFont(font)
        self.listWidget.setViewMode(QtWidgets.QListView.ListMode)
        self.listWidget.setModelColumn(0)
        self.listWidget.setSelectionRectVisible(False)
        self.listWidget.setObjectName(_fromUtf8("listWidget"))
        self.gridLayout_7.addWidget(self.listWidget, 1, 0, 1, 1)
        self.gridLayout_10.addWidget(self.groupBox_log, 0, 0, window_box_nb_vert-1, 3)  # -1 du logo
        #le logo
        self.logo_ins = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        self.logo_ins.setFont(font)
        self.logo_ins.setText(_fromUtf8(""))
        self.logo_ins.setPixmap(QtGui.QPixmap('generic_uploader\\config\\logoINSreduit.png'))
        self.logo_ins.setObjectName(_fromUtf8("logo_ins"))
        #self.gridLayout_10.addWidget(self.logo_ins, window_box_nb_vert, 0, 2, 3)
        self.gridLayout_10.addWidget(self.logo_ins, window_box_nb_vert-1, 0, 1, 3)
        #test Aude to add scrollabr
        self.groupBox_mod = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_mod.setObjectName(_fromUtf8("groupBox_mod"))
        self.groupBox_mod.setMinimumSize(QtCore.QSize((width_box * 2) -20, 16777215))
        self.gridLayout_mod = QtWidgets.QGridLayout(self.groupBox_mod)
        self.gridLayout_mod.setObjectName(_fromUtf8("gridLayout_mod"))
        self.groupBox_list = []
        self.import_button_list = []
        horz_pos = -1
        for i in range(0, len(MainWindow.moda_needed)):
            self.groupBox_list.append(GroupboxModalite(MainWindow.moda_needed[i], width_box, ptFont))
            impair = i % 2
            if impair == 0:
                vert_pos =0
                horz_pos = horz_pos + 1
            else:
                vert_pos=2
            # vert_pos = 2+i/2
            # horz_pos = 3+impair
            # self.gridLayout_10.addWidget(self.groupBox_list[i], vert_pos, horz_pos, 1, 1)
            self.gridLayout_mod.addWidget(self.groupBox_list[i], horz_pos, vert_pos, 1, 2)
            self.groupBox_list[i].raise_()
        #self.groupBox_mod.setLayout(self.gridLayout_mod)
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidget(self.groupBox_mod)
        #self.scroll.setWidgetResizable(True)
        self.scroll.setFixedHeight(round(height_box*2))
        self.scroll.setFixedWidth(round(width_box*2))
        self.layout = QtWidgets.QVBoxLayout(MainWindow)
        self.layout.addWidget(self.scroll)
        self.gridLayout_10.addWidget(self.scroll, 2, 3, 2, 2)
        self.groupBox_validation = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_validation.setMinimumSize(QtCore.QSize(width_box, 0))
        #self.groupBox_validation.setMinimumSize(QtCore.QSize(400, 0))
        #self.groupBox_validation.setMaximumSize(QtCore.QSize(3610, 1500))
        #self.groupBox_validation.setMaximumSize(QtCore.QSize(400, 120))  ## SAM modif 10/09/2020
        self.groupBox_validation.setMaximumSize(QtCore.QSize(width_box*3, height_box))
        self.groupBox_validation.setObjectName(_fromUtf8("groupBox_validation"))
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_validation)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        # spacerItem22 = QtWidgets.QSpacerItem(20, 17, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        # self.gridLayout_2.addItem(spacerItem22, 0, 0, 1, 1)
        # spacerItem23 = QtWidgets.QSpacerItem(20, 17, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        # self.gridLayout_2.addItem(spacerItem23, 0, 1, 1, 1)
        # spacerItem24 = QtWidgets.QSpacerItem(20, 17, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        # self.gridLayout_2.addItem(spacerItem24, 0, 2, 1, 1)
        self.pushButtonValidation = QtWidgets.QPushButton(self.groupBox_validation)
        self.pushButtonValidation.setEnabled(False)
        self.pushButtonValidation.setMinimumSize(QtCore.QSize(box_width, box_height))
        #self.pushButtonValidation.setMaximumSize(QtCore.QSize(box_width, box_height))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        font.setPointSize(ptFont)
        self.pushButtonValidation.setFont(font)
        self.pushButtonValidation.setObjectName(_fromUtf8("pushButtonValidation"))
        self.gridLayout_2.addWidget(self.pushButtonValidation, 0, 0, 1, 1)
        # spacerItem25 = QtWidgets.QSpacerItem(48, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        # self.gridLayout_2.addItem(spacerItem25, 0, 1, 1, 1)
        self.pushButtonReset = QtWidgets.QPushButton(self.groupBox_validation)
        self.pushButtonReset.setEnabled(False)
        self.pushButtonReset.setMinimumSize(QtCore.QSize(box_width, box_height))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        font.setPointSize(ptFont)
        self.pushButtonReset.setFont(font)
        self.pushButtonReset.setObjectName(_fromUtf8("pushButtonReset"))
        self.gridLayout_2.addWidget(self.pushButtonReset, 0, 1, 1, 1)
        self.progressBar = QtWidgets.QProgressBar(self.groupBox_validation)
        self.progressBar.setEnabled(True)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        self.progressBar.setFont(font)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.gridLayout_2.addWidget(self.progressBar, 1, 0, 1, 1)
        #spacerItem26 = QtWidgets.QSpacerItem(48, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        #self.gridLayout_2.addItem(spacerItem26, 1, 1, 1, 1)
        #spacerItem27 = QtWidgets.QSpacerItem(68, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        #self.gridLayout_2.addItem(spacerItem27, 1, 1, 1, 1)
        self.labelProgressbar = QtWidgets.QLabel(self.groupBox_validation)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        font.setPointSize(ptFont)
        self.labelProgressbar.setFont(font)
        self.labelProgressbar.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.labelProgressbar.setText(_fromUtf8(""))
        self.labelProgressbar.setTextFormat(QtCore.Qt.AutoText)
        self.labelProgressbar.setAlignment(QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.labelProgressbar.setObjectName(_fromUtf8("labelProgressbar"))
        self.gridLayout_2.addWidget(self.labelProgressbar, 3, 0, 1, 1)
        #Add by Aude: Button Finish and Import
        self.pushButtonFinish = QtWidgets.QPushButton(self.groupBox_validation)
        self.pushButtonFinish.setFont(font)
        self.pushButtonFinish.setEnabled(True)
        self.pushButtonFinish.setMinimumSize(QtCore.QSize(box_width, box_height))
        self.pushButtonFinish.setObjectName(_fromUtf8("pushButtonFinish"))
        self.gridLayout_2.addWidget(self.pushButtonFinish, 1, 1, 1, 1)
        self.gridLayout_10.addWidget(self.groupBox_validation, window_box_nb_vert - 2, 3, 2, 2)
        self.groupBox_log.raise_()
        self.groupBox_identite.raise_()
        self.logo_ins.raise_()
        self.groupBox_validation.raise_()
        # self.pushButtonResume.raise_()
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 994, 17))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.groupBox_identite.setTitle(_translate("MainWindow", "Identity", None))
        self.groupBox_identite.setStyleSheet("QGroupBox {"
                                             "font-weight: bold;"
                                             "font-size: 12px; }")
        self.labelName.setText(_translate("MainWindow", "last name", None))
        self.labelFirstname.setText(_translate("MainWindow", "first name", None))
        self.labelBirthdate.setText(_translate("MainWindow", "birth date", None))
        self.labelSexe.setText(_translate("MainWindow", "sex", None))
        self.radioButtonM.setText(_translate("MainWindow", "M", None))
        self.radioButtonF.setText(_translate("MainWindow", "F", None))
        self.anonymize_patient_checkBox.setText(_translate("MainWindow", "anonymize", None))
        self.groupBox_validation.setTitle(_translate("MainWindow", "Validation", None))
        self.groupBox_validation.setStyleSheet('QGroupBox {'
                                                'font-size: 12px;'
                                                'font-weight: bold;'
                                                '}')
        self.pushButtonValidation.setText(_translate("MainWindow", "Validate", None))
        self.pushButtonReset.setText(_translate("MainWindow", "Reset", None))
        self.pushButtonFinish.setText(_translate('MainWindow', 'Finish and Import', None))

