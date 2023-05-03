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
from math import ceil

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class ModalityGui(QtWidgets.QDialog):
    # def __init__(self, session, modality, acquisition, task, run):
    def __init__(self, keys_dict):
        QtWidgets.QDialog.__init__(self)
        self.setObjectName("Modality GUI")
        self.setWindowTitle("Modality GUI")
        self.setModal(True)
        self.flag_emptyroom =False
        try:
            screen_geom = self.screen().geometry()
            screen_width = screen_geom.width()
            screen_height = screen_geom.height()
        except AttributeError:
            screen_width = 1920
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        '''elements = [element for element in ["session", "modality", "acquisition", "task", "run", "space"]
                    if eval(element)]'''
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Segoe UI"))
        font.setPointSize(8)
        elements = keys_dict.keys()
        nb_elements = len(elements)
        line_edit_list = []
        element_list = []
        i = 0
        largeur_des_elements = 250*screen_width/1920
        inter_element = 20*screen_width/1920
        hauteur_des_elements = 25
        nb_by_line = 3.0
        nb_line = ceil(nb_elements/nb_by_line) + 1 # 'import' button
        #self.resize
        self.setFixedSize(nb_by_line*largeur_des_elements + (nb_by_line+1)*inter_element,
                    nb_line*2*hauteur_des_elements + (nb_line+1)*inter_element)
        self.setSizeGripEnabled(False)
        line_edit_list = []
        combobox_list = []
        i = 0
        for field in elements:
            reste_division = i % nb_by_line
            line_edit_list.append(QtWidgets.QLineEdit(self))
            line_edit_list[i].setEnabled(False)
            line_edit_list[i].setGeometry(QtCore.QRect(inter_element + reste_division*(largeur_des_elements+inter_element)
                                                       , inter_element + (i//nb_by_line*(2*hauteur_des_elements+inter_element)),
                                                       largeur_des_elements, hauteur_des_elements))
            line_edit_list[i].setSizePolicy(sizePolicy)
            line_edit_list[i].setObjectName(field)
            line_edit_list[i].setText(field)
            line_edit_list[i].setFont(font)
            combobox_list.append(QtWidgets.QComboBox(self))
            combobox_list[i].setEnabled(True)
            combobox_list[i].setGeometry(QtCore.QRect(inter_element + reste_division*(largeur_des_elements+inter_element),
                                                      inter_element + (i//nb_by_line*(2*hauteur_des_elements+inter_element))
                                                      + hauteur_des_elements, largeur_des_elements, hauteur_des_elements))
            combobox_list[i].setSizePolicy(sizePolicy)
            combobox_list[i].setObjectName(field)
            combobox_list[i].setFont(font)
            # combobox_list[i].addItems(eval(field))
            # correction car ne fonctionnait pas avec les globals sidecars si pas de liste
            if type(keys_dict[field]) is not list:
                combobox_list[i].addItems([keys_dict[field]])
            else:
                combobox_list[i].addItems(keys_dict[field])
            i = i+1
        # add import button
        self.import_button = QtWidgets.QPushButton(self)
        self.import_button.setEnabled(True)
        self.import_button.setGeometry(QtCore.QRect(inter_element + (nb_by_line - 1)
                                                    * (largeur_des_elements+inter_element),
                                                    ((nb_line-1)*(2*hauteur_des_elements+inter_element))
                                                    + hauteur_des_elements, largeur_des_elements / 2,
                                                    hauteur_des_elements))
        self.import_button.setSizePolicy(sizePolicy)
        self.import_button.setText("Import")
        self.import_button.setFont(font)
        self.import_button.clicked.connect(self.import_files)
        self.combobox_list = combobox_list
        if 'meg' in keys_dict['modality']:
            self.empty_room = QtWidgets.QPushButton(self)
            self.empty_room.setEnabled(True)
            self.empty_room.setGeometry(QtCore.QRect(inter_element + (0)
                                                        * (largeur_des_elements + inter_element),
                                                        ((nb_line - 1) * (2 * hauteur_des_elements + inter_element))
                                                        + hauteur_des_elements, largeur_des_elements / 2,
                                                        hauteur_des_elements))
            self.empty_room.setText("empty_room")
            self.empty_room.clicked.connect(self.import_empty_room)

    def import_files(self):
        self.accept()
        self.close()

    def import_empty_room(self):
        self.flag_emptyroom= True
        self.accept()
