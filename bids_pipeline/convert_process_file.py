import os
from scipy.io import loadmat
from numpy import ndarray
import json
import xlrd
from datetime import datetime

#variables used in all script
__modality_type__ = ['ieeg', 'eeg', 'meg', 'beh'] #'anat', 'pet', 'func', 'fmap', 'dwi',
__channel_name__ = ['channel', 'channels', 'electrode_name', 'electrodes_name', 'electrode_names', 'label', 'labels']


def go_throught_dir_to_convert(dirname):
    log_error=''
    tmp_list = []
    if not os.path.exists(dirname):
        raise ('The directroy doesn"t exists')
    with os.scandir(dirname) as it:
        for entry in it:
            if (entry.name.startswith('sub-') or entry.name.startswith('ses-')) and entry.is_dir():
                log_error, tsv_list = go_throught_dir_to_convert(entry.path)
                tmp_list.extend(tsv_list)
            elif entry.name in __modality_type__ and entry.is_dir():
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
                        json_dict, tsv_dict = convert_mat_file(filename)
                        log_error, tsv_file = write_file_after_convert(json_dict, tsv_dict)
                        tmp_list.append(os.path.join(entry.path, tsv_file))
                    return log_error, tmp_list
                elif ('.xls' and '.xlsx') in ext_list:
                    xls_file = [file for file in file_list if '.xls' in file]
                    tmp_list = []
                    for file in xls_file:
                        filename = os.path.join(entry.path, file)
                        json_dict, tsv_dict = convert_xls_file(filename)
                        log_error, tsv_file = write_file_after_convert(json_dict, tsv_dict)
                        tmp_list.append(os.path.join(entry.path, tsv_file))
                    return log_error, tmp_list
                else:
                    log_error += 'Files presents in this software cannot be converted.\n'
    return log_error, tmp_list


def parse_derivatives_folder(folder, table2write, table_attributes, folder_out=None, derivatives_folder=None):
    dev_folder = None
    if derivatives_folder:
        dev_folder = derivatives_folder
    log_error = ''
    if folder_out is not None:
        folder_out = folder_out + ['log', 'log_old', 'parsing', 'parsing_old']
    else:
        folder_out = ['log', 'log_old', 'parsing', 'parsing_old']
    header = None
    with os.scandir(folder) as it:
        for entry in it:
            if entry.name not in folder_out and entry.is_dir():
                #Find the software name:
                soft_name = entry.path.split(dev_folder)[1]
                soft_name = soft_name.split('\\')[1]
                error, file_list = go_throught_dir_to_convert(entry.path)
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


def write_big_table(derivatives_folder, folder_out=None):
    #before write_table
    table2write = [[]]
    table_attributes = [[]]
    table_attributes[0] = ['sub']
    log_error = parse_derivatives_folder(derivatives_folder, table2write, table_attributes, folder_out, derivatives_folder=derivatives_folder)
    if not len(table2write) == len(table_attributes):
        print('ERROR')
    else:
        final_table = [None] * len(table2write)
        head_length = len(table2write[0])
        head_att = len(table_attributes[0])
        for i in range(0, len(table2write), 1):
            l_tw = len(table2write[i])
            l_ta = len(table_attributes[i])
            if l_tw != head_length:
                for n in range(l_tw, head_length, 1):
                    table2write[i].append('n/a')
            if l_ta != head_att:
                for n in range(l_ta, head_att, 1):
                    table_attributes[i].append('n/a')
            if final_table[i] is None:
                final_table[i] = []
            final_table[i].extend(table_attributes[i])
            final_table[i].extend(table2write[i])
    filename = 'statistical_table.tsv'
    write_table(final_table, filename, derivatives_folder)
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
        all_true = []
        last_elt = nbr[0]
        for elt in nbr[1:]:
            if elt == last_elt +1:
                all_true.append(True)
            else:
                all_true.append(False)
            last_elt = elt
        if all(all_true):
            return True
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
        for lines in worksheet._cell_values[jj:]:
            if not all(elt == '' for elt in lines):
                for cnt, elt in enumerate(lines):
                    if cnt < len(tmp_dict):
                        if tmp_dict[cnt] == 'DOB' and elt != '':
                            dob = datetime.strptime(elt, '%d\%m\%Y')
                            elt = dob.strftime('%d%m%Y')
                        tsv_tmp_dict[tmp_dict[cnt]].append(elt)
            else:
                idx = worksheet._cell_values.index(lines) + 1
                for line in worksheet._cell_values[idx::]:
                    if not all(elt == '' for elt in line):
                        count = sum(1 for e in line if e != '')
                        if count % 2 == 0:
                            for j in range(0, ncol, 2):
                                if line[j] and j+1 < ncol:
                                    json_dict[i][line[j]] = line[j+1]
                #break
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
    file = open(filename, 'r+')
    data = file.readlines()
    data = [line.replace('\n', '') for line in data]
    header = data[0].split('\t')
    tsv_dict = {key: [] for key in header}
    for lines in data[1::]:
        line = lines.split('\t')
        for key in header:
            idx = header.index(key)
            tsv_dict[key].append(line[idx])

    return json_dict, tsv_dict


def create_table(tsv_dict, channel, key2remove, table2write, header_real_val=None, table_attributes=None, file=None, soft_analysis=None):
    if header_real_val is None:
        header_real_val = {'header': table2write[0]}
    name = {}
    id_same_file = None
    if soft_analysis:
        soft = soft_analysis + '_'
    else:
        soft = ''
    if 'Channel' not in header_real_val['header']:
        header_real_val['header'].insert(0, 'Channel')
    for key in tsv_dict:
        if key not in key2remove and soft + key.replace(' ', '_') not in header_real_val['header'] and len(tsv_dict[key]) == len(channel) and key != '':
            new_key = soft + key.replace(' ', '_')
            header_real_val['header'].append(new_key)
            header_real_val[new_key] = key
        # create_attributes_table
    if table_attributes:
        name_list = os.path.basename(file).split('_')
        name = {elt.split('-')[0]: elt.split('-')[1] for elt in name_list if '-' in elt}
        headatt = table_attributes[0]
        for key in name:
            if key not in headatt:
                headatt.append(key)
        lines_att = ['n/a'] * len(headatt)
        for key in headatt:
            ida = headatt.index(key)
            if key in name:
                lines_att[ida] = name[key]
        if lines_att in table_attributes:
            id_same_file = table_attributes.index(lines_att)
    for i in range(0, len(channel), 1):
        chan = channel[i]
        id_chan = header_real_val['header'].index('Channel')
        flag_not_inside = True
        lines = None
        if id_same_file is not None:
            for j in range(id_same_file, id_same_file + len(channel), 1):
                if table2write[j][id_chan] == chan:
                    lines = table2write[j]
                    flag_not_inside = False
                    break
            if lines is None:
                flag_not_inside = True
                lines = ['n/a'] * len(header_real_val['header'])
                #table_attributes.append(lines_att)
            elif len(lines) != len(header_real_val['header']):
                for n in range(len(lines), len(header_real_val['header']), 1):
                    lines.append('n/a')
        else:
            lines = ['n/a'] * len(header_real_val['header'])
        for key in header_real_val['header']:
            idx = header_real_val['header'].index(key)
            if key in header_real_val:
                key_sub = header_real_val[key]
            elif key == 'Channel':
                key_sub = key
            else:
                continue
            if key_sub in tsv_dict.keys():
                lines[idx] = str(tsv_dict[key_sub][i])
            elif key_sub in name.keys():
                lines[idx] = str(name[key_sub])
            elif key == 'Channel':
                lines[idx] = chan
        if flag_not_inside:
            table2write.append(lines)
            if table_attributes:
                table_attributes.append(lines_att)

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
            except:
                log_error += 'The table for the file {} cannot be created.\n'.format(json_dict['filename'])

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
        except:
            log_error += 'The table for the file {} cannot be created.\n'.format(json_dict['filename'])
    return log_error, filename
