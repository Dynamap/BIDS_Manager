# -*- coding: utf-8 -*-<

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

from PyQt5 import QtGui, QtWidgets


class AnatImportDialog(QtWidgets.QDialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle("Nifti file or Dicom folder ?")
        self.setMinimumSize(300, 100)
        files_button = QtWidgets.QPushButton("Nifti file")
        files_button.clicked.connect(self.import_files)
        folder_button = QtWidgets.QPushButton("Dicom Folder")
        folder_button.clicked.connect(self.import_folder)
        meg_dialog_button = QtWidgets.QDialogButtonBox(self)
        meg_dialog_button.addButton(files_button, meg_dialog_button.YesRole)
        meg_dialog_button.addButton(folder_button, meg_dialog_button.NoRole)
        self.flag_import = ""

    def import_files(self):
        self.flag_import = "Nifti file"
        self.accept()

    def import_folder(self):
        self.flag_import = "Dicom Folder"
        self.accept()