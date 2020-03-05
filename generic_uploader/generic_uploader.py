# -*- coding: utf-8 -*-

#     BIDS Manager collect, organise and manage data in BIDS format.
#     Copyright © 2018-2020 Aix-Marseille University, INSERM, INS
#
#     This file is part of BIDS Manager. BIDS uploader collects data and
#     creates the data2import requires by BIDS Manager.
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

"""
Created on Mon Mar 19 11:19:56 2018
"""

from PyQt5 import QtGui, QtCore, QtWidgets
from generic_uploader.generic_uploaderUI import Ui_MainWindow
from generic_uploader.validationdialog import Ui_Dialog
import sys
import os
import shutil
import hashlib
import datetime
import re
import unicodedata
from generic_uploader.micromed import anonymize_micromed
from generic_uploader.read_seeg_images_header import read_headers
from generic_uploader.anonymizeDicom import anonymize as anonymize_dcm
# import pysftp
# import paramiko
import bids_manager.ins_bids_class
from generic_uploader import patient_requirements_class
from generic_uploader.modality_gui import ModalityGui
from generic_uploader.import_by_modality import import_by_modality

if 0:  # Used to compile, otherwise, it crashes
    pass


class GenericUploader(QtWidgets.QMainWindow, Ui_MainWindow):
    class ListMenuObject(QtWidgets.QMenu):
        def __init__(self, papa):
            QtWidgets.QMenu.__init__(self)
            # Creation des actions a effectuer lors du clique droit sur la liste de log
            #   Action de suppresion de l'action
            self.delete_action = QtWidgets.QAction("Delete", self)
            self.delete_action.triggered.connect(lambda: self.delete_list_command(papa))
            #   Action de Forcage de l'opération de l'action
            self.force_action = QtWidgets.QAction("Force", self)
            self.force_action.triggered.connect(lambda: self.force_list_command(papa))
            self.check_and_force_action = QtWidgets.QAction("Check", self)
            self.check_and_force_action.triggered.connect(lambda: self.check_and_force_list_command(papa))
            self.modify_identity = QtWidgets.QAction("Modify_identity", self)
            self.modify_identity.triggered.connect(lambda: self.modify_id(papa))
            self.modify_info_action = QtWidgets.QAction("Modify_info", self)
            self.modify_info_action.triggered.connect(lambda: self.modify_info_command(papa))
            self.addAction(self.delete_action)
            self.addAction(self.force_action)
            self.addAction(self.check_and_force_action)

        def delete_list_command(self, papa):
            selected_item = papa.listWidget.currentRow()
            if str(papa.listWidget.currentItem().text()).startswith("ID"):
                return
            else:
                modality = papa.maplist[selected_item]["Modality"]
                index_in_sub = papa.maplist[selected_item]["Index"]
                # trouver le fichier et le supprimer de la list
                current_file2delete = str(papa.listWidget.currentItem().text())
                current_file2delete_part = current_file2delete.split(", ")
                current_file2delete_part2 = current_file2delete_part[1].split(" : ")
                current_file2delete = current_file2delete_part2[1]
                idx2delete = [idx for idx in range(0, len(papa.electrode_brand)) if
                              papa.electrode_brand[idx].split(", ")[0] == current_file2delete]
                for index in sorted(idx2delete, reverse=True):
                    papa.electrode_brand.pop(index)
                # vider la liste
                removed_item = papa.Subject[modality].pop(index_in_sub)
                # reordonner les run ici
                papa.Subject = papa.update_subject_class(papa.Subject, removed_item, modality)
                papa.maplist.pop(selected_item)
                papa.mapping_subject2list(papa.Subject, True)
                return papa
            # elif str(papa.listWidget.currentItem().text()).startswith("Addi"):
            #     index_in_addi = papa.addi_files.index(papa.maplist[selected_item]["Addi_file_path"])
            #     papa.addi_files.pop(index_in_addi)
            #     papa.listWidget.takeItem(selected_item)
            #     if papa.checkBoxProtocole1.isChecked():
            #         papa.mapping_subject2list(papa.Subject, True)
            #         return papa
            #     if papa.checkBoxProtocole2.isChecked():
            #         papa.mapping_subject2list(papa.SubjectPHRC, True)
            #     return papa
            # elif str(papa.listWidget.currentItem().text()).startswith("Fiche"):
            #     index_in_fiche_patient = papa.fiche_patient.index(papa.maplist[selected_item]["fiche_patient"])
            #     papa.fiche_patient.pop(index_in_fiche_patient)
            #     papa.listWidget.takeItem(selected_item)
            #     if papa.checkBoxProtocole1.isChecked():
            #         papa.mapping_subject2list(papa.Subject, True)
            #         return papa
            #     if papa.checkBoxProtocole2.isChecked():
            #         papa.mapping_subject2list(papa.SubjectPHRC, True)
            #     return papa

        def modify_id(self, papa):
            papa.listWidget.currentItem().setForeground(QtGui.QColor("black"))
            papa.TextName.setEnabled(True)
            papa.TextPrenom.setEnabled(True)
            papa.dateEdit.setEnabled(True)
            papa.restart_groupbox_identite()
            # papa.groupBox_protocole.setEnabled(True)
#             papa.listElectrodeTypes.setDisabled(True)
            for groupBox in papa.groupBox_list:
                groupBox.setDisabled(True)
            '''papa.import_neuroimagery.setDisabled(True)
            papa.import_ieeg.setDisabled(True)
            papa.import_eeg.setDisabled(True)
            papa.import_meg.setDisabled(True)'''
            # papa.pushButtonAddiFiles.setDisabled(True)
            papa.pushButtonValidation.setDisabled(True)
            f = open(papa.log_filename, "r")
            lines = f.readlines()
            f.close()
            f = open(papa.log_filename, "w")
            f.write(lines[0])
            f.close()

        def modify_info_command(self, papa):
            papa.standardize_info()

        def force_list_command(self, papa):
            papa.listWidget.currentItem().setForeground(QtGui.QColor("orange"))
            papa.maplist[papa.listWidget.currentRow()]["curr_state"] = "forced"
            # ecriture dans le log des validation =========================
            f = open(papa.log_filename, "a+")
            f.write(str(papa.listWidget.currentItem().text()) + " =====>" + "forced" + "\n")
            f.close()
            # =============================================================
            papa.flag_validated, papa.current_state = papa.check_total_validation()
            if papa.flag_validated:
                upload_dialog = QtWidgets.QMessageBox.question(papa, "Bids import ?",
                                                           "Do you want to copy and format to bids?",
                                                           QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
                if upload_dialog == QtWidgets.QMessageBox.Cancel:
                    return
                else:
                    papa.copy_and_upload()

        def check_and_force_list_command(self, papa):
            current_action = papa.maplist[papa.listWidget.currentRow()]
            sujet = papa.Subject
            if os.path.exists(sujet[current_action["Modality"]][current_action["Index"]]["fileLoc"]):
                data_path = sujet[current_action["Modality"]][current_action["Index"]]["fileLoc"]
            else:
                data_path = os.path.join(papa.init_path, sujet[current_action["Modality"]][current_action["Index"]]["fileLoc"])
            if os.path.isdir(data_path):
                [nom, prenom, date] = papa.recursively_read_imagery_folder(data_path)
            else:
                [nom, prenom, date] = read_headers(data_path)
            if nom == prenom == date == 0:
                qmesbox = QtWidgets.QMessageBox(papa)
                qmesbox.setText("Le dossier ne contient pas que des fichiers dicom")
                qmesbox.exec_()
                return 0
            my_dialog = Dialog(papa.listWidget)
            my_dialog.lineEdit_uploaderlastname.setText(str(papa.TextName.toPlainText()).lower())
            my_dialog.lineEdit_uploaderfirstname.setText(str(papa.TextPrenom.toPlainText()).lower())
            # modif pour même format de date
            entered_data = papa.birth_date_str[0:2] + papa.birth_date_str[3:5] + papa.birth_date_str[6:10]
            my_dialog.lineEdit_uploaderdate.setText(entered_data)
            my_dialog.lineEdit_filelastname.setText(nom.lower())
            my_dialog.lineEdit_filefirstname.setText(prenom.lower())
            my_dialog.lineEdit_filebirthdate.setText(date)
            res = my_dialog.exec_()
            if res == 0:
                return 0
            else:
                papa.listWidget.currentItem().setForeground(QtGui.QColor("orange"))
                papa.maplist[papa.listWidget.currentRow()]["curr_state"] = "forced"
                # ecriture dans le log des validation =========================
                f = open(papa.log_filename, "a+")
                f.write(str(papa.listWidget.currentItem().text()) + " =====>" + "forced" + "\n")
                f.close()
                # =============================================================
                papa.flag_validated, papa.current_state = papa.check_total_validation()
                if papa.flag_validated:
                    upload_dialog = QtWidgets.QMessageBox.question(papa, "Import data ?",
                                                               "Do you want to copy data ?",
                                                               QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
                    if upload_dialog == QtWidgets.QMessageBox.Cancel:
                        return
                    else:
                        papa.copy_and_upload()

    def variable_initialization(self):
        self.dateEdit.setDateTime(QtCore.QDateTime(QtCore.QDate(1753, 9, 14), QtCore.QTime(1, 0, 0)))
        self.radioButtonM.setToolTip("Please select sex for ID creation")
        self.radioButtonF.setToolTip("Please select sex for ID creation")
        # self.groupBox_implantation.listElectrodeTypes.setToolTip("Select electrode manufacturer")
        # self.comboBoxImplantation.setToolTip("Chosse scheme type")
        # self.import_neuroimagery.setToolTip("Choose neuroimagery files to import")
        # self.import_ieeg.setToolTip("Choose ieeg files to import")
        # self.import_meg.setToolTip("Choose meg files to import")
        # self.import_eeg.setToolTip("Choose eeg files to import")
        self.listWidget.setToolTip("Double click to check, modifiy or delete")
        self.pushButtonValidation.setToolTip(
            "Compare data and patient info, copy when validated, and anonymisation if checked")
        self.pushButtonReset.setToolTip("re-initialize the window")
        self.pushButtonFinish.setToolTip('Close the window and start the importation of the data selected by subject.')
        init_path = self.init_path
        self.last_path = init_path
        self.log_path = os.path.join(self.importation_path, "importer_log")
        # creation du dossier des logs
        if not os.path.isdir(self.log_path):
            os.mkdir(self.log_path)
        # self.already_uploaded = os.path.join(init_path, "already_uploaded")
        # creation du dossier des fichiers déja uploades
        # if not os.path.isdir(self.already_uploaded):
        #     os.mkdir(self.already_uploaded)
        # creation du fichier de log
        curr_time = datetime.datetime.now().strftime('%d%m%Y-%H%M')
        self.currentTimeStr = curr_time
        self.log_filename = os.path.join(self.log_path, "importer_log_" + curr_time + ".log")
        f = open(self.log_filename, "a+")
        f.close()
        self.Subject = {}

    def __init__(self, bids_path):
    # def __init__(self, bids_path=None):
                    # requirement_name="requirements_new.json"):
        # print("Generic Uploader is starting")
        # print(bids_path)
        QtWidgets.QMainWindow.__init__(self)
        if isinstance(bids_path, str):
            if not os.path.exists(bids_path):
                raise TypeError('The path doesn"t exists.')
            self.init_path = bids_path
            self.bids_dataset = ins_bids_class.BidsDataset(bids_path)
        elif isinstance(bids_path, ins_bids_class.BidsDataset):
            self.init_path = bids_path.dirname
            self.bids_dataset = bids_path
        else:
            raise TypeError('The argument should be path or Bids Dataset')
        # ========= rajouter ici la creation de l'interface ========#
        # Lecture des requirements :
        # Pour initialiser le sujet avec les requirements ===============
        self.requirements = self.bids_dataset.requirements
        self.importation_path = os.path.normpath(os.path.join(self.init_path, ".."))
        self.bids_requirements_path = os.path.join(self.init_path, "code", "requirements.json")
        # b = ins_bids_class.Data2Import(requirements_fileloc=self.bids_requirements_path)
        # b.get_requirements(self.bids_requirements_path)
        # b.requirements['Requirements']['Subject'].keys()
        #self.requirements = b
        self.moda_needed = [moda for moda in self.requirements['Requirements'].keys()
                            if moda not in ["Subject"]]

        dstdesc = self.bids_dataset['DatasetDescJSON']
        protocole_name = dstdesc["Name"]
        self.secret_key = protocole_name
        # ========================================================================================================== #
        self.setupUi(self)
        self.progressBar.setVisible(False)
        self.progressBar.setValue(0)
        self.generic_uploader_version = str(1.03)
        self.setWindowTitle("BIDSUploader v" + self.generic_uploader_version)
        self.MenuList = self.ListMenuObject(self)
        self.listWidget.clear()
        self.current_working_path = self.init_path
        self.proto_name = protocole_name
        # variable init
        self.birth_date_str = None
        self.currentTimeStr = None
        self.fiche_patient = []
        self.electrode_brand = []
        self.seeg_run_number = {}
        self.Subject = {}
        self.SubjectPHRC = {}
        self.flag_validated = False
        self.protocole = []
        self.maplist = []
        self.addi_files = []
        self.already_uploaded = None
        self.ID = None
        self.Sex = None
        self.log_filename = None
        self.log_path = None
        self.last_path = None
        self.epinov_imagery_config_list = None
        self.spread_imagery_config_list = None
        self.protocoleAllowed = None
        self.temp_patient_path = None
        self.temp_patient_path = None
        self.old_maplist = None
        self.variable_initialization()
        # modif sam pour creation dynamique de l'interface
        # A refléchir pas easy
        self.interactions_callbacks()
        for import_button in self.import_button_list:
            import_button.setToolTip("Choose " + str(import_button.parent().title()) + " to import")
        QtWidgets.qApp.processEvents()

    def interactions_callbacks(self):
        self.radioButtonM.clicked.connect(self.standardize_info)
        self.radioButtonF.clicked.connect(self.standardize_info)
        self.anonymize_patient_checkBox.stateChanged.connect(self.display_id_textbox)
        # self.listElectrodeTypes.itemClicked.connect(self.electrode_type)
        # self.comboBoxImplantation.activated.connect(self.import_implantation_file)
        # boucler pour les boutons
        # self.import_neuroimagery.clicked.connect(self.import_neuroimagery_folder)
        # self.import_ieeg.clicked.connect(self.import_ieeg_files)
        # self.import_eeg.clicked.connect(self.import_eeg_files)
        # self.import_meg.clicked.connect(self.import_meg_files)
        '''self.groupBox_list[0].import_button.clicked.connect(lambda: self.import_files(0))
        self.groupBox_list[1].import_button.clicked.connect(lambda: self.import_files(1))
        self.groupBox_list[2].import_button.clicked.connect(lambda: self.import_files(2))'''
        for i in range(0, len(self.groupBox_list)):
            helper = lambda i: (lambda: self.import_files(i))
            self.groupBox_list[i].import_button.clicked.connect(helper(i))
        self.pushButtonReset.clicked.connect(self.reset_subject)
        self.pushButtonValidation.clicked.connect(self.validation)
        self.pushButtonFinish.clicked.connect(QtWidgets.QApplication.quit)
        self.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self.listWidget.connect(self.listWidget, QtCore.SIGNAL("customContextMenuRequested(QPoint)"),
        #          self.list_item_right_clicked)   QtCore.pyqtSignal(self.listWidget.customContextMenuRequested(QPoint))
        QPoint = QtGui.QCursor.pos()
        self.listWidget.itemDoubleClicked.connect(lambda: self.list_item_right_clicked(QPoint))
        # self.pushButtonResume.clicked.connect(self.resume_of_subject)

    def mapping_subject2list(self, sub, delete_flag=None, curr_keys_dict=None):
        if self.maplist:
            self.old_maplist = self.maplist
        self.maplist = []
        self.listWidget.clear()
        if not sub['sub']:
            return "Pas de sujet"
        # self.maplist.append({"Modality": "", "ID": sub["sub"], "Protocole : ": self.protocole1_name.toPlainText(),
        #                      "curr_state": "invalid"})
        # self.listWidget.addItem("ID : " + sub["sub"] + ", protocole : " + self.protocole1_name.toPlainText())
        # self.listWidget.item(0).setText("ID : " + sub["sub"] + ", protocole : " + self.protocole1_name.toPlainText())
        if self.old_maplist:
            curr_state = self.old_maplist[0]["curr_state"]
        else:
            curr_state = "invalid"
        self.maplist.append({"Modality": "", "ID": sub["sub"], "Protocole : ": self.proto_name,
                             "curr_state": curr_state})
        self.listWidget.addItem("ID : " + sub["sub"] + ", subject info : " + "Double_click => <Modify_identity> for modification")
        self.listWidget.item(0).setText("ID : " + sub["sub"] + ", subject info : " + "Double_click => <Modify_identity> for modification")
        if curr_state == "invalid":
            self.listWidget.item(0).setForeground(QtGui.QColor("red"))
            self.listWidget.item(0)
        elif curr_state == "forced":
            self.listWidget.item(0).setForeground(QtGui.QColor("orange"))
        elif curr_state == "valid":
            self.listWidget.item(0).setForeground(QtGui.QColor("green"))
        for key_class in sub.keys():
            if key_class in ins_bids_class.ModalityType.get_list_subclasses_names() or \
                    key_class in ins_bids_class.GlobalSidecars.get_list_subclasses_names():
                for mod in sub[key_class]:
                    idx_in_mod = sub[key_class].index(mod)
                    # garder les items non vides,
                    key_list = mod.keys()
                    non_empty_keys = [item for item in key_list if (mod[item] and item not in ["sub", "fileLoc"])]
                    description = ""
                    '''if sub[key_class].index(mod):
                        curr_state = self.old_maplist[sub[key_class].index(mod)]["curr_state"]
                    else:
                        curr_state = "invalid"'''
                    # code pour remplir la liste lisiblement :
                    for key in non_empty_keys:
                        description = description + mod[key] + "_"
                    if description:
                        description = description[0:-1]
                    curr_state = "invalid"
                    if self.old_maplist:
                        old_maplist_idx = []
                        for k in range(1, len(self.old_maplist)):
                            idx = str(self.old_maplist[k]["Modality"]) == mod.__class__.__name__
                            if idx:
                                old_maplist_idx.append(k)
                        if old_maplist_idx and idx_in_mod < len(old_maplist_idx):
                            curr_state = self.old_maplist[old_maplist_idx[idx_in_mod]]["curr_state"]
                    self.maplist.append({"Modality": mod.__class__.__name__, "Index": sub[key_class].index(mod),
                                         "curr_state": curr_state, "description": description})
                    # description = mod["modality"]
                    self.listWidget.addItem(mod.__class__.__name__ + ", " + description + " : " + mod["fileLoc"])
                    if curr_state == "invalid":
                        self.listWidget.item(self.listWidget.__len__()-1).setForeground(QtGui.QColor("red"))
                    elif curr_state == "forced":
                        self.listWidget.item(self.listWidget.__len__()-1).setForeground(QtGui.QColor("orange"))
                    elif curr_state == "valid":
                        self.listWidget.item(self.listWidget.__len__()-1).setForeground(QtGui.QColor("green"))
        if hasattr(self, "addi_files"):
            for files in self.addi_files:
                self.maplist.append({"Modality": "", "Addi_file_path": files, "curr_state": "invalid"})
                self.listWidget.addItem("Additional file : " + files)
        if hasattr(self, "fiche_patient"):
            for files in self.fiche_patient:
                self.maplist.append({"Modality": "", "fiche_patient": files, "curr_state": "invalid"})
                self.listWidget.addItem("Fiche patient : " + files)
        # RAJOUTER ICI la MAJ DES RUNS si suppressions dans pattient et dans le nom du fichier d'implantation.
        try:
            # remplir le log, trouver dabord les anciens import et remplacer
            curr_time = datetime.datetime.now().strftime('%d%m%Y-%H%M')
            f = open(self.log_filename, "r")
            lines = f.readlines()
            f.close()
            first_line_index = None
            first_line_index = [x for x in range(0, len(lines)) if str(self.listWidget.item(0).text()) in lines[x]]
            f.close()
            # ecriture des élements
            if not first_line_index:
                f = open(self.log_filename, "a+")
                f.write(curr_time + ", " + str(self.listWidget.item(0).text()) + "\n")
                f.close()
            elif first_line_index:
                # for i in range(0, self.listWidget.count()):
                f = open(self.log_filename, "w")
                for a in range(0, 2):
                    f.write(lines[a])
                f.close()
                f = open(self.log_filename, "a+")
                for i in range(first_line_index[0], self.listWidget.count()):
                    f.write(curr_time + ", " + str(self.listWidget.item(i).text()) + "\n")
                f.close()
        except:
            return

    def update_subject_class(self, sub, removed_item, global_moda):
        '''for global_moda in sub.keys():
            if global_moda == "IeegGlobalSidecars":
                scheme_type = ["Drawing", "Xray"]
                if sub[global_moda]:
                    for scheme in scheme_type:
                        name_to_change = [(item["acq"], sub[global_moda].index(item)) for item in sub[global_moda] if
                                          item["acq"].startswith(scheme)]
                        r = re.compile("([a-zA-Z]+)([0-9]+)")
                        for i in range(0, len(name_to_change)):
                            name = r.match(name_to_change[i][0])
                            new_name = name.group(1) + str(i + 1)
                            sub[global_moda][name_to_change[i][1]]["acq"] = new_name
                    return sub '''
        required_global_moda = self.requirements["Requirements"].keys()
        if global_moda in required_global_moda and global_moda not in ["IeegGlobalSidecars", "Subject"]:
            # start modif sam
            keys_dict = self.define_bids_needs_for_import([global_moda])
            key_list = keys_dict.keys()
            idx_of_interest = []
            for i in range(0, len(sub[global_moda])):
                for key in key_list:
                    if sub[global_moda][i][key] != removed_item[key]:
                        break
                    idx_of_interest.append(i)
            if not idx_of_interest:
                return sub
            idx_of_interest = list(set(idx_of_interest))    # pour unicite
            if sub[global_moda][idx_of_interest[0]]["run"] >= removed_item["run"]:  # corriger ici
                first_run = int(removed_item["run"])
            else:
                first_run = int(sub[global_moda][0]["run"])
            count = 0
            for j in idx_of_interest:
                sub[global_moda][j]["run"] = str(first_run + count)
                count = count + 1
            # task_existing = [task['task'] for task in sub[global_moda] if task['task']]
            # task_existing_unique = list(set(task_existing))  # pour unicite
            # type_existing = [task['acq'] for task in sub[global_moda] if task['acq']]
            # type_existing_unique = list(set(type_existing))  # pour unicite
            # for task in task_existing_unique:
            #     if task == "seizure":
            #         for typ in type_existing_unique:
            #             run_to_change = [(item["run"], sub[global_moda].index(item)) for item in sub[global_moda] if
            #                              item["task"] == task and item["acq"] == typ]
            #             for i in range(0, len(run_to_change)):
            #                 sub[global_moda][run_to_change[i][1]]["run"] = str(i + 1)
            #     else:
            #         run_to_change = [(item["run"], sub[key].index(item)) for item in sub[key] if
            #                          item["task"] == task]
            #         for i in range(0, len(run_to_change)):
            #             sub[global_moda][run_to_change[i][1]]["run"] = str(i + 1)
            return sub

    def list_item_right_clicked(self, qpos):
            QPoint = QtGui.QCursor.pos()
            if self.listWidget.currentItem() is None:
                return 0
            force_action = [action for action in self.MenuList.actions() if action == self.MenuList.force_action]
            check_and_force = [action for action in self.MenuList.actions() if
                               action == self.MenuList.check_and_force_action]
            modify_identity = [action for action in self.MenuList.actions() if
                               action == self.MenuList.modify_identity]
            delete_action = [action for action in self.MenuList.actions() if action == self.MenuList.delete_action]
            modify_info_action = [action for action in self.MenuList.actions() if action == self.MenuList.modify_info_action]
            self.MenuList.addAction(self.MenuList.force_action)
            self.MenuList.addAction(self.MenuList.modify_identity)
            self.MenuList.addAction(self.MenuList.check_and_force_action)
            self.MenuList.addAction(self.MenuList.delete_action)
            self.MenuList.addAction(self.MenuList.modify_info_action)
            if self.maplist[self.listWidget.currentRow()]["Modality"] == "":
                if "ID" in self.maplist[self.listWidget.currentRow()]:
                    self.MenuList.force_action.setVisible(False)
                    self.MenuList.check_and_force_action.setVisible(False)
                    self.MenuList.delete_action.setVisible(False)
                    self.MenuList.modify_identity.setVisible(True)
                    self.MenuList.modify_info_action.setVisible(True)
                else:
                    self.MenuList.force_action.setVisible(False)
                    self.MenuList.check_and_force_action.setVisible(False)
                    self.MenuList.delete_action.setVisible(True)
                    self.MenuList.modify_identity.setVisible(False)
            #elif self.maplist[self.listWidget.currentRow()]["Modality"] == "Anat" or \
            #        self.maplist[self.listWidget.currentRow()]["Modality"] == "Dwi":
            elif self.maplist[self.listWidget.currentRow()]["Modality"] not in ins_bids_class.GlobalSidecars.get_list_subclasses_names():
                tmp_modality = getattr(ins_bids_class, self.maplist[self.listWidget.currentRow()]["Modality"])()
                # if self.maplist[self.listWidget.currentRow()]["Modality"] in ["Anat", "Func", "Dwi"]:
                if isinstance(tmp_modality, ins_bids_class.Imaging):
                    if len(force_action) > 1:
                        return 0
                    sub = self.Subject
                    if sub[self.maplist[self.listWidget.currentRow()]["Modality"]][
                           self.maplist[self.listWidget.currentRow()]["Index"]]["modality"]:
                        self.MenuList.force_action.setVisible(False)
                        self.MenuList.check_and_force_action.setVisible(True)
                        self.MenuList.delete_action.setVisible(True)
                        self.MenuList.modify_identity.setVisible(False)
                        self.MenuList.modify_info_action.setVisible(False)
                    else:
                        self.MenuList.force_action.setVisible(True)
                        self.MenuList.check_and_force_action.setVisible(False)
                        self.MenuList.delete_action.setVisible(True)
                        self.MenuList.modify_identity.setVisible(False)
                        self.MenuList.modify_info_action.setVisible(False)
                # elif self.maplist[self.listWidget.currentRow()]["Modality"] == "Ieeg":
                elif isinstance(tmp_modality, ins_bids_class.Electrophy):
                    if len(force_action) > 1:
                        return 0
                    self.MenuList.force_action.setVisible(False)
                    self.MenuList.check_and_force_action.setVisible(True)
                    self.MenuList.delete_action.setVisible(True)
                    self.MenuList.modify_identity.setVisible(False)
                    self.MenuList.modify_info_action.setVisible(False)
            else:
                self.MenuList.force_action.setVisible(False)
                self.MenuList.check_and_force_action.setVisible(False)
                self.MenuList.delete_action.setVisible(True)
                self.MenuList.modify_identity.setVisible(False)
                self.MenuList.modify_info_action.setVisible(False)
            # self.MenuList.move(self.listWidget.mapToGlobal(qpos))
            self.MenuList.move(QPoint)
            self.MenuList.show()

    def restart_groupbox_identite(self):
        self.groupBox_identite.setEnabled(True)
        self.TextName.setEnabled(True)
        self.TextPrenom.setEnabled(True)
        self.dateEdit.setEnabled(True)
        self.radioButtonM.setAutoExclusive(False)
        self.radioButtonF.setAutoExclusive(False)
        self.radioButtonF.setChecked(False)
        self.radioButtonM.setChecked(False)
        self.radioButtonM.setAutoExclusive(True)
        self.radioButtonF.setAutoExclusive(True)
        self.radioButtonM.setEnabled(True)
        self.radioButtonF.setEnabled(True)

    def resume_of_subject(self):
        subject_file = os.path.join(self.already_uploaded, self.ID + ".txt")
        if os.path.exists(subject_file):
            resume = ResumeWidget(self)
            f = open(subject_file)
            lines = f.readlines()
            for line in lines:
                resume.list_widget.addItem(line)
            resume.exec_()

    def display_id_textbox(self):
        if self.anonymize_patient_checkBox.isChecked():
            self.id_textinfo.setVisible(False)
            self.id_textbox.setVisible(False)
        else:
            self.id_textbox.setVisible(True)
            self.id_textinfo.setVisible(True)

    def standardize_info(self):
        def calculate_age(born):
            born_datetime = born.toPyDate()
            today = datetime.date.today()
            age = today.year - born_datetime.year - (
                    (today.month, today.day) < (born_datetime.month, born_datetime.day))
            if age > 3:
                return str(age)
            else:
                if today.month >= born_datetime.month and today.day >= born_datetime.day:
                    month = today.month - born_datetime.month
                elif today.month >= born_datetime.month and today.day < born_datetime.day:
                    month = today.month - born_datetime.month - 1
                elif today.month < born_datetime.month and today.day >= born_datetime.day:
                    month = 12 - abs(today.month - born_datetime.month)
                elif today.month < born_datetime.month and today.day < born_datetime.day:
                    month = 12 - abs(today.month - born_datetime.month) - 1
                return str(age) + "," + str(month)

        def valide_mot(mot):
            nfkd_form = unicodedata.normalize('NFKD', mot)
            only_ascii = nfkd_form.encode('ASCII', 'ignore')  # supprime les accents et les diacritiques
            only_ascii_string = only_ascii.decode('ASCII').upper()  # reconvertit les bytes en string
            only_az = re.sub('[^A-Z]', '', only_ascii_string)  # supprime tout ce qui n'est pas [A-Z]
            return only_az

        def hash_object(obj):
            clef256 = hashlib.sha256(obj.encode())
            clef_digest = clef256.hexdigest()
            clef = clef_digest[0:12]
            return clef

        def valide_date(d):
            try:
                dd = datetime.datetime.strptime(d, '%d/%m/%Y')
            except:
                return False
            else:
                if (dd < datetime.datetime(year=1800, month=1, day=1)) or (dd > datetime.datetime.now()):
                    return False
                else:
                    return dd.strftime('%d%m%Y')

        def creation_id(last_name, first_name, birth_date_str_dd_mm_yyyy):
            if last_name and first_name and birth_date:
                last_name_validated = valide_mot(str(last_name))
                last_name_validated = str(last_name_validated)
                first_name_validated = valide_mot(str(first_name))
                first_name_validated = str(first_name_validated)
                birth_date_validated = valide_date(birth_date_str_dd_mm_yyyy)
                if birth_date_validated == False:
                    return 0
            if self.anonymize_patient_checkBox.isChecked():
                graine = last_name_validated + first_name_validated + birth_date_validated + self.secret_key
                hashed = hash_object(graine)
            else:
                alternative_id = str(self.id_textbox.toPlainText())
                if not alternative_id:
                    hashed = last_name_validated + first_name_validated
                else:
                    hashed = alternative_id
            return hashed, last_name_validated, first_name_validated

        def creation_sujet_bids(sub_required_keys, id, date, sex, protocole, *args):
            subj_age = calculate_age(date)
            sub_id_dict_list = [{'sub': id}, {'age': subj_age}, {'sex': sex}]
            if not args:
                current_subject = ins_bids_class.Subject()
                # current_subject.keys()
                # currentSubject.update({'sub': ID, 'age': Age, 'sex': sex, 'eCRF': protocole})
                # nouveau requierement sans eCRF
                # current_subject.update({'sub': id, 'age': subj_age, 'sex': sex})
                for id_dict in sub_id_dict_list:
                    if list(id_dict.keys())[0] in sub_required_keys:
                        current_subject.update({list(id_dict.keys())[0]: list(id_dict.values())[0]})
            else:
                # gérer ici si déjà existant
                for sub in args:
                    # sub.update({'sub': ID, 'age': Age, 'sex': sex, 'eCRF': protocole})
                    # sub.update({'sub': id, 'age': subj_age, 'sex': sex})
                    for id_dict in sub_id_dict_list:
                        if list(id_dict.keys())[0] in sub_required_keys:
                            sub.update({list(id_dict.keys())[0]: list(id_dict.values())[0]})
                    current_subject = sub
            return current_subject

        last_name = self.TextName.toPlainText()
        last_name = last_name
        first_name = self.TextPrenom.toPlainText()
        first_name = first_name
        birth_date = self.dateEdit.date()
        birth_date_str = birth_date.toString('dd/MM/yyyy')
        self.birth_date_str = str(birth_date_str)
        if self.radioButtonM.isChecked():
            sexe = "M"
        else:
            sexe = "F"
        try:
            self.ID, last_name_valid, first_name_valid = creation_id(last_name, first_name, self.birth_date_str)
        except :
            self.restart_groupbox_identite()
            return
        self.TextName.setPlainText(last_name_valid.lower())
        self.TextPrenom.setPlainText(first_name_valid.lower())
        if (self.radioButtonM.isChecked() or self.radioButtonF.isChecked()) and str(
                self.TextName.toPlainText()) != "" \
                and self.TextPrenom.toPlainText() != "":
        # if self.groupBox_implantation:
        # self.groupBox_implantation.setEnabled(True)
            for groupBox in self.groupBox_list:
                groupBox.setEnabled(True)
            # self.groupBox_neuroimagerie.setEnabled(True)
            # self.groupBox_seeg.setEnabled(True)
            self.groupBox_identite.setDisabled(True)
            # self.groupBox_protocole.setDisabled(True)
        else:
            self.restart_groupbox_identite()
            return
        if self.ID == 0:
            self.restart_groupbox_identite()
            return 0
        self.Sex = sexe
        # regarder ici si plusieurs protocoles ou pas
        if not self.Subject:
            sub_required_keys = self.requirements.required_keys
            self.Subject = creation_sujet_bids(sub_required_keys, self.ID, birth_date, sexe, str(self.proto_name))
        else:
            sub_required_keys = self.requirements.required_keys
            self.Subject = creation_sujet_bids(sub_required_keys, self.ID, birth_date, sexe, str(self.proto_name),
                                               self.Subject)
        suj = self.Subject
        # self.mapping_subject2list(suj)
        # Enabler les différents comboBox et afficher dans listWidget
        self.pushButtonValidation.setEnabled(True)
        self.pushButtonReset.setEnabled(True)
        # self.listElectrodeTypes.setEnabled(True)
        '''self.comboBoxImagerie.setEnabled(True)
        self.comboBoxSeeg.setEnabled(True)'''
        '''for import_button in self.import_button_list:
            import_button.setEnabled(True)'''
        # self.import_neuroimagery.setEnabled(True)
        # self.import_ieeg.setEnabled(True)
        # self.import_meg.setEnabled(True)
        # self.import_eeg.setEnabled(True)
        for groupBox in self.groupBox_list:
            groupBox.setEnabled(True)
            groupBox.import_button.setEnabled(True)
#        if self.groupBox_implantation:
#            self.groupBox_implantation.setEnabled(True)
        # self.groupBox_neuroimagerie.setEnabled(True)
        # self.groupBox_seeg.setEnabled(True)
        self.groupBox_validation.setEnabled(True)
        # self.pushButtonAddiFiles.setEnabled(True)
        # self.pushButtonFichePatient.setEnabled(True)
#         self.pushButtonResume.setEnabled(True)
        # patient_info_gui = patient_requirements_class.PatientRequirementsClass(self.requirements, sexe, suj["age"])
        patient_info_gui = patient_requirements_class.PatientRequirementsClass(self.requirements, suj)
        res = patient_info_gui.exec_()
        if res == 0:
            self.restart_groupbox_identite()
            return
        QtWidgets.qApp.processEvents()
        for i in range(0, len(patient_info_gui.requirements_object_list)):
            key = str(patient_info_gui.requirements_object_list[i].objectName())
            if type(patient_info_gui.requirements_object_list[i]) is QtWidgets.QLineEdit:
                self.Subject[key] = str(patient_info_gui.requirements_object_list[i].text())
            if type(patient_info_gui.requirements_object_list[i]) is QtWidgets.QComboBox:
                self.Subject[key] = str(patient_info_gui.requirements_object_list[i].currentText())
        # update of sub_list
        # a faire ???
        self.mapping_subject2list(self.Subject)

    def creation_repertoire_temporaire(self):
        def creation_rep_temp_and_json(id, current_date, protocole_name, seeg_run_number):
            # current_working_path = os.getcwd()
            current_working_path = self.importation_path
            temp_folder_path = os.path.join(current_working_path, "TempFolder4Upload")
            temp_patient_path = os.path.join(current_working_path, "TempFolder4Upload", id + "_" + protocole_name +
                                             "_" + current_date)
            seeg_run_number = seeg_run_number
            if os.path.isdir(temp_folder_path) is False:
                os.mkdir(temp_folder_path)
            if os.path.isdir(temp_patient_path) is False:
                os.mkdir(temp_patient_path)
                # mise a zero des runs
                seeg_run_number = {}
            return temp_patient_path, seeg_run_number

        birth_date = self.dateEdit.date()
        birth_date_str = str(birth_date.toString('dd/MM/yyyy'))
        current_date = self.currentTimeStr
        temp_patient_path, self.seeg_run_number = creation_rep_temp_and_json(self.ID, current_date, self.proto_name,
                                                                             self.seeg_run_number)
        return temp_patient_path

    def electrode_type(self):
        if len(self.listElectrodeTypes.selectedIndexes()) != 0 and (
                self.radioButtonM.isChecked() or self.radioButtonF.isChecked()):
            self.comboBoxImplantation.setEnabled(True)
        elif len(self.listElectrodeTypes.selectedIndexes()) == 0:
            self.comboBoxImplantation.setEnabled(False)

    def return_error_if_accent_in_name(self, file_list):
        try:
            for file in file_list:
                str(file)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "opening error", "Careful with accent. " + str(e))
            return 0

    def sidecar_parser(self, sujet, mode_type, task, acq_name, *acq):
        if acq:
            cur_nb = len(
                [line for line in sujet[mode_type] if (line[task].startswith(acq_name) and line["acq"] == acq[0])])
        else:
            cur_nb = len([line for line in sujet[mode_type] if line[task].startswith(acq_name)])
        return cur_nb

    def import_implantation_file(self):
        try:
            # gérer ici le type de fichier à
            current_item_index = self.comboBoxImplantation.currentIndex()
            files_type_allowed = "(*.png *.jpeg *.jpg *. *.bmp *.ppt *.pptx *.pdf)"
            if current_item_index == 0:
                return 0
            elif current_item_index == 1:
                files_type = "Drawing"
            elif current_item_index == 2:
                files_type = "Xray"
            elif current_item_index == 3:
                files_type = "Drawing"
            schema_filename = QtWidgets.QFileDialog.getOpenFileNames(None,
                                                                 "Select one or more implantation files",
                                                                 self.last_path,
                                                                 files_type_allowed)
            if not schema_filename:
                self.comboBoxImplantation.setCurrentIndex(0)
                return
            self.last_path = os.path.dirname(str(schema_filename[0]))
            nb_file = schema_filename.count()
            if nb_file == 0:
                self.comboBoxImplantation.setCurrentIndex(0)
                return
            file_list = [str(schema_filename[i]) for i in range(0, nb_file)]
            files_status = self.return_error_if_accent_in_name(file_list)
            if files_status == 0:
                self.comboBoxImplantation.setCurrentIndex(0)
                return
            # Sauvegarde dans le patient des différentes chemin des fichiers :
            for i in range(nb_file):
                cur_type_nb = self.sidecar_parser(self.Subject, "IeegGlobalSidecars", "acq", files_type)
                self.Subject["IeegGlobalSidecars"] = ins_bids_class.IeegGlobalSidecars(file_list[i])
                self.Subject['IeegGlobalSidecars'][-1].update({'sub': self.Subject['sub'], 'ses': '01',
                                                                      'acq': files_type + str(cur_type_nb + 1),
                                                                      'fileLoc': file_list[i]})
                suj = self.Subject
                self.mapping_subject2list(suj)
                QtWidgets.qApp.processEvents()
                # ecriture du fichier texte avec la compagnie
                for a in range(0, len(self.listElectrodeTypes.selectedItems())):
                    # self.electrode_brand.append(str(schema_filename[i]) + ", " + files_type + str(cur_type_nb + 1) +
                    #                             ", " + str(self.listElectrodeTypes.selectedItems()[a].text()))
                    self.electrode_brand.append(
                        str(schema_filename[i]) + ", " + str(self.listElectrodeTypes.selectedItems()[a].text()))
            # remise à 0 du combobox et remplissage de la liste
            self.comboBoxImplantation.setCurrentIndex(0)
        except Exception as e:
            qmesbox = QtWidgets.QMessageBox(self)
            qmesbox.setText("Erreur dans le nom du fichier. Ne pas mettre d'accent ou caractere special.")
            qmesbox.exec_()

    def define_bids_needs_for_import(self, modality_class_list):
        ses_list = []
        modality_list = []
        acq_list = []
        task_list = []
        run_list = []
        keys_dict = {}
        for modality_class in modality_class_list:
            # for nb in range(0, len(self.requirements.requirements['Requirements'][modality_class]['keys'])):
            for key in self.requirements['Requirements'][modality_class]['keys']:
                if key != "modality":
                    items = self.requirements['Requirements'][modality_class]['keys'][key]
                    keys_dict[key] = items
                # if key == 'ses':
                #     items = self.requirements.requirements['Requirements'][modality_class]['keys']['ses']
                #     if type(items) is list:
                #         ses_list = ses_list + items
                #     else:
                #         ses_list.append(items)
                # # if 'modality' in self.requirements.requirements['Requirements'][modality_class]['keys']:
                # if key == 'acq':
                #     items = self.requirements.requirements['Requirements'][modality_class]['keys']['acq']
                #     if type(items) is list:
                #         acq_list = acq_list + items
                #     else:
                #         acq_list.append(items)
                #     #acq_list = acq_list + self.requirements.requirements['Requirements'][modality_class]['keys']['acq']
                # if key == 'task':
                #     items = self.requirements.requirements['Requirements'][modality_class]['keys']['task']
                #     if type(items) is list:
                #         task_list = task_list + items
                #     else:
                #         task_list.append(items)
                #     #task_list = task_list + self.requirements.requirements['Requirements'][modality_class]['keys']['task']
                # if key == 'run':
                #     #run_list = run_list + self.requirements.requirements['Requirements'][modality_class]['keys']['run']
                #     items = self.requirements.requirements['Requirements'][modality_class]['keys']['run']
                #     if type(items) is list:
                #         run_list = run_list + items
                #     else:
                #         run_list.append(items)
                # if key == 'space':
                #     #run_list = run_list + self.requirements.requirements['Requirements'][modality_class]['keys']['run']
                #     items = self.requirements.requirements['Requirements'][modality_class]['keys']['space']
                #     if type(items) is list:
                #         space_list = space_list + items
                #     else:
                #         space_list.append(items)
            modality_list = modality_list + (eval("ins_bids_class." + modality_class + ".allowed_modalities"))
            keys_dict['modality'] = modality_list
        # ses_list = list(set(ses_list))
        ses_list.sort()
        # modality_list = list(set(modality_list))
        modality_list.sort()
        # acq_list = list(set(acq_list))
        acq_list.sort()
        # task_list = list(set(task_list))
        task_list.sort()
        # run_list = list(set(run_list))
        run_list.sort()
        # return ses_list, modality_list, acq_list, task_list, run_list
        return keys_dict

    def import_files(self, curr_groupbox_idx):
        modality = str(self.groupBox_list[curr_groupbox_idx].title())
#         [ses_list, modality_list, acq_list, task_list, run_list] = self.define_bids_needs_for_import([modality])
        keys_dict = self.define_bids_needs_for_import([modality])
        # modality_gui = ModalityGui(ses_list, modality_list, acq_list, task_list, run_list)
        modality_gui = ModalityGui(keys_dict)
        res = modality_gui.exec_()
        if res == 0:
            return 0
        try:
            sub, curr_keys_dict = import_by_modality(self, modality, modality_gui, self.Subject)
        except Exception as e:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText(str(e))
            msg.setWindowTitle("error")
            retval = msg.exec_()
            if retval:
                return 0
        if sub == 0:
            return 0
        self.Subject = sub
        # pour bien remplir la liste :
        self.mapping_subject2list(sub)
        QtWidgets.qApp.processEvents()


    def import_neuroimagery_folder(self):
        '''
        # gérer ici le type de dossier à importer
        current_item_index = self.comboBoxImagerie.currentIndex()
        if current_item_index == 0:
            return 0
        selected_type = self.comboBoxImagerie.itemText(current_item_index)
        modality = str(selected_type.split('_')[0])
        session = str(selected_type.split('_')[-1])
        if modality == "dwi":
            modalite_class = "Dwi"
        else:
            modalite_class = "Anat"
        imagery_folder = QtGui.QFileDialog.getExistingDirectory(None, "Choisir le dossier d'imagerie",
                                                                self.last_path)
        self.last_path = imagery_folder
        if imagery_folder == "":
            self.comboBoxImagerie.setCurrentIndex(0)
            return 0
        folder_list = [str(imagery_folder)]
        files_status = self.return_error_if_accent_in_name(folder_list)
        if files_status == 0:
            self.comboBoxImplantation.setCurrentIndex(0)
            return
        '''
        keys_to_avoid = ["keys", "IeegGlobalSidecars", "Ieeg", "Meg", "Eeg", "Subject"]
        modality_class_list = [key for key in self.requirements['Requirements'].keys()
                               if key not in keys_to_avoid]
        [ses_list, modality_list, acq_list, task_list, run_list] = \
            self.define_bids_needs_for_import(modality_class_list)

        neuroimagery_gui = ModalityGui(ses_list, modality_list, acq_list, task_list, run_list)
        res = neuroimagery_gui.exec_()
        if res == 0:
            return 0
        imagery_folder = QtWidgets.QFileDialog.getExistingDirectory(None, "Choisir le dossier d'imagerie",
                                                                self.last_path)
        # Sauvegarde dans le patient des différentes chemin des fichiers :
        modality_idx = [idx for idx in range(0, len(neuroimagery_gui.combobox_list))
                        if neuroimagery_gui.combobox_list[idx].objectName() == "modality"]
        if (modality_idx.__len__() == 1) and modality_idx:
            modality = str(neuroimagery_gui.combobox_list[modality_idx[0]].currentText())
            if modality == "Dwi":
                modalite_class = "Dwi"
            else:
                modalite_class = "Anat"
        else:
            modality = ""
        session_idx = [idx for idx in range(0, len(neuroimagery_gui.combobox_list))
                       if neuroimagery_gui.combobox_list[idx].objectName() == "session"]
        if session_idx:
            session = str(neuroimagery_gui.combobox_list[session_idx[0]].currentText())
        else:
            session = ""
        acq_idx = [idx for idx in range(0, len(neuroimagery_gui.combobox_list))
                   if neuroimagery_gui.combobox_list[idx].objectName() == "acq"]
        if acq_idx:
            acq = str(neuroimagery_gui.combobox_list[acq_idx[0]].objectName())
        else:
            acq = ''
        task_idx = [idx for idx in range(0, len(neuroimagery_gui.combobox_list))
                   if neuroimagery_gui.combobox_list[idx].objectName() == "task"]
        if task_idx:
            task = str(neuroimagery_gui.combobox_list[task_idx[0]].objectName())
        else:
            task = ''
        # !!! IL FAUDRAIT LIRE ICI CE QUIL Y A DANS LE FICHIER
        cur_type_nb = self.sidecar_parser(self.Subject, modalite_class, "modality", modality)
        self.Subject[modalite_class] = eval("ins_bids_class." + modalite_class + "()")
        self.Subject[modalite_class][-1].update({'sub': self.Subject['sub'], 'ses': session, 'acq': acq,
                                                 'modality': modality, 'fileLoc': str(imagery_folder)})
        suj = self.Subject
        self.mapping_subject2list(suj)
        QtWidgets.qApp.processEvents()

    def import_ieeg_files(self):
        key = 'Ieeg'
        modality_class_list = [key]
        [ses_list, modality_list, acq_list, task_list, run_list] = \
            self.define_bids_needs_for_import(modality_class_list)
        ieeg_gui = ModalityGui(ses_list, modality_list, acq_list, task_list, run_list)
        res = ieeg_gui.exec_()
        if res == 0:
            return 0
        files_type_allowed = "(*.trc *.eeg *.vhdr *.vmrk *.dat)"
        seeg_filename = QtWidgets.QFileDialog.getOpenFileNames(None, "Select one or more seeg files",
                                                           self.last_path, files_type_allowed)
        if not seeg_filename:
            return
        self.last_path = os.path.dirname(str(seeg_filename[0]))
        nb_file = seeg_filename.count()
        if nb_file == 0:
            return
        file_list = [str(seeg_filename[i]) for i in range(0, nb_file)]
        files_status = self.return_error_if_accent_in_name(file_list)
        if files_status == 0:
            return
        # Sauvegarde dans le patient des différentes chemin des fichiers :
        modality_idx = [idx for idx in range(0, len(ieeg_gui.combobox_list))
                        if ieeg_gui.combobox_list[idx].objectName() == "modality"]
        if (modality_idx.__len__() == 1) and modality_idx:
            modality = str(ieeg_gui.combobox_list[modality_idx[0]].currentText())
            modalite_class = modality_class_list[0]
        else:
            modality = ""
        session_idx = [idx for idx in range(0, len(ieeg_gui.combobox_list))
                       if ieeg_gui.combobox_list[idx].objectName() == "session"]
        if session_idx:
            session = str(ieeg_gui.combobox_list[session_idx[0]].currentText())
        else:
            session = ""
        acq_idx = [idx for idx in range(0, len(ieeg_gui.combobox_list))
                   if ieeg_gui.combobox_list[idx].objectName() == "acq"]
        if acq_idx:
            acq = str(ieeg_gui.combobox_list[acq_idx[0]].currentText())
        else:
            acq = ''
        task_idx = [idx for idx in range(0, len(ieeg_gui.combobox_list))
                    if ieeg_gui.combobox_list[idx].objectName() == "task"]
        if task_idx:
            task = str(ieeg_gui.combobox_list[task_idx[0]].currentText())
        else:
            task = ''
        # Sauvegarde dans le patient des différentes chemin des fichiers :
        for i in range(nb_file):
            filename, file_ext = os.path.splitext(file_list[i])
            if file_ext == ".dat" or file_ext == ".vmrk" or (
                    file_ext == ".eeg" and os.path.isfile(filename + '.vhdr')):
                continue
            ## DEMANDER ICI LE RUN !!! ==================================================================
            # !!! IL FAUDRAIT LIRE ICI EC QUIL Y A DANS LE FICHIER
            cur_type_nb = self.sidecar_parser(self.Subject, modalite_class, "modality", modality)
            self.Subject[modalite_class] = eval("ins_bids_class." + modalite_class + "()")
            self.Subject[modalite_class][-1].update({'sub': self.Subject['sub'], 'ses': session, 'acq': acq,
                                                 'modality': modality, 'task': task, 'fileLoc': file_list[i]})
            suj = self.Subject
            self.mapping_subject2list(suj)
            QtWidgets.qApp.processEvents()

    def import_meg_files(self):
        print("toto")

    def import_eeg_files(self):
        print("toto")

    def find_position_on_screen(self, widget):
        ancetre = widget
        widget_position = QtCore.QPoint()
        while ancetre != self:
            widget_position = widget_position + ancetre.pos()
            ancetre = ancetre.parent()
        pos_on_screen = widget_position + self.pos()
        return pos_on_screen

    def import_seeg_file(self):
        # gérer ici le type de fichier à importer
        current_item_index = self.comboBoxSeeg.currentIndex()
        files_type_allowed = "(*.trc *.eeg *.vhdr *.vmrk *.dat)"
        if current_item_index == 0:
            return 0
        # elif current_item_index == 1:
        #     files_type = "seizure"
        #     acquisition = "type"
        #     widget_pos_on_screen = self.find_position_on_screen(self.comboBoxSeeg)
        #     seeg_type_dialog = DialogSeizureType(widget_pos_on_screen)
        #     seeg_type_dialog_status = seeg_type_dialog.exec_()
        #     if seeg_type_dialog_status == 0:
        #         return 0
        #     seizure_type = seeg_type_dialog.seizure_type
        # elif current_item_index == 2:
        #     files_type = "rest"
        #     seizure_type = ""
        #     acquisition = ""
        # elif current_item_index == 3:
        #     files_type = "sleep"
        #     seizure_type = ""
        #     acquisition = ""
        else:
            files_type = str(self.comboBoxSeeg.currentText()).split('_')
            files_type = files_type[1]
            if files_type == "seizure":
                acquisition = "type"
                widget_pos_on_screen = self.find_position_on_screen(self.comboBoxSeeg)
                seeg_type_dialog = DialogSeizureType(widget_pos_on_screen)
                seeg_type_dialog_status = seeg_type_dialog.exec_()
                if seeg_type_dialog_status == 0:
                    return 0
                seizure_type = seeg_type_dialog.seizure_type
            else:
                seizure_type = ""
                acquisition = ""
        seeg_filename = QtWidgets.QFileDialog.getOpenFileNames(None,
                                                           "Selectionner un ou plusieurs fichiers SEEG",
                                                           self.last_path,
                                                           files_type_allowed)
        if not seeg_filename:
            self.comboBoxSeeg.setCurrentIndex(0)
            return
        self.last_path = os.path.dirname(str(seeg_filename[0]))
        nb_file = seeg_filename.count()
        if nb_file == 0:
            self.comboBoxSeeg.setCurrentIndex(0)
            return
        file_list = [str(seeg_filename[i]) for i in range(0, nb_file)]
        files_status = self.return_error_if_accent_in_name(file_list)
        if files_status == 0:
            self.comboBoxSeeg.setCurrentIndex(0)
            return
        # Sauvegarde dans le patient des différentes chemin des fichiers :
        acq = acquisition + str(seizure_type)
        for i in range(nb_file):
            filename, file_ext = os.path.splitext(file_list[i])
            if file_ext == ".dat" or file_ext == ".vmrk" or (file_ext == ".eeg" and os.path.isfile(filename+'.vhdr')):
                continue
            cur_type_nb = self.sidecar_parser(self.Subject, "Ieeg", "task", files_type, acq)
            self.Subject["Ieeg"] = ins_bids_class.Ieeg()
            self.Subject['Ieeg'][-1].update({'sub': self.Subject['sub'], 'ses': '01',
                                                    'acq': acq, 'task': files_type,
                                                    'fileLoc': file_list[i], 'run': str(cur_type_nb + 1)})
            suj = self.Subject
            self.mapping_subject2list(suj)
            QtWidgets.qApp.processEvents()
        # remise à 0 du combobox et remplissage de la liste
        self.comboBoxSeeg.setCurrentIndex(0)

    def import_addi_files(self):
        addi_files = QtWidgets.QFileDialog.getOpenFileNames(None, "Selectionner le/les fichiers additionels",
                                                        self.last_path)
        if not addi_files:
            return 0
        self.last_path = os.path.dirname(str(addi_files[0]))
        suj = self.Subject
        for files in addi_files:
            self.addi_files.append(str(files))
        self.mapping_subject2list(suj)
        QtWidgets.qApp.processEvents()

    def import_fiche_patient(self):
        fiche_patient_files = QtWidgets.QFileDialog.getOpenFileNames(None, "Selectionner la/les fiche patient",
                                                                 self.last_path)
        if not fiche_patient_files:
            return 0
        self.last_path = os.path.dirname(str(fiche_patient_files[0]))
        suj = self.Subject
        for files in fiche_patient_files:
            self.fiche_patient.append(str(files))
        self.mapping_subject2list(suj)
        QtWidgets.qApp.processEvents()

    def raz_gui(self):
        self.TextPrenom.setPlainText("")
        self.TextName.setPlainText("")
        # self.groupBox_identite.setDisabled(True)
        self.restart_groupbox_identite()
        # self.pushButtonAddiFiles.setDisabled(True)
        # self.pushButtonFichePatient.setDisabled(True)
        # self.protocole1_name.setDisabled(True)
        # self.protocole1_name.setPlainText("")
        # self.groupBox_protocole.setEnabled(True)
        ##Aude modif
        #self.groupBox_validation.setDisabled(True)
        self.pushButtonValidation.setDisabled(True)
        self.pushButtonReset.setDisabled(True)
        '''if self.groupBox_implantation:
            self.groupBox_implantation.setDisabled(True)
        self.groupBox_neuroimagerie.setDisabled(True)
        self.groupBox_seeg.setDisabled(True)'''
        for groupBox in self.groupBox_list:
            groupBox.setDisabled(True)
#         self.pushButtonResume.setDisabled(True)
        self.listWidget.clear()
        self.variable_initialization()

    def reset_subject(self):
        carefulf_dialog = QtWidgets.QMessageBox.question(self, "Reset?",
                                                     "Do you really want to reset information?",
                                                     QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        if carefulf_dialog == QtWidgets.QMessageBox.Cancel:
            return
        else:
            self.raz_gui()

    def recursively_read_imagery_folder(self, path):
        for file in os.listdir(path):
            try:
                [nom, prenom, date] = read_headers(os.path.join(path, file))
                return nom, prenom, date
            except:
                if os.path.isdir(os.path.join(path, file)):
                    new_path = os.path.join(path, file)
                    [nom, prenom, date] = self.recursively_read_imagery_folder(new_path)
                    if nom and prenom and date:
                        return [nom, prenom, date]
        nom = prenom = date = 0
        return nom, prenom, date

    def valid_patient_with_requirements(self, suj):
        required_items = self.requirements["Requirements"]["Subject"]["required_keys"]
        missing_keys = ""
        valid_boolean = 1
        for item in required_items:
            if not suj[item] or suj[item] == "n/a":
                # missing_keys.append(item)
                missing_keys = missing_keys + item + ", "
                valid_boolean = 0
        missing_keys = missing_keys[0:-2]
        return valid_boolean, missing_keys

    def validation(self):
        def validation_information(suj, map_line, action_number):
            valid_boolean, missing_keys = self.valid_patient_with_requirements(suj)
            if suj["sub"] == "":
                self.listWidget.item(action_number).setForeground(QtGui.QColor("red"))
                self.listWidget.item(action_number).setText(
                    self.listWidget.item(action_number).text() + " => no existing subject")
                self.maplist[action_number]["curr_state"] = "invalid"
            elif valid_boolean == 0:
                self.listWidget.item(action_number).setForeground(QtGui.QColor("red"))
                self.listWidget.item(action_number).setText(
                    self.listWidget.item(action_number).text() + " => missing keys : " + missing_keys)
                self.maplist[action_number]["curr_state"] = "invalid"
            else:
                self.listWidget.item(action_number).setForeground(QtGui.QColor("green"))
                self.maplist[action_number]["curr_state"] = "valid"
            return self.maplist[action_number]["curr_state"]

        def validation_implantation(suj, map_line, action_number):
            self.listWidget.item(action_number).setForeground(QtGui.QColor("green"))
            self.maplist[action_number]["curr_state"] = "valid"
            return self.maplist[action_number]["curr_state"]

        def validation_neuroimagerie(suj, map_line, action_number, key):
            if str(self.maplist[action_number]["curr_state"]) not in ["valid", "forced"]:
                data_path = os.path.join(self.current_working_path, suj[key][map_line["Index"]]["fileLoc"])
                list_files = os.listdir(data_path)
                if suj[key][map_line["Index"]]["modality"]:
                    [nom, prenom, date] = self.recursively_read_imagery_folder(data_path)
                    if nom == prenom == date == 0:
                        return 0
                    birthdate = self.birth_date_str[0:2] + self.birth_date_str[3:5] + self.birth_date_str[6:10]
                    if nom.lower().rstrip('\x00') != str(self.TextName.toPlainText()).lower() or prenom.lower().rstrip(
                            '\x00') != str(self.TextPrenom.toPlainText()).lower() or date.lower() != birthdate:
                        self.listWidget.item(action_number).setForeground(QtGui.QColor("red"))
                        self.listWidget.item(action_number).setText(self.listWidget.item(
                            action_number).text() + " => given identity and informations in files are different !")
                        self.maplist[action_number]["curr_state"] = "invalid"
                    else:
                        self.listWidget.item(action_number).setForeground(QtGui.QColor("green"))
                        self.maplist[action_number]["curr_state"] = "valid"
                    return self.maplist[action_number]["curr_state"]
                else:
                    self.listWidget.item(action_number).setForeground(QtGui.QColor("green"))
                    self.maplist[action_number]["curr_state"] = "valid"
            return self.maplist[action_number]["curr_state"]

        def validation_seeg(suj, map_line, action_number):
            if str(self.maplist[action_number]["curr_state"]) not in ["valid", "forced"]:
                data_path = os.path.join(self.current_working_path, suj["Ieeg"][map_line["Index"]]["fileLoc"])
                try:
                    [nom, prenom, date] = read_headers(os.path.join(data_path, data_path))
                except Exception as e:
                    # QtWidgets.QMessageBox.critical(self, "Erreur de lecture", "Impossible de lire les fichiers seeg")
                    return 0, e
                if nom == prenom == date == 0:
                    return 0, ""
                birthdate = self.birth_date_str[0:2] + self.birth_date_str[3:5] + self.birth_date_str[6:10]
                if nom.lower().rstrip('\x00') != str(self.TextName.toPlainText()).lower() or prenom.lower().rstrip(
                                      '\x00') \
                                      != str(self.TextPrenom.toPlainText()).lower() or date.lower() != birthdate:
                    self.listWidget.item(action_number).setForeground(QtGui.QColor("red"))
                    self.listWidget.item(action_number).setText(self.listWidget.item(
                        action_number).text() + " => given identity and informations in files are different !")
                    self.maplist[action_number]["curr_state"] = "invalid"
                else:
                    self.listWidget.item(action_number).setForeground(QtGui.QColor("green"))
                    self.maplist[action_number]["curr_state"] = "valid"
            return self.maplist[action_number]["curr_state"], ""

        def validation_addi_files(suj, map_line, action_number):
            self.listWidget.item(action_number).setForeground(QtGui.QColor("green"))
            self.maplist[action_number]["curr_state"] = "valid"
            return self.maplist[action_number]["curr_state"]

        def validation_fiche_patient_files(suj, map_line, action_number):
            self.listWidget.item(action_number).setForeground(QtGui.QColor("green"))
            self.maplist[action_number]["curr_state"] = "valid"
            return self.maplist[action_number]["curr_state"]

        # parcourir la liste des logs et effectuer les actions
        total_actions = self.listWidget.count()
        if total_actions == 0 or total_actions != self.maplist.__len__():
            return
        for action in range(0, total_actions):
            line = self.maplist[action]
            '''if line["curr_state"] != "invalid":
                continue'''
            '''if line["curr_state"] == "valid" or line["curr_state"] == "forced":
                continue'''
            if line["Modality"] == "" and "ID" in line:
                cur_state = validation_information(self.Subject, line, action)
            elif line["Modality"] == "IeegGlobalSidecars":
                cur_state = validation_implantation(self.Subject, line, action)
            # elif line["Modality"] == "Anat" or line["Modality"] == "Dwi":
            # elif line["Modality"] in ["Anat", "Func", "Dwi"]:
            #    cur_state = validation_neuroimagerie(self.Subject, line, action, line["Modality"])
            # elif line["Modality"] == "Ieeg":
            #     cur_state = validation_seeg(self.Subject, line, action)
            elif line["Modality"] not in ins_bids_class.GlobalSidecars.get_list_subclasses_names():
                tmp_modality = getattr(ins_bids_class, line["Modality"])()
                if isinstance(tmp_modality, ins_bids_class.Imaging):
                    cur_state = validation_neuroimagerie(self.Subject, line, action, line["Modality"])
                elif isinstance(tmp_modality, ins_bids_class.Electrophy):
                    if tmp_modality.classname() in ["Ieeg", "Eeg"]:
                        cur_state, error = validation_seeg(self.Subject, line, action)
                    elif tmp_modality.classname() == "Meg":
                        "reflechir a valider la meg ou neurophy de facon generale"
            # elif line["Modality"] == "" and "Addi_file_path" in line:
            #     cur_state = validation_addi_files(self.Subject, line, action)
            # elif line["Modality"] == "" and "fiche_patient" in line:
            #     cur_state = validation_fiche_patient_files(self.Subject, line, action)
            if cur_state == 0:
                qmesbox = QtWidgets.QMessageBox(self)
                qmesbox.setText("problem in validating files " + line["Modality"] + str(error))
                qmesbox.exec_()
                return 0
            # ecriture dans le log des validation
            f = open(self.log_filename, "a+")
            f.write(str(self.listWidget.item(action).text()) + " =====>" + cur_state + "\n")
            f.close()
        f = open(self.log_filename, "a+")
        f.write("\n")
        f.close()
        self.flag_validated, self.current_state = self.check_total_validation()
        if self.flag_validated:
            upload_dialog = QtWidgets.QMessageBox.question(self, "Bids import ?",
                                                       "Do you want to copy and format to bids?",
                                                       QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            if upload_dialog == QtWidgets.QMessageBox.Cancel:
                return
            else:
                self.copy_and_upload()
        else:
            QtWidgets.QMessageBox.information(self, "Incomplete Validation", "Please check your data", QtWidgets.QMessageBox.Ok)

    def check_total_validation(self):
        valid_flag = True
        current_state = "valid"
        for a in self.maplist:
            if a["curr_state"] == "invalid":
                valid_flag = False
                current_state = "invalid"
                return valid_flag, current_state
            if a["curr_state"] == "forced":
                current_state = "forced"
        return valid_flag, current_state

    def copy_and_upload(self):
        def dest_path_fonction(sujet, item, src_path, temp_path):
            filename, file_extension = os.path.splitext(src_path)
            filename = os.path.basename(filename)
            classe = item["Modality"]
            idx = item["Index"]
            # if classe in ["Anat", "Dwi", "Func"]:
            if classe not in ins_bids_class.GlobalSidecars.get_list_subclasses_names():
                tmp_modality = getattr(ins_bids_class, classe)()
                if isinstance(tmp_modality, ins_bids_class.Imaging) or os.path.isdir(src_path):
                    foldername_list = [sujet[classe][idx][notempty] for notempty in sujet[classe][idx].keys()
                                       if (sujet[classe][idx][notempty] and notempty != "fileLoc" and notempty != "sub")]
                    foldername = ""
                    for item in foldername_list:
                        foldername = foldername + item + "_"
                    if foldername:
                        foldername = foldername[0:-1]
                    # if modality:  % pour nouvel uploader 4 boutons
                    # if acq:
                    #     ## faire attention si 2 sélections de pas avoir le meme nom
                    #     if os.path.isdir(os.path.join(temp_path, modality + acq)) is False:
                    #         dest_name = modality + acq
                    #         os.mkdir(os.path.join(temp_path, dest_name))
                    #     else :
                    #         cur_nb = len([line for line in os.listdir(temp_path) if line.startswith(acq)])
                    #         dest_name = modality + acq + str(cur_nb)
                    #         os.mkdir(os.path.join(temp_path, dest_name))
                    #     dest_filename = os.path.join(temp_path, dest_name)
                    #     dest4data2import = dest_name
                    # else:
                    #     os.mkdir(os.path.join(temp_path, filename))
                    #     dest_filename = os.path.join(temp_path, filename)
                    #     dest4data2import = filename
                    dest_filename = os.path.join(temp_path, foldername)
                    dest4data2import = foldername
                    if os.path.isdir(dest_filename) is False:
                        os.mkdir(dest_filename)
                #elif classe == "Dwi":
                #    acq = sujet[item["Modality"]][item["Index"]]["acq"]
                #    if os.path.isdir(os.path.join(temp_path, acq)) is False:
                #        os.mkdir(os.path.join(temp_path, acq))
                #    dest_filename = os.path.join(temp_path, acq)
                #    dest4data2import = acq
                # elif classe in ["Ieeg", "Meg", "Eeg"]:
                elif isinstance(tmp_modality, ins_bids_class.Electrophy):
                    dest_filename = os.path.join(temp_path, filename + file_extension)
                    dest4data2import = filename + file_extension
                # elif classe == "IeegGlobalSidecars":
            else:
                # if isinstance(classe, ins_bids_class.GlobalSidecars):
                # acq = sujet[item["Modality"]][item["Index"]]["acq"]
                # new_filename = acq
                new_filename = filename
                dest_filename = os.path.join(temp_path, new_filename + file_extension)
                dest4data2import = new_filename + file_extension
            # else:
            #     if "Addi_file_path" in item:
            #         # dest_filename = os.path.join(temp_path, filename + file_extension)
            #         cur_nb = len([line for line in os.listdir(temp_path) if line.startswith("additional_file")])
            #         dest_name = "additional_file" + str(cur_nb)
            #         dest_filename = os.path.join(temp_path, dest_name + file_extension)
            #         dest4data2import = filename + file_extension
            #     elif "fiche_patient" in item:
            #         cur_nb = len([line for line in os.listdir(temp_path) if line.startswith("fiche_patient")])
            #         dest_name = "fiche_patient" + str(cur_nb)
            #         dest_filename = os.path.join(temp_path, dest_name + file_extension)
            #         dest4data2import = dest_name + file_extension
            #     # dest_filename = os.path.join(temp_path, filename + file_extension)
            #     # dest4data2import = filename + file_extension
            return dest_filename, dest4data2import

        def anonymize(classe, dest_filename, sub_id):
            filename, file_extension = os.path.splitext(src_path)
            if classe == "Ieeg":
                try:
                    file_extension = file_extension.lower()
                    if file_extension == ".trc":
                        anonymize_micromed(dest_filename)
                except Exception as e:
                    QtWidgets.qApp.processEvents()
                    qmesbox = QtWidgets.QMessageBox(self)
                    qmesbox.setText("anonymization failed. " + str(e))
                    qmesbox.exec_()
                    return
            elif classe in ["Anat", "Dwi", "Func"]:
                try:
                    anonymize_dcm(dest_filename, dest_filename, sub_id, sub_id, True, False)
                except:
                    # suppression pour ne garder que les Dicoms
                    os.remove(dest_filename)
                    return

        def local_copy_and_anonymization(file_class, src, dest, sub_id, *modality):
            if os.path.isdir(src):
                for files in os.listdir(src):
                    try:
                        if os.path.isdir(os.path.join(src, files)):
                            new_dest = os.path.join(dest, files)
                            new_src = os.path.join(src, files)
                            os.mkdir(new_dest)
                            local_copy_and_anonymization(file_class, new_src, new_dest, sub_id, modality[0])
                            if not os.listdir(new_dest):
                                shutil.rmtree(new_dest)
                        else:

                            shutil.copy2(os.path.join(src, files), dest)
                            # try:
                            if self.anonymize_patient_checkBox.isChecked():
                                anonymize(file_class, os.path.join(dest, files), sub_id)
                            # except:   # pour ne pas anonymiser si pas fichiers dicom
                            #     continue
                    except Exception as e:
                        w = QtWidgets.QWidget(self)
                        QtWidgets.QMessageBox.critical(w, "Erreur", "Incorrect File format. " + str(e))
                        return
            else:
                shutil.copy2(src, dest)
                if self.anonymize_patient_checkBox.isChecked():
                    if modality[0]:
                        anonymize(file_class, os.path.join(dest), sub_id)

        counter = 0
        self.disable_gui()
        self.progressBar.setVisible(True)
        self.labelProgressbar.setText("local copy and anonymisation in progress")
        QtWidgets.qApp.processEvents()
        # test si il y a des data à envoyer et ne rien faire sinon
        if self.maplist.__len__() == 1:
            self.progressBar.setValue(0)
            self.progressBar.setVisible(False)
            self.labelProgressbar.setVisible(False)
            self.enable_gui()
            self.raz_gui()
            QtWidgets.qApp.processEvents()
            qmesbox = QtWidgets.QMessageBox(self)
            qmesbox.setText("no file to send")
            qmesbox.exec_()
            return
        temp_patient_path = self.creation_repertoire_temporaire()
        self.temp_patient_path = temp_patient_path
        for item in self.maplist:
            if counter == 0:
                counter += 1
                continue
            classe = item["Modality"]
            if classe:
                if os.path.exists(self.Subject[item["Modality"]][item["Index"]]["fileLoc"]):
                    src_path = self.Subject[item["Modality"]][item["Index"]]["fileLoc"]
                else:
                    filepath = self.Subject[item["Modality"]][item["Index"]]["fileLoc"]
                    src_path = os.path.join(self.init_path, filepath)
            else:
                if "Addi_file_path" in item:
                    src_path = item["Addi_file_path"]
                elif "fiche_patient" in item:
                    src_path = item["fiche_patient"]
            temp_folder = temp_patient_path
            dest_path, dest4data2import = dest_path_fonction(self.Subject, item, src_path, temp_folder)
            if classe:
                filename, file_ext = os.path.splitext(src_path)
                if file_ext == '.vhdr' and (os.path.isfile(filename + '.dat') or os.path.isfile(filename + '.eeg')) \
                        and os.path.isfile(filename + '.vmrk'):
                    local_copy_and_anonymization(classe, src_path, dest_path, self.Subject["sub"],
                                                 self.Subject[classe][item["Index"]]["modality"])
                    src = filename + '.vmrk'
                    vmrk_name = os.path.split(filename)[1] + '.vmrk'
                    dest_path_vmrk = os.path.split(dest_path)
                    dest_path_vmrk = os.path.join(dest_path_vmrk[0], vmrk_name)
                    local_copy_and_anonymization(classe, src, dest_path_vmrk, self.Subject["sub"],
                                                 self.Subject[classe][item["Index"]]["modality"])
                    if os.path.isfile(filename + '.dat'):
                        dat_name = os.path.split(filename)[1] + '.dat'
                        src = filename + '.dat'
                    elif os.path.isfile(filename + '.eeg'):
                        dat_name = os.path.split(filename)[1] + '.eeg'
                        src = filename + '.eeg'
                    dest_path_dat = os.path.split(dest_path)
                    dest_path_dat = os.path.join(dest_path_dat[0], dat_name)
                    local_copy_and_anonymization(classe, src, dest_path_dat, self.Subject["sub"],
                                                 self.Subject[classe][item["Index"]]["modality"])
                else:
                    local_copy_and_anonymization(classe, src_path, dest_path, self.Subject["sub"],
                                                 self.Subject[classe][item["Index"]]["modality"])
                ins_bids_class.Data2Import._assign_import_dir(temp_patient_path)
                self.Subject[item["Modality"]][item["Index"]]["fileLoc"] = dest4data2import
            else:
                local_copy_and_anonymization(classe, src_path, dest_path, self.Subject["sub"], "")
            counter += 1
            self.progressBar.setValue(round(counter * 100 / self.maplist.__len__()))
            QtWidgets.qApp.processEvents()
        # creation du data2import
        ins_bids_class.Data2Import._assign_import_dir(temp_patient_path)
        data_to_import = ins_bids_class.Data2Import(temp_patient_path)
        data_to_import['DatasetDescJSON'] = ins_bids_class.DatasetDescJSON()
        data_to_import['DatasetDescJSON'].update({'Name': self.proto_name, 'BIDSVersion': '1.0.1'})
        data_to_import['Subject'] = self.Subject
        data_to_import.save_as_json()
        # # creation du fichier electrode_company
        # company_list = []
        # for line in self.electrode_brand:
        #     company = line.split(", ")[1]
        #     company_list.append(company)
        #     company_list = list(set(company_list))
        # if company_list:
        #     f = open(os.path.join(temp_patient_path, "electrode_company.txt"), "w+")
        #     for a in range(0, len(company_list)):
        #         f.write(company_list[a] + "\n")
        #     f.close()
        # AJOUTER ICI LE TRANSFERT PAR SFTP

        # ====================================================
        # rajouter ici la RAZ GUI
        self.progressBar.setValue(0)
        self.progressBar.setVisible(False)
        self.labelProgressbar.setVisible(False)
        self.enable_gui()
        self.raz_gui()
        QtWidgets.qApp.processEvents()
        qmesbox = QtWidgets.QMessageBox(self)
        qmesbox.setWindowTitle('successful upload')
        qmesbox.setText("Copy done successfully !")
        qmesbox.exec_()

    def seizure_type(self):
        if self.spinBoxType.value() != 0:
            self.pushButtonSEEG.setEnabled(True)
        else:
            self.pushButtonSEEG.setDisabled(True)

    # def push_raz_patient(self):
    #     self.TextName.setPlainText("")
    #     self.TextPrenom.setPlainText("")
    #     self.TextID.setPlainText("")
    #     self.protocole1_name.setPlainText("")
    #     self.radioButtonM.setAutoExclusive(False)
    #     self.radioButtonF.setAutoExclusive(False)
    #     self.radioButtonF.setChecked(False)
    #     self.radioButtonM.setChecked(False)
    #     self.radioButtonM.setAutoExclusive(True)
    #     self.radioButtonF.setAutoExclusive(True)
    #     self.groupBox.setEnabled(True)
    #     self.groupBox_2.setEnabled(True)
    #     self.TextName.setEnabled(True)
    #     self.TextPrenom.setEnabled(True)
    #     self.groupBox_3.setDisabled(True)

    def disable_gui(self):
#         self.listElectrodeTypes.setDisabled(True)
        # self.comboBoxImplantation.setDisabled(True)
        # self.comboBoxImagerie.setDisabled(True)
        # self.comboBoxSeeg.setDisabled(True)
        # self.pushButtonAddiFiles.setDisabled(True)
        self.pushButtonReset.setDisabled(True)
#        self.pushButtonResume.setDisabled(True)

    def enable_gui(self):
        # self.protocole1_name.setEnabled(True)
        #self.push_raz_patient()
        self.raz_gui()


class Dialog(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, pere):
        QtWidgets.QDialog.__init__(self, pere)
        self.setupUi(self)


class ResumeWidget(QtWidgets.QDialog):
    def __init__(self, pere):
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle("Fichiers deja envoyes par cet ordinateur")
        self.setGeometry(pere.x() + 30, pere.y() + 60, pere.size().width() / 1.5, pere.size().height() / 1.5)
        self.list_widget = QtWidgets.QListWidget(self)
        self.list_widget.setEnabled(True)
        self.list_widget.setGeometry(
            QtCore.QRect(20, 20, pere.size().width() / 1.5 - 80, pere.size().height() / 1.5 - 80))
        self.list_widget.sizePolicy()


class DialogSeizureType(QtWidgets.QDialog):
    def __init__(self, widget_pos_on_screen):
        QtWidgets.QDialog.__init__(self)
        # self.seeg_type_dialog = QtWidgets.QDialog()
        self.setWindowTitle("Type de crise")
        self.setGeometry(widget_pos_on_screen.x(), widget_pos_on_screen.y(), 200, 100)
        self.typeLabel = QtWidgets.QLabel(self)
        self.typeLabel.setEnabled(True)
        self.typeLabel.setGeometry(QtCore.QRect(20, 30, 80, 20))
        self.typeLabel.setText("Type :")
        self.typeLabel.setVisible(True)
        self.typeNumber = QtWidgets.QSpinBox(self)
        self.typeNumber.setEnabled(True)
        self.typeNumber.setGeometry(QtCore.QRect(100, 30, 80, 20))
        self.buttonOk = QtWidgets.QPushButton(self)
        self.buttonOk.setGeometry(QtCore.QRect(100, 60, 80, 20))
        self.buttonOk.setText("OK")
        self.buttonOk.clicked.connect(self.valid_type)

    def valid_type(self):
        if self.typeNumber.value() != 0:
            self.seizure_type = self.typeNumber.value()
            self.accept()


def call_generic_uplader(bids_path):
    # print(sys.argv)
    # print(len(sys.argv))
    QtCore.pyqtRemoveInputHook()
    # app = QtWidgets.QApplication(sys.argv)
    app = QtWidgets.QApplication(sys.argv)
    window = GenericUploader(bids_path)
    window.show()
    app.exec_()
    #sys.exit(app.exec_())


if __name__ == "__main__":
    try:
        print(sys.argv)
        print(len(sys.argv))
        QtCore.pyqtRemoveInputHook()
        # app = QtWidgets.QApplication(sys.argv)
        app = QtWidgets.QApplication(sys.argv)
        if len(sys.argv) > 1:
            window = GenericUploader(sys.argv[1])
        else:
            window = GenericUploader()
        window.show()
        sys.exit(app.exec_())
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise
