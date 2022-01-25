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

from PyQt5 import QtGui, QtWidgets, QtCore
import datetime


class EmptyRoomImportDialog(QtWidgets.QDialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle("Enter session date")
        self.setMinimumSize(400, 100)
        self.date_edit = QtWidgets.QDateEdit(self)
        self.date_edit.setGeometry(25, 25, 150, 25)
        self.date_edit.setObjectName('acquisition date')
        curr_time = datetime.datetime.now()
        self.date_edit.setDateTime(QtCore.QDateTime(QtCore.QDate(curr_time.year, curr_time.month, curr_time.day),
                                                    QtCore.QTime(1, 0, 0)))
        accept_button = QtWidgets.QPushButton("Import", self)
        accept_button.setGeometry(200, 25, 100, 25)
        accept_button.clicked.connect(self.import_files)

    def import_files(self):
        date = self.date_edit.date()
        date_str = date.toString('yyyyMMdd')
        self.ses = date_str
        self.task = 'noise'
        self.accept()
