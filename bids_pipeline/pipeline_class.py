from bids_manager import ins_bids_class as bids
import json
import os
import datetime
import getpass
import getopt
import sys
import subprocess
import shutil
from tkinter import messagebox, filedialog
from bids_pipeline.convert_process_file import go_throught_dir_to_convert
from sys import exc_info


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


class DerivativesSetting(object):
    path = None
    pipelines = []

    def __init__(self, bids_dev):
        if isinstance(bids_dev, bids.Derivatives):
            self.pipelines = bids_dev['Pipeline']
            self.path = os.path.join(bids_dev.cwdir, 'derivatives')
        elif isinstance(bids_dev, str):
            if os.path.exists(bids_dev) and bids_dev.endswith('derivatives'):
                self.path = bids_dev
                self.read_directory(bids_dev)

    def read_directory(self, dev_dir):
        with os.scandir(dev_dir) as it:
            for entry in it:
                if entry.is_dir():
                    pip = bids.Pipeline()
                    pip.dirname = entry.path
                    empty_dir = self.empty_dirs(entry.name, recursive=True)
                    if not empty_dir:
                        self.parse_pipeline(pip.dirname, entry.name)
                    else:
                        shutil.rmtree(entry.path, ignore_errors=True)
                    #self.pipelines.append(pip)

    def is_empty(self):
        default = ['log', 'parsing']
        pip_list = [pip['name'] for pip in self.pipelines if pip['name'] not in default]
        if pip_list:
            is_empty = False
        else:
            is_empty = True
        return is_empty, pip_list

    def create_pipeline_directory(self, pip_name, param_var, subject_list):
        def check_pipeline_variant(pip_list, pip_name):
            variant_list = []
            it_exist = False
            for pip in pip_list:
                if pip.startswith(pip_name.lower()):
                    # variant = pip.split('-')
                    # if len(variant) > 1:
                    #     variant_list.append(variant[1:])
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
                    # empty_dirs = self.empty_dirs(elt, recursive=True)
                    # if empty_dirs:
                    #     directory_name = elt
                    #     desc_data = DatasetDescPipeline(param_vars=param_var, subject_list=subject_list)
                    #     desc_data['Name'] = directory_name
                    #     break
                    dataset_file = os.path.join(self.path, elt, DatasetDescPipeline.filename)
                    if not os.path.exists(dataset_file):
                        dataset_file = None
                    desc_data = DatasetDescPipeline(filename=dataset_file)
                    same_param, sub_inside = desc_data.compare_parameters(param_var, subject_list)
                    if (same_param and not sub_inside) or mode:
                        directory_name = elt
                        if not mode:
                            #desc_data['SourceDataset']['sub'].append(subject_list['sub'])
                            desc_data.update(subject_list)
                        break
                if not directory_name:
                    directory_name = pip_name.lower() + '-v' + str(len(variant_list) + 1)
                    desc_data = DatasetDescPipeline(param_vars=param_var, subject_list=subject_list)
                    desc_data['Name'] = directory_name
            # if it_exist and not variant_list:
            #     directory_name = pip_name + '-v1'
            # elif it_exist and variant_list:
            #     directory_name = pip_name + '-v' + str(len(variant_list)+1)
            else:
                directory_name = pip_name.lower()
                desc_data = DatasetDescPipeline(param_vars=param_var, subject_list=subject_list)
                desc_data['Name'] = directory_name
        else:
            directory_name = pip_name.lower()
            desc_data = DatasetDescPipeline(param_vars=param_var, subject_list=subject_list)
            desc_data['Name'] = directory_name
        directory_path = os.path.join(self.path, directory_name)
        norm_path = os.path.normpath(directory_path)
        os.makedirs(norm_path, exist_ok=True)
        desc_data.write_file(jsonfilename=os.path.join(norm_path, DatasetDescPipeline.filename))
        return norm_path, directory_name, desc_data

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
                            subinfo.check_file_in_scans(file.name, mod_dir + 'Process')
                            #subinfo[mod_dir + 'Process'][-1].get_sidecar_files()
                        # elif mod_dir + 'GlobalSidecars' in bids.BidsBrick.get_list_subclasses_names() and ext.lower() \
                        #         in eval(mod_dir + 'GlobalSidecars.allowed_file_formats') and filename.split('_')[-1]\
                        #         in [eval(value + '.modality_field') for _, value in
                        #             enumerate(bids.IeegGlobalSidecars.complementary_keylist)]:
                        #     subinfo[mod_dir + 'GlobalSidecars'] = eval(mod_dir + 'GlobalSidecars(filename+ext)')
                        #     subinfo[mod_dir + 'GlobalSidecars'][-1]['fileLoc'] = file.path
                        #     subinfo[mod_dir + 'GlobalSidecars'][-1].get_attributes_from_filename()
                        #     subinfo[mod_dir + 'GlobalSidecars'][-1].get_sidecar_files()
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
                elif entry.name.startswith(name) and entry.is_dir():
                    for file in os.listdir(entry):
                        shutil.move(os.path.join(entry, file), directory_path)
                elif entry.name.startswith('sub-') and entry.is_dir():
                    sub, subname = entry.name.split('-')
                    pip['SubjectProcess'].append(bids.SubjectProcess())
                    pip['SubjectProcess'][-1]['sub'] = subname
                    parse_sub_bids_dir(entry.path, pip['SubjectProcess'][-1])

    def empty_dirs(self, pip_name, recursive=False):
        def is_empty(files, default_files):
            return (len(files) == 0 or all(file in default_files for file in files))

        empty_dirs = False
        emp_dirs = []
        pip_directory = os.path.join(self.path, pip_name)
        analyse_name = pip_name.split('-')[0].lower()
        default_files = [DatasetDescPipeline.filename, bids.ParticipantsTSV.filename, Parameters.filename, 'log_error_analyse.log', analyse_name + '_parameters.json']
        for root, dirs, files in os.walk(pip_directory, topdown=False):
            # print root, dirs, files
            if recursive:
                all_subs_empty = True  # until proven otherwise
                for sub in dirs:
                    full_sub = os.path.join(root, sub)
                    if full_sub not in emp_dirs:
                        # print full_sub, "not empty"
                        all_subs_empty = False
                        break
            else:
                all_subs_empty = (len(dirs) == 0)
            if all_subs_empty and is_empty(files, default_files):
                empty_dirs = True
                emp_dirs.append(root)
                # yield root
        return empty_dirs


class DatasetDescPipeline(bids.DatasetDescJSON):
    keylist = ['Name', 'BIDSVersion', 'PipelineDescription', 'SourceDataset', 'Author', 'Date']
    filename = 'dataset_description.json'
    bids_version = '1.3.0'

    def __init__(self, filename=None, param_vars=None, subject_list=None):
        super().__init__()
        if filename:
            self.read_file(filename)
        else:
            self['PipelineDescription'] = {}
            self['Author'] = getpass.getuser()
            self['Date'] = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            if param_vars and subject_list:
                for key in param_vars:
                    if key == 'Callname':
                        self['PipelineDescription']['Name'] = param_vars[key]
                    else:
                        self['PipelineDescription'][key] = param_vars[key]
                self['SourceDataset'] = {key: subject_list[key] for key in subject_list}

    def read_file(self, jsonfilename):
        if os.path.splitext(jsonfilename)[1] == '.json':
            if not os.path.exists(jsonfilename):
                print('datasetdescription.json does not exists.')
                return
            with open(jsonfilename, 'r') as file:
                read_json = json.load(file)
                for key in read_json:
                    if key == 'Authors' and isinstance(self[key], list) and self[key] == ['n/a']:
                        self[key] = read_json[key]
                    elif (key in self.keylist and self[key] == 'n/a') or key not in self.keylist:
                        self[key] = read_json[key]
        else:
            raise TypeError('File is not ".json".')

    def compare_parameters(self, param_vars, subject_list):
        keylist = [key for key in param_vars if not key == 'Callname']
        is_same = []
        if isinstance(self['PipelineDescription'], str):
            is_same = False
            no_subject = False
            return is_same, no_subject
        for key in keylist:
            if key in self['PipelineDescription']:
                if self['PipelineDescription'][key] == param_vars[key]:
                    is_same.append(True)
                else:
                    is_same.append(False)
            else:
                return False, False
        is_same = all(is_same)
        sub_not_in = []
        elt_not_in = []
        for key in subject_list:
            if key in self['SourceDataset'].keys():
                if isinstance(subject_list[key], dict):
                    for elt in subject_list[key]:
                        if elt in self['SourceDataset'][key]:
                            elt_not_in.append(any(el not in self['SourceDataset'][key][elt] for el in subject_list[key][elt]))
                else:
                    sub_not_in.append(all(elt not in self['SourceDataset'][key] for elt in subject_list[key]))
            else:
                elt_not_in.append(False)
        #subject_inside = all(sub in self['SourceDataset']['sub'] for sub in subject_list['sub'])
        if all(sub_not_in):
            subject_inside = False
        elif any(elt_not_in):
            subject_inside = False
        else:
            subject_inside = True
        #subject_inside = all(sub_not_in and elt_in)

        return is_same, subject_inside

    def update(self, subject2add):
        for elt in subject2add:
            if isinstance(subject2add[elt], list) and elt in self['SourceDataset'].keys():
                self['SourceDataset'][elt].extend(subject2add[elt])
                self['SourceDataset'][elt] = list(set(self['SourceDataset'][elt]))
            elif isinstance(subject2add[elt], dict):
                if elt in self['SourceDataset'].keys():
                    for clef in subject2add[elt]:
                        if clef in self['SourceDataset'][elt]:
                            self['SourceDataset'][elt][clef].extend(subject2add[elt][clef])
                        else:
                            self['SourceDataset'][elt][clef] = subject2add[elt][clef]
                        self['SourceDataset'][elt][clef] = list(set(self['SourceDataset'][elt][clef]))


class PipelineSetting(dict):
    keylist = ['Name', 'Path', 'Parameters']
    soft_path = os.path.join(os.getcwd(), 'SoftwarePipeline')
    log_error = ''
    curr_dev = None
    curr_bids = None
    curr_path = None
    cwdir=None
    jsonfilename=None

    def __init__(self, bids_dir, soft_name, soft_path=None):
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
        if soft_name + '.json' in os.listdir(self.soft_path):
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
        os.makedirs(os.path.join(self.cwdir, 'derivatives', 'bids_pipeline'), exist_ok=True)

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
        for key in input_dict:
            if key in self.keylist:
                if key == 'Parameters':
                    self[key] = Parameters(self.curr_bids.cwdir)
                    self[key].copy_values(input_dict[key])
                else:
                    self[key] = input_dict[key]
            elif key in Parameters.get_list_subclasses_names():
                self[key] = eval(key+'()')
                self[key].copy_values(input_dict[key])
            else:
                self[key] = input_dict[key]

    def read_json_parameter_file(self, soft_name):
        jsonfile = os.path.join(self.soft_path, soft_name + '.json')
        with open(jsonfile, 'r') as file:
            read_json = json.load(file)
            self.copy_values(read_json)
        self.curr_path = self['Parameters'].check_presence_of_software(self['Path'])
        if self.curr_path.startswith('ERROR'):
            raise EOFError(self.curr_path)
        #check the validity of the json ??
        if not all(key in self.keys() for key in self.keylist):
            raise EOFError("JSON is not conform.")

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

        def anywave_constraint(order, idx_in, in_out):
            in_idx = list(idx_in.keys())[0]
            order_key = list(order.keys())
            if '--output_file' in order or '--output_prefix' in order:
                pref_tag = [elt for elt in order if elt in ['--output_prefix', '--output_file']][0]
                if not in_out[order[pref_tag]]:
                    in_out[order[pref_tag]] = []
                    for file in in_out[in_idx]:
                        if "c,rfDC" in file:
                            file = os.path.dirname(file)
                        dirname, filename = os.path.split(file)
                        file_elt = filename.split('_')
                        new_file = '_'.join(file_elt[0:len(file_elt)-1])
                        in_out[order[pref_tag]].append(new_file)

        param_vars = results['analysis_param']
        output_name = ''
        try:
            # update the parameters and get the subjects
            self['Parameters'].update_values(param_vars, results['input_param'])
            #Verify the validity of the input value
            warn, err = verify_subject_has_parameters(self.curr_bids,
                                                      results['subject_selected'],
                                                      results['input_param'],
                                                      self['Parameters']['Input'])
            if warn:
                self.log_error += 'Warning: ' + warn
            if err:
                raise ValueError(err+warn)
            subject_to_analyse = SubjectToAnalyse(results['subject_selected'], input_dict=results['input_param'])
            dev = DerivativesSetting(self.curr_bids['Derivatives'][0])
            output_directory, output_name, dataset_desc = dev.create_pipeline_directory(self['Name'], param_vars, subject_to_analyse)
            participants = bids.ParticipantsProcessTSV()

            # Check if the subjects have all the required values
            #self['Parameters'].write_file(output_directory)

            #dataset_desc['PipelineDescription']['fileLoc'] = os.path.join(output_directory, Parameters.filename)
            dataset_desc.write_file(jsonfilename=os.path.join(output_directory, 'dataset_description.json'))

            #Get the value for the command_line
            cmd_arg, cmd_line, order, input_dict, output_dict = self.create_command_to_run_analysis(output_directory, subject_to_analyse) #input_dict, output_dict
        except (EOFError, TypeError, ValueError, SystemError) as er:
            exc_type, exc_obj, exc_tb = exc_info()
            err_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.log_error += 'Error type: ' + str(exc_type) + ', scriptname: ' + err_name + ', line number, ' + str(
                exc_tb.tb_lineno) + ': ' + str(er)
            self.write_log()
            shutil.rmtree(output_directory)
            return self.log_error, output_name, {}

        if not order:
            proc = subprocess.Popen(cmd_line, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            error_proc = proc.communicate()
            self.log_error += cmd_arg.verify_log_for_errors('', error_proc)
            self.write_json_associated(order, output_directory, cmd_arg)
        elif order:
            taille, idx_in, in_out, err_input = input_dict.get_input_values(subject_to_analyse, order)
            self.log_error += err_input
            if output_dict:
                output_dict.get_output_values(in_out, taille, order, output_directory, idx_in)  # sub
            for sub in in_out:
                ##To take into account the prefix and suffix in AnyWave
                anywave_constraint(order, idx_in, in_out[sub])
                idx = 0
                log_error = []
                while idx < taille[sub]:
                    use_list = list_for_str_format(in_out[sub], idx)
                    cmd = cmd_line.format(*use_list)
                    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            universal_newlines=True)
                    error_proc = proc.communicate()
                    self.log_error += cmd_arg.verify_log_for_errors(use_list, error_proc)
                    if error_proc[1]:
                        log_error.append(error_proc[1])
                    if not error_proc[1]:
                        self.write_json_associated(use_list, output_directory, cmd_arg)
                    else:
                        log_error.append(error_proc[1])
                    idx = idx + 1
                # if len(log_error) != taille[sub]:
                #     participants.append({'participant_id': sub})
        else:
            self.log_error += datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S") + ': ' + 'ERROR: The analysis {0} could not be run due to an issue with the inputs and the outputs.\n'.format(self['Name'])
            self.write_log()
            return self.log_error, output_name, {}
        empty_dir = dev.empty_dirs(output_name, recursive=True)
        if not empty_dir:
            sub_analysed = [sub.split('-')[1] for sub in os.listdir(output_directory) if sub.startswith('sub')]
            sub2remove = [sub for sub in subject_to_analyse['sub'] if sub not in sub_analysed]
            for subid in sub2remove:
                subject_to_analyse['sub'].remove(subid)
                self.log_error += 'The {} subject has finally not be analysed.\n'.format(subid)
            for sub in subject_to_analyse['sub']:
                participants.append({'participant_id': sub})
            participants.write_file(tsv_full_filename=os.path.join(output_directory, bids.ParticipantsTSV.filename))
            dataset_desc.update(subject_to_analyse)
            dataset_desc.write_file(jsonfilename=os.path.join(output_directory, DatasetDescPipeline.filename))
            try:
                go_throught_dir_to_convert(output_directory)
            except:
                pass
            dev.parse_pipeline(output_directory, output_name)
            self.curr_bids.save_as_json()
            temp = self.write_analysis_done_log(dataset_desc, filename=os.path.join(output_directory, Parameters.filename))
        else:
            self.log_error += datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S") + ': ' + 'Warning: The folder {0} has no results so your analysis may not succeed. The folder {0} will be erased.\n'.format(output_name)
            shutil.rmtree(output_directory)

        self.write_log()
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
            cmd_arg = eval(interm + '(curr_path=self.curr_path, dev_path=output_directory, callname=callname)') #'(bids_directory="'+self.cwdir+'", curr_path="'+self.curr_path+'", dev_path="'+output_directory+'", callname="'+callname+'")')
        else:
            cmd_arg = Parameters(curr_path=self.curr_path, dev_path=output_directory, callname=callname)

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
        #order.multiplesubject = input_p[0]['multiplesubject']
        return cmd_arg, cmd_line, order, input_p, output_p

    def write_json_associated(self, inout_file, output_directory, analyse):
        def create_json(input_file, output_json, analyse):
            jsonf = bids.BidsJSON()
            jsonf['Description'] = 'Results of ' + self['Name'] + ' analysis.'
            jsonf['RawSources'] = input_file
            jsonf['Parameters'] = analyse
            jsonf['Author'] = getpass.getuser()
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
                    output_file = potential_file[-1].replace(ext, bids.BidsJSON.extension)
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
        log_dir = os.path.join(self.cwdir, 'derivatives', 'bids_pipeline', 'log')
        os.makedirs(log_dir, exist_ok=True)
        time_format = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        log_filename = 'bids-pipeline_' + time_format + '.log'
        with open(os.path.join(log_dir, log_filename), 'w+') as file:
            file.write(self.log_error + '\n')

    def write_analysis_done_log(self, dataset_desc, filename=None):
        file_to_write = {key: '' for key in
                         ['analysis_param', 'subject_selected', 'input_param', 'Software', 'SoftwareVersion',
                          'JsonName']}
        # Voir comment gérer Software version
        file_to_write['JsonName'] = self.jsonfilename
        author = dataset_desc['Author']
        name = dataset_desc['Name'].split('-')[0]
        file_to_write['Software'] = name
        if author is None or author == '':
            author = getpass.getuser()
        date = dataset_desc['Date']
        if date is None or date == '':
            date = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        date.replace(' ', 'T')
        if not filename:
            analysis_dir = os.path.join(self.cwdir, 'derivatives', 'bids_pipeline', 'analysis_done')
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
    arg_readbids = []
    filename = 'BP_parameters_file.json'

    def __init__(self, curr_path=None, dev_path=None, callname=None):
        if dev_path:
            self.derivatives_directory = dev_path
        if callname:
            self.callname = callname
        if curr_path:
            self.curr_path = curr_path

    def copy_values(self, input_dict):
        for key in input_dict:
            if key in self.keylist:
                self[key] = input_dict[key]
            elif key in ParametersSide.get_list_subclasses_names() + Parameters.get_list_subclasses_names():
                self[key] = eval(key + '()')
                self[key].copy_values(input_dict[key])
            else:
                self[key] = Arguments()
                readbids = self[key].copy_values(input_dict[key])
                if readbids:
                    self.arg_readbids.append(readbids)

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
                if elt['tag']:
                    input_tag.append(elt['tag'])
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
            messagebox.showerror('PathError', 'The current pipeline path is not valid')
            filename = filedialog.askopenfilename(title='Please select ' + name + ' file',
                                                  filetypes=[('files', ext)])
            if not name in filename:
                messagebox.showerror('PathError', 'The selected file is not the good one for this pipeline')
                return 'ERROR: The path is not valid'

            return filename

        interm = None
        if 'Intermediate' in self.keys():
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
        if 'value_selected' in self.keys():
            # if isinstance(self['value_selected'], list):
            #     cmd_dict[key] = ', '.join(self['value_selected'])
            # else:
            cmd_dict[key] = self['value_selected']
        # elif 'default' in self.keys():
        #     if self['default']:
        #         cmd_dict[key] = self['default']
        elif 'readbids' in self.keys():
            type_value = None
            for clef in subject_list.keys():
                if clef == self['type']:
                    type_value = subject_list[self['type']]
                elif isinstance(subject_list[clef], dict):
                    type_value = []
                    for elt in subject_list[clef]:
                        if elt == self['type']:
                            type_value.extend(subject_list[clef][self['type']])
                if type_value:
                    cmd_dict[key] = type_value
                elif type_value is None and self['type'] == 'file':
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
                    tag_val = elt['tag']
                    if not elt['tag']:
                        tag_val = 'in' + str(cn)
                    if elt['multiplesubject'] and elt['type'] == 'dir':
                        if not elt.deriv_input:
                            cmd_line += ' ' + elt['tag'] + ' ' + self.bids_directory
                        elif elt.deriv_input and (elt['deriv-folder'] and elt['deriv-folder'] != ['']):
                            cmd_line += ' ' + elt['tag'] + ' ' + os.path.join(self.bids_directory, 'derivatives', elt['deriv-folder'][0])
                    else:
                        if elt.deriv_input:
                            if (not elt['deriv-folder'] or elt['deriv-folder'] == ['']) and not elt['optional']:
                                raise ValueError('The derivative folder for this paramater {} should be mentionned.\n'.format(elt['tag']))
                            elif elt['deriv-folder'] != [''] and elt['deriv-folder']:
                                order[tag_val] = cnt_tot
                                cmd_line += ' ' + elt['tag'] + ' {' + str(cnt_tot) + '}'
                                cnt_tot += 1
                        else:
                            order[tag_val] = cnt_tot
                            cmd_line += ' ' + elt['tag'] + ' {' + str(cnt_tot) + '}'
                            cnt_tot += 1
            elif clef == 'Output':
                if output_dict['multiplesubject'] and output_dict['directory']:
                    cmd_line += ' ' + output_dict['tag'] + ' ' + output_directory
                else:
                    if not output_dict['tag']:
                        order['out'] = cnt_tot
                    else:
                        order[output_dict['tag']] = cnt_tot
                    cmd_line += ' ' + output_dict['tag'] + ' {' + str(cnt_tot) + '}'
                    cnt_tot += 1
                #cmd_line += determine_input_output_type(output_dict, cnt_tot, order)
                #order.append(output_dict)
            elif isinstance(self[clef], bool):
                cmd_line += ' ' + clef
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

    def command_line_base(self, cmd_line_set, mode, output_directory, input_p, output_p):
        self['plugin'] = self.callname
        cmd_end = ''
        if not cmd_line_set:
            cmd_line_set = ' --run'
        cmd_base = self.curr_path + cmd_line_set

        cmd_line, order = self.chaine_parameters(output_directory, input_p, output_p)
        cmd = cmd_base + cmd_line
        return cmd, order

    def chaine_parameters(self, output_directory, input_dict, output_dict):
        jsonfilename = os.path.join(self.derivatives_directory, self['plugin'] + '_parameters' + '.json')
        pref_flag = False
        suff_flag = False

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
        with open(jsonfilename, 'w') as json_file:
            if 'modality' in self and isinstance(self['modality'], list):
                self['modality'] = self['modality'][-1]
                if self['modality'] == 'Ieeg':
                    self['modality'] = 'SEEG'
            json.dump(self, json_file)
        cmd_line = ' ' + jsonfilename

        order = {}
        #Handle the input and output
        cnt_tot = 0
        for cn, elt in enumerate(input_dict):
            tag_val = elt['tag']
            if not elt['tag']:
                tag_val = 'in' + str(cn)
            if elt['multiplesubject'] and elt['type'] == 'dir':
                if not elt.deriv_input:
                    cmd_line += ' ' + elt['tag'] + ' ' + self.bids_directory
                elif elt.deriv_input and (elt['deriv-folder'] and elt['deriv-folder'] != ['']):
                    cmd_line += ' ' + elt['tag'] + ' ' + os.path.join(self.bids_directory, 'derivatives',
                                                                      elt['deriv-folder'][0])
            else:
                if elt.deriv_input:
                    if (elt['deriv-folder'] == [''] or not elt['deriv-folder']) and not elt['optional']:
                        raise ValueError(
                            'The derivative folder for this paramater {} should be mentionned.\n'.format(elt['tag']))
                    elif elt['deriv-folder'] != [''] and elt['deriv-folder']:
                        order[tag_val] = cnt_tot
                        cmd_line += ' ' + elt['tag'] + ' {' + str(cnt_tot) + '}'
                        cnt_tot += 1
                else:
                    order[tag_val] = cnt_tot
                    cmd_line += ' ' + elt['tag'] + ' {' + str(cnt_tot) + '}'
                    cnt_tot += 1
        if output_dict is not None:
            if output_dict['multiplesubject'] and output_dict['directory']:
                cmd_line += ' ' + output_dict['tag'] + ' ' + output_directory
            else:
                if not output_dict['tag']:
                    order['out'] = cnt_tot
                else:
                    order[output_dict['tag']] = cnt_tot
                cmd_line += ' ' + output_dict['tag'] + ' {' + str(cnt_tot) + '}'
                cnt_tot += 1
        if pref_flag:
            order[pref_tag] = cnt_tot
            cmd_line += ' ' + pref_tag + ' {' + str(cnt_tot) + '}'
            cnt_tot += 1
        if suff_flag:
            order['--output_suffix'] = cnt_tot
            cmd_line += ' --output_suffix {' + str(cnt_tot) + '}'
            cnt_tot += 1
        return cmd_line, order

    def verify_log_for_errors(self, input, x=None):
        log_error = ''
        # read log in Documents
        home = os.path.expanduser('~')
        if getpass.getuser() == 'jegou':
            self.anywave_directory = r'Z:\AnyWave\Log'
        else:
            self.anywave_directory = os.path.join(home, 'AnyWave', 'Log')
            if not os.path.exists(self.anywave_directory):
                self.anywave_directory = os.path.join('\\dynaserv', 'home', getpass.getuser(), 'AnyWave', 'Log')
        temp_time = 0
        filename =''
        if os.path.exists(self.anywave_directory):
            with os.scandir(self.anywave_directory) as it:
                for entry in it:
                    time_file = os.path.getctime(entry)
                    if time_file > temp_time:
                        temp_time = time_file
                        filename = entry.path
            f = open(filename, 'r')
            f_cont = f.readlines()
            for elt in f_cont:
                log_error += elt
            f.close()
        else:
            log_error += 'The AnyWave log path was not found.\n'

        return log_error


class Docker(Parameters):
    keylist = ['command_line_base', 'Intermediate', 'Callname']

    def __init__(self, curr_path=None, dev_path=None, callname=None):
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
        if mode == 'automatic':
            if not cmd_line_set:
                cmd_line_set = "matlab -wait -nosplash -nodesktop -r \"cd('" + os.path.dirname(self.curr_path) + "'); "
            cmd_end = '; exit\"'
        elif mode == 'manual':
            if not cmd_line_set:
                cmd_line_set = "matlab -wait -nosplash -nodesktop -r \"cd('" + os.path.dirname(self.curr_path) + "'); "
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
                    tag_val = elt['tag']
                    if not elt['tag']:
                        tag_val = 'in' + str(cn)
                    if elt['multiplesubject'] and elt['type'] == 'dir':
                        if elt['tag']:
                            cmd_line.append("'" + elt['tag'] + "'")
                        if not elt.deriv_input:
                            cmd_line.append("'" + self.bids_directory + "' ")
                        elif elt.deriv_input and (elt['deriv-folder'] and elt['deriv-folder'] != ['']):
                            cmd_line.append("'" + os.path.join(self.bids_directory, 'derivatives',
                                                                              elt['deriv-folder'][0]) + "' ")
                    else:
                        if elt.deriv_input:
                            if (elt['deriv-folder'] == [''] or not elt['deriv-folder']) and not elt['optional']:
                                raise ValueError(
                                    'The derivative folder for this paramater {} should be mentionned.\n'.format(
                                        elt['tag']))
                            elif elt['deriv-folder'] != [''] and elt['deriv-folder']:
                                order[tag_val] = cnt_tot
                                if elt['tag']:
                                    cmd_line.append("'" + elt['tag'] + "'")
                                cmd_line.append("'{" + str(cnt_tot) + "}'")
                                cnt_tot += 1
                        else:
                            order[tag_val] = cnt_tot
                            if elt['tag']:
                                cmd_line.append("'" + elt['tag'] + "'")
                            cmd_line.append("'{" + str(cnt_tot) + "}'")
                            cnt_tot += 1
            elif clef == 'Output':
                if output_dict['multiplesubject'] and output_dict['directory']:
                    if output_dict['tag']:
                        cmd_line.append("'"+output_dict['tag']+"'")
                    cmd_line.append("'" + output_directory + "'")
                else:
                    if not output_dict['tag']:
                        order['out'] = cnt_tot
                    else:
                        order[output_dict['tag']] = cnt_tot
                        cmd_line.append("'"+output_dict['tag']+"'")
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
            mod_dict.copy_values(elt)
            self.append(mod_dict)

    def update_values(self, input_dict, tag, input_param=None):
        for elt in self:
            if elt['tag'] == tag:
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
        def compare_length_multi_input(in_out, idx_in):
            err = ''
            nbr_in = None
            for i in range(0, len(idx_in)-1):
                if len(in_out[i]) != len(in_out[i+1]):
                    err += 'ERROR: The elements in the list don"t have the same size.\n'
            if not err:
                nbr_in = len(in_out[0])
            return err, nbr_in

        def reorder_inputs(in_out, idx_in):
            if all(idx_in[elt]=='file' for elt in idx_in):
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
            tag_val = elt['tag']
            if not elt['tag']:
                tag_val = 'in'+str(cn)
            if tag_val not in order_tag:
                not_inside = True
            else:
                idx = order[tag_val]
            if not not_inside:
                input_att['Input_' + tag_val] = elt.get_input_values(subject_to_analyse, in_out, idx, order_tag[idx])
                # if temp:
                #     if temp != len(in_out[idx]):
                #         raise ValueError('The elements in the list don"t have the same size')
                # else:
                #     temp = len(in_out[idx])
                idx_in[idx] = elt['type']
        sub_to_delete = []
        for sub in in_out:
            if len(idx_in) > 1:
                error, nbr_in = compare_length_multi_input(in_out[sub], idx_in)
                if error:
                    sub_to_delete.append(sub)
                    error_in += error
                    error_in += 'The subject {} won"t be analysed because there is not the same length of inputs.\n'.format(sub)
                else:
                    reorder_inputs(in_out[sub], idx_in)
            else:
                nbr_in = len(in_out[sub][idx])
            temp[sub] = nbr_in
        for sub in sub_to_delete:
            del in_out[sub]
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
    keylist = ['tag', 'multiplesubject', 'modality', 'type']
    keylist_deriv = keylist + ['deriv-folder', 'filetype', 'optional']
    path_key = ['sub', 'ses', 'modality']
    multiplesubject = False
    deriv_input = False

    def copy_values(self, input_dict): #, flag_process=False):
        keys = list(input_dict.keys())
        if not keys == self.keylist and not keys == self.keylist_deriv: #and not flag_process:
            raise KeyError('Your json is not conform.\n')
        else:
            for key in input_dict:
                if key == 'modality':
                    if isinstance(input_dict[key], str):
                        self[key] = []
                        value = input_dict[key].capitalize()
                        self[key].append(value)
                    elif isinstance(input_dict[key], list):
                        value = [elt.capitalize() for elt in input_dict[key]]
                        self[key] = value
                elif key == 'deriv-folder':
                    if isinstance(input_dict[key], str):
                        self[key] = [input_dict[key]]
                    else:
                        self[key] = input_dict[key]
                    self.deriv_input = True
                else:
                    self[key] = input_dict[key]
        if self['multiplesubject'] and self['type'] == 'file':
            raise ValueError('Your json is not conform.\n It is not possible to have files as input and process multiple subject.\n')

    def update_values(self, input_dict):
        for key in input_dict:
            if key in self.keys() and key == 'deriv-folder':
                self[key] = input_dict[key]
        #self['value_selected'] = input_dict

    def get_input_values(self, subject_to_analyse, in_out, idx, tag):#sub, input_param=None):
        def check_dir_existence(bids_directory, chemin):
            chemin_final = os.path.join(self.bids_directory, '\\'.join(chemin))
            if os.path.exists(chemin_final):
                return os.path.normpath(chemin_final)
            else:
                del chemin[-1]
                return check_dir_existence(bids_directory, chemin)

        input_att = {sub: {} for sub in subject_to_analyse['sub']}
        if self.deriv_input: #'deriv-folder' in self.keys():
            if self['deriv-folder'] and self['deriv-folder'] != ['']:
                self.curr_bids.is_pipeline_present(self['deriv-folder'][0])
                if not self.curr_bids.curr_pipeline['isPresent']:
                    raise ValueError(
                        'The derivatives folder {} selected doesn"t exists in the Bids Dataset.\n'.format(
                            self['deriv-folder']))
                #self.read_deriv_fold = subject_to_analyse[self['tag']]['deriv-folder']
            elif (self['deriv-folder'] == [''] or not self['deriv-folder']) and self['optional']:
                return
            else:
                raise ValueError('You have to select a derivatives folder for the input {}'.format(tag))
        if self['type'] == 'file':
            for sub in subject_to_analyse['sub']:
                in_out[sub][idx], input_att[sub] = self.get_subject_files(subject_to_analyse['Input_'+tag], sub)
        elif self['type'] == 'dir':
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
                if self.deriv_input:
                    chemin.append('derivatives\\' + self['deriv-folder'][0])
                    path_key['modality'] = path_key['modality'] + 'Process'
                for key, val in path_key.items():
                    if val and key != 'modality':
                        chemin.append(key+'-'+val)
                    elif val and key == 'modality':
                        chemin.append(val.lower())
                    # elif not val:
                    #     break
                #check the existence of the directory
                in_out[sub][idx] = [check_dir_existence(self.bids_directory, chemin)]
        return input_att

    def get_subject_files(self, subject, sub_id, deriv_reader=None):#, modality, subject_list, curr_bids):
        input_files = []
        temp_att = {}
        if 'modality' not in subject.keys():
            subject['modality'] = self['modality']
        # modality = [elt for elt in bids.ModalityType.get_list_subclasses_names() if elt in subject['modality']]
        # if not modality:
        #     modality = [elt for elt in bids.ModalityType.get_list_subclasses_names() if any(elmt in subject['modality'] for elmt in eval('bids.' + elt + '.allowed_modalities'))]
        if self.deriv_input:
            self.curr_bids.is_pipeline_present(self['deriv-folder'][0])
            for sub in self.curr_bids.curr_pipeline['Pipeline']['SubjectProcess']:
                if sub['sub'] == sub_id:
                    for mod in subject['modality']:
                        if not mod.endswith('Process'):
                            mod = mod + 'Process'
                        for elt in sub[mod]:
                            is_equal = [True]
                            for key in subject:
                                if key == 'modality' or key == 'deriv-folder':
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
                                # elif key == 'fileLoc':
                                #     if elt[key].endswith(self['filetype']):
                                #         is_equal.append(True)
                                #     else:
                                #         is_equal.append(False)
                            if all(is_equal) and elt['fileLoc'].endswith(self['filetype']):
                                key_attributes = [clef for clef in SubjectToAnalyse.keylist if not clef == 'modality']
                                for key in key_attributes:
                                    if key in elt and elt[key] and key not in temp_att:
                                        temp_att[key] = [elt[key]]
                                    elif key in elt and elt[key] and elt[key] not in temp_att[key]:
                                        temp_att[key].append(elt[key])
                                input_files.append(os.path.join(self.bids_directory, elt['fileLoc']))
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
                                if mod == 'Meg' and os.path.isdir(input_files[-1]):
                                    input_files[-1] = os.path.join(input_files[-1], 'c,rfDC')
        #subject.update(temp_att)
        return input_files, temp_att


class Output(Parameters):
    keylist = ['tag', 'multiplesubject', 'directory', 'type', 'extension']
    multiplesubject = False

    def copy_values(self, input_dict, flag_process=False):
        keys = list(input_dict.keys())
        if not keys == self.keylist and not flag_process:
            raise KeyError('Your json is not conform')
        else:
            if (input_dict['type'] == 'dir' and not input_dict['directory']) or (input_dict['type'] == 'file' and input_dict['directory']):
                raise KeyError('The output in your json is not conform due to the type.\n You mention directory: {0} and type: {1}.\n'.format(input_dict['directory'], input_dict['type']))
            for key in keys:
                self[key] = input_dict[key]
        if self['multiplesubject'] and self['type'] == 'file':
            raise ValueError('Your json is not conform.\n It is not possible to have files as output and process multiple subject.\n')

    def update_values(self, input_dict):
        self['value_selected'] = input_dict

    def get_output_values(self, in_out, taille, order, output_directory, idx_in): #sub,
        def create_output_file(output_dir, filename, extension, bids_directory):
            out_file = []
            soft_name = os.path.basename(output_dir).lower()
            soft_name = soft_name.split('-v')[0]
            if "c,rfDC" in filename:
                filename = os.path.dirname(filename)
            dirname, filename = os.path.split(filename)
            trash, dirname = dirname.split(bids_directory + '\\')
            if 'derivatives' in dirname:
                idx = dirname.find('sub-')
                dirname = dirname[idx::]
            file_elt = filename.split('_')
            if isinstance(extension, list):
                for ext in extension:
                    file_elt[-1] = soft_name + ext
                    filename = '_'.join(file_elt)
                    output = os.path.join(output_dir, dirname, filename)
                    os.makedirs(os.path.dirname(output), exist_ok=True)
                    out_file.append(output)
            else:
                file_elt[-1] = soft_name + extension
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
                trash, dirname = dirname.split(bids_directory + '\\')
            else:
                trash, dirname = filename.split(bids_directory+'\\')
            if 'derivatives' in dirname:
                idx = dirname.find('sub-')
                dirname = dirname[idx::]
            out_dir = [os.path.join(output_dir, dirname)]
            os.makedirs(out_dir[0], exist_ok=True)
            return out_dir

        if not self['tag']:
            idx = order['out']
        else:
            idx = order[self['tag']]
        if not self['directory']:
            if self['type'] == 'file':
                if not taille:
                    raise EOFError('No input list to create the output')
                else:
                    for sub in in_out:
                        output_files = []
                        idx_list = list(idx_in.keys())
                        for filename in in_out[sub][idx_list[0]]:
                            out_file = create_output_file(output_directory, filename, self['extension'], self.bids_directory)
                            output_files.append(out_file)
                        in_out[sub][idx] = output_files
            # elif self['type'] == 'sub':
            #     if not self['multiplesubject']:
            #         output_files = sub
        #A revoir avec subject_list
        else:
            if self['multiplesubject']:
                for sub in in_out:
                    in_out[sub][idx] = output_directory #[output_directory] * taille[sub]
            else:
                for sub in in_out:
                    output_files = []
                    idx_list = list(idx_in.keys())
                    for filename in in_out[sub][idx_list[0]]:
                        output_dir = create_output_sub_dir(output_directory, filename, self.bids_directory)
                        output_files.append(output_dir)
                    in_out[sub][idx] = output_files

    def command_arg(self, output_dir, soft_name, subject_list, input_type, input_file_list=None):
        def create_output_file(output_dir, filename, extension, soft_name, bids_directory):
            out_file = []
            soft_name = soft_name.lower()
            dirname, filename = os.path.split(filename)
            trash, dirname = dirname.split(bids_directory + '\\')
            file_elt = filename.split('_')
            if isinstance(extension, list):
                for ext in extension:
                    file_elt[-1] = soft_name + '.' + ext
                    filename = '_'.join(file_elt)
                    output = os.path.join(output_dir, dirname, filename)
                    os.makedirs(os.path.dirname(output), exist_ok=True)
                    out_file.append(output)
            else:
                file_elt[-1] = soft_name + '.' + extension
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
        if not self['directory']:
            if self['type'] == 'file':
                if not input_file_list:
                    raise EOFError('No input list to create the output')
                for filename in input_file_list:
                    out_file = create_output_file(output_dir, filename, self['extension'], soft_name, self.bids_directory)
                    output_file_list.append(out_file)
            elif self['type'] == 'sub':
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

        out_to_return[self['tag']] = output_file_list
        out_to_return.multiplesubject = self.multiplesubject

        return out_to_return


class Arguments(Parameters):
    unit_value = ['default', 'unit']
    read_value = ['read', 'elementstoread', 'multipleselection']
    list_value = ['possible_value', 'multipleselection']
    file_value = ['fileLoc', 'extension']
    bool_value = ['default']
    bids_value = ['readbids', 'type']

    def copy_values(self, input_dict):
        keylist = list(input_dict.keys())
        readbids = []
        if keylist != self.unit_value and keylist != self.read_value and keylist != self.list_value and keylist != self.file_value and keylist != self.bool_value and keylist != self.bids_value:
            raise EOFError(
                'The keys in Parameters of your JSON file are not conform.\n Please modify it according to the given template.\n')
        for key in input_dict:
            self[key] = input_dict[key]
            if key == self.bids_value:
                readbids.append(input_dict[key]['type'])
        return readbids

    def update_values(self, input_dict):
        if not input_dict:
            pass
        elif isinstance(input_dict, list):
            self['value_selected'] = input_dict
        elif isinstance(input_dict, str):
            if input_dict:
                if 'unit' in self.keys():
                    unit = self['unit']
                    if input_dict == unit:
                        pass
                    elif unit and unit in input_dict:
                        self['value_selected'] = input_dict.split(unit)[0]
                    else:
                        self['value_selected'] = input_dict
                    if self['value_selected'] and any(c.isdigit() for c in self['value_selected']):
                        if '.' in self['value_selected'] or ',' in self['value_selected']:
                            self['value_selected'] = float(self['value_selected'])
                        else:
                            self['value_selected'] = int(self['value_selected'])
                elif 'type' in self.keys():
                    unit = self['type']
                    if not input_dict == unit:
                        self['value_selected'] = input_dict
                else:
                    self['value_selected'] = input_dict
        elif isinstance(input_dict, bool):
            self['value_selected'] = input_dict


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
                   elt['tag'] == key.split('_')[1]][0]
            if param[idx]['modality']:
                input_vars[key]['modality'] = param[idx]['modality']
                mod = input_vars[key]['modality'][-1]
            else:
                continue
        else:
            mod = input_vars[key]['modality'][-1]
        if 'deriv-folder' in input_vars[key].keys():
            deriv_folder = input_vars[key]['deriv-folder'][-1]
            if deriv_folder == '' or 'Previous analysis results' in deriv_folder:# or deriv_folder == ['']:
                continue
        # if any(elmt not in bids.ModalityType.get_list_subclasses_names() for elmt in input_vars[key]['modality']):
        #     mod = []
        #     for elmt in input_vars[key]['modality']:
        #         if elmt in bids.ModalityType.get_list_subclasses_names():
        #             mod.append(elmt)
        #         else:
        #             val = [elt for elt in bids.ModalityType.get_list_subclasses_names() if elmt in eval('bids.' + elt + '.allowed_modalities')]
        #             if deriv_folder:
        #                 val = [va for va in val if va in bids.Process.get_list_subclasses_names()]
        #             else:
        #                 val = [va for va in val if va not in bids.Process.get_list_subclasses_names()]
        #             mod.extend(val)
        #     mod = list(set(mod))
        # else:
        #     mod = input_vars[key]['modality']

        # if len(mod) > 1:
        #     err_txt += 'Modalities selected in the input {} are too differents\n.'.format(key)
        #     return warn_txt, err_txt
        # else:
        #     mod = mod[-1]
        keylist = [clef for clef in input_vars[key] if (clef != 'modality' and clef != 'deriv-folder')]

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


class Interface(dict):

    def __init__(self, bids_data):
        self.bids_data = bids_data
        self.subject = [sub['sub'] for sub in self.bids_data['Subject']]
        self.vars_interface()

    def copy_values(self, input_dict):
        for key in input_dict:
            self[key] = input_dict[key]

    def vars_interface(self):
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
        display_dict = {key: value for key, value in req_keys.items() if value or 'age' in key or 'duration' in key}
        # for key, value in req_keys.items():
            # if value:
            #     display_dict[key] = value
            # elif 'age' in key:
            #     display_dict[key] = value
            # elif 'duration' in key:
            #     display_dict[key] = value
        criteria = participant_dict.header
        key_list = display_dict.keys()
        for key in key_list:
            idx = criteria.index(key)
            is_string = False
            display_value = []
            for val_part in participant_dict[1::]:
                is_number = check_numerical_value(val_part[idx])
                if is_number and display_dict[key]:
                    display_value.append(val_part[idx])
                elif is_number:
                    display_value.append('min_' + key)
                    display_value.append('max_' + key)
                    is_string = True
                else:
                    l_elt = val_part[idx].split(', ')
                    for l in l_elt:
                        display_value.append(l)
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
                display_value = list(set(display_value).intersection(set(display_dict[key])))
                if len(display_value) == 1 and not 'n/a' in display_value:
                    self[key] = {}
                    self[key]['attribut'] = 'Label'
                    self[key]['value'] = [value for value in display_value]
                elif len(display_value) > 1:
                    self[key] = {}
                    self[key]['attribut'] = 'Variable'
                    self[key]['value'] = [value for value in display_value]

    def get_parameter(self):
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
                        res_dict[key] = range(minA, maxA)
                else:
                    res_dict[key] = val_temp.get()
                if key in res_dict and key in res_dict[key]:
                    res_dict[key] = res_dict[key].replace('_'+key, '')
            elif att_type == 'Listbox':
                res_dict[key] = val_temp.get()
            elif att_type == 'Bool':
                if val_temp.get() == True:
                    res_dict[key] = True
            elif att_type == 'Label':
                res_dict[key] = val_temp
            elif att_type == 'File':
                if len(val_temp) >1 and val_temp[1]:
                    if isinstance(val_temp[1], list):
                        res_dict[key] = ', '.join(val_temp[1])
                    else:
                        res_dict[key] = val_temp[1]

        return res_dict

    def get_subject_list(self, input_dict):
        subject_list = []
        for elt in self.bids_data['ParticipantsTSV'][1::]:
            elt_in = []
            for key, value in input_dict.items():
                idx_key = self.bids_data['ParticipantsTSV'].header.index(key)
                if isinstance(value, range):
                    elt[idx_key] = elt[idx_key].replace(',', '.')
                    age_p = round(float(elt[idx_key].rstrip('YyMm ')))
                    if age_p in value:
                        elt_in.append(True)
                elif isinstance(value, list):
                    for val in value:
                        if val in elt[idx_key]:
                            elt_in.append(True)
                        else:
                            elt_in.append(False)
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
    def __init__(self, bids_data, parameter_soft=None):
        self.bids_data = bids_data
        if parameter_soft:
            self.parameters = {key: value for key, value in parameter_soft.items() if key not in ['Input', 'Output', 'Callname', 'command_line_base', 'Intermediate']}
            self.vars_interface()

    def vars_interface(self):
        for key in self.parameters:
            self[key] = {}
            if key == 'Mode':
                if len(self.parameters[key]) > 1:
                    self[key]['attribut'] = 'Listbox'
                    self[key]['value'] = self.parameters[key]
                elif len(self.parameters[key]) == 1:
                    self[key]['attribut'] = 'Label'
                    self[key]['value'] = self.parameters[key][-1]
            else:
                keys = list(self.parameters[key].keys())
                if keys == Arguments.unit_value:
                    self[key]['attribut'] = 'StringVar'
                    self[key]['value'] = str(self.parameters[key]['default']) + self.parameters[key]['unit'] + '_' + key
                    self[key]['unit'] = self.parameters[key]['unit']
                elif keys == Arguments.list_value:
                    if self.parameters[key]['multipleselection']:
                        st_type = 'Variable'
                    else:
                        st_type = 'Listbox'
                    self[key]['attribut'] = st_type
                    self[key]['value'] = self.parameters[key]['possible_value']
                elif keys == Arguments.file_value:  # A revoir
                    self[key]['attribut'] = 'File'
                    self[key]['value'] = [self.parameters[key]['extension']]
                elif keys == Arguments.bool_value:
                    self[key]['attribut'] = 'Bool'
                    self[key]['value'] = self.parameters[key]['default']
                elif keys == Arguments.read_value:
                    if self.parameters[key]['multipleselection']:
                        st_type = 'Variable'
                    else:
                        st_type = 'Listbox'
                    self[key]['attribut'] = st_type
                    self[key]['value'] = self.reading_file(key)
                elif keys == Arguments.bids_value:
                    del self[key]
                else:
                    raise EOFError(
                        'The keys in Parameters of your JSON file are not conform.\n Please modify it according to the template given.\n')

    def reading_file(self, key):
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

        def compare_listes(liste_final, liste_file):
            is_same = True
            sX = set(liste_final)
            sY = set(liste_file)
            set_common = sX - sY
            if not set_common == sX:
                is_same = False
            for elt in liste_file:
                if elt not in liste_final:
                    liste_final.append(elt)
            return is_same

        reading_file = self.parameters[key]['read'].strip('*')
        elements = self.parameters[key]['elementstoread']
        mark_to_remove = ['?', '***', '*']
        param = []
        is_same = True
        for subject in os.listdir(self.bids_data.cwdir):
            if subject.endswith(reading_file) and os.path.isfile(os.path.join(self.bids_data.cwdir, subject)):
                file_param = read_file(os.path.join(self.bids_data.cwdir, subject), elements)
                if not param:
                    param = [elt for elt in file_param]
                else:
                    is_same = compare_listes(param, file_param)
                break
            elif subject.startswith('sub') and os.path.isdir(os.path.join(self.bids_data.cwdir, subject)):
                for session in os.listdir(os.path.join(self.bids_data.cwdir, subject)):
                    if os.path.isdir(os.path.join(self.bids_data.cwdir, subject, session)):
                        for mod in os.listdir(os.path.join(self.bids_data.cwdir, subject, session)):
                            if os.path.isdir(os.path.join(self.bids_data.cwdir, subject, session, mod)):
                                with os.scandir(os.path.join(self.bids_data.cwdir, subject, session, mod)) as it:
                                    for entry in it:
                                        if entry.name.endswith(reading_file):
                                            file_param = read_file(entry.path, elements)
                                            if not param:
                                                param = [elt for elt in file_param]
                                            else:
                                                is_same = compare_listes(param, file_param)
                            elif os.path.isfile(
                                    os.path.join(self.bids_data.cwdir, subject, session, mod)) and mod.endswith(
                                    reading_file):
                                file_param = read_file(os.path.join(self.bids_data.cwdir, subject, session, mod),
                                                       elements)
                                if not param:
                                    param = [elt for elt in file_param]
                                else:
                                    is_same = compare_listes(param, file_param)
        param = list(set(param))
        param.sort()
        return [par for par in param if not par in mark_to_remove]


class InputParameterInterface(Interface):
    def __init__(self, bids_data, parameter_soft_input=None):
        self.bids_data = bids_data
        if parameter_soft_input:
            self.parameters = parameter_soft_input
            mod_list = bids.Electrophy.get_list_subclasses_names() + bids.Imaging.get_list_subclasses_names()
            if self.parameters.deriv_input:
                mod_list = bids.ElectrophyProcess.get_list_subclasses_names() + bids.ImagingProcess.get_list_subclasses_names()
            keylist = [elt for key in mod_list for elt in eval('bids.' + key + '.keylist') if not (
                     elt in bids.BidsJSON.get_list_subclasses_names() or elt in bids.BidsTSV.get_list_subclasses_names()
                     or elt in bids.BidsFreeFile.get_list_subclasses_names() or elt.endswith('Loc') or elt.endswith(
                'modality') or elt == 'sub' or elt.endswith('Labels'))] #elt.endswith('JSON') or elt.endswith('TSV')
            self.keylist = list(set(keylist))
            self.vars_interface()

    def vars_interface(self):
        if self.parameters is not None:
            if self.parameters.deriv_input:
                self['deriv-folder'] = dict()
                self['deriv-folder']['attribut'] = 'Listbox'
                deriv_list = [elt for elt in os.listdir(os.path.join(self.bids_data.cwdir, 'derivatives'))if
                                  elt not in ['log', 'parsing', 'parsing_old', 'log_old'] and os.path.isdir(os.path.join(self.bids_data.cwdir, 'derivatives',elt))]
                self['deriv-folder']['value'] = deriv_list
            self['modality'] = dict()
            if self.parameters['modality']:
                if len(self.parameters['modality']) > 1:
                    self['modality']['attribut'] = 'Listbox'
                    self['modality']['value'] = self.parameters['modality']
                else:
                    self['modality']['value'] = self.parameters['modality'][-1]
                    self['modality']['attribut'] = 'Label'
            else:
                self['modality']['attribut'] = 'Listbox'
                self['modality']['value'] = bids.Electrophy.get_list_subclasses_names() + bids.Imaging.get_list_subclasses_names()
        else:
            self = {'modality': {}}
            self['modality']['attribut'] = 'Listbox'
            self['modality']['value'] = bids.Imaging.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names()

        if self['modality']['attribut'] == 'Label':
            modality = [self['modality']['value']]
        else:
            modality = self['modality']['value']
        if not self.parameters.deriv_input:
            for sub in self.bids_data['Subject']:
                for mod in sub:
                    if mod and mod in modality:
                        keys = [elt for elt in self.keylist if elt in eval('bids.' + mod + '.keylist') and elt != 'sub']
                        if mod in bids.Imaging.get_list_subclasses_names() and 'mod' not in keys:
                            keys.append('mod')
                        if sub[mod]:
                            self.get_values(mod, keys, sub)
        else:
            for pip in self.bids_data['Derivatives'][0]['Pipeline']:
                sub_list = [sub for sub in pip['SubjectProcess']]
                for sub in sub_list:
                    for mod in sub:
                        if mod and mod.split('Process')[0] in modality:
                            keys = [elt for elt in self.keylist if
                                    elt in eval('bids.' + mod + '.keylist') and elt != 'sub']
                            if mod in bids.ImagingProcess.get_list_subclasses_names() and 'mod' not in keys:
                                keys.append('mod')
                            if sub[mod]:
                                self.get_values(mod, keys, sub)
        clefs = [key for key in self]
        for key in clefs:
            if self[key]['attribut'] == 'Label' and key not in ['modality', 'ses']:
                del self[key]
        #Ecrire qqch si juste la modality en label et rien d'autre

    def get_values(self, mod, keys, sub):
        for key in keys:
            value = [elt[key] for elt in sub[mod]]
            if key == 'mod':
                value = [elt['modality'] for elt in sub[mod]]
            value = sorted(list(set(value)))
            # if '' in value:
            #     value.remove('')
            if value: #and value[0] is not '':
                # if key == 'modality':
                #     if self[key]['attribut'] == 'Label':
                #         self[key]['value'] = value
                #     else:
                #         self[key]['value'].extend(value)
                if key == 'ses' and '' in value:
                    value.remove('')
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
