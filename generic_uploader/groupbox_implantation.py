# -*- coding: utf-8 -*-<

#     BIDS Manager collect, organise and manage data in BIDS format.
#     Copyright © 2018-2020 Aix-Marseille University, INSERM, INS
#
#     This file is part of BIDS Manager.
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

from PyQt5 import QtCore, QtGui, QtWidgets
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class GroupboxImplantation(QtWidgets.QGroupBox):
    def __init__(self, modalite):
        QtGui.QGroupBox.__init__(self)
        #self = QtGui.QGroupBox(central_widget)
        self.setEnabled(False)
        self.setMinimumSize(QtCore.QSize(400, 0))
        self.setMaximumSize(QtCore.QSize(361, 200))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        self.setFont(font)
        self.setObjectName(_fromUtf8("groupBox_implantation"))
        self.gridLayout_4 = QtGui.QGridLayout(self)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.label_10 = QtGui.QLabel(self)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        font.setPointSize(10)
        self.label_10.setFont(font)
        self.label_10.setObjectName(_fromUtf8("label_10"))
        self.gridLayout_4.addWidget(self.label_10, 0, 0, 1, 1)
        spacerItem3 = QtGui.QSpacerItem(20, 38, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.gridLayout_4.addItem(spacerItem3, 0, 2, 2, 1)
        self.listElectrodeTypes = QtGui.QListWidget(self)
        self.listElectrodeTypes.setEnabled(False)
        self.listElectrodeTypes.setMaximumSize(QtCore.QSize(131, 81))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        self.listElectrodeTypes.setFont(font)
        self.listElectrodeTypes.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.listElectrodeTypes.setResizeMode(QtGui.QListView.Adjust)
        self.listElectrodeTypes.setViewMode(QtGui.QListView.ListMode)
        self.listElectrodeTypes.setWordWrap(False)
        self.listElectrodeTypes.setObjectName(_fromUtf8("listElectrodeTypes"))
        item = QtGui.QListWidgetItem()
        self.listElectrodeTypes.addItem(item)
        item = QtGui.QListWidgetItem()
        self.listElectrodeTypes.addItem(item)
        item = QtGui.QListWidgetItem()
        self.listElectrodeTypes.addItem(item)
        item = QtGui.QListWidgetItem()
        self.listElectrodeTypes.addItem(item)
        self.gridLayout_4.addWidget(self.listElectrodeTypes, 1, 0, 3, 1)
        spacerItem4 = QtGui.QSpacerItem(80, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_4.addItem(spacerItem4, 2, 1, 1, 1)
        self.comboBoxImplantation = QtGui.QComboBox(self)
        self.comboBoxImplantation.setEnabled(False)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBoxImplantation.sizePolicy().hasHeightForWidth())
        self.comboBoxImplantation.setSizePolicy(sizePolicy)
        self.comboBoxImplantation.setMinimumSize(QtCore.QSize(150, 0))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        self.comboBoxImplantation.setFont(font)
        self.comboBoxImplantation.setDuplicatesEnabled(False)
        self.comboBoxImplantation.setObjectName(_fromUtf8("comboBoxImplantation"))
        self.comboBoxImplantation.addItem(_fromUtf8(""))
        self.comboBoxImplantation.addItem(_fromUtf8(""))
        self.comboBoxImplantation.addItem(_fromUtf8(""))
        self.comboBoxImplantation.addItem(_fromUtf8(""))
        self.gridLayout_4.addWidget(self.comboBoxImplantation, 2, 2, 1, 1)
        spacerItem5 = QtGui.QSpacerItem(28, 20, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.gridLayout_4.addItem(spacerItem5, 2, 3, 1, 1)
        spacerItem6 = QtGui.QSpacerItem(20, 47, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_4.addItem(spacerItem6, 3, 2, 1, 1)