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


class PatientRequirementsClass(QtWidgets.QDialog):
    def __init__(self, requirements, suj):
        QtWidgets.QDialog.__init__(self)
        self.setObjectName("Requirements windows")
        self.setWindowTitle("Requirements windows")
        # self.resize(1000, 800)
        # self.setSizeGripEnabled(True)
        self.setModal(True)
        requirements['Requirements']['Subject'].keys()
        required_keys = requirements['Requirements']['Subject']['keys']
        needed_items = requirements['Requirements']['Subject']['required_keys']
        nb_keys = len(required_keys)
        # required_keys = suj.required_keys
        line_edit_list = []
        requirements_object_list = []
        i = 0
        largeur_des_elements = 250
        hauteur_des_elements = 25
        inter_element = 20
        nb_by_line = 3.0
        nb_line = ceil(nb_keys / nb_by_line) + 1  # 'OK' button
        # self.resize(1000, nb_keys/3*hauteur_des_elements*4)
        self.resize(nb_by_line*largeur_des_elements + (nb_by_line-1)*inter_element + largeur_des_elements/nb_by_line*(nb_by_line-1),
                    nb_line * 2 * 1.5 * hauteur_des_elements + hauteur_des_elements)
        self.setSizeGripEnabled(True)
        for key in required_keys:
            if key == "sub":
                continue
            reste_division = i % nb_by_line
            line_edit_list.append(QtWidgets.QLineEdit(self))
            line_edit_list[i].setEnabled(False)
            line_edit_list[i].setGeometry(QtCore.QRect(inter_element + reste_division*(largeur_des_elements+largeur_des_elements/nb_by_line)
                                                       , (i//nb_by_line*2*1.5*hauteur_des_elements) + hauteur_des_elements,
                                                       largeur_des_elements, hauteur_des_elements))
            line_edit_list[i].setObjectName(key)
            if key in needed_items:
                line_edit_list[i].setText(key + " *")
                line_edit_list[i].setToolTip("Mandatory")
            else:
                line_edit_list[i].setText(key)
            if not required_keys[key]:
                requirements_object_list.append(QtWidgets.QLineEdit(self))
                requirements_object_list[i].setEnabled(True)
                requirements_object_list[i].setGeometry(QtCore.QRect(inter_element + reste_division *
                                                                     (largeur_des_elements+largeur_des_elements/nb_by_line),
                                                                     (i//nb_by_line*2*1.5*hauteur_des_elements)
                                                                     + 2*hauteur_des_elements,
                                                                     largeur_des_elements, hauteur_des_elements))
                requirements_object_list[i].setObjectName(key)
                requirements_object_list[i].setText(suj[key])
            else:
                requirements_object_list.append(QtWidgets.QComboBox(self))
                requirements_object_list[i].setEnabled(True)
                requirements_object_list[i].setGeometry(QtCore.QRect(inter_element + reste_division *
                                                                     (largeur_des_elements+largeur_des_elements/nb_by_line),
                                                                     (i//nb_by_line*2*1.5*hauteur_des_elements)
                                                                     + 2*hauteur_des_elements,
                                                                     largeur_des_elements, hauteur_des_elements))
                requirements_object_list[i].setObjectName(key)
                if not 'n/a' in required_keys[key]:
                    requirements_object_list[i].addItems(["n/a"] + required_keys[key])
                else:
                    requirements_object_list[i].addItems(required_keys[key])
                if suj[key]:
                    key_idx = requirements_object_list[i].findText(suj[key])
                    requirements_object_list[i].setCurrentIndex(key_idx)
            if key == "sex" or key == "age":
                requirements_object_list[i].setEnabled(False)
            #     sex_idx = requirements_object_list[i].findText(suj[key])
            #     requirements_object_list[i].setCurrentIndex(sex_idx)
            # if key == "age":
            #     requirements_object_list[i].setText(suj[key])
            i += 1
        # add OK button
        self.ok_button = QtWidgets.QPushButton(self)
        self.ok_button.setEnabled(True)
        self.ok_button.setGeometry(QtCore.QRect(20 + 2 * (largeur_des_elements+largeur_des_elements/3),
                                                ((nb_line-1)*2*1.5*hauteur_des_elements) + 2*hauteur_des_elements,
                                                largeur_des_elements/2, hauteur_des_elements))
        self.ok_button.setText("OK")
        self.ok_button.clicked.connect(self.ok_function)
        self.requirements_object_list = requirements_object_list

    def ok_function(self):
        self.accept()
        self.close()
