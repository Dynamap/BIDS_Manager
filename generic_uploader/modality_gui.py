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
from math import ceil


class ModalityGui(QtWidgets.QDialog):
    # def __init__(self, session, modality, acquisition, task, run):
    def __init__(self, keys_dict):
        QtWidgets.QDialog.__init__(self)
        self.setObjectName("Modality GUI")
        self.setWindowTitle("Modality GUI")
        self.setModal(True)
        '''elements = [element for element in ["session", "modality", "acquisition", "task", "run", "space"]
                    if eval(element)]'''
        elements = keys_dict.keys()
        nb_elements = len(elements)
        line_edit_list = []
        element_list = []
        i = 0
        largeur_des_elements = 250
        inter_element = 20
        hauteur_des_elements = 25
        nb_by_line = 3.0
        nb_line = ceil(nb_elements/nb_by_line) + 1 # 'import' button
        self.resize(nb_by_line*largeur_des_elements + (nb_by_line+1)*inter_element,
                    nb_line*2*hauteur_des_elements + (nb_line+1)*inter_element)
        self.setSizeGripEnabled(True)
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
            line_edit_list[i].setObjectName(field)
            line_edit_list[i].setText(field)
            combobox_list.append(QtWidgets.QComboBox(self))
            combobox_list[i].setEnabled(True)
            combobox_list[i].setGeometry(QtCore.QRect(inter_element + reste_division*(largeur_des_elements+inter_element),
                                                      inter_element + (i//nb_by_line*(2*hauteur_des_elements+inter_element))
                                                      + hauteur_des_elements, largeur_des_elements, hauteur_des_elements))
            combobox_list[i].setObjectName(field)
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
        self.import_button.setGeometry(QtCore.QRect(inter_element + (nb_by_line-1)
                                                    * (largeur_des_elements+inter_element),
                                                    ((nb_line-1)*(2*hauteur_des_elements+inter_element))
                                                    + hauteur_des_elements, largeur_des_elements / 2,
                                                    hauteur_des_elements))
        self.import_button.setText("Import")
        self.import_button.clicked.connect(self.import_files)
        self.combobox_list = combobox_list

    def import_files(self):
        self.accept()
        self.close()
