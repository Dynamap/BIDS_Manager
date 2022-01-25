#!/usr/bin/python3
# -*-coding:Utf-8 -*

#     BIDS Pipeline select and analyse data in BIDS format.
#     Copyright © 2018-2020 Aix-Marseille University, INSERM, INS
#
#     This file is part of BIDS Pipeline. This file manages the analysis.
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

import bids_manager.ins_bids_class as bids
from bids_manager.ins_anywave import anywave_ext_analysis, handle_anywave_files
import json
import os
import datetime
import getpass
import getopt
import sys
import subprocess
import shutil
import itertools
import platform
from tkinter import messagebox, filedialog
from bids_pipeline.convert_process_file import go_throught_dir_to_convert, convert_channels_in_montage_file, convert_events_in_marker_file
from sys import exc_info
import tempfile
import PySimpleGUI as sg


def save_batch(bids_dir, batch_dict):
    batch_dir = os.path.join(bids_dir, 'derivatives', 'bids_pipeline', 'batch')
    os.makedirs(batch_dir, exist_ok=True)
    author = getpass.getuser()
    date = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    date.replace(' ', 'T')
    filename = 'batch_' + author + '_' + date + '.json'
    if any(batch_dict[key] for key in batch_dict):
        with open(os.path.join(batch_dir, filename), 'w+') as file:
            json_str = json.dumps(batch_dict, indent=1, separators=(',', ': '), ensure_ascii=False, sort_keys=False)
            file.write(json_str)


def check_pipeline_presence_locally(pip_name, output_dir, param_var, subject_to_analyse):
    def determine_variant_name(name, dirlist):
        if name in dirlist:
            oldname = name.split('-v')
            new_variant = str(int(oldname[1])+1)
            new_name = oldname[0] + '-v' + new_variant
            finale_name = determine_variant_name(new_name, dirlist)
        else:
            finale_name = name
        return finale_name
    dirlist = [file for file in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, file))]
    isin =0
    variant_list = []
    for folder in dirlist:
        if folder.lower().startswith(pip_name.lower()):
            isin= isin+1
            name = folder.split('-')
            if len(name) >1:
                variant_list.append(name[1])
    if isin > 0:
        output_name = pip_name.lower() + '-v' + str(isin + 1)
        if output_name in dirlist:
            output_name = determine_variant_name(output_name, dirlist)
    else:
        output_name = pip_name.lower()
    output_directory = os.path.join(output_dir, output_name)
    os.makedirs(output_directory, exist_ok=True)
    desc_data = bids.DatasetDescPipeline(param_vars=param_var, subject_list=subject_to_analyse)
    desc_data['Name'] = output_name

    return output_directory, output_name, desc_data


class DerivativesSetting(object):
    path = None
    pipelines = []
    log = ''

    def __init__(self, bids_dev):
        if isinstance(bids_dev, bids.Derivatives):
            self.pipelines = bids_dev['Pipeline']
            self.path = os.path.join(bids_dev.cwdir, 'derivatives')
        elif isinstance(bids_dev, str):
            if os.path.exists(bids_dev) and bids_dev.endswith('derivatives'):
                self.path = bids_dev
                self.log = self.read_directory(bids_dev)

    def read_directory(self, dev_dir):
        log_reading = ''
        with os.scandir(dev_dir) as it:
            for entry in it:
                if entry.is_dir():
                    pip = bids.Pipeline()
                    pip.dirname = entry.path
                    empty_dir, log = self.empty_dirs(entry.path)#, recursive=True)
                    log_reading += log
                    if not empty_dir:
                        self.parse_pipeline(pip.dirname, entry.name)
                    else:
                        log_reading += 'Folder {} has been removed from the derivatives BIDS dataset because it is empty.\n'.format(entry.name)
                        shutil.rmtree(entry.path, ignore_errors=True)
                    #self.pipelines.append(pip)
        return log_reading

    def is_empty(self):
        default = ['log', 'parsing']
        pip_list = [pip['name'] for pip in self.pipelines if pip['name'] not in default]
        if pip_list:
            is_empty = False
        else:
            is_empty = True
        return is_empty, pip_list

    def create_pipeline_directory(self, pip_name, param_var, subject_to_analyse):
        def check_pipeline_variant(pip_list, pip_name):
            variant_list = []
            it_exist = False
            for pip in pip_list:
                if pip.startswith(pip_name.lower()):
                    variant_list.append(pip)
                    it_exist=True
            return it_exist, variant_list

        directory_name = None
        is_empty, pip_list = self.is_empty()
        mode = (param_var['Mode'] == 'manual')
        if not is_empty:
            it_exist, variant_list = check_pipeline_variant(pip_list, pip_name)
            if it_exist:
                for elt in variant_list:
                    dataset_file = os.path.join(self.path, elt, bids.DatasetDescPipeline.filename)
                    if not os.path.exists(dataset_file):
                        dataset_file = None
                    desc_data = bids.DatasetDescPipeline(filename=dataset_file)
                    same_param, sub_inside, same_input = desc_data.compare_parameters(param_var, subject_to_analyse)
                    if (same_param and same_input and not sub_inside) or (same_input and mode):
                        directory_name = elt
                        if not mode:
                            #desc_data['SourceDataset']['sub'].append(subject_list['sub'])
                            desc_data.update(subject_to_analyse)
                        break
                if not directory_name:
                    directory_name = pip_name.lower() + '-v' + str(len(variant_list) + 1)
                    desc_data = bids.DatasetDescPipeline(param_vars=param_var, subject_list=subject_to_analyse)
                    desc_data['Name'] = directory_name
            else:
                directory_name = pip_name.lower()
                desc_data = bids.DatasetDescPipeline(param_vars=param_var, subject_list=subject_to_analyse)
                desc_data['Name'] = directory_name
        else:
            directory_name = pip_name.lower()
            desc_data = bids.DatasetDescPipeline(param_vars=param_var, subject_list=subject_to_analyse)
            desc_data['Name'] = directory_name
        directory_path = os.path.join(self.path, directory_name)
        os.makedirs(directory_path, exist_ok=True)
        desc_data.write_file(jsonfilename=os.path.join(directory_path, bids.DatasetDescPipeline.filename))
        return directory_path, directory_name, desc_data

    def pipeline_is_present(self, pip_name):
        is_present = False
        idx= None
        for pip in self.pipelines:
            if pip['name'] == pip_name:
                is_present = True
                idx = self.pipelines.index(pip)

        return is_present, idx

    def parse_pipeline(self, directory_path, pip_name):
        #Function wrote by Nicolas and adapted by Aude
        def parse_sub_bids_dir(sub_currdir, subinfo, num_ses=None, mod_dir=None):
            with os.scandir(sub_currdir) as it:
                for file in it:
                    if file.name.startswith('ses-') and file.is_dir():
                        num_ses = file.name.replace('ses-', '')
                        parse_sub_bids_dir(file.path, subinfo, num_ses=num_ses)
                    elif not mod_dir and file.name.capitalize() in bids.ModalityType.get_list_subclasses_names() and \
                            file.is_dir():
                        # enumerate permits to filter the key that corresponds to other subclass e.g Anat, Func, Ieeg
                        parse_sub_bids_dir(file.path, subinfo, num_ses=num_ses, mod_dir=file.name.capitalize())
                    elif not mod_dir and file.name.endswith('_scans.tsv') and file.is_file():
                        tmp_scantsv = bids.ScansTSV()
                        tmp_scantsv.read_file(file)
                        for scan in subinfo['Scans']:
                            scan.compare_scanstsv(tmp_scantsv)
                    elif mod_dir and file.is_file():
                        filename, ext = os.path.splitext(file)
                        if ext.lower() == '.gz':
                            filename, ext = os.path.splitext(filename)
                        if ext.lower() in eval('bids.'+ mod_dir + 'Process.allowed_file_formats'):
                            subinfo[mod_dir + 'Process'] = eval('bids.' + mod_dir + 'Process()')
                            subinfo[mod_dir + 'Process'][-1]['fileLoc'] = file.path
                            subinfo[mod_dir + 'Process'][-1].get_attributes_from_filename()
                            subinfo[mod_dir + 'Process'][-1]['modality'] = mod_dir
                            if subinfo[mod_dir + 'Process'][-1]['sub'] == '':
                                norm_path = os.path.normpath(sub_currdir)
                                pathlist = norm_path.split(os.sep)
                                subname = [s.replace('sub-', '') for s in pathlist if s.startswith('sub-')]
                                sesname = [s.replace('ses-', '') for s in pathlist if s.startswith('ses-')]
                                if subname:
                                    subinfo[mod_dir + 'Process'][-1]['sub'] = subname[0]
                                if sesname:
                                    subinfo[mod_dir + 'Process'][-1]['ses'] = sesname[0]
                    elif mod_dir and file.is_dir():
                        str2add = 'Process'
                        subinfo[mod_dir + str2add] = eval('bids.' + mod_dir + str2add + '()')
                        subinfo[mod_dir + str2add][-1]['fileLoc'] = file.path

        def get_attribute_filename(filename):
            dir_list = ['sub', 'ses']
            dirname = []
            filename, ext = os.path.splitext(filename)
            if ext == '.gz':
                filename, ext = os.path.splitext(filename)
            fname_pieces = filename.split('_')
            for word in fname_pieces:
                w = word.split('-')
                if len(w) == 2 and w[0] in dir_list:
                    dirname.append(w[0]+'-'+w[1])
            modality = fname_pieces[-1]
            if not modality.capitalize() in bids.ModalityType.get_list_subclasses_names():
                modality = ''
            dirname.append(modality)
            directory = '/'.join(dirname)
            directory = os.path.join(directory_path, directory)
            os.makedirs(directory, exist_ok=True)
            return directory

        is_present, index_pip = self.pipeline_is_present(pip_name)
        if not is_present:
            pip = bids.Pipeline(name=pip_name, dirname=self.path)
            self.pipelines.append(pip)
        else:
            pip = self.pipelines[index_pip]
        name = pip_name.split('-')
        name = name[0]
        with os.scandir(directory_path) as it:
            for entry in it:
                if entry.name.startswith('sub-') and entry.is_file():
                    directory = get_attribute_filename(entry.name)
                    shutil.move(entry, os.path.join(directory, entry.name))
                elif entry.name.startswith('sub-') and entry.is_dir():
                    sub, subname = entry.name.split('-')
                    pip['SubjectProcess'].append(bids.SubjectProcess())
                    pip['SubjectProcess'][-1]['sub'] = subname
                    parse_sub_bids_dir(entry.path, pip['SubjectProcess'][-1])

    def empty_dirs(self, output_directory, rmemptysub=False):
        def sub_empty(subdir):
            empty_dirs = []
            emp_dirs = []
            # dir2check = os.path.join(output_directory, subdir)
            for root, dirs, files in os.walk(subdir, topdown=False):
                # print root, dirs, files
                if not dirs:
                    all_subs_empty = True  # until proven otherwise
                    for sub in dirs:
                        full_sub = os.path.join(root, sub)
                        if full_sub not in emp_dirs:
                            # print full_sub, "not empty"
                            all_subs_empty = False
                            break
                    if all_subs_empty and len(files) == 0:  # Add something about if it's in empty_dirs True,
                        # Aouter un truc pour remove les sujets vide
                        empty_dirs.append(True)
                        emp_dirs.append(root)
                    else:
                        empty_dirs.append(False)
                        # yield root
            return empty_dirs
        #pip_directory = os.path.join(self.path, pip_name)
        subdir = {sub: True for sub in os.listdir(output_directory) if sub.startswith('sub-') and os.path.isdir(os.path.join(output_directory, sub))}
        all_files = []
        pip_name = os.path.basename(output_directory)
        analyse_name = pip_name.split('-')[0].lower()
        default_files = [bids.DatasetDescPipeline.filename, bids.ParticipantsTSV.filename, Parameters.filename,
                         'log_error_analyse.log', analyse_name + '_parameters.json']
        log = ''
        with os.scandir(output_directory) as it:
            for entry in it:
                if entry.is_dir():
                    isempty = sub_empty(entry.path)
                    if all(isempty):
                        subdir[entry.name] = True
                    else:
                        subdir[entry.name] = False
                else:
                    if entry.name in default_files:
                        all_files.append(True)
                    else:
                        all_files.append(False)
        if all(subdir[sub] for sub in subdir) and all(all_files):
            return True, log
        else:
            #remove sub directory
            if rmemptysub:
                for sub in subdir:
                    if subdir[sub]:
                        shutil.rmtree(os.path.join(output_directory, sub))
                        log += 'Subject {} has been removed from the derivatives folder {}\n'.format(sub, output_directory)
                        #remove from dataste_desc
                        for pip in self.pipelines:
                            if pip['name'] == pip_name:
                                if 'SourceDataset' in pip['DatasetDescJSON'] and 'sub' in pip['DatasetDescJSON']['SourceDataset']:
                                    try:
                                        subname = sub.replace('sub-', '')
                                        pip['DatasetDescJSON']['SourceDataset']['sub'].remove(subname)
                                        pip['DatasetDescJSON'].write_file(os.path.join(output_directory, bids.DatasetDescPipeline.filename))
                                        break
                                    except:
                                        continue
                                if 'ParticipantsProcessTSV' in pip.keys():
                                    ids = [cnt for cnt, line in enumerate(pip['ParticipantsProcessTSV']) if line[0] == sub]
                                    if ids:
                                        pip['ParticipantsProcessTSV'].pop(ids[0])
                                        pip['ParticipantsProcessTSV'].write_file(os.path.join(output_directory, bids.ParticipantsTSV.filename))
            return False, log

    def possible_output_for_analysis(self, analysis_name):
        pip_folder = {}
        for pip in self.pipelines:
            if pip['name'].startswith(analysis_name.lower()):
                pip_folder[pip['name']] = {}
                pip_folder[pip['name']]['subject'] = pip['DatsetDescJSON']['SourceDataset']['sub']
                pip_folder[pip['name']]['parameters'] = pip['DatsetDescJSON']['PipelineDescription']
        return pip_folder


class PipelineSetting(dict):
    keylist = ['Name', 'Path', 'Parameters']
    soft_path = os.path.join(os.getcwd(), 'SoftwarePipeline')
    log_error = ''
    cmd_line_log = []
    curr_dev = None
    curr_bids = None
    curr_path = None
    cwdir=None
    jsonfilename=None
    version = '1.1.0'

    def __init__(self, bids_dir, soft_name=None, soft_path=None):
        if isinstance(bids_dir, str):
            if os.path.exists(bids_dir):
                try:
                    self.curr_bids = bids.BidsDataset(bids_dir)
                    self.cwdir = self.curr_bids.cwdir
                except:
                    self.log_error += 'ERROR: The bids data selected is not conform'
                    raise EOFError(self.log_error)
            else:
                self.log_error += 'ERROR: The bids data selected doesn"t exist'
                raise EOFError(self.log_error)
        elif isinstance(bids_dir, bids.BidsDataset):
            self.curr_bids = bids_dir
            self.cwdir = self.curr_bids.cwdir
        Parameters._assign_bids_dir(self.cwdir, self.curr_bids)
        if soft_path and os.path.exists(soft_path):
            self.soft_path = soft_path
        if soft_name is None:
            self.curr_path = ''
            for key in self.keylist:
                if key == 'Parameters':
                    self[key] = {}
                else:
                    self[key] = ''
        elif soft_name + '.json' in os.listdir(self.soft_path):
            self.jsonfilename = soft_name
            err_str = self.read_json_parameter_file(soft_name)
            if err_str:
                raise EOFError(err_str)
        else:
            self.log_error += 'ERROR: The software doesn"t exist'
            raise EOFError(self.log_error)
        if self.curr_path is not self['Path']:
            self['Path'] = self.curr_path
            self.write_file(os.path.join(self.soft_path, soft_name + '.json'))
        self.curr_dev = DerivativesSetting(self.curr_bids['Derivatives'][0])
        self.curr_dev.bp_folder = os.path.join(self.cwdir, 'derivatives', 'bids_pipeline')
        os.makedirs(self.curr_dev.bp_folder, exist_ok=True)

    def __setitem__(self, key, value):
        if key in self.keylist:
            if isinstance(key, str):
                dict.__setitem__(self, key, value)
            elif isinstance(key, eval(key)):
                super().__setitem__(key, value)
            elif key == 'Path':
                if value.__class__.__name__ in ['str', 'unicode']:  # makes it python 2 and python 3 compatible
                    if value:
                        if os.path.isabs(value):
                            filename = value
                        else:
                            filename = os.path.join(self.soft_path, value)
                        if not os.path.exists(filename):
                            str_issue = 'file: ' + str(filename) + ' does not exist.'
                            raise FileNotFoundError(str_issue)
                    else:
                        value = self.soft_path
                    dict.__setitem__(self, key, value)
            else:
                dict.__setitem__(self, key, value)

    def copy_values(self, input_dict):
        rewrite = False
        for key in input_dict:
            if key in self.keylist:
                if key == 'Parameters':
                    self[key] = Parameters(self.curr_bids.cwdir)
                    write = self[key].copy_values(input_dict[key])
                    if write:
                        rewrite = True
                else:
                    self[key] = input_dict[key]
            elif key in Parameters.get_list_subclasses_names():
                self[key] = eval(key+'()')
                write = self[key].copy_values(input_dict[key])
                if write:
                    rewrite = True
            else:
                self[key] = input_dict[key]
        return rewrite

    def read_json_parameter_file(self, soft_name):
        jsonfile = os.path.join(self.soft_path, soft_name + '.json')
        with open(jsonfile, 'r') as file:
            read_json = json.load(file)
            rewrite = self.copy_values(read_json)
        self.curr_path = self['Parameters'].check_presence_of_software(self['Path'])
        if self.curr_path.startswith('ERROR'):
            raise EOFError(self.curr_path)
        #check the validity of the json ??
        if not all(key in self.keys() for key in self.keylist):
            raise EOFError("JSON is not conform.")
        if rewrite:
            self.write_file(jsonfile)

    def set_everything_for_analysis(self, results):

        def list_for_str_format(order, idx):
            use_list = []
            for elt in order:
                if isinstance(elt, list):
                    if isinstance(elt[idx], list):
                        use_list.append(', '.join(elt[idx]))
                    else:
                        if elt[idx]:
                            use_list.append(elt[idx])
                else:
                    if elt and elt != '':
                        use_list.append(elt)
            return use_list

        perm, users, log_info = self.curr_bids.access.use_token_analyse(bids.BidsBrick.curr_user, self['Name'])
        if not perm:
            self.log_error += '{} don"t have permission to analyse data because {}.\n'.format(bids.BidsBrick.curr_user, log_info)
            return self.log_error, '', {}
        param_vars = {}
        res_outside = False
        for key in results['analysis_param']:
            if key[0].isdigit() and key[1] == '_':
                lab = key[2::]
            else:
                lab = key
            param_vars[lab] = results['analysis_param'][key]
        output_name = ''
        parameters_input = None
        try:
            # update the parameters and get the subjects
            self['Parameters'].update_values(param_vars, results['input_param'])
            if 'Input' in self['Parameters']:
                parameters_input = self['Parameters']['Input']
            #Verify the validity of the input value
            warn, err = verify_subject_has_parameters(self.curr_bids,
                                                          results['subject_selected'],
                                                          results['input_param'],
                                                      parameters_input)


            if warn:
                self.log_error += 'Warning {}:\n'.format(self['Name']) + warn
            if err:
                raise ValueError(err+warn)
            subject_to_analyse = SubjectToAnalyse(results['subject_selected'], input_dict=results['input_param'])
            participants = bids.ParticipantsProcessTSV()
            if 'derivatives_output' not in results:
                results['derivatives_output'] = []
            if 'local_output' not in results:
                results['local_output'] = []
            if not results['derivatives_output'] and not results['local_output']:
                output_directory, output_name, dataset_desc = self.curr_dev.create_pipeline_directory(self['Name'], param_vars, subject_to_analyse)
            elif results['local_output']:
                # Check in the output directory if the analysis doesnot exist
                output_directory, output_name, dataset_desc = check_pipeline_presence_locally(self['Name'], results['local_output'], param_vars, subject_to_analyse)
                res_outside = True
            else:
                output_name = results['derivatives_output']
                output_directory = os.path.join(self.cwdir, 'derivatives', output_name)
                dataset_desc = bids.DatasetDescPipeline(filename=os.path.join(output_directory, 'dataset_description.json'))
                participants.read_file(os.path.join(output_directory, 'participants.tsv'))

            ##Create the progression bar
            sg.theme('Light Grey 1')
            layout = [
                [sg.Text(self['Name'] + ' is running saved in ' +output_name, justification='center')],
                [sg.InputText(readonly=True, key='-INPUT-')],
                [sg.ProgressBar(max_value=200, orientation='h', size=(30, 20), key='progress')]
            ]
            window = sg.Window('Bids Pipeline: Progression bar', layout, finalize=True)
            # Check if the subjects have all the required values
            #self['Parameters'].write_file(output_directory)

            #dataset_desc['PipelineDescription']['fileLoc'] = os.path.join(output_directory, Parameters.filename)
            dataset_desc['PipelineDescription']['BIDSPipelineVersion'] = self.version
            dataset_desc.write_file(jsonfilename=os.path.join(output_directory, 'dataset_description.json'))

            #Get the value for the command_line
            cmd_arg, cmd_line, order, input_dict, output_dict, interm = self.create_command_to_run_analysis(output_directory, subject_to_analyse) #input_dict, output_dict
        except (EOFError, TypeError, ValueError, SystemError) as er:
            exc_type, exc_obj, exc_tb = exc_info()
            err_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.log_error += 'Error type: ' + str(exc_type) + ', scriptname: ' + err_name + ', line number, ' + str(
                exc_tb.tb_lineno) + ': ' + str(er)
            self.write_log()
            empty_dir, log_empty = self.curr_dev.empty_dirs(output_directory, rmemptysub=False)
            if empty_dir:
                shutil.rmtree(output_directory)
            window.close()
            return self.log_error, output_name, {}

        progress_bar = window['progress']
        progress_bar.UpdateBar(0)
        if not order:
            window['-INPUT-'].update('BIDS Pipeline cannot give the progression for this pipeline.')
            proc = subprocess.Popen(cmd_line, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            error_proc = proc.communicate()
            self.log_error += cmd_arg.verify_log_for_errors('', error_proc)
            self.write_json_associated(order, output_directory, cmd_arg)
            order_keys=None
        elif order:
            taille, idx_in, in_out, err_input = input_dict.get_input_values(subject_to_analyse, order)
            self.log_error += err_input
            if output_dict:
                output_dict.get_output_values(in_out, taille, order, output_directory, idx_in)  # sub
            ##To take into account the prefix and suffix in AnyWave
            if isinstance(cmd_arg, AnyWave):
                try:
                    warn, sub_tmp_dir = cmd_arg.copy_create_anywave_files_for_analysis(order, idx_in, in_out)
                    if warn:
                        self.log_error += 'Warning {}:\n'.format(self['Name']) + warn
                except Exception as er:
                    self.log_error += 'Error: ' + str(er)
                    self.write_log()
                    empty_dir, log_empty = self.curr_dev.empty_dirs(output_directory, rmemptysub=True)
                    if empty_dir:
                        shutil.rmtree(output_directory)
                    return self.log_error, output_name, {}

            ## Do the process by subject
            nbrtot = sum([taille[sub] for sub in taille])
            init =1
            for sub in in_out:
                window['-INPUT-'].update(sub + ' being analysed')
                idx = 0
                log_error = []
                while idx < taille[sub]:
                    use_list = list_for_str_format(in_out[sub], idx)
                    cmd = cmd_line.format(*use_list)
                    self.cmd_line_log.append(cmd)
                    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            universal_newlines=True)
                    error_proc = proc.communicate()
                    valueBar = round(init * 200 / nbrtot)
                    progress_bar.UpdateBar(valueBar)
                    self.log_error += cmd_arg.verify_log_for_errors(use_list, error_proc)
                    if error_proc[1]:
                        log_error.append(error_proc[1])
                    if not error_proc[1]:
                        self.write_json_associated(use_list, output_directory, cmd_arg)
                    else:
                        log_error.append(error_proc[1])
                    idx = idx + 1
                    init = init+1
                # if len(log_error) != taille[sub]:
                #     participants.append({'participant_id': sub})
                order_keys = [key for key in order]
            if isinstance(cmd_arg, AnyWave) and cmd_arg.move_files_refused:
                shutil.rmtree(sub_tmp_dir)
        else:
            self.log_error += datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S") + ': ' + 'ERROR: The analysis {0} could not be run due to an issue with the inputs and the outputs.\n'.format(self['Name'])
            self.write_log()
            window.close()
            return self.log_error, output_name, {}
        window.close()
        # Move back AnyWave files in the derivatives/anywave/username folder
        if isinstance(cmd_arg, AnyWave) and not cmd_arg.move_files_refused:
            handle_anywave_files(self.curr_bids.dirname, self.curr_bids.access, cmd_arg.curr_user, reverse=False, sublist=subject_to_analyse['sub'])
        # Check that the output_directory is not empty and update the specific files
        empty_dir, log_empty = self.curr_dev.empty_dirs(output_directory, rmemptysub=True)
        if not empty_dir or (empty_dir and bids.BidsBrick.curr_user not in dataset_desc['Authors']):
            #remove the empty directory
            sub_analysed = [sub.split('-')[1] for sub in os.listdir(output_directory) if sub.startswith('sub')]
            sub2remove = [sub for sub in subject_to_analyse['sub'] if sub not in sub_analysed]
            for subid in sub2remove:
                subject_to_analyse.remove(subid)
                self.log_error += 'The {} subject has finally not be analysed.\n'.format(subid)
            participants.update_after_analysis(sub_analysed, sub2remove)
            participants.write_file(tsv_full_filename=os.path.join(output_directory, bids.ParticipantsTSV.filename))
            dataset_desc.update(subject_to_analyse, sub2remove, sub_analysed, order_keys=order_keys)
            dataset_desc.write_file(jsonfilename=os.path.join(output_directory, bids.DatasetDescPipeline.filename))
            try:
                go_throught_dir_to_convert(output_directory)
            except:
                pass
            if not res_outside:
                self.curr_dev.parse_pipeline(output_directory, output_name)
                self.curr_bids.save_as_json()
            temp = self.write_analysis_done_log(dataset_desc, filename=os.path.join(output_directory, Parameters.filename))
        else:
            self.log_error += datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S") + ': ' + 'Warning: The folder {0} has no results so your analysis may not succeed. The folder {0} will be erased.\n'.format(output_name)
            shutil.rmtree(output_directory)

        self.write_log()
        self.write_command_line_log()
        file_to_write = self.write_analysis_done_log(dataset_desc)
        return self.log_error, output_name, file_to_write

    def create_command_to_run_analysis(self, output_directory, subject_to_analyse):
        #Take the mode into account for now, only automatic
        interm = None
        cmd_line_set = None
        callname = self['Parameters']['Callname']
        mode = self['Parameters']['Mode'][-1]
        input_p = None
        output_p = None
        if 'command_line_base' in self['Parameters'].keys():
            cmd_line_set = self['Parameters']['command_line_base']
        if 'Intermediate' in self['Parameters'].keys():
            interm = self['Parameters']['Intermediate']

        if interm:
            cmd_arg = eval(interm + '(curr_path=self.curr_path, dev_path=output_directory, callname=callname, subject_to_analyse=subject_to_analyse)') #'(bids_directory="'+self.cwdir+'", curr_path="'+self.curr_path+'", dev_path="'+output_directory+'", callname="'+callname+'")')
        else:
            cmd_arg = Parameters(curr_path=self.curr_path, dev_path=output_directory, callname=callname, subject_to_analyse=subject_to_analyse)

        for key in self['Parameters']:
            if isinstance(self['Parameters'][key], Arguments):
                self['Parameters'][key].command_arg(key, cmd_arg, subject_to_analyse)
            elif key == 'Input':
                input_p = Input()
                input_p.copy_values(self['Parameters'][key])
                cmd_arg['Input'] = ''
            elif key == 'Output':
                output_p = Output()
                output_p.copy_values(self['Parameters'][key])
                output_p.bids_directory = self.cwdir
                cmd_arg['Output'] = ''

        cmd_line, order = cmd_arg.command_line_base(cmd_line_set, mode, output_directory, input_p, output_p)#, input_dict, output_dict)
        #order.multiplesubject = input_p[0]['MultipleSubjects]
        return cmd_arg, cmd_line, order, input_p, output_p, interm

    def write_json_associated(self, inout_file, output_directory, analyse):
        def create_json(input_file, output_json, analyse):
            jsonf = bids.BidsJSON()
            jsonf['Description'] = 'Results of ' + self['Name'] + ' analysis.'
            jsonf['RawSources'] = input_file
            jsonf['Parameters'] = analyse
            jsonf['Authors'] = getpass.getuser()
            jsonf['Date'] = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            jsonf.write_file(output_json)

        output_fin = None
        input_file = None
        for elt in inout_file:
            if output_directory in elt:
                output_fin = elt
            else:
                input_file = elt

        if not output_fin:
            pass
        elif os.path.isfile(output_fin):
            filename, ext = os.path.splitext(output_fin)
            output_json = output_fin.replace(ext, bids.BidsJSON.extension)
            if os.path.exists(output_json):
                pass
            else:
                create_json(input_file, output_json, analyse)
        elif os.path.isdir(output_fin):
            if input_file:
                filename = os.path.basename(input_file)
                filename, ext = os.path.splitext(filename)
                modality = os.path.basename(output_fin)
                filename = filename.replace(modality, '')
                potential_file = [entry for entry in os.listdir(output_fin) if entry.startswith(filename)]
                is_json = False
                for it in potential_file:
                    if it.endswith(bids.BidsJSON.extension):
                        is_json = True
                if not is_json and potential_file:
                    filename, ext = os.path.splitext(potential_file[-1])
                    if ext:
                        output_file = potential_file[-1].replace(ext, bids.BidsJSON.extension)
                    else:
                        output_file = 'analysis_information.json'
                    output_json = os.path.join(output_fin, output_file)
                    create_json(input_file, output_json, analyse)
            else:
                for entry in os.listdir(output_fin):
                    if os.path.isfile(os.path.join(output_fin, entry)):
                        filename, ext = os.path.splitext(entry)
                        if not (filename.startswith('dataset_description') or filename.startswith(
                                'log_error_analyse') or filename.startswith('participants')):
                            potential_file = [entry for entry in os.listdir(output_fin) if entry.startswith(filename)]
                            is_json = False
                            for it in potential_file:
                                if it.endswith(bids.BidsJSON.extension):
                                    is_json = True
                            if not is_json:
                                filename, ext = os.path.splitext(potential_file[-1])
                                output_file = potential_file[-1].replace(ext, bids.BidsJSON.extension)
                                output_json = os.path.join(output_fin, output_file)
                                create_json('', output_json, analyse)

    def write_file(self, filename):
        with open(filename, 'w+') as f:
            json_str = json.dumps(self, indent=1, separators=(',', ': '), ensure_ascii=False, sort_keys=False)
            f.write(json_str)

    def write_log(self):
        log_dir = os.path.join(self.curr_dev.bp_folder, 'log')
        os.makedirs(log_dir, exist_ok=True)
        time_format = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        log_filename = 'bids-pipeline_' + time_format + '.log'
        try:
            with open(os.path.join(log_dir, log_filename), 'w+') as file:
                file.write(self.log_error + '\n')
        except MemoryError:
            with open(os.path.join(log_dir, log_filename), 'w+') as file:
                file.write('The log is too big to be written.\n')

    def write_command_line_log(self):
        log_dir = os.path.join(self.curr_dev.bp_folder, 'command_line')
        os.makedirs(log_dir, exist_ok=True)
        time_format = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        log_filename = self['Name'] + '_' + time_format + '.log'
        with open(os.path.join(log_dir, log_filename), 'w+') as file:
            file.write('\n'.join(self.cmd_line_log) + '\n')

    def write_analysis_done_log(self, dataset_desc, filename=None):
        file_to_write = {key: '' for key in
                         ['analysis_param', 'subject_selected', 'input_param', 'Software', 'SoftwareVersion',
                          'JsonName']}
        # Voir comment gérer Software version
        file_to_write['JsonName'] = self.jsonfilename
        author = dataset_desc['Authors']
        name = dataset_desc['Name'].split('-')[0]
        file_to_write['Software'] = name
        if author is None or author == '':
            author = getpass.getuser()
        elif isinstance(author, list):
            author = '-'.join(author)
        if author == 'n/a':
            author = getpass.getuser()
        date = dataset_desc['Date']
        if date is None or date == '' or date == 'n/a':
            date = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        date.replace(' ', 'T')
        if not filename:
            analysis_dir = os.path.join(self.curr_dev.bp_folder, 'analysis_done')
            os.makedirs(analysis_dir, exist_ok=True)
            filename = name +'_' + author + '_' + date + '.json'
            filename = os.path.join(analysis_dir, filename)
        file_to_write['analysis_param'] = dataset_desc['PipelineDescription']
        for key, value in dataset_desc['SourceDataset'].items():
            if key == 'sub':
                file_to_write['subject_selected'] = value
            else:
                if not isinstance(file_to_write['input_param'], dict):
                    file_to_write['input_param'] = {}
                file_to_write['input_param'][key] = value
        with open(filename, 'w+') as file:
            json_str = json.dumps(file_to_write, indent=1, separators=(',', ': '), ensure_ascii=False, sort_keys=False)
            file.write(json_str)
        return file_to_write


class Parameters(dict):
    keylist = ['command_line_base', 'Intermediate', 'Callname']
    analyse_type = []
    analyse_type = None
    derivatives_directory = None
    bids_directory = None
    callname = None
    curr_path = None
    curr_bids = None
    mtg_file = None
    arg_readbids = []
    filename = 'BP_parameters_file.json'

    def __init__(self, curr_path=None, dev_path=None, callname=None, subject_to_analyse=None):
        if dev_path:
            self.derivatives_directory = dev_path
        if callname:
            self.callname = callname
        if curr_path:
            self.curr_path = curr_path

    def keys_standardization(self, input_dict):
        log = ''
        new_dict = {}
        if isinstance(self, InputArguments):
            all_keys = InputArguments.keylist + InputArguments.keylist_deriv
        elif isinstance(self, Arguments):
            all_keys = Arguments.unit_value + Arguments.read_value + Arguments.list_value + Arguments.file_value + Arguments.bool_value + Arguments.bids_value
        elif isinstance(self, Output):
            all_keys = Output.keylist
        all_lower = [elt.lower() for elt in all_keys]
        for key in input_dict:
            new_key = key.replace('_', '').replace('-', '')
            if new_key == 'multiplesubject':
                new_key = 'MultipleSubjects'
                new_dict[new_key] = input_dict[key]
            elif new_key == 'combinationmode':
                new_key = 'CombinationMode'
                new_dict[new_key] = input_dict[key]
            else:
                try:
                    idx = all_lower.index(new_key.lower())
                    new_key = all_keys[idx]
                    new_dict[new_key] = input_dict[key]
                except:
                    log += key + ' '
        return new_dict, log

    def copy_values(self, input_dict):
        rewrite = False
        for key in input_dict:
            if key in self.keylist:
                self[key] = input_dict[key]
            elif key in ParametersSide.get_list_subclasses_names() + Parameters.get_list_subclasses_names():
                self[key] = eval(key + '()')
                write = self[key].copy_values(input_dict[key])
                if write:
                    rewrite = True
            else:
                self[key] = Arguments()
                readbids, write = self[key].copy_values(input_dict[key])
                if readbids:
                    self.arg_readbids.append(readbids)
                if write:
                    rewrite = True
        return rewrite

    def update_values(self, input_dict, input_param=None):
        keylist = list(self.keys())
        for key in input_dict:
            if key in keylist:
                self[key].update_values(input_dict[key])
            else:
                new_key, *tag = key.split('_')
                if isinstance(tag, list):
                    tag = '_'.join(tag)
                self[new_key].update_values(input_dict[key], tag)
        if input_param:
            input_tag = []
            for cn, elt in enumerate(self['Input']):
                if elt['Tag']:
                    input_tag.append(elt['Tag'])
                else:
                    input_tag.append('in'+str(cn))
            for inp in input_param:
                inp_tag = inp.split('Input_')[1]
                if inp_tag in input_tag:
                    idx = input_tag.index(inp_tag)
                    self['Input'][idx].update_values(input_param[inp])

    def check_presence_of_software(self, curr_path):
        def type_of_software(name, intermediaire):
            if not intermediaire:
                ext = '.exe'
            elif intermediaire == 'Docker':
                ext = ''
                name = ''
            elif intermediaire == 'Python':
                ext = '.py'
            elif intermediaire == 'Matlab':
                ext = '.m'
            elif intermediaire == 'AnyWave':
                ext = '.exe'
                name = 'AnyWave'
            return name, ext

        def select_pipeline_path(name, ext):
            if platform.system() == 'Windows':
                ask_file_options = {'filetypes': [('files', ext)]}
            elif platform.system() == 'Linux':
                ask_file_options = dict()
            messagebox.showerror('PathError', 'The current pipeline path is not valid.\n'
                                              'Please select module path/location (e.g. .exe, .m, etc)')
            filename = filedialog.askopenfilename(title='Please select ' + name + ' file', **ask_file_options)
            if not name in filename:
                messagebox.showerror('PathError', 'The selected file is not the good one for this pipeline')
                return 'ERROR: The path is not valid'

            return filename

        interm = None
        if 'Intermediate' in self.keys():
            if self['Intermediate'].lower() == 'anywave':
                self['Intermediate'] = 'AnyWave'
            interm = self['Intermediate']
        name, ext = type_of_software(self['Callname'], interm)
        if not name:
            return ''
        if curr_path:
            if not os.path.exists(curr_path):
                curr_path = select_pipeline_path(name, ext)
            elif not name in curr_path:
                curr_path = select_pipeline_path(name, ext)
        else:
            curr_path = select_pipeline_path(name, ext)
        return curr_path

    def command_arg(self, key, cmd_dict, subject_list):
        if 'InCommandLine' in self.keys():
            if self['InCommandLine']:
                if 'ValueSelected' in self.keys():
                    cmd_dict[key] = self['ValueSelected']
                else:
                    cmd_dict[key] = self['Default']
            else:
                if 'ValueSelected' not in self.keys():
                    self['ValueSelected'] = self['Default']
                if self['ValueSelected']:
                    cmd_dict[key] = ''
        elif 'ValueSelected' in self.keys():
            # if isinstance(self['ValueSelected], list):
            #     cmd_dict[key] = ', '.join(self['ValueSelected])
            # else:
            cmd_dict[key] = self['ValueSelected']
        # elif 'default' in self.keys():
        #     if self['default']:
        #         cmd_dict[key] = self['default']
        elif 'ReadBids' in self.keys():
            type_value = None
            for clef in subject_list.keys():
                if clef == self['Type']:
                    type_value = subject_list[self['Type']]
                elif isinstance(subject_list[clef], dict):
                    type_value = []
                    for elt in subject_list[clef]:
                        if elt == self['Type']:
                            type_value.extend(subject_list[clef][self['Type']])
                if type_value:
                    cmd_dict[key] = type_value
                elif type_value is None and self['Type'] == 'file':
                    cmd_dict[key] = ''

    def command_line_base(self, cmd_line_set, mode, output_directory, input_p, output_p):
        if not cmd_line_set:
            cmd_base = self.curr_path
        else:
            cmd_base = self.curr_path + cmd_line_set

        cmd_line, order = self.chaine_parameters(output_directory, input_p, output_p)
        cmd = cmd_base + cmd_line
        return cmd, order

    def chaine_parameters(self, output_directory, input_dict, output_dict):
        cmd_line =''
        cnt_tot = 0
        order = {}
        for clef in self:
            if clef == 'Input':
                for cn, elt in enumerate(input_dict):
                    tag_val = elt['Tag']
                    if not elt['Tag']:
                        tag_val = 'in' + str(cn)
                    if elt['MultipleSubjects'] and elt['Type'] == 'dir':
                        if not elt.deriv_input:
                            cmd_line += ' ' + elt['Tag'] + ' ' + self.bids_directory
                        elif elt.deriv_input and (elt['DerivFolder'] and elt['DerivFolder'] != ['']):
                            cmd_line += ' ' + elt['Tag'] + ' ' + os.path.join(self.bids_directory, 'derivatives', elt['DerivFolder'][0])
                    else:
                        if elt.deriv_input:
                            if (not elt['DerivFolder'] or elt['DerivFolder'] == ['']) and not elt['Optional']:
                                raise ValueError('The derivative folder for this paramater {} should be mentionned.\n'.format(elt['Tag']))
                            elif elt['DerivFolder'] != [''] and elt['DerivFolder']:
                                order[tag_val] = cnt_tot
                                cmd_line += ' ' + elt['Tag'] + ' {' + str(cnt_tot) + '}'
                                cnt_tot += 1
                        else:
                            order[tag_val] = cnt_tot
                            cmd_line += ' ' + elt['Tag'] + ' {' + str(cnt_tot) + '}'
                            cnt_tot += 1
            elif clef == 'Output':
                if output_dict['MultipleSubjects'] and output_dict['Directory']:
                    cmd_line += ' ' + output_dict['Tag'] + ' ' + output_directory
                else:
                    if not output_dict['Tag']:
                        order['out'] = cnt_tot
                    else:
                        order[output_dict['Tag']] = cnt_tot
                    cmd_line += ' ' + output_dict['Tag'] + ' {' + str(cnt_tot) + '}'
                    cnt_tot += 1
                #cmd_line += determine_input_output_type(output_dict, cnt_tot, order)
                #order.append(output_dict)
            elif isinstance(self[clef], bool):
                cmd_line += ' ' + clef + ' ' + '{}'.format(self[clef])
            elif isinstance(self[clef], int) or isinstance(self[clef], float):
                cmd_line += ' ' + clef + ' ' + '{}'.format(self[clef])
            elif isinstance(self[clef], list):
                if len(self[clef]) == 1:
                    cmd_line += ' ' + clef + ' ' + self[clef][0]
                elif all(isinstance(elt, str) for elt in self[clef]):
                    cmd_line += ' ' + clef + ' "' + ', '.join(self[clef]) + '"'
                else:
                    cmd_temp = ' ' + clef + ' "'
                    for n, elt in enumerate(self[clef]):
                        if isinstance(elt, str):
                            cmd_temp += elt
                        else:
                            cmd_temp += '{}'.format(elt)
                        if n < len(cmd_line) - 1:
                            cmd_temp += ', '
                    cmd_temp += '"'
                    cmd_line += cmd_temp
            else:
                cmd_line += ' ' + clef + ' ' + self[clef]
        return cmd_line, order

    def verify_log_for_errors(self, input, x):
        log_error = ''
        if isinstance(x, tuple):
            if not x[0] and not x[1]:
                log_error += datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S") + ': ' + ' '.join(input) + ' has been analyzed with no error\n'
            elif not x[1]:
                log_error += datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S") + ': ' + ' '.join(input) + ': '+ x[0] + '\n'
            else:
                log_error += datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S") + ': ERROR: ' + ' '.join(input)+ ': ' + x[1] + '\n'

        return log_error

    def write_file(self, output_directory):
        filename = os.path.join(output_directory, self.filename)
        with open(filename, 'w+') as f:
            json_str = json.dumps(self, indent=1, separators=(',', ': '), ensure_ascii=False, sort_keys=False)
            f.write(json_str)

    #Fonction wrote by Nicolas Roehri
    @classmethod
    def get_list_subclasses_names(cls):
        sub_classes_names = []
        for subcls in cls.__subclasses__():
            sub_classes_names.append(subcls.__name__)
            sub_classes_names.extend(subcls.get_list_subclasses_names())
        return sub_classes_names

    @classmethod
    def _assign_bids_dir(cls, bids_dir, curr_bids):
        cls.bids_directory = bids_dir
        cls.curr_bids = curr_bids
        PipelineSetting.cwdir = bids_dir


class AnyWave(Parameters):
    anywave_directory = None
    move_files_refused=False
    curr_user = None
    anywave_folder_user = None
    anywave_folder_common = None

    def __init__(self, curr_path=None, dev_path=None, callname=None, subject_to_analyse=None):
        self.curr_user = bids.BidsBrick.curr_user
        if dev_path:
            self.derivatives_directory = dev_path
        if callname:
            self.callname = callname
        if curr_path:
            self.curr_path = curr_path
        home = os.path.expanduser('~')
        self.anywave_directory = os.path.join(home, 'AnyWave', 'Log')
        os.makedirs(self.anywave_directory, exist_ok=True)
        ## Initiate anywave folder
        self.anywave_folder_user = os.path.join(bids.BidsDataset.dirname, 'derivatives', 'anywave', self.curr_user)
        self.anywave_folder_common = os.path.join(bids.BidsDataset.dirname, 'derivatives', 'anywave', 'common')
        ## Check the access to see if user can move files
        perm, is_used_by, info = self.curr_bids.access.use_token_analyse(self.curr_user, soft=self.callname)
        if (perm and not self.curr_bids.access[self.curr_user]['permission'] == 'full') or (perm and is_used_by):
            self.move_files_refused = True

    def command_line_base(self, cmd_line_set, mode, output_directory, input_p, output_p):
        self['plugin'] = self.callname
        cmd_end = ''
        if not cmd_line_set:
            cmd_line_set = ' --run'# + self.callname
        cmd_base = self.curr_path + cmd_line_set

        cmd_line, order = self.chaine_parameters(output_directory, input_p, output_p)
        cmd = cmd_base + cmd_line + ' --log_dir ' + self.anywave_directory
        return cmd, order

    def chaine_parameters(self, output_directory, input_dict, output_dict):
        jsonfilename = os.path.normpath(os.path.join(self.derivatives_directory, self.callname + '_parameters' + '.json'))
        pref_flag = False
        suff_flag = False
        mtg_flag = False
        if 'Input' in self.keys():
            del self['Input']
        if 'Output' in self.keys():
            del self['Output']
        if 'output_prefix' in self.keys() or 'output_file' in self.keys():
            if 'output_prefix' in self.keys():
                pref_tag = '--output_prefix'
            else:
                pref_tag = '--output_file'
            pref_flag = True
            del self[pref_tag.replace('--', '')]
        if 'output_suffix' in self.keys():
            suff_flag = True
            del self['output_suffix']
        if 'montage_file' in self.keys() and self['montage_file'] not in ['bipolar_ieeg', 'None']:
            mtg_flag = True
            self.mtg_file = self['montage_file']
            del self['montage_file']
        with open(jsonfilename, 'w') as json_file:
            if 'modality' in self and isinstance(self['modality'], list):
                self['modality'] = self['modality'][-1]
                if self['modality'] == 'Ieeg':
                    self['modality'] = 'SEEG'
                self['modality'] = self['modality'].upper()
            json.dump(self, json_file)
        cmd_line = ' ' + jsonfilename

        order = {}
        #Handle the input and output
        cnt_tot = 0
        for cn, elt in enumerate(input_dict):
            tag_val = elt['Tag']
            if not elt['Tag']:
                tag_val = 'in' + str(cn)
            if elt['MultipleSubjects'] and elt['Type'] == 'dir':
                if not elt.deriv_input:
                    cmd_line += ' ' + elt['Tag'] + ' ' + self.bids_directory
                elif elt.deriv_input and (elt['DerivFolder'] and elt['DerivFolder'] != ['']):
                    cmd_line += ' ' + elt['Tag'] + ' ' + os.path.join(self.bids_directory, 'derivatives',
                                                                      elt['DerivFolder'][0])
            else:
                if elt.deriv_input:
                    if (elt['DerivFolder'] == [''] or not elt['DerivFolder']) and not elt['Optional']:
                        raise ValueError(
                            'The derivative folder for this paramater {} should be mentionned.\n'.format(elt['Tag']))
                    elif elt['DerivFolder'] != [''] and elt['DerivFolder']:
                        order[tag_val] = cnt_tot
                        cmd_line += ' ' + elt['Tag'] + ' {' + str(cnt_tot) + '}'
                        cnt_tot += 1
                else:
                    order[tag_val] = cnt_tot
                    cmd_line += ' ' + elt['Tag'] + ' {' + str(cnt_tot) + '}'
                    cnt_tot += 1
        if output_dict is not None:
            if output_dict['MultipleSubjects'] and output_dict['Directory']:
                cmd_line += ' ' + output_dict['Tag'] + ' ' + output_directory
            else:
                if not output_dict['Tag']:
                    order['out'] = cnt_tot
                else:
                    order[output_dict['Tag']] = cnt_tot
                cmd_line += ' ' + output_dict['Tag'] + ' {' + str(cnt_tot) + '}'
                cnt_tot += 1
        if pref_flag:
            order[pref_tag] = cnt_tot
            cmd_line += ' ' + pref_tag + ' {' + str(cnt_tot) + '}'
            cnt_tot += 1
        if suff_flag:
            order['--output_suffix'] = cnt_tot
            cmd_line += ' --output_suffix {' + str(cnt_tot) + '}'
            cnt_tot += 1
        if mtg_flag:
            order['montage_file'] = cnt_tot
            cmd_line += ' --montage_file {' + str(cnt_tot) + '}'
            cnt_tot +=1
        return cmd_line, order

    def verify_log_for_errors(self, input, x=None):
        log_error = ''
        # read log in Documents
        # home = os.path.expanduser('~')
        # if getpass.getuser() == 'jegou':
        #     self.anywave_directory = r'Z:\AnyWave\Log'
        # else:
        #     self.anywave_directory = os.path.join(home, 'AnyWave', 'Log')
        #     if not os.path.exists(self.anywave_directory):
        #         self.anywave_directory = os.path.join('\\dynaserv', 'home', getpass.getuser(), 'AnyWave', 'Log')
        temp_time = 0
        filename =''
        if os.path.exists(self.anywave_directory):
            with os.scandir(self.anywave_directory) as it:
                for entry in it:
                    time_file = os.path.getctime(entry)
                    if time_file > temp_time:
                        temp_time = time_file
                        filename = entry.path
            if os.path.exists(filename):
                f = open(filename, 'r')
                f_cont = f.readlines()
                for elt in f_cont:
                    log_error += elt
                f.close()
            else:
                log_error += 'The AnyWave log path was not found.\n'
        else:
            log_error += 'The AnyWave log path was not found.\n'

        return log_error

    def copy_create_anywave_files_for_analysis(self, order, idx_in, in_out):
        warning = ''
        if self.move_files_refused:
            tmp_dir = tempfile.gettempdir()
            curr_time = datetime.datetime.now().strftime('%d%m%Y-%H%M')
            sub_tmp_dir = os.path.join(tmp_dir, 'BP_anywave_'+curr_time)
            os.makedirs(sub_tmp_dir, exist_ok=True)
        ## Move anywave files
        for sub in in_out:
            for id_in in idx_in:
                get_specific_montage = False
                get_specific_prefix = False
                ## create the suffix for the outputs
                if '--output_file' in order or '--output_prefix' in order:
                    pref_tag = [elt for elt in order if elt in ['--output_prefix', '--output_file']][0]
                    if not in_out[sub][order[pref_tag]]:
                        in_out[sub][order[pref_tag]] = []
                        get_specific_prefix = True
                ## specific montage
                if 'montage_file' in order:
                    if not in_out[sub][order['montage_file']]:
                        in_out[order['montage_file']] = []
                        get_specific_montage = True
                ## Get the other anywave files
                for in_idx, file in enumerate(in_out[sub][id_in]):
                    isFileMeg = False
                    if "c,rfDC" in file:
                        file = os.path.dirname(file)
                        isFileMeg = True
                    sub_dir = file.split(self.bids_directory)
                    sub_dirname = [elt for elt in sub_dir[1].split(os.sep) if elt != '']
                    sub_anywave_file_user = os.path.join(self.anywave_folder_user, os.sep.join(sub_dirname))
                    sub_anywave_file_common = os.path.join(self.anywave_folder_common, os.sep.join(sub_dirname))
                    dirname, filename = os.path.split(file)
                    file_elt = filename.split('_')
                    modalitytype = file_elt[-1].split('.')

                    ## If don't have permission, have to move the eeg files in tmp dir
                    if not self.move_files_refused:
                        tmp_dir = os.path.dirname(sub_dir[1])
                        tmp_dir_elt = tmp_dir.split(os.sep)
                        if '' in tmp_dir_elt:
                            idv = tmp_dir_elt.index('')
                            del tmp_dir_elt[idv]
                        sub_tmp_dir_write = os.path.join(self.bids_directory, os.sep.join(tmp_dir_elt))
                        if isFileMeg:
                            sub_tmp_dir_write  = os.path.join(sub_tmp_dir_write , '_'.join(file_elt))
                    else:
                        # copy the entry
                        new_entry = os.path.join(sub_tmp_dir, filename)
                        if os.path.isdir(file):
                            shutil.copytree(file, new_entry)
                            sub_tmp_dir_write = os.path.join(sub_tmp_dir, '_'.join(file_elt))
                        else:
                            shutil.copy2(file, new_entry)
                            sub_tmp_dir_write =sub_tmp_dir
                        if isFileMeg:
                            in_out[sub][id_in][in_idx] = os.path.join(new_entry, "c,rfDC")
                        else:
                            in_out[sub][id_in][in_idx] = new_entry
                        # have to move the eeg and the vmrk too
                        if filename.endswith('.vhdr'):
                            vmrkfile = filename.replace('.vhdr', '.vmrk')
                            tmp_dir2copy = os.path.dirname(file)
                            shutil.copy2(os.path.join(tmp_dir2copy, vmrkfile), os.path.join(sub_tmp_dir_write, vmrkfile))
                            eegfile = filename.replace('.vhdr', '.eeg')
                            if not os.path.exists(os.path.join(tmp_dir2copy, eegfile)):
                                eegfile = filename.replace('.vhdr', '.dat')
                            shutil.copy2(os.path.join(tmp_dir2copy, eegfile), os.path.join(sub_tmp_dir_write, eegfile))

                    if get_specific_prefix:
                        new_file = '_'.join(file_elt[0:len(file_elt) - 1])
                        in_out[sub][order[pref_tag]].append(new_file)
                    if get_specific_montage:
                        listing = os.listdir(dirname)
                        file_mtg = [fi for fi in listing if self.mtg_file in fi and fi.endswith('_montage.mtg')]
                        if len(file_mtg) < 1 or len(file_mtg) > 1:
                            # raise EOFError('There is {0} montage file with the type {1}.'.format(len(file_mtg), mtg_type))
                            warning += 'There is no montage file for analysis {}. The montage from teh patient will be used.\n'.format(
                                filename)
                            # in_out[sub][order['montage_file']].append('bipolar_ieeg')
                        else:
                            if self.move_files_refused:
                                filename = file_mtg[0]
                                filename_mtg = os.path.join(sub_tmp_dir_write, filename)
                                shutil.copy2(file_mtg[0], filename_mtg)
                            else:
                                filename_mtg = os.path.join(dirname, file_mtg[0])
                            in_out[sub][order['montage_file']].append(filename_mtg)
                    if 'DerivFolder' not in idx_in[id_in].keys():
                        for cnt, ext in enumerate(anywave_ext_analysis):
                            if os.path.exists(sub_anywave_file_user + ext):
                                shutil.copy(sub_anywave_file_user + ext, os.path.join(sub_tmp_dir_write, file + ext))
                            elif os.path.exists(sub_anywave_file_common + ext):
                                shutil.copy(sub_anywave_file_common + ext, os.path.join(sub_tmp_dir_write, file + ext))
                            else:
                                if cnt == 1:
                                    eventfile = os.path.join(dirname, '_'.join(file_elt[0:-1]) + '_events.tsv')
                                    mrkfile = os.path.join(dirname, filename.replace('.vhdr', '.vmrk'))
                                    if os.path.exists(eventfile):
                                        err = convert_events_in_marker_file(eventfile, modalitytype[0], sub_tmp_dir_write)
                                        if err:
                                            warning = warning + err
                                    elif os.path.exists(mrkfile):
                                        err = convert_events_in_marker_file(mrkfile, modalitytype[0], sub_tmp_dir_write)
                                        if err:
                                            warning = warning + err
                                elif cnt == 2 and not get_specific_montage:
                                    channelfile = os.path.join(dirname, '_'.join(file_elt[0:-1]) + '_channels.tsv')
                                    if os.path.exists(channelfile):
                                        err = convert_channels_in_montage_file(channelfile, modalitytype[0], sub_tmp_dir_write)
                                        if err:
                                            warning = warning + err
        if not self.move_files_refused:
            sub_tmp_dir = None

        return warning, sub_tmp_dir


class Docker(Parameters):
    keylist = ['command_line_base', 'Intermediate', 'Callname']

    def __init__(self, curr_path=None, dev_path=None, callname=None, subject_to_analyse=None):
        super().__init__(curr_path=curr_path, dev_path=dev_path, callname=callname)
        out_docker = subprocess.check_output("docker -v", shell=True)
        out_docker = out_docker.decode("utf-8")
        if not out_docker.startswith('Docker version'):
            raise SystemError('Docker is not installed on your computer.\n Please install docker before to continue.\n')

    def command_line_base(self, cmd_line_set, mode, output_directory, input_p, output_p):
        os.system('docker pull ' + self.callname)
        if not cmd_line_set:
            cmd_line_set = 'docker run -ti --rm'
        #should change outputs in derivatives normally
        cmd_base = cmd_line_set + ' -v ' + self.bids_directory + ':/bids_dataset:ro -v ' + self.derivatives_directory + ':/outputs ' + self.callname + ' /bids_dataset /outputs'

        cmd_line, order = self.chaine_parameters(input_p, output_p)
        cmd = cmd_base + cmd_line
        return cmd, order

    def chaine_parameters(self, input_dict, output_dict):
        cmd_line = ''
        cnt_tot = 0
        order = {}
        for clef in self:
            if isinstance(self[clef], bool):
                cmd_line += ' ' + clef
            elif isinstance(self[clef], list):
                if len(self[clef]) > 1:
                    if all(isinstance(elt, str) for elt in self[clef]):
                        value = ' '.join(self[clef])
                    else:
                        value = ''
                        for n, elt in enumerate(self[clef]):
                            if isinstance(elt, str):
                                value += elt
                            else:
                                value += '{}'.format(elt)
                            if n < len(cmd_line) - 1:
                                value += ', '
                    cmd_line += ' ' + clef + ' [' + value + ']'
                else:
                    value = self[clef][0]
                    cmd_line += ' ' + clef + ' ' + value
            elif isinstance(self[clef], int) or isinstance(self[clef], float):
                cmd_line += ' ' + clef + ' ' + '{}'.format(self[clef])
            else:
                cmd_line += ' ' + clef + ' ' + self[clef]
        return cmd_line, order


class Matlab(Parameters):

    def command_line_base(self, cmd_line_set, mode, output_directory, input_p, output_p):
        cmd_end = ''
        if platform.system() == 'Windows':
            base = "matlab -wait"
        elif platform.system() == "Linux":
            base = "matlab"
        if mode == 'automatic':
            if not cmd_line_set:
                cmd_line_set = base + " -nosplash -nodesktop -r \"cd('" + os.path.dirname(self.curr_path) + "'); "
            cmd_end = '; exit\"'
        elif mode == 'manual':
            if not cmd_line_set:
                cmd_line_set = base + " -nosplash -nodesktop -r \"cd('" + os.path.dirname(self.curr_path) + "'); "
        cmd_base = cmd_line_set + self.callname

        cmd_line, order = self.chaine_parameters(output_directory, input_p, output_p)
        cmd = cmd_base + cmd_line + cmd_end
        return cmd, order

    def chaine_parameters(self, output_directory, input_dict, output_dict):
        cmd_line = []
        cnt_tot = 0
        order = {}

        for clef in self:
            if clef == 'Input':
                for cn, elt in enumerate(input_dict):
                    tag_val = elt['Tag']
                    if not elt['Tag']:
                        tag_val = 'in' + str(cn)
                    if elt['MultipleSubjects'] and elt['Type'] == 'dir':
                        if elt['Tag']:
                            cmd_line.append("'" + elt['Tag'] + "'")
                        if not elt.deriv_input:
                            cmd_line.append("'" + self.bids_directory + "' ")
                        elif elt.deriv_input and (elt['DerivFolder'] and elt['DerivFolder'] != ['']):
                            cmd_line.append("'" + os.path.join(self.bids_directory, 'derivatives',
                                                                              elt['DerivFolder'][0]) + "' ")
                    else:
                        if elt.deriv_input:
                            if (elt['DerivFolder'] == [''] or not elt['DerivFolder']) and not elt['Optional']:
                                raise ValueError(
                                    'The derivative folder for this paramater {} should be mentionned.\n'.format(
                                        elt['Tag']))
                            elif elt['DerivFolder'] != [''] and elt['DerivFolder']:
                                order[tag_val] = cnt_tot
                                if elt['Tag']:
                                    cmd_line.append("'" + elt['Tag'] + "'")
                                cmd_line.append("'{" + str(cnt_tot) + "}'")
                                cnt_tot += 1
                        else:
                            order[tag_val] = cnt_tot
                            if elt['Tag']:
                                cmd_line.append("'" + elt['Tag'] + "'")
                            cmd_line.append("'{" + str(cnt_tot) + "}'")
                            cnt_tot += 1
            elif clef == 'Output':
                if output_dict['MultipleSubjects'] and output_dict['Directory']:
                    if output_dict['Tag']:
                        cmd_line.append("'"+output_dict['Tag']+"'")
                    cmd_line.append("'" + output_directory + "'")
                else:
                    if not output_dict['Tag']:
                        order['out'] = cnt_tot
                    else:
                        order[output_dict['Tag']] = cnt_tot
                        cmd_line.append("'"+output_dict['Tag']+"'")
                    cmd_line.append("'{" + str(cnt_tot) + "}'")
                    cnt_tot += 1
            elif isinstance(self[clef], list):
                cmd_line.append("'"+clef+"'")
                value = ', '.join(self[clef])
                cmd_line.append("'" + value + "'")
            elif isinstance(self[clef], int) or isinstance(self[clef], float):
                cmd_line.append("'"+clef+"'")
                if isinstance(self[clef], bool):
                    self[clef] = int(self[clef])
                cmd_line.append(self[clef])
            else:
                cmd_line.append("'" + clef + "'")
                if self[clef].isnumeric():
                    self[clef] = int(self[clef])
                    cmd_line.append(self[clef])
                else:
                    cmd_line.append("'"+self[clef]+"'")
        cmd_temp = '('
        for n, elt in enumerate(cmd_line):
            if isinstance(elt, str):
                cmd_temp += elt
            else:
                cmd_temp += '{}'.format(elt)
            if n < len(cmd_line)-1:
                cmd_temp += ', '
        cmd_temp += ')'
        return cmd_temp, order


class Python(Parameters):

    def command_line_base(self, cmd_line_set, mode, output_directory, input_p, output_p):
        if not cmd_line_set:
            cmd_base = 'python ' + self.curr_path + ''
        else:
            cmd_base = 'python ' + self.curr_path + cmd_line_set
        cmd_line, order = self.chaine_parameters(output_directory, input_p, output_p)
        cmd = cmd_base + cmd_line
        return cmd, order

    #def chaine_parameters(self, output_directory, input_dict, output_dict):


class ParametersSide(list):

    def copy_values(self, input_dict):
        for elt in input_dict:
            self.append(elt)
        return False

    #Fonction wrote by Nicolas Roehri
    @classmethod
    def get_list_subclasses_names(cls):
        sub_classes_names = []
        for subcls in cls.__subclasses__():
            sub_classes_names.append(subcls.__name__)
            sub_classes_names.extend(subcls.get_list_subclasses_names())
        return sub_classes_names


class Mode(ParametersSide):

    def update_values(self, input_dict):
        key2remove = []
        for elt in self:
            if not elt == input_dict:
                key2remove.append(elt)
                #self.remove(elt)
        for key in key2remove:
            self.remove(key)


class Input(ParametersSide):

    def copy_values(self, input_dict):
        for elt in input_dict:
            mod_dict = InputArguments()
            rewrite = mod_dict.copy_values(elt)
            self.append(mod_dict)
        return rewrite

    def update_values(self, input_dict, tag, input_param=None):
        for elt in self:
            if elt['Tag'] == tag:
                elt.update_values(input_dict)

    def command_arg(self, subject_list, curr_bids):
        size = len(self)
        if size == 1:
            input_file = self[0].command_arg(subject_list, curr_bids)
        else:
            input_file = Input()
            for elt in self:
                f_list = elt.command_arg(subject_list, curr_bids)
                input_file.append(f_list)
        return input_file

    def control_length_of_multiple_input(self):
        taille = [len(list(elt.values())[0]) for elt in self]
        result = all(elem == taille[0] for elem in taille)
        if result:
            return True
        else:
            return False

    def get_input_values(self, subject_to_analyse, order):
        def compare_and_reorder(in_out, idx_in):
            err = ''
            the_len = len(in_out[0])
            key2order = [0]
            key2combine = [0]
            for cnt, l in enumerate(in_out):
                if cnt > 0 and isinstance(l, list):
                    if len(l) == the_len and not idx_in[cnt]['CombinationMode']:
                        key2order.append(cnt)
                    elif idx_in[cnt]['CombinationMode']:
                        key2combine.append(cnt)
                    else:
                        err += 'ERROR: The elements in the list don"t have the same size.\n'
                        return err
            reorder_inputs(in_out, idx_in, key2order=key2order)
            if len(key2combine) > 1:
                B = [in_out[idx] for idx in key2combine]
                combinaison = [i for i in itertools.product(*B)]
                for cnt, idx in enumerate(key2combine):
                    in_out[idx] = [cb[cnt] for cb in combinaison]
            return err

        # def compare_length_multi_input(in_out, idx_in):
        #     err = ''
        #     nbr_in = None
        #     for i in range(0, len(idx_in)-1):
        #         if len(in_out[i]) != len(in_out[i+1]):
        #             err += 'ERROR: The elements in the list don"t have the same size.\n'
        #     if not err:
        #         nbr_in = len(in_out[0])
        #     return err, nbr_in

        def reorder_inputs(in_out, idx_in, key2order=None):
            if key2order is None:
                key2order = list(idx_in.keys())
            if len(key2order) > 1:
                if all(idx_in[elt]['Type']=='file' for elt in idx_in if elt in key2order):
                    idx_list = list(idx_in.keys())
                    tmp_dict = {idx: {} for idx in idx_list[1:]}
                    for cnt, file in enumerate(in_out[idx_list[0]]):
                        file_split = file.split('_')
                        val_ind = {elt: val for elt in SubjectToAnalyse.keylist for val in file_split if val.startswith(elt+'-')}
                        for id in idx_list[1:]:
                            val_diff = [val_ind[key] for key in val_ind if not all(val_ind[key] in subfile for subfile in in_out[id])]
                            if val_diff:
                                new_file = [flist for flist in in_out[id] if all(val in flist for val in val_diff)]
                                if new_file and len(new_file) ==1:
                                    tmp_dict[id][cnt] = new_file[0]
                    for id in tmp_dict:
                        for ct in tmp_dict[id]:
                            in_out[id][ct] = tmp_dict[id][ct]

        in_out = {clef: ['']*len(order) for clef in subject_to_analyse['sub']}
        temp = {clef: 0 for clef in subject_to_analyse['sub']}
        order_tag = [tag for tag in order]
        input_att = {'Input_'+tag: {} for tag in order_tag}
        idx_in = {}
        error_in = ''
        for cn, elt in enumerate(self):
            not_inside = False
            tag_val = elt['Tag']
            if not elt['Tag']:
                tag_val = 'in'+str(cn)
            if tag_val not in order_tag:
                not_inside = True
            else:
                idx = order[tag_val]
            if not not_inside:
                input_att['Input_' + tag_val] = elt.get_input_values(subject_to_analyse, in_out, idx, order_tag[idx])
                idx_in[idx] = {'Type': elt['Type'], 'CombinationMode': elt['CombinationMode']}
        sub_to_delete = []
        for sub in in_out:
            if len(idx_in) > 1:
                # error, nbr_in = compare_length_multi_input(in_out[sub], idx_in)
                error = compare_and_reorder(in_out[sub], idx_in)
                if error:
                    sub_to_delete.append(sub)
                    error_in += error
                    error_in += 'The subject {} won"t be analysed because it doesn"t match the inputs specificity.\n'.format(sub)
            temp[sub] = len(in_out[sub][idx])
        for sub in sub_to_delete:
            del in_out[sub]
            del temp[sub]
        for inp in input_att:
            for sub in input_att[inp]:
                if sub not in sub_to_delete:
                    for key, val in input_att[inp][sub].items():
                        try:
                            subject_to_analyse[inp][key].extend(val)
                        except:
                            subject_to_analyse[inp][key] = val
                        subject_to_analyse[inp][key] = list(set(subject_to_analyse[inp][key]))
                        subject_to_analyse[inp][key].sort()
        return temp, idx_in, in_out, error_in


class InputArguments(Parameters):
    keylist = ['Tag', 'MultipleSubjects', 'Modality', 'Type']
    keylist_deriv = ['DerivFolder', 'FileType', 'Optional']
    keylist_optional = ['CombinationMode']
    path_key = ['sub', 'ses', 'modality']
    multiplesubject = False
    deriv_input = False

    def copy_values(self, input_dict): #, flag_process=False):
        keys = list(input_dict.keys())
        rewrite = False
        if not all(k in keys for k in self.keylist): #and not flag_process:
            new_dict, log = self.keys_standardization(input_dict)
            keys = list(new_dict.keys())
            if log or (not all(k in keys for k in self.keylist)):
                raise KeyError('Your json is not conform.\n')
            else:
                rewrite = True
                input_dict = new_dict

        for key in input_dict:
            if key == 'Modality':
                if isinstance(input_dict[key], str):
                    self[key] = []
                    value = input_dict[key].capitalize()
                    self[key].append(value)
                elif isinstance(input_dict[key], list):
                    value = [elt.capitalize() for elt in input_dict[key]]
                    self[key] = value
            elif key == 'DerivFolder':
                if isinstance(input_dict[key], str):
                    self[key] = [input_dict[key]]
                else:
                    self[key] = input_dict[key]
                self.deriv_input = True
            else:
                self[key] = input_dict[key]
        if 'CombinationMode' not in keys:
            self['CombinationMode'] = False
        if self['MultipleSubjects'] and self['Type'] == 'file':
            raise ValueError('Your json is not conform.\n It is not possible to have files as input and process multiple subject.\n')

        return rewrite

    def update_values(self, input_dict):
        for key in input_dict:
            if key in self.keys() and key == 'DerivFolder':
                self[key] = input_dict[key]
        #self['ValueSelected] = input_dict

    def get_input_values(self, subject_to_analyse, in_out, idx, tag):#sub, input_param=None):
        def check_dir_existence(bids_directory, chemin, filetype=None):
            chemin_final = os.path.join(self.bids_directory, os.sep.join(chemin))
            if os.path.exists(chemin_final):
                return chemin_final
            else:
                idx2remove = len(chemin)-1
                if filetype is not None:
                    if chemin[idx2remove] == filetype:
                        idx2remove = idx2remove - 1
                del chemin[idx2remove]
                return check_dir_existence(bids_directory, chemin, filetype=filetype)

        input_att = {sub: {} for sub in subject_to_analyse['sub']}
        if self.deriv_input: #'DerivFolder in self.keys():
            if self['DerivFolder'] and self['DerivFolder'] != ['']:
                self.curr_bids.is_pipeline_present(self['DerivFolder'][0])
                if not self.curr_bids.curr_pipeline['isPresent']:
                    raise ValueError(
                        'The derivatives folder {} selected doesn"t exists in the Bids Dataset.\n'.format(
                            self['DerivFolder']))
                #self.read_deriv_fold = subject_to_analyse[self['Tag]]['DerivFolder]
            elif (self['DerivFolder'] == [''] or not self['DerivFolder']) and self['Optional']:
                return
            else:
                raise ValueError('You have to select a derivatives folder for the input {}'.format(tag))
        if self['Type'] in ['file', '4D']:
            for sub in subject_to_analyse['sub']:
                in_out[sub][idx], input_att[sub] = self.get_subject_files(subject_to_analyse['Input_'+tag], sub)
        elif self['Type'] == 'dir':
            path_key = {key: '' for key in self.path_key}
            for key in path_key:
                if key in subject_to_analyse['Input_'+tag]:
                    val = subject_to_analyse['Input_'+tag][key]
                    if isinstance(val, list) and len(val) == 1:
                        path_key[key] = val[0]
                    # elif isinstance(val, str):
                    #     path_key[key] = val.lower()
            #que faire si plusieurs session sont selectionner ?
            for sub in subject_to_analyse['sub']:
                path_key['sub'] = sub
                chemin = []
                filetype = None
                if self.deriv_input:
                    chemin.append('derivatives'+ os.sep + self['DerivFolder'][0])
                    #path_key['modality'] = path_key['modality'] + 'Process'
                for key, val in path_key.items():
                    if val and key != 'modality':
                        chemin.append(key+'-'+val)
                    elif val and key == 'modality':
                        chemin.append(val.lower())
                    elif not val and key == 'ses':
                        subdir = os.path.join(self.bids_directory, os.sep.join(chemin))
                        if os.path.exists(subdir):
                            ses = [f for f in os.listdir(subdir) if os.path.isdir(os.path.join(subdir,f)) and f.startswith('ses-')]
                            if len(ses) == 1:
                                chemin.append(ses[0])
                    # elif not val:
                    #     break
                if self.deriv_input and ('FileType' in self and self['FileType']):
                    filetype = self['FileType']
                    chemin.append(filetype)
                #check the existence of the directory
                in_out[sub][idx] = [check_dir_existence(self.bids_directory, chemin, filetype=filetype)]
        elif self['Type'] == 'montage':
            for sub in subject_to_analyse['sub']:
                in_out[sub][idx] = self.get_montage_files(subject_to_analyse['Input_'+tag], sub)
        return input_att

    def get_subject_files(self, subject, sub_id):#, modality, subject_list, curr_bids):
        input_files = []
        temp_att = {}
        if 'modality' not in subject.keys():
            subject['modality'] = self['Modality']
        # modality = [elt for elt in bids.ModalityType.get_list_subclasses_names() if elt in subject['modality']]
        # if not modality:
        #     modality = [elt for elt in bids.ModalityType.get_list_subclasses_names() if any(elmt in subject['modality'] for elmt in eval('bids.' + elt + '.allowed_modalities'))]
        if self.deriv_input and not self['DerivFolder'][0].startswith('freesurfer'):
            self.curr_bids.is_pipeline_present(self['DerivFolder'][0])
            for sub in self.curr_bids.curr_pipeline['Pipeline']['SubjectProcess']:
                if sub['sub'] == sub_id:
                    for mod in subject['modality']:
                        if not mod.endswith('Process'):
                            mod = mod + 'Process'
                        if sub[mod]:
                            for elt in sub[mod]:
                                attrdict = elt.get_attributes(['modality', 'fileLoc'])
                                is_equal = [True]
                                for key in subject:
                                    if key == 'modality' or key == 'DerivFolder':
                                        continue
                                    elif key == 'mod':
                                        if elt['modality'] in subject[key]:
                                            is_equal.append(True)
                                        else:
                                            is_equal.append(False)
                                    elif elt[key] in subject[key]:
                                        is_equal.append(True)
                                    else:
                                        is_equal.append(False)
                                # if not is_equal and self.deriv_input:
                                #     if elt['fileLoc'].endswith(self['filetype']):
                                #         is_equal.append(True)
                                #     else:
                                #         is_equal.append(False)
                                if (all(is_equal) and elt['fileLoc'].endswith(self['FileType'])) or (all(attrdict[k] == '' for k in attrdict) and elt['fileLoc'].endswith(self['FileType'])):
                                    key_attributes = [clef for clef in SubjectToAnalyse.keylist if not clef == 'modality']
                                    for key in key_attributes:
                                        if key in elt and elt[key] and key not in temp_att:
                                            temp_att[key] = [elt[key]]
                                        elif key in elt and elt[key] and elt[key] not in temp_att[key]:
                                            temp_att[key].append(elt[key])
                                    input_files.append(os.path.join(self.bids_directory, elt['fileLoc']))
        elif self.deriv_input and self['DerivFolder'][0].startswith('freesurfer'):
            dir_free, fle_type = self['FileType'].split('/*')
            sub_path = os.path.join(self.curr_bids.dirname, 'derivatives', self['DerivFolder'][0], 'sub-' + sub_id, dir_free)
            if os.path.exists(sub_path):
                listing = os.listdir(sub_path)
                file = [fle for fle in listing if fle.endswith(fle_type)]
                if len(file) == 1:
                    input_files.append(os.path.join(sub_path, file[0]))
        else:
            for sub in self.curr_bids['Subject']:
                if sub['sub'] == sub_id:
                    for mod in subject['modality']:
                        for elt in sub[mod]:
                            is_equal = [True]
                            for key in subject:
                                if key == 'modality':
                                    continue
                                elif key == 'mod':
                                    if elt['modality'] in subject[key]:
                                        is_equal.append(True)
                                    else:
                                        is_equal.append(False)
                                elif elt[key] in subject[key]:
                                    is_equal.append(True)
                                else:
                                    is_equal.append(False)
                            if all(is_equal):
                                key_attributes = [clef for clef in SubjectToAnalyse.keylist if not clef == 'modality']
                                for key in key_attributes:
                                    if key in elt and elt[key] and key not in temp_att:
                                        temp_att[key] = [elt[key]]
                                    elif key in elt and elt[key] and elt[key] not in temp_att[key]:
                                        temp_att[key].append(elt[key])
                                input_files.append(os.path.join(self.bids_directory, elt['fileLoc']))
                                if mod == 'Meg' and os.path.isdir(input_files[-1]) and self['Type'] == 'file':
                                    input_files[-1] = os.path.join(input_files[-1], 'c,rfDC')
        #subject.update(temp_att)
        return input_files, temp_att

    def get_montage_files(self, subject, sub_id):
        filetype = ''
        input_files = []
        temp_att = {}
        if 'modality' not in subject.keys():
            subject['modality'] = self['Modality']
        if 'FileType' in self:
            filetype = self['FileType']
        for sub in self.curr_bids['Subject']:
            if sub['sub'] == sub_id:
                for mod in subject['modality']:
                    if 'ses' in subject:
                        session = subject['ses']
                    else:
                        session = [elt['ses'] for elt in sub[mod]]
                        session = list(set(session))
                    for ses in session:
                        sesname=''
                        if ses:
                            sesname = 'ses-'+ses
                        path = os.path.join(self.curr_bids.dirname, 'sub-'+sub['sub'], sesname, mod.lower())
                        listing = os.listdir(path)
                        file = [os.path.join(path,file) for file in listing if '_montage' in file and filetype in file and os.path.isfile(os.path.join(path, file))]
                        input_files.extend(file)
        return input_files



class Output(Parameters):
    keylist = ['Tag', 'MultipleSubjects', 'Directory', 'Type', 'Extension']
    # keylist = ['Tag, 'MultipleSubjects, 'Directory, 'Type, 'Extension]
    multiplesubject = False

    def copy_values(self, input_dict, flag_process=False):
        keys = list(input_dict.keys())
        rewrite = False
        if not keys == self.keylist and not flag_process:
            new_dict, log = self.keys_standardization(input_dict)
            keys = list(new_dict.keys())
            if log or (not keys == self.keylist and not flag_process):
                raise KeyError('Your json is not conform.\n')
            else:
                rewrite = True
                input_dict = new_dict

        if (input_dict['Type'] == 'dir' and not input_dict['Directory']) or (input_dict['Type'] == 'file' and input_dict['Directory']):
            raise KeyError('The output in your json is not conform due to the type.\n You mention directory: {0} and type: {1}.\n'.format(input_dict['Directory'], input_dict['Type']))
        for key in keys:
            self[key] = input_dict[key]
        if self['MultipleSubjects'] and self['Type'] == 'file':
            raise ValueError('Your json is not conform.\n It is not possible to have files as output and process multiple subject.\n')
        return rewrite

    def update_values(self, input_dict):
        self['ValueSelected'] = input_dict

    def get_output_values(self, in_out, taille, order, output_directory, idx_in): #sub,
        def create_output_file(output_dir, filename, extension, bids_directory):
            out_file = []
            soft_name = os.path.basename(output_dir).lower()
            soft_name = soft_name.split('-v')[0]
            if "c,rfDC" in filename:
                filename = os.path.dirname(filename)
            dirname, filename = os.path.split(filename)
            trash, dirname = dirname.split(bids_directory + os.sep)
            if 'derivatives' in dirname:
                idx = dirname.find('sub-')
                dirname = dirname[idx::]
            file_elt = filename.split('_')
            if isinstance(extension, list) and extension:
                for ext in extension:
                    file_elt[-1] = soft_name + ext
                    filename = '_'.join(file_elt)
                    output = os.path.join(output_dir, dirname, filename)
                    os.makedirs(os.path.dirname(output), exist_ok=True)
                    out_file.append(output)
            elif isinstance(extension, str) and extension != '':
                file_elt[-1] = soft_name + '.' + extension
                filename = '_'.join(file_elt)
                output = os.path.join(output_dir, dirname, filename)
                os.makedirs(os.path.dirname(output), exist_ok=True)
                out_file.append(output)
            else:
                file_elt = filename.split('_')
                del file_elt[-1]
                filename = '_'.join(file_elt)
                output = os.path.join(output_dir, dirname, filename)
                os.makedirs(os.path.dirname(output), exist_ok=True)
                out_file.append(output)
            return out_file

        def create_output_sub_dir(output_dir, filename, bids_directory):
            if os.path.isfile(filename) or (os.path.isdir(filename) and filename.endswith('meg')):
                dirname, filename = os.path.split(filename)
                if dirname.endswith('_meg'):
                    dirname = os.path.dirname(dirname)
                trash, dirname = dirname.split(bids_directory + os.sep)
            else:
                trash, dirname = filename.split(bids_directory+ os.sep)
            if 'derivatives' in dirname:
                idx = dirname.find('sub-')
                dirname = dirname[idx::]
            out_dir = [os.path.join(output_dir, dirname)]
            os.makedirs(out_dir[0], exist_ok=True)
            return out_dir

        if not self['Tag']:
            idx = order['out']
        else:
            idx = order[self['Tag']]
        if not self['Directory']:
            if self['Type'] == 'file':
                if not taille:
                    raise EOFError('No input list to create the output')
                else:
                    for sub in in_out:
                        output_files = []
                        idx_list = list(idx_in.keys())
                        if len(idx_list) > 1:
                            idl=[]
                            for i in idx_list:
                                if 'CombinationMode' in idx_in[i] and not idx_in[i]['CombinationMode']:
                                    idl.append(i)
                            if idl:
                                if len(idl) != len(idx_list):
                                    idi = idl[-1]
                                else:
                                    idi = idx_list[0]
                            else:
                                idi = idx_list[0]
                        else:
                            idi = idx_list[0]
                        for filename in in_out[sub][idi]:
                            out_file = create_output_file(output_directory, filename, self['Extension'], self.bids_directory)
                            output_files.append(out_file)
                        in_out[sub][idx] = output_files
            # elif self['type'] == 'sub':
            #     if not self['multiplesubject']:
            #         output_files = sub
        #A revoir avec subject_list
        else:
            if self['MultipleSubjects']:
                for sub in in_out:
                    in_out[sub][idx] = output_directory #[output_directory] * taille[sub]
            else:
                for sub in in_out:
                    output_files = []
                    idx_list = list(idx_in.keys())
                    if len(idx_list) > 1:
                        idl = []
                        for i in idx_list:
                            if 'CombinationMode' in idx_in[i] and not idx_in[i]['CombinationMode']:
                                idl.append(i)
                        if idl:
                            idi = idl[-1]
                        else:
                            idi = idx_list[0]
                    else:
                        idi = idx_list[0]
                    for filename in in_out[sub][idi]:
                        output_dir = create_output_sub_dir(output_directory, filename, self.bids_directory)
                        output_files.append(output_dir)
                    in_out[sub][idx] = output_files

    def command_arg(self, output_dir, soft_name, subject_list, input_type, input_file_list=None):
        def create_output_file(output_dir, filename, extension, soft_name, bids_directory):
            out_file = []
            soft_name = soft_name.lower()
            dirname, filename = os.path.split(filename)
            trash, dirname = dirname.split(bids_directory + os.sep)
            file_elt = filename.split('_')
            if isinstance(extension, list) and extension:
                for ext in extension:
                    file_elt[-1] = soft_name + '.' + ext
                    filename = '_'.join(file_elt)
                    output = os.path.join(output_dir, dirname, filename)
                    os.makedirs(os.path.dirname(output), exist_ok=True)
                    out_file.append(output)
            elif isinstance(extension, str) and extension != '':
                file_elt[-1] = soft_name + '.' + extension
                filename = '_'.join(file_elt)
                output = os.path.join(output_dir, dirname, filename)
                os.makedirs(os.path.dirname(output), exist_ok=True)
                out_file.append(output)
            else:
                file_elt = filename.split('_')
                del file_elt[-1]
                filename = '_'.join(file_elt)
                output = os.path.join(output_dir, dirname, filename)
                os.makedirs(os.path.dirname(output), exist_ok=True)
                out_file.append(output)
            return out_file

        def create_output_folder(output_dir, bids_directory, input_name=None, subject_to_analyse=None):
            out_file = []
            if input_name:
                for filename in input_file_list:
                    path = os.path.dirname(filename)
                    trash, path = path.split(bids_directory)
                    output = output_dir + path
                    os.makedirs(output, exist_ok=True)
                    out_file.append(output)
            elif subject_to_analyse:
                for sub in subject_to_analyse['sub']:
                    output = os.path.join(output_dir, sub)
                    os.makedirs(output, exist_ok=True)
                    out_file.append(output)
            return out_file

        output_file_list = []
        out_to_return = Output()
        if not self['Directory']:
            if self['Type'] == 'file':
                if not input_file_list:
                    raise EOFError('No input list to create the output')
                for filename in input_file_list:
                    out_file = create_output_file(output_dir, filename, self['Extension'], soft_name, self.bids_directory)
                    output_file_list.append(out_file)
            elif self['Type'] == 'sub':
                #A revoir
                if not self.multiplesubject:
                    output_file_list = subject_list['sub']

        else:
            #A revoir avec subject_list
            if self.multiplesubject:
                output_file_list.append(output_dir)
            elif input_type == 'file':
                output_file_list = create_output_folder(output_dir, self.bids_directory, input_name=input_file_list)
            elif input_type == 'sub':
                output_file_list = create_output_folder(output_dir, self.bids_directory, subject_to_analyse=subject_list)

        out_to_return[self['Tag']] = output_file_list
        out_to_return.multiplesubject = self.multiplesubject

        return out_to_return


class Arguments(Parameters):
    unit_value = ['Default', 'Unit']
    read_value = ['Read', 'ElementsToRead', 'MultipleSelection']
    list_value = ['PossibleValue', 'MultipleSelection']
    file_value = ['FileLoc', 'Extension']
    bool_value = ['Default', 'InCommandLine']
    bids_value = ['ReadBids', 'Type']

    def copy_values(self, input_dict):
        keylist = list(input_dict.keys())
        readbids = []
        rewrite = False
        if keylist != self.unit_value and keylist != self.read_value and keylist != self.list_value and keylist != self.file_value and keylist != self.bool_value and keylist != self.bids_value:
            new_dict, err = self.keys_standardization(input_dict)
            keylist = list(new_dict.keys())
            if err or (keylist != self.unit_value and keylist != self.read_value and keylist != self.list_value and keylist != self.file_value and keylist != self.bool_value and keylist != self.bids_value):
                raise EOFError(
                    'The {} in Parameters of your JSON file are not conform.\n Please modify it according to the given template.\n'.format(err))
            else:
                rewrite = True
                input_dict = new_dict
        for key in input_dict:
            self[key] = input_dict[key]
            if key == self.bids_value:
                readbids.append(input_dict[key]['Type'])
        return readbids, rewrite

    def update_values(self, input_dict):
        if not input_dict:
            pass
        elif isinstance(input_dict, list):
            self['ValueSelected'] = input_dict
        elif isinstance(input_dict, str):
            if input_dict:
                if 'Unit' in self.keys():
                    unit = self['Unit']
                    if input_dict == unit:
                        pass
                    elif unit and unit in input_dict:
                        self['ValueSelected'] = input_dict.split(unit)[0]
                    else:
                        self['ValueSelected'] = input_dict
                    if 'ValueSelected' in self and self['ValueSelected'] and any(c.isdigit() for c in self['ValueSelected']):
                        if '.' in self['ValueSelected'] or ',' in self['ValueSelected']:
                            self['ValueSelected'] = float(self['ValueSelected'])
                        elif all(c.isdigit() for c in self['ValueSelected']):
                            self['ValueSelected'] = int(self['ValueSelected'])
                elif 'Type' in self.keys():
                    unit = self['Type']
                    if not input_dict == unit:
                        self['ValueSelected'] = input_dict
                else:
                    self['ValueSelected'] = input_dict
        elif isinstance(input_dict, bool):
            self['ValueSelected'] = input_dict


class SubjectToAnalyse(Parameters):
    #required_keys = 'sub'
    keylist = ['ses', 'task', 'acq', 'proc', 'run', 'modality']

    def __init__(self, sub_list, input_dict=None):
        if isinstance(sub_list, list):
            self['sub'] = sub_list
        else:
            self['sub'] = [sub_list]
        if input_dict:
            for key, val in input_dict.items():
                self[key] = {}
                for clef in val.keys():
                    if isinstance(val[clef], list):
                        self[key][clef] = val[clef]
                    else:
                        self[key][clef] = [val[clef]]
        else:
            for key in self.keylist:
                self[key] = []

    def copy_values(self, input_dict):
        for key in input_dict:
            if key not in self.keys():
                self[key] = []
            if isinstance(input_dict[key], str):
                self[key].append(input_dict[key])
            else:
                self[key].extend(input_dict[key])

    def write_file(self, output_directory):
        filename = os.path.join(output_directory, 'subjects_selected_file.json')
        with open(filename, 'w+') as f:
            json_str = json.dumps(self, indent=1, separators=(',', ': '), ensure_ascii=False, sort_keys=False)
            f.write(json_str)

    def remove(self, subid):
        self['sub'].remove(subid)


def verify_subject_has_parameters(curr_bids, sub_id, input_vars, param=None):
    warn_txt = ''
    err_txt = ''
    sub2remove = []
    deriv_folder = None
    for key in input_vars:
        keylist = []
        if input_vars[key] is None or not input_vars[key]:
            continue
        #make sure everything is list
        for elt in input_vars[key]:
            if isinstance(input_vars[key][elt], str):
                input_vars[key][elt] = [input_vars[key][elt]]
        if 'modality' not in input_vars[key].keys() and param is None:
            warn_txt += 'No modality has been mentionned for the input {}. Bids pipeline will select the one by default.\n'.format(key)
            #input_vars[key]['modality'] = bids.Imaging.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names()
            continue
        elif 'modality' not in input_vars[key].keys() and param:
            #Verifie le multiple selection
            idx = [param.index(elt) for elt in param if
                   elt['Tag'] == key.split('_')[1]][0]
            if param[idx]['modality']:
                input_vars[key]['modality'] = param[idx]['modality']
                mod = input_vars[key]['modality'][-1]
            else:
                continue
        else:
            mod = input_vars[key]['modality'][-1]
        if 'DerivFolder' in input_vars[key].keys():
            deriv_folder = input_vars[key]['DerivFolder'][-1]
            if deriv_folder == '' or 'Previous analysis results' in deriv_folder:# or deriv_folder == ['']:
                continue
        keylist = [clef for clef in input_vars[key] if (clef != 'modality' and clef != 'DerivFolder')]

        for clef in keylist:
            for sid in sub_id:
                if deriv_folder is not None:
                    curr_bids.is_pipeline_present(deriv_folder)
                    if not curr_bids.curr_pipeline['isPresent']:
                        err_txt += "The derivative folder selected {0} in {1} is not present in the bids dataset.\n".format(deriv_folder, key)
                        return warn_txt, err_txt
                    curr_bids.curr_pipeline['Pipeline'].is_subject_present(sid, True)
                    if curr_bids.curr_pipeline['Pipeline'].curr_subject['isPresent']:
                        if not mod.endswith('Process'):
                            mod = mod+'Process'
                        elmt = [val[clef] for val in curr_bids.curr_pipeline['Pipeline'].curr_subject['SubjectProcess'][mod]]
                        if clef == 'mod':
                            elmt = [val['modality'] for val in
                                    curr_bids.curr_pipeline['Pipeline'].curr_subject['SubjectProcess'][mod]]
                    else:
                        warn_txt += 'The subject {0} is not present in the {1} folder.\n'.format(sid, deriv_folder)
                        sub2remove.append(sid)
                        continue
                else:
                    curr_bids.is_subject_present(sid)
                    if curr_bids.curr_subject['isPresent']:
                        elmt = [val[clef] for val in curr_bids.curr_subject['Subject'][mod]]
                        if clef == 'mod':
                            elmt = [val['modality'] for val in curr_bids.curr_subject['Subject'][mod]]
                    else:
                        warn_txt += 'The subject {0} is not present in the bids dataset.\n'.format(sid)
                        sub2remove.append(sid)
                        continue
                if not any(elt in elmt for elt in input_vars[key][clef]):
                    warn_txt += 'The subject {0} doesn"t have the required {1} for the analysis.\n The {2} is missing.\n'.format(sid, key, clef)
                    sub2remove.append(sid)
        deriv_folder = None
    if sub2remove:
        sub2remove = list(set(sub2remove))
        for sub in sub2remove:
            if sub in sub_id:
                warn_txt += 'The subject {} will be removed from the subject selection.\n'.format(sub)
                sub_id.remove(sub)
    if not sub_id:
        err_txt += 'There is no more subject in the selection.\n Please modify your parameters.\n'
        return warn_txt, err_txt

    return warn_txt, err_txt


def main(argv):
    bidsdirectory = None
    analysisname = ''
    parameters = {}
    subjectlist = {}

    try:
        opts, args = getopt.getopt(argv, "hb:a:p:s:", ["bidsdirectory=", "analysisname=", "parameters=", "subjectlist="])
    except getopt.GetoptError:
        print('pipeline_class.py -b <bidsdirectory> -a <analysisname> -p <parameters> -s <subjectlist>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('pipeline_class.py -b <bidsdirectory> -a <analysisname> -p <parameters> -s <subjectlist>')
            sys.exit()
        elif opt in ('-b', '--bidsdirectory'):
            bidsdirectory = arg
        elif opt in ('-a', '--analysisname'):
            analysisname = arg
        elif opt in ('-p', '--parameters'):
            if os.path.exists(arg):
                parameters = arg
            else:
                parameters = eval(arg)
                if not isinstance(parameters, dict):
                    print('ERROR: Parameters should be a dictionnary or filename.\n')
                    sys.exit(-1)
        elif opt in ('-s', '--subjectlist'):
            subjectlist = eval(arg)
            if not isinstance(subjectlist, dict):
                print('ERROR: Subject should be a dictionnary with at least sub as key.\n')
                sys.exit(-1)

    if not bidsdirectory or not analysisname or not parameters or not subjectlist:
        print('ERROR: All arguments are required.\n')
        sys.exit(-1)

    return bidsdirectory, analysisname, parameters, subjectlist


if __name__ == '__main__':
    bidsdirectory, analysisname, parameters, subjectlist = main(sys.argv[1:])
    soft_analyse = PipelineSetting(bidsdirectory, analysisname)
    log_analyse = soft_analyse.set_everything_for_analysis(parameters, subjectlist)
    print(log_analyse)
