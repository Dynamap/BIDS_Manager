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

from PyQt5 import QtGui, QtWidgets


class MegImportDialog(QtWidgets.QDialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle("MEG files or MEG folder ?")
        self.setMinimumSize(275, 25)
        files_button = QtWidgets.QPushButton("Files")
        files_button.clicked.connect(self.import_files)
        folder_button = QtWidgets.QPushButton("Folder")
        folder_button.clicked.connect(self.import_folder)
        meg_dialog_button = QtWidgets.QDialogButtonBox(self)
        meg_dialog_button.addButton(files_button, meg_dialog_button.YesRole)
        meg_dialog_button.addButton(folder_button, meg_dialog_button.NoRole)
        self.flag_import = ""

    def import_files(self):
        self.flag_import = "files"
        self.accept()

    def import_folder(self):
        self.flag_import = "folder"
        self.accept()