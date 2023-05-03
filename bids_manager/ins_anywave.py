#!/usr/bin/python3
# -*-coding:Utf-8 -*

#     BIDS Manager collect, organise and manage data in BIDS format.
#     Copyright © 2018-2020 Aix Marseille University, INSERM, INS
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
#     Authors: Aude Jegou, 2021-2022

import os
import shutil

anywave_ext = ['.flt', '.levels', '.bad', '.mrk', '.mtg', '.display', '.sel']
anywave_ext_analysis = ['.bad', '.mrk', '.mtg']
__modality_type__ = ['ieeg', 'eeg', 'meg']


def handle_anywave_files(bids_dirname, access, foldername, reverse=False, sublist=None, overwrite=None, dirname_dest=None, files_type=None, modality=None):
    """ Function to manage anywave files, copying them into derivatives/anywave/etc or in raw data while it is required for
    the process

    :param bids_dirname:
    :param access:
    :param foldername:
    :param reverse:
    :param sublist:
    :param overwrite:
    :param dirname_dest:
    :param files_type:
    :param modality:
    :return:
    """

    # TODO option to say if the output is local or not

    if modality is None:
        modality = __modality_type__
    if files_type is None:
        files_type = anywave_ext
    log = ''
    if foldername != 'common' and dirname_dest is None:
        if access[foldername]['permission'] == 'read': #peut-etre ne pas mettre reverse car finalement si juste en lecture il ne peuvent pas move
            log += '/!\\ WARNING /!\\ Current user {} cannot write or move in the BIDS dataset folder so the AnyWave files won"t be moved\n'.format(foldername)
            return log
        elif len(access.keys()) >1:
            if any(access[us]['import_data'] or access[us]['analyse_data'] for us in access if not us == foldername):
                log += '/!\\ WARNING /!\\ Anywave files cannot be moved because the dataset is in used by someone else.\n'
                return log
    if sublist is None:
        sublist = [sub for sub in os.listdir(bids_dirname) if sub.startswith(('sub-'))]
    else:
        if 'sub-' not in sublist[0]:
            sublist = ['sub-' + sub for sub in sublist]
    anywave_folder = os.path.join(bids_dirname, 'derivatives', 'anywave', foldername)
    os.makedirs(anywave_folder, exist_ok=True)
    if reverse:
        with os.scandir(anywave_folder) as it:
            for entry in it:
                if entry.name.startswith('sub-') and entry.name in sublist:
                    parse_sub_dir(bids_dirname, entry.path, modality, files_type, original_dirname=anywave_folder, reverse=True)
    elif not reverse and dirname_dest is None:
        with os.scandir(bids_dirname) as it:
            for entry in it:
                if entry.name.startswith('sub-') and entry.is_dir() and entry.name in sublist:
                    parse_sub_dir(bids_dirname, entry.path, modality, files_type, original_dirname=bids_dirname, dirname_dest=anywave_folder, overwrite=overwrite)
    elif dirname_dest is not None:
        with os.scandir(anywave_folder) as it:
            for entry in it:
                if entry.name.startswith('sub-') and entry.name in sublist:
                    parse_sub_dir(bids_dirname, entry.path, modality, files_type, original_dirname=anywave_folder, reverse=True, dirname_dest=dirname_dest)
    return log


## Add security to not overwrite
def parse_sub_dir(bids_dirname, dirname, modality, files_type, original_dirname=None, dirname_dest=None, reverse=False, overwrite=None):
    """Parse the subject directory to find anywave files

    :param bids_dirname:
    :param dirname:
    :param modality:
    :param files_type:
    :param original_dirname:
    :param dirname_dest:
    :param reverse:
    :param overwrite:
    :return:
    """
    with os.scandir(dirname) as it:
        for entry in it:
            [filename, ext] = os.path.splitext(entry.name)
            if entry.name.startswith('ses-') and entry.is_dir():
                parse_sub_dir(bids_dirname, entry.path, modality, files_type, original_dirname=original_dirname, dirname_dest=dirname_dest, reverse=reverse, overwrite=overwrite)
            elif entry.name in __modality_type__ and entry.is_dir() and entry.name in modality:
                parse_sub_dir(bids_dirname, entry.path, modality, files_type, original_dirname=original_dirname, dirname_dest=dirname_dest, reverse=reverse, overwrite=overwrite)
            elif entry.is_file() and ext.lower() in files_type and not entry.name.endswith('_montage.mtg'):
                if dirname_dest is None:
                    dirname_dest = bids_dirname
                sub_dirname = os.path.dirname(entry.path)
                sub_dirname = sub_dirname.replace(original_dirname + '\\', '')
                dirname_dest_sub = os.path.normpath(os.path.join(dirname_dest, sub_dirname))
                os.makedirs(dirname_dest_sub, exist_ok=True)
                if reverse:
                    shutil.copy2(entry.path, os.path.join(dirname_dest_sub, entry.name))
                else:
                    if not os.path.exists(dirname_dest_sub):
                        os.makedirs(dirname_dest_sub)
                    if (os.path.exists(os.path.join(dirname_dest_sub, entry.name)) and (overwrite is None or overwrite)) or not os.path.exists(os.path.join(dirname_dest_sub, entry.name)):
                        shutil.move(entry.path, os.path.join(dirname_dest_sub, entry.name))
                    elif not overwrite and os.path.exists(os.path.join(dirname_dest_sub, entry.name)):
                        os.remove(entry.path)
            elif entry.is_dir() and entry.name.endswith('_meg'):
                if dirname_dest is None:
                    dirname_dest = bids_dirname
                sub_dirname = entry.path
                sub_dirname = sub_dirname.replace(original_dirname + '\\', '')
                dirname_dest_sub = os.path.normpath(os.path.join(dirname_dest, sub_dirname))
                os.makedirs(dirname_dest_sub, exist_ok=True)
                for file in os.listdir(entry.path):
                    [filename, ext] = os.path.splitext(file)
                    if ext.lower() in anywave_ext:
                        if reverse:
                            shutil.copy2(os.path.join(entry.path, file), os.path.join(dirname_dest_sub, file))
                        else:
                            if not os.path.exists(dirname_dest_sub):
                                os.makedirs(dirname_dest_sub)
                            if (os.path.exists(os.path.join(dirname_dest_sub, entry.name)) and (
                                    overwrite is None or overwrite)) or not os.path.exists(
                                    os.path.join(dirname_dest_sub, entry.name)):
                                shutil.move(os.path.join(entry.path, file), os.path.join(dirname_dest_sub, file))
