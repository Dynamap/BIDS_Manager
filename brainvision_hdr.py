#!/usr/bin/python3

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
#     Authors: Nicolas Roehri, 2018-2019

import os
import re


class BrainvisionHeader(object):

    hdr_ext = '.vhdr'
    data_tag = '[Channel Infos]'
    expr = r'(?P<channel>Ch\d{1,3}=)(?P<label>.*?)(?P<num>\d{0,3}),'
    expr2besub = [r'(?P<channel>Ch\d{1,3}=)(?P<label>', r')(?P<num>\d{0,3}),']
    expr2sub = r''

    def __init__(self, filename=None):
        self.header = []
        self.channel_list = []
        self.electrode_list = []
        self.electrode_set = {}
        self.data_section = []
        self.filename = filename
        if self.filename:
            self.read_header()

    def read_header(self):
        if os.path.isfile(self.filename) and os.path.splitext(self.filename)[1] == self.hdr_ext:
            with open(self.filename, 'r') as file:
                for line in file:
                    self.header.append(line)
            self.fill_data_section()
        else:
            raise FileNotFoundError(self.filename + ' was not found.')

    def fill_data_section(self):
        data_sect_starts = self.header.index(self.data_tag + '\n') + 1
        data_sect_ends = len(self.header)
        self.data_section = self.header[data_sect_starts:data_sect_ends]
        """search for expression that starts with 'Ch', is followed by one to three digits and '=' and finishes with a 
        comma. The first group is alphanumeric and the second can be made of  three digits"""
        self.channel_list.clear()
        self.electrode_list.clear()
        self.electrode_set.clear()

        for line in self.data_section:
            m = re.search(self.expr, line)
            self.channel_list.append(m['label'] + m['num'])
            self.electrode_list.append(m['label'])
        self.electrode_set = set(self.electrode_list)

    def modify_header(self, orig_name, new_name):
        def repl(m):
            return m['channel'] + new_name + m['num'] + ','

        if orig_name not in self.electrode_set:
            raise NameError(orig_name + ' electrode is not found in ' + self.filename + '.')
        for cnt, line in enumerate(self.header):
            line = re.sub(self.expr2besub[0] + orig_name + self.expr2besub[1], repl, line)
            self.header[cnt] = line
        self.fill_data_section()

    def write_header(self):
        if os.path.isfile(self.filename) and os.path.splitext(self.filename)[1] == self.hdr_ext:
            # with open(self.filename.replace('.vhdr', '_test.vhdr'), 'w') as file:
            with open(self.filename, 'w') as file:
                for line in self.header:
                    file.write(line)


if __name__ == '__main__':
    # bv_path = r'F:\Users\Nico\Documents\Marseille\PHRC\small_2048_4test\sub-PaiJul\ses-01\ieeg\sub-PaiJul_ses-01_task-seizure_run-01_ieeg.vhdr'
    bv_path = r'D:\roehri\BIDs\small_2048_test\sub-PaiJul\ses-01\ieeg\sub-PaiJul_ses-01_task-seizure_run-01_ieeg.vhdr'
    bv_hdr = BrainvisionHeader(bv_path)
    print(bv_hdr.electrode_set)
    old_name = bv_hdr.electrode_list[0]
    bv_hdr.modify_header(old_name, "WWW")
    bv_hdr.write_header()
    print(bv_hdr.electrode_set)
    bv_hdr.modify_header("WWW", old_name)
    bv_hdr.write_header()
    # bv_hdr.write_header()
