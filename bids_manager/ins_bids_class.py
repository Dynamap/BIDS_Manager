#!/usr/bin/python3
# -*-coding:Utf-8 -*

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
#     Authors: Nicolas Roehri, 2018-2019
#              Aude Jegou, 2019-2020

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import dict
from builtins import super
from builtins import open
from builtins import int
from builtins import range
from builtins import str
from future import standard_library
import os
from sys import argv, modules, exc_info
#from sys import modules
import json
from bids_manager import brainvision_hdr as bv_hdr
from datetime import datetime
import pprint
import gzip
import shutil
import random as rnd
import getpass
import platform
standard_library.install_aliases()

try:
    # Python 2
    from __builtin__ import str as builtin_str
except ImportError:
    # Python 3
    from builtins import str as builtin_str

''' Three main bricks: BidsBrick: to handles the modality and high level directories, BidsJSON: to handles the JSON 
sidecars, BidsTSV: to handle the tsv sidecars. '''


class BidsBrick(dict):

    keylist = ['sub']
    required_keys = ['sub']
    required_protocol_keys = None
    access_time = datetime.now()
    time_format = "%Y-%m-%dT%H-%M-%S"
    try:  # python 3
        cwdir = os.getcwd()
    except:  # python 2
        cwdir = os.getcwdu()
    allowed_modalities = []
    state_list = ['valid', 'invalid', 'forced', 'ready']
    curr_state = None
    curr_user = getpass.getuser()

    def __init__(self, keylist=None, required_keys=None):
        """initiate a  dict var for modality info"""
        if keylist:
            self.keylist = keylist
        else:
            self.keylist = self.__class__.keylist
        if required_keys:
            self.required_keys = required_keys
        else:
            self.required_keys = self.__class__.required_keys
        self.curr_state = BidsBrick.curr_state

        for key in self.keylist:
            if key in BidsBrick.get_list_subclasses_names() or key in BidsTSV.get_list_subclasses_names() or key in BidsFreeFile.get_list_subclasses_names():
                self[key] = []
            elif key in BidsJSON.get_list_subclasses_names():
                self[key] = {}
            else:
                self[key] = ''

    def __setitem__(self, key, value):

        if key in self.keylist:
            if key in BidsBrick.get_list_subclasses_names():
                # if value and eval('type(value) == ' + key):
                if value and isinstance(value, eval(key)):
                    # check whether the value is from the correct class when not empty
                    self[key].append(value)
                else:
                    dict.__setitem__(self, key, [])
            elif key in BidsJSON.get_list_subclasses_names():
                if value and isinstance(value, eval(key)):
                    # check whether the value is from the correct class when not empty
                    super().__setitem__(key, value)
                else:
                    dict.__setitem__(self, key, {})
            elif key in BidsTSV.get_list_subclasses_names():
                # if value and eval('type(value) == ' + key):
                if value and isinstance(value, eval(key)):
                    # check whether the value is from the correct class when not empty
                    super().__setitem__(key, value)
                else:
                    dict.__setitem__(self, key, [])
            elif key == 'fileLoc':
                if value.__class__.__name__ in ['str', 'unicode']:  # makes it python 2 and python 3 compatible
                    if value:
                        filename = value
                        if os.path.isabs(value):
                            if BidsBrick.cwdir in value:
                                value = os.path.relpath(value, BidsBrick.cwdir)
                        else:
                            filename = os.path.join(BidsBrick.cwdir, value)
                        if not os.path.exists(filename):
                            str_issue = 'file: ' + str(filename) + ' does not exist.'
                            self.write_log(str_issue)
                            raise FileNotFoundError(str_issue)
                    # This seems useless O_o to be checked...
                    # elif not value == '':
                    #     str_issue = 'fileLoc value ' + str(value) + ' should be a path.'
                    #     self.write_log(str_issue)
                    #     raise TypeError(str_issue)
                    dict.__setitem__(self, key, value)
                else:
                    str_issue = 'fileLoc value ' + str(value) + ' should be a string.'
                    self.write_log(str_issue)
                    raise TypeError(str_issue)
            elif key == 'modality':
                if value:
                    if not self.allowed_modalities or value in self.allowed_modalities:
                        dict.__setitem__(self, key, value)
                    elif isinstance(self, Process) and value not in self.allowed_modalities:
                        self.__class__.allowed_modalities.append(value)
                        dict.__setitem__(self, key, value)
                    else:
                        str_issue = 'modality value ' + str(value) + ' is not allowed. Check ' + \
                                    self.classname() + '.allowed_modalities().'
                        self.write_log(str_issue)
                        raise TypeError(str_issue)
                else:
                    dict.__setitem__(self, key, value)
            elif key == 'run':
                if value:
                    if isinstance(value, int):
                        dict.__setitem__(self, key, str(value).zfill(2))
                    elif value.__class__.__name__ in ['str', 'unicode'] and value.isdigit():
                        dict.__setitem__(self, key, value.zfill(2))
                    else:
                        str_issue = 'run value ' + str(value) + ' should be a digit (integer or string).'
                        self.write_log(str_issue)
                        raise TypeError(str_issue)
                else:
                    dict.__setitem__(self, key, value)
            elif isinstance(value, int):
                dict.__setitem__(self, key, str(value).zfill(2))
            elif value.__class__.__name__ in ['str', 'unicode'] and \
                    (not value or (value.isalnum() and isinstance(self, ModalityType))
                     or not isinstance(self, ModalityType)) or \
                    key in BidsFreeFile.get_list_subclasses_names():
                dict.__setitem__(self, key, value)
            else:
                str_issue = '/!\ key: ' + str(key) + ' should either be an alphanumeric string or an integer /!\ '
                self.write_log(str_issue)
                raise TypeError(str_issue)
        else:
            str_issue = '/!\ Not recognized key: ' + str(key) + ', check ' + self.classname() +\
                        ' class keylist /!\ '
            self.write_log(str_issue)
            raise KeyError(str_issue)

    def __delitem__(self, key):
        if key in self.keylist:
            if key in BidsBrick.get_list_subclasses_names() or key in BidsTSV.get_list_subclasses_names():
                self[key] = []
            elif key in BidsTSV.get_list_subclasses_names():
                self[key] = {}
            else:
                self[key] = ''
        else:
            str_issue = '/!\ Not recognized key: ' + str(key) + ', check ' + self.__class__.__name__ + \
                        ' class keylist /!\ '
            print(str_issue)

    def update(self, input_dict, f=None):
        if isinstance(input_dict, dict):
            for key in input_dict:
                if key not in self.keylist:
                    del (input_dict[key])
                else:
                    self.__setitem__(key, input_dict[key])
            # super().update(input_dict)

    def pop(self, key, val=None):
        if key in self.keylist:
            value = self[key]
            if key in BidsBrick.get_list_subclasses_names() or key in BidsTSV.get_list_subclasses_names():
                self[key] = []
            elif key in BidsTSV.get_list_subclasses_names():
                self[key] = {}
            else:
                self[key] = ''
            return value
        else:
            str_issue = '/!\ Not recognized key: ' + str(key) + ', check ' + self.__class__.__name__ + \
                        ' class keylist /!\ '
            print(str_issue)

    def popitem(self):
        value = []
        for key in self.keylist:
            value.append(self[key])
            if key in BidsBrick.get_list_subclasses_names() or key in BidsTSV.get_list_subclasses_names():
                self[key] = []
            elif key in BidsTSV.get_list_subclasses_names():
                self[key] = {}
            else:
                self[key] = ''
        return value

    def clear(self):
        for key in self.keylist:
            if key in BidsBrick.get_list_subclasses_names() or key in BidsTSV.get_list_subclasses_names():
                self[key] = []
            elif key in BidsTSV.get_list_subclasses_names():
                self[key] = {}
            else:
                self[key] = ''

    def has_all_req_attributes(self, missing_elements=None, nested=True):
        # check if the required attributes are not empty to create
        # the filename (/!\ Json or coordsystem checked elsewhere)
        if not missing_elements:
            missing_elements = ''

        for key in self.keylist:
            if key in BidsDataset.keylist[1:] and key in BidsBrick.get_list_subclasses_names():
                ''' source data, derivatives, code do not have requirements yet'''
                continue
            if self.required_keys:
                if key in self.required_keys and (self[key] == '' or self[key] == []):
                    missing_elements += 'In ' + type(self).__name__ + ', key ' + str(key) + ' is missing.\n'
            if self[key] and isinstance(self[key], list) and nested:
                # check if self has modality brick, if not empty than
                # recursively check whether it has also all req attributes
                for item in self[key]:
                    if issubclass(type(item), BidsBrick):
                        missing_elements = item.has_all_req_attributes(missing_elements)[1]
        return [not bool(missing_elements), missing_elements]

    def get_attributes_from_filename(self, fname=None):
        """ get the attribute from the filename, used when parsing pre-existing bids dataset """

        def parse_filename(mod_dict, file):
            fname_pieces = file.split('_')
            for word in fname_pieces:
                w = word.split('-')
                if len(w) == 2 and w[0] in mod_dict.keys():
                    mod_dict[w[0]] = w[1]
            if 'modality' in mod_dict and not mod_dict['modality']:
                mod_dict['modality'] = fname_pieces[-1]

        if isinstance(self, ModalityType) or isinstance(self, GlobalSidecars):
            if 'fileLoc' in self.keys() and self['fileLoc']:
                filename = self['fileLoc']
            else:
                return
            filename, ext = os.path.splitext(os.path.basename(filename))
            if ext.lower() == '.gz':
                filename, ext = os.path.splitext(filename)
            if ext.lower() in self.allowed_file_formats:
                parse_filename(self, filename)

    def create_filename_from_attributes(self):
        filename = ''
        dirname = ''
        ext = ''
        if isinstance(self, ModalityType) or isinstance(self, GlobalSidecars) or isinstance(self, Scans):
            for key in self.get_attributes(['fileLoc', 'modality']):
                if self[key]:
                    if isinstance(self[key], str):
                        str2add = self[key]
                    else:
                        str2add = str(self[key]).zfill(2)
                    filename += key + '-' + str2add + '_'
            filename += self['modality']
            piece_dirname = []
            piece_dirname += [shrt_name for _, shrt_name in enumerate(filename.split('_')) if
                              shrt_name.startswith('sub-') or shrt_name.startswith('ses-')]
            mod_type = self.classname()
            if isinstance(self, GlobalSidecars):
                mod_type = mod_type.lower().replace(GlobalSidecars.__name__.lower(), '')
            elif isinstance(self, Process):
                mod_type = mod_type.lower().replace(Process.__name__.lower(), '')
            elif isinstance(self, Scans):
                mod_type = ''
            else:
                mod_type = mod_type.lower()
            piece_dirname += [mod_type]
            dirname = os.path.join(*piece_dirname)
            if isinstance(self, Electrophy):
                ext = BidsDataset.converters['Electrophy']['ext'][0]
            elif isinstance(self, Imaging):
                ext = BidsDataset.converters['Imaging']['ext'][0]
            elif isinstance(self, Scans):
                ext = ScansTSV.extension
            elif isinstance(self, Process):
                _, ex = os.path.splitext(self['fileLoc'])
                if ex:
                    ext = ex
                else:
                    if isinstance(self, ImagingProcess):
                        ext = '.nii'
                    elif isinstance(self, ElectrophyProcess):
                        ext = '.vhdr'
                    else:
                        ext = '.tsv'
            else:
                ext = os.path.splitext(self['fileLoc'])[1]
        return filename, dirname, ext

    def get_sidecar_files(self, in_bids_dir=True, input_dirname=None, input_filename=None, import_process=False):
        # find corresponding JSON file and read its attributes and save fileloc
        def find_sidecar_file(sidecar_dict, fname, drname, direct_search):
            piece_fname = fname.split('_')
            if sidecar_dict.inheritance and not direct_search:
                while os.path.dirname(drname) != BidsDataset.dirname:
                    drname = os.path.dirname(drname)
                    if drname.endswith('\\'):
                        sz = len(drname) - 1
                        drname = drname[0:sz]
                    has_broken = False
                    with os.scandir(drname) as it:
                        for idx in range(1, len(piece_fname)):
                            # a bit greedy because some case are not possible but should work
                            # firstly try to find an exact match (all attributes) then try to match fewer attributes
                            j_name = '_'.join(piece_fname[0:-idx] + [sidecar_dict.modality_field]) + \
                                     sidecar_dict.extension
                            for entry in it:
                                entry_fname, entry_ext = os.path.splitext(entry.name)
                                if entry_ext.lower() == '.gz':
                                    entry_fname, entry_ext = os.path.splitext(entry.name)
                                if entry_ext == sidecar_dict.extension and entry_fname.split('_')[-1] == \
                                        sidecar_dict.modality_field:
                                    if entry.name == j_name:
                                        # jsondict['fileLoc'] = entry.path
                                        sidecar_dict.read_file(entry.path)
                                        has_broken = True
                                        break
                            if has_broken:
                                break
                if os.path.dirname(drname) == BidsDataset.dirname:
                    drname = os.path.dirname(drname)
                    piece_fname = [value for _, value in enumerate(piece_fname) if not (value.startswith('sub-') or
                                                                                        value.startswith('ses-'))]
                    has_broken = False
                    with os.scandir(drname) as it:
                        for idx in range(1, len(piece_fname)):
                            j_name = '_'.join(piece_fname[0:-idx] + [sidecar_dict.modality_field]) + \
                                     sidecar_dict.extension
                            for entry in it:
                                entry_fname, entry_ext = os.path.splitext(entry.name)
                                if entry_ext.lower() == '.gz':
                                    entry_fname, entry_ext = os.path.splitext(entry.name)
                                if entry_ext == sidecar_dict.extension and entry_fname.split('_')[-1] == \
                                        sidecar_dict.modality_field:
                                    if entry.name == j_name:
                                        sidecar_dict.read_file(entry.path)
                                        has_broken = True
                                        break
                            if has_broken:
                                break
            else:
                drname = os.path.dirname(drname)
                if drname.endswith('\\'):
                    sz = len(drname) - 1
                    drname = drname[0:sz]
                has_broken = False
                with os.scandir(drname) as it:
                    for idx in range(1, len(piece_fname)):
                        j_name = '_'.join(piece_fname[0:-idx] + [sidecar_dict.modality_field]) + \
                                 sidecar_dict.extension
                        for entry in it:
                            entry_fname, entry_ext = os.path.splitext(entry.name)
                            if entry_ext.lower() == '.gz':
                                entry_fname, entry_ext = os.path.splitext(entry.name)
                            if entry_ext == sidecar_dict.extension and entry_fname.split('_')[-1] == \
                                    sidecar_dict.modality_field:

                                if entry.name == j_name:
                                    # jsondict['fileLoc'] = entry.path
                                    sidecar_dict.read_file(entry.path)
                                    has_broken = True
                                    break
                        if has_broken:
                            break
            sidecar_dict.has_all_req_attributes()

        def find_sidecar_file_process(sidecar_dict, fname, drname):
            drname = os.path.dirname(drname)
            with os.scandir(drname) as it:
                for entry in it:
                    entry_fname, entry_ext = os.path.splitext(entry.name)
                    if entry_ext.lower() == '.gz':
                        entry_fname, entry_ext = os.path.splitext(entry.name)
                    if entry_ext == sidecar_dict.extension and entry_fname.startswith(fname):
                        sidecar_dict.read_file(entry.path)
                        break
                sidecar_dict.has_all_req_attributes()

        #  firstly, check whether the subclass needs a JSON or a TSV files
        sidecar_flag = [value for _, value in enumerate(self.keylist) if value in
                        BidsSidecar.get_list_subclasses_names()]

        if isinstance(self, BidsBrick) and sidecar_flag:
            if in_bids_dir:
                if 'fileLoc' in self.keys() and self['fileLoc']:
                    rootdir, filename = os.path.split(self['fileLoc'])
                    if 'sourcedata' in rootdir:
                        # only look for sidecar if in raw folder
                        return
                    main_dirname = BidsDataset.dirname
                else:
                    self.write_log('Need file location first to find sidecars ( file attribute: ' +
                                   str(self.get_attributes()) + ')')
            else:
                filename = input_filename
                rootdir = ''
                main_dirname = input_dirname

            filename, ext = os.path.splitext(filename)
            if ext.lower() == '.gz':
                filename, ext = os.path.splitext(filename)
            for sidecar_tag in sidecar_flag:
                if 'modality' in self and not eval(sidecar_tag + '.modality_field'):
                    sdcr_tmp = eval(sidecar_tag + '(modality_field=self["modality"])')
                else:
                    sdcr_tmp = eval(sidecar_tag + '()')
                if self[sidecar_tag]:
                    #  if info are given in modJSON or TSV in data2import prior to importation
                    self[sidecar_tag].copy_values(sdcr_tmp, simplify_flag=False)
                else:
                    self[sidecar_tag] = sdcr_tmp
                if import_process:
                    fname, ext = os.path.splitext(self['fileLoc'])
                    find_sidecar_file_process(self[sidecar_tag], fname, os.path.join(main_dirname, rootdir, filename))
                else:
                    find_sidecar_file(self[sidecar_tag], filename, os.path.join(main_dirname, rootdir, filename),
                                  direct_search=not in_bids_dir)
                self[sidecar_tag].simplify_sidecar(required_only=False)

    def save_as_json(self, savedir, file_start=None, write_date=True, compress=True):
        # \t*\[\n\t*(?P<name>[^\[])*?\n\t*\]
        if os.path.isdir(savedir):
            if not file_start:
                file_start = ''
            else:
                if file_start.__class__.__name__ in ['str', 'unicode']:  # makes it pyton2 and python3 compatible
                    if not file_start.endswith('_'):
                        file_start += '_'
                else:
                    str_issue = 'Input file beginning is not a string; json saved with default name.'
                    self.write_log(str_issue)
            if write_date:
                date_string = '_' + BidsBrick.access_time.strftime(self.time_format)
            else:
                date_string = ''

            json_filename = file_start + type(self).__name__.lower() + date_string + '.json'

            output_fname = os.path.join(savedir, json_filename)
            with open(output_fname, 'w') as f:
                # json.dump(self, f, indent=1, separators=(',', ': '), ensure_ascii=False)
                json_str = json.dumps(self, indent=1, separators=(',', ': '), ensure_ascii=False, sort_keys=False)
                # r"(?P<open_table>\[\n\t{1,}\[)(?P<content>.*?)(?P<close_table>\]\n\t{1,}\])"
                # This solution is way too slow. need to reimplemente a json writer...
                # if isinstance(self, BidsDataset):
                #     #  make the table more readible (otherwise each elmt is isolated on a line...)
                #     exp = r'\s*(?P<name>\[\n\s*[^\[\{\]]*?\n\s*\])'
                #     matched_exp = re.findall(exp, json_str)
                #     for elmt in matched_exp:
                #         json_str = json_str.replace(elmt, elmt.replace('\n', ''))
                f.write(json_str)
            if platform.system() == 'Linux':
                chmod_recursive(output_fname, 0o777)
            if compress:
                with open(output_fname, 'rb') as f_in, \
                        gzip.open(output_fname + '.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                os.remove(output_fname)
                if platform.system() == 'Linux':
                    chmod_recursive(output_fname, 0o777)
        else:
            raise TypeError('savedir should be a directory.')

    def __str__(self):
        return pprint.pformat(self)

    def classname(self):
        return self.__class__.__name__

    def get_attributes(self, keys2remove=None):
        attr_dict = {key: self[key] for key in self.keys() if key not in
                     BidsBrick.get_list_subclasses_names() + BidsSidecar.get_list_subclasses_names()}
        if keys2remove:
            if not isinstance(keys2remove, list):
                keys2remove = [keys2remove]
            for key in keys2remove:
                if key in attr_dict.keys():
                    del(attr_dict[key])
        return attr_dict

    def copy_values(self, input_dict):
        # attr_dict = {key: self[key] for _, key in enumerate(self.keys()) if key not in
        #              BidsBrick.get_list_subclasses_names() and key not in BidsSidecar.get_list_subclasses_names()}
        # self.update(attr_dict)
        for key in input_dict:
            if not input_dict[key]:
                continue
            if key in BidsBrick.get_list_subclasses_names():
                if key in GlobalSidecars.get_list_subclasses_names():
                    flag_globalsidecar = True
                else:
                    flag_globalsidecar = False
                for elmt in input_dict[key]:
                    if flag_globalsidecar:
                        mod_dict = eval(key + '(elmt["fileLoc"])')
                    else:
                        mod_dict = eval(key + '()')
                    mod_dict.copy_values(elmt)
                    self[key] = mod_dict
            elif key in BidsSidecar.get_list_subclasses_names():
                if 'modality' in self and not eval(key + '.modality_field'):
                    self[key] = eval(key + '(modality_field=self["modality"])')
                else:
                    self[key] = eval(key + '()')
                self[key].copy_values(input_dict[key])
            else:
                self[key] = input_dict[key]

    def get_modality_sidecars(self, cls=None):
        if cls is None:
            sidecar_dict = {key: self[key] for key in self if key in BidsSidecar.get_list_subclasses_names()}
        elif issubclass(cls, BidsSidecar):
            sidecar_dict = {key: self[key] for key in self if key in cls.get_list_subclasses_names()}
        else:
            sidecar_dict = []
            print('Class input is not a subclass of BidsSidecars!')
        return sidecar_dict

    # def extract_sidecares_from_sourcedata(self):
    #     filename, dirname, ext = self.create_filename_from_attributes()
    #
    #     if not Data2Import.dirname or not Data2Import.dirname:
    #         str_issue = 'Need import and bids directory to be set.'
    #         self.write_log(str_issue)
    #         raise NotADirectoryError(str_issue)
    #     if isinstance(self, Imaging):
    #         converter_path = BidsDataset.converters['Imaging']['path']
    #         cmd_line_base = '""' + converter_path + '"' + " -b y -ba y -m y -z n -f "
    #         cmd_line = cmd_line_base + filename + ' -o ' + Data2Import.dirname + ' ' + \
    #                    os.path.join(Data2Import.dirname, self['fileLoc']) + '"'
    #     elif isinstance(self, Electrophy):
    #         converter_path = BidsDataset.converters['Electrophy']['path']
    #         attr_dict = self.get_attributes(['fileLoc', 'modality'])
    #         name_cmd = ' '.join(['--bids_' + key + ' ' + attr_dict[key] for key in attr_dict if attr_dict[key]])
    #
    #         cmd_line = '""' + converter_path + '"' + ' --seegBIDS "' + \
    #                    os.path.join(Data2Import.dirname, self['fileLoc']) + '" ' + name_cmd + \
    #                    ' --bids_dir "' + Data2Import.dirname + '" --bids_output sidecars"'
    #     else:
    #         str_issue = 'Sidecars from ' + os.path.basename(self['fileLoc']) + ' cannot be extracted!!'
    #         self.write_log(str_issue)
    #         return
    #
    #     os.system(cmd_line)
    #     # list_filename = [filename + ext for ext in conv_ext]
    #     dict_copy = eval(self.classname() + '()')
    #     set_cwd = BidsBrick.cwdir
    #     if not BidsBrick.cwdir == Data2Import.dirname:
    #         BidsBrick.cwdir = Data2Import.dirname
    #
    #     dict_copy.copy_values(self)
    #     dict_copy.get_sidecar_files(in_bids_dir=False, input_dirname=Data2Import.dirname,
    #                                 input_filename=filename)
    #     BidsBrick.cwdir = set_cwd
    #
    #     return dict_copy.get_modality_sidecars()

    def check_requirements(self, specif_subs=None):

        def get_amount_of_file(sub_mod_list, type_dict, modality):
            if isinstance(type_dict, dict):
                type_dict = [type_dict]
            # add empty keys to type dict empty_keys = [key for key in keylist if key not in type_req]

            amount = 0
            if sub_mod_list:
                for type_req in type_dict:
                    if 'modality' in type_req and type_req['modality'] == 'photo':
                        keylist = Photo.keylist
                    else:
                        keylist = eval(modality + '.keylist')
                    # add empty keys to type_req dict for sake of comparison with modality dict
                    [type_req.__setitem__(key, '') for key in keylist if key not in type_req and
                     key not in ['sub', 'fileLoc'] + BidsSidecar.get_list_subclasses_names()]
                    non_specif_keys = [key for key in type_req if type_req[key] == '_']

                    # empty_keys = [key for key in keylist if key not in type_req]
                    # reduced_dict = {key: type_req[key] for key in type_req if not type_req[key] == '_'}
                    for sub_mod in sub_mod_list:
                        attr_dict = sub_mod.get_attributes(['sub', 'fileLoc'])
                        # replace value for non specific keys by '_' in mod attribute dict if not empty for sake of
                        # comparison (ex: 'run': '01' by run: '_' but 'run': '' remains unchanged)
                        [attr_dict.__setitem__(key, '_') for key in non_specif_keys if key in attr_dict and attr_dict[key]]
                        if attr_dict == type_req:
                            amount += 1
            return amount

        def check_dict_from_req(sub_mod_list, mod_req, modality, sub_name):
            type_dict = mod_req['type']
            amount = get_amount_of_file(sub_mod_list, type_dict, modality)

            if isinstance(mod_req['amount'], (int, dict)):
                if isinstance(mod_req['amount'], int):
                    req_amount = mod_req['amount']
                else:
                    req_amount = get_amount_of_file(sub_mod_list, mod_req['amount'], modality)

                if amount == 0:
                    str_iss = 'Subject ' + sub_name + ' in modality '+ modality + ' does not have files of type: ' + str(type_dict) + '.'
                elif amount < req_amount:
                    str_iss = 'Subject ' + sub_name + ' misses ' + str(req_amount-amount) \
                                + ' files of type: ' + str(type_dict) + '.'
                else:
                    return True
            else:
                str_iss = 'For subject ' + sub_name + ', the amount parameter for ' + str(type_dict) + \
                          ' is wrongly set in modality ' + modality + '. It should be an integer or a dictionary.'

            self.write_log(str_iss)
            return False

        def get_group_from_elecname(tsv):
            if not isinstance(tsv, (ChannelsTSV, ElecTSV)):
                str_issue = 'Input is not of class ChannelsTSV or ElecTSV'
                BidsDataset.write_log(str_issue)
                raise TypeError(str_issue)

            if 'group' in tsv.header:
                idx_elec_name = tsv.header.index('group')
                groupnm = [line[idx_elec_name] for line in tsv[1:]]
            else:
                groupnm = []
                idx_elec_name = tsv.header.index('name')
                for line in tsv[1:]:
                    str_group = [c for c in line[idx_elec_name] if not c.isdigit()]
                    if str_group:
                        groupnm.append(''.join(str_group))
                    else:  # case where the electrode name is a number (EGI)
                        groupnm.append(line[idx_elec_name])
            return groupnm

        if isinstance(self, BidsDataset) and self.requirements and self.requirements['Requirements']:
            self.write_log(10 * '=' + '\nCheck requirements\n' + 10 * '=')
            key_words = self.requirements.keywords
            participant_idx = self['ParticipantsTSV'].header.index('participant_id')
            present_sub_list = [line[participant_idx].replace('sub-', '') for line in self['ParticipantsTSV'][1:]]
            sub_list = present_sub_list
            if specif_subs:
                # if one want to check the requirements for a specific subject only, then specif_sub should be in
                # sub_list and then sublist become the specific subject otherwise check each subject
                if isinstance(specif_subs, str) and specif_subs in present_sub_list:
                    sub_list = [specif_subs]
                elif isinstance(specif_subs, list) and all(sub in present_sub_list for sub in specif_subs):
                    sub_list = specif_subs
            check_list = [[word.replace(key_words[0], ''), idx]
                          for idx, word in enumerate(self['ParticipantsTSV'].header) if word.endswith(key_words[0]) and
                          not word == 'Subject' + key_words[0]]
            subject_ready_idx = self['ParticipantsTSV'].header.index('Subject_ready')
            integrity_list = [[word.replace(key_words[1], ''), idx]
                              for idx, word in enumerate(self['ParticipantsTSV'].header) if word.endswith(key_words[1])]

            if sub_list and check_list:
                for bidsbrick_key in check_list:
                    if bidsbrick_key[0] in ModalityType.get_list_subclasses_names() + \
                            GlobalSidecars.get_list_subclasses_names():
                        for sub in sub_list:
                            self.is_subject_present(sub)
                            sub_index = self.curr_subject['index']
                            curr_sub_mod = self['Subject'][sub_index][bidsbrick_key[0]]
                            bln_list = []
                            for mod_requirement in self.requirements['Requirements']['Subject'][bidsbrick_key[0]]:
                                flag_req = check_dict_from_req(curr_sub_mod, mod_requirement, bidsbrick_key[0], sub)
                                bln_list.append(flag_req)
                            parttsv_idx = present_sub_list.index(sub)
                            self['ParticipantsTSV'][1+parttsv_idx][bidsbrick_key[1]] = str(all(bln_list))

            if sub_list and integrity_list:
                for bidsintegrity_key in integrity_list:
                    elec_class_name = bidsintegrity_key[0] + 'ElecTSV'
                    channel_class_name = bidsintegrity_key[0] + 'ChannelsTSV'
                    for sub in sub_list:
                        # initiate to True and mark False for any issue
                        self.is_subject_present(sub)
                        sub_index = self.curr_subject['index']
                        parttsv_idx = present_sub_list.index(sub)
                        self['ParticipantsTSV'][1 + parttsv_idx][bidsintegrity_key[1]] = str(True)
                        curr_sub_mod = self['Subject'][sub_index][bidsintegrity_key[0]]
                        ref_elec = []
                        sdcr_list = self['Subject'][sub_index][bidsintegrity_key[0] + 'GlobalSidecars']

                        if not sdcr_list or not [brick[elec_class_name] for brick in sdcr_list if
                                                 brick['modality'] == 'electrodes']:
                            str_issue = 'Subject ' + sub + ' does not have electrodes.tsv file for ' +\
                                        bidsintegrity_key[0] + '.'
                            self.write_log(str_issue)
                            self['ParticipantsTSV'][1 + parttsv_idx][bidsintegrity_key[1]] = \
                                str(False)
                            continue

                        elect_tsv = [brick[elec_class_name] for brick in sdcr_list if brick['modality'] == 'electrodes']

                        # several electrodes.tsv can be found (e.g. for several space)
                        for tsv in elect_tsv:  # how are different implantation handled? 2 SEEG or classical and hd-EEG
                            if not ref_elec:
                                groupname = get_group_from_elecname(tsv)
                                [ref_elec.append(name) for name in groupname if name not in ref_elec]
                                ref_elec.sort()
                            else:  #!!!!!!!!!! here there is something wrong when group does not exist.
                                curr_elec = []
                                groupname = get_group_from_elecname(tsv)
                                [curr_elec.append(name) for name in groupname if name not in curr_elec]
                                curr_elec.sort()
                                if not curr_elec == ref_elec:
                                    ref_elec = []

                        if not ref_elec:
                            str_issue = 'Subject ' + sub + ' has inconsistent electrodes.tsv files ' +\
                                        bidsintegrity_key[0] + '.'
                            self.write_log(str_issue)
                            self['ParticipantsTSV'][1 + parttsv_idx][bidsintegrity_key[1]] = \
                                str(False)
                            continue

                        for mod in curr_sub_mod:
                            curr_elec = []
                            curr_type = []
                            """ list all the channels of the modality type end check whether their are in the reference 
                            list of electrodes"""
                            elecname = get_group_from_elecname(mod[channel_class_name])
                            idx_chan_type = mod[channel_class_name].header.index('type')
                            elec_type = [line[idx_chan_type] for line in mod[channel_class_name][1:]]
                            for nme, typ in zip(elecname, elec_type):
                                if nme not in curr_elec and not nme == BidsSidecar.bids_default_unknown and\
                                        typ in mod.mod_channel_type:
                                    curr_elec.append(nme)
                                    curr_type.append(typ)

                            miss_matching_elec = [{'name': name, 'type': curr_type[cnt]}
                                                  for cnt, name in enumerate(curr_elec) if name not in ref_elec]
                            if miss_matching_elec:
                                str_issue = 'File ' + os.path.basename(mod['fileLoc']) + \
                                            ' has inconsistent electrode name(s) ' + str(miss_matching_elec) + '.'
                                self.write_log(str_issue)
                                # filepath = mod.create_filename_from_attributes()

                                self.issues.add_issue('ElectrodeIssue', sub=sub,
                                                      fileLoc=mod['fileLoc'],
                                                      RefElectrodes=ref_elec, MismatchedElectrodes=miss_matching_elec,
                                                      mod=bidsintegrity_key[0])
                                self['ParticipantsTSV'][1 + parttsv_idx][bidsintegrity_key[1]] = str(False)

            self.issues.check_with_latest_issue()
            self.issues.save_as_json()

            for sub in sub_list:
                idx = [elmt for elmt in integrity_list + check_list
                       if self['ParticipantsTSV'][1 + present_sub_list.index(sub)][elmt[1]] == 'False']
                if not idx:
                    self.write_log('!!!!!!!!!!! Subject ' + sub + ' is ready !!!!!!!!!!!')
                    self.is_subject_present(sub)
                    self['Subject'][self.curr_subject['index']].curr_state = 'ready'
                    self['ParticipantsTSV'][1 + present_sub_list.index(sub)][subject_ready_idx] = str(True)
                else:
                    self['ParticipantsTSV'][1 + present_sub_list.index(sub)][subject_ready_idx] = str(False)
            self['ParticipantsTSV'].write_file()
            self.save_as_json()

    def convert(self, dest_change=None):
        filename, dirname, ext = self.create_filename_from_attributes()
        list_filename=None
        process_flag=False

        if not Data2Import.dirname or not Data2Import.dirname:
            str_issue = 'Need import and bids directory to be set.'
            self.write_log(str_issue)
            raise NotADirectoryError(str_issue)
        if isinstance(self, (Imaging, ImagingProcess)):
            converter_path = BidsDataset.converters['Imaging']['path']
            conv_ext = BidsDataset.converters['Imaging']['ext']
            # by default dcm2niix does not overwrite file with same names but adds a letter to it (inptnamea,inptnameb)
            # # therefore one should firstly test whether a file with the same input name already exist and remove it to
            # # avoid risking to import this one rather than the one which was converted and added a suffix
            # for ext in conv_ext:
            #     if os.path.exists(os.path.join(Data2Import.dirname, filename + ext)):
            #         os.remove(os.path.join(Data2Import.dirname, filename + ext))
            # cmd_line_base = '""' + converter_path + '"' + " -b y -ba y -m y -z n -f "
            # cmd_line = cmd_line_base + filename + ' -o "' + Data2Import.dirname + '" "' + os.path.join(
            #     Data2Import.dirname, self['fileLoc']) + '"'
            # issue with an MRI using dcm2niix but not with dicm2nii.m which is now preferred (after compilation)
            if os.path.isdir(os.path.join(Data2Import.dirname, self['fileLoc'])):
                cmd_line_base = '""' + converter_path + '" '
                cmd_line = cmd_line_base + ' "' + os.path.join(Data2Import.dirname, self['fileLoc']) + '" "' + \
                           os.path.join(Data2Import.dirname, self['fileLoc']) + '" .nii"'
                os.system(cmd_line)
                # as dicm2nii does not take filename as input, one has to find the newest .nii and sidecar files and rename
                # them
                list_files = os.listdir(os.path.join(Data2Import.dirname, self['fileLoc']))
                nii_file = [file for file in list_files if os.path.splitext(file)[1] == '.nii']
                if len(nii_file) > 1:
                    raise FileExistsError('Several Nifti files were created')
                nii_fname = os.path.splitext(nii_file[0])[0]
                [shutil.move(os.path.join(Data2Import.dirname, self['fileLoc'], file),
                             os.path.join(Data2Import.dirname, filename + os.path.splitext(file)[1]))
                 for file in list_files if os.path.splitext(file)[0] == nii_fname]
                os.remove(os.path.join(Data2Import.dirname, self['fileLoc'], 'dcmHeaders.mat'))
            elif os.path.isfile(os.path.join(Data2Import.dirname, self['fileLoc'])) and \
                    ext in ImagingProcess.allowed_file_formats:#self['fileLoc'].endswith('.nii'):
                os.makedirs(os.path.join(dest_change, dirname), exist_ok=True)
                shutil.copy(os.path.join(Data2Import.dirname, self['fileLoc']),
                            os.path.join(Data2Import.dirname, filename + ext))
                list_filename = [filename + ext]
                if dest_change is not None:
                    process_flag = True
            else:
                raise FileExistsError('Imaging file format is not correct and cannot be imported.')
        elif isinstance(self, Electrophy):
            converter_path = BidsDataset.converters['Electrophy']['path']
            conv_ext = BidsDataset.converters['Electrophy']['ext']
            attr_dict = self.get_attributes(['fileLoc'])
            name_cmd = ' '.join(['--bids_' + key + ' ' + attr_dict[key] for key in attr_dict if attr_dict[key]])
            if os.path.isdir(os.path.join(Data2Import.dirname, self['fileLoc'])):
                input_cmd = '--input_dir "'
                bids_format = ''
                conv_ext = ['']
            elif os.path.isfile(os.path.join(Data2Import.dirname, self['fileLoc'])) and (isinstance(self, Ieeg) or isinstance(self, Eeg)):
                input_cmd = '--input_file "'
                bids_format = ' --bids_format vhdr'

            #Revoir la commande pour linux, voir si fonctionne de la mm façon
            cmd_line = '""' + converter_path + '"' + ' --toBIDS ' + input_cmd + \
                        os.path.join(Data2Import.dirname, self['fileLoc']) + '" ' + ' --output_dir "' + \
                        Data2Import.dirname + '" ' + name_cmd + bids_format + '"'

            # # cmd_line = '""' + converter_path + '"' + ' --seegBIDS "' +\
            # #            os.path.join(Data2Import.dirname, self['fileLoc']) + '" ' +\
            # #            name_cmd + ' --bids_dir "' + Data2Import.dirname + '" --bids_format vhdr"'
            # cmd_line = '""' + converter_path + '"' + ' --toBIDS --input_file "' + \
            #            os.path.join(Data2Import.dirname, self['fileLoc']) + '" ' + ' --output_dir "' + \
            #            Data2Import.dirname + '" ' + name_cmd + ' --bids_format vhdr"'

            os.system(cmd_line)
        elif isinstance(self, GlobalSidecars):
            fname = filename + os.path.splitext(self['fileLoc'])[1]
            if not os.path.exists(os.path.join(BidsDataset.dirname, dirname)):
                os.makedirs(os.path.join(BidsDataset.dirname, dirname))
            try:
                shutil.move(os.path.join(Data2Import.dirname, self['fileLoc']), os.path.join(
                    BidsDataset.dirname, dirname, fname))
            except:
                shutil.copy(os.path.join(Data2Import.dirname, self['fileLoc']), os.path.join(
                    BidsDataset.dirname, dirname, fname))
            return [fname]
        elif isinstance(self, ElectrophyProcess):
            name, ext = os.path.splitext(self['fileLoc'])
            fname = filename + ext
            if not os.path.exists(os.path.join(dest_change, dirname)):
                os.makedirs(os.path.join(dest_change, dirname))
            if os.path.exists(os.path.join(Data2Import.dirname, name+'.json')) and not self['ElectrophyProcessJSON']:
                self['ElectrophyProcessJSON'] = ElectrophyProcessJSON(jsonfile=os.path.join(Data2Import.dirname, name+'.json'))
            shutil.copy(os.path.join(Data2Import.dirname, self['fileLoc']), os.path.join(Data2Import.dirname, fname))
            list_filename = [fname]
            process_flag = True
            #return [fname]
        else:
            str_issue = os.path.basename(self['fileLoc']) + ' cannot be converted!'
            self.write_log(str_issue)
            raise TypeError(str_issue)

        if list_filename is None:
            list_filename = [filename + ext for ext in conv_ext]
        if not os.path.exists(os.path.join(Data2Import.dirname, list_filename[0])):#if not all(os.path.exists(os.path.join(Data2Import.dirname, file)) for file in list_filename):
            str_issue = 'file: ' + str(filename) + ' does not exist after conversion. Please verify the ' + \
                        ' converter and the original file (' + os.path.join(Data2Import.dirname, self['fileLoc']) + ')'
            raise FileNotFoundError(str_issue)
        # store sidecars that were already present in the data2import (those have higher priority than the ones created
        # by converters)
        curr_sdcrs = self.get_modality_sidecars()
        tmp_mod = getattr(modules[__name__], self.classname())()
        tmp_mod.copy_values(curr_sdcrs)  # necessary because curr_sdcrs is the sidecars of self and will change the same
        # way (mutable) this makes two separate objects
        self.get_sidecar_files(in_bids_dir=False, input_dirname=Data2Import.dirname,
                               input_filename=filename, import_process=process_flag)
        for key in curr_sdcrs:
            # replace the sidecars obtained by converter by sidecars found in data2import if not empty (as they may have
            # additional info)
            if tmp_mod[key]:
                self[key] = tmp_mod[key]
        if not os.path.exists(os.path.join(BidsDataset.dirname, dirname)):
            os.makedirs(os.path.join(BidsDataset.dirname, dirname))
        for fname in list_filename:
            if os.path.exists(os.path.join(Data2Import.dirname, fname)):
                if dest_change:
                    if not os.path.exists(os.path.join(dest_change, dirname)):
                        os.makedirs(os.path.join(dest_change, dirname))
                    shutil.move(os.path.join(Data2Import.dirname, fname),
                                os.path.join(dest_change, dirname, fname))
                else:
                    shutil.move(os.path.join(Data2Import.dirname, fname),
                            os.path.join(BidsDataset.dirname, dirname, fname))
        return list_filename

    def is_empty(self):
        if isinstance(self, MetaBrick):
            for sub in self['Subject']:
                if not sub.is_empty():
                    return False
            if self['Derivatives']:
                for pip in self['Derivatives'][-1]['Pipeline']:
                    for sub in pip['SubjectProcess']:
                        if not sub.is_empty():
                            return False
            return True
        else:
            if isinstance(self, GlobalSidecars):
                init_inst = type(self)(self['fileLoc'])
            else:
                init_inst = type(self)()
            return self == init_inst

    def difference(self, brick2compare, reverse=False):
        """ compare two BidsBricks from the same type and returns a dictionary of the key and values of the
        brick2compare that are different from self. /!\ this operation is NOT commutative"""
        if type(self) is type(brick2compare) or (isinstance(brick2compare, dict) and
                                                 not isinstance(brick2compare, (BidsBrick, BidsSidecar))):
            if reverse:
                return {key: brick2compare[key] for key in brick2compare if key not in self or
                        not self[key] == brick2compare[key]}
            else:
                return {key: brick2compare[key] for key in self if key not in brick2compare or
                        not self[key] == brick2compare[key]}
        else:
            err_str = 'The type of the two instance to compare are different (' + self.classname() + ', '\
                      + type(brick2compare).__name__ + ')'
            self.write_log(err_str)
            raise TypeError(err_str)

    def write_command(self, brick2compare, added_info=None):
        if added_info and not isinstance(added_info, dict):
            print('added_info should be a dict. Set to None.')
            added_info = None
        diff = self.difference(brick2compare)
        cmd_str = ', '.join([str(k + '="' + diff[k] + '"') for k in diff])
        if added_info:
            cmd_str += ',' + ', '.join([str(k + '="' + str(added_info[k]) + '"') for k in added_info])
        return cmd_str

    def fileparts(self):
        if isinstance(self, ModalityType) and self['fileLoc']:
            filename, ext = os.path.splitext(os.path.basename(self['fileLoc']))
            dirname = os.path.dirname(self['fileLoc'])
            return dirname, filename, ext
        else:
            return None, None, None

    @classmethod
    def clear_log(cls):
        if cls == BidsDataset or cls == Data2Import:
            cls.curr_log = ''

    @classmethod
    def get_list_subclasses_names(cls):
        sub_classes_names = []
        for subcls in cls.__subclasses__():
            sub_classes_names.append(subcls.__name__)
            sub_classes_names.extend(subcls.get_list_subclasses_names())
        return sub_classes_names

    def write_log(self, str2write):

        if BidsDataset.dirname:
            main_dir = BidsDataset.dirname
        elif Data2Import.dirname:
            main_dir = Data2Import.dirname
        else:
            main_dir = BidsBrick.cwdir

        log_path = os.path.join(main_dir, 'derivatives', 'log')
        log_filename = 'bids_' + BidsBrick.access_time.strftime(BidsBrick.time_format) + '.log'
        if not os.path.isdir(log_path):  # test whether the folder already exist, otherwise make it
            os.makedirs(log_path)
        if not os.path.isfile(os.path.join(log_path, log_filename)):
            cmd = 'w'
            str2write = 10*'=' + '\n' + 'Current User: ' + self.curr_user + '\n' + self.access_time.strftime(
                "%Y-%m-%dT%H:%M:%S") + '\n' + 10*'=' + '\n' + str2write
        else:
            cmd = 'a'
        with open(os.path.join(log_path, log_filename), cmd) as file:
            file.write(str2write + '\n')
            BidsDataset.curr_log += str2write + '\n'
            Data2Import.curr_log += str2write + '\n'
        if platform.system() == 'Linux':
            chmod_recursive(os.path.join(log_path, log_filename), 0o777)
        print(str2write)
        if BidsDataset.update_text:
            BidsDataset.update_text(str2write, delete_flag=False)


class BidsSidecar(object):
    bids_default_unknown = 'n/a'
    extension = ''
    inheritance = True
    modality_field = []
    allowed_modalities = []
    keylist = []
    required_keys = []
    required_protocol_keys = []

    def __init__(self, modality_field=None):
        """initiate a  dict of n/a strings for JSON Imaging"""
        self.is_complete = False
        if not modality_field:
            self.modality_field = self.__class__.modality_field
        else:
            self.modality_field = modality_field

    def read_file(self, filename):
        """read sidecar file and store in self according to its class (BidsJSON, BidsTSV, BidsFreeFile)"""
        if os.path.isfile(filename):
            if isinstance(self, BidsJSON):
                if os.path.splitext(filename)[1] == '.json':
                    with open(filename, 'r') as file:
                        read_json = json.load(file)
                        for key in read_json:
                            if (key in self.keylist and self[key] == BidsSidecar.bids_default_unknown) or \
                                    key not in self.keylist:
                                self[key] = read_json[key]
                else:
                    raise TypeError('File is not ".json".')
            elif isinstance(self, BidsTSV):
                if os.path.splitext(filename)[1] == '.tsv':
                    with open(os.path.join(filename), 'r') as file:
                        tsv_header_line = file.readline()
                        tsv_header = tsv_header_line.strip().split("\t")
                        if len([word for word in tsv_header if word in self.required_fields]) < \
                                len(self.required_fields):
                            issue_str = 'Header of ' + os.path.basename(filename) +\
                                        ' does not contain the required fields.'
                            print(issue_str)
                        #to get into account the header that need to be add at the end of the participantsTSV
                        temp_header = [elt for elt in tsv_header if elt not in self.required_fields]
                        self.header = self.required_fields + temp_header
                        self[:] = []  # not sure if useful
                        for line in file:
                            self.append({tsv_header[cnt]: val for cnt, val in enumerate(line.strip().split("\t"))})
                else:
                    raise TypeError('File is not ".tsv".')
            elif isinstance(self, BidsFreeFile):
                self.clear()
                try:
                    with open(os.path.join(filename), 'r') as file:
                        for line in file:
                            self.append(line.replace('\n', ''))
                except UnicodeDecodeError:
                    with open(os.path.join(filename), 'rb') as file:
                        for line in file:
                            self.append(line)
            else:
                raise TypeError('Not readable class input ' + self.classname() + '.')

    def simplify_sidecar(self, required_only=True):
        """remove fields that have 'n/a' and are not required or if required_only=True keep only required fields."""
        if isinstance(self, BidsJSON):
            list_key2del = []
            for key in self:
                if (self[key] == BidsJSON.bids_default_unknown and key not in self.required_keys) or \
                        (required_only and key not in self.required_keys):
                    list_key2del.append(key)
            for key in list_key2del:
                del(self[key])

    def copy_values(self, sidecar_elmt, simplify_flag=True):
        if isinstance(self, BidsJSON):
            # attr_dict = {key: sidecar_elmt[key] for key in sidecar_elmt.keys() if (key in self.keylist
            #              and self[key] == BidsSidecar.bids_default_unknown) or key not in self.keylist}
            # change into this otherwise cannot modify dataset_description.json (to test)
            attr_dict = {key: sidecar_elmt[key] for key in sidecar_elmt.keys()}
            self.update(attr_dict)
        elif isinstance(self, BidsTSV) and isinstance(sidecar_elmt, list):
            if sidecar_elmt and len([word for word in sidecar_elmt[0] if word in self.required_fields]) >= \
                    len(self.required_fields):
                self.header = sidecar_elmt[0]
                self[:] = []
                for line in sidecar_elmt[1:]:
                    self.append({sidecar_elmt[0][cnt]: val for cnt, val in enumerate(line)})
        elif isinstance(self, BidsFreeFile):
            if not isinstance(sidecar_elmt, list):
                sidecar_elmt = [sidecar_elmt]
            for line in sidecar_elmt:
                self.append(line)
        if simplify_flag:
            self.simplify_sidecar(required_only=False)

    def has_all_req_attributes(self):  # check if the required attributes are not empty
        self.is_complete = True
        missing_elements = ''
        if 'required_keys' in dir(self) and self.required_keys:
            for key in self.required_keys:
                if key not in self or self[key] == BidsSidecar.bids_default_unknown:
                    missing_elements += 'In ' + type(self).__name__ + ', key ' + str(key) + ' is missing.\n'
        self.is_complete = not bool(missing_elements)
        return [self.is_complete, missing_elements]

    def classname(self):
        return self.__class__.__name__

    @classmethod
    def get_list_subclasses_names(cls):
        sub_classes_names = []
        for subcls in cls.__subclasses__():
            sub_classes_names.append(subcls.__name__)
            sub_classes_names.extend(subcls.get_list_subclasses_names())
        return sub_classes_names


class BidsFreeFile(BidsSidecar, list):

    def write_file(self, freefilename):
        if isinstance(self[0], bytes):
            with open(os.path.join(freefilename), 'wb') as file:
                for line in self:
                    file.write(line)
            self.clear()
        else:
            with open(os.path.join(freefilename), 'w') as file:
                for line in self:
                    file.write(line + '\n')
        if platform.system() == 'Linux':
            chmod_recursive(freefilename, 0o777)


class BidsJSON(BidsSidecar, dict):

    extension = '.json'
    modality_field = ''
    keylist = []

    def __init__(self, keylist=None, required_keys=None, modality_field=None):
        """initiate a  dict of n/a strings for JSON Imaging"""
        # if not modality_field:
        #     self.modality_field = self.__class__.modality_field
        # else:
        #     self.modality_field = modality_field
        super().__init__(modality_field=modality_field)
        self.is_complete = False
        if not keylist:
            self.keylist = self.__class__.keylist
        else:
            self.keylist = keylist
        if not required_keys:
            self.required_keys = self.__class__.required_keys
        else:
            self.required_keys = required_keys
        for item in self.keylist:
            self[item] = BidsJSON.bids_default_unknown

    def difference(self, brick2compare):
        """ different compare two BidsBricks from the same type and returns a dictionary of the key and values of the
        brick2compare that are different from self. /!\ this operation is NOT commutative"""
        if type(self) is type(brick2compare):
            return {key: brick2compare[key] for key in self if key in brick2compare and
                    not self[key] == brick2compare[key]}
        else:
            err_str = 'The type of the two instance to compare are different (' + self.classname() + ', '\
                      + type(brick2compare).__name__ + ')'
            self.write_log(err_str)
            raise TypeError(err_str)

    def write_command(self, brick2compare, added_info=None):
        if added_info and not isinstance(added_info, dict):
            print('added_info should be a dict. Set to None.')
            added_info = None
        diff = self.difference(brick2compare)
        cmd_list = []
        for k in diff:
            if isinstance(diff[k], str):
                cmd_list.append(str(k + '="' + diff[k] + '"'))
            else:
                cmd_list.append(str(k + '=' + str(diff[k])))
        cmd_str = ', '.join(cmd_list)
        if added_info:
            cmd_str += ',' + ', '.join([str(k + '="' + str(added_info[k]) + '"') for k in added_info])
        return cmd_str

    def write_file(self, jsonfilename):
        if os.path.splitext(jsonfilename)[1] == '.json':
            with open(jsonfilename, 'w') as f:
                # json.dump(self, f, indent=2, separators=(',', ': '), ensure_ascii=False)
                json_str = json.dumps(self, indent=1, separators=(',', ': '), ensure_ascii=False, sort_keys=False)
                f.write(json_str)
            if platform.system() == 'Linux':
                chmod_recursive(jsonfilename, 0o777)
        else:
            raise TypeError('File ' + jsonfilename + ' is not ".json".')


class ModalityType(BidsBrick):
    required_keys = BidsBrick.required_keys + ['fileLoc']

    def get_bids_dir_from_filename(self):
        if not self['fileLoc']:
            raise TypeError('There is no filename set for this object.')
        if not self['sub']:
            self.get_attributes_from_filename()
        if not self['sub']:
            raise TypeError(self['fileLoc'] + ' is incorrect since there is no subject attribute.')
        dirname = os.path.dirname(self['fileLoc'])
        dname_splt = dirname.split('sub-' + self['sub'])
        if not len(dname_splt) == 2:
            raise NotADirectoryError(dirname + ' is not a correct Bids directory.')
        else:
            return dname_splt[0]


class Imaging(ModalityType):
    pass


class Electrophy(ModalityType):
    channel_type = ['EEG', 'VEOG', 'HEOG', 'EOG', 'ECG', 'EMG', 'TRIG', 'AUDIO', 'EYEGAZE', 'PUPIL', 'MISC', 'SYSCLOCK']#['EEG', 'ECOG', 'SEEG', 'DBS', 'VEOG', 'HEOG', 'EOG', 'ECG', 'EMG', 'TRIG', 'AUDIO', 'PD', 'EYEGAZ',
                    #'PUPIL', 'MISC', 'SYSCLOCK', 'ADC', 'DAC', 'REF', 'OTHER']


class ImagingJSON(BidsJSON):
    keylist = ['Manufacturer', 'ManufacturersModelName', 'DeviceSerialNumber', 'StationName', 'SoftwareVersions',
                'HardcopyDeviceSoftwareVersion', 'MagneticFieldStrength', 'ReceiveCoilName', 'ReceiveCoilActiveElements',
               'GradientSetType', 'MRTransmitCoilSequence', 'MatrixCoilMode', 'CoilCombinationMethod',
               'PulseSequenceType', 'ScanningSequence', 'SequenceVariant', 'ScanOptions', 'SequenceName', 'PulseSequenceDetails',
               'NonlinearGradientCorrection', 'NumberShots', 'ParallelReductionFactorInPlane',
               'ParallelAcquisitionTechnique', 'PartialFourier', 'PartialFourierDirection', 'RepetitionTime', 'PhaseEncodingDirection',
               'EffectiveEchoSpacing', 'TotalReadoutTime', 'EchoTime', 'EchoTrainLength', 'InversionTime', 'SliceTiming',
               'SliceEncodingDirection', 'SliceThickness', 'DwellTime', 'FlipAngle', 'MultibandAccelerationFactor', 'NegativeContrast',
               'AnatomicalLandmarkCoordinates', 'InstitutionName', 'InstitutionAddress', 'InstitutionalDepartmentName']
                #'WaterFatShift', ,
    required_keys = []


class ElectrophyJSON(BidsJSON):
    keylist = ['TaskName', 'Manufacturer', 'ManufacturersModelName', 'TaskDescription', 'Instructions', 'CogAtlasID',
               'CogPOID', 'InstitutionName', 'InstitutionAddress', 'DeviceSerialNumber', 'PowerLineFrequency',
               'ECOGChannelCount', 'SEEGChannelCount', 'EEGChannelCount', 'EOGChannelCount', 'ECGChannelCount',
               'EMGChannelCount', 'MiscChannelCount', 'TriggerChannelCount', 'RecordingDuration', 'RecordingType',
               'EpochLength', 'DeviceSoftwareVersion', 'SubjectArtefactDescription', 'iEEGPlacementScheme',
               'iEEGReferenceScheme', 'Stimulation', 'Medication']
    required_keys = ['TaskName', 'Manufacturer', 'PowerLineFrequency']


class Process(ModalityType):
    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'run', 'proc', 'desc', 'modality', 'fileLoc']
    required_keys = ModalityType.required_keys
    required_protocol_keys = []
    allowed_file_formats = ['.tsv', '.txt', '.mat']

    def __init__(self):
        super().__init__()


class ProcessJSON(BidsJSON):
    keylist = []
    required_keys = ['Description', 'Sources', 'User', 'Date']


class ImagingProcess(Process):
    keylist = Process.keylist + ['proc', 'desc', 'hemi', 'space', 'label']
    allowed_modalities = ['mask', 'dseg', 'probseg', 'dparc']
    allowed_file_formats = Process.allowed_file_formats + ['.nii', '.nii.gz', '.gii', '.pial', '.surf.gii']

    def check_files_conformity(self):
        pass


class ImagingProcessJSON(ProcessJSON):
    keylist = ['Description', 'Sources', 'RawSources', 'SpatialReference', 'ReferenceIndex', 'SkullStripped', 'Type', 'Manual', 'Atlas', 'LabelMap']
    required_keys = []#SpatialReference', 'ReferenceIndex', 'SkullStripped', 'RawSources'


class ElectrophyProcess(Process):
    keylist = Process.keylist + ['ElectrophyProcessJSON']
    allowed_modalities = ['annotations', 'meg', 'eeg', 'ieeg', 'proj', 'epochs', 'average', 'mixing', 'components']
    allowed_file_formats = Process.allowed_file_formats + ['.npy', '.h5', '.vhdr', '.edf', '.set', '.ades']

    def check_files_conformity(self):
        if self['fileLoc'].endswith('.tsv'):
            if self['modality'] in ['average', 'epochs']:
                self['AverageTSV'] = AverageTSV()
                self['AverageTSV'].read_file(self['fileLoc'])
            else:
                self['ElectrophyProcessTSV'] = AverageTSV()
                self['ElectrophyProcessTSV'].read_file(self['fileLoc'])


class ElectrophyProcessJSON(ProcessJSON):
    keylist = ['Description', 'IntendedFor', 'Sources', 'Author', 'LabelDescription']
    required_keys = ['Description', 'IntendedFor']
    detrending_keys = ['Detrending']
    filter_keys = ['FilterType', 'HighCutoff', 'LowCutoff', 'HighCutoffDefinition', 'LowCutoffDefinition',
                   'FilterOrder', 'Direction', 'DirectionDescription']
    downsample_keys = ['SamplingFrequency', 'IsDownsampled']
    average_keys = ['BaselineCorrection', 'BaselineCorrectionMethod', 'BaselinePeriod']

    def __init__(self, jsonfile=None, flagfilter=False, flagdown=False, flagdetendring=False, modality_field=None):
        self.keylist = self.required_keys
        if flagfilter:
            self.keylist = self.keylist + self.filter_keys
        if flagdown:
            self.keylist = self.keylist + self.downsample_keys
        if flagdetendring:
            self.keylist = self.keylist + self.detrending_keys
        super().__init__(keylist=self.keylist, modality_field=modality_field)
        if jsonfile:
            self.read_file(jsonfile)


class BidsTSV(BidsSidecar, list):

    extension = '.tsv'
    modality_field = ''
    required_fields = []
    header = []

    def __init__(self, header=None, required_fields=None, modality_field=None):
        """initiate a  table containing the header"""
        self.is_complete = False
        super().__init__(modality_field=modality_field)
        if not header:
            self.header = self.__class__.header
        else:
            self.header = header
        if not required_fields:
            self.required_fields = self.__class__.required_fields
        else:
            self.required_fields = required_fields

        super().append(self.header)

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            if key.stop or key.step:
                raise NotImplementedError(type(self).__name__ + 'do not handle slice only integers.')
            elif not key.start:
                idx = 0
            elif key.start < len(self):
                idx = key.start
            else:
                raise IndexError('List index out of range; list length = ' + str(len(self)) + '.')
        elif isinstance(key, int) and key < len(self):
            idx = key
        else:
            raise IndexError('List index out of range; list length = ' + str(len(self)) + '.')
        if isinstance(value, dict):
            lines = self[key]
            for key in value:
                if key in self.header:
                    lines[self.header.index(key)] = str(value[key])
                else:
                    print('Key ' + str(key) + ' is not in the header')
            super().__setitem__(idx, lines)
        elif not value:
            del(self[:])
            # super().append(self.header)
        else:
            raise TypeError('Input should be a dict with at least keys in required_keys and not more than '
                            'those of the header.')

    def __delitem__(self, key):
        if isinstance(key, int) and key == 0:
            return
        elif isinstance(key, slice) and key.start == 0 or not key.start:
            super().__setitem__(0, self.header)
            key = slice(1, key.stop, key.step)
        super().__delitem__(key)

    def append(self, dict2append):
        if not isinstance(dict2append, dict):
            raise TypeError('The element to be appended has to be a dict instance.')
        lines = [self.bids_default_unknown]*len(self.header)
        for key in dict2append:
            if key in self.header:
                if dict2append[key] == '' or dict2append[key] is None:
                    dict2append[key] = BidsTSV.bids_default_unknown
                lines[self.header.index(key)] = str(dict2append[key])
        super().append(lines)

    def write_file(self, tsvfilename):
        if os.path.splitext(tsvfilename)[1] == '.tsv':
            with open(tsvfilename, 'w') as file:
                for _, line in enumerate(self):
                    file.write('\t'.join(line) + '\n')
            if platform.system() == 'Linux':
                chmod_recursive(tsvfilename, 0o777)
        else:
            raise TypeError('File is not ".tsv".')

    def has_all_req_attributes(self):  # check if the required attributes are not empty
        self.is_complete = False  # To be implemented, stay False for the moment
        return [self.is_complete, '']

    def clear(self):
        super().clear()
        self.append({elmt: elmt for elmt in self.header})

    def __str__(self):
        str2print = super().__str__()
        str2print = str2print.replace('], [', '],\n[')
        return str2print

    def find_lines_which(self, key, value, key2=None):
        if key not in self.header:
            err_str = 'Key ' + str(key) + 'not found in header.'
            raise TypeError(err_str)
        if key2 and key2 not in self.header:
            err_str = 'Key ' + str(key2) + 'not found in header.'
            raise TypeError(err_str)
        idx_key = self.header.index(key)
        if not key2:
            return [line for line in self[1:] if line[idx_key] == value]
        else:
            idx_key2 = self.header.index(key2)
            return [line[idx_key2] for line in self[1:] if line[idx_key] == value]

    @staticmethod
    def createalias(subname=None, numsyl=3):
        rnd.seed(subname)
        alias = ''
        consonants = 'zrtpdfklmvbn'
        consonants = consonants.upper()
        num_cons = len(consonants)-1
        vowels = 'aeiou'
        vowels = vowels.upper()
        num_voy = len(vowels)-1
        order = rnd.randint(0, 2)
        for syl in range(0, numsyl):
            if order == 1:
                alias = alias + consonants[rnd.randint(0, num_cons)]
                alias = alias + vowels[rnd.randint(0, num_voy)]
            else:
                alias = alias + vowels[rnd.randint(0, num_voy)]
                alias = alias + consonants[rnd.randint(0, num_cons)]
        alias = alias + datetime.now().strftime('%y')
        return alias


class EventsTSV(BidsTSV):

    required_fields = ['onset', 'duration']
    header = required_fields + ['sample', 'trial_type', 'response_time', 'stim_file', 'value', 'HED']
    modality_field = 'events'


class ChannelsTSV(BidsTSV):
    """Store the info of the #_channels.tsv, listing amplifier metadata such as channel names, types, sampling
    frequency, and other information. Note that this may include non-electrode channels such as trigger channels."""

    header = ['name', 'type', 'units', 'sampling_frequency', 'low_cutoff', 'high_cutoff', 'notch', 'reference', 'group',
              'description', 'status', 'status_description', 'software_filters']
    required_fields = ['name', 'type', 'units', 'sampling_frequency', 'low_cutoff', 'high_cutoff', 'notch', 'reference']
    modality_field = 'channels'


class GlobalSidecars(BidsBrick):
    keylist = BidsBrick.keylist + ['ses', 'space', 'modality', 'fileLoc']
    complementary_keylist = []
    required_keys = BidsBrick.required_keys
    allowed_file_formats = ['.tsv', '.json']

    # def __new__(cls, filename):
    #     pass

    def __init__(self, filename):
        """initiates a  dict var for ieeg info"""
        filename = filename.replace('.gz', '')
        filename, ext = os.path.splitext(filename)
        if ext.lower() in ['.json', '.tsv']:
            comp_key = [value for counter, value in enumerate(self.complementary_keylist) if value in
                        BidsSidecar.get_list_subclasses_names() and eval(value + '.extension') ==
                        ext.lower()]
            super().__init__(keylist=self.__class__.keylist + comp_key,
                             required_keys=self.__class__.required_keys)
            self['modality'] = getattr(modules[__name__], comp_key[0]).modality_field
            self['fileLoc'] = filename + ext
        # elif ext in self.allowed_file_formats and filename.split('_')[-1] == 'photo':
        else:
            photo_key = [value for value in self.complementary_keylist if value in
                         BidsBrick.get_list_subclasses_names()][0]
            if ext.lower() in eval(photo_key + '.allowed_file_formats'):
                super().__init__(keylist=eval(photo_key + '.keylist'), required_keys=eval(photo_key + '.required_keys'))
                self['modality'] = 'photo'
                self['fileLoc'] = filename + ext
            else:
                err_str = 'Not recognise file type for ' + self.classname() + '.'
                self.write_log(err_str)
                raise TypeError(err_str)


class Photo(BidsBrick):
    keylist = BidsBrick.keylist + ['ses', 'acq', 'modality', 'fileLoc']
    required_keys = BidsBrick.required_keys + ['modality']
    allowed_file_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.pdf', '.ppt', '.pptx']
    readable_file_format = allowed_file_formats
    modality_field = 'photo'

    def __init__(self):
        BidsBrick().__init__()
        self['modality'] = self.__class__.modality_field


''' A special class for setting the requirements of a given BIDS dataset '''


class Requirements(BidsBrick):
    keywords = ['_ready', '_integrity']

    def __init__(self, full_filename=None):

        if full_filename:
            self['Requirements'] = dict()
            with open(full_filename, 'r') as file:
                json_dict = json.load(file)
                if 'Requirements' in json_dict.keys():
                    self['Requirements'] = json_dict['Requirements']
                if 'Readers' in json_dict.keys():
                    BidsDataset.readers = json_dict['Readers']
                    self['Readers'] = json_dict['Readers']
                if 'Converters' in json_dict.keys():
                    BidsDataset.converters = json_dict['Converters']
                    self['Converters'] = json_dict['Converters']
        else:
            self['Requirements'] = dict()

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)

    def update(self, input_dict, f=None):
        dict.update(input_dict, f=None)

    def save_as_json(self, savedir=None, file_start=None, write_date=True, compress=True):
        savedir = os.path.join(BidsDataset.dirname, 'code')
        if not os.path.exists(savedir):
            os.makedirs(savedir)
        super().save_as_json(savedir, file_start=None, write_date=False, compress=False)

    def make_option_dict(self, key, flag_process=False):
        if flag_process:
            stradd = 'Process'
            key = key.split(stradd)[0]
        else:
            stradd=''
        req = self['Requirements']
        if key not in ModalityType.get_list_subclasses_names() or key not in self['Requirements'].keys() or \
                'keys' not in self['Requirements'][key].keys():
            return dict()
        new_brick = getattr(modules[__name__], key+stradd)()
        options = dict()
        mod_dict = self['Requirements'][key]['keys']
        if not isinstance(mod_dict, dict):
            return dict()
        for k in mod_dict:
            if k in new_brick.keylist:
                if not isinstance(mod_dict[k], list):
                    options[k] = [mod_dict[k]]
                else:
                    options[k] = mod_dict[k]
        options['modality'] = new_brick.allowed_modalities
        if isinstance(new_brick, DwiProcess):
            options['model'] = new_brick.allowed_model
        return options


class ProcessTSV(BidsTSV):
    pass


class AnatomicalLabels(ProcessTSV):
    required_fields = ['index', 'name']
    header = required_fields + ['abbr', 'mapping', 'color']
    #Add something to control the name and the abbreviation value, should use the one in Bids specifications


class ElectrophyProcessTSV(ProcessTSV):
    required_fields = ['onset', 'duration', 'label']
    header = required_fields + ['channels', 'absolute_time']
    recommended_labels = ['artifact', 'motion', 'flux_jump', 'line_noise', 'muscle', 'epilepsy_preictal', 'epilepsy_seizure',
                          'epilepsy_postictal', 'epileptiform_single', 'epileptiform_run', 'eye_blink', 'eye_movement',
                          'eye_fixation', 'sleep_N1', 'sleep_N2', 'sleep_N3', 'sleep_REM', 'sleep_wake', 'sleep_spindle',
                          'sleep_k-complex', 'scorelabeled']


class AverageTSV(ElectrophyProcessTSV):
    required_fields = ['duration', 'zero_time']
    header = required_fields + ['trial_type', 'latency', 'number_averages', 'HED']


''' The different modality bricks, subclasses of BidsBrick. '''

""" iEEG brick with its file-specific (IeegJSON, IeegChannelsTSV) and global sidecar 
(IeegCoordSysJSON, IeegElecTSV or IeegPhoto) files. """


class Ieeg(Electrophy):

    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'run', 'proc', 'modality', 'fileLoc', 'IeegJSON',
                                   'IeegChannelsTSV', 'IeegEventsTSV']
    required_keys = Electrophy.required_keys + ['task', 'modality']
    allowed_modalities = ['ieeg']
    allowed_file_formats = ['.edf', '.vhdr']# '.set'
    readable_file_formats = allowed_file_formats + ['.trc'] #'.ades', '.mat', '.eeg', '.mff',
    channel_type = ['ECOG', 'SEEG', 'DBS', 'PD', 'ADC', 'DAC', 'REF', 'OTHER'] + Electrophy.channel_type
    mod_channel_type = ['ECOG', 'SEEG']
    required_protocol_keys = []

    def __init__(self):
        super().__init__()
        self['modality'] = 'ieeg'


class IeegJSON(ElectrophyJSON):
    keylist = ['TaskName', 'Manufacturer', 'ManufacturersModelName', 'TaskDescription', 'Instructions', 'CogAtlasID',
               'CogPOID', 'InstitutionName', 'InstitutionAddress', 'DeviceSerialNumber', 'PowerLineFrequency',
               'ECOGChannelCount', 'SEEGChannelCount', 'EEGChannelCount', 'EOGChannelCount', 'ECGChannelCount',
               'EMGChannelCount', 'MiscChannelCount', 'TriggerChannelCount', 'RecordingDate', 'RecordingDuration',
               'RecordingType', 'EpochLength', 'DeviceSoftwareVersion', 'SubjectArtefactDescription',
               'iEEGPlacementScheme', 'iEEGReferenceScheme', 'ElectricalStimulation', 'ElectricalStimulationParameters',
               'Medication', 'iEEGReference', 'SamplingFrequency', 'SoftwareFilters']
    required_keys = ['TaskName', 'PowerLineFrequency', 'SoftwareFilters', 'iEEGReference', 'SamplingFrequency']


class IeegChannelsTSV(ChannelsTSV):
    """Store the info of the #_channels.tsv, listing amplifier metadata such as channel names, types, sampling
    frequency, and other information. Note that this may include non-electrode channels such as trigger channels."""

    required_fields = ['name', 'type', 'units', 'low_cutoff', 'high_cutoff']
    header = required_fields + ['reference', 'group', 'sampling_frequency', 'description', 'notch', 'status',
                                'status_description']
    modality_field = 'channels'


class IeegEventsTSV(EventsTSV):
    """Store the info of the #_events.tsv."""
    pass


class IeegElecTSV(BidsTSV):
    required_fields = ['name', 'x', 'y', 'z', 'size']
    header = required_fields + ['material', 'manufacturer', 'group', 'hemisphere'] + ['type', 'impedance', 'dimension']
    modality_field = 'electrodes'


class IeegCoordSysJSON(BidsJSON):
    required_keys = ['iEEGCoordinateSystem', 'iEEGCoordinateUnits']
    keylist = required_keys + ['iEEGCoordinateSystemDescription', 'iEEGCoordinateProcessingDescription',
                               'iEEGCoordinateProcessingReference', 'IntendedFor']

    modality_field = 'coordsystem'


class IeegPhoto(Photo):
    pass


class IeegGlobalSidecars(GlobalSidecars):
    complementary_keylist = ['IeegElecTSV', 'IeegCoordSysJSON', 'IeegPhoto']
    required_keys = BidsBrick.required_keys
    allowed_file_formats = ['.tsv', '.json'] + IeegPhoto.allowed_file_formats
    allowed_modalities = [eval(elmt).modality_field for elmt in complementary_keylist]
    required_protocol_keys = []


""" EEG brick with its file-specific (EegJSON, EegChannelsTSV) and global sidecar 
(EegCoordSysJSON, EegElecTSV or EegPhoto) files. """


class Eeg(Electrophy):

    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'run', 'proc', 'modality', 'fileLoc', 'EegJSON',
                                   'EegChannelsTSV', 'EegEventsTSV']
    required_keys = Electrophy.required_keys + ['task', 'modality']
    allowed_modalities = ['eeg']
    allowed_file_formats = ['.edf', '.vhdr']#, '.set'
    readable_file_formats = allowed_file_formats + ['.trc', '.fif', '.ds'] #, '.mff', '.eeg', '.ades', '.cnt', '.mat',
    channel_type = Electrophy.channel_type + ['GSR', 'REF', 'RESP', 'TEMP']
    mod_channel_type = ['EEG']
    required_protocol_keys = []

    def __init__(self):
        super().__init__()
        self['modality'] = 'eeg'


class EegJSON(ElectrophyJSON):
    required_keys = ['TaskName', 'EEGReference', 'SamplingFrequency', 'PowerLineFrequency', 'SoftwareFilters']
    keylist = required_keys + ['Manufacturer', 'ManufacturersModelName', 'TaskDescription', 'Instructions', 'CogAtlasID',
               'CogPOID', 'InstitutionName', 'InstitutionAddress', 'DeviceSerialNumber', 'CapManufacturer', 'CapManufacturersModelName', 'ECOGChannelCount', 'EEGChannelCount', 'EOGChannelCount', 'ECGChannelCount',
               'EMGChannelCount', 'MiscChannelCount', 'TriggerChannelCount', 'RecordingDuration', 'RecordingType',
               'EpochLength', 'EEGGround', 'HeadCircumference', 'SoftwareVersions', 'HardwareFilters',
                               'SubjectArtefactDescription', 'EEGPlacementScheme']


class EegChannelsTSV(ChannelsTSV):
    """Store the info of the #_channels.tsv, listing amplifier metadata such as channel names, types, sampling
    frequency, and other information. Note that this may include non-electrode channels such as trigger channels."""
    required_fields = ['name', 'type', 'units']
    header = required_fields + ['sampling_frequency', 'low_cutoff', 'high_cutoff', 'notch', 'reference', 'group',
              'description', 'status', 'status_description', 'software_filters']

    modality_field = 'channels'


class EegEventsTSV(EventsTSV):
    """Store the info of the #_events.tsv."""
    pass


class EegElecTSV(BidsTSV):
    required_fields = ['name', 'x', 'y', 'z']
    header = required_fields + ['type', 'material', 'impedance']
    modality_field = 'electrodes'


class EegCoordSysJSON(BidsJSON):
    required_keys = ['EEGCoordinateSystem', 'EEGCoordinateUnits', 'EEGCoordinateSystemDescription']
    keylist = required_keys + ['IntendedFor', 'FiducialsDescription', 'FiducialsCoordinates', 'FiducialsCoordinateSystem',
                               'FiducialsCoordinateUnits', 'FiducialsCoordinateSystemDescription', 'AnatomicalLandmarkCoordinates',
                               'AnatomicalLandmarkCoordinateSystem', 'AnatomicalLandmarkCoordinateUnits', 'AnatomicalLandmarkCoordinateSystemDescription']

    modality_field = 'coordsystem'


class EegPhoto(Photo):
    pass


class EegGlobalSidecars(GlobalSidecars):
    complementary_keylist = ['EegElecTSV', 'EegCoordSysJSON', 'EegPhoto']
    required_keys = BidsBrick.required_keys
    allowed_file_formats = ['.tsv', '.json'] + EegPhoto.allowed_file_formats
    allowed_modalities = [eval(elmt).modality_field for elmt in complementary_keylist]


""" Anat brick with its file-specific sidecar files."""


class Anat(Imaging):

    keylist = BidsBrick.keylist + ['ses', 'acq', 'ce', 'rec', 'run', 'mod', 'modality', 'fileLoc', 'AnatJSON']
    required_keys = Imaging.required_keys + ['modality']
    allowed_modalities = ['T1w', 'T2w', 'T1rho', 'T1map', 'T2map', 'T2star', 'FLAIR', 'PD', 'Pdmap', 'PDT2', 'inplaneT1'
                          , 'inplaneT2', 'angio', 'defacemask', 'CT']
    allowed_file_formats = ['.nii']
    readable_file_formats = allowed_file_formats + ['.dcm']
    required_protocol_keys = []

    def __init__(self):
        super().__init__()


class AnatJSON(ImagingJSON):
    keylist = ImagingJSON.keylist + ['ContrastBolusIngredient', 'NiftiDescription']


class AnatProcess(ImagingProcess):
    keylist = BidsBrick.keylist + ['ses', 'acq', 'ce', 'rec', 'run', 'mod', 'proc', 'desc', 'hemi', 'space', 'volspace', 'label', 'modality', 'fileLoc', 'AnatProcessJSON', 'AnatomicalLabels']
    required_keys = Anat.required_keys
    allowed_modalities = ImagingProcess.allowed_modalities + ['wm', 'smoothwm', 'pial', 'midthickness', 'inflated', 'vinflated', 'sphere', 'flat', 'curv', 'thickness', 'area', 'dist', 'defects', 'sulc', 'myelinmap', 'distortion', 'morph']
    allowed_file_formats = ImagingProcess.allowed_file_formats + ['.surf.gii', '.shape.gii', 'dscalar.nii', '.tsv']
    readable_file_formats = allowed_file_formats + ['.dcm']
    modality = 'anat'

    def check_files_conformity(self):
        if self['modality'] == 'morph':
            if not self['fileLoc'].endswith('.tsv'):
                raise FileNotFoundError('The morphometrics derivatives should be tsv file.')
            else:
                self['Morphometrics'] = Morphometrics()
                self['Morphometrics'].read_file(self['fileLoc'])


class AnatProcessJSON(ImagingProcessJSON):
    pass


class Morphometrics(ProcessTSV):
    header = ['index', 'name', 'centroid', 'volume', 'intensity', 'thickness', 'area', 'curv']


""" Func brick with its file-specific sidecar files. """


class Func(Imaging):

    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'rec', 'run', 'echo', 'modality', 'fileLoc', 'FuncJSON',
                                   'FuncEventsTSV']
    required_keys = Imaging.required_keys + ['task', 'modality']
    allowed_modalities = ['bold', 'sbref']
    allowed_file_formats = ['.nii']
    readable_file_formats = allowed_file_formats + ['.dcm']
    required_protocol_keys = []

    def __init__(self):
        super().__init__()


class FuncJSON(ImagingJSON):
    keylist = ImagingJSON.keylist + ['VolumeTiming', 'TaskName',
                                     'NumberOfVolumesDiscardedByScanner', 'NumberOfVolumesDiscardedByUser',
                                     'DelayTime', 'AcquisitionDuration', 'DelayAfterTrigger',
                                     'Instructions', 'TaskDescription', 'CogAtlasID', 'CogPOID']
    required_keys = ['RepetitionTime', 'VolumeTiming', 'TaskName']


class FuncEventsTSV(EventsTSV):
    """Store the info of the #_events.tsv."""
    pass


class FuncProcess(ImagingProcess):
    keylist = BidsBrick.keylist + ['ses', 'acq', 'rec', 'run', 'echo', 'proc', 'desc', 'hemi', 'space', 'atlas', 'modality', 'fileLoc', 'FuncProcessJSON']
    allowed_modalities = ImagingProcess.allowed_modalities + ['mean', 'std', 'tsnr', 'sfs', 'alff', 'falff', 'reho',
                                                              'dcb', 'dcw', 'ecb', 'ecw', 'lfcdb', 'lfcdw', 'vmhc', 'timeseries']
    allowed_file_formats = ImagingProcess.allowed_file_formats + ['.tsv']
    modality = 'func'

    def check_files_conformity(self):
        if self['modality'] in ['timeseries', 'motion', 'outliers']:
            if not self['fileLoc'].endswith('.tsv'):
                raise FileNotFoundError('The derivatives functional file should be tsv file.')
            else:
                self['FuncProcessTSV'] = FuncProcessTSV()
                self['FuncProcessTSV'].read_file(self['fileLoc'])


class FuncProcessJSON(ImagingProcessJSON):
    keylist = ImagingProcessJSON.keylist + ['BandpassFilter', 'Neighborhood', 'Threshold', 'Method', 'SamplingFrequency', 'StartTime']
    required_keys = ['SamplingFrequency']


class FuncProcessTSV(ProcessTSV):
    pass


""" Fmap brick with its file-specific sidecar files. """


class Fmap(Imaging):

    keylist = BidsBrick.keylist + ['ses', 'acq', 'dir', 'run', 'modality', 'fileLoc', 'FmapJSON']
    required_keys = Imaging.required_keys + ['modality']
    allowed_modalities = ['phasediff', 'phase1', 'phase2', 'magnitude1', 'magnitude2', 'magnitude', 'fieldmap', 'epi']
    allowed_file_formats = ['.nii']
    readable_file_formats = allowed_file_formats + ['.dcm']
    required_protocol_keys = []

    def __init__(self):
        super().__init__()


class FmapJSON(ImagingJSON):

    required_keys = ['PhaseEncodingDirection', 'EffectiveEchoSpacing', 'TotalReadoutTime', 'EchoTime']


class FmapProcess(ImagingProcess):
    keylist = ImagingProcess.keylist + ['FmapProcessJSON']


class FmapProcessJSON(ImagingProcessJSON):
    pass


""" Fmap brick with its file-specific sidecar files. """


class Dwi(Imaging):

    keylist = BidsBrick.keylist + ['ses', 'acq', 'dir', 'run', 'modality', 'fileLoc', 'DwiJSON', 'Bval', "Bvec"]
    required_keys = Imaging.required_keys + ['modality']
    allowed_modalities = ['dwi']
    allowed_file_formats = ['.nii']
    readable_file_formats = allowed_file_formats + ['.dcm']
    required_protocol_keys = []

    def __init__(self):
        super().__init__()
        self['modality'] = 'dwi'


class DwiJSON(ImagingJSON):
    pass


class DwiProcess(ImagingProcess):
    keylist =BidsBrick.keylist + ['ses', 'acq', 'dir', 'run', 'proc', 'desc', 'hemi', 'space', 'model', 'subset', 'parameter', 'modality', 'fileLoc', 'DwiProcessJSON']
    required_keys = Imaging.required_keys + ['modality']
    allowed_file_formats = ['.nii']
    readable_file_formats = allowed_file_formats + ['.dcm']
    allowed_modalities = ['dwi', 'diffmodel', 'tractography', 'FA', 'MD', 'AD', 'RD', 'MODE', 'LINEARITY', 'PLANARITY', 'SPHERICITY', 'MK', 'RK', 'AK', 'GFA', 'FSUM', 'Fi', 'D', 'DSTD', 'RTPP', 'RTAP']
    modality = 'dwi'
    allowed_model = ['DTI', 'DKI', 'WMTI', 'CSD', 'NODDI', 'DSI', 'CSA', 'SHORE', 'MAPMRI', 'FORECAST', 'fwDTI', 'BedpostX']


class DwiProcessJSON(ImagingProcessJSON):
    keylist = ImagingProcessJSON.keylist + ['Shells', 'Gradients', 'ModelDescription', 'ModelURL', 'Parameters']


class Bval(BidsFreeFile):
    extension = '.bval'


class Bvec(BidsFreeFile):
    extension = '.bvec'


""" MEG brick with its file-specific sidecar files (To be finalized). """


class Meg(Electrophy):

    keylist = BidsBrick.keylist + ['ses', 'task', 'acq', 'run', 'proc', 'modality', 'fileLoc', 'MegJSON',
                                   'MegChannelsTSV', 'MegEventsTSV', 'MegHeadShape', 'MegCoordSysJSON']
    # keybln = BidsBrick.create_keytype(keylist)
    required_keys = Imaging.required_keys + ['task', 'modality']
    allowed_modalities = ['meg']
    allowed_file_formats = [''] #'.ctf', '.ds', '.fif', '.kdf', '.raw', '.mhd', '.sqd', '.con', '.ave', '.mrk',
    readable_file_formats = allowed_file_formats
    channel_type = ['MEGMAG', 'MEGGRADAXIAL', 'MEGGRADPLANAR', 'MEGREFMAG', 'MEGREFGRADAXIAL', 'MEGREFGRADPLANAR',
                    'MEGOTHER', 'ECOG', 'SEEG', 'DBS', 'PD', 'ADC', 'DAC', 'HLU', 'FITERR', 'OTHER'] + Electrophy.channel_type
    mod_channel_type = ['MEGMAG', 'MEGGRADAXIAL', 'MEGGRADPLANAR', 'MEGREFMAG', 'MEGREFGRADAXIAL', 'MEGREFGRADPLANAR', 'MEGOTHER']
    required_protocol_keys = []

    def __init__(self):
        super().__init__()
        self['modality'] = 'meg'


class MegJSON(ElectrophyJSON):
    keylist = ['TaskName', 'InstitutionName', 'InstitutionAddress', 'Manufacturer', 'ManufacturersModelName', 'SoftwareVersions',
               'TaskDescription', 'Instructions', 'CogAtlasID', 'CogPOID',  'DeviceSerialNumber', 'PowerLineFrequency',
               'DewarPosition', 'DigitizedLandmarks', 'DigitizedHeadPoints', 'SamplingFrequency', 'SoftwareFilters',
               'MEGChannelCount', 'MEGREFChannelCount', 'EEGChannelCount', 'ECOGChannelCount', 'SEEGChannelCount',
               'EOGChannelCount', 'ECGChannelCount', 'EMGChannelCount', 'MiscChannelCount', 'TriggerChannelCount', 'RecordingDuration',
               'RecordingType', 'EpochLength', 'ContinuousHeadLocalization', 'HeadCoilFrequency', 'MaxMovement', 'SubjectArtefactDescription',
               'AssociatedEmptyRoom', 'HardwareFilters', 'EEGPlacementScheme', 'ManufacturersAmplifierModelName', 'CapManufacturer',
               'CapManufacturersModelName', 'EEGReference']
    required_keys = ['TaskName', 'PowerLineFrequency', 'SoftwareFilters', 'SamplingFrequency', 'DewarPosition', 'DigitizedLandmarks', 'DigitizedHeadPoints']


class MegChannelsTSV(ChannelsTSV):
    header = ['name', 'type', 'units', 'description', 'sampling_frequency', 'low_cutoff', 'high_cutoff', 'notch', 'software_filters',
               'status', 'status_description']
    required_fields = ['name', 'type', 'units']
    modality_field = 'channels'


class MegCoordSysJSON(BidsJSON):
    keylist = ['MEGCoordinateSystem', 'MEGCoordinateUnits', 'MEGCoordinateSystemDescription', 'IntendedFor',
               'EEGCoordinateSystem', 'EEGCoordinateUnits', 'EEGCoordinateSystemDescription',
               'HeadCoilCoordinates', 'HeadCoilCoordinateSystem', 'HeadCoilCoordinatesUnits', 'HeadCoilCoordinateSystemDescription',
               'DigitizedHeadPoints', 'DigitizedHeadPointsCoordinateSystem', 'DigitizedHeadPointsCoordinateUnits',
               'DigitizedHeadPointsCoordinateSystemDescription', 'IntendedFor', 'AnatomicalLandmarkCoordinates',
               'AnatomicalLandmarkCoordinateSystem', 'AnatomicalLandmarkCoordinateUnits', 'AnatomicalLandmarkCoordinateSystemDescription', 'FiducialsDescription']
    required_keys = ['MEGCoordinateSystem', 'MEGCoordinateUnits']
    modality_field = 'coordsystem'


class MegEventsTSV(EventsTSV):
    """Store the info of the #_events.tsv."""
    pass


class MegHeadShape(BidsFreeFile):
    extension = '.pos'
    modality_field = 'headshape'

    def clear_head(self):
        if self and isinstance(self[0], bytes):
            self.clear()

# class MegGlobalSidecars(GlobalSidecars):
#     pass
    # complementary_keylist = ['MegCoordSysJSON', 'MegPhoto']
    # required_keys = BidsBrick.required_keys
    # allowed_file_formats = ['.tsv', '.json'] + IeegPhoto.allowed_file_formats
    # allowed_modalities = [eval(elmt).modality_field for elmt in complementary_keylist]
    # required_protocol_keys = []

""" Behaviour brick with its file-specific sidecar files (To be finalized). """


class Beh(ModalityType):

    keylist = BidsBrick.keylist + ['ses', 'task', 'modality', 'fileLoc', 'BehEventsTSV']
    required_keys = ModalityType.required_keys + ['task', 'modality']
    allowed_modalities = ['beh', 'physio', 'stim']
    allowed_file_formats = ['.tsv']
    readable_file_formats = allowed_file_formats

    def __init__(self):
        super().__init__()
        self['modality'] = 'beh'


class BehEventsTSV(EventsTSV):
    """Store the info of the #_events.tsv."""
    pass


class BehProcess(Process):
    pass


""" Scans bricks which store information about the acquisition time of the files """


class Scans(BidsBrick):
    keylist = BidsBrick.keylist + ['ses', 'modality', 'fileLoc', 'ScansTSV']
    modality = 'scans'

    def __init__(self):
        super().__init__()
        self['modality'] = self.modality
        self['ScansTSV'] = ScansTSV()

    def add_modality(self, mod_dict, bids_dir):
        if not isinstance(mod_dict, ModalityType):
            return
        mod_type = mod_dict.classname()
        if isinstance(mod_dict, Process):
            mod_type = mod_type.replace(Process.__name__, '')
        scan_name = os.path.join(mod_type.lower(), os.path.basename(mod_dict['fileLoc']))
        if not self['ScansTSV']:
            self['ScansTSV'] = ScansTSV()
        self['sub'] = mod_dict['sub']
        self['ses'] = mod_dict['ses']
        scan_time = '1900-01-01T00:00:00'
        if mod_dict[mod_dict.classname()+'JSON']:  # check if object has a JSON
            mod_json = mod_dict[mod_dict.classname()+'JSON']
            # check if JSON has recording time information otherwise mark default one
            if 'RecordingISODate' in mod_json.keys() and mod_json['RecordingISODate']:
                scan_time = mod_json['RecordingISODate']
            elif 'AcquisitionTime' in mod_json.keys() and mod_json['AcquisitionTime']:
                scan_time = '1900-01-01T' + mod_json['AcquisitionTime']
            elif 'AcquisitionDateTime' in mod_json.keys() and mod_json['AcquisitionDateTime']:
                try:
                    scan_time = str(datetime.strptime(mod_json['AcquisitionDateTime'], '%Y%m%d%H%M%S.%f'))
                except:
                    scan_time = '1900-01-01T00:00:00'
                del mod_json['AcquisitionDateTime']
            elif 'AcquisitionDate' in mod_json.keys() and mod_json['AcquisitionDate'] and mod_json['AcquisitionDate'] != 'n/a':
                try:
                    scan_time = mod_json['AcquisitionDate'].replace(' ', 'T')

                except:
                    scan_time = '1900-01-01T00:00:00'
                del mod_json['AcquisitionDate']
        self['ScansTSV'].append({'filename': scan_name, 'acq_time': scan_time})

    def write_file(self):
        fname, dname, ext = self.create_filename_from_attributes()
        file_ses = fname + ext
        dirname_ses = os.path.join(BidsDataset.dirname, dname)
        self['ScansTSV'].write_file(os.path.join(dirname_ses, file_ses))
        self['fileLoc'] = os.path.join(dname, file_ses)

    def compare_scanstsv(self, tmp_scn):
        is_same = False
        ls = [x[0] for x in self['ScansTSV']]
        ltemp = [y[0] for y in tmp_scn]
        index_list = [[ls.index(elt), ltemp.index(elt)] for elt in ls if elt in ltemp]
        for i in index_list:
            if not tmp_scn[i[1]][1] == 'acq_time':
                self['ScansTSV'][i[0]][1] = tmp_scn[i[1]][1]
                is_same = True
        return is_same


class ScansTSV(BidsTSV):
    header = ['filename', 'acq_time']
    required_fields = ['filename']
    modality_field = 'scans.tsv'


''' Higher level bricks '''


class Subject(BidsBrick):

    keylist = BidsBrick.keylist + ['Anat', 'Func', 'Fmap', 'Dwi', 'Meg', 'Eeg', 'Ieeg',
                                   'Beh', 'IeegGlobalSidecars', 'EegGlobalSidecars', 'Scans']
    required_keys = BidsBrick.required_keys

    def __setitem__(self, key, value):
        if value and key in ModalityType.get_list_subclasses_names() + GlobalSidecars.get_list_subclasses_names():
            if value['sub'] and self['sub'] and not value['sub'] == self['sub']:
                err_str = value['fileLoc'] + ' cannot be added to ' + self['sub'] + ' since sub: ' + value['sub']
                self.write_log(err_str)
                raise KeyError(err_str)
        super().__setitem__(key, value)
        # if Subject 'sub' attribute changes than it changes all 'sub' of its Modality and globalsidecar objects
        if key == 'sub' and value:
            for subkey in self:
                if subkey in ModalityType.get_list_subclasses_names() + GlobalSidecars.get_list_subclasses_names():
                    if self[subkey]:
                        for modalityy in self[subkey]:
                            modalityy['sub'] = self['sub']

    def get_attr_tsv(self, parttsv):
        if isinstance(parttsv, ParticipantsTSV):
            bln, sub_dict, sub_idx = parttsv.is_subject_present(self['sub'])
            if bln:
                sub_dict = {key: sub_dict[key] for key in parttsv.header if key in self.keylist}
                self.copy_values(sub_dict)

    def is_empty(self):
        for key in self:
            if key in ModalityType.get_list_subclasses_names() + GlobalSidecars.get_list_subclasses_names() \
                    and self[key]:
                return False
        return True

    def check_file_in_scans(self, filename, mod_dir):
        def scan_in_file(scan_tsv, filescan):
            line = [scan[0] for scan in scan_tsv[1:]]
            if filescan not in line:
                scan_tsv.append({'filename': filescan, 'acq_time': '1900-01-01T00:00:00'})

        # check if current file is already inside scans.tsv otherwise add it (to be improved)
        scan_dir = os.path.dirname(self[mod_dir][-1]['fileLoc'])
        if mod_dir.endswith('Process'):
            mod_dir = mod_dir.split('Process')[0]
        scan_dir = os.path.split(scan_dir)[0]
        scan_present = False
        ses_present = False
        ses_label = ''
        sub_label = ''
        name_pieces = filename.split('_')
        for word in name_pieces:
            w = word.split('-')
            if len(w) == 2 and w[0] == 'ses':
                ses_label = w[1]
            elif len(w) == 2 and w[0] == 'sub':
                sub_label = w[1]

        scanfile = 'sub-' + sub_label
        if ses_label != '':
            scanfile += '_ses-' + ses_label
        scanfile = os.path.join(scan_dir, scanfile + '_scans.tsv')

        filename = os.path.join(mod_dir.lower(), filename)

        for elt in self['Scans']:
            if elt['ses'] == ses_label:
                ses_present = True
                idx = self['Scans'].index(elt)
                scan_in_file(self['Scans'][idx]['ScansTSV'], filename)
                break

        if not ses_present:
            self['Scans'] = getattr(modules[__name__], 'Scans')()
            self['Scans'][-1]['sub'] = sub_label
            self['Scans'][-1]['ses'] = ses_label
            self['Scans'][-1]['ScansTSV'] = getattr(modules[__name__], 'ScansTSV')()
            if os.path.exists(os.path.join(BidsDataset.dirname, scanfile)):
                self['Scans'][-1]['ScansTSV'].read_file(os.path.join(BidsDataset.dirname, scanfile))
                scan_in_file(self['Scans'][-1]['ScansTSV'], filename)
            else:
                self['Scans'][-1]['ScansTSV'].append({'filename': filename,
                                                  'acq_time': '1900-01-01T00:00:00'})
                self['Scans'][-1]['ScansTSV'].write_file(os.path.join(BidsDataset.dirname, scanfile))
            self['Scans'][-1]['fileLoc'] = scanfile

        # for elt in self['Scans']:
        #     if not elt['fileLoc']:
        #         scanfile =''
        #         for key in elt:
        #             if key in ['sub', 'ses'] and (elt[key] and elt[key] != ''):
        #                 scanfile += key + '-' + elt[key] + '_'
        #         scanfile = os.path.join(scan_dir, scanfile + 'scans.tsv')
        #         if not os.path.exists(os.path.join(BidsDataset.dirname, scanfile)):
        #             elt['ScansTSV'].write_file(os.path.join(BidsDataset.dirname, scanfile))
        #         elt['fileLoc'] = scanfile


class SubjectProcess(Subject):
    keylist = BidsBrick.keylist + ['AnatProcess', 'FuncProcess', 'FmapProcess', 'DwiProcess', 'MegProcess', 'EegProcess', 'IeegProcess',
                                   'BehProcess', 'Scans']
    required_keys = BidsBrick.required_keys

    # def __setitem__(self, key, value):
    #     if key in self.keylist:
    #         if value and isinstance(value, Process):
    #             # check whether the value is from the correct class when not empty
    #             self[key].append(value)
    #         else:
    #             dict.__setitem__(self, key, [])
    #     else:
    #         super().__setitem__(key, value)


        # for modproc in keyprocess:
        #     newclass = type(modproc, (superclasse,), {})  # To add a base key.capitalize()
        #     newclass.__module__ = superclasse.__module__
        #     setattr(modules[__name__], newclass.__name__, newclass)


class Derivatives(BidsBrick):

    keylist = ['Pipeline']


class Code(BidsBrick):
    pass


class Stimuli(BidsBrick):
    pass


''' Dataset related JSON bricks '''


class DatasetDescJSON(BidsJSON):

    keylist = ['Name', 'BIDSVersion', 'License', 'Authors', 'Acknowledgements', 'HowToAcknowledge', 'Funding',
               'ReferencesAndLinks', 'DatasetDOI']
    required_keys = ['Name', 'BIDSVersion']
    filename = 'dataset_description.json'
    bids_version = '1.2.0'

    def __init__(self):
        super().__init__()
        self['BIDSVersion'] = self.bids_version

    def __setitem__(self, key, value):
        if key == 'Authors':
            value = self.check_authors_value(value)
        super().__setitem__(key, value)

    def write_file(self, jsonfilename=None):
        if not jsonfilename:
            jsonfilename = os.path.join(BidsDataset.dirname, DatasetDescJSON.filename)
        super().write_file(jsonfilename)

    def read_file(self, jsonfilename=None):
        if not jsonfilename:
            jsonfilename = os.path.join(BidsDataset.dirname, DatasetDescJSON.filename)
        if isinstance(self, BidsJSON):
            if os.path.splitext(jsonfilename)[1] == '.json':
                if not os.path.exists(jsonfilename):
                    print('dataset_description.json does not exists.')
                    return
                with open(jsonfilename, 'r') as file:
                    read_json = json.load(file)
                    for key in read_json:
                        if key == 'Authors' and isinstance(self[key], list) and \
                                self[key] == [BidsSidecar.bids_default_unknown]:
                            self[key] = read_json[key]
                        elif (key in self.keylist and self[key] == BidsSidecar.bids_default_unknown) or \
                                key not in self.keylist:
                            self[key] = read_json[key]
            else:
                raise TypeError('File is not ".json".')

    def copy_values(self, sidecar_elmt, simplify_flag=False):
        super().copy_values(sidecar_elmt, simplify_flag=simplify_flag)
        if 'Authors' in self.keys():
            self['Authors'] = self.check_authors_value(self['Authors'])

    @staticmethod
    def check_authors_value(value):
        if value.__class__.__name__ in ['str', 'unicode']:
            value = value.split(', ')
        elif isinstance(value, list):
            pass
        else:
            err_str = 'Authors key in dataset_description.json only allows string of comma separated authors,' \
                      ' ex: "John Doe, Jane Doe"'
            raise TypeError(err_str)
        return value


''' TSV bricks '''


class SrcDataTrack(BidsTSV):
    header = ['orig_filename', 'bids_filename', 'upload_date']
    required_fields = ['orig_filename', 'bids_filename', 'upload_date']
    filename = 'source_data_trace.tsv'

    def write_file(self, tsv_full_filename=None):
        if not os.path.exists(os.path.join(BidsDataset.dirname, 'sourcedata')):
            os.makedirs(os.path.join(BidsDataset.dirname, 'sourcedata'))
        tsv_full_filename = os.path.join(BidsDataset.dirname, 'sourcedata', SrcDataTrack.filename)
        super().write_file(tsv_full_filename)

    def read_file(self, tsv_full_filename=None):
        tsv_full_filename = os.path.join(BidsDataset.dirname, 'sourcedata', SrcDataTrack.filename)
        super().read_file(tsv_full_filename)

    def get_source_from_raw_filename(self, filename):
        filename, ext = os.path.splitext(os.path.basename(filename).replace('.gz', ''))

        bids_fname_idx = self.header.index('bids_filename')
        orig_fname_idx = self.header.index('orig_filename')
        orig_fname = None
        idx = None
        for line in self[1:]:
            if filename in line[bids_fname_idx]:
                orig_fname = line[orig_fname_idx]
                idx = self.index(line)
                break
        # orig_fname = [line[orig_fname_idx] for line in self[1:] if filename in line[bids_fname_idx]]
        # if orig_fname:
        #     orig_fname = orig_fname[0]

        return orig_fname, filename, idx


class ParticipantsTSV(BidsTSV):
    header = ['participant_id']
    required_fields = ['participant_id']
    filename = 'participants.tsv'

    def write_file(self, tsv_full_filename=None):
        if not tsv_full_filename:
            tsv_full_filename = os.path.join(BidsDataset.dirname, ParticipantsTSV.filename)

        super().write_file(tsv_full_filename)

    def read_file(self, tsv_full_filename=None):
        if not tsv_full_filename:
            tsv_full_filename = os.path.join(BidsDataset.dirname, ParticipantsTSV.filename)
        if not os.path.isfile(tsv_full_filename):
            return
        if os.path.splitext(tsv_full_filename)[1] == '.tsv':
            with open(os.path.join(tsv_full_filename), 'r') as file:
                tsv_header_line = file.readline()
                tsv_header = tsv_header_line.strip().split("\t")
                if len([word for word in tsv_header if word in self.required_fields]) < \
                        len(self.required_fields):
                    issue_str = 'Header of ' + os.path.basename(tsv_full_filename) + \
                                ' does not contain the required fields.'
                    print(issue_str)
                # to get into account the header that need to be add at the end of the participantsTSV
                temp_header = [elt for elt in tsv_header if elt not in self.required_fields]
                self.header = [self.required_fields[0]] + temp_header + self.required_fields[1:]
                self[:] = []  # not sure if useful
                for line in file:
                    self.append({tsv_header[cnt]: val for cnt, val in enumerate(line.strip().split("\t"))})
        else:
            raise TypeError('File is not ".tsv".')
        self.update_ids()

    def is_subject_present(self, sub_id):
        participant_idx = self.header.index('participant_id')
        sub_line = [line for line in self[1:] if sub_id in line[participant_idx]]
        sub_idx = None
        sub_info = {}
        if sub_line:
            sub_idx = self.index(sub_line[0])
            sub_info = {self.header[cnt]: val for cnt, val in enumerate(sub_line[0])}
            sub_info['sub'] = sub_info['participant_id'].replace('sub-', '')
            del(sub_info['participant_id'])

        return bool(sub_info), sub_info, sub_idx

    def add_subject(self, sub_dict):
        if isinstance(sub_dict, Subject):
            if not self.is_subject_present(sub_dict['sub'])[0]:
                tmp_dict = sub_dict.get_attributes()
                if 'sub-' not in tmp_dict['sub']:
                    tmp_dict['participant_id'] = 'sub-' + tmp_dict['sub']
                tmp_dict['upload_date'] = BidsBrick.access_time.strftime("%Y-%m-%dT%H:%M:%S")
                if 'alias' in self.header and 'alias' in tmp_dict:
                    tmp_dict['alias'] = self.createalias(sub_dict['sub'])
                self.append(tmp_dict)

    def update_subject(self, sub_name, update_dict):
        for cnt, elt in enumerate(self):
            if sub_name in elt[0]:
                idx_sub = cnt
        for key, value in update_dict.items():
            idx = self.header.index(key)
            self[idx_sub][idx] = value

    def update_ids(self):
        #Check if participants_id is written with <sub-id>
        idx = self.header.index('participant_id')
        if len(self) > 1:
            for line in self[1:]:
                if 'sub-' not in line[idx]:
                    line[idx] = 'sub-' + line[idx]

class ParticipantsProcessTSV(ParticipantsTSV):
    header = ['participant_id']
    required_fields = ['participant_id']
    filename = 'participants.tsv'

    def simplify_participants(self):
        if len(self[0]) > 1:
            tmp_tsv = self[:]
            idx = self[0].index(self.required_fields[0])
            self.header = self.required_fields
            self[:] = []
            for line in tmp_tsv[1:]:
                val = line[idx]
                if 'sub-' not in val:
                    val = 'sub-' + val
                self.append({self.required_fields[0]: val})

    def read_file(self, tsv_full_filename=None):
        super().read_file(tsv_full_filename=tsv_full_filename)
        self.simplify_participants()


class MetaBrick(BidsBrick):
    curr_subject = {}
    curr_pipeline = {}
    dirname = None

    def is_subject_present(self, subject_label, flagProcess=False):
        """
        Method that look if a given subject is in the current dataset. It returns a tuple composed
        of a boolean, an integer. The boolean is True if the sub is present, the integer gives its indices in the
        subject list of the dataset.
        Ex: bids.is_subject_present('05') ->
        self.curr_subject = {'Subject': Suject(), 'isPresent': boolean, 'index': integer}
        """
        if flagProcess:
            self.curr_subject = {'SubjectProcess': SubjectProcess(), 'isPresent': False, 'index': None}
            sub_list = [sub['sub'] for sub in self['SubjectProcess']]
            if subject_label in sub_list:
                index = sub_list.index(subject_label)
                self.curr_subject['SubjectProcess'] = self['SubjectProcess'][index]
                self.curr_subject.update({'isPresent': True, 'index': index})
        else:
            self.curr_subject = {'Subject': Subject(), 'isPresent': False, 'index': None}
            sub_list = self.get_subject_list()
            if subject_label in sub_list:
                index = sub_list.index(subject_label)
                self.curr_subject['Subject'] = self['Subject'][index]
                self.curr_subject.update({'isPresent': True, 'index': index})

    def is_pipeline_present(self, pipeline_label):
        flag_pipeline = False
        if isinstance(self, Pipeline):
            flag_pipeline = True
        if not flag_pipeline:
            self.curr_pipeline = {'Pipeline': Pipeline(), 'isPresent': False, 'index': None}
            pip_list = self.get_derpip_list()
            # pipeline_subject = pipeline['SubjectProcess']
            if pipeline_label in pip_list:
                indexPip = pip_list.index(pipeline_label)
                self.curr_pipeline['Pipeline'] = self['Derivatives'][-1]['Pipeline'][indexPip]
                self.curr_pipeline.update({'isPresent': True, 'index': indexPip})

    def get_derpip_list(self):
        # generates error if self is instance of Pipeline or SourceData as no Derivatives
        der_list = list()
        pip_list = list()
        for der in self['Derivatives']:
            der_list.append(der['Pipeline'])
            for pip in der['Pipeline']:
                pip_list.append(pip['name'])
        return pip_list

    def get_subject_list(self):
        return [sub['sub'] for sub in self['Subject']]

    def get_object_from_filename(self, filename, sub_id=None):
        if filename.__class__.__name__ in ['str', 'unicode']:  # py2/py3 compatible...
            sub_list = self.get_subject_list()
            if isinstance(self, BidsDataset):
                fname = os.path.splitext(os.path.basename(filename))[0]
                fname_pieces = fname.split('_')
                if 'sub-' in fname_pieces[0]:
                    sub_id = fname_pieces[0].split('-')[1]
                else:
                    error_str = 'Filename ' + filename + ' does not follow bids architecture.'
                    self.write_log(error_str)
                    return
                subclass = [subcls for subcls in Electrophy.__subclasses__() + Imaging.__subclasses__() +
                            GlobalSidecars.__subclasses__() if fname_pieces[-1] in subcls.allowed_modalities]
            else:
                if sub_id in sub_list:
                    sub_list = [sub_id]
                subclass = Electrophy.__subclasses__() + Imaging.__subclasses__() + GlobalSidecars.__subclasses__()
            # if fname_pieces[-1] in [for subclss in ModalityType.get_list_subclasses_names()]
            for s_id in sub_list:
                self.is_subject_present(s_id)
                if self.curr_subject['Subject'] and subclass:
                    for subclss in subclass:
                        for mod_elmt in self.curr_subject['Subject'][subclss.__name__]:
                            if os.path.basename(mod_elmt['fileLoc']) == os.path.basename(filename):
                                return mod_elmt
            pip_list = self.get_derpip_list()
            subclass = ImagingProcess.__subclasses__() + ElectrophyProcess.__subclasses__()
            for pip in pip_list:
                self.is_pipeline_present(pip)
                if self.curr_pipeline['isPresent']:
                    sub_list = [sub['sub'] for sub in self.curr_pipeline['Pipeline']['SubjectProcess']]
                    for s_id in sub_list:
                        self.curr_pipeline['Pipeline'].is_subject_present(s_id, flagProcess=True)
                        if self.curr_pipeline['Pipeline'].curr_subject['isPresent'] and subclass:
                            for subclss in subclass:
                                for mod_elmt in self.curr_pipeline['Pipeline'].curr_subject['SubjectProcess'][subclss.__name__]:
                                    if os.path.basename(mod_elmt['fileLoc']) == os.path.basename(filename):
                                        return mod_elmt
            error_str = 'Subject ' + str(sub_id) + ' filename ' + str(filename) + ' is not found in '\
                        + self.dirname + '.'
        else:
            error_str = 'Filename ' + str(filename) + ' should be a string.'
        self.write_log(error_str)
        return

    def get_requirements(self, reqfiloc=None):

        if isinstance(self, BidsDataset) and BidsDataset.dirname and \
                os.path.exists(os.path.join(BidsDataset.dirname, 'code', 'requirements.json')):
            full_filename = os.path.join(BidsDataset.dirname, 'code', 'requirements.json')
        elif reqfiloc and os.path.exists(reqfiloc):
            full_filename = reqfiloc
        else:
            full_filename = None

        if isinstance(self, BidsDataset):
            self.requirements = Requirements(full_filename)
            BidsDataset.requirements = self.requirements
            if 'Requirements' not in self.requirements.keys() or not self.requirements['Requirements']:
                self.write_log('/!\\ WARNING /!\\ No requirements set! Default requirements from BIDS ' +
                               DatasetDescJSON.bids_version + ' applied')

            if self.requirements and self.requirements['Requirements'] and \
                    'Subject' in self.requirements['Requirements'].keys():

                for key in self.requirements['Requirements']['Subject']:

                    if key == 'keys':
                        ParticipantsTSV.header += [elmt for elmt in self.requirements['Requirements']['Subject']['keys']
                                                   if elmt not in ParticipantsTSV.header]
                        ParticipantsTSV.required_fields += [elmt for elmt in
                                                            self.requirements['Requirements']['Subject']['keys'] if
                                                            elmt not in ParticipantsTSV.required_fields]
                        Subject.keylist += [elmt for elmt in self.requirements['Requirements']['Subject']['keys']
                                            if elmt not in Subject.keylist]
                    elif key == 'required_keys':
                        Subject.required_keys += [elmt for elmt in
                                                  self.requirements['Requirements']['Subject']['required_keys']
                                                  if elmt not in Subject.required_keys]
                    elif key in BidsBrick.get_list_subclasses_names() and key + self.requirements.keywords[0] \
                            not in ParticipantsTSV.header:
                        ParticipantsTSV.header.append(key + self.requirements.keywords[0])
                        ParticipantsTSV.required_fields.append(key + self.requirements.keywords[0])
                        #To modify when we will know how to check the integrity of Eeg and Meg
                        if key in ['Ieeg', 'Eeg'] and key + self.requirements.keywords[1] \
                                not in ParticipantsTSV.header: #in Electrophy.get_list_subclasses_names()
                            ParticipantsTSV.header.append(key + self.requirements.keywords[1])
                            ParticipantsTSV.required_fields.append(key + self.requirements.keywords[1])
                    elif key in ModalityType.get_list_subclasses_names() + GlobalSidecars.get_list_subclasses_names():
                        protocol_keys = []
                        for elt in self.requirements['Requirements']['Subject'][key]:
                            if isinstance(elt['type'], dict):
                                protocol_keys.extend(list(elt['type'].keys()))
                            elif isinstance(elt['type'], list):
                                temp_keys = [ty for clef in elt['type'] for ty in clef]
                                protocol_keys.extend(temp_keys)
                        protocol_keys = list(set(protocol_keys))
                        for prot in protocol_keys:
                            if prot not in eval(key+'.required_protocol_keys'):
                                eval(key+'.required_protocol_keys.append(prot)')

            if 'Subject' + self.requirements.keywords[0] not in ParticipantsTSV.header:
                ParticipantsTSV.header.append('Subject' + self.requirements.keywords[0])
                ParticipantsTSV.required_fields.append('Subject' + self.requirements.keywords[0])
        elif isinstance(self, Data2Import):
            self.requirements = Requirements(full_filename)
            if 'Requirements' in self.requirements.keys() and 'Subject' in self.requirements['Requirements'].keys():
                for key in self.requirements['Requirements']['Subject']:
                    if key == 'keys':
                        Subject.keylist += [elmt for elmt in self.requirements['Requirements']['Subject'][key]
                                            if elmt not in Subject.keylist]
                    elif key == 'required_keys':
                        Subject.required_keys += [elmt for elmt in
                                                  self.requirements['Requirements']['Subject']['required_keys']
                                                  if elmt not in Subject.required_keys]


''' BIDS brick which contains all the information about the data to be imported '''


class Data2Import(MetaBrick):
    #Add Derivatives in keylist
    keylist = ['Subject', 'Derivatives', 'DatasetDescJSON', 'UploadDate']
    filename = 'data2import.json'
    requirements = None
    curr_log = ''

    def __init__(self, data2import_dir=None, requirements_fileloc=None):
        """initiate a  dict var for Subject info"""
        self.__class__.clear_log()
        super().__init__()
        self.dirname = data2import_dir
        self.get_requirements(requirements_fileloc)
        if data2import_dir is None:
            return
        if os.path.isdir(data2import_dir):
            self._assign_import_dir(data2import_dir)
            # self.requirements = None
            if os.path.isfile(os.path.join(self.dirname, Data2Import.filename)):
                with open(os.path.join(self.dirname, Data2Import.filename)) as file:
                    inter_dict = json.load(file)
                    self.copy_values(inter_dict)
                    # self.write_log('Importation procedure ready!')
            else:
                self['UploadDate'] = datetime.now().strftime(self.time_format)
        else:
            str_error = data2import_dir + ' is not a directory.'
            self.write_log(str_error)
            raise NotADirectoryError(str_error)

    def save_as_json(self, savedir=None, file_start=None, write_date=False, compress=False):
        if savedir is None:
            savedir = self.dirname
        super().save_as_json(savedir=savedir, file_start=None, write_date=write_date, compress=False)

    @classmethod
    def _assign_import_dir(cls, data2import_dir):
        cls.dirname = data2import_dir
        BidsBrick.cwdir = data2import_dir


class SourceData(MetaBrick):
    keylist = ['Subject', 'SrcDataTrack']
    dirname = 'sourcedata'

    def is_pipeline_present(self, pipeline_label):
        print(self.classname() + ' does not have pipelines!')


''' Main BIDS brick which contains all the information concerning the patients and the sidecars. It permits to parse a 
given bids dataset, request information (e.g. is a given subject is present, has a given subject a given modality), 
import new data or export a subset of the current dataset (not yet implemented ) '''


class BidsDataset(MetaBrick):

    keylist = ['Subject', 'SourceData', 'Derivatives', 'Code', 'Stimuli', 'DatasetDescJSON', 'ParticipantsTSV']
    requirements = dict()
    curr_log = ''
    readers = dict()
    converters = {'Imaging': {'ext': ['.nii'], 'path': ''}, 'Electrophy': {'ext': ['.vhdr'], 'path': ''}}
    parsing_path = os.path.join('derivatives', 'parsing')
    log_path = os.path.join('derivatives', 'log')
    update_text = None

    def __init__(self, bids_dir, update_text=None):
        """initiate a  dict var for patient info"""
        self.__class__.clear_log()
        if update_text:
            self.__class__.update_text = update_text
        super().__init__()
        self.dirname = bids_dir
        self._assign_bids_dir(bids_dir)
        self.curr_subject = {}
        self.issues = Issue()
        self.access = Access()
        self.access['user'] = self.curr_user
        self.access['access_time'] = self.access_time.strftime("%Y-%m-%dT%H:%M:%S")
        self.requirements = BidsDataset.requirements
        # check if there is a parsing file in the derivatives and load it as the current dataset state
        try:
            flag = self.check_latest_parsing_file()
            if flag:
                self.parse_bids()
            else:
                if self.update_text:
                    self.update_text(self.curr_log, delete_flag=False)
        except (FileNotFoundError, KeyError) as err:
            self.write_log('An error occurred {}.\nRefreshing Bids dataset!'.format(err))
            self.parse_bids()
        # check if parsing and log pipeline were created otherwise make them
        self.make_func_pipeline()

    def get_all_logs(self):
        logs = ''
        if os.path.exists(os.path.join(self.dirname, BidsDataset.parsing_path)):
            list_of_files = os.listdir(os.path.join(self.dirname, BidsDataset.log_path))
            list_of_log_files = [os.path.join(self.dirname, BidsDataset.log_path, file)
                                 for file in list_of_files if file.startswith('bids_') and file.endswith('.log')]
            if list_of_log_files:
                list_of_log_files = sorted(list_of_log_files, key=os.path.getctime)
                for log_file in list_of_log_files:
                    with open(log_file, 'r') as file:
                        for line in file:
                            logs += line
        return logs

    def check_latest_parsing_file(self):
        def read_file(filename):
            with gzip.open(filename, 'rb') as f_in, open(filename.replace('.gz', ''), 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            with open(filename.replace('.gz', ''), 'r') as file:
                rd_json = json.load(file)
            os.remove(filename.replace('.gz', ''))
            return rd_json

        if os.path.exists(os.path.join(self.dirname, BidsDataset.parsing_path)):
            latest_parsing = latest_file(os.path.join(self.dirname, BidsDataset.parsing_path), 'parsing')
            if latest_parsing:
                BidsBrick.access_time = datetime.now()
                self.__class__.clear_log()
                # self.write_log('Current User: ' + self.curr_user)
                # First read requirements.json which should be in the code folder of bids dir.
                self.get_requirements()
                read_json = read_file(latest_parsing)
                self.copy_values(read_json)
                self.issues.check_with_latest_issue()
                # the latest log file may have been created after the latest parsing file (case of issues removal
                #  which does not affect parsing.json)
                log_file = latest_file(os.path.join(self.dirname, self.log_path), 'log')
                log_line = []
                if log_file:
                    with open(log_file, 'r') as file:
                        for line in file:
                            log_line.append(line)
                    if len(log_line) > 100000:
                        self.__class__.curr_log += 'The log is too big to be displayed on Bids Manager.\n Please use text editor to read it.\n'
                    else:
                        for line in log_line:
                            self.__class__.curr_log += line
                    print(self.__class__.curr_log)
                return False  # no need to parse the dataset
        return True  # need to parse the dataset

    def parse_bids(self):

        def parse_sub_bids_dir(sub_currdir, subinfo, num_ses=None, mod_dir=None, srcdata=False, flag_process=False):
            with os.scandir(sub_currdir) as it:
                for file in it:
                    if file.name.startswith('ses-') and file.is_dir():
                        num_ses = file.name.replace('ses-', '')
                        parse_sub_bids_dir(file.path, subinfo, num_ses=num_ses, srcdata=srcdata,
                                           flag_process=flag_process)
                    elif not mod_dir and file.name.capitalize() in ModalityType.get_list_subclasses_names() and \
                            file.is_dir():
                        # enumerate permits to filter the key that corresponds to other subclass e.g Anat, Func, Ieeg
                        parse_sub_bids_dir(file.path, subinfo, num_ses=num_ses, mod_dir=file.name.capitalize(),
                                           srcdata=srcdata, flag_process=flag_process)
                    elif not mod_dir and file.name.endswith('_scans.tsv') and file.is_file():
                        tmp_scantsv = ScansTSV()
                        tmp_scantsv.read_file(file)
                        for scan in subinfo['Scans']:
                            is_same = scan.compare_scanstsv(tmp_scantsv)
                            if is_same:
                                scan['fileLoc'] = file.path
                    elif mod_dir and file.is_file():
                        if flag_process and not mod_dir.endswith('Process'):
                            mod_dir = mod_dir + 'Process'
                        filename, ext = os.path.splitext(file)
                        if ext.lower() == '.gz':
                            filename, ext = os.path.splitext(filename)
                        if ext.lower() in eval(mod_dir + '.allowed_file_formats') or \
                                (srcdata and ext.lower() in eval(mod_dir + '.readable_file_formats')):
                            subinfo[mod_dir] = eval(mod_dir + '()')
                            # create empty object for the given modality
                            subinfo[mod_dir][-1]['fileLoc'] = file.path
                            # here again, modified dict behaviour, it appends to a list therefore checking the last
                            # element is equivalent to checking the newest element
                            if not srcdata:
                                subinfo[mod_dir][-1].get_attributes_from_filename()
                                subinfo[mod_dir][-1].get_sidecar_files()
                                subinfo.check_file_in_scans(file.name, mod_dir)
                            if 'MegHeadShape' in subinfo[mod_dir][-1] and isinstance(subinfo[mod_dir][-1]['MegHeadShape'], MegHeadShape):
                                subinfo[mod_dir][-1]['MegHeadShape'].clear_head()
                            # need to find corresponding json file and import it in modality json class
                        elif mod_dir + 'GlobalSidecars' in BidsBrick.get_list_subclasses_names() and ext.lower() \
                                in eval(mod_dir + 'GlobalSidecars.allowed_file_formats') and filename.split('_')[-1]\
                                in [eval(value + '.modality_field') for _, value in
                                    enumerate(eval(mod_dir +'GlobalSidecars.complementary_keylist'))]:
                            subinfo[mod_dir + 'GlobalSidecars'] = eval(mod_dir + 'GlobalSidecars(filename+ext)')
                            subinfo[mod_dir + 'GlobalSidecars'][-1]['fileLoc'] = file.path
                            subinfo[mod_dir + 'GlobalSidecars'][-1].get_attributes_from_filename()
                            subinfo[mod_dir + 'GlobalSidecars'][-1].get_sidecar_files()
                        # elif flag_process and ext.lower() in Process.allowed_file_formats:
                        #     subinfo[mod_dir] = getattr(modules[__name__], mod_dir)()
                        #     subinfo[mod_dir][-1]['fileLoc'] = file.path
                        #     subinfo[mod_dir][-1].get_attributes_from_filename()
                        #     subinfo[mod_dir][-1].get_sidecar_files()
                    elif mod_dir and file.is_dir():
                        if flag_process and not mod_dir.endswith('Process'):
                            mod_dir = mod_dir + 'Process'
                        subinfo[mod_dir] = getattr(modules[__name__], mod_dir)()
                        subinfo[mod_dir][-1]['fileLoc'] = file.path
                        if mod_dir == 'Meg':
                            subinfo[mod_dir][-1].get_attributes_from_filename()
                            subinfo[mod_dir][-1].get_sidecar_files()
                            if isinstance(subinfo[mod_dir][-1]['MegHeadShape'], MegHeadShape):
                                subinfo[mod_dir][-1]['MegHeadShape'].clear_head()

            for scan in subinfo['Scans']:
                scan['ScansTSV'].write_file(os.path.join(BidsDataset.dirname, scan['fileLoc']))

        def parse_bids_dir(bids_brick, currdir, sourcedata=False, flag_process=False):

            with os.scandir(currdir) as it:
                for entry in it:
                    if entry.name.startswith('sub-') and entry.is_dir():
                        # bids_brick['Subject'] = Subject('derivatives' not in entry.path and 'sourcedata' not in
                        #                                 entry.path)
                        if not flag_process:
                            str_sub = Subject.__name__
                        else:
                            str_sub = SubjectProcess.__name__
                        bids_brick[str_sub] = getattr(modules[__name__], str_sub)()
                        bids_brick[str_sub][-1]['sub'] = entry.name.replace('sub-', '')
                        if not flag_process and isinstance(bids_brick, BidsDataset) and bids_brick['ParticipantsTSV']:
                            bids_brick[str_sub][-1].get_attr_tsv(bids_brick['ParticipantsTSV'])
                        parse_sub_bids_dir(entry.path, bids_brick[str_sub][-1], srcdata=sourcedata,
                                           flag_process=flag_process)
                        # since all Bidsbrick that are not string are appended [-1] is enough
                    elif entry.name == 'sourcedata' and entry.is_dir():
                        bids_brick['SourceData'] = SourceData()
                        bids_brick['SourceData'][-1]['SrcDataTrack'] = SrcDataTrack()
                        bids_brick['SourceData'][-1]['SrcDataTrack'].read_file()
                        parse_bids_dir(bids_brick['SourceData'][-1], entry.path, sourcedata=True)
                    elif entry.name == 'derivatives' and entry.is_dir():
                        bids_brick['Derivatives'] = Derivatives()
                        parse_bids_dir(bids_brick['Derivatives'][-1], entry.path)
                    elif os.path.basename(currdir) == 'derivatives' and isinstance(bids_brick, Derivatives)\
                            and entry.is_dir():
                        bids_brick['Pipeline'] = Pipeline()
                        bids_brick['Pipeline'][-1]['name'] = entry.name
                        bids_brick['Pipeline'][-1]['DatasetDescJSON'] = DatasetDescJSON()
                        bids_brick['Pipeline'][-1]['DatasetDescJSON'].read_file(
                            jsonfilename=os.path.join(entry.path, DatasetDescJSON.filename))
                        if os.path.exists(os.path.join(entry.path, ParticipantsTSV.filename)):
                            bids_brick['Pipeline'][-1]['ParticipantsProcessTSV'] = ParticipantsProcessTSV()
                            # only need the "participants_id" not all the other info from the main participants.tsv
                            # bids_brick['Pipeline'][-1]['ParticipantsTSV'].required_fields = \
                            #     [bids_brick['Pipeline'][-1]['ParticipantsTSV'].required_fields[0]]
                            bids_brick['Pipeline'][-1]['ParticipantsProcessTSV'].read_file(
                                tsv_full_filename=os.path.join(entry.path, ParticipantsTSV.filename))
                        parse_bids_dir(bids_brick['Pipeline'][-1], entry.path, flag_process=True)

        BidsBrick.access_time = datetime.now()
        self.clear()  # clear the bids variable before parsing to avoid rewrite the same things
        self.__class__.clear_log()
        self.issues.clear()  # clear issue to only get the unsolved ones but
        # self.write_log('Current User: ' + self.curr_user + '\n' + BidsBrick.access_time.strftime("%Y-%m-%dT%H:%M:%S"))
        # First read requirements.json which should be in the code folder of bids dir.
        self.get_requirements()

        self['DatasetDescJSON'] = DatasetDescJSON()
        self['DatasetDescJSON'].read_file()
        self['ParticipantsTSV'] = ParticipantsTSV()
        self['ParticipantsTSV'].read_file()

        #verify the datasetdescription
        self['DatasetDescJSON'].has_all_req_attributes()
        if not self['DatasetDescJSON'].is_complete and \
                self['DatasetDescJSON']['Name'] == DatasetDescJSON.bids_default_unknown:
            raise NameError(DatasetDescJSON.filename + ' needs at least these elements: ' + \
                         str(DatasetDescJSON.required_keys) + 'to be filled.\n Please modify your dataset_description.json.')

        if not self.requirements['Requirements'] or 'Subject' in self.requirements['Requirements'] and \
                not self.requirements['Requirements']['Subject']:
            # create and save the requirements if either requirements does not exist or subject requirement is empty
            keylist = [key for key in self['ParticipantsTSV'].header
                       if key not in self['ParticipantsTSV'].required_fields]
            # put the _ready elements at the end of the file
            ParticipantsTSV.header = [self['ParticipantsTSV'].required_fields[0]] + keylist + \
                                     self['ParticipantsTSV'].required_fields[1:]
            self.requirements['Requirements']['Subject'] = dict()
            self.requirements['Requirements']['Subject']['keys'] = {key: '' for key in keylist}
            self.requirements.save_as_json()
            self.get_requirements()
        else:
            # modify also for incomplete requirements !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # check whether the number of keys in Subject keys matches the number of elements in participants.tsv
            sub_keys = self.requirements['Requirements']['Subject']['keys']
            keylist = [key for key in self['ParticipantsTSV'].header
                       if key not in self['ParticipantsTSV'].required_fields and key not in sub_keys]
            if keylist:
                for key in keylist:
                    self.requirements['Requirements']['Subject']['keys'][key] = ''
                self.requirements.save_as_json()

        parse_bids_dir(self, self.dirname)
        self.check_requirements()
        self.save_as_json()

    def has_subject_modality_type(self, subject_label, modality_type):
        """
        Method that look if a given subject has a given modality type (e.g. Anat, Ieeg). It returns a tuple composed
        of a boolean, an integer and a dict. The boolean is True if the sub has the mod type, the integer gives the
        number of recordings of the modality and the dict returns the number of recordings of each modality
        Ex: (True, 4, {'T1w': 2, 'T2w':2}) = bids.has_subject_modality_type('01', 'Anat')
        """
        modality_type = modality_type.capitalize()
        if modality_type in ModalityType.get_list_subclasses_names():
            if not self.curr_subject or not self.curr_subject['Subject']['sub'] == subject_label:
                # check whether the required subject is the current subject otherwise make it the current one
                self.is_subject_present(subject_label)

            bln = self.curr_subject['isPresent']
            sub_index = self.curr_subject['index']

            if bln:
                _, ses_list = self.get_number_of_session4subject(subject_label)
                curr_sub = self['Subject'][sub_index]
                if curr_sub[modality_type]:
                    allowed_mod = eval(modality_type + '.allowed_modalities')
                    if ses_list:  # create a list of tuple to be used as keys ex: ('ses-01', 'T1w')
                        key_list = []

                        for ses_label in ses_list:
                            for key in allowed_mod:
                                key_list += [('ses-' + ses_label, key)]
                        resume_modality = {key: 0 for key in key_list}
                    else:
                        key_list = allowed_mod
                        resume_modality = {key: 0 for key in key_list}
                    for mod_dict in curr_sub[modality_type]:
                        if mod_dict['ses']:  # if at least one session exists
                            resume_modality[('ses-' + mod_dict['ses'], mod_dict['modality'])] += 1
                        else:
                            resume_modality[mod_dict['modality']] += 1
                    [resume_modality.__delitem__(key) for key in key_list
                     if resume_modality[key] == 0]
                    return True, len(curr_sub[modality_type]), resume_modality
                else:
                    return False, 0, {}
            else:
                raise NameError('subject: ' + subject_label + ' is not present in the database')
        else:
            raise NameError('modality_type: ' + modality_type + ' is not a correct modality type.\n'
                                                                'Check ModalityType.get_list_subclasses_names().')

    def get_number_of_session4subject(self, subject_label, flag_process=False):
        if flag_process:
            str='Process'
        else:
            str=''
        if not self.curr_subject or not self.curr_subject['Subject' + str]['sub'] == subject_label:
            # check whether the required subject is the current subject otherwise make it the current one
            self.is_subject_present(subject_label, flagProcess=flag_process)
        bln = self.curr_subject['isPresent']
        sub_index = self.curr_subject['index']
        if self.curr_subject['Subject'+str].is_empty():
            # if a subject is created without any data (in case of the first import crashes) return None because
            return None, None
        if bln:
            ses_list = []
            sub = self['Subject'+str][sub_index]
            for mod_type in sub:
                if mod_type in ModalityType.get_list_subclasses_names() + GlobalSidecars.get_list_subclasses_names():
                    mod_list = sub[mod_type]
                    for mod in mod_list:
                        if mod['ses'] and mod['ses'] not in ses_list:
                            # 'ses': '' means no session therefore does not count
                            ses_list.append(mod['ses'])
            return len(ses_list), ses_list
        else:
            raise NameError('subject: ' + subject_label + ' is not present in the database')

    def get_number_of_runs(self, mod_dict_with_attr, flag_process=False):
        """
        Method that returns the number of runs if in key list in database for a schema of modality dict.
        Ex:
        func_schema = Func()
        func_schema['sub'] = '01'
        func_schema['ses'] = '01'
        func_schema['task'] = 'bapa'
        N = bids.get_number_of_runs(func_schema)
        """
        if flag_process:
            st2add = 'Process'
        else:
            st2add = ''
        nb_runs = None
        highest_run = None
        if 'run' in mod_dict_with_attr.keylist:
            mod_type = mod_dict_with_attr.classname()
            if mod_type in ModalityType.get_list_subclasses_names():
                if not self.curr_subject or not self.curr_subject['Subject'+st2add]['sub'] == mod_dict_with_attr['sub']:
                    # check whether the required subject is the current subject otherwise make it the current one
                    self.is_subject_present(mod_dict_with_attr['sub'])
                bln = self.curr_subject['isPresent']
                sub_index = self.curr_subject['index']
                if bln:
                    if self['Subject'+st2add][sub_index][mod_type]:
                        mod_input_attr = mod_dict_with_attr.get_attributes(['fileLoc', 'run'])
                        # compare every attributes but fileLoc and run
                        for mod in self['Subject'+st2add][sub_index][mod_type]:
                            mod_attr = mod.get_attributes('fileLoc')
                            idx_run = mod_attr.pop('run')
                            if mod_input_attr == mod_attr and idx_run:
                                if nb_runs is None:
                                    nb_runs = 0
                                    highest_run = 0
                                idx_run = int(idx_run)
                                nb_runs += 1
                                highest_run = max(highest_run, idx_run)
        return nb_runs, highest_run

    def import_data(self, data2import, keep_sourcedata=True, keep_file_trace=True):

        def push_into_dataset(bids_dst, mod_dict2import, keep_srcdata, keep_ftrack, flag_process=False):
            filename, dirname, ext = mod_dict2import.create_filename_from_attributes()

            fname2import, ext2import = os.path.splitext(mod_dict2import['fileLoc'])
            orig_ext = ext2import
            dest_deriv = None
            # bsname_bids_dir = os.path.basename(bids_dst.dirname)
            sidecar_flag = [value for _, value in enumerate(mod_dict2import.keylist) if value in
                            BidsSidecar.get_list_subclasses_names()]
            mod_type = mod_dict2import.classname()
            if flag_process:
                sub = bids_dst.curr_subject['SubjectProcess']
                dest_deriv = bids_dst.dirname
            else:
                sub = bids_dst.curr_subject['Subject']
            fnames_list = mod_dict2import.convert(dest_deriv)
            tmp_attr = mod_dict2import.get_attributes()
            tmp_attr['fileLoc'] = os.path.join(bids_dst.dirname, dirname, fnames_list[0])

            if isinstance(mod_dict2import, GlobalSidecars):
                sub[mod_type] = eval(mod_type + '(tmp_attr["fileLoc"])')
            else:
                sub[mod_type] = eval(mod_type + '()')
            sub[mod_type][-1].update(tmp_attr)

            if keep_srcdata and not isinstance(mod_dict2import, GlobalSidecars):
                scr_data_dirname = os.path.join(BidsDataset.dirname, 'sourcedata', dirname)
                if not os.path.exists(scr_data_dirname):
                    os.makedirs(scr_data_dirname)
                path_src = os.path.join(Data2Import.dirname, mod_dict2import['fileLoc'])
                path_dst = os.path.join(scr_data_dirname, os.path.basename(mod_dict2import['fileLoc']))
                if os.path.isdir(path_src):
                    # if source data is a directory simply import the folder
                    path_src = [path_src]
                    path_dst = [path_dst]
                else:
                    # if source data is a file, find all files in the data2import folder with the same fname but
                    # diff ext
                    src_dir = os.path.dirname(path_src)
                    f_list = os.listdir(src_dir)
                    fbasename = os.path.splitext(os.path.basename(mod_dict2import['fileLoc']))[0]
                    path_src = [os.path.join(src_dir, file) for file in f_list if os.path.splitext(file)[0]
                                == fbasename]
                    path_dst = [os.path.join(scr_data_dirname, os.path.basename(file)) for file in path_src]
                for cnt, src_fname in enumerate(path_src):
                    try:
                        shutil.move(src_fname, path_dst[cnt])
                    except:
                        shutil.copy2(src_fname, path_dst[cnt])
                    if os.path.basename(src_fname) == os.path.basename(mod_dict2import['fileLoc']):
                        try:
                            src_data_sub = bids_dst['SourceData'][-1]['Subject'][bids_dst.curr_subject['index']]
                        except:
                            bids_dst['SourceData'][-1].is_subject_present(sub['sub'])
                            if bids_dst['SourceData'][-1].curr_subject['isPresent']:
                                src_data_sub = bids_dst['SourceData'][-1].curr_subject['Subject']
                            else:
                                bids_dst['SourceData'][-1]['Subject'].append(Subject())
                                src_data_sub = bids_dst['SourceData'][-1]['Subject'][-1]
                        src_data_sub[mod_type] = eval(mod_type + '()')
                        tmp_attr = mod_dict2import.get_attributes()
                        tmp_attr['fileLoc'] = path_dst[cnt]
                        src_data_sub[mod_type][-1].update(tmp_attr)
                        if keep_ftrack:
                            orig_fname = os.path.basename(src_data_sub[mod_type][-1]['fileLoc'])
                            upload_date = bids_dst.access_time.strftime("%Y-%m-%dT%H:%M:%S")
                            scr_track = bids_dst['SourceData'][-1]['SrcDataTrack']
                            scr_track.append({'orig_filename': orig_fname, 'bids_filename': filename,
                                              'upload_date': upload_date})
                            scr_track.write_file()

            if sidecar_flag:
                for sidecar_tag in sidecar_flag:
                    if mod_dict2import[sidecar_tag]:
                        if mod_dict2import[sidecar_tag].modality_field:
                            fname = filename.replace(mod_dict2import['modality'],
                                                     mod_dict2import[sidecar_tag].modality_field)
                        else:
                            fname = filename
                        if flag_process:
                            fname2bewritten = os.path.join(bids_dst.dirname, dirname, fname +
                                                           mod_dict2import[sidecar_tag].extension)
                        else:
                            fname2bewritten = os.path.join(BidsDataset.dirname, dirname, fname +
                                                           mod_dict2import[sidecar_tag].extension)
                        mod_dict2import[sidecar_tag].write_file(fname2bewritten)
                if flag_process:
                    sub[mod_type][-1].get_sidecar_files(input_dirname=bids_dst.dirname, input_filename=fname)
                else:
                    sub[mod_type][-1].get_sidecar_files()
                    if 'MegHeadShape' in sidecar_flag:
                        sub[mod_type][-1]['MegHeadShape'].clear_head()

            # To write the scans.tsv
            if not flag_process:
                ses_list = [scan['ses'] for scan in sub['Scans']]
                if tmp_attr['ses'] in ses_list:
                    ses_index = ses_list.index(tmp_attr['ses'])
                    sub['Scans'][ses_index].add_modality(sub[mod_type][-1], bids_dst)
                else:
                    sub['Scans'].append(Scans())
                    sub['Scans'][-1].add_modality(sub[mod_type][-1], bids_dst)

            mod_dict2import.write_log(mod_dict2import['fileLoc'] + ' was imported as ' + filename)

        def have_data_same_source_file(bids_dict, mod_dict):
            flg = False
            if bids_dict['SourceData']:
                src_dict = bids_dict['SourceData'][-1]
                input_basefname = os.path.basename(mod_dict['fileLoc'])
                if src_dict['SrcDataTrack']:
                    for line in src_dict['SrcDataTrack'][1:]:
                        word_grp = line[1].split('_')
                        sub_id = word_grp[0].split('-')[1]
                        flg = line[0] == input_basefname and sub_id == mod_dict['sub']
                        if flg and 'ses' in word_grp[1]:
                            ses_id = word_grp[1].split('-')[1]
                            flg = flg and ses_id == mod_dict['ses']
                        if flg:
                            break
                else:
                    src_dict.is_subject_present(mod_dict['sub'])
                    src_sub = src_dict.curr_subject['Subject']
                    flg = any(os.path.basename(mod_brick['fileLoc']) == input_basefname
                              for mod_brick in src_sub[mod_dict.classname()])
            return flg

        def have_data_same_attrs_and_sidecars(bids_dst, mod_dict2import, sub_idx, flag_process=False):
            """
            Method that compares whether a given modality dict is the same as the ones present in the bids dataset.
            Ex: True = bids.have_data_same_attrs_and_sidecars(instance of Anat())
            """
            if flag_process:
                bids_mod_list = bids_dst['SubjectProcess'][sub_idx][mod_dict2import.classname()]
            else:
                bids_mod_list = bids_dst['Subject'][sub_idx][mod_dict2import.classname()]
            mod_dict2import_attr = mod_dict2import.get_attributes('fileLoc')
            for mod in bids_mod_list:
                mod_in_bids_attr = mod.get_attributes('fileLoc')
                if mod_dict2import_attr == mod_in_bids_attr:  # check if both mod dict have same attributes
                    # if 'run' in mod_dict2import_attr.keys() and mod_dict2import_attr['run']:
                    #     # if run if a key check the JSON and possibly increment the run integer of mod_
                    #     # dict2import to import it
                    #     mod_dict2import_dep = mod_dict2import.extract_sidecares_from_sourcedata()
                    #     highest_run = bids_dst.get_number_of_runs(mod_dict2import)[1]
                    #     mod_in_bids_dep = mod.get_modality_sidecars()
                    #     if not mod_dict2import_dep == mod_in_bids_dep:
                    #         # check the sidecar files to verify whether they are the same data, in that the case
                    #         # add current nb_runs to 'run' if available otherwise do not import
                    #         mod_dict2import['run'] = str(1 + highest_run).zfill(2)
                    #         return False
                    return True
            return False

        def check_self_after_error(bids_dict, modality):
            if bids_dict.curr_subject['Subject']['sub'] == modality['sub']:
                attr_dict = modality.get_attributes('fileLoc')
                idx_in = [cnt for cnt, elt in enumerate(bids_dict['Subject'][bids_dict.curr_subject['index']][modality.classname()]) if elt.get_attributes('fileLoc') == attr_dict]
                if idx_in:
                    bids_dict['Subject'][bids_dict.curr_subject['index']][modality.classname()].pop(idx_in[0])
                if bids_dict['Subject'][bids_dict.curr_subject['index']].is_empty():
                    bids_dict['Subject'].pop(bids_dict.curr_subject['index'])
                    is_in, sub_info, sub_index = bids_dict['ParticipantsTSV'].is_subject_present(modality['sub'])
                    if is_in:
                        bids_dict['ParticipantsTSV'].pop(sub_index)
                    if os.path.exists(os.path.join(bids_dict.dirname, 'sub-' + modality['sub'])):
                        shutil.rmtree(os.path.join(bids_dict.dirname, 'sub-' + modality['sub']))
                else:
                    for sc in bids_dict['Subject'][bids_dict.curr_subject['index']]['Scans']:
                        sc.write_file()


        # if True:
        self.__class__.clear_log()
        self.write_log(10*'=' + '\nImport of ' + data2import.dirname + '\n' + 10*'=')
        if not isinstance(data2import, Data2Import) or not data2import.has_all_req_attributes()[0]:
            flag, missing_str = data2import.has_all_req_attributes()
            self.write_log(missing_str)
            return

        if not self.verif_upload_issues(data2import.dirname):
            error_str = 'Some elements in ' + data2import.dirname + ' have not been verified.'
            self.write_log(error_str)
            return

        if not BidsDataset.converters['Electrophy']['path'] or \
                not os.path.isfile(BidsDataset.converters['Electrophy']['path']) or \
                not BidsDataset.converters['Imaging']['path'] or \
                not os.path.isfile(BidsDataset.converters['Imaging']['path']):
            error_str = 'At least one converter path in requirements.json is wrongly set'
            self.issues.add_issue(issue_type='ImportIssue', description=error_str, brick=None)
            self.write_log(error_str)
            return

        if not data2import['DatasetDescJSON']['Name'] == self['DatasetDescJSON']['Name']:
            error_str = 'The data to be imported (' + os.path.basename(data2import.dirname) + ') belong to a different protocol (' \
                        + data2import['DatasetDescJSON']['Name'] + ') than the current bids dataset (' \
                        + self['DatasetDescJSON']['Name'] + ').'
            self.issues.add_issue(issue_type='ImportIssue', brick=data2import['DatasetDescJSON'],
                                  description=error_str)
            self.write_log(error_str)
            return

        '''Here we copy the data2import dictionary to pop all the imported data in order to avoid importing
        the same data twice in case there is an error and we have to launch the import procedure on the same
        folder again. The original data2import is renamed by adding the date at the end of the filename'''
        if not BidsBrick.cwdir == data2import.dirname:
            Data2Import._assign_import_dir(data2import.dirname)
        copy_data2import = Data2Import()
        copy_data2import.copy_values(data2import)
        copy_data2import.dirname = data2import.dirname
        sublist = set()  # list to store subject who received new data
        try:
            data2import.save_as_json(write_date=True)
            if keep_sourcedata:
                if not self['SourceData']:
                    self['SourceData'] = SourceData()
                    if keep_file_trace:
                        self['SourceData'][-1]['SrcDataTrack'] = SrcDataTrack()

            self._assign_bids_dir(self.dirname)  # make sure to import in the current bids_dir
            for sub in data2import['Subject']:
                import_sub_idx = data2import['Subject'].index(sub)
                # test if subject is already present
                if not self.curr_subject or not self.curr_subject['Subject']['sub'] == sub['sub']:
                    # check whether the required subject is the current subject otherwise make it the
                    # current one
                    self.is_subject_present(sub['sub'])
                sub_present = self.curr_subject['isPresent']
                sub_index = self.curr_subject['index']

                # # test whether the subject data have all attributes required by bids
                # [flag, missing_str] = sub.has_all_req_attributes()
                # if not flag:
                #     self.issues.add_issue('ImportIssue', brick=sub,
                #                           description=missing_str + ' (' + data2import.dirname + ')')
                #     self.write_log(missing_str)
                #     continue

                # test whether the subject to be imported has the same attributes as the one already inside the
                # bids dataset
                not_req_keys = [elmt for elmt in Subject.keylist if elmt not in Subject.required_keys]
                req_keys_and_clin = [elmt for elmt in Subject.keylist if elmt in Subject.required_keys or elmt in BidsBrick.get_list_subclasses_names()]
                if sub_present and not self.curr_subject['Subject'].get_attributes(not_req_keys) == \
                                       sub.get_attributes(not_req_keys):
                    error_str = 'The subject to be imported (' + os.path.basename(data2import.dirname) + \
                                ') has different attributes than the analogous subject in the bids dataset (' \
                                + str(sub.get_attributes(not_req_keys)) + '=/=' + \
                                str(self.curr_subject['Subject'].get_attributes(not_req_keys)) + ').'
                    self.issues.add_issue('ImportIssue', brick=sub, description=error_str)
                    self.write_log(error_str)
                    continue
                elif sub_present:
                    clin_to_update = sub.get_attributes(req_keys_and_clin)
                    key_to_remove = [key for key in clin_to_update if not clin_to_update[key] or clin_to_update[key] == BidsSidecar.bids_default_unknown]
                    for key in key_to_remove:
                        del clin_to_update[key]
                    self['Subject'][sub_index].copy_values(clin_to_update)
                    self['ParticipantsTSV'].update_subject(sub['sub'], clin_to_update)

                for modality_type in sub.keys():
                    if modality_type in BidsBrick.get_list_subclasses_names():
                        for modality in sub[modality_type]:
                            # flag, missing_str = modality.has_all_req_attributes()
                            # if not flag:
                            #     self.issues.add_issue('ImportIssue', brick=modality,
                            #                           description=missing_str + ' (' + data2import.dirname + ')')
                            #     self.write_log(missing_str)
                            #     continue
                            self.write_log('Start importing ' + modality['fileLoc'])
                            """check again if the subject is present because it could be absent at the beginning but
                            you could have added data from the subject in a previous iteration of the loop.
                            For instance, if you add a T1w and by mistake add the another T1w but with the same
                            attributes you need to know what was previously imported for the subject"""
                            self.is_subject_present(sub['sub'])
                            sub_present = self.curr_subject['isPresent']
                            sub_index = self.curr_subject['index']

                            if sub_present:

                                nb_ses, bids_ses = self.get_number_of_session4subject(sub['sub'])
                                if nb_ses is None or modality['ses'] and bids_ses:
                                    """ if subject is present, have to check if ses in the data2import matches
                                    the session structures of the dataset (if ses-X already exist than
                                    data2import has to have a ses), However, empty patient return None ses struct"""
                                    same_src_file_bln = have_data_same_source_file(self, modality)
                                    if not same_src_file_bln:
                                        same_attr_bln = have_data_same_attrs_and_sidecars(self, modality,
                                                                                          sub_index)
                                        if same_attr_bln:
                                            string_issue = 'Subject ' + sub['sub'] + '\'s file:' + modality[
                                                'fileLoc'] \
                                                           + ' was not imported from ' + os.path.basename(data2import.dirname) + \
                                                           ' because ' + \
                                                           modality.create_filename_from_attributes()[0] + \
                                                           ' is already present in the bids dataset ' + \
                                                           '(' + self['DatasetDescJSON']['Name'] + ').'
                                            self.issues.add_issue('ImportIssue', brick=modality,
                                                                  description=string_issue)
                                            self.write_log(string_issue)
                                            continue
                                    else:
                                        string_issue = 'Subject ' + sub['sub'] + '\'s file:' + \
                                                       modality['fileLoc'] + ' was not imported from ' + \
                                                       os.path.basename(data2import.dirname) +\
                                                       ' because a source file with the same name is already ' \
                                                       'present in the bids dataset ' + \
                                                       self['DatasetDescJSON']['Name'] + '.'
                                        self.issues.add_issue('ImportIssue', brick=modality,
                                                              description=string_issue)
                                        self.write_log(string_issue)
                                        continue
                                else:
                                    string_issue = 'Session structure of the data to be imported (' + \
                                                   os.path.basename(data2import.dirname) + ')does not ' \
                                                   'match the one of the current dataset.\nSession label(s): ' \
                                                   + ', '.join(bids_ses) + '.\nSubject ' + sub['sub'] + \
                                                   ' not imported.'
                                    self.issues.add_issue('ImportIssue', brick=modality,
                                                          description=string_issue)
                                    self.write_log(string_issue)
                                    continue
                            else:
                                self['Subject'] = Subject()
                                self['Subject'][-1].update(sub.get_attributes())
                                self['ParticipantsTSV'].add_subject(sub)
                                self.is_subject_present(sub['sub'])
                                sub_present = self.curr_subject['isPresent']
                                sub_index = self.curr_subject['index']
                                if keep_sourcedata:
                                    self['SourceData'][-1]['Subject'] = Subject()
                                    self['SourceData'][-1]['Subject'][-1].update(sub.get_attributes())

                            self.issues.remove(modality)
                            # need to get the index before importing because push_into_dataset adds data from sidecars
                            idx2pop = copy_data2import['Subject'][import_sub_idx][modality_type].index(modality)
                            push_into_dataset(self, modality, keep_sourcedata, keep_file_trace)
                            self.save_as_json()
                            self.issues.save_as_json()
                            copy_data2import['Subject'][import_sub_idx][modality_type].pop(idx2pop)
                            copy_data2import.save_as_json()
                            sublist.add(sub['sub'])
                    # if copy_data2import['Subject'][import_sub_idx].is_empty():
                    # pop empty subject
                if not sub_index is None:
                    for scan in self['Subject'][sub_index]['Scans']:
                        scan.write_file()

            # Add the derivatives folder
            for dev in data2import['Derivatives']:
                idxdev = data2import['Derivatives'].index(dev)
                if not os.path.exists(os.path.join(BidsDataset.dirname, 'derivatives')):
                    os.makedirs(os.path.join(BidsDataset.dirname, 'derivatives'))
                for pip in dev['Pipeline']:
                    idxpip = dev['Pipeline'].index(pip)
                    if not os.path.exists(os.path.join(BidsDataset.dirname, 'derivatives', pip['name'])):
                        os.makedirs(os.path.join(BidsDataset.dirname, 'derivatives', pip['name']))
                    self.is_pipeline_present(pip['name'])
                    pip_present = self.curr_pipeline['isPresent']
                    pip_index = self.curr_pipeline['index']
                    if pip_present:
                        if not pip['DatasetDescJSON']['Name'] == self.curr_pipeline['Pipeline']['DatasetDescJSON']['Name']:
                            error_str = 'Derivatives folder ' + pip['name'] + ' is already present in the database with the following protocol (' \
                                    + self.curr_pipeline['Pipeline']['DatasetDescJSON']['Name'] + ') whereas the data to be imported ('+ os.path.basename(data2import.dirname) \
                                        +') belong to a different protocol (' + pip['DatasetDescJSON']['Name'] + ').'
                            self.issues.add_issue(issue_type='ImportIssue', brick=pip['DatasetDescJSON'],
                                                  description=error_str)
                            self.write_log(error_str)
                            return
                        pipDataset = self.curr_pipeline['Pipeline']
                    else:
                        pipDataset = Pipeline(pip['name'])
                        self['Derivatives'][0]['Pipeline'].append(pipDataset)
                        self.is_pipeline_present(pip['name'])

                    pipDataset.dirname = os.path.join(BidsDataset.dirname, 'derivatives', pip['name'])
                    for sub in pip['SubjectProcess']:
                        import_sub_idx = pip['SubjectProcess'].index(sub)

                        # test if subject is already present
                        if not pipDataset.curr_subject or not pipDataset.curr_subject['SubjectProcess']['sub'] == sub['sub']:
                            # check whether the required subject is the current subject otherwise make it the
                            # current one
                            pipDataset.is_subject_present(sub['sub'], flagProcess=True)
                        sub_present = pipDataset.curr_subject['isPresent']
                        sub_index = pipDataset.curr_subject['index']

                        #Not necessary because, the subject's information are not given in pipeline
                        # if sub_present and not pipDataset.curr_subject['SubjectProcess'].get_attributes(['alias', 'upload_date']) == \
                        #                        sub.get_attributes(['alias', 'upload_date']):
                        #     error_str = 'The subject to be imported (' + os.path.basename(data2import.dirname) + \
                        #                 ') has different attributes than the analogous subject in the bids dataset (' \
                        #                 + str(sub.get_attributes()) + '=/=' + \
                        #                 str(pipDataset.curr_subject['Subject'].get_attributes()) + ').'
                        #     self.issues.add_issue('ImportIssue', brick=sub, description=error_str)
                        #     self.write_log(error_str)
                        #     continue

                        for modality_type in sub.keys():
                            if modality_type in BidsBrick.get_list_subclasses_names():
                                for modality in sub[modality_type]:
                                    self.write_log('Start importing in Derivatives ' + modality['fileLoc'])
                                    """check again if the subject is present because it could be absent at the beginning but
                                    you could have added data from the subject in a previous iteration of the loop.
                                    For instance, if you add a T1w and by mistake add the another T1w but with the same
                                    attributes you need to know what was previously imported for the subject"""
                                    pipDataset.is_subject_present(sub['sub'], flagProcess=True)
                                    sub_present = pipDataset.curr_subject['isPresent']
                                    sub_index = pipDataset.curr_subject['index']

                                    if sub_present:
                                        nb_ses, bids_ses = pipDataset.get_number_of_session4subject(sub['sub'], flag_process=True)
                                        if modality['ses'] and bids_ses:
                                            same_attr_der = have_data_same_attrs_and_sidecars(pipDataset, modality, sub_index, flag_process=True)
                                            if same_attr_der:
                                                string_issue = 'Derivatives folder ' + pip['name'] + ' : Subject ' + sub['sub'] + '\'s file: ' + modality[
                                                    'fileLoc'] \
                                                               + ' was not imported from ' + os.path.basename(data2import.dirname) + \
                                                               ' because ' + \
                                                               modality.create_filename_from_attributes()[0] + \
                                                               ' is already present in the bids dataset.'
                                                self.issues.add_issue('ImportIssue', brick=modality,
                                                                      description=string_issue)
                                                self.write_log(string_issue)
                                                continue
                                        else:
                                            string_issue = 'Derivatives folder ' + pip['name'] + ' : Session structure of the data to be imported (' + \
                                                            os.path.basename(data2import.dirname) + ')does not ' \
                                                                                     'match the one of the current dataset.\nSession label(s): ' \
                                                            + ', '.join(bids_ses) + '.\nSubject ' + sub['sub'] + \
                                                            ' not imported.'
                                            self.issues.add_issue('ImportIssue', brick=modality,
                                                                      description=string_issue)
                                            self.write_log(string_issue)
                                            continue
                                    else:
                                        pipDataset.add_subject(sub)
                                        pipDataset.is_subject_present(sub['sub'], flagProcess=True)

                                    self.issues.remove(modality)
                                    # need to get the index before importing because push_into_dataset adds data from sidecars
                                    try:
                                        keep_sourcedata=False
                                        keep_file_trace=False
                                        idx2pop = copy_data2import['Derivatives'][idxdev]['Pipeline'][idxpip]['SubjectProcess'][import_sub_idx][modality_type].index(modality)
                                        push_into_dataset(pipDataset, modality, keep_sourcedata, keep_file_trace, flag_process=True)
                                        #Not sure this function is useful
                                        pipDataset.update_bids_original(self, modality)
                                        self.save_as_json()
                                        self.issues.save_as_json()

                                        copy_data2import['Derivatives'][idxdev]['Pipeline'][idxpip]['SubjectProcess'][import_sub_idx][modality_type].pop(idx2pop)
                                        copy_data2import.save_as_json(savedir=os.path.join(copy_data2import.dirname))
                                        #sublist.add(sub['sub'])
                                    except FileNotFoundError as err:
                                        exc_type, exc_obj, exc_tb = exc_info()
                                        err_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                                        self.write_log('Error type: ' + str(exc_type) + ', scriptname: ' + err_name + ', line number, ' + str(
                                            exc_tb.tb_lineno) + ': ' + str(err))
                                        copy_data2import.save_as_json(savedir=os.path.join(copy_data2import.dirname))

                                    if pipDataset['ParticipantsProcessTSV']:
                                        part_present, part_info, part_index = pipDataset['ParticipantsProcessTSV'].is_subject_present(sub['sub'])
                                        if not part_present:
                                            pipDataset['ParticipantsProcessTSV'].add_subject(sub)
                            # if copy_data2import['Subject'][import_sub_idx].is_empty():
                            # pop empty subject
                    self.is_pipeline_present(pip['name'])
                    if pipDataset['DatasetDescJSON']:
                        pipDataset['DatasetDescJSON'].write_file(jsonfilename=os.path.join(pipDataset.dirname, 'dataset_description.json'))
                    if pipDataset['ParticipantsProcessTSV']:
                        pipDataset['ParticipantsProcessTSV'].write_file(tsv_full_filename=os.path.join(pipDataset.dirname, 'participants.tsv'))
                    #self.save_as_json()

            if copy_data2import.is_empty():
                if all(file.endswith('.json') or file.endswith('.tsv') or file.endswith('.flt') or file.endswith('.mtg')
                       or file.endswith('.mrk') or file.endswith('.levels')
                       for file in os.listdir(copy_data2import.dirname)):
                    # if there are only the data2import.json and the sidecar files created during conversions,
                    # (Anywave files) the import dir can be removed
                    shutil.rmtree(copy_data2import.dirname)
                    self.write_log(copy_data2import.dirname + ' is now empty and will be removed.')

            # not useful
            # if self['DatasetDescJSON']:
            #     self['DatasetDescJSON'].write_file()
            # data2import.clear()
            # self.parse_bids()

        # shutil.rmtree(data2import.data2import_dir)
        except Exception as err:
            exc_type, exc_obj, exc_tb = exc_info()
            err_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.write_log('Error type: ' + str(exc_type) + ', scriptname: ' + err_name + ', line number, ' +
                           str(exc_tb.tb_lineno) + ': ' + str(err))
            copy_data2import.save_as_json()
            #Check if the modality is not in the parsing
            if ('modality' in locals() or 'modality' in globals()):
                check_self_after_error(self, modality)

        if sublist:
            sublist = list(sublist)
            self.check_requirements(specif_subs=sublist)

        # could make it faster by just appending a new line instead of writing the whole file again
        self['ParticipantsTSV'].write_file()
        self.save_as_json()

        # if self['SourceData'] and self['SourceData'][-1]['SrcDataTrack']:
        #     # could make it faster by just appending a new line instead of writing the whole file again
        #     self['SourceData'][-1]['SrcDataTrack'].write_file()

    def remove(self, element2remove, with_issues=True, in_deriv=None):
        """method to remove either the whole data set, a subject or a file (with respective sidecar files)"""
        # a bit bulky rewrite to make it nice
        if element2remove is self and not isinstance(element2remove, Pipeline):
            shutil.rmtree(self.dirname)
            print('The whole Bids dataset ' + self['DatasetDescJSON']['Name'] + ' has been removed')
            BidsDataset.clear_log()
            self.issues.clear()
            self.clear()
        elif isinstance(element2remove, Subject):
            if not isinstance(element2remove, SubjectProcess) and not in_deriv:
                self.is_subject_present(element2remove['sub'])
                if self.curr_subject['isPresent']:
                    # remove from sourcedata folder
                    if self['SourceData']:
                        self['SourceData'][-1].is_subject_present(element2remove['sub'])
                        if self['SourceData'][-1].curr_subject['isPresent']:
                            shutil.rmtree(os.path.join(self.dirname, 'sourcedata', 'sub-' + element2remove['sub']))
                            self['SourceData'][-1]['Subject'].pop(self['SourceData'][-1].curr_subject['index'])
                            self.save_as_json()
                            self.write_log('Subject ' + element2remove['sub'] + ' has been removed from Bids dataset ' +
                                           self['DatasetDescJSON']['Name'] + ' source folder.')
                            if self['SourceData'][-1]['SrcDataTrack']:
                                # remove from source_data_trace.tsv folder
                                src_tsv = self['SourceData'][-1]['SrcDataTrack']
                                bids_fname_idx = src_tsv.header.index('bids_filename')
                                src_tsv_copy = SrcDataTrack()
                                src_tsv_copy.copy_values([line for line in src_tsv
                                                          if not line[bids_fname_idx].startswith('sub-'
                                                                                                 + element2remove['sub'])])
                                self['SourceData'][-1]['SrcDataTrack'] = src_tsv_copy
                                self['SourceData'][-1]['SrcDataTrack'].write_file()
                                self.save_as_json()
                                self.write_log('Subject ' + element2remove['sub'] + ' has been removed from Bids dataset ' +
                                               self['DatasetDescJSON']['Name'] + ' ' + src_tsv_copy.filename + '.')
                    #remove from derivatives
                    if self['Derivatives']:
                        for pip in self['Derivatives'][0]['Pipeline']:
                            pip.is_subject_present(element2remove['sub'], True)
                            if pip.curr_subject['isPresent']:
                                shutil.rmtree(os.path.join(self.dirname, 'derivatives', pip['name'], 'sub-' + element2remove['sub']))
                                pip['SubjectProcess'].pop(pip.curr_subject['index'])
                                self.save_as_json()
                                self.write_log(
                                    'Subject ' + element2remove['sub'] + ' has been removed from Bids dataset ' +
                                    self['DatasetDescJSON']['Name'] + ' derivatives '+ pip['name'] + ' folder.')
                                _, _, sub_part_idx = pip['ParticipantsProcessTSV'].is_subject_present(element2remove['sub'])
                                if sub_part_idx:
                                    pip['ParticipantsProcessTSV'].pop(sub_part_idx)
                                    pip['ParticipantsProcessTSV'].write_file(tsv_full_filename=os.path.join(self.dirname, 'derivatives', pip['name'], ParticipantsProcessTSV.filename))
                                    self.save_as_json()

                    # remove from ParticipantsTSV
                    _, _, sub_idx = self['ParticipantsTSV'].is_subject_present(element2remove['sub'])
                    if sub_idx:
                        self['ParticipantsTSV'].pop(sub_idx)
                        self['ParticipantsTSV'].write_file()
                        self.save_as_json()
                        self.write_log(
                            'Subject ' + element2remove['sub'] + ' has been removed from Bids dataset ' +
                            self['DatasetDescJSON']['Name'] + ' ' + self['ParticipantsTSV'].filename + '.')
                    if with_issues:
                        # remove issues related to this patient
                        self.issues.remove(element2remove)
                    # remove from raw folder
                    shutil.rmtree(os.path.join(self.dirname, 'sub-' + element2remove['sub']))
                    self['Subject'].pop(self.curr_subject['index'])
                    self.save_as_json()
                    self.write_log('Subject ' + element2remove['sub'] + ' has been removed from Bids dataset ' +
                                   self['DatasetDescJSON']['Name'] + ' raw folder.')
                    self.is_subject_present(element2remove['sub'])
            else:
                if isinstance(self, Pipeline):
                    pip = self
                elif isinstance(self, BidsDataset):
                    self.is_pipeline_present(in_deriv)
                    if self.curr_pipeline['isPresent']:
                        pip = self['Derivatives'][-1]['Pipeline'][self.curr_pipeline['index']]
                pip.is_subject_present(element2remove['sub'], flagProcess=True)
                if pip.curr_subject['isPresent']:
                    shutil.rmtree(os.path.join(self.dirname, 'derivatives', in_deriv, 'sub-'+element2remove['sub']))
                    pip['SubjectProcess'].pop(pip.curr_subject['index'])
                    #self.save_as_json()
                    self.write_log('Subject ' + element2remove['sub'] + ' has been removed from derivatives folder ' +
                                   pip['name'])
                    _, _, sub_idx = pip['ParticipantsProcessTSV'].is_subject_present(element2remove['sub'])
                    if sub_idx:
                        pip['ParticipantsProcessTSV'].pop(sub_idx)
                        pip['ParticipantsProcessTSV'].write_file(os.path.join(self.dirname, 'derivatives', in_deriv, ParticipantsProcessTSV.filename))
                        #self.save_as_json()
                        self.write_log('Subject ' + element2remove['sub'] + ' has been removed from derivatives folder ' +
                        pip['name'] + ' ' + self['ParticipantsProcessTSV'].filename + '.')
                if not isinstance(self, Pipeline):
                    self.save_as_json()
        elif isinstance(element2remove, ModalityType) and element2remove.classname() in Subject.keylist:
            self.is_subject_present(element2remove['sub'])
            if self.curr_subject['isPresent'] and \
                    element2remove in self.curr_subject['Subject'][element2remove.classname()]:
                elmt_idx = self.curr_subject['Subject'][element2remove.classname()].index(element2remove)
                dirname, fname, ext = element2remove.fileparts()
                comp_ext = ''
                if ext.lower() == '.gz':
                    comp_ext = ext
                    fname, ext = os.path.splitext(fname)
                if self['SourceData']:
                    # remove file in sourcedata folder and in source_data_trace.tsv
                    self['SourceData'][-1].is_subject_present(element2remove['sub'])
                    if self['SourceData'][-1].curr_subject['isPresent'] and self['SourceData'][-1]['SrcDataTrack']:
                        # you have to have the sourcedatatrack to be able to remove the source file otherwise no way to
                        # know the link between the raw and the source file
                        src_tsv = self['SourceData'][-1]['SrcDataTrack']
                        src_sub = self['SourceData'][-1].curr_subject['Subject']
                        orig_fname, _, idx2remove = src_tsv.get_source_from_raw_filename(element2remove['fileLoc'])
                        if orig_fname:

                            full_orig_name = os.path.join(SourceData.dirname, dirname, orig_fname)

                            # remove info of file in source trace table
                            if idx2remove:  # if source data is present in the source_trace
                                src_tsv.pop(idx2remove)
                                src_tsv.write_file()
                                self.write_log(element2remove['fileLoc'] + '(' + orig_fname +
                                               ') has been removed from Bids dataset ' +
                                               self['DatasetDescJSON']['Name'] + ' in ' + src_tsv.filename + '.')
                                self.save_as_json()

                            # remove file in sourcedata folder
                            idx = [src_sub[element2remove.classname()].index(modal)
                                   for modal in src_sub[element2remove.classname()]
                                   if modal['fileLoc'] == full_orig_name]
                            if idx:  # if source data is present

                                if os.path.isfile(os.path.join(self.dirname, full_orig_name)):
                                    # remove source file along with its sidecar files
                                    src_dir = os.path.join(self.dirname, SourceData.dirname, dirname)
                                    [os.remove(os.path.join(src_dir, file)) for file in os.listdir(src_dir)
                                     if os.path.splitext(file)[0] == os.path.splitext(orig_fname)[0]]
                                else:
                                    shutil.rmtree(os.path.join(self.dirname, full_orig_name))
                                src_sub[element2remove.classname()].pop(idx[0])
                                self.save_as_json()
                                self.write_log(element2remove['fileLoc'] + '(' + orig_fname +
                                               ') has been removed from Bids dataset ' +
                                               self['DatasetDescJSON']['Name'] + ' in source folder.')

                        else:
                            self.write_log(element2remove['fileLoc'] + ' has no source folder, it was probably manually'
                                                                       ' remove please refresh the bids dataset.')

                if self.curr_subject['Subject']['Scans']:
                    # remove the line contained in scans.tsv relative to this file
                    for elmt in self.curr_subject['Subject']['Scans']:
                        if elmt['ses'] == element2remove['ses']:
                            # strip the subject folder from the full filename
                            subrel_fname = os.path.join(element2remove.classname().lower(), fname + ext + comp_ext)
                            line = elmt['ScansTSV'].find_lines_which('filename', subrel_fname)
                            if line:
                                idx_line = elmt['ScansTSV'].index(line[0])
                                elmt['ScansTSV'].pop(idx_line)
                                tsv_fname, dname, ext = elmt.create_filename_from_attributes()
                                tsv_fullname = os.path.join(self.dirname, dname, tsv_fname + ext)
                                elmt['ScansTSV'].write_file(tsv_fullname)
                                break  # go out since there is only one scans.tsv containing this file

                # remove file in raw folder and its first level sidecar files (higher level may characterize
                # remaining files)
                sdcar_dict = element2remove.get_modality_sidecars()
                for sidecar_key in sdcar_dict:
                    if element2remove[sidecar_key]:
                        if element2remove[sidecar_key].modality_field:
                            sdcar_fname = fname.replace(element2remove['modality'],
                                                        element2remove[sidecar_key].modality_field)
                        else:
                            sdcar_fname = fname
                        if os.path.exists(os.path.join(BidsDataset.dirname, dirname,
                                                       sdcar_fname + element2remove[sidecar_key].extension)):
                            os.remove(os.path.join(BidsDataset.dirname, dirname, sdcar_fname +
                                                   element2remove[sidecar_key].extension))
                if with_issues:
                    self.issues.remove(element2remove)
                if isinstance(element2remove, Electrophy):
                    ext = self.converters['Electrophy']['ext']
                elif isinstance(element2remove, Imaging):
                    ext = self.converters['Imaging']['ext']
                ext.reverse()
                for ex in ext:
                    if os.path.exists(os.path.join(self.dirname, dirname, fname+ex+comp_ext)):
                        os.remove(os.path.join(self.dirname, dirname, fname+ex+comp_ext))
                self.curr_subject['Subject'][element2remove.classname()].pop(elmt_idx)
                self.write_log(element2remove['fileLoc'] +
                               ' and its sidecar files were removed from Bids dataset ' +
                               self['DatasetDescJSON']['Name'] + ' raw folder.')
                self.save_as_json()
        elif isinstance(element2remove, ModalityType) and element2remove.classname() in SubjectProcess.keylist:
            if in_deriv:
                self.is_pipeline_present(in_deriv)
                pip = self['Derivatives'][-1]['Pipeline'][self.curr_pipeline['index']]
                pip.is_subject_present(element2remove['sub'], flagProcess=True)
            else:
                for pip in self['Derivatives'][-1]['Pipeline']:
                    pip.is_subject_present(element2remove['sub'], flagProcess=True)
                    if pip.curr_subject['isPresent'] and element2remove in pip.curr_subject['SubjectProcess'][element2remove.classname()]:
                        break
            if pip.curr_subject['isPresent'] and element2remove in pip.curr_subject['SubjectProcess'][element2remove.classname()]:
                elmt_idx = pip.curr_subject['SubjectProcess'][element2remove.classname()].index(element2remove)
                dirname, fname, ext = element2remove.fileparts()
                #dirname = os.path.join(self.dirname, 'derivatives', pip['name'])
                comp_ext = ''
                if ext.lower() == '.gz':
                    comp_ext = ext
                    fname, ext = os.path.splitext(fname)
                if pip.curr_subject['SubjectProcess']['Scans']:
                    # remove the line contained in scans.tsv relative to this file
                    for elmt in pip.curr_subject['SubjectProcess']['Scans']:
                        if elmt['ses'] == element2remove['ses']:
                            # strip the subject folder from the full filename
                            mod_dir = element2remove.classname().split('Process')[0]
                            subrel_fname = os.path.join(mod_dir.lower(), fname + ext + comp_ext)
                            line = elmt['ScansTSV'].find_lines_which('filename', subrel_fname)
                            if line:
                                idx_line = elmt['ScansTSV'].index(line[0])
                                elmt['ScansTSV'].pop(idx_line)
                                tsv_fname, dname, ext = elmt.create_filename_from_attributes()
                                tsv_fullname = os.path.join(self.dirname, 'derivatives', pip['name'], dname, tsv_fname + ext)
                                elmt['ScansTSV'].write_file(tsv_fullname)
                                break  # go out since there is only one scans.tsv containing this file

                # remove file in raw folder and its first level sidecar files (higher level may characterize
                # remaining files)
                sdcar_dict = element2remove.get_modality_sidecars()
                for sidecar_key in sdcar_dict:
                    if element2remove[sidecar_key]:
                        if element2remove[sidecar_key].modality_field:
                            sdcar_fname = fname.replace(element2remove['modality'],
                                                        element2remove[sidecar_key].modality_field)
                        else:
                            sdcar_fname = fname
                        if os.path.exists(os.path.join(BidsDataset.dirname, dirname,
                                                       sdcar_fname + element2remove[sidecar_key].extension)):
                            os.remove(os.path.join(BidsDataset.dirname, dirname, sdcar_fname +
                                                   element2remove[sidecar_key].extension))
                if isinstance(element2remove, ElectrophyProcess):
                    ext = ElectrophyProcess.allowed_file_formats
                elif isinstance(element2remove, ImagingProcess):
                    ext = ImagingProcess.allowed_file_formats
                for ex in ext:
                    if os.path.exists(os.path.join(self.dirname, dirname, fname+ex+comp_ext)):
                        os.remove(os.path.join(self.dirname, dirname, fname+ex+comp_ext))
                pip.curr_subject['SubjectProcess'][element2remove.classname()].pop(elmt_idx)
                self.write_log(element2remove['fileLoc'] +
                               ' and its sidecar files were removed from derivative folder ' +
                               in_deriv + '.')
                self.save_as_json()
        elif isinstance(element2remove, GlobalSidecars):
            self.is_subject_present(element2remove['sub'])
            if self.curr_subject['isPresent'] and \
                    element2remove in self.curr_subject['Subject'][element2remove.classname()]:
                elmt_idx = self.curr_subject['Subject'][element2remove.classname()].index(element2remove)
                os.remove(os.path.join(self.dirname, element2remove['fileLoc']))
                if with_issues:
                    self.issues.remove(element2remove)
                self.curr_subject['Subject'][element2remove.classname()].pop(elmt_idx)
                self.write_log(element2remove['fileLoc'] +
                               ' and its sidecar files were removed from Bids dataset ' +
                               self['DatasetDescJSON']['Name'] + ' raw folder.')
                self.save_as_json()
        elif isinstance(element2remove, Pipeline):
            self.is_pipeline_present(element2remove['name'])
            if self.curr_pipeline['isPresent']:
                shutil.rmtree(os.path.join(self.dirname, 'derivatives', element2remove['name']), ignore_errors=True)
                self['Derivatives'][0]['Pipeline'].pop(self.curr_pipeline['index'])
                self.save_as_json()
                self.write_log(element2remove['name'] + ' has been removed from derivatives folder.')

    def save_as_json(self, savedir=None, file_start=None, write_date=True, compress=True):
        save_parsing_path = os.path.join(self.dirname, 'derivatives', 'parsing')
        if not os.path.exists(save_parsing_path):
            os.makedirs(save_parsing_path)
        super().save_as_json(savedir=save_parsing_path, file_start='parsing', write_date=True, compress=True)
        self.issues.save_as_json()

    def apply_actions(self):

        def modify_electrodes_files(ch_issue):
            def change_electrode(**kwargs):  # appears unused because it is called from eval()
                type_bln = False
                name_bln = False
                if 'type' in kwargs.keys():  # have to change the electrode type
                    type_bln = True
                    input_key = 'type'
                if 'name' in kwargs.keys():  # have to change the electrode name
                    name_bln = True
                    input_key = 'name'
                if type_bln ^ name_bln:
                    #  XOR only one of them is true, cannot change both type and name!
                    dirname, mod_fname, ext=modality.fileparts()
                    sidecar = modality.get_modality_sidecars(BidsTSV)
                    # /!\ first change the name in .vhdr and .vmrk because those are ot read during check requirements!
                    if name_bln:
                        hdr = bv_hdr.BrainvisionHeader(os.path.join(self.dirname, dirname, mod_fname + ext))
                        hdr.modify_header(action['name'], kwargs['name'])
                        hdr.write_header()
                    for key in sidecar:
                        if isinstance(sidecar[key], IeegChannelsTSV) and 'group' not in sidecar[key].header:
                            sidecar[key].header.append('group')
                            idx_elec_name = sidecar[key].header.index('name')
                            for line in sidecar[key][1:]:
                                str_group = [c for c in line[idx_elec_name] if not c.isdigit()]
                                grp_name = ''.join(str_group)
                                line.append(grp_name)
                        if type_bln and all(wrd in sidecar[key].header for wrd in ['type', 'group']):
                            idx_group = sidecar[key].header.index('group')
                            idx_type = sidecar[key].header.index('type')
                            """ replace current type by the new one for all channels from same electrode"""
                            for line in sidecar[key][1:]:
                                if line[idx_group] == action['name']:
                                    line[idx_type] = kwargs['type']
                            act_str = 'Change electrode type of ' + action['name'] + ' to ' + kwargs['type'] + \
                                      ' in the ' + mod_fname + sidecar[key].extension + '.'
                        elif name_bln and all(wrd in sidecar[key].header for wrd in ['name', 'group']):
                            idx_group = sidecar[key].header.index('group')
                            idx_name = sidecar[key].header.index('name')
                            """ replace current group by the new one for all channel from same electrode and rename 
                            the channel accordingly"""
                            for line in sidecar[key][1:]:
                                if line[idx_group] == action['name']:
                                    # need replace here to keep the number of the channel
                                    line[idx_name] = line[idx_name].replace(line[idx_group], kwargs['name'])
                                    line[idx_group] = kwargs['name']
                            act_str = 'Change electrode name from ' + action['name'] + ' to ' + kwargs['name'] + \
                                      ' in the ' + mod_fname + sidecar[key].extension + '.'
                        else:
                            continue
                        fname2bewritten = os.path.join(BidsDataset.dirname, dirname,
                                                       mod_fname.replace(modality['modality'],
                                                                         sidecar[key].modality_field)
                                                       + sidecar[key].extension)
                        sidecar[key].write_file(fname2bewritten)
                        # remove the mismatched electrode from the list, when empty the issue will be popped
                        [curr_iss_cpy['MismatchedElectrodes'].pop(curr_iss_cpy['MismatchedElectrodes'].index(mm_elec))
                         for mm_elec in ch_issue['MismatchedElectrodes'] if mm_elec['name'] == action['name']]
                        curr_iss_cpy['Action'].pop(curr_iss_cpy['Action'].index(action))
                        # modality[key] = []
                        # modality[key].copy_values(sidecar[key])  # sidecar is not in self but a copy
                        self.save_as_json()
                        modality.write_log(act_str)
                else:
                    err_str = 'One cannot modify the name and the type of the electrode at the same time'
                    ch_issue.write_log(err_str)

            modality = self.get_object_from_filename(ch_issue['fileLoc'])
            if not modality:  # no need to update the log since get_object_from_filename does it
                return
            for action in ch_issue['Action']:
                eval('change_electrode(' + action['command'] + ')')
                pass

        def modify_files(**kwargs):

            elmt_iss = issue.get_element()
            if 'remove_issue' in kwargs and kwargs['remove_issue']:
                # nothing else to do since the issue will be popped anyway ^_^ (except for UploaderIssues)
                if isinstance(issue, ImportIssue):
                    str_rmv = issue['description']
                else:
                    str_rmv = os.path.basename(elmt_iss['fileLoc'])
                self.write_log('Issue concerning "' + str_rmv + '" has been removed.')
                return
            if 'state' in kwargs and kwargs['state'] and isinstance(issue, UpldFldrIssue):
                # simple command to modify the state
                curr_iss = issues_copy['UpldFldrIssue'][issues_copy['UpldFldrIssue'].index(issue)]
                curr_iss['state'] = kwargs['state']
                curr_iss['Action'] = []
                self.write_log('State of file ' + elmt_iss['fileLoc'] + ' has been set to ' + curr_iss['state'] + '.')
                return
            if 'in_bids' in kwargs:
                if kwargs['in_bids'] == 'True' or kwargs['in_bids'] is True:
                    kwargs['in_bids'] = True
                    curr_brick = self
                    loc_str = ' in bids dir. ' + self.dirname + '.'
                else:
                    kwargs['in_bids'] = False
                    curr_brick = Data2Import(issue['path'])
                    curr_brick.save_as_json(write_date=True)
                    loc_str = ' in import dir. ' + issue['path'] + '.'
            else:
                err_str = 'No information about whether the change has to be made in bids or import directory.'
                self.write_log(err_str)
                return
            if 'pop' in kwargs and kwargs['pop'] and not kwargs['in_bids']:
                # if pop = True => not to import this element
                if isinstance(elmt_iss, (ModalityType, GlobalSidecars)):
                    idx = None
                    curr_brick.is_subject_present(elmt_iss['sub'])
                    curr_sub = curr_brick.curr_subject['Subject']
                    if 'in_deriv' in kwargs:
                        curr_brick.is_pipeline_present(kwargs['in_deriv'])
                        curr_pip = curr_brick['Derivatives'][-1]['Pipeline'][curr_brick.curr_pipeline['index']]
                        curr_pip.is_subject_present(elmt_iss['sub'], flagProcess=True)
                        curr_sub = curr_pip.curr_subject['SubjectProcess']
                    for elmt in curr_sub[elmt_iss.classname()]:
                        if elmt.get_attributes('fileLoc') == elmt_iss.get_attributes('fileLoc') and \
                                elmt['fileLoc'] == os.path.basename(elmt_iss['fileLoc']):
                            # remember that is issues the fileLoc are absolute path, therefore one has to tests the
                            # basename
                            idx = curr_sub[elmt_iss.classname()].index(elmt)
                            break
                    curr_sub[elmt_iss.classname()].pop(idx)
                    self.write_log('Element ' + elmt_iss['fileLoc'] + ' has been removed from the data to import'
                                   + loc_str + '.')
            elif isinstance(elmt_iss, DatasetDescJSON):
                if 'in_deriv' in kwargs:
                    curr_brick.is_pipeline_present(kwargs['in_deriv'])
                    curr_data = curr_brick['Derivatives'][-1]['Pipeline'][curr_brick.curr_pipeline['index']]
                    jsonfilename = os.path.join(BidsDataset.dirname, 'derivatives', kwargs['in_deriv'], DatasetDescJSON.filename)
                    loc_str += ' in deriv dir. ' + kwargs['in_deriv']
                    for key in kwargs:
                        if key in curr_data['DatasetDescJSON']:
                            curr_data['DatasetDescJSON'][key] = kwargs[key]
                    if kwargs['in_bids']:
                        # special case here since need also write the change in bids directory
                        curr_data['DatasetDescJSON'].write_file(jsonfilename)
                else:
                    for key in kwargs:
                        if key in curr_brick['DatasetDescJSON']:
                            curr_brick['DatasetDescJSON'][key] = kwargs[key]
                    if kwargs['in_bids']:
                        # special case here since need also write the change in bids directory
                        curr_brick['DatasetDescJSON'].write_file()
                self.write_log('Modification of ' + DatasetDescJSON.filename + loc_str)
            elif isinstance(elmt_iss, Subject):
                curr_brick.is_subject_present(elmt_iss['sub'])
                curr_sub = curr_brick.curr_subject['Subject']
                for key in kwargs:
                    if key in curr_sub and key not in BidsBrick.get_list_subclasses_names() and not key == 'sub':
                        curr_sub[key] = kwargs[key]
                if kwargs['in_bids']:
                    # special case here since need also to update the participants.tsv
                    _, sub_info, idx = curr_brick['ParticipantsTSV'].is_subject_present(curr_sub['sub'])
                    curr_brick['ParticipantsTSV'].pop(idx)
                    sub_info.update({key: kwargs[key] for key in sub_info if key in kwargs})
                    sub_info['participant_id'] = sub_info['sub']
                    curr_brick['ParticipantsTSV'].append(sub_info)
                    curr_brick['ParticipantsTSV'].write_file()
                self.write_log('Modification of for ' + curr_sub['sub'] + loc_str)
            elif isinstance(elmt_iss, (ModalityType, GlobalSidecars)):
                if 'remove' in kwargs and kwargs['in_bids']:
                    mod_brick = curr_brick.get_object_from_filename(kwargs['remove'])
                    if 'in_deriv' in kwargs and kwargs['in_deriv']:
                        deriv_folder = kwargs['in_deriv']
                    else:
                        deriv_folder = None
                    # check if element had other issues (ieeg file could have electrode issues)
                    #  to be checked before removing file because of the fileLoc safety (cf BidsBrick __setitem__)
                    issues_copy.remove(mod_brick)
                    # put with_issues=False because if affects self.issues and not the copy where the other issues are
                    # popped out
                    curr_brick.remove(mod_brick, with_issues=False, in_deriv=deriv_folder)
                elif not kwargs['in_bids']:
                    if 'in_deriv' in kwargs:
                        curr_brick.is_pipeline_present(kwargs['in_deriv'])
                        curr_pip = curr_brick['Derivatives'][-1]['Pipeline'][curr_brick.curr_pipeline['index']]
                        curr_pip.is_subject_present(elmt_iss['sub'], flagProcess=True)
                        curr_sub = curr_pip.curr_subject['SubjectProcess']
                        loc_str += ' in deriv dir. ' + kwargs['in_deriv']
                    else:
                        curr_brick.is_subject_present(elmt_iss['sub'])
                        curr_sub = curr_brick.curr_subject['Subject']
                    idx = None
                    for elmt in curr_sub[elmt_iss.classname()]:
                        if elmt.get_attributes('fileLoc') == elmt_iss.get_attributes('fileLoc') and \
                                elmt['fileLoc'] == os.path.basename(elmt_iss['fileLoc']):
                            idx = curr_sub[elmt_iss.classname()].index(elmt)
                            break
                    elmt = curr_sub[elmt_iss.classname()][idx]
                    for key in kwargs:
                        if key in elmt and key not in ['sub', 'fileLoc']:
                            if isinstance(kwargs[key], str):
                                if kwargs[key].isdigit:
                                    val = kwargs[key].zfill(2)
                                else:
                                    val = kwargs[key]
                            else:
                                val = str(kwargs[key]).zfill(2)
                            elmt[key] = val
                    self.write_log('Modification of ' + elmt['fileLoc'] + ' has been done' + loc_str)
            if isinstance(issue, UpldFldrIssue):
                if 'pop' in kwargs:
                    # UpldFldrIssue are normally not popped, thus need to add this line
                    issues_copy['UpldFldrIssue'].pop(issues_copy['UpldFldrIssue'].index(issue))
                else:
                    curr_iss = issues_copy['UpldFldrIssue'][issues_copy['UpldFldrIssue'].index(issue)]
                    curr_iss['Action'] = []
            curr_brick.save_as_json()

        BidsBrick.access_time = datetime.now()
        self.clear_log()
        self._assign_bids_dir(self.dirname)
        # self.write_log('Current User: ' + self.curr_user + '\n' + BidsBrick.access_time.strftime("%Y-%m-%dT%H:%M:%S"))
        issues_copy = Issue()
        issues_copy.copy_values(self.issues)  # again have to copy to pop while looping
        file_removal = False
        try:
            self.write_log(10 * '=' + '\nApplying actions\n' + 10 * '=')
            # could optimize/make nicer
            # the order is important because you could remove a file and than its relative ElectrodeIssue
            for issue in self.issues['ElectrodeIssue']:
                if not issue['Action']:
                    continue
                curr_iss_cpy = issues_copy['ElectrodeIssue'][issues_copy['ElectrodeIssue'].index(issue)]
                modify_electrodes_files(issue)
                if not curr_iss_cpy['MismatchedElectrodes']:
                    # only remove the issue if no more mismatched electrodes (so it keeps comment from the remaining
                    # electrodes)
                    # have to empty these since this was modified in the copied versions
                    issue['MismatchedElectrodes'] = []
                    issue['Action'] = []
                    issues_copy['ElectrodeIssue'].pop(issues_copy['ElectrodeIssue'].index(issue))
                issues_copy.save_as_json()
            for issue in self.issues['ImportIssue']:
                if not issue['Action']:
                    continue
                eval('modify_files(' + issue['Action'][0]['command'] + ')')
                if 'remove' in issue['Action'][0]['command']:
                    file_removal = True
                issues_copy['ImportIssue'].pop(issues_copy['ImportIssue'].index(issue))
                issues_copy.save_as_json()
            for issue in self.issues['UpldFldrIssue']:
                if not issue['Action']:
                    continue
                eval('modify_files(' + issue['Action'][0]['command'] + ')')
                if 'remove_issue=True' in issue['Action'][0]['command']:
                    issues_copy['UpldFldrIssue'].pop(issues_copy['UpldFldrIssue'].index(issue))
                # here issues are not popped out because in import_data() they are checked to make sure files were
                # verified
                issues_copy.save_as_json()
        except Exception as ex:
            exc_type, exc_obj, exc_tb = exc_info()
            err_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.write_log('Error type: ' + str(exc_type) + ', scriptname: ' + err_name + ', line number, ' + str(
                exc_tb.tb_lineno) + ': ' + str(ex))
            #self.write_log(str(ex))
        if issues_copy['ElectrodeIssue'] == self.issues['ElectrodeIssue'] and not file_removal:
            elec_iss_bln = False
        else:
            elec_iss_bln = True
        self._assign_bids_dir(self.dirname)  # because of the data2import the cwdir could change
        self.issues = Issue()
        self.issues.copy_values(issues_copy)
        if elec_iss_bln:  # only check requirement if actions were made for ElectrodeIssues
            self.check_requirements()

    def make_upload_issues(self, data2import, force_verif=False):
        """ each time a data2import is instantiated, one has to create upload issues to force the user to verify that
        the files have the correct attributes. """
        if not isinstance(data2import, Data2Import):
            self.write_log('Current method takes instance of Data2Import.')
            return
        if force_verif is True:
            state = 'verified'
        else:
            state = 'not verified'
        self._assign_bids_dir(self.dirname)
        list_upld = [os.path.normpath(elt['fileLoc']) for elt in self.issues['UpldFldrIssue']]
        for sub in data2import['Subject']:
            for key in sub:
                if key in ModalityType.get_list_subclasses_names() + GlobalSidecars.get_list_subclasses_names():
                    for mod_brick in sub[key]:
                        if os.path.normpath(os.path.join(data2import.dirname, mod_brick['fileLoc'])) not in list_upld:
                            self.issues.add_issue('UpldFldrIssue', fileLoc=mod_brick['fileLoc'],
                                              sub=mod_brick['sub'], path=data2import.dirname,
                                              state=state)
                        else:
                            idx = list_upld.index(os.path.normpath(os.path.join(data2import.dirname, mod_brick['fileLoc'])))
                            self.issues['UpldFldrIssue'][idx]['Action'] = []
                            self.issues['UpldFldrIssue'][idx]['state'] = state
        for dev in data2import['Derivatives']:
            for pip in dev['Pipeline']:
                for sub in pip['SubjectProcess']:
                    for key in sub:
                        if key in Process.get_list_subclasses_names():
                            for mod_brick in sub[key]:
                                if os.path.normpath(os.path.join(data2import.dirname, mod_brick['fileLoc'])) not in list_upld:
                                    self.issues.add_issue('UpldFldrIssue', fileLoc=mod_brick['fileLoc'],
                                                      sub=mod_brick['sub'], path=data2import.dirname,
                                                      state=state)
                                else:
                                    idx = list_upld.index(os.path.normpath(os.path.join(data2import.dirname, mod_brick['fileLoc'])))
                                    self.issues['UpldFldrIssue'][idx]['Action'] = []

    def verif_upload_issues(self, import_dir):
        return self.issues.verif_upload_issues(import_dir)

    def make_func_pipeline(self):
        """ initiate the log and parsing pipelines which are the ones create for ins_bids_class functioning """
        if 'Derivatives' in self.keylist:
            functionning_pip = {'log': 'Folder containing all log and issue files created by ins_bids_class. '
                                       'access.json stores the current user and the time of login.',
                                'parsing': 'Folder containing all the parsing.json files which store the current status'
                                           ' of the bids dataset including all the sidecar files and participants.tsv'}
            for k in functionning_pip.keys():
                self.is_pipeline_present(k)
                dname = os.path.join(BidsDataset.dirname, 'derivatives', k)
                if not self.curr_pipeline['isPresent']:
                    new_pip = Pipeline()
                    new_pip['name'] = k
                    if not self['Derivatives']:
                        self['Derivatives'] = Derivatives()
                    self['Derivatives'][0]['Pipeline'] = new_pip
                    self.is_pipeline_present(k)
                    if not os.path.exists(dname):
                        os.makedirs(dname)

                if not os.path.exists(os.path.join(dname, DatasetDescJSON.filename)):
                    new_pip = self.curr_pipeline['Pipeline']
                    new_pip['DatasetDescJSON'] = DatasetDescJSON()
                    new_pip['DatasetDescJSON'].update({'Name': k, 'Description': functionning_pip[k]})
                    new_pip['DatasetDescJSON'].write_file(os.path.join(dname, DatasetDescJSON.filename))
                    self.save_as_json()

    @classmethod
    def _assign_bids_dir(cls, bids_dir):
        cls.dirname = bids_dir
        BidsBrick.cwdir = bids_dir


''' Concurrent access object '''


class Access(BidsJSON):
    keylist = ['user', 'access_time']

    def __init__(self):
        super().__init__()
        self.filename = os.path.join(BidsDataset.dirname, BidsDataset.log_path, 'access.json')

    def display(self):
        return 'This Bids dataset (' + BidsDataset.dirname + ') is in use by ' + self['user'] + ' since ' + \
               self['access_time'] + '.'

    def read_file(self, filename=None):
        super().read_file(self.filename)

    def write_file(self, jsonfilename=None):
        super().write_file(self.filename)

    def delete_file(self):
        if os.path.isfile(self.filename):
            os.remove(self.filename)


''' Additional class to handle issues and relative actions '''


class RefElectrodes(BidsFreeFile):
    pass


class MismatchedElectrodes(BidsBrick):
    keylist = ['name', 'type']
    required_keys = keylist


class Comment(BidsBrick):
    keylist = ['name', 'date', 'user', 'description']

    def __init__(self, new_keys=None):
        if not new_keys:
            new_keys = []
        if isinstance(new_keys, str):
            new_keys = [new_keys]
        if isinstance(new_keys, list):
            self.keylist = new_keys + self.keylist
            super().__init__(keylist=self.keylist)
            self['user'] = self.curr_user
            self['date'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        else:
            error_str = 'The new keys of ' + self.classname() + ' should be either a list of a string.'
            self.write_log(error_str)
            raise TypeError(error_str)

    def formatting(self):
        return '==> ' + self.classname() + ' by ' + self['user'] + ' at ' + self['date'] + ':\n'\
               + self['description']


class Action(Comment):
    keylist = Comment.keylist + ['command']


class IssueType(BidsBrick):

    def add_comment(self,  desc, elec_name=None):

        """verify that the given electrode name is part of the mismatched electrodes"""
        if isinstance(self, ElectrodeIssue) and elec_name not in self.list_mismatched_electrodes():
            print(elec_name + ' does not belong to the current mismatched electrode.')
            return

        comment = Comment()
        if elec_name:  # add comment about a given mismatched electrodes
            comment['name'] = elec_name
        comment['description'] = desc
        self['Comment'] = comment

    def get_element(self):
        if isinstance(self, ImportIssue):
            """get_element returns the brick which produced this issue. Since there is only one brick per ImportIssue,
            one can break the for loop when found"""
            for key in ImportIssue.keylist:
                if key == 'DatasetDescJSON' and self[key]:
                    return self[key]
                elif key in ModalityType.get_list_subclasses_names() + GlobalSidecars.get_list_subclasses_names() \
                        + ['Subject', 'SubjectProcess'] and self[key]: #A verifier
                    return self[key][0]
        elif isinstance(self, UpldFldrIssue):
            tmp_data2import = Data2Import(self['path'])
            return tmp_data2import.get_object_from_filename(self['fileLoc'])
        return

    def formatting(self, comment_type=None, elec_name=None):
        if comment_type and (not isinstance(comment_type, str) or
                             comment_type.capitalize() not in Comment.get_list_subclasses_names() + ['Comment']):
            raise KeyError(comment_type + ' is not a recognized key of ' + self.classname() + '.')
        if not comment_type:
            comment_type = Comment.get_list_subclasses_names() + ['Comment']
        else:
            comment_type = [comment_type.capitalize()]
        formatted_list = []
        for cmnt_type in comment_type:
            for cmnt in self[cmnt_type]:
                if isinstance(self, ElectrodeIssue):
                    if elec_name and not cmnt['name'] == elec_name:
                        continue
                formatted_list.append(cmnt.formatting())
        return formatted_list

    def add_action(self, desc, command, elec_name=None):
        action = Action()
        if isinstance(self, ElectrodeIssue):
            """verify that the given electrode name is part of the mismatched electrodes"""
            if elec_name not in self.list_mismatched_electrodes():
                return
            """check whether a mismatched electrode already has an action. Only one action per electrode is permitted"""
            idx2pop = None
            for act in self['Action']:
                if act['name'] == elec_name:
                    idx2pop = self['Action'].index(act)
                    break
            if idx2pop is not None:
                self['Action'].pop(idx2pop)
            """ add action for given mismatched electrodes """
            action['name'] = elec_name
        else:
            """ImportIssue and UpldFldrIssue have only one issue per instance (different from channelIssue that can have
             as many actions as there are mismatched channels)"""
            if self['Action']:
                self['Action'].pop(0)
        """ add action for given mismatched electrodes """
        action['description'] = desc
        action['command'] = command
        self['Action'] = action


class UpldFldrIssue(IssueType):
    keylist = BidsBrick.keylist + ['path', 'state', 'fileLoc', 'Comment', 'Action']
    required_keys = BidsBrick.keylist + ['path', 'state', 'fileLoc']


class ElectrodeIssue(IssueType):
    keylist = BidsBrick.keylist + ['mod', 'RefElectrodes', 'MismatchedElectrodes', 'fileLoc', 'Comment', 'Action']
    required_keys = BidsBrick.keylist + ['RefElectrodes', 'MismatchedElectrodes', 'fileLoc']

    def list_mismatched_electrodes(self):
        return [miselec['name'] for miselec in self['MismatchedElectrodes']]


class ImportIssue(IssueType):
    """instance of ImportIssue allows storing information, comments and actions about issues encounter during
    importation. 'Subject' corresponds to a list of Subject(), the first one to be imported and the second to the
    current subject in the dataset and give info about subject related issue. Same for the modality keys."""
    keylist = ['DatasetDescJSON', 'Subject'] + \
              [key for key in Subject.keylist if key in ModalityType.get_list_subclasses_names()
               + GlobalSidecars.get_list_subclasses_names()] + ['SubjectProcess'] + \
              [key for key in SubjectProcess.keylist if key.endswith('Process')] + \
              ['description', 'path', 'Comment', 'Action']


class Issue(BidsBrick):
    keylist = ['UpldFldrIssue', 'ImportIssue', 'ElectrodeIssue']

    def check_with_latest_issue(self):
        """ This method verified in the lastest issue.json if there are issues corresponding to the current Issue().
        If so, it loads previous Comments and Actions and State (for the upload issues) of the related issue."""
        def read_file(filename):
            with open(filename, 'r') as file:
                rd_json = json.load(file)
            return rd_json

        log_dir = os.path.join(BidsDataset.dirname, BidsDataset.log_path)
        if BidsDataset.dirname and os.path.isdir(log_dir):
            latest_issue = latest_file(log_dir, self.classname().lower())
            if latest_issue:
                # find the latest issue.json file
                read_json = read_file(latest_issue)

                # remove all import dir that were removed, it will raise an error in the fileLoc test otherwise
                # to avoid error read json as normal dict and then copy_value in the correct bids object
                cpy_read_json = read_file(latest_issue)
                for issue_key in cpy_read_json.keys():
                    issue_list = [issue for issue in read_json[issue_key]]
                    for issue in issue_list:
                        iss_test = getattr(modules[__name__], issue_key)()
                        try:
                            iss_test.copy_values(issue)
                        except FileNotFoundError:  # is the only error that could occur
                            self.write_log('Related ' + issue_key + ' issues are removed')
                            read_json[issue_key].pop(read_json[issue_key].index(issue))

                if self == Issue():
                    self.copy_values(read_json)
                    if not read_json == cpy_read_json:
                        self.save_as_json()
                else:
                    prev_issues = Issue()
                    prev_issues.copy_values(read_json)

                    for issue_key in self.keys():
                        for issue in self[issue_key]:
                            """ find in the previous issue.json the comment and action concerning the same file; 
                            add_comment() and add_action() take care of the electrode matching."""
                            idx = None
                            for cnt, prev_iss in enumerate(prev_issues[issue_key]):
                                if prev_iss.get_attributes() == issue.get_attributes():
                                    idx = cnt
                                    break
                            # could pop prev_iss from prev_issues to make it fasted
                            comment_list = prev_issues[issue_key][idx]['Comment']
                            action_list = prev_issues[issue_key][idx]['Action']
                            for comment in comment_list:
                                issue.add_comment(comment['name'], comment['description'])
                            for action in action_list:
                                if issue_key == 'ElectrodeIssue':
                                    issue.add_action(action['name'], action['description'], action['command'])
                                else:
                                    issue.add_action(action['description'], action['command'])

    def save_as_json(self, savedir=None, file_start=None, write_date=True, compress=True):

        log_path = os.path.join(BidsDataset.dirname, 'derivatives', 'log')
        super().save_as_json(savedir=log_path, file_start=None, write_date=True, compress=False)

    def formatting(self, specific_issue=None, comment_type=None, elec_name=None):
        if specific_issue and specific_issue not in self.keys():
            raise KeyError(specific_issue + ' is not a recognized key of ' + self.classname() + '.')
        if comment_type and (not isinstance(comment_type, str) or
                             comment_type.capitalize() not in Comment.get_list_subclasses_names() + ['Comment']):
            raise KeyError(comment_type + ' is not a reckognized key of ' + self.classname() + '.')
        formatted_list = []
        if specific_issue:
            key2check = [specific_issue]
        else:
            key2check = self.keylist
        for key in key2check:
            for issue in self[key]:
                formatted_list += issue.formatting(comment_type=comment_type, elec_name=elec_name)

        return formatted_list

    def add_issue(self, issue_type, **kwargs):
        # key used by kwarg:
        # ['sub', 'mod', 'RefElectrodes', 'MismatchedElectrodes', 'fileLoc', 'brick', 'description']
        if issue_type == 'ElectrodeIssue':
            issue = ElectrodeIssue()
            for key in kwargs:
                if key in issue.keylist:
                    if key == 'MismatchedElectrodes':
                        if isinstance(kwargs[key], list):
                            for elmt in kwargs[key]:
                                melec = MismatchedElectrodes()
                                melec.copy_values(elmt)
                                issue[key] = melec
                        else:
                            issue[key] = kwargs[key]
                    else:
                        issue[key] = kwargs[key]
        elif issue_type == 'ImportIssue' and kwargs['brick']:
            issue = ImportIssue()
            issue['path'] = Data2Import.dirname
            if kwargs['brick']:
                if isinstance(kwargs['brick'], DatasetDescJSON):
                    brick_imp_shrt = kwargs['brick']
                elif isinstance(kwargs['brick'], (ModalityType, GlobalSidecars)):
                    fname = os.path.join(Data2Import.dirname, kwargs['brick']['fileLoc'])
                    if isinstance(kwargs['brick'], ModalityType):
                        brick_imp_shrt = kwargs['brick'].__class__()
                    elif isinstance(kwargs['brick'], GlobalSidecars):
                        brick_imp_shrt = kwargs['brick'].__class__(fname)
                    brick_imp_shrt.update(kwargs['brick'].get_attributes('fileLoc'))
                    brick_imp_shrt['fileLoc'] = os.path.join(fname)
                elif isinstance(kwargs['brick'], Subject) or isinstance(kwargs['brick'], SubjectProcess):
                    brick_imp_shrt = kwargs['brick'].__class__()
                    brick_imp_shrt.update(kwargs['brick'].get_attributes())
                issue[kwargs['brick'].classname()] = brick_imp_shrt
            if kwargs['description'] and isinstance(kwargs['description'], str):
                issue['description'] = kwargs['description']
        elif issue_type == 'UpldFldrIssue':
            issue = UpldFldrIssue()
            if 'fileLoc' in kwargs.keys() and 'path' in kwargs.keys():
                kwargs['fileLoc'] = os.path.join(kwargs['path'], kwargs['fileLoc'])
            for key in kwargs:
                if key in issue.keylist:
                    issue[key] = kwargs[key]
        else:
            return

        # check if the same issue is already in the Issue brick by testing all the keys except Comment, Action and State
        for prev_issue in self[issue_type]:
            if all(prev_issue[key] == issue[key] for key in prev_issue if key not in ['Comment', 'Action', 'state']):
                return

        # before adding the issue test whether it has all needed attributes
        flag, missing_str = issue.has_all_req_attributes()
        if not flag:
            raise AttributeError(missing_str)

        self[issue_type] = issue
        self.save_as_json()

    def remove(self, brick2remove):
        new_issue = self.__class__()
        new_issue.copy_values(self)
        # need a copy because we cannot loop over a list and pop its content at the same time
        for key in self:
            if isinstance(brick2remove, Subject):
                if key == 'ElectrodeIssue':
                    for issue in self[key]:
                        if issue['sub'] == brick2remove['sub']:
                            new_issue[key].pop(new_issue[key].index(issue))
                elif key == 'ImportIssue':
                    for issue in self[key]:
                        for k in issue:
                            if k in BidsBrick.get_list_subclasses_names() and issue[k] and \
                                    issue[k][0]['sub'] == brick2remove['sub']:
                                new_issue[key].pop(new_issue[key].index(issue))
                                break  # only one element is not empty, break when found
            elif isinstance(brick2remove, (ModalityType, GlobalSidecars)):
                if key == 'ImportIssue':
                    for issue in self[key]:
                        if issue[brick2remove.classname()] and \
                                brick2remove['fileLoc'] in issue[brick2remove.classname()][0]['fileLoc']:
                                #issue[brick2remove.classname()][0]['fileLoc'] == brick2remove['fileLoc']:
                            new_issue[key].pop(new_issue[key].index(issue))
                            break
                else:
                    for issue in self[key]:
                        if brick2remove['fileLoc'] in issue['fileLoc']:#os.path.basename(issue['fileLoc']) == os.path.basename(brick2remove['fileLoc']):
                            new_issue[key].pop(new_issue[key].index(issue))
                            break
            # elif not key == 'ElectrodeIssue' and (isinstance(brick2remove, Imaging) or
            #                                       isinstance(brick2remove, GlobalSidecars)):
            #     for issue in self[key]:
            #         if issue[brick2remove.classname()] and \
            #                 issue[brick2remove.classname()][0]['fileLoc'] == brick2remove['fileLoc']:
            #             new_issue[key].pop(new_issue[key].index(issue))
            #             break

        self.clear()
        self.copy_values(new_issue)

    def verif_upload_issues(self, import_dir):
        state_list = [up_iss['state'] == 'verified' for up_iss in self['UpldFldrIssue'] if os.path.normpath(up_iss['path']) == os.path.normpath(import_dir)]
        if state_list:
            return all(state_list)
        else:  # all([]) => True; means that if verif issue was removed than you can import it, not the wanted behaviour
            return False

    @staticmethod
    def empty_dict():
        keylist = ['sub', 'mod', 'RefElectrodes', 'MismatchedElectrodes', 'fileLoc', 'brick', 'description']
        return {key: None for key in keylist}


''' Additional class to handle pipelines and relative actions '''


class Pipeline(BidsDataset):

    keylist = ['SubjectProcess', 'name', 'DatasetDescJSON', 'ParticipantsProcessTSV']
    curr_name = None
    list_ext = ['.nii', '.vhdr', '.txt']

    def __init__(self, name=None):
        self.requirements = BidsDataset.requirements
        self.parsing_path = BidsDataset.parsing_path
        self.log_path = BidsDataset.log_path
        self.curr_subject = {'SubjectProcess': SubjectProcess(), 'isPresent': False, 'index': None}

        for key in self.keylist:
            if key in BidsBrick.get_list_subclasses_names() or key in BidsTSV.get_list_subclasses_names():
                self[key] = []
            elif key in BidsJSON.get_list_subclasses_names():
                self[key] = {}
            else:
                self[key] = ''

        if name:
            self['name'] = name
            self['DatasetDescJSON'] = DatasetDescJSON()
            self['ParticipantsProcessTSV'] = ParticipantsProcessTSV()
            dataset_dir = os.path.join(BidsDataset.dirname, 'derivatives', name, DatasetDescJSON.filename)
            if os.path.exists(dataset_dir):
                self['DatasetDescJSON'].read_file(jsonfilename=dataset_dir)
            else:
                self['DatasetDescJSON']['Name'] = name
                self['DatasetDescJSON'].write_file(jsonfilename=dataset_dir)
            participants_dir = os.path.join(BidsDataset.dirname, 'derivatives', name, ParticipantsTSV.filename)
            if os.path.exists(participants_dir):
                self['ParticipantsProcessTSV'].read_file(tsv_full_filename=participants_dir)
            # else:
            #     self['ParticipantsTSV'].header = ['participant_id']
            #     self['ParticipantsTSV'].required_fields = ['participant_id']
            #     self['ParticipantsTSV'][:] = []
            #     self['ParticipantsTSV'].write_file(tsv_full_filename=participants_dir)

    # def parse_filename_dervivatives(self, mod_dict, file):
    #     fname_pieces = file.split('_')
    #     for word in fname_pieces:
    #         w = word.split('-')
    #         if len(w) == 2 and w[0] in mod_dict.keys():
    #             mod_dict[w[0]] = w[1]
    #     if 'modality' in mod_dict and not mod_dict['modality']:
    #         mod_dict['modality'] = fname_pieces[-1]
    #     return mod_dict
    #
    # def get_attributes_from_BidsSource(self, index_sub, bids_dir_source, subject_id):
    #     sub_list = bids_dir_source.get_subject_list()
    #     for sub in sub_list:
    #         if sub == subject_id:
    #             index_source = sub_list.index(sub)
    #             self['SubjectProcess'][index_sub]['age'] = bids_dir_source['Subject'][index_source]['age']
    #             self['SubjectProcess'][index_sub]['sex'] = bids_dir_source['Subject'][index_source]['sex']

    def add_subject(self, sub):
        if not self['SubjectProcess']:
            self['SubjectProcess'] = SubjectProcess()
            self['SubjectProcess'][-1].update(sub.get_attributes())
        else:
            self['SubjectProcess'].append(SubjectProcess())
            self['SubjectProcess'][-1].update(sub.get_attributes())
        if not self['ParticipantsProcessTSV']:
            self['ParticipantsProcessTSV'] = ParticipantsTSV()
            self['ParticipantsProcessTSV'].header = ['participant_id']
            self['ParticipantsProcessTSV'][:] = []
        part_present, part_info, part_index = self['ParticipantsProcessTSV'].is_subject_present(sub['sub'])
        if not part_present:
            self['ParticipantsProcessTSV'].add_subject(sub)

    def update_bids_original(self, bids_origin, modality):
        pip = bids_origin.curr_pipeline['Pipeline']
        mod_type = modality.classname()
        sub = self.curr_subject['SubjectProcess']
        sublist = {sub['sub']: pip['SubjectProcess'].index(sub) for sub in pip['SubjectProcess']}
        if sub['sub'] in sublist.keys():
            for mod in sub[mod_type]:
                is_in = False
                tmp_attr = mod.get_attributes('fileLoc')
                for elt in pip['SubjectProcess'][sublist[sub['sub']]][mod_type]:
                    tmp_elt = elt.get_attributes('fileLoc')
                    if tmp_elt == tmp_attr:
                        elt.update(mod)
                        is_in = True
                if not is_in:
                    pip['SubjectProcess'][sublist[sub['sub']]][mod_type].append(mod)
        else:
            pip['SubjectProcess'].append(sub)

        # for sub in self['SubjectProcess']:
        #     tmp_attr = modality.get_attributes()
        #     tmp_attr['fileLoc'] = sub[mod_type][-1]['fileLoc']
        #     for sub_origin in pip['SubjectProcess']:
        #         if sub['sub'] == sub_origin['sub']:
        #             sub_origin[mod_type] = create_subclass_instance(mod_type, Process)
        #             sub_origin[mod_type][-1].update(tmp_attr)

    def is_pipeline_present(self, pipeline_label):
        print(self.classname() + ' does not have pipelines!')


class Info(BidsFreeFile):
    pass


class Command(BidsBrick):
    keylist = ["tag", "Info"]
    required_keys = keylist


class Settings(BidsBrick):
    keylist = ["label", "fileLoc", "Command", 'automatic']
    required_keys = keylist[0:1]


class PipelineSettings(BidsBrick):
    keylist = ['Settings']
    required_keys = keylist
    recognised_keys = ['bids_dir', 'sub']

    def read_file(self):
        if os.path.exists('pipeline_settings.json'):
            with open('pipeline_settings.json', 'r') as file:
                rd_json = json.load(file)
            self.copy_values(rd_json)

    def propose_param(self, bidsdataset, idx):
        if not isinstance(bidsdataset, BidsDataset):
            return
        selected_pip = self['Settings'][idx]
        proposal = dict()
        for elmt in selected_pip['Command']:
            if 'sub' in elmt['Info']:
                proposal['sub'] = bidsdataset.get_subject_list()
        return proposal

    def launch_pipeline(self, idx):
        pass


def subclasses_tree(brick_class, nb_space=0):
    if nb_space:
        tree_str = '|--'
    else:
        tree_str = ''
    sub_classes_tree = nb_space * ' ' + tree_str + brick_class.__name__ + str(brick_class.keylist) + '\n'
    nb_space += 2
    for subcls in brick_class.__subclasses__():
        sub_classes_tree += subclasses_tree(subcls, nb_space=nb_space)
    return sub_classes_tree


def latest_file(folderpath, file_type):
    try:
        list_of_files = os.listdir(folderpath)

        if file_type == 'parsing':
            ext = '.json.gz'
            condition = lambda fname: fname.startswith('parsing')
        elif file_type == 'log':
            ext = '.log'
            condition = lambda fname: fname.endswith(ext)
        elif file_type == 'issue':
            ext = '.json'
            condition = lambda fname: fname.startswith('issue') and fname.endswith(ext)
        else:
            raise NotImplementedError()
        list_of_specific_files = [file for file in list_of_files if condition(file)]
        date_obj = [
            datetime.strptime(file.replace(ext, '').split('_')[-1], BidsBrick.time_format)
            for file in list_of_specific_files]

        if date_obj:
            latest_dt = max(dt for dt in date_obj)
            return os.path.join(folderpath, list_of_specific_files[date_obj.index(latest_dt)])
        else:
            return None

    except Exception as err:
        exc_type, exc_obj, exc_tb = exc_info()
        err_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print('Error type: ' + str(exc_type) + ', scriptname: ' + err_name + ', line number, ' + str(
            exc_tb.tb_lineno) + ': ' + str(err))
        #print(str(err))
        return None


def create_subclass_instance(name, superclasse):
    sucl_list = ElectrophyProcess.get_list_subclasses_names()
    if name in sucl_list:
        ind_class = sucl_list.index(name)
        newclass = superclasse.__subclasses__()[ind_class]
    else:
        newclass = type(name, (superclasse,), {}) #To add a base key.capitalize()
        newclass.__module__ = superclasse.__module__
        setattr(modules[__name__], newclass.__name__, newclass)
    str = name.split('P')[0]
    instance = newclass()
    instance['modality'] = str.lower()

    return instance


# create all modality processes
for elmt in Electrophy.get_list_subclasses_names():
    newclass = type(builtin_str(elmt+'Process'), (ElectrophyProcess,), {})  # To add a base key.capitalize()
    newclass.__module__ = Process.__module__
    setattr(newclass, 'modality', elmt.lower())
    setattr(modules[__name__], newclass.__name__, newclass)


def chmod_recursive(this_path, mode, debug=False):
    if os.getuid() == os.stat(this_path).st_uid:
        os.chmod(this_path, mode)
    elif debug:
        print(" Changing permission denied because the directory doesn't belong to the current user !")
    for root, dirs, files in os.walk(this_path):
        for this_dir in [os.path.join(root, d) for d in dirs]:
            if os.getuid() != os.stat(this_dir).st_uid:
                if debug:
                    print("{} can not change permissions of {} belonging to {}".format(os.getuid(), this_dir, os.stat(this_dir).st_uid))
                continue
            else:
                os.chmod(this_dir, mode)
                print("{} changed privileges to {}".format(this_dir, mode))
        for this_file in [os.path.join(root, f) for f in files]:
            if os.getuid() != os.stat(this_file).st_uid:
                if debug:
                    print("{} belongs to {}. So, {} can not set its permissions ".format(this_file, os.stat(this_file).st_uid, os.getuid()))
                continue
            else:
                os.chmod(this_file, mode)
                print("{} changed its privileges to {}".format(this_file, mode))


if __name__ == '__main__':

    if len(argv) == 1 or len(argv) > 3:
        cls_tree_str = subclasses_tree(BidsBrick)
        print(cls_tree_str)
        cls_tree_str = subclasses_tree(BidsSidecar)
        print(cls_tree_str)
        # exit('bidsification.py should be launched with at least on argument.\n bidsification.py bids_directory '
        #          '[import_directory]')
    elif len(argv) == 2:
        # parse the directory and initialise the bids_data instance
        bids_dataset = BidsDataset(argv[1])

    # if len(argv) == 3:
    #     # read the data2import folder and initialise the the data2import by reading the data2import.json
    #     data2import = Data2Import(argv[2])
    #     # import the data in the bids_directory
    #     bids_dataset.import_data(data2import)


