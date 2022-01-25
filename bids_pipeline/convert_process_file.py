#!/usr/bin/python3
# -*-coding:Utf-8 -*

#     BIDS Pipeline select and analyse data in BIDS format.
#     Copyright © 2018-2020 Aix-Marseille University, INSERM, INS
#
#     This file is part of BIDS Pipeline. This file creates statistical table.
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
from scipy.io import loadmat
from numpy import ndarray
import json
import xlrd
from datetime import datetime

#variables used in all script
__modality_type__ = ['ieeg', 'eeg', 'meg', 'beh'] #'anat', 'pet', 'func', 'fmap', 'dwi',
__channel_name__ = ['channel', 'channels', 'electrode_name', 'electrodes_name', 'electrode_names', 'label', 'labels']
__file_attr__ = ['sub', 'ses', 'task', 'acq', 'proc', 'run']
__reject_dir__ = ['parsing', 'log', 'parsing_old', 'log_old', 'bids_pipeline', 'bids_uploader', 'anywave']


def go_throught_dir_to_convert(dirname, modality):
    log_error=''
    tmp_list = []
    if not os.path.exists(dirname):
        raise ('The directroy doesn"t exists')
    with os.scandir(dirname) as it:
        for entry in it:
            if (entry.name.startswith('sub-') or entry.name.startswith('ses-')) and entry.is_dir():
                log_error, tsv_list = go_throught_dir_to_convert(entry.path, modality)
                tmp_list.extend(tsv_list)
            elif entry.name in modality and entry.is_dir():
                file_list = os.listdir(entry.path)
                ext_list = [os.path.splitext(os.path.join(entry.path, file))[1] for file in file_list]
                ext_list = list(set(ext_list))
                if '.tsv' in ext_list:
                    tmp_list = [os.path.join(entry.path, file) for file in file_list if os.path.splitext(file)[1] == '.tsv']
                    return '', tmp_list
                elif '.mat' in ext_list and ('.xls' and '.xlsx') not in ext_list:
                    mat_file = [file for file in file_list if '.mat' in file]
                    tmp_list = []
                    for file in mat_file:
                        filename = os.path.join(entry.path, file)
                        try:
                            json_dict, tsv_dict = convert_mat_file(filename)
                            log_error, tsv_file = write_file_after_convert(json_dict, tsv_dict)
                            if tsv_file is not None:
                                tmp_list.append(os.path.join(entry.path, tsv_file))
                        except:
                            log_error += filename +' could not be converted in tsv'
                    return log_error, tmp_list
                elif ('.xls' and '.xlsx') in ext_list:
                    xls_file = [file for file in file_list if '.xls' in file]
                    tmp_list = []
                    for file in xls_file:
                        filename = os.path.join(entry.path, file)
                        try:
                            json_dict, tsv_dict = convert_xls_file(filename)
                            log_error, tsv_file = write_file_after_convert(json_dict, tsv_dict)
                            if tsv_file is not None:
                                tmp_list.append(os.path.join(entry.path, tsv_file))
                        except:
                            log_error += filename + ' could not be converted in tsv format'
                            continue
                    return log_error, tmp_list
                else:
                    log_error += 'Some files do not have the right extension (i.e tsv, mat, tsv) and cannot be converted.\n'
    return log_error, tmp_list


def parse_derivatives_folder(folder, table2write, table_attributes=False, folder_in=None, derivatives_folder=None, modality=None):
    dev_folder = None
    if derivatives_folder:
        dev_folder = derivatives_folder
    log_error = ''
    if folder_in is None:
        folder_in = [elt for elt in os.listdir(dev_folder) if elt not in __reject_dir__]
    header = None
    with os.scandir(folder) as it:
        for entry in it:
            if entry.name in folder_in and entry.is_dir():
                #Find the software name:
                soft_name = entry.path.split(dev_folder)[1]
                soft_name = soft_name.split('\\')[1]
                error, file_list = go_throught_dir_to_convert(entry.path, modality)
                log_error += error
                #file_list = os.listdir(entry.path)
                for file in file_list:
                    json_dict, tsv_dict = read_tsv(file)
                    key2remove = []
                    for key in tsv_dict:
                        if key.lower() in __channel_name__ and all(isinstance(elt, str) for elt in tsv_dict[key]):
                            channel = tsv_dict[key]
                            key2remove.append(key)
                    try:
                        header = create_table(tsv_dict, channel, key2remove, table2write, header, table_attributes, file, soft_analysis=soft_name)
                    except UnboundLocalError:
                        log_error += 'The file {} cannot be present in the table.\n'.format(file)
                        pass
            # elif entry.name not in folder_out and entry.is_dir():
            #     error = parse_derivatives_folder(entry.path, table2write, table_attributes, derivatives_folder=dev_folder)
            #     log_error += error
    return log_error


def write_big_table(derivatives_folder, folder_in=None, modality=None):
    if modality is None:
        modality = __modality_type__
        stmod = 'all'
    elif isinstance(modality, str):
        stmod = modality
        modality=[modality]
    #before write_table
    table2write = [[]]
    log_error = parse_derivatives_folder(derivatives_folder, table2write, table_attributes=True, folder_in=folder_in,
                                         derivatives_folder=derivatives_folder, modality=modality)
    filename = 'statistical_table_' + stmod +'.tsv'
    header_len = len(table2write[0])
    if header_len > 0:
        for line in table2write[1::]:
            if len(line) != header_len:
                diff_len = header_len-len(line)
                line.extend(['n/a']*diff_len)
        write_table(table2write, filename, derivatives_folder)
        log_error += 'The statistical table has been written in derivatives folder.\n'
    return log_error


def convert_mat_file(filename):
    def turn_array_in_list(elt):
        if isinstance(elt, ndarray):
            value = elt.tolist()
            final_value = turn_array_in_list(value)
        elif isinstance(elt, list):
            value = []
            for val in elt:
                if isinstance(val, list):
                    inter_value = turn_array_in_list(val)
                    value.extend(inter_value)
                elif isinstance(val, ndarray):
                    if val.dtype.fields is None:
                        if val.size == 1:
                            value.append(val.item())
                        elif val.size <= 306:
                            val = val.tolist()
                            inter_value = turn_array_in_list(val)
                            value.extend(inter_value)
                else:
                    value.append(val)
            final_value = value
        return final_value

    data = loadmat(filename)
    json_dict = {}
    tsv_dict = {}
    mat_keys = ['__header__', '__version__', '__globals__']
    keylist = [key for key in data.keys() if key not in mat_keys]
    for key in keylist:
        if data[key].dtype.hasobject and data[key].dtype.fields is not None:
            dt = data[key].dtype
            for stname in dt.names:
                value = turn_array_in_list(data[key][stname])
                if isinstance(value, str):
                    json_dict[stname] = value
                elif isinstance(value, list):
                    if len(value) == 1:
                        json_dict[stname] = value[0]
                    else:
                        tsv_dict[stname] = value
                else:
                    tsv_dict[stname] = value
        else:
            if data[key].size == 1:
                json_dict[key] = data[key].item()
            elif data[key].size > 1:
                shape = data[key].shape
                if len(shape) <= 2:
                    value = turn_array_in_list(data[key])
                    tsv_dict[key] = value
                else:
                    json_dict[key] = 'value is in {} dimension'.format(len(shape))
    json_dict['filename'] = filename
    return json_dict, tsv_dict


def convert_xls_file(filename):
    def check_header_continu(tmp_dict):
        nbr = [key for key in tmp_dict]
        if len(nbr)>0:
            all_true = []
            last_elt = nbr[0]
            for elt in nbr[1:]:
                if elt == last_elt + 1:
                    all_true.append(True)
                else:
                    all_true.append(False)
                last_elt = elt
            if all(all_true):
                return True
            elif all_true.count(False) < round(len(nbr)*10/100):
                return True
            else:
                return False
        else:
            return False

    workbook = xlrd.open_workbook(filename)
    nsheets = workbook.nsheets
    json_dict = {}
    tsv_dict = {}
    for i in range(0, nsheets, 1):
        json_dict[i] = {}
        worksheet = workbook.sheet_by_index(i)
        ncol = worksheet.ncols
        nrow = worksheet.nrows
        if ncol == 0:
            continue

        for j in range(0, len(worksheet._cell_values), 1):
            tmp_dict = {worksheet._cell_values[j].index(key): key for key in worksheet._cell_values[j] if key}
            if check_header_continu(tmp_dict):
                jj = j +1
                break
        tsv_tmp_dict = {val: [] for key, val in tmp_dict.items()}
        for nbr, lines in enumerate(worksheet._cell_values[jj:]):
            if not all(elt == '' for elt in lines):
                for cnt, elt in enumerate(lines):
                    if cnt < len(tmp_dict)and cnt in tmp_dict:
                        if tmp_dict[cnt] == 'DOB' and elt != '':
                            dob = datetime.strptime(elt, '%d\%m\%Y')
                            elt = dob.strftime('%d%m%Y')
                        elif isinstance(elt, float) and tmp_dict[cnt].lower().startswith('date'):
                            date = datetime(*xlrd.xldate_as_tuple(elt, workbook.datemode))
                            elt = date.strftime('%d/%m/%Y')
                        tsv_tmp_dict[tmp_dict[cnt]].append(elt)
                    elif cnt not in tmp_dict and cnt-1 in tmp_dict:
                        if len(tsv_tmp_dict[tmp_dict[cnt-1]]) <= nbr:
                            tsv_tmp_dict[tmp_dict[cnt - 1]].append(elt)
                        elif not tsv_tmp_dict[tmp_dict[cnt - 1]][-1]:
                            tsv_tmp_dict[tmp_dict[cnt - 1]][-1] = elt
            else:
                idx = worksheet._cell_values.index(lines) + 1
                for line in worksheet._cell_values[idx::]:
                    if not all(elt == '' for elt in line):
                        count = sum(1 for e in line if e != '')
                        if count % 2 == 0:
                            for j in range(0, ncol, 2):
                                if line[j] and j+1 < ncol:
                                    json_dict[i][line[j]] = line[j+1]
                break
        tsv_dict[i] = tsv_tmp_dict
    if len(tsv_dict.keys()) == 1:
        tsv_dict = tsv_dict[0]
        json_dict = json_dict[0]
    json_dict['filename'] = filename
    return json_dict, tsv_dict


def convert_txt_file(filename):
    json_dict = {'filename': filename}
    f = open(filename, 'r+')
    f_cont = f.readlines()
    f_cont = [line.replace('\n', '') for line in f_cont]
    if all('\t' in line for line in f_cont):
        pass
    #to complicated to handle I guess
    #Recuperer les lignes avec separateur /n
    #si dans la ligne /t
    #en faire un tableau
    pass


def read_tsv(filename):
    json_dict = {'filename': filename}
    file = open(filename, 'r')
    data = file.readlines()
    data = [line.replace('\n', '') for line in data]
    if data:
        header = data[0].split('\t')
        tsv_dict = {key: [] for key in header}
        for lines in data[1::]:
            line = lines.split('\t')
            for key in header:
                idx = header.index(key)
                if idx < len(line):
                    tsv_dict[key].append(line[idx])
                else:
                    tsv_dict[key].append('')
    else:
        tsv_dict = {}

    return json_dict, tsv_dict


def read_vmrk(filename):
    infos_dict = extract_info_vhdr(filename.replace('.vmrk', '.vhdr'))
    ts = float(infos_dict['SamplingInterval'])*1e-6
    json_dict = {'filename': filename}
    tsv_dict = {'onset': [], 'duration': [], 'trial_type': []}
    file = open(filename, 'r')
    data = file.readlines()
    if '[Marker Infos]\n' in data:
        beg = data.index('[Marker Infos]\n')
        for line in data[beg+1::]:
            if line.startswith('Mk'):
                elt = line.split(',')
                tsv_dict['trial_type'].append(elt[1])
                tsv_dict['onset'].append(str(float(elt[2])*ts))
                tsv_dict['duration'].append(str(float(elt[3])*ts))

        file.close()
    return json_dict, tsv_dict


def extract_info_vhdr(filename):
    file = open(filename, 'r')
    data = file.readlines()
    beg = data.index('[Common Infos]\n')
    fin = data.index('[Binary Infos]\n')
    infos_dict = {}
    for line in data[beg+1:fin]:
        line = line.replace('\n', '')
        if '=' in line:
            elt = line.split('=')
            infos_dict[elt[0]] = elt[1]
    file.close()
    return infos_dict


def create_table(tsv_dict, channel, key2remove, table2write, header_real_val=None, table_attributes=False, file=None, soft_analysis=None):
    header_tsv = []
    if header_real_val is None:
        header_real_val = {'header': table2write[0]}
    name = {}
    if soft_analysis:
        soft = soft_analysis + '_'
    else:
        soft = ''

    if table_attributes:
        name_list = os.path.basename(file).split('_')
        name = {elt.split('-')[0]: elt.split('-')[1] for elt in name_list if '-' in elt and elt.split('-')[0] in __file_attr__}
        if not header_real_val['header']:
            header_real_val['header'].extend(name)
        elif any(elt not in header_real_val['header'] for elt in name):
            if 'Channel' in header_real_val['header']:
                idx = header_real_val['header'].index('Channel')
            else:
                idx = len(header_real_val['header'])
            for elt in name:
                if elt not in header_real_val['header']:
                    header_real_val['header'].insert(idx, elt)
                    for line in table2write[1::]:
                        line.insert(idx, 'n/a')

    if 'sub' not in header_real_val['header']:
        header_real_val['header'].insert(0, 'sub')
    if 'Channel' not in header_real_val['header']:
        header_real_val['header'].insert(len(header_real_val['header']), 'Channel')
        # col_attr = [name[nm] for nm in name if nm in __file_attr__]
        # key_attr = '_'.join(col_attr)
    for key in tsv_dict:
        key2write = key.replace(' ', '_')
        # if table_attributes:
        #     key2write = key_attr + '_' + key.replace(' ', '_')
        # else:
        #     key2write = key.replace(' ', '_')
        if key not in key2remove and soft + key2write not in header_real_val['header'] and len(tsv_dict[key]) == len(channel) and key != '':
            new_key = soft + key2write
            header_real_val['header'].append(new_key)
            header_real_val[new_key] = {'infile':key, 'softname':soft}

        # header_tsv.append(soft + key2write)
        # create_attributes_table
    for i in range(0, len(channel), 1):
        chan = channel[i]
        id_chan = header_real_val['header'].index('Channel')
        flag_not_inside = True
        lines = None
        if table_attributes:
            idx = [cnt for cnt, l in enumerate(table2write) if all(l[j] == name[header_real_val['header'][j]] for j in range(0, id_chan, 1) if header_real_val['header'][j] in name) and l[id_chan] == chan]
            if idx:
                flag_not_inside = False
                lines = table2write[idx[0]]
                if len(lines) != len(header_real_val['header']):
                    for n in range(len(lines), len(header_real_val['header']), 1):
                        lines.append('n/a')
            else:
                lines = ['n/a'] * len(header_real_val['header'])
        else:
            lines = ['n/a'] * len(header_real_val['header'])
        for key in header_real_val['header']:
            idx = header_real_val['header'].index(key)
            try:
                if key in header_real_val:
                    lines[idx] = str(tsv_dict[header_real_val[key]['infile']][i])
                elif key == 'Channel' and lines[idx] == 'n/a':
                    lines[idx] = chan
                elif key in name.keys() and lines[idx] == 'n/a':
                    lines[idx] = str(name[key])
                else:
                    continue
            except:
                continue
        if flag_not_inside:
            table2write.append(lines)

    return header_real_val


def write_table(table2write, filename, path, json_dict=None):
    if json_dict:
        if 'filename' in json_dict:
            file, ext = os.path.splitext(json_dict['filename'])
            jsonfilename = file + '.json'
        else:
            jsonfilename = os.path.splitext(filename)[0] + '.json'
        if os.path.exists(jsonfilename) and os.path.getsize(jsonfilename) != 0:
            with open(jsonfilename, 'r') as file:
                exist_dict = json.load(file)
                file.close()
        else:
            exist_dict = {key: '' for key in ['Description', 'RawSources', 'Parameters', 'Author', 'Date']}
            exist_dict['Date'] = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        with open(jsonfilename, 'w') as f:
            if 'Parameters' not in exist_dict.keys():
                exist_dict['Parameters'] = json_dict
            else:
                if isinstance(exist_dict['Parameters'], dict):
                    for clef, val in json_dict.items():
                        exist_dict['Parameters'][clef] = val
                else:
                    exist_dict['Parameters'] = json_dict
            json_str = json.dumps(exist_dict, indent=1, separators=(',', ': '), ensure_ascii=False, sort_keys=False)
            f.write(json_str)
    #write tsv file
    if path not in filename:
        tsvfilename = os.path.join(path, filename)
    else:
        tsvfilename = filename
    with open(tsvfilename, 'w') as file:
        for lines in table2write:
            file.write('\t'.join(lines) + '\n')


def write_file_after_convert(json_dict, tsv_dict):
    log_error = ''
    filename = os.path.splitext(json_dict['filename'])[0] + '.tsv'
    path = os.path.dirname(filename)
    flag_multifile = all(isinstance(key, int) for key in tsv_dict.keys())
    key2remove = []
    if flag_multifile:
        for i in tsv_dict:
            for key in tsv_dict[i]:
                if key.lower() in __channel_name__ and all(isinstance(elt, str) for elt in tsv_dict[i][key]):
                    channel = tsv_dict[i][key]
                    key2remove.append(key)
            if not key2remove:
                continue
            try:
                table2write = [[]]
                header = create_table(tsv_dict[i], channel, key2remove, table2write)
                if 'filename' in json_dict[i]:
                    filename = os.path.splitext(json_dict[i]['filename'])[0] + '.tsv'
                else:
                    filename = os.path.splitext(filename)[0] + '_run-' + str(i) + '.tsv'
                if table2write[0] != ['Channel'] and len(table2write) > 1:
                    write_table(table2write, filename, path, json_dict=json_dict[i])
                else:
                    log_error += 'The table for the file {} cannot be created.\n'.format(json_dict['filename'])
                    filenmae = None
            except:
                log_error += 'The table for the file {} cannot be created.\n'.format(json_dict['filename'])
                filename = None

    else:
        table2write = [[]]
        for key in tsv_dict:
            if key.lower() in __channel_name__ and all(isinstance(elt, str) for elt in tsv_dict[key]):
                channel = tsv_dict[key]
                key2remove.append(key)
        try:
            header = create_table(tsv_dict, channel, key2remove, table2write)
            if table2write[0] != ['Channel'] and len(table2write) > 1:
                write_table(table2write, filename, path, json_dict)
            else:
                log_error += 'The table for the file {} cannot be created.\n'.format(json_dict['filename'])
                filename = None
        except:
            log_error += 'The table for the file {} cannot be created.\n'.format(json_dict['filename'])
            filename = None
    return log_error, filename


def convert_channels_in_montage_file(channelfile, modalitytype, outdirname=None):
    err = ''
    dirname, filename = os.path.split(channelfile)
    f = open(channelfile, 'r')
    f_cont = f.readlines()
    f.close()
    if modalitytype.lower() in ['ieeg', 'eeg']:
        newfilename = filename.replace('channels.tsv', modalitytype.lower() + '.vhdr.mtg')
    elif modalitytype.lower() in ['meg']:
        megdirname = os.path.join(dirname, filename.replace('channels.tsv', modalitytype.lower()))
        if os.path.exists(megdirname):
            dirname = megdirname
            newfilename = 'c,rfDC.mtg'
        else:
            err += 'Cannot create the montage file for {} modality.\n'.format(modalitytype)
            return err
    if outdirname is not None:
        dirname=outdirname
    mtgfile = os.path.join(dirname, newfilename)
    if not os.path.exists(mtgfile):
        with open(mtgfile, 'w') as file:
            file.write('<!DOCTYPE AnyWaveMontage>\n<Montage>\n')
            for line in f_cont[1::]:
                sline = line.split('\t')
                channame = sline[0]
                modtype = sline[1]
                file.write('\t<Channel name="{}">\n\t\t<type>{}</type>\n\t\t<reference></reference>\n\t\t<color>black</color>\n\t</Channel>\n'.format(channame, modtype))
            file.write('</Montage>')
    return err


def convert_events_in_marker_file(eventfile, modalitytype, outdirname=None):
    err = ''
    dirname, filename = os.path.split(eventfile)
    if eventfile.endswith('.tsv'):
        json_dict, tsv_dict = read_tsv(eventfile)
    elif eventfile.endswith('.vmrk'):
        newfilename = filename.replace('.vmrk', '.vhdr.mrk')
        json_dict, tsv_dict = read_vmrk(eventfile)
    else:
        err = 'The file format of {} is not supported'.format(filename)
        return err
    if modalitytype.lower() in ['ieeg', 'eeg']:
        newfilename = filename.replace('events.tsv', modalitytype.lower() + '.vhdr.mrk')
    elif modalitytype.lower() in ['meg']:
        megdirname = os.path.join(dirname, filename.replace('events.tsv', modalitytype.lower()))
        if os.path.exists(megdirname):
            dirname = megdirname
            newfilename = 'c,rfDC.mrk'
        else:
            err += 'Cannot create the marker file for {} modality.\n'.format(modalitytype)
            return err
    if outdirname is not None:
        dirname = outdirname
    mrkfile = os.path.join(dirname, newfilename)
    if not os.path.exists(mrkfile):
        with open(mrkfile, 'w') as file:
            file.write('// AnyWave Marker File\n')
            for cnt, elt in enumerate(tsv_dict['trial_type']):
                file.write('{0}\t-1\t{1}\t{2}\n'.format(elt, tsv_dict['onset'][cnt], tsv_dict['duration'][cnt]))
    return err
