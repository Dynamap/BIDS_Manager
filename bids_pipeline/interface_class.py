#!/usr/bin/python3
# -*-coding:Utf-8 -*

#     BIDS Pipeline select and analyse data in BIDS format.
#     Copyright © 2018-2020 Aix-Marseille University, INSERM, INS
#
#     This file is part of BIDS Pipeline. This file manages the graphical interfaces.
#
#     BIDS Pipeline is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     any later version
#
#     BIDS Pipeline is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with BIDS Pipeline.  If not, see <https://www.gnu.org/licenses/>
#
#     Authors: Aude Jegou, 2019-2021

import os
import bids_manager.ins_bids_class as bids
from bids_manager.ins_anywave import anywave_ext


def compare_listes(liste_final, liste_file, get_only_common=False):
    """ Compare two lists to keep the only common elements

    :param liste_final: list
    :param liste_file: list
    :param get_only_common: Boolean, to know if the list should contain only common elements
    :return: boolean to know if the lists are similar and the new list
    """
    is_same = True
    new_liste_final = []
    sX = set(liste_final)
    sY = set(liste_file)
    set_common = sX - sY
    if not set_common == sX:
        is_same = False
    if not get_only_common:
        for elt in liste_file:
            if elt not in liste_final:
                liste_final.append(elt)
    else:
        new_liste_final = [elt for elt in list(sX.intersection(sY))]
    return is_same, new_liste_final


class Interface(dict):
    """
        A class to create the require directory to create the Graphical Interface for selection

        Attributes
        ----------
        bids_data: BidsDataset
    """

    def __init__(self, bids_data):
        self.bids_data = bids_data
        self.subject = [sub['sub'] for sub in self.bids_data['Subject']]
        self.vars_interface()

    def copy_values(self, input_dict):
        for key in input_dict:
            if isinstance(input_dict[key], dict):
                self[key] = input_dict[key]
        if hasattr(input_dict, 'savereadingbysub'):
            if isinstance(input_dict.savereadingbysub, ElementsBySubjects):
                self.savereadingbysub = ElementsBySubjects()
                self.savereadingbysub.copy_values(input_dict.savereadingbysub)

    def vars_interface(self):
        """Get the type of button for each arguments of the JSON file

        :return:
        """
        def check_numerical_value(element):
            is_numerical = False
            punctuation = ',.?!:'
            temp = element.translate(str.maketrans('', '', punctuation))
            temp = temp.strip('YymM ')
            if temp.isnumeric():
                is_numerical = True
            return is_numerical

        participant_dict = self.bids_data['ParticipantsTSV']
        req_keys = self.bids_data.requirements['Requirements']['Subject']['keys']
        if isinstance(req_keys, dict):
            display_dict = {key: value for key, value in req_keys.items() if (
                value and value != '') or 'age' in key or 'duration' in key}
        elif isinstance(req_keys, list):
            display_dict = {
                key: '' for key in req_keys if 'age' in key or 'duration' in key}
        #display_dict = {key: value for key, value in req_keys.items() if value or 'age' in key or 'duration' in key}
        # for key, value in req_keys.items():
            # if value:
            #     display_dict[key] = value
            # elif 'age' in key:
            #     display_dict[key] = value
            # elif 'duration' in key:
            #     display_dict[key] = value
        criteria = participant_dict.header
        for key in display_dict:
            is_string = False
            display_value = []
            if isinstance(display_dict[key], list):
                display_value = display_dict[key]
            else:
                display_value.append('min_' + key)
                display_value.append('max_' + key)
                is_string = True
            # idx = criteria.index(key)
            # for val_part in participant_dict[1::]:
            #     is_number = check_numerical_value(val_part[idx])
            #     if is_number and display_dict[key]:
            #         display_value.append(val_part[idx])
            #     elif is_number:
            #         display_value.append('min_' + key)
            #         display_value.append('max_' + key)
            #         is_string = True
            #     else:
            #         l_elt = val_part[idx].split(', ')
            #         for l in l_elt:
            #             display_value.append(l)
            display_value = list(set(display_value))
            if is_string:
                self[key] = {}
                display_value = sorted(display_value, reverse=True)
                if 'n/a' in display_value:
                    display_value.remove('n/a')
                elif 'N/A' in display_value:
                    display_value.remove('N/A')
                self[key]['attribut'] = 'StringVar'
                self[key]['value'] = [value for value in display_value]
            elif display_value:
                # display_value = list(set(display_value).intersection(set(display_dict[key])))
                if len(display_value) == 1 and not 'n/a' in display_value:
                    self[key] = {}
                    self[key]['attribut'] = 'Label'
                    self[key]['value'] = [value for value in display_value]
                elif len(display_value) > 1:
                    self[key] = {}
                    self[key]['attribut'] = 'Variable'
                    self[key]['value'] = [value for value in display_value]

    def get_parameter(self):
        """ Get the value for each arguments after selection in GUI

        :return: Dictionary with the results
        """
        res_dict = dict()
        for key in self:
            att_type = self[key]['attribut']
            val_temp = self[key]['value']
            if att_type == 'Variable':
                for val in self[key]['results']:
                    if val.get():
                        idx = self[key]['results'].index(val)
                        try:
                            res_dict[key].append(val_temp[idx])
                        except:
                            res_dict[key] = []
                            res_dict[key].append(val_temp[idx])
            elif att_type == 'StringVar':
                num_value = False
                if isinstance(val_temp, list):
                    for id_var in val_temp:
                        if id_var.get().isalnum():
                            if id_var._name.startswith('min'):
                                minA = int(id_var.get())
                                num_value = True
                            elif id_var._name.startswith('max'):
                                maxA = int(id_var.get())
                                num_value = True
                            else:
                                res_dict[key] = id_var.get()
                    if num_value:
                        res_dict[key] = range(minA, maxA+1)
                else:
                    try:
                        res_dict[key] = val_temp.get()
                    except:
                        res_dict[key] = ""
                if key in res_dict and key in res_dict[key]:
                    res_dict[key] = res_dict[key].replace('_'+key, '')
            elif att_type == 'Listbox':
                val_temp = self[key]['results']
                res_dict[key] = val_temp.get()
            elif att_type == 'Bool':
                if val_temp.get() == True:
                    res_dict[key] = True
                else:
                    res_dict[key] = False
            elif att_type == 'Label':
                res_dict[key] = val_temp
            elif att_type == 'File':
                if len(val_temp) > 1 and val_temp[1]:
                    if isinstance(val_temp[1], list):
                        res_dict[key] = ', '.join(val_temp[1])
                    else:
                        res_dict[key] = val_temp[1]

        return res_dict

    def get_subject_list(self, input_dict):
        """ Get the subject corresponding to the criteria selected by the user

        :param input_dict: dict, containing the criteria selection
        :return: List of subjects corresponding to the results
        """
        subject_list = []
        for elt in self.bids_data['ParticipantsTSV'][1::]:
            elt_in = []
            for key, value in input_dict.items():
                idx_key = self.bids_data['ParticipantsTSV'].header.index(key)
                # list of the input values (in the participants.tsv there can be more than one value per field, and the delimiter is ;)
                values_sub = elt[idx_key].split(';')
                if isinstance(value, range):
                    elt[idx_key] = elt[idx_key].replace(',', '.')
                    age_p = round(float(elt[idx_key].rstrip('YyMm ')))
                    if age_p in value:
                        elt_in.append(True)
                    else:
                        elt_in.append(False)
                elif isinstance(value, list):
                    found = 0
                    for element in values_sub:
                        if element in value:
                            found = found + 1
                    if found == 0:
                        elt_in.append(False)
                    else:
                        elt_in.append(True)
                elif isinstance(value, str):
                    if value in elt[idx_key]:
                        elt_in.append(True)
                    else:
                        elt_in.append(False)
            elt_in = list(set(elt_in))
            if len(elt_in) == 1 and elt_in[0] is True:
                if 'sub-' in elt[0]:
                    elt[0] = elt[0].split('sub-')[1]
                subject_list.append(elt[0])
        return subject_list


class ParameterInterface(Interface):
    """
        A subclass of Interface for the Parameters
    """
    unit_value = ['Default', 'Unit']
    read_value = ['Read', 'ElementsToRead', 'MultipleSelection']
    list_value = ['PossibleValue', 'MultipleSelection']
    file_value = ['FileLoc', 'Extension']
    bool_value = ['Default', 'InCommandLine']
    bids_value = ['ReadBids', 'Type']
    savereadingbysub = {}

    def __init__(self, bids_data, parameter_soft=None, nbr=None):
        nb = ''
        if nbr is not None:
            nb = str(nbr) + '_'
        self.bids_data = bids_data
        if parameter_soft:
            self.parameters = {nb+key: value for key, value in parameter_soft.items(
            ) if key not in ['Input', 'Output', 'Callname', 'command_line_base', 'Intermediate']}
            self.vars_interface()

    def vars_interface(self):
        for key in self.parameters:
            self[key] = {}
            if 'Mode' in key:
                if len(self.parameters[key]) > 1:
                    self[key]['attribut'] = 'Listbox'
                    self[key]['value'] = self.parameters[key]
                elif len(self.parameters[key]) == 1:
                    self[key]['attribut'] = 'Label'
                    self[key]['value'] = self.parameters[key][-1]
            else:
                keys = list(self.parameters[key].keys())
                if keys == self.unit_value:
                    self[key]['attribut'] = 'StringVar'
                    self[key]['value'] = str(
                        self.parameters[key]['Default']) + self.parameters[key]['Unit'] + '_' + key
                    self[key]['unit'] = self.parameters[key]['Unit']
                elif keys == self.list_value:
                    if self.parameters[key]['MultipleSelection']:
                        st_type = 'Variable'
                    else:
                        st_type = 'Listbox'
                    self[key]['attribut'] = st_type
                    self[key]['value'] = self.parameters[key]['PossibleValue']
                elif keys == self.file_value:  # A revoir
                    self[key]['attribut'] = 'File'
                    self[key]['value'] = [self.parameters[key]['Extension']]
                elif keys == self.bool_value:
                    self[key]['attribut'] = 'Bool'
                    self[key]['value'] = self.parameters[key]['Default']
                elif keys == self.read_value:
                    self.savereadingbysub[key] = {}
                    if self.parameters[key]['MultipleSelection']:
                        st_type = 'Variable'
                    else:
                        st_type = 'Listbox'
                    self[key]['attribut'] = st_type
                    self[key]['value'] = self.reading_file(key)
                elif keys == self.bids_value:
                    del self[key]
                else:
                    raise EOFError(
                        'The keys in Parameters of your JSON file are not conform.\n Please modify it according to the template given.\n')

    def reading_file(self, key):
        """Read the different files inside teh dataset to offer the possible value to the user

        :param key: str
        :return: List of possible value
        """
        def read_file(file, elements):
            param = []
            name, ext = os.path.splitext(file)
            if ext == '.csv':
                split_value = ', '
            else:
                split_value = '\t'
            f = open(file, 'r')
            f_cont = f.readlines()
            if elements == 'header':
                header = f_cont[0].split(split_value)
                for val in header:
                    param.append(val)
                f.close()
                return param
            elif elements.isnumeric():
                idx = int(elements)
            elif elements:
                line = f_cont[0].split('\n')[0]
                header = line.split(split_value)
                idx = header.index(elements)
            else:
                idx = 0
            for line in f_cont[1::]:
                line = line.split('\n')[0]
                trial_type = line.split(split_value)
                param.append(trial_type[idx])
            f.close()
            return param

        reading_file = self.parameters[key]['Read'].strip('*')
        [filetype, ext] = reading_file.split('.')
        if '.' + ext in anywave_ext:
            dir2read = os.path.join(
                bids.BidsDataset.dirname, 'derivatives', 'anywave', bids.BidsBrick.curr_user)
            if not os.path.exists(dir2read):
                dir2read = os.path.join(
                    bids.BidsDataset.dirname, 'derivatives', 'anywave', 'common')
            if not os.path.exists(dir2read):
                dir2read = self.bids_data.cwdir
        else:
            dir2read = self.bids_data.cwdir
        elements = self.parameters[key]['ElementsToRead']
        mark_to_remove = ['?', '***', '*']
        param = []
        parambysub = {}
        is_same = True
        for subject in os.listdir(dir2read):
            if subject.endswith(reading_file) and os.path.isfile(os.path.join(dir2read, subject)):
                file_param = read_file(
                    os.path.join(dir2read, subject), elements)
                if not param:
                    param = [elt for elt in file_param]
                else:
                    is_same, other = compare_listes(param, file_param)
                if subject not in parambysub:
                    parambysub[subject] = file_param
                else:
                    is_same, other = compare_listes(
                        parambysub[subject], file_param)
                break
            elif subject.startswith('sub') and os.path.isdir(os.path.join(dir2read, subject)):
                for session in os.listdir(os.path.join(dir2read, subject)):
                    if os.path.isdir(os.path.join(dir2read, subject, session)):
                        for mod in os.listdir(os.path.join(dir2read, subject, session)):
                            if os.path.isdir(os.path.join(dir2read, subject, session, mod)):
                                with os.scandir(os.path.join(dir2read, subject, session, mod)) as it:
                                    for entry in it:
                                        if entry.name.endswith(reading_file):
                                            file_param = read_file(
                                                entry.path, elements)
                                            if not param:
                                                param = [
                                                    elt for elt in file_param]
                                            else:
                                                is_same, other = compare_listes(
                                                    param, file_param)
                                            if subject not in parambysub:
                                                parambysub[subject] = file_param
                                            else:
                                                is_same, other = compare_listes(
                                                    parambysub[subject], file_param)
                            elif os.path.isfile(
                                    os.path.join(dir2read, subject, session, mod)) and mod.endswith(
                                    reading_file):
                                file_param = read_file(os.path.join(dir2read, subject, session, mod),
                                                       elements)
                                if not param:
                                    param = [elt for elt in file_param]
                                else:
                                    is_same, other = compare_listes(
                                        param, file_param)
                                if subject not in parambysub:
                                    parambysub[subject] = file_param
                                else:
                                    is_same, other = compare_listes(
                                        parambysub[subject], file_param)
        param = list(set(param))
        param.sort()
        self.savereadingbysub[key] = parambysub
        return [par for par in param if not par in mark_to_remove]


class InputParameterInterface(Interface):
    """
        A subclass of Interface for the Input Parameters
    """

    def __init__(self, bids_data, parameter_soft_input=None):
        self.bids_data = bids_data
        if parameter_soft_input:
            self.parameters = parameter_soft_input
            mod_list = bids.Electrophy.get_list_subclasses_names(
            ) + bids.Imaging.get_list_subclasses_names()
            if self.parameters.deriv_input:
                mod_list = bids.ElectrophyProcess.get_list_subclasses_names(
                ) + bids.ImagingProcess.get_list_subclasses_names()
                if 'InRaw' in self.parameters:
                    mod_list.extend(bids.Electrophy.get_list_subclasses_names(
                    ) + bids.Imaging.get_list_subclasses_names())
            keylist = [elt for key in mod_list for elt in eval('bids.' + key + '.keylist') if not (
                elt in bids.BidsJSON.get_list_subclasses_names(
                ) or elt in bids.BidsTSV.get_list_subclasses_names()
                or elt in bids.BidsFreeFile.get_list_subclasses_names() or elt.endswith('Loc') or elt.endswith(
                    'modality') or elt == 'sub' or elt.endswith('Labels'))]  # elt.endswith('JSON') or elt.endswith('TSV')
            self.keylist = list(set(keylist))
            self.savereadingbysub = ElementsBySubjects()
            self.vars_interface()

    def vars_interface(self):
        if self.parameters is not None:
            if self.parameters.deriv_input:
                self['DerivFolder'] = dict()
                self['DerivFolder']['attribut'] = 'Listbox'
                deriv_list = [elt for elt in os.listdir(os.path.join(self.bids_data.cwdir, 'derivatives'))if
                              elt not in ['log', 'parsing', 'parsing_old', 'log_old'] and
                              os.path.isdir(os.path.join(self.bids_data.cwdir, 'derivatives', elt))]
                if 'anywave' in deriv_list:
                    userdir = os.listdir(os.path.join(
                        self.bids_data.cwdir, 'derivatives', 'anywave'))
                    deriv_list.extend(userdir)
                self['DerivFolder']['value'] = deriv_list
            self['modality'] = dict()
            if self.parameters['Modality']:
                if len(self.parameters['Modality']) > 1:
                    self['modality']['attribut'] = 'Listbox'
                    self['modality']['value'] = self.parameters['Modality']
                else:
                    self['modality']['value'] = self.parameters['Modality'][-1]
                    self['modality']['attribut'] = 'Label'
            else:
                self['modality']['attribut'] = 'Listbox'
                self['modality']['value'] = bids.Electrophy.get_list_subclasses_names(
                ) + bids.Imaging.get_list_subclasses_names()
            if 'InRaw' in self.parameters:
                self['InRaw'] = dict()
                self['InRaw']['attribut'] = 'Bool'
                self['InRaw']['value'] = self.parameters['InRaw']
                self['FileType'] = dict()
                self['FileType']['attribut'] = 'StringVar'
                self['FileType']['value'] = str(
                    self.parameters['FileType']+'_FileType')
        else:
            self = {'modality': {}}
            self['modality']['attribut'] = 'Listbox'
            self['modality']['value'] = bids.Imaging.get_list_subclasses_names(
            ) + bids.Electrophy.get_list_subclasses_names()

        if self['modality']['attribut'] == 'Label':
            modality = [self['modality']['value']]
        else:
            modality = self['modality']['value']
        if not self.parameters.deriv_input:
            for sub in self.bids_data['Subject']:
                # self.savereadingbysub[sub['sub']] = dict()
                for mod in sub:
                    if mod and mod in modality:
                        keys = [elt for elt in self.keylist if elt in eval(
                            'bids.' + mod + '.keylist') and elt != 'sub']
                        if mod in bids.Imaging.get_list_subclasses_names() and 'mod' not in keys:
                            keys.append('mod')
                        if sub[mod]:
                            dictsub = self.get_values(mod, keys, sub)
                            self.savereadingbysub.copy_values(
                                dictsub, sub['sub'])
        else:
            for pip in self.bids_data['Derivatives'][0]['Pipeline']:
                sub_list = [sub for sub in pip['SubjectProcess']]
                for sub in sub_list:
                    # self.savereadingbysub[sub['sub']] = {}
                    for mod in sub:
                        if mod and mod.split('Process')[0] in modality:
                            keys = [elt for elt in self.keylist if
                                    elt in eval('bids.' + mod + '.keylist') and elt != 'sub']
                            if mod in bids.ImagingProcess.get_list_subclasses_names() and 'mod' not in keys:
                                keys.append('mod')
                            if sub[mod]:
                                dictsub = self.get_values(mod, keys, sub)
                                self.savereadingbysub.copy_values(
                                    dictsub, sub['sub'])
        clefs = [key for key in self]
        for key in clefs:
            if self[key]['attribut'] == 'Label' and key not in ['modality', 'ses']:
                del self[key]
        # Ecrire qqch si juste la modality en label et rien d'autre

    def get_values(self, mod, keys, sub):
        """ Get the possible values for the inputs

        :param mod:
        :param keys:
        :param sub:
        :return:
        """
        dict2update = dict()
        for key in keys:
            value = [elt[key] for elt in sub[mod]]
            if key == 'mod':
                value = [elt['modality'] for elt in sub[mod]]
            value = sorted(list(set(value)))
            # if '' in value:
            #     value.remove('')
            if value:  # and value[0] is not '':
                # if key == 'modality':
                #     if self[key]['attribut'] == 'Label':
                #         self[key]['value'] = value
                #     else:
                #         self[key]['value'].extend(value)
                if key == 'ses' and '' in value:
                    value.remove('')
                dict2update[key] = value
                if not key in self:
                    self[key] = {}
                    self[key]['value'] = value
                    self[key]['attribut'] = 'IntVar'
                else:
                    self[key]['value'].extend(value)
                self[key]['value'] = sorted(
                    list(set(self[key]['value'])))
                if len(self[key]['value']) > 1:
                    self[key]['attribut'] = 'Variable'
                elif len(self[key]['value']) == 1:
                    self[key]['attribut'] = 'Label'
        return dict2update


class ElementsBySubjects(dict):
    """
        A class to know what elements (i.e. events) are presents for each subject
    """

    def __int__(self):
        self = dict()

    def copy_values(self, input_dict, sub=None):
        if sub is None:
            for sub in input_dict:
                self.copy_values(input_dict[sub], sub)
        else:
            if sub not in self:
                self[sub] = {}
            for key in input_dict:
                if key not in self[sub]:
                    self[sub][key] = input_dict[key]
                elif isinstance(self[sub][key], list):
                    self[sub][key].extend(input_dict[key])
