#!/usr/bin/python3
# -*-coding:Utf-8 -*

#     BIDS Pipeline select and analyse data in BIDS format.
#     Copyright © 2018-2020 Aix-Marseille University, INSERM, INS
#
#     This file is part of BIDS Pipeline. This file manages the exportation of BIDS data.
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
from bids_pipeline.interface_class import Interface
from generic_uploader import deltamed, micromed, anonymize_edf, anonymizeDicom
from generic_uploader.generic_uploader import valide_mot, hash_object, valide_date
from tkinter import filedialog
from tkinter import Tk,  Button, Frame, Label, GROOVE, messagebox, Entry, Toplevel, BOTH
from tkinter.ttk import Combobox
from tkcalendar import DateEntry
import re
import os
import shutil
import random
import platform

__param__ = ['import_in_bids', 'output_directory', 'select_session', 'select_modality', 'anonymise', 'derivatives']


def export_data(bids_data, output_select, root=None):
    """Function to export data from one BIDS dataset

    :param bids_data: str or BidsDataset
    :param output_select: str, path of output directory
    :param root: tkinter, Windows to display new features
    :return:
    """
    log = ''
    anonymize = False
    new_bids_attributes = None
    deface = None
    full = False
    #initiate the parameter value
    if isinstance(bids_data, str):
        bids_data = bids.BidsDataset(bids_data)
    #Get the value from user
    param = output_select['0_exp']['analysis_param']
    #sub_selected = random.shuffle(output_select['0_exp']['subject_selected'])
    sub_selected = output_select['0_exp']['subject_selected']
    if 'output_directory' not in param:
        raise EOFError('The output directory is missing.')
    if 'anonymise' not in param:
        log += 'The anonymise key was not provided so by default the data won"t be anonymised'
        param['anonymise'] = None
    if 'import_in_bids' not in param:
        param['import_in_bids'] = False
    if 'sourcedata' not in param:
        param['sourcedata'] = None
    if 'derivatives' not in param:
        param['derivatives'] = 'None'
    if 'defaceanat' in param:
        deface=param['defaceanat']
        if deface == '':
            deface=None
    #Errors if merge and the dataset selected is not Bids or if the session name are different
    if param['import_in_bids']:
        try:
            new_bids_data = bids.BidsDataset(param['output_directory'])
            new_bids_attributes, ses = get_attributes_newbids(new_bids_data)
            if 'all' in param['select_session']:
                ses_old = [elt['ses'] for sub in bids_data['Subject'] for mod in
                   bids.Imaging.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names() if mod for elt
                   in sub[mod]]
                ses_old = list(set(ses_old))
            else:
                ses_old = param['select_session']
            if not all(so in ses for so in ses_old):
                raise EOFError('The BIDS dataset cannot be merged because the session names are different.')
        except:
            raise EOFError('The output directory is not BIDS dataset so it is not possible to merge data.')
    #Check if anonymisation is required
    if param['anonymise'] == 'pseudo-anonymisation' or param['anonymise'] == 'full-anonymisation':
        anonymize = True
        full = False
        if param['anonymise'] == 'full-anonymisation':
            full = True
    if not param['import_in_bids']:
        if not full:
            header = [elt for elt in bids_data['ParticipantsTSV'].header if
                      not elt.endswith('_ready') and not elt.endswith('_integrity')]
        else:
            header = ['participant_id']
        new_partTSV = bids.ParticipantsTSV(header=header, required_fields=['participant_id'])
        random.shuffle(sub_selected)
        sub_anonymize = {}
        for sub in sub_selected:
            idx_part = [cnt for cnt, line in enumerate(bids_data['ParticipantsTSV']) if
                        line[0].replace('sub-', '') == sub]
            tmp_dict = {elt: bids_data['ParticipantsTSV'][idx_part[0]][bids_data['ParticipantsTSV'][0].index(elt)] for
                        elt in bids_data['ParticipantsTSV'].header}
            if anonymize:
                sub_anonymize[sub] = hash_object(sub+'exportation')
            else:
                sub_anonymize[sub] = sub
            tmp_dict['participant_id'] = 'sub-'+sub_anonymize[sub]
            new_partTSV.append(tmp_dict)
        dataset = bids.DatasetDescJSON()
        dataset['Name'] = 'export'
    else:
        if root is None:
            messagebox.showerror('Window problem', 'There is no graphical interface')
            return
        dataset = bids.DatasetDescJSON()
        dataset.read_file(os.path.join(param['output_directory'], dataset.filename))
        secret_key = dataset['Name']
        other_part = bids.ParticipantsTSV(header=['participant_id'], required_fields=['participant_id'])
        other_part.read_file(os.path.join(param['output_directory'], other_part.filename))
        #get the subject ID from the new
        subinside = [sub['sub'] for sub in new_bids_data['Subject']]
        results = AssociateSubjects(root, sub_selected, subinside, secret_key, anonymize)
        newsub_dict = results.new_id
        random.shuffle(sub_selected)
        try:
            sub_anonymize, new_partTSV = create_subject_id(sub_selected, bids_data['ParticipantsTSV'], otherpart=other_part, full=full, sub_dict=newsub_dict)
        except Exception as err:
            messagebox.showerror('Subject selection', err)
            return
    #tmp_directory = os.path.join(bids_data.dirname, 'derivatives', 'bids_pipeline', 'tmp_directory')
    #os.makedirs(tmp_directory, exist_ok=True)
    try:
        for sub in bids_data['Subject']:
            if sub['sub'] in sub_selected:
                new_name = sub_anonymize[sub['sub']]
                for mod in bids.Imaging.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names() + bids.GlobalSidecars.get_list_subclasses_names():
                    if ('all' in param['select_modality'] or mod in param['select_modality'] or mod.replace('GlobalSidecars', '') in param['select_modality']) and sub[mod]:
                        get_files(sub[mod], mod, param['select_session'], param['output_directory'], new_name, bids_data.dirname, new_bids_attributes=new_bids_attributes, deface=deface)
                    elif mod == 'Scans' and sub[mod] and not param['import_in_bids']:
                        for elt in sub[mod]:
                            new_scans = bids.Scans()
                            new_scans['sub'] = new_name
                            new_scans['ses'] = elt['ses']
                            path, filename, ext = elt['fileLoc']
                            path = path.replace(sub['sub'], new_name)
                            filename = filename.replace(sub['sub'], new_name)
                            new_scans['fileLoc'] = os.path.join(param['output_directory'], path, filename+ext)
                            for line in elt['ScansTSV'][1:]:
                                tmp_dict = {}
                                tmp_dict['filename'] = line[0].replace(sub['sub'], new_name)
                                tmp_dict['acq_time'] = line[1]
                                new_scans['ScansTSV'].append(tmp_dict)
                            new_scans.write_file()
        if param['sourcedata']:
            if full:
                flag = messagebox.askyesno('ERROR: Full-Anonymisation',
                                           'Sourcedata cannot be saved with full-anonymisation.'
                                           'Do you want to continue without saving sourcedata?')
                if not flag:
                    return
            if not full:
                tmp_directory = os.path.join(param['output_directory'], 'sourcedata')
                os.makedirs(tmp_directory, exist_ok=True)
                for sub in bids_data['SourceData'][0]['Subject']:
                    if sub['sub'] in sub_selected:
                        new_name = sub_anonymize[sub['sub']]
                        for mod in bids.Imaging.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names() + bids.GlobalSidecars.get_list_subclasses_names():
                            if ('all' in param['select_modality'] or mod in param['select_modality'] or mod.replace(
                                    'GlobalSidecars', '') in param['select_modality']) and sub[mod]:
                                get_files(sub[mod], mod, param['select_session'], param['output_directory'], new_name, bids_data.dirname, sdcar=False, anonymize=anonymize, in_src=True, deface=deface)
                #for dir in os.listdir(os.path.join(tmp_directory, 'sourcedata')):
                #    shutil.move(os.path.join(tmp_directory, 'sourcedata', dir), os.path.join(param['output_directory'], 'sourcedata'))
                new_srctrck = bids.SrcDataTrack()
                srctrack_file = os.path.join(tmp_directory, bids.SrcDataTrack.filename)
                if param['import_in_bids'] and os.path.exists(srctrack_file):
                    new_srctrck.read_file(tsv_full_filename=srctrack_file)
                for line in bids_data['SourceData'][0]['SrcDataTrack'][1::]:
                    file_split = line[1].split('_')
                    sub = file_split[0].replace('sub-', '')
                    if sub in sub_selected:
                        tmp_dict = {}
                        tmp_dict['orig_filename'] = line[0]
                        if anonymize:
                            tmp_dict['bids_filename'] = line[1].replace(sub, sub_anonymize[sub])
                        else:
                            tmp_dict['bids_filename'] = line[1]
                        tmp_dict['upload_date'] = line[2]
                        new_srctrck.append(tmp_dict)
                new_srctrck.write_file(tsv_full_filename=srctrack_file)

        #To test for the run number because cannot cange from derivatives
        if param['derivatives'] != 'None':
            for dev in bids_data['Derivatives'][0]['Pipeline']:
                tmp_directory = os.path.join(param['output_directory'], 'derivatives', dev['name'])
                if ('all' in param['derivatives'] or dev['name'] in param['derivatives']) and dev['name'] not in ['log', 'parsing', 'log_old', 'parsing_old']:
                    os.makedirs(tmp_directory, exist_ok=True)
                    for sub in dev['SubjectProcess']:
                        if sub['sub'] in sub_selected:
                            new_name = sub_anonymize[sub['sub']]
                            anymod = []
                            for mod in bids.ImagingProcess.get_list_subclasses_names() + bids.ElectrophyProcess.get_list_subclasses_names():
                                if ('all' in param['select_modality'] or mod.replace('Process', '') in param['select_modality']):
                                    if sub[mod]:
                                        anymod.append(True)
                                        get_files(sub[mod], mod, param['select_session'], param['output_directory'], new_name, bids_data.dirname, in_dev=True, deface=deface)
                                    else:
                                        anymod.append(False)
                            if not any(anymod):
                                devorigpath = os.path.join(bids_data.dirname, 'derivatives', dev['name'])
                                origpath = os.path.join(devorigpath, 'sub-' + sub['sub'])
                                if os.path.exists(origpath):
                                    newpath = os.path.join(tmp_directory, 'sub-' + new_name)
                                    recursive_copy(origpath, newpath)
                    new_datsetdesc = bids.DatasetDescPipeline()
                    for key in dev['DatasetDescJSON']:
                        if isinstance(dev['DatasetDescJSON'][key], bids.BidsBrick):
                            new_datsetdesc[key].copy_values(dev['DatasetDescJSON'][key])
                        else:
                            new_datsetdesc[key] = dev['DatasetDescJSON'][key]
                    if 'SourceDataset' in dev['DatasetDescJSON']:
                        if anonymize:
                            new_datsetdesc['SourceDataset'] = [sub_anonymize[elt] for elt in dev['DatasetDescJSON']['SourceDataset'] if elt in sub_selected]
                        else:
                            new_datsetdesc['SourceDataset'] = [elt for elt in
                                                               dev['DatasetDescJSON']['SourceDataset'] if elt in sub_selected]
                    new_datsetdesc.write_file(os.path.join(tmp_directory, new_datsetdesc.filename))
    except Exception as err:
        new_partTSV.write_file(tsv_full_filename=os.path.join(param['output_directory'], bids.ParticipantsTSV.filename))
        dataset.write_file(jsonfilename=os.path.join(param['output_directory'], bids.DatasetDescJSON.filename))
        messagebox.showerror('ERROR', err)
        return
    new_partTSV.write_file(tsv_full_filename=os.path.join(param['output_directory'], bids.ParticipantsTSV.filename))
    dataset.write_file(jsonfilename=os.path.join(param['output_directory'], bids.DatasetDescJSON.filename))
    if param['import_in_bids']:
        new_bids_data._assign_bids_dir(new_bids_data.dirname)
        new_bids_data.parse_bids()
        bids_data._assign_bids_dir(bids_data.dirname)

    return


def get_files(mod_list, mod_type, ses_list,  output_dir, new_name, bidsdirname, sdcar=True, anonymize=False, in_src=False, new_bids_attributes=None, deface=None, in_dev=False):
    """Take the file to export/merge, do a copy in teh output directory

    :param mod_list:
    :param mod_type:
    :param ses_list:
    :param output_dir:
    :param new_name:
    :param bidsdirname:
    :param sdcar:
    :param anonymize:
    :param in_src:
    :param new_bids_attributes:
    :param deface:
    :param in_dev:
    :return:
    """
    for elt in mod_list:
        sub_id = elt['sub']
        if sub_id == '':
            val = re.split(r'[\\, /]+', elt['fileLoc'])
            sib = [v.replace('sub-', '') for v in val if v.startswith('sub-')]
            if sib:
                sub_id = sib[0]
            else:
                raise EOFError(elt['fileLoc'] + ' is not in BIDS format')
        if (elt['ses'] in ses_list or 'all' in ses_list) or (in_src and not elt['ses']):
            path = os.path.dirname(elt['fileLoc'])
            file = os.path.basename(elt['fileLoc'])
            filename, ext = os.path.splitext(file)
            if mod_type in bids.GlobalSidecars.get_list_subclasses_names():
                new_elt_attributes = eval('bids.' + mod_type + '(r"' + os.path.join(bidsdirname, elt['fileLoc']) + '")')
            else:
                new_elt_attributes = eval('bids.'+mod_type+'()')
            dicttocopy = {key: val for key, val in elt.items() if key not in ['sub', 'fileLoc'] + bids.GlobalSidecars.get_list_subclasses_names()}
            dicttocopy['sub'] = new_name
            new_elt_attributes.update(dicttocopy)
            if new_bids_attributes is not None:
                if new_name in new_bids_attributes and mod_type in new_bids_attributes[new_name]:
                    strrun = compare_attributes(elt, new_bids_attributes[new_name][mod_type])
                    new_elt_attributes.update({'run':strrun})
            if not in_src:
                new_filename, otherdir, otherext = new_elt_attributes.create_filename_from_attributes()
            else:
                new_filename = filename
                delimiter = os.path.sep
                listpath = path.split(delimiter)
                id = [st.replace('sub-', '') for st in listpath if st.startswith('sub-')]
                sub_id = id[0]
            sub_dir = os.path.join(output_dir, path)
            sub_dir = sub_dir.replace(sub_id, new_name)
            os.makedirs(sub_dir, exist_ok=True)
            if ext == '.vhdr':
                extension = ['.vhdr', '.vmrk', '.eeg']
            else:
                extension = [ext]
            for ex in extension:
                origfile = os.path.join(bidsdirname, path, filename + ex)
                if ex != '' and os.path.exists(origfile):
                    out_file = os.path.join(sub_dir, new_filename + ex)
                    shutil.copy2(origfile,
                                 out_file)
                    if ex in ['.vhdr', '.vmrk', '.json'] and sub_id != new_name:
                        rewrite_txt_infile(out_file, filename, new_filename)
                elif (in_dev or in_src) and ext == '':
                    new_filename = filename.replace('sub-'+sub_id, 'sub-'+new_name)
                    out_file = os.path.join(sub_dir, new_filename)
                    if mod_type in bids.Imaging.get_list_subclasses_names() + bids.ImagingProcess.get_list_subclasses_names() and deface is not None:
                        messagebox.showinfo('WARNING', 'As you selected deface mode, the folder {} cannot be copied.'.format(origfile))
                        pass
                    else:
                        recursive_copy(origfile, out_file, sub_id, new_name)


            if sdcar:
                sidecar = elt.get_modality_sidecars()
                for sidecar_key in sidecar:
                    if elt[sidecar_key]:
                        if elt[sidecar_key].modality_field:
                            sdcar_fname = filename.replace(elt['modality'],
                                                           elt[sidecar_key].modality_field)
                        else:
                            sdcar_fname = filename
                        new_sdcar_fname = sdcar_fname.replace(sub_id, new_name)
                        if os.path.exists(os.path.join(bidsdirname, path, sdcar_fname + elt[sidecar_key].extension)):
                            shutil.copy2(os.path.join(bidsdirname, path, sdcar_fname + elt[sidecar_key].extension),
                                         os.path.join(sub_dir, new_sdcar_fname + elt[sidecar_key].extension))
            if anonymize:
                if ext == ".trc":
                    micromed.anonymize_micromed(out_file)
                elif ext == ".eeg":
                    deltamed.anonymize_deltamed(out_file)
                elif ext == ".edf":
                    anonymize_edf.anonymize_edf(out_file)
                elif ext == '' and elt.classname() in bids.Imaging.get_list_subclasses_names() and in_src:
                    anonymizeDicom.anonymize(out_file, out_file, new_name, new_name, True, False)
            if deface is not None and mod_type in bids.Imaging.get_list_subclasses_names():
                if ext == ".nii":
                    keepgoing = deface_anatomical_data(out_file, deface)
                    if not keepgoing:
                        raise Exception('Mango is not installed on your computer.\n')


def recursive_copy(path, dest, subid='', newid=''):
    """Copy all the file of subfolders

    :param path:
    :param dest:
    :param subid:
    :param newid:
    :return:
    """
    os.makedirs(dest, exist_ok=True)
    with os.scandir(path) as it:
        for entry in it:
            name = entry.name
            file, ext = os.path.splitext(name)
            if 'sub-'+subid in name:
                name = entry.name.replace('sub-'+subid, 'sub-'+newid)
            newdest = os.path.join(dest, name)
            if entry.is_dir():
                os.makedirs(os.path.join(dest, name), exist_ok=True)
                recursive_copy(entry.path, newdest)
            elif entry.is_file():
                shutil.copy2(entry.path, newdest)
                if ext in ['.json', '.txt', '.vhdr', '.vmrk']:
                    rewrite_txt_infile(newdest, 'sub-'+subid, 'sub-'+newid)


def create_subject_id(sub_selected, part_list, otherpart=None, full=False, sub_dict=None):
    """Create the new subject ID if merge or anonymisation selected

    :param sub_selected:
    :param part_list:
    :param otherpart:
    :param full:
    :param sub_dict:
    :return:
    """
    anonym_dict = {}
    if not full:
        header = [elt for elt in part_list.header if not elt.endswith('_ready') and not elt.endswith('_integrity')]
    elif full and otherpart is not None:
        yesno = messagebox.askyesno(title='Warning', message='Full-anonymisation is not possible with merging option.\n A pseudo-anonymisation will be done.\n Do you want to continue?')
        if yesno:
            header = [elt for elt in otherpart.header if not elt.endswith('_ready') and not elt.endswith('_integrity')]
        else:
            return {}, {}
    else:
        header = ['participant_id']
    if otherpart is None:
        otherpart = bids.ParticipantsTSV(header=header)
    for sub in sub_selected:
        idx_part = [cnt+1 for cnt, line in enumerate(part_list[1::]) if line[0].replace('sub-', '') == sub]
        new_id = ''
        if sub_dict is not None and sub in sub_dict:
            new_id = sub_dict[sub]
        if not new_id:
            new_id = sub
        anonym_dict[sub] = new_id
        isin, subinfo, subidx = otherpart.is_subject_present(new_id)
        tmp_dict = {elt: part_list[idx_part[0]][part_list[0].index(elt)] for elt in header if elt in part_list[0]}
        if not isin:
            tmp_dict['participant_id'] = 'sub-' + new_id
            otherpart.append(tmp_dict)
        else:
            if not all(subinfo[key] == tmp_dict[key] for key in subinfo if key in tmp_dict):
                raise EOFError('The subject ID selected {} for the subject {} doesn"t have the same information.'.format(new_id, sub))
    return anonym_dict, otherpart


def deface_anatomical_data(data, mode):
    """Deface the nifti images for full anonymisation

    :param data: str, nifti file
    :param mode: str, type of defacing (spm or mango)
    :return:
    """
    #data should be in temporary folder
    keepgoing=True
    outfilename=''
    origdirname, origfilename = os.path.split(data)
    origfile, ext = os.path.splitext(origfilename)
    if platform.system() == 'Windows':
        #use the mango script
        #check if the folde exists
        if mode == 'Mango':
            mango_dir = os.path.join(os.getcwd(), 'deface_needs', 'mango-script.bat')
            if os.path.exists(mango_dir):
                #check if mango is installed on the system
                if not os.path.exists('C:\Program Files\Mango'):
                    filename = filedialog.askopenfilename(title='Please select Mango.exe',
                                                      filetypes=[('files', '.exe')])
                    dirname = os.path.dirname(filename)
                    rewrite_txt_infile(os.path.join(mango_dir, 'mango-script.bat'), 'C:\Program Files\Mango', dirname)
                #run the deface process
                os.system('deface_needs\mango-script.bat -f deface_needs\mango_bet_winput.py ' + data)
                #verifer comment où se trouve le fichier et son nouveau nom
                files = os.listdir(origdirname)
                for f in files:
                    if f.startswith(origfile):
                        if f != origfilename:
                            os.remove(data)
                            os.rename(os.path.join(origdirname, f), data)

            else:
                flag = messagebox.askyesno('ERROR: Mango is not installed on your computer', 'Anatomical data cannot be defaced.'
                                                                                             'Do you want to continue without defacing anatomical data?')
                if not flag:
                    keepgoing=False
        elif mode == 'SPM':
            tmpdir = os.path.join(os.getcwd(), 'deface_needs')
            os.system(os.path.join(tmpdir, 'deface_with_spm.exe') + ' dirname {} inputfile {}'.format(tmpdir, data))
            files = os.listdir(origdirname)
            for f in files:
                if f.startswith('anon_') and f.endswith(origfilename):
                    os.remove(data)
                    os.rename(os.path.join(origdirname, f), data)
    else:
        #use pydeface for the other system
        pass
    return keepgoing


def get_attributes_newbids(new_bids_data):
    """For merging, get the attributes of the other bids dataset

    :param new_bids_data: BidsDataset
    :return:
    """
    dict_attributes = {}
    seslist = []
    for sub in new_bids_data['Subject']:
        dict_attributes[sub['sub']] = {}
        for mod in sub:
            if mod in bids.Imaging.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names() and sub[mod]:
                if mod not in dict_attributes[sub['sub']]:
                    dict_attributes[sub['sub']][mod] = {}
                for elt in sub[mod]:
                    if elt['ses'] not in dict_attributes[sub['sub']][mod]:
                        dict_attributes[sub['sub']][mod][elt['ses']] = {}
                        seslist.append(elt['ses'])
                    if mod in bids.Electrophy.get_list_subclasses_names():
                        if 'task' in elt and elt['task']:
                            if elt['task'] not in dict_attributes[sub['sub']][mod][elt['ses']]:
                                dict_attributes[sub['sub']][mod][elt['ses']][elt['task']] = {}
                            if 'acq' in elt and elt['acq']:
                                if elt['acq'] not in dict_attributes[sub['sub']][mod][elt['ses']][elt['task']] :
                                    dict_attributes[sub['sub']][mod][elt['ses']][elt['task']][elt['acq']] = 1
                                else:
                                    dict_attributes[sub['sub']][mod][elt['ses']][elt['task']][elt['acq']] += 1
                            else:
                                if 'nbr' not in dict_attributes[sub['sub']][mod][elt['ses']][elt['task']]:
                                    dict_attributes[sub['sub']][mod][elt['ses']][elt['task']]['nbr'] = 1
                                else:
                                    dict_attributes[sub['sub']][mod][elt['ses']][elt['task']]['nbr'] += 1
                    elif mod in bids.Imaging.get_list_subclasses_names():
                        if 'modality' in elt and elt['modality']:
                            if elt['modality'] not in dict_attributes[sub['sub']][mod][elt['ses']]:
                                dict_attributes[sub['sub']][mod][elt['ses']][elt['modality']] = {}
                            if 'acq' in elt and elt['acq']:
                                if elt['acq'] not in dict_attributes[sub['sub']][mod][elt['ses']][elt['modality']] :
                                    dict_attributes[sub['sub']][mod][elt['ses']][elt['modality']][elt['acq']] = 1
                                else:
                                    dict_attributes[sub['sub']][mod][elt['ses']][elt['modality']][elt['acq']] += 1
                            else:
                                if 'nbr' not in dict_attributes[sub['sub']][mod][elt['ses']][elt['modality']]:
                                    dict_attributes[sub['sub']][mod][elt['ses']][elt['modality']]['nbr'] = 1
                                else:
                                    dict_attributes[sub['sub']][mod][elt['ses']][elt['modality']]['nbr'] += 1
    seslist = list(set(seslist))
    return dict_attributes, seslist


def compare_attributes(mod_elt, dict_attributes):
    """For merging, compare the attributes of the two dataste

    :param mod_elt:
    :param dict_attributes:
    :return:
    """
    keys = [key for key in mod_elt if key != 'ses']
    key='modality'
    run=1
    if 'task' in keys:
        key='task'
    if mod_elt[key] in dict_attributes:
        if mod_elt['acq']:
            if mod_elt['acq'] in dict_attributes[mod_elt[key]]:
                run =  dict_attributes[mod_elt[key]][mod_elt['acq']]+1
        elif 'nbr' in dict_attributes:
            run = dict_attributes[mod_elt[key]]['nbr'] + 1
    if run<10:
        strrun = '0'+str(run)
    else:
        strrun=str(run)
    return strrun


def rewrite_txt_infile(filename, tochange, newstr):
    """Modify the copied file with the new value

    :param filename:
    :param tochange:
    :param newstr:
    :return:
    """
    f = open(filename, 'r')
    contents = f.readlines()
    f.close()
    new_contents = []
    for line in contents:
        if tochange in line:
            elt = line.replace(tochange, newstr)
        else:
            elt = line
        new_contents.append(elt)
    f = open(filename, 'w')
    for nc in new_contents:
        f.write(nc)
    f.close()


class ParametersInterface(Interface):
    """
        A subclass of Interface from interface_class, to create the interface for export option
    """
    def __init__(self, bids_data):
        self.bids_data = bids_data
        self.subject = [sub['sub'] for sub in self.bids_data['Subject']]
        self.dev = [dev['name'] for dev in bids_data['Derivatives'][0]['Pipeline']]
        ses = [elt['ses'] for sub in self.bids_data['Subject'] for mod in bids.Imaging.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names() if mod for elt in sub[mod]]
        ses = list(set(ses))
        mod = [mod for sub in self.bids_data['Subject'] for mod in bids.Imaging.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names() if sub[mod]]
        mod = list(set(mod))
        self.ses = ses + ['all']
        self.mod = mod +['all']
        self.vars_interface()

    def vars_interface(self):
        # self['algorithm'] = {}
        # self['algorithm']['attribut'] = 'Listbox'
        # self['algporithm']['value'] = ['Export', 'Merge', 'Anonymise']
        self['import_in_bids'] = {}
        self['import_in_bids']['attribut'] = 'Bool'
        self['import_in_bids']['value'] = False
        self['output_directory'] = {}
        self['output_directory']['attribut'] = 'File'
        self['output_directory']['value'] = ['dir']
        self['select_session'] = {}
        self['select_session']['attribut'] = 'Variable'
        self['select_session']['value'] = self.ses
        self['select_modality'] = {}
        self['select_modality']['attribut'] = 'Variable'
        self['select_modality']['value'] = self.mod
        self['anonymise'] = {}
        self['anonymise']['attribut'] = 'Listbox'
        self['anonymise']['value'] = ['full-anonymisation', 'pseudo-anonymisation', 'None']
        self['derivatives'] = {}
        self['derivatives']['attribut'] = 'Variable'
        self['derivatives']['value'] = self.dev + ['None', 'all']
        self['sourcedata'] = {}
        self['sourcedata']['attribut'] = 'Bool'
        self['sourcedata']['value'] = False
        self['defaceanat'] = {}
        self['defaceanat']['attribut'] = 'Listbox'
        self['defaceanat']['value'] = ['Mango', 'SPM', 'None']


class AssociateSubjects(Toplevel, Frame):
    """
        A subclass to manage the graphical interface in order to create a new window to associate the ID of the current dataset
        with the new dataset
    """

    def __init__(self, root, subject2import, subjectinside, protocolname, anonymise=False):
        #super().__init__()
        Toplevel.__init__(self, root)

        self.geometry('500x500')
        self.wm_resizable(True, True)
        self.withdraw()
        self.subject2import = subject2import
        self.subjectinside = subjectinside
        self.protocolname = protocolname
        self.anonymise =anonymise
        self.initial_focus = None
        if root.winfo_viewable():
            self.transient(root)
        self.parent = root
        self.body_widget = Frame(self)
        self.body_widget.pack(padx=2, pady=2, fill=BOTH, expand=1)
        self.body(self.body_widget)

        if not self.initial_focus:
            self.initial_focus = self
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.deiconify()
        self.initial_focus.focus_set()
        self.center()
        self.wait_visibility()
        self.grab_set()
        self.wait_window(self)

    def body(self, parent):
        nbr_sub = len(self.subject2import)
        self.finish = False

        self.title('Choose the ID of your subject or give is Name to create the appropriate ID')
        frame_subject2import = Frame(parent, relief=GROOVE, borderwidth=2)
        Label(frame_subject2import, text='Subjects ID to import').grid(row=0, column=0, columnspan=2)
        Label(frame_subject2import, text='').grid(row=1, column=0)
        frame_subject2import.grid(row=0, column=0, rowspan=nbr_sub+1)

        frame_selectid = Frame(parent, relief=GROOVE, borderwidth=2)
        Label(frame_selectid, text='Subjects ID in the BIDS target').grid(row=0, column=0, columnspan=2)
        Label(frame_selectid, text='').grid(row=1, column=0)
        frame_selectid.grid(row=0, column=1, rowspan=nbr_sub+1)

        frame_names = Frame(parent, relief=GROOVE, borderwidth=2)
        Label(frame_names, text='Indicate Name of your subject to create the proper ID').grid(row=0, column=0, columnspan=3)
        Label(frame_names, text='Last Name').grid(row=1, column=0)
        Label(frame_names, text='First Name').grid(row=1, column=1)
        Label(frame_names, text='Date Of Birth').grid(row=1, column=2)
        frame_names.grid(row=0, column=2, rowspan=nbr_sub+1, columnspan=3)

        frame_id = Frame(parent, relief=GROOVE, borderwidth=2)
        Label(frame_id, text='Indicate the new ID if no anonymisation').grid(row=0, column=0, columnspan=2)
        Label(frame_id, text='').grid(row=1, column=0)
        frame_id.grid(row=0, column=5)

        frame_button = Frame(parent)
        frame_button.grid(row=nbr_sub*2+2, column=1, columnspan=2)
        #initiate variables
        self.frame_name = ['frame_subject2import', 'frame_selectid', 'frame_names', 'frame_id']
        self.frame_button = {key: {} for key in self.frame_name}
        self.new_id = {sub: '' for sub in self.subject2import}
        self.subjectinside = self.subjectinside
        self.secret_key = self.protocolname

        #listchoice = Variable(frame_selectid, self.subjectinside)
        for cnt,sub in enumerate(self.subject2import):
            if cnt == 0:
                nbrow = 2
            else:
                nbrow = cnt*2 +2
            self.frame_button[self.frame_name[0]][sub] = Label(frame_subject2import, text=sub)
            self.frame_button[self.frame_name[0]][sub].grid(row=nbrow, column=0)
            self.frame_button[self.frame_name[1]][sub] = Combobox(frame_selectid, values=self.subjectinside)
            self.frame_button[self.frame_name[1]][sub].grid(row=nbrow, column=0)
            self.frame_button[self.frame_name[2]][sub] = {}
            self.frame_button[self.frame_name[2]][sub][0] = Entry(frame_names, exportselection=0)
            self.frame_button[self.frame_name[2]][sub][0].grid(row=nbrow, column=0)
            self.frame_button[self.frame_name[2]][sub][1] = Entry(frame_names, exportselection=0)
            self.frame_button[self.frame_name[2]][sub][1].grid(row=nbrow, column=1)
            self.frame_button[self.frame_name[2]][sub][2] = DateEntry(frame_names, year=1900, month=1, day=1, date_pattern='dd/mm/yyyy', foreground='white', background='darkblue')
            self.frame_button[self.frame_name[2]][sub][2].grid(row=nbrow, column=2)
            self.frame_button[self.frame_name[3]][sub] = Entry(frame_id, exportselection=0)
            self.frame_button[self.frame_name[3]][sub].grid(row=nbrow, column=0)
        Button(frame_button, text='OK', width=4, command=self.ok).grid(row=0, column=1)
        Button(frame_button, text='Cancel',width=8, command=self.cancel).grid(row=0, column=2)

        if not self.anonymise:
            fr = frame_names
        else:
            fr = frame_id
        for child in fr.winfo_children():
            try:
                child.configure(state='disabled')
            except:
                pass
        self.update_idletasks()


    def ok(self):
        for sub in self.new_id:
            idx = self.frame_button[self.frame_name[1]][sub].get()
            lastname = self.frame_button[self.frame_name[2]][sub][0].get()
            firstname = self.frame_button[self.frame_name[2]][sub][1].get()
            dob = self.frame_button[self.frame_name[2]][sub][2].get()
            idnoan = self.frame_button[self.frame_name[3]][sub].get()
            if idx:
                self.new_id[sub] = idx
            elif lastname or firstname or dob:
                if not lastname:
                    messagebox.showerror('Error', 'Last Name is required to create the ID of {}'.format(sub))
                    return
                if not firstname:
                    messagebox.showerror('Error', 'First Name is required to create the ID of {}'.format(sub))
                    return
                if not dob:
                    messagebox.showerror('Error', 'Date of Birth is required to create the ID of {}'.format(sub))
                    return
                lastname = valide_mot(lastname)
                firstname = valide_mot(firstname)
                # month, day, year = dob.split('/')
                # DOB = '/'.join([day, month, year])
                dob = valide_date(dob)
                graine = lastname + firstname + dob + self.secret_key
                self.new_id[sub] = hash_object(graine)
            elif idnoan:
                self.new_id[sub] = idnoan
        # self.root.destroy()
        Toplevel.destroy(self)

    def cancel(self):
        self.frame_button = {}
        self.new_id = {}
        self.subjectinside = []
        self.secret_key = ''
        # self.root.destroy()
        Toplevel.destroy(self)

    def center(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        if width > 1800:
            width = 1800
        if width < 1000 and self.winfo_screenwidth()>1000:
            width = 1000
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
