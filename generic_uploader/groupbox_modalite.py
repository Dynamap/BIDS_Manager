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

from PyQt5 import QtCore, QtGui, QtWidgets
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class GroupboxModalite(QtWidgets.QGroupBox):
    def __init__(self, modalite, width_max, ptFont):
        QtWidgets.QGroupBox.__init__(self)
        #self = QtWidgets.QGroupBox(central_widget)
        self.setEnabled(False)
        #self.setMinimumSize(QtCore.QSize(195, 0))
        # self.setMaximumSize(QtCore.QSize(175, 100))
        self.setMaximumSize(QtCore.QSize(width_max-10, 100))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        self.setFont(font)
        self.setObjectName(_fromUtf8("groupBox_" + modalite))
        self.setTitle(modalite)
        self.gridLayout_9 = QtWidgets.QGridLayout(self)
        self.gridLayout_9.setObjectName(_fromUtf8("gridLayout_9"))
        # spacerItem7 = QtWidgets.QSpacerItem(20, 37, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        # self.gridLayout_9.addItem(spacerItem7, 0, 0, 1, 1)
        self.import_button = QtWidgets.QPushButton(self)
        self.import_button.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.import_button.sizePolicy().hasHeightForWidth())
        self.import_button.setSizePolicy(sizePolicy)
        self.import_button.setMinimumSize(QtCore.QSize(150, 30))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        font.setPointSize(ptFont)
        self.import_button.setFont(font)
        self.import_button.setObjectName(_fromUtf8("import_" + modalite))
        #self.import_button.setText("import_" + modalite)
        self.import_button.setText("import")        # modif sam pour ne pas déborder si nom long
        self.import_button.setToolTip("Click to import " + modalite)
        self.gridLayout_9.addWidget(self.import_button, 1, 0, 1, 1)
        # spacerItem8 = QtWidgets.QSpacerItem(20, 34, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        # self.gridLayout_9.addItem(spacerItem8, 2, 0, 1, 1)
        # spacerItem9 = QtWidgets.QSpacerItem(174, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        # self.gridLayout_9.addItem(spacerItem9, 3, 0, 1, 1)