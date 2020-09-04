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

from PyQt5 import QtWidgets
import os
from bids_manager import ins_bids_class
from generic_uploader.meg_import_dialog import MegImportDialog
from generic_uploader.anat_import_dialog import AnatImportDialog


def find_run_nb(subject_modality, items_list, bids_dataset):
    err = 0
    run_nb = None
    for i in range(1, len(subject_modality)):       # 1 car on vient d'updater le sujet sans le run encore
        idx = -1 - i
        current_subject_modality = subject_modality[idx]
        for item in items_list:
            if current_subject_modality[item] != subject_modality[-1][item]:
                err = 5
                break
        if err == 5:
            err = 0
            continue
        run_nb = int(current_subject_modality["run"])
        break
    if err == 5:
        return 1
    elif run_nb:
        return run_nb + 1
    else:
        if not run_nb:
            run, high_run = bids_dataset.get_number_of_runs(subject_modality[-1])
            # if not run:
            if not high_run:
                run_nb = 0 + 1
            else:
                # run_nb = run + 1
                run_nb = high_run + 1
        return run_nb


def import_by_modality(main_window, modality_class, modality_gui, subject):
    bids_dataset = main_window.bids_dataset
    key_list = [str(modality_gui.combobox_list[idx].objectName()) for idx in range(0, len(modality_gui.combobox_list))]
    keys_dict = {}
    for i in range(0, len(key_list)):
        key_list_value = str(modality_gui.combobox_list[i].currentText())
        keys_dict[key_list[i]] = key_list_value
    # modality_idx = [idx for idx in range(0, len(modality_gui.combobox_list))
    #                 if modality_gui.combobox_list[idx].objectName() == "modality"]
    # if (modality_idx.__len__() == 1) and modality_idx:
    #     modality = str(modality_gui.combobox_list[modality_idx[0]].currentText())
    # else:
    #     modality = ""
    # session_idx = [idx for idx in range(0, len(modality_gui.combobox_list))
    #                if modality_gui.combobox_list[idx].objectName() == "session"]
    # if session_idx:
    #     ses = str(modality_gui.combobox_list[session_idx[0]].currentText())
    # else:
    #     ses = ""
    # acq_idx = [idx for idx in range(0, len(modality_gui.combobox_list))
    #            if modality_gui.combobox_list[idx].objectName() == "acq"]
    # if acq_idx:
    #     acq = str(modality_gui.combobox_list[acq_idx[0]].currentText())
    # else:
    #     acq = ''
    # task_idx = [idx for idx in range(0, len(modality_gui.combobox_list))
    #             if modality_gui.combobox_list[idx].objectName() == "task"]
    # if task_idx:
    #     task = str(modality_gui.combobox_list[task_idx[0]].currentText())
    # else:
    #     task = ''
    # if modality_class not in ["Ieeg", "Eeg", "IeegGlobalSidecars"]:
    if modality_class not in ins_bids_class.GlobalSidecars.get_list_subclasses_names():
        tmp_modality = getattr(ins_bids_class, modality_class)()
        if isinstance(tmp_modality, ins_bids_class.Imaging):
            files_type_allowed = tmp_modality.readable_file_formats
            extenstion_allowed = '*' + ' *'.join(files_type_allowed)
            imaging_import_dialog = AnatImportDialog()
            res = imaging_import_dialog.exec_()
            if res == 0:
                return 0
            else:
                if imaging_import_dialog.flag_import == "Nifti file":
                    imported_name = QtWidgets.QFileDialog.getOpenFileName(None, "Select Nifti file",
                                                                           main_window.last_path, extenstion_allowed)
                    main_window.last_path = os.path.dirname(str(imported_name[0]))
                    imagery_folder = imported_name[0]  # to go from tupple to list
                elif imaging_import_dialog.flag_import == "Dicom Folder":
                    imagery_folder = QtWidgets.QFileDialog.getExistingDirectory(None, "Select Dicom folder",
                                                                               main_window.last_path)
                    main_window.last_path = imagery_folder
            if imagery_folder == "":
                return 0, 0
            subject[modality_class] = eval("ins_bids_class." + modality_class + "()")
            '''subject[modality_class][-1].update({'sub': subject['sub'], 'ses': session, 'acq': acq,
                                            'modality': modality, 'fileLoc': str(imagery_folder)})'''
            # test sam pour update generic
            subject[modality_class][-1].update({'sub': subject['sub'], 'fileLoc': str(imagery_folder)})
            items_list = [item for item in subject[modality_class][-1].keys() if item in key_list]
            for i in range(0, len(items_list)):
                subject[modality_class][-1].update({items_list[i]: keys_dict[items_list[i]]})
            # gérer le run ici
            run_nb = find_run_nb(subject[modality_class], items_list, bids_dataset)
            subject[modality_class][-1].update({'run': str(run_nb)})
    # elif modality_class in ["Ieeg", "Meg", "Eeg", "IeegGlobalSidecars"]:
        elif isinstance(tmp_modality, ins_bids_class.Electrophy):
        # files_type_allowed = "(*.trc *.eeg *.vhdr *.vmrk *.dat *.jpg *.png *.edf *.ctf *.fif)"
            files_type_allowed = tmp_modality.readable_file_formats
            extenstion_allowed = '*' + ' *'.join(files_type_allowed)
            if tmp_modality.classname() is not "Meg":
                imported_name = QtWidgets.QFileDialog.getOpenFileNames(None, "Select one or more files",
                                                               main_window.last_path, extenstion_allowed)
                # SEEG part
                if not imported_name[0]:
                    return 0, 0
                main_window.last_path = os.path.dirname(str(imported_name[0]))
                nb_file = imported_name[0].__len__()
                if nb_file == 0:
                    return 0, 0
                imported_name = imported_name[0]  # to go from tupple to list
                file_list = [str(imported_name[i]) for i in range(0, nb_file)]
                files_status = main_window.return_error_if_accent_in_name(file_list)
                if files_status == 0:
                    return 0, 0
                for i in range(0, nb_file):
                    filename, file_ext = os.path.splitext(file_list[i])
                    if file_ext == ".dat" or file_ext == ".vmrk" or (
                            file_ext == ".eeg" and os.path.isfile(filename + '.vhdr')):
                        continue
                    # attention si nom de fichier existant erreur ---------------------
                    for a in range(1, len(main_window.maplist)):
                        listwidget_element = str(main_window.listWidget.item(a).text())
                        filepath = listwidget_element.split(": ")
                        filepath = filepath[1]
                        existing_basename = os.path.basename(filepath)
                        new_basename = os.path.basename(file_list[i])
                        if existing_basename == new_basename:
                            QtWidgets.QMessageBox.critical(main_window, "error",
                                                           "error, file with same name already existing")
                            return 0, 0
                            # -------------------------------------------------------------
                    subject[modality_class] = eval("ins_bids_class." + modality_class + "()")  # PROBLEM ICI PHOTO
                    '''subject[modality_class][-1].update({'sub': subject['sub'], 'ses': session, 'acq': acq,
                                                        'modality': modality, 'fileLoc': str(file_list[i])})'''
                    # test sam pour update generic
                    subject[modality_class][-1].update({'sub': subject['sub'], 'fileLoc': str(file_list[i])})
                    # items_list = [item for item in subject[modality_class][-1].keys() if
                    #               item in ["ses", "acq", "modality", "task"]]
                    items_list = [item for item in subject[modality_class][-1].keys() if item in key_list]
                    for j in range(0, len(items_list)):
                        subject[modality_class][-1].update({items_list[j]: keys_dict[items_list[j]]})
                    # gérer le run ici
                    run_nb = find_run_nb(subject[modality_class], items_list, bids_dataset)
                    subject[modality_class][-1].update({'run': str(run_nb)})
            else:
                meg_import_dialog = MegImportDialog()
                res = meg_import_dialog.exec_()
                if res == 0:
                    return 0
                else:
                    if meg_import_dialog.flag_import == "files":
                        imported_name = QtWidgets.QFileDialog.getOpenFileNames(None, "Select one or more files",
                                                                           main_window.last_path, extenstion_allowed)
                        main_window.last_path = os.path.dirname(str(imported_name[0]))
                        # car il peut y avoir plusieurs fichier !!
                        main_window.last_path = os.path.dirname(str(imported_name[0]))
                        nb_file = imported_name[0].__len__()
                        if nb_file == 0:
                            return 0, 0
                        imported_name = imported_name[0]  # to go from tupple to list
                        file_list = [str(imported_name[i]) for i in range(0, nb_file)]
                        files_status = main_window.return_error_if_accent_in_name(file_list)
                        if files_status == 0:
                            return 0, 0
                        for i in range(0, nb_file):
                            filename, file_ext = os.path.splitext(file_list[i])
                            if file_ext not in files_type_allowed:
                                continue
                            # attention si nom de fichier existant erreur ---------------------
                            for a in range(1, len(main_window.maplist)):
                                listwidget_element = str(main_window.listWidget.item(a).text())
                                filepath = listwidget_element.split(": ")
                                filepath = filepath[1]
                                existing_basename = os.path.basename(filepath)
                                new_basename = os.path.basename(file_list[i])
                                if existing_basename == new_basename:
                                    QtWidgets.QMessageBox.critical(main_window, "error",
                                                                   "error, file with same name already existing")
                                    return 0, 0
                                    # -------------------------------------------------------------
                            subject[modality_class] = eval(
                                "ins_bids_class." + modality_class + "()")  # PROBLEM ICI PHOTO
                            '''subject[modality_class][-1].update({'sub': subject['sub'], 'ses': session, 'acq': acq,
                                                                'modality': modality, 'fileLoc': str(file_list[i])})'''
                            # test sam pour update generic
                            subject[modality_class][-1].update({'sub': subject['sub'], 'fileLoc': str(file_list[i])})
                            # items_list = [item for item in subject[modality_class][-1].keys() if
                            #               item in ["ses", "acq", "modality", "task"]]
                            items_list = [item for item in subject[modality_class][-1].keys() if item in key_list]
                            for j in range(0, len(items_list)):
                                subject[modality_class][-1].update({items_list[j]: keys_dict[items_list[j]]})
                            # gérer le run ici
                            run_nb = find_run_nb(subject[modality_class], items_list, bids_dataset)
                            subject[modality_class][-1].update({'run': str(run_nb)})
                    elif meg_import_dialog.flag_import == "folder":
                        imported_name = QtWidgets.QFileDialog.getExistingDirectory(None, "Select MEG folder",
                                                                           main_window.last_path)
                        # continuer ici et mettre le return
                        if imported_name == "":
                            return 0, 0
                        subject[modality_class] = eval("ins_bids_class." + modality_class + "()")
                        subject[modality_class][-1].update({'sub': subject['sub'], 'fileLoc': str(imported_name)})
                        items_list = [item for item in subject[modality_class][-1].keys() if item in key_list]
                        for i in range(0, len(items_list)):
                            subject[modality_class][-1].update({items_list[i]: keys_dict[items_list[i]]})
                        # gérer le run ici
                        run_nb = find_run_nb(subject[modality_class], items_list, bids_dataset)
                        subject[modality_class][-1].update({'run': str(run_nb)})
                        main_window.last_path = imported_name
                        return subject, keys_dict
    else:
        if "modality" in key_list:
            if keys_dict["modality"] == "coordsystem":
                extenstion_allowed = "*.json"
            elif keys_dict["modality"] == "photo":
                files_type_allowed = ins_bids_class.Photo.readable_file_format
                extenstion_allowed = '*' + ' *'.join(files_type_allowed)
            elif keys_dict["modality"] == "electrodes":
                extenstion_allowed = "*.tsv"
            elif keys_dict["modality"] == 'blood':
                extenstion_allowed = "(*.json *.tsv)"
        # else:                     # mettre une erreur ici
        #     files_type_allowed = getattr(ins_bids_class, modality_class).allowed_file_formats
        #     extenstion_allowed = '*' + ' *'.join(files_type_allowed)
        imported_name = QtWidgets.QFileDialog.getOpenFileNames(None, "Select one or more files",
                                                           main_window.last_path, extenstion_allowed)
        imported_name = imported_name[0] # to manage pyqt5 and tuple from QtWidgets.openfile
        if not imported_name:
            return 0, 0
        nb_file = imported_name.__len__()
        if nb_file == 0:
            return 0, 0
        file_list = [str(imported_name[i]) for i in range(0, nb_file)]
        files_status = main_window.return_error_if_accent_in_name(file_list)
        if files_status == 0:
            return 0, 0
        for i in range(0, nb_file):
            tmp_modality = getattr(ins_bids_class, modality_class)(str(file_list[i]))
            subject[modality_class].append(tmp_modality)
            subject[modality_class][-1].update({'sub': subject['sub']})
            # subject[modality_class][-1].update(tmp_modality)
            items_list = [item for item in subject[modality_class][-1].keys() if item in key_list]
            for j in range(0, len(items_list)):
                if not subject[modality_class][-1][items_list[j]]:
                    subject[modality_class][-1].update({items_list[j]: keys_dict[items_list[j]]})
    return subject, keys_dict
