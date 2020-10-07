#!/usr/bin/python3
# -*-coding:Utf-8 -*

#     BIDS Manager collect, organise and manage data in BIDS format.
#     Copyright © 2018-2020 Aix Marseille University, INSERM, INS
#
#     This file is part of BIDS Manager. This file generates/manages the graphical
#     interface of BIDS Manager
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

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from builtins import super
from builtins import round
from builtins import range
from builtins import dict
from builtins import str
from builtins import object
from future import standard_library
from bids_manager import ins_bids_class as bids
import os
import platform
from generic_uploader.generic_uploader import call_generic_uplader
from tkinter import ttk, Tk, Menu, messagebox, filedialog, Frame, Listbox, scrolledtext, Toplevel, \
    Label, Button, Entry, StringVar, IntVar, DISABLED, NORMAL, END, W, N, E, BOTH, X, Y, RIGHT, LEFT,\
    TOP, BOTTOM, BROWSE, MULTIPLE, EXTENDED, ACTIVE, RIDGE, Scrollbar, CENTER, OptionMenu, Checkbutton, Radiobutton, GROOVE, \
    Canvas, font
from ctypes import windll
try:
    from importlib import reload
except:
    pass
standard_library.install_aliases()


class BidsManager(Frame, object):  # !!!!!!!!!! object is used to make the class Py2 compatible
    # (https://stackoverflow.com/questions/18171328/python-2-7-super-error) While it is true that Tkinter uses
    # old-style classes, this limitation can be overcome by additionally deriving the subclass Application from object
    # (using Python multiple inheritance) !!!!!!!!!
    version = '0.2.6'
    bids_startfile = ''
    import_startfile = ''

    def __init__(self, root, monitor_width, monitor_height):
        super().__init__()
        self.monitor_width = monitor_width
        self.monitor_height = monitor_height
        self.master.title("BidsManager " + BidsManager.version)
        self.master.geometry("500x500")
        self.bids_startfile = BidsManager.bids_startfile
        self.import_startfile = BidsManager.import_startfile

        self.curr_bids = None
        self.curr_data2import = None
        self.curr_import_folder = None
        self.bids_dir = None
        self.upload_dir = None
        self.main_frame = dict()
        self.root = root
        # make menu
        menu_bar = Menu(self.master)
        self.root['menu'] = menu_bar
        # settings menu
        bids_menu = Menu(menu_bar, tearoff=0)
        self.bids_menu = bids_menu
        uploader_menu = Menu(menu_bar, tearoff=0)
        self.uploader_menu = uploader_menu
        # bids_menu = Menu(menu_bar, tearoff=0)
        # self.bids_menu = bids_menu
        issue_menu = Menu(menu_bar, tearoff=0)
        self.issue_menu = issue_menu
        about_menu = Menu(menu_bar, tearoff=0)
        self.about_menu = about_menu
        # pipeline_menu = Menu(menu_bar, tearoff=0)
        # self.pipeline_menu = pipeline_menu
        # fill up the bids menu
        bids_menu.add_command(label='Create new BIDS directory', command=lambda: self.ask4bidsdir(True))
        bids_menu.add_command(label='Set BIDS directory', command=self.ask4bidsdir)
        bids_menu.add_command(label='Refresh BIDS dataset', command=self.refresh, state=DISABLED)
        bids_menu.add_command(label='Show current log', command=lambda: self.show_logs(),
                              state=DISABLED)
        bids_menu.add_command(label='Show previous logs', command=lambda: self.show_logs(all=True), state=DISABLED)
        bids_menu.add_command(label='Show dataset_description.json', state=DISABLED)
        bids_menu.add_command(label='Explore Bids dataset', state=DISABLED)
        bids_menu.add_command(label='Modify requirements file', command=self.modify_requirements_file, state=DISABLED)
        # fill up the upload/import menu
        uploader_menu.add_command(label='Import data with BIDS Uploader', command=self.ask4uploader_import, state=DISABLED)
        uploader_menu.add_command(label='Set Upload directory', command=self.ask4upload_dir, state=DISABLED)
        uploader_menu.add_command(label='Add elements to import', command=self.add_elmt2data2import, state=DISABLED)
        uploader_menu.add_command(label='Import', command=self.import_data, state=DISABLED)
        # fill up the issue menu
        issue_menu.add_command(label='Verify upload folder content',
                               command=lambda: self.solve_issues('UpldFldrIssue'), state=DISABLED)
        issue_menu.add_command(label='Solve importation issues',
                               command=lambda: self.solve_issues('ImportIssue'), state=DISABLED)
        issue_menu.add_command(label='Solve channel issues',
                               command=lambda: self.solve_issues('ElectrodeIssue'), state=DISABLED)
        # fill up the about menu
        about_menu.add_command(label='License', command=self.read_license)
        about_menu.add_command(label='How to cite the paper', command=self.cite_paper)
        # fill up the pipeline menu
        # self.pipeline_settings = bids.PipelineSettings()
        # self.pipeline_settings.read_file()
        # for cnt, pipl in enumerate(self.pipeline_settings['Settings']):
        #     pipeline_menu.add_command(label=pipl['label'], command=lambda idx=cnt:
        # self.launch_pipeline(idx), state=DISABLED)
        # settings_menu.add_command(label='Exit', command=self.quit)
        menu_bar.add_cascade(label="BIDS", underline=0, menu=bids_menu)
        menu_bar.add_cascade(label="Uploader", underline=0, menu=uploader_menu)
        menu_bar.add_cascade(label="Issues", underline=0, menu=issue_menu)
        # menu_bar.add_cascade(label="Pipelines", underline=0, menu=pipeline_menu)
        menu_bar.add_cascade(label='About', underline=0, menu=about_menu)

        # area to print logs
        self.main_frame['text'] = DisplayText(master=self.master)

        # area to print lists
        self.main_frame['list'] = Listbox(master=self.master, font=("Arial", 12))

        # area to print double linked list
        self.main_frame['double_list'] = IssueList(self.master, self.apply_actions, self.delete_actions)

        # little band to print small infos
        self.banner_label = StringVar()
        self.banner_label.set('Please set/create a Bids directory')
        self.banner_color = StringVar()
        self.banner = Label(self.master, textvariable=self.banner_label, bg="blue", fg="white", font=("Arial", 15))
        self.banner.pack(fill=X, side=TOP)
        # self.pack_element(self.main_frame['text'])
        # self.update_text('\n'.join(make_splash()))

    # def launch_pipeline(self, idx):
    #     pass
    #     # self.pipeline_settings.propose_param(self.curr_bids, idx)
    #     # self.curr_bids.write_log('Launching: ' + self.pipeline_settings['Settings'][idx]['label']
    #     #  + '(to be set!!!!!)')

    def pack_element(self, element, side=None, remove_previous=True):

        if not element.winfo_ismapped():

            if side not in [TOP, BOTTOM, LEFT, RIGHT]:
                side = None

            if remove_previous:
                for widget_name in self.main_frame:
                    if self.main_frame[widget_name].winfo_ismapped():
                        self.main_frame[widget_name].pack_forget()
            if isinstance(element, DoubleListbox):
                element.pack_elements()
            else:
                element.pack(fill=BOTH, expand=1, side=side, padx=5, pady=5)

    def update_text(self, str2show, delete_flag=True, location=None):
        if str2show and not str2show.endswith('\n'):
            str2show = str2show + '\n'
        self.main_frame['text'].update_text(str2show, delete_flag=delete_flag, location=location)
        self.update()

    def apply_actions(self):
        flag = messagebox.askyesno('Apply all actions', 'Are you sure you want to apply actions of all issues?')
        import_data_flag = any(self.curr_bids.issues[key] for key in ['UpldFldrIssue', 'ImportIssue'])
        #upload_dir = [elt['path'] for elt in self.curr_bids.issues['UpldFldrIssue'] + self.curr_bids.issues['ImportIssue']]
        if flag:
            self.make_idle('Appling actions')
            self.curr_bids.apply_actions()
            if self.upload_dir:
                self.curr_data2import = bids.Data2Import(self.upload_dir)
            self.update_text(self.curr_bids.curr_log)
            self.pack_element(self.main_frame['text'])
            self.make_available()
        if import_data_flag:
            flag_import = False
            upload_dir = [os.path.normpath(elt['path']) for elt in self.curr_bids.issues['UpldFldrIssue'] + self.curr_bids.issues['ImportIssue']]
            upload_dir = list(set(upload_dir))
            if len(upload_dir) > 1 or (len(upload_dir) == 1 and os.path.normpath(self.upload_dir) != upload_dir[0]):
                if self.upload_dir is not None and self.upload_dir not in upload_dir:
                    upload_dir.append(self.upload_dir)
                self.upload_dir = None
                small_win = SmallDialog(self, upload_dir, 'Do you want to import data?', 'Select the upload directory:')
                if small_win.results:
                    flag_import = small_win.results['flag']
                    self.upload_dir = small_win.results['value']
            elif len(upload_dir) == 1:
                flag_import = messagebox.askyesno('Import data',
                                                  'Do you want to import the data from {} directory?'.format(
                                                      os.path.basename(upload_dir[0])))
                self.upload_dir = upload_dir[0]
            if flag_import:
                self.curr_data2import = bids.Data2Import(self.upload_dir)
                self.import_data()

    def delete_actions(self):
        flag = messagebox.askyesno('DELETE All Actions', 'Are you sure you want to DELETE all planned actions?')
        if flag:
            for issue_type in self.curr_bids.issues:
                for issue in self.curr_bids.issues[issue_type]:
                    issue['Action'] = []
            issue_list = self.main_frame['double_list'].elements['list1']
            action_list = self.main_frame['double_list'].elements['list2']
            for list_idx in range(0, action_list.size()-1):
                action_list.delete(list_idx)
                action_list.insert(list_idx, '')
                issue_list.itemconfig(list_idx, foreground='black')
            info_str = 'All actions were deleted'
            self.curr_bids.write_log(info_str)
            self.curr_bids.issues.save_as_json()
            messagebox.showinfo('Delete actions', info_str)

    def add_elmt2data2import(self):
        self.curr_data2import._assign_import_dir(self.curr_data2import.dirname)
        self.curr_data2import.save_as_json(write_date=True)
        results = BidsBrickDialog(self.root, self.curr_data2import,
                                  disabled=self.curr_data2import['DatasetDescJSON'].keylist,
                                  title=self.curr_data2import.classname()).apply()
        if results is not None and messagebox.askyesno('Change ' + self.curr_data2import.classname() + '?',
                                                       'You are about to permanently modify ' +
                                                       self.curr_data2import.classname() + '.\nAre you sure?'):
            self.curr_data2import.save_as_json()
            if self.curr_data2import.is_empty():
                self.update_text('There is no file to import in ' + self.upload_dir)
                self.upload_dir = None
                self.curr_data2import = None
            else:
                self.curr_bids.make_upload_issues(self.curr_data2import)
                self.solve_issues('UpldFldrIssue')
            # self.update_text(self.curr_data2import)

    def show_logs(self, all=False):
        if self.curr_bids:
            if all:
                logs_str = self.curr_bids.get_all_logs()
                self.update_text(logs_str)
            else:
                self.update_text(self.curr_bids.curr_log)
            self.pack_element(self.main_frame['text'])

    def refresh(self):
        self.pack_element(self.main_frame['text'])
        self.make_idle('Parsing BIDS directory.')
        self.curr_bids._assign_bids_dir(self.curr_bids.dirname)
        try:
            if self.curr_bids:
                self.curr_bids.parse_bids()
                self.update_text(self.curr_bids.curr_log)
        except Exception as err:
            self.banner_label._default = 'Please set/create a Bids directory'
            self.curr_bids = None
            self.change_menu_state(self.bids_menu, start_idx=2, state=DISABLED)
            self.change_menu_state(self.uploader_menu, state=DISABLED)
            self.change_menu_state(self.issue_menu, state=DISABLED)
            self.update_text(str(err))
        self.make_available()

    @staticmethod
    def populate_list(list_object, input_list):
        for item in input_list:
            list_object.insert(END, item)

    def show_bids_desc(self, input_dict):

        if isinstance(input_dict, bids.BidsBrick):
            output_dict = FormDialog(self.root, input_dict,
                                     required_keys=input_dict.required_keys,
                                     title='Fill up the ' + input_dict.__class__.__name__ + 'attributes').apply()
        elif isinstance(input_dict, bids.DatasetDescJSON):
            messagebox.showwarning('Warning !!', 'If you change the Name of the dataset, it will change the anonymisation key!')
            temp_dict = input_dict.__class__()
            temp_dict.copy_values(input_dict, simplify_flag=False)
            output_dict = FormDialog(self.root, temp_dict,
                                     required_keys=input_dict.required_keys,
                                     title='Fill up the ' + input_dict.__class__.filename).apply()
            if output_dict:
                if 'Authors' in output_dict:
                    # tkinter modifies the author list ['NR' , 'FB', 'CGB'] into a string '{NR} {FB} {CGB}'
                    tmp_str = output_dict['Authors'].replace('} {', ', ')
                    tmp_str = tmp_str.replace('{', '').replace('}', '')
                    output_dict['Authors'] = tmp_str
                if not output_dict == temp_dict and \
                        messagebox.askyesno('Change ' + input_dict.__class__.filename + '?',
                                            'You are about to modify ' + input_dict.__class__.filename +
                                            '.\nAre you sure?'):
                    input_dict.copy_values(output_dict)
                    input_dict.write_file()
                    self.curr_bids.save_as_json()

    @staticmethod
    def change_menu_state(menu, start_idx=0, end_idx=None, state=None):
        if state is None or state not in [NORMAL, DISABLED]:
            state = NORMAL
        if end_idx is None:
            end_idx = menu.index(END)
            if end_idx is None:
                return
        if end_idx and end_idx > menu.index(END):
            raise IndexError('End index is out of range (' + str(end_idx) + '>' + str(menu.index(END)) + ').')
        if start_idx > end_idx:
            raise IndexError('Start index greater than the end index (' + str(start_idx) + '>' + str(end_idx) + ').')
        for i in range(start_idx, end_idx+1):
            menu.entryconfigure(i, state=state)

    def ask4bidsdir(self, isnew_dir=False):
        """Either set (isnew_dir = False) or create Bids directory (isnew_dir=True)"""

        def create_new_bidsdataset(parent, bids_dir):
            error_str = ''
            if os.listdir(bids_dir):
                error_str += 'The folder is not empty!'
                return error_str
            # create a dataset description file
            datasetdesc = bids.DatasetDescJSON()
            output_dict = FormDialog(self.root, datasetdesc,
                                     required_keys=bids.DatasetDescJSON.required_keys,
                                     title='Fill up the ' + bids.DatasetDescJSON.filename).apply()
            if output_dict:
                datasetdesc.copy_values(output_dict)
                datasetdesc.has_all_req_attributes()
            if not datasetdesc.is_complete and \
                    datasetdesc['Name'] == bids.DatasetDescJSON.bids_default_unknown:
                error_str += bids.DatasetDescJSON.filename + ' needs at least these elements: ' + \
                            str(bids.DatasetDescJSON.required_keys) + 'to be filled.'
                return error_str
            # Select type of requirements
            error_str = RequirementsDialog(parent, bids_dir).error_str
            if not error_str:
                datasetdesc.write_file()

            return error_str


        def check_access():
            if os.path.isfile(self.curr_bids.access.filename):
                acss = bids.Access()
                acss.read_file(self.curr_bids.access.filename)
            else:
                acss = False
                self.curr_bids.access.write_file()
            return acss

        bids_dir = filedialog.askdirectory(title='Please select a BIDS dataset directory',
                                           initialdir=self.bids_startfile)
        if not bids_dir:
            return
        self.bids_startfile = bids_dir
        reload(bids)
        self.pack_element(self.main_frame['text'])
        self.upload_dir = None
        self.curr_data2import = None
        self.update_text('')
        if self.curr_bids:
            self.curr_bids.access.delete_file()
            self.curr_bids = None
        if isnew_dir:
            # if new bids directory than create dataset_desc.json and but the requirements in code
            error_str = create_new_bidsdataset(self, bids_dir)
            if error_str:
                messagebox.showerror('Error', error_str)
                self.change_menu_state(self.uploader_menu, state=DISABLED)
                self.change_menu_state(self.issue_menu, state=DISABLED)
                return
            else:
                self.curr_bids = bids.BidsDataset(bids_dir, update_text=self.update_text)
        else:
            ''' if bids directory already exits, check if there is a dataset_description.json otherwise stop 
            (it should be present to avoid nesting bids dir unintentionally)'''
            if os.path.isfile(os.path.join(bids_dir, bids.DatasetDescJSON.filename)):

                self.banner_label._default = 'Current BIDS directory: ' + bids_dir
                self.make_idle('Parsing BIDS directory.')
                try:
                    self.curr_bids = bids.BidsDataset(bids_dir, update_text=self.update_text)
                except NameError as error_str:
                    messagebox.showerror('Error', error_str)
                    self.change_menu_state(self.uploader_menu, state=DISABLED)
                    self.change_menu_state(self.issue_menu, state=DISABLED)
                    self.make_available()
                    return
                access = check_access()
                if access:
                    messagebox.showerror('Error', access.display())
                    self.banner_label._default = 'Please set/create a Bids directory'
                    self.curr_bids = None
                    self.change_menu_state(self.uploader_menu, state=DISABLED)
                    self.change_menu_state(self.issue_menu, state=DISABLED)
                    self.make_available()
                    return

            else:
                self.change_menu_state(self.uploader_menu, state=DISABLED)
                self.change_menu_state(self.issue_menu, state=DISABLED)
                self.update_text('Error: No ' + bids.DatasetDescJSON.filename + ' was found. Please set a correct ' +
                                 'path to a BIDS directory or create a new one.')
                return

        self.curr_bids.get_requirements()
        # enable all bids sub-menu
        self.change_menu_state(self.bids_menu)
        self.bids_menu.entryconfigure(5, command=lambda: self.show_bids_desc(self.curr_bids['DatasetDescJSON']))
        self.bids_menu.entryconfigure(6, command=self.explore_bids_dataset)
        # enable selection of upload directory
        self.change_menu_state(self.uploader_menu, end_idx=1)
        # enable all issue sub-menu
        self.change_menu_state(self.issue_menu)
        # enalbe all pipelines
        #self.change_menu_state(self.pipeline_menu)
        # self.update_text(self.curr_bids.curr_log)
        self.make_available()

    def explore_bids_dataset(self):
        self.pack_element(self.main_frame['text'])
        BidsBrickDialog(self, self.curr_bids)
        self.curr_bids.save_as_json()

    def ask4upload_dir(self):
        self.pack_element(self.main_frame['text'])
        self.upload_dir = filedialog.askdirectory(title='Please select a upload/import directory',
                                                  initialdir=self.import_startfile)
        if not self.upload_dir:
            return
        self.import_startfile = self.upload_dir
        self.make_idle()
        try:
            if os.path.isfile(os.path.join(self.upload_dir, bids.Data2Import.filename)):
                req_path = os.path.join(self.curr_bids.dirname, 'code', 'requirements.json')
                self.curr_data2import = bids.Data2Import(self.upload_dir, req_path)
                if self.curr_data2import.is_empty():
                    self.update_text('There is no file to import in ' + self.upload_dir)
                    self.upload_dir = None
                    self.curr_data2import = None
                else:
                    self.change_menu_state(self.uploader_menu)
                    self.curr_bids.make_upload_issues(self.curr_data2import)
                    # self.update_text(self.curr_data2import.curr_log)
                    # self.update_text(self.curr_data2import, delete_flag=False)
                    self.solve_issues('UpldFldrIssue')
            else:
                self.update_text('Error: data2import.json not found in ' + self.upload_dir)
                self.upload_dir = None
                self.curr_data2import = None
                self.change_menu_state(self.uploader_menu, state=DISABLED, start_idx=1)

        except Exception as err:
            # exc_type, exc_obj, exc_tb = exc_info()
            # err_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            # self.write_log('Error type: ' + str(exc_type) + ', scriptname: ' + err_name + ', line number, ' + str(
            #     exc_tb.tb_lineno) + ': ' + str(err))
            self.update_text(str(err))
        self.make_available()

    def print_participants_tsv(self):
        self.pack_element(self.main_frame['text'])
        self.update_text(self.make_table(self.curr_bids['ParticipantsTSV']))

    def print_srcdata_tsv(self):
        self.pack_element(self.main_frame['text'])
        if self.curr_bids['SourceData'] and self.curr_bids['SourceData'][-1]['SrcDataTrack']:
            self.update_text(self.make_table(self.curr_bids['SourceData'][-1]['SrcDataTrack']))
        else:
            self.update_text('Source Data Track does not exist')

    def update_issue_list(self, iss_ict, list_idx, info):
        if not isinstance(iss_ict, bids.IssueType):
            raise TypeError('First argument should be an instance of IssueType class.')
        issue_list = self.main_frame['double_list'].elements['list1']
        action_list = self.main_frame['double_list'].elements['list2']
        action_list.delete(list_idx)
        if info['IsAction']:
            action_list.insert(list_idx, iss_ict['Action'][-1].formatting())
            issue_list.itemconfig(list_idx, foreground='green')
        else:
            action_list.insert(list_idx, '')
            issue_list.itemconfig(list_idx, foreground='black')
        self.curr_bids.issues.save_as_json()

    def remove_file(self, list_idx, info, deriv_folder=None):
        flag = messagebox.askyesno('Remove file in BIDS', 'Are you sure that you want to remove ' +
                                   str(info['Element'].get_attributes('fileLoc')) + 'from BIDS ?')
        if flag:
            idx = info['index']
            curr_dict = self.curr_bids.issues['ImportIssue'][idx]
            fname, dirn, ext = info['Element'].create_filename_from_attributes()
            cmd = 'remove="' + fname + ext + '", in_bids=True'
            if deriv_folder:
                cmd += ' , in_deriv="' + deriv_folder + '"'
            curr_dict.add_action(desc='Remove element ' + str(info['Element'].get_attributes('fileLoc')) +
                                      ' from data to import.', command=cmd)
            info['IsAction'] = True
            self.update_issue_list(curr_dict, list_idx, info)

    def remove_issue(self, iss_key, list_idx, info):
        flag = messagebox.askyesno('Remove issue', 'Are you sure that you want to remove this issue?')
        if flag:
            idx = info['index']
            curr_dict = self.curr_bids.issues[iss_key][idx]
            cmd = 'remove_issue=True'
            curr_dict.add_action(desc='Remove issue from the list.', command=cmd)
            info['IsAction'] = True
            self.update_issue_list(curr_dict, list_idx, info)

    def do_not_import(self, iss_key, list_idx, info, deriv_folder=None):
        flag = messagebox.askyesno('Do Not Import', 'Are you sure that you do not want to import this element' +
                                   str(info['Element'].get_attributes()) + '?')
        if flag:
            idx = info['index']
            curr_dict = self.curr_bids.issues[iss_key][idx]
            make_cmd4pop(curr_dict, deriv_folder)
            info['IsAction'] = True
            self.update_issue_list(curr_dict, list_idx, info)

    def modify_attributes(self, iss_key, list_idx, info, in_bids=False, deriv_folder=None):
        elmt_brick = info['Element']
        input_dict, option_dict = prepare_chg_attr(elmt_brick, self.curr_bids, in_bids, deriv_folder)
        if input_dict is None:
            return
        output_dict = FormDialog(self, input_dict, options=option_dict,
                                 required_keys=elmt_brick.required_keys).apply()
        if output_dict and not output_dict == input_dict:
            idx = info['index']
            curr_dict = self.curr_bids.issues[iss_key][idx]
            make_cmd4chg_attr(curr_dict, elmt_brick, input_dict, output_dict, in_bids, deriv_folder)
            info['IsAction'] = True
            self.update_issue_list(curr_dict, list_idx, info)

    def select_correct_name(self, list_idx, info):

        idx = info['index']
        mismtch_elec = info['Element']
        curr_dict = self.curr_bids.issues['ElectrodeIssue'][idx]
        results = ListDialog(self.master, curr_dict['RefElectrodes'], 'Rename ' + mismtch_elec + ' as :').apply()
        if results:
            make_cmd4elecnamechg(results, curr_dict, mismtch_elec)
            info['IsAction'] = True
            self.update_issue_list(curr_dict, list_idx, info)

    def change_elec_type(self, list_idx, info):
        idx = info['index']
        mismtch_elec = info['Element']

        curr_dict = self.curr_bids.issues['ElectrodeIssue'][idx]
        # input_dict = {'type': mism_elec['type'] for mism_elec in curr_dict['MismatchedElectrodes']
        #               if mism_elec['name'] == mismtch_elec}
        # opt_dict = {'type': bids.Electrophy.channel_type}
        input_dict, opt_dict = prepare_chg_eletype(curr_dict, mismtch_elec)
        output_dict = FormDialog(self, input_dict, title='Modify electrode type of ' + mismtch_elec + ' into:',
                                 options=opt_dict, required_keys=input_dict).apply()
        if output_dict and not output_dict['type'] == input_dict['type']:
            str_info = 'Change electrode type of ' + mismtch_elec + ' from ' + input_dict['type'] + ' to ' + \
                       output_dict['type'] + ' in the electrode file related to ' + \
                       os.path.basename(curr_dict['fileLoc']) + '.\n'
            # self.pack_element(self.main_frame['text'], side=LEFT, remove_previous=False)
            # to fancy, used for others
            # command = ', '.join([str(k + '="' + output_dict[k] + '"') for k in output_dict])
            command = 'type="' + output_dict['type'] + '"'
            curr_dict.add_action(str_info, command, elec_name=mismtch_elec)
            make_cmd4electypechg(output_dict, input_dict, curr_dict, mismtch_elec)
            info['IsAction'] = True
            self.update_issue_list(curr_dict, list_idx, info)

    def get_entry(self, issue_key, list_idx, info):
        idx = info['index']
        if issue_key == 'ElectrodeIssue':
            mismtch_elec = info['Element']
        else:
            mismtch_elec = None
        curr_dict = self.curr_bids.issues[issue_key][idx]
        issue_list = self.main_frame['double_list'].elements['list1']
        prev_comm = '\n'.join(curr_dict.formatting(comment_type='Comment', elec_name=mismtch_elec))
        new_comments = CommentDialog(self.master, prev_comm).apply()
        if new_comments:
            curr_dict.add_comment(new_comments, elec_name=mismtch_elec)
            issue_list.itemconfig(list_idx, bg='yellow')
            self.curr_bids.issues.save_as_json()

    def cancel_action(self, issue_key, list_idx, info):
        idx = info['index']
        mismtch_elec = info['Element']
        curr_dict = self.curr_bids.issues[issue_key][idx]
        if issue_key == 'ElectrodeIssue':
            for action in curr_dict['Action']:
                if action['name'] == mismtch_elec:
                    curr_dict['Action'].pop(curr_dict['Action'].index(action))
                    info['IsAction'] = False
                    break  # there is only one action per channel so break when found
        elif curr_dict['Action']:
            curr_dict['Action'].pop(-1)
            info['IsAction'] = False
        self.update_issue_list(curr_dict, list_idx, info)

    def open_file(self, issue_key, list_idx, info):
        curr_iss = self.curr_bids.issues[issue_key][info['index']]
        if issue_key == 'ElectrodeIssue':
            os.startfile(os.path.normpath(os.path.join(self.curr_bids.dirname, curr_iss['fileLoc'])))
        else:
            os.startfile(os.path.normpath(os.path.join(curr_iss['path'], info['Element']['fileLoc'])))

    def mark_as_verified(self, list_idx, info, state_str):
        idx = info['index']
        curr_dict = self.curr_bids.issues['UpldFldrIssue'][idx]
        str_info = os.path.basename(info['Element']['fileLoc']) + ' will be marked as ' + state_str + '.'
        command = 'state="' + state_str + '"'
        curr_dict.add_action(str_info, command)
        info['IsAction'] = True
        self.update_issue_list(curr_dict, list_idx, info)

    def solve_issues(self, issue_key):

        def what2domenu(iss_key, dlb_lst, line_map, event, deriv_issue=None):

            if not dlb_lst.elements['list1'].curselection():
                return
            curr_idx = dlb_lst.elements['list1'].curselection()[0]

            pop_menu = Menu(self.master, tearoff=0)

            if iss_key == 'ElectrodeIssue':
                pop_menu.add_command(label='Open file',
                                     command=lambda: self.open_file(issue_key, curr_idx, line_map[curr_idx]))
                pop_menu.add_command(label='Change electrode name',
                                     command=lambda: self.select_correct_name(curr_idx, line_map[curr_idx]))
                pop_menu.add_command(label='Change electrode type',
                                     command=lambda: self.change_elec_type(curr_idx, line_map[curr_idx]))
            else:
                if isinstance(line_map[curr_idx]['Element'], bids.DatasetDescJSON):
                    # if issue arise from DatasetDescJSON change the DatasetDescJSON object in data2import.json
                    pop_menu.add_command(label='Modify ' + bids.DatasetDescJSON.filename + ' in current BIDS directory',
                                         command=lambda: self.modify_attributes(issue_key, curr_idx, line_map[curr_idx],
                                                                                in_bids=True, deriv_folder=deriv_issue))
                    pop_menu.add_command(label='Modify ' + bids.DatasetDescJSON.filename +
                                               ' in current Upload directory',
                                         command=lambda: self.modify_attributes(issue_key, curr_idx, line_map[curr_idx],
                                                                                in_bids=False, deriv_folder=deriv_issue))
                elif isinstance(line_map[curr_idx]['Element'], bids.BidsBrick):
                    if isinstance(line_map[curr_idx]['Element'], bids.Subject):
                        """
                        if issue arise from Subject, it means that its attributes are incomplete or wrong (e.g. age 
                        does not matched the age of this patient in bids dataset). One can either change the attributes
                        of the subject to be imported or the ones of the already imported subject (in participatns.tsv)
                        """
                        pop_menu.add_command(label='Change subject\'s attribute in ' + bids.Data2Import.filename,
                                             command=lambda: self.modify_attributes(issue_key, curr_idx,
                                                                                    line_map[curr_idx], in_bids=False))
                        pop_menu.add_command(label='Change subject\'s attribute in ' + bids.ParticipantsTSV.filename,
                                             command=lambda: self.modify_attributes(issue_key, curr_idx,
                                                                                    line_map[curr_idx], in_bids=True))
                    else:
                        """if issue arise from a modality, it means that the attributes of the modality are incomplete
                        or wrong and has to be changed according to the description or the file remove from the list of
                         file that will be imported"""
                        pop_menu.add_command(label='Open file',
                                             command=lambda: self.open_file(issue_key, curr_idx, line_map[curr_idx]))
                        pop_menu.add_command(label='Change modality attributes',
                                             command=lambda: self.modify_attributes(issue_key, curr_idx,
                                                                                    line_map[curr_idx], in_bids=False, deriv_folder=deriv_issue))
                        if iss_key == 'ImportIssue':
                            pop_menu.add_command(label='Remove file in BIDS',
                                                 command=lambda: self.remove_file(curr_idx, line_map[curr_idx], deriv_folder=deriv_issue))
                        else:
                            idx = line_map[curr_idx]['index']
                            curr_dict = self.curr_bids.issues['UpldFldrIssue'][idx]
                            if curr_dict['state'] == 'verified':
                                state_str = 'not verified'
                            else:
                                state_str = 'verified'
                                pop_menu.add_command(label='Mark as verified',
                                                     command=lambda: self.mark_as_verified(curr_idx, line_map[curr_idx],
                                                                                           state_str))

                    pop_menu.add_command(label='Do not import',
                                         command=lambda: self.do_not_import(issue_key, curr_idx, line_map[curr_idx], deriv_folder=deriv_issue))
                    # in case you wrongly chose a folder
                    pop_menu.add_command(label='Remove issue',
                                         command=lambda: self.remove_issue(issue_key, curr_idx,
                                                                           line_map[curr_idx]))

            pop_menu.add_command(label='Read or add comment',
                                 command=lambda: self.get_entry(issue_key, curr_idx, line_map[curr_idx]))
            pop_menu.add_command(label='Cancel action',
                                 command=lambda: self.cancel_action(issue_key, curr_idx, line_map[curr_idx]))
            pop_menu.post(event.x_root, event.y_root)

        dlb_list = self.main_frame['double_list']
        dlb_list.clear_list()
        self.pack_element(dlb_list)

        deriv_issue = None
        issue_dict = self.curr_bids.issues[issue_key]
        issue_list2write = []
        action_list2write = []
        line_mapping = []
        if issue_key == 'ElectrodeIssue':
            label_str = 'electrode issue'
            for issue in issue_dict:
                for mismatch_el in issue.list_mismatched_electrodes():
                    issue_list2write.append('In file ' + os.path.basename(issue['fileLoc']) + ' of subject ' +
                                            issue['sub'] + ', ' + mismatch_el +
                                            ' does not match electrodes.tsv reference.')
                    act_str = issue.formatting(comment_type='Action', elec_name=mismatch_el)

                    line_mapping.append({'index': issue_dict.index(issue), 'Element': mismatch_el,
                                         'IsComment': bool(issue.formatting(comment_type='Comment',
                                                                            elec_name=mismatch_el)),
                                         'IsAction': False})
                    if act_str:
                        action_list2write.append(act_str[0])
                        # you can write act_str[0] because there is only one action per channel
                        line_mapping[-1]['IsAction'] = True
                    else:
                        action_list2write.append('')
        elif issue_key == 'ImportIssue' or issue_key == 'UpldFldrIssue':
            if issue_key == 'ImportIssue':
                label_str = 'importation issue'
            else:
                label_str = 'upload folder issue'
            for issue in issue_dict:
                element = issue.get_element()
                if not element:
                    continue
                line_mapping.append({'index': issue_dict.index(issue), 'Element': element,
                                     'IsComment': bool(issue.formatting(comment_type='Comment')),
                                     'IsAction': False})
                if issue_key == 'ImportIssue':
                    issue_list2write.append(issue['description'])
                    if issue['description'].startswith('Derivatives folder'):
                        deriv_issue = issue['description'].split(' ')[2]
                else:
                    issue_list2write.append('sub-' + issue['sub'] + ' : ' + os.path.basename(issue['path']) + ' : ' + os.path.basename(issue['fileLoc']) + ' file is ' + issue['state'])
                    #issue_list2write.append('File: ' + os.path.basename(issue['fileLoc']) + ' is ' + issue['state'])
                act_str = issue.formatting(comment_type='Action')

                if act_str:
                    action_list2write.append(act_str[0])
                    # you can write act_str[0] because there is only one action per channel
                    line_mapping[-1]['IsAction'] = True
                else:
                    action_list2write.append('')
        else:
            messagebox.showerror('Unknown issue', 'This issue is currently not recognize')
            return

        self.populate_list(dlb_list.elements['list1'], issue_list2write)

        # set the colors according to the previously saved but not applied actions in issues.json
        for cnt, mapping in enumerate(line_mapping):
            if mapping['IsComment']:
                dlb_list.elements['list1'].itemconfig(cnt, bg='yellow')
            if mapping['IsAction']:
                dlb_list.elements['list1'].itemconfig(cnt, foreground='green')

        self.populate_list(dlb_list.elements['list2'], action_list2write)
        self.banner_label.set(self.banner_label._default + '\nSelect issue from the ' + label_str + ' list')
        dlb_list.elements['list1'].bind('<Double-Button-1>',
                                        lambda event: what2domenu(issue_key, dlb_list, line_mapping, event, deriv_issue))
        dlb_list.elements['list1'].bind('<Return>', lambda event: what2domenu(issue_key, dlb_list, line_mapping, event, deriv_issue))

    def import_data(self):
        self.pack_element(self.main_frame['text'])
        self.make_idle('Importing data from ' + self.curr_data2import.dirname)
        try:
            if self.curr_data2import:
                self.curr_bids.import_data(self.curr_data2import)
                # self.update_text(self.curr_bids.curr_log)
            else:
                self.update_text('No upload directory is set.')
        except Exception as err:
            self.update_text(self.curr_bids.curr_log + str(err))
        self.curr_data2import = None
        self.upload_dir = None
        self.change_menu_state(self.uploader_menu, start_idx=2, state=DISABLED)
        self.make_available()

    def close_window(self):
        if self.curr_bids:
            self.curr_bids.access.delete_file()
            # if not os.path.isfile(os.path.join(self.curr_bids.dirname, self.curr_bids.log_path,
            #                                    'bids_' + self.curr_bids.access["access_time"] + '.log')):
            #     self.curr_bids.write_log(self.curr_bids.curr_log)
            self.curr_bids.write_log('BIDS Manager was closed')
            self.curr_bids.save_as_json()
        self.quit()
        self.root.destroy()

    def make_idle(self, str2print=None):
        if str2print is None:
            str2print = ''
        else:
            str2print = '\n' + str2print
        self.root.config(cursor="wait")
        for key in self.main_frame:
            self.main_frame[key].config(cursor="wait")
        self.banner.configure(bg="red")
        self.banner_label.set(self.banner_label._default + str2print)
        self.update()

    def make_available(self):
        self.root.config(cursor="")
        for key in self.main_frame:
            self.main_frame[key].config(cursor="")
        self.banner.configure(bg="blue")
        self.banner_label.set(self.banner_label._default)
        self.update()  # may not be necessary if at the end of method but is needed otherwise...

    def ask4uploader_import(self):
        #Check if the requirements is conform
        is_conform = False
        for key in self.curr_bids.requirements['Requirements'].keys():
            if key in bids.ModalityType.get_list_subclasses_names():
                is_conform = True
        if not is_conform:
            messagebox.showinfo('Requirements is not conform', 'Your requirements doesn"t contain the "different possible values for all modalities" (3rd column in requirements GUI), \nso BIDS Uploader cannot be ran\n')
            req_box = messagebox.askquestion('Modify your Requirements', 'Do you want to open the GUI to modify your requirements?')
            if req_box == 'yes':
                self.modify_requirements_file()
            else:
                messagebox.showinfo('BIDS Uploader', 'BIDS Uploader cannot be ran')
                return
        #Run the BIDS Uploader
        self.make_idle('BIDS Uploader is running')
        try:
            call_generic_uplader(self.curr_bids)
            self.update()
        except:
            self.update_text('BIDS uploader crashed')
            self.make_available()
            return
        dirname = os.path.dirname(self.curr_bids.dirname)
        self.upload_dir = os.path.join(dirname, 'TempFolder4Upload')
        if not os.path.exists(self.upload_dir):
            self.update_text('The importation has been cancel because there is no data to import.')
            self.make_available()
            return
        self.make_idle('Data are ready to be imported.')
        if not os.listdir(self.upload_dir):
            self.update_text('There is nothing to import.')
        elif os.path.isfile(os.path.join(self.upload_dir, bids.Data2Import.filename)):
            is_ready = self.verify_data2import(self.upload_dir)
            if is_ready:
                self.curr_bids.import_data(self.curr_data2import)
                self.curr_data2import = None
        else:
            data_imported = 0
            with os.scandir(self.upload_dir) as it:
                for entry in it:
                    if entry.is_dir() and self.curr_bids['DatasetDescJSON']['Name'] in entry.name:
                        if os.path.isfile(os.path.join(entry.path, bids.Data2Import.filename)):
                            is_ready = self.verify_data2import(entry.path)
                            if is_ready:
                                self.curr_bids.import_data(self.curr_data2import)
                                self.curr_data2import = None
                                data_imported += 1
            if data_imported == 0:
                self.update_text('There is nothing to import.')
        self.make_available()

    def verify_data2import(self, upload_dir):
        is_ready = False
        req_path = os.path.join(self.curr_bids.dirname, 'code', 'requirements.json')
        self.curr_data2import = bids.Data2Import(upload_dir, req_path)
        if self.curr_data2import.is_empty():
            self.update_text('There is no file to import in ' + upload_dir)
            self.upload_dir = None
            self.curr_data2import = None
        else:
            self.curr_bids.make_upload_issues(self.curr_data2import, force_verif=True)
            is_ready = True
        return is_ready

    def modify_requirements_file(self):
        if self.curr_bids:
            filename = os.path.join(self.curr_bids.dirname, 'code', 'requirements.json')
            RequirementsDialog(self, self.curr_bids.dirname, filename)
            self.curr_bids.requirements = bids.Requirements(filename)

    def read_license(self):
        notice_license = 'BIDS Manager  Copyright (C) 2018-2020  Aix-Marseille University, INSERM, INS.\n' \
        'This program is free software: you can redistribute it and/or modify it under the terms of the\n' \
         'GNU General Public License as published by the Free Software Foundation, either version 3 of the License,\n' \
         'or any later version.\n' \
        'You should have received a copy of the GNU General Public License along with this program.\n' \
                           'If not, see <http://www.gnu.org/licenses/>.'

        messagebox.showinfo('License', notice_license)

    def cite_paper(self):
        citation = 'Roehri, N., Medina-Villalon, S., Jegou, A., Colombet, B., Giusiano, B., Ponz, A., & Bénar, C. G. (2020)\n' \
                   'Transfer , collection and organisation of electrophysiological and imaging data for multicenter studies.\n'\
                    '(submitted)'
        messagebox.showinfo('Citation', citation)


    # def run_analysis(self, nameS):
    #     try:
    #         soft_analyse = pip.PipelineSetting(self.curr_bids, nameS)
    #     except (EOFError, KeyError) as err:
    #         self.update_text(err)
    #         #self.ask4bidsdir(isnew_dir=False)
    #     output_dict = BidsSelectDialog(self, self.curr_bids, soft_analyse)
    #     #add the parameters
    #     self.update_text('Subjects selected \n' + '\n'.join(output_dict.subject_selected['sub']) + '\nThe analysis is ready to be run')
    #     log_analysis = soft_analyse.set_everything_for_analysis(output_dict.analysis_param, output_dict.subject_selected)
    #     self.update_text(log_analysis)

    def createtablestats(self):
        deriv_dir = os.path.join(self.curr_bids.dirname, 'derivatives')
        select_list = TableForStatsDialog(self, deriv_dir)
        type_select = SelectHowToCreateTable(self, select_list.results)
        print('coucou')

    @staticmethod
    def make_table(table):
        string_table = ''
        for line in table:
            string_table += '\t'.join(line) + '\n'

        return string_table


class DoubleListbox(object):
    """ DoubleListbox is a class to display two ListBox which share the same scrollbar and are thus synchronous """

    def __init__(self, parent):
        self.elements = dict()
        self.elements['scrollbar'] = Scrollbar(master=parent, orient="vertical", command=self.on_vsb)
        self.elements['list1'] = Listbox(master=parent, font=("Arial", 12),
                                         yscrollcommand=self.elements['scrollbar'].set)
        self.elements['list2'] = Listbox(master=parent, font=("Arial", 12),
                                         yscrollcommand=self.elements['scrollbar'].set)
        self.elements['list1'].bind("<MouseWheel>", self.on_mouse_wheel)
        self.elements['list2'].bind("<MouseWheel>", self.on_mouse_wheel)

    def on_vsb(self, *args):
        self.elements['list1'].yview(*args)
        self.elements['list2'].yview(*args)

    def on_mouse_wheel(self, event):
        self.elements['list1'].yview("scroll", event.delta, "units")
        self.elements['list2'].yview("scroll", event.delta, "units")
        # this prevents default bindings from firing, which
        # would end up scrolling the widget twice
        return "break"

    def pack_elements(self):
        self.elements['scrollbar'].pack(side=RIGHT, fill=Y)
        self.elements['list2'].pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)
        self.elements['list1'].pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)

    def clear_list(self):
        self.elements['list1'].delete(0, END)
        self.elements['list2'].delete(0, END)

    def winfo_ismapped(self):
        return self.elements['list1'].winfo_ismapped()

    def pack_forget(self):
        for key in self.elements.keys():
            self.elements[key].pack_forget()


class IssueList(DoubleListbox):
    """ Based on the DoubleListbox class, the IssueList class adds three buttons to the joint listbox to allow
    validating, saving or deleting the actions chosen by the user related to the issues in the right-hand side list"""
    button_size = [2, 10]

    def __init__(self, master, cmd_apply, cmd_delete):
        super().__init__(master)
        self.user_choice = None
        self.elements['apply'] = Button(master=master, text='Apply', command=cmd_apply,
                                        height=self.button_size[0], width=self.button_size[1])

        self.elements['delete'] = Button(master=master, text='DELETE', command=cmd_delete, height=self.button_size[0],
                                         width=self.button_size[1], default=ACTIVE)

    def pack_elements(self):
        super().pack_elements()
        self.elements['apply'].pack(side=TOP, expand=1, padx=10, pady=5)
        self.elements['delete'].pack(side=TOP, expand=1, padx=10, pady=5)

    def config(self, **kwargs):
        for key in self.elements:
            self.elements[key].config(**kwargs)


class DefaultText(scrolledtext.ScrolledText, object):

    def clear_text(self, start=None, end=None):
        if not start:
            start = 1.0
        if not end:
            end = END
        self.delete(start, end)


class DisplayText(DefaultText):

    def update_text(self, str2show, delete_flag=True, location=None):
        self.config(state=NORMAL)
        if delete_flag:
            self.delete(1.0, END)
        if not location:
            location = END
        self.insert(location, str2show)
        self.config(state=DISABLED)


class TemplateDialog(Toplevel, object):
    button_size = [2, 10]
    default_pad = [2, 2]

    def __init__(self, parent):

        def center(win):
            win.update_idletasks()
            width = win.winfo_width()
            height = win.winfo_height()
            if width > 1800:
                width = 1800
            x = (win.winfo_screenwidth() // 2) - (width // 2)
            y = (win.winfo_screenheight() // 2) - (height // 2)
            win.geometry('{}x{}+{}+{}'.format(width, height, x, y))

        Toplevel.__init__(self, parent)
        if isinstance(parent, Tk):
            self.monitor_width = parent.winfo_screenwidth()
            self.monitor_height = parent.winfo_screenheight()
        else:
            self.monitor_width = parent.monitor_width
            self.monitor_height = parent.monitor_height
        # self.wm_resizable(False, False)
        self.maxsize(width=self.monitor_width, height=self.monitor_height)
        self.wm_resizable(True, False)
        self.btn_ok = None
        self.btn_cancel = None
        self.withdraw()  # remain invisible for now
        # If the master is not viewable, don't
        # make the child transient, or else it
        # would be opened withdrawn
        self.initial_focus = None
        if parent.winfo_viewable():
            self.transient(parent)

        self.parent = parent
        self.body_widget = Frame(self)
        self.body_widget.pack(padx=self.default_pad[0], pady=self.default_pad[1], fill=BOTH, expand=1)

        self.body(self.body_widget)

        # self.body_widget.geo
        self.results = None
        self.bind("<Escape>", self.cancel)

        # self.list_and_button(parent, input_list=input_list, label_str=label_str, selection_style=selection_style)
        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        if self.parent is not None:
            self.geometry("+%d+%d" % (parent.winfo_rootx() + 50,
                                      parent.winfo_rooty() + 50))

        self.deiconify()  # become visible now

        self.initial_focus.focus_set()
        center(self)
        # wait for window to appear on screen before calling grab_set
        self.wait_visibility()
        self.grab_set()
        self.wait_window(self)

    def body(self, parent):
        pass

    def ok_cancel_button(self, parent, row=None):
        self.btn_ok = Button(parent, text='OK', command=self.ok, height=self.button_size[0],
                             width=self.button_size[1])

        self.btn_cancel = Button(parent, text='Cancel', command=self.cancel, height=self.button_size[0],
                                 width=self.button_size[1], default=ACTIVE)
        if row:

            self.btn_ok.grid(row=row, column=0, sticky=W+E, padx=self.default_pad[0], pady=self.default_pad[1])
            self.btn_cancel.grid(row=row, column=self.body_widget.grid_size()[0]-1, sticky=W+E,
                                 padx=self.default_pad[0], pady=self.default_pad[1])
        else:
            self.btn_cancel.pack(side=RIGHT, fill=Y, expand=1, padx=10, pady=5)
            self.btn_ok.pack(side=LEFT, fill=Y, expand=1, padx=10, pady=5)

    def ok(self, event=None):
        pass

    def destroy(self):
        """Destroy the window"""
        self.initial_focus = None
        Toplevel.destroy(self)

    def cancel(self, event=None):
        # put focus back to the parent window
        if self.parent is not None:
            self.parent.focus_set()
        self.results = None
        self.destroy()

    def apply(self):
        return self.results


class ListDialog(TemplateDialog):

    def __init__(self, parent, input_list, label_str=None, selection_style=None):

        if not selection_style:
            selection_style = BROWSE
        if not label_str:
            if selection_style in [MULTIPLE, EXTENDED]:
                label_str = 'Select element(s) from the list'
            else:
                label_str = 'Select an element from the list'
        self.label_str = label_str
        self.selection_style = selection_style
        self.input_list = input_list
        self.list = None
        super().__init__(parent)

    def body(self, parent):

        self.title = 'Choose from list'
        Label(parent, text=self.label_str).pack(expand=1, fill=BOTH, side=TOP,
                                                padx=self.default_pad[0], pady=self.default_pad[1])
        self.list = Listbox(parent, selectmode=self.selection_style)
        self.list.pack(expand=1, fill=BOTH,
                       padx=self.default_pad[0], pady=self.default_pad[1])

        for item in self.input_list:
            self.list.insert(END, item)
        # add the default ok and cancel button
        self.ok_cancel_button(parent)

    def ok(self, event=None):
        if self.list.curselection():
            self.results = self.selection_get()
            self.destroy()
        else:
            self.results = None
            self.bell()


class CommentDialog(TemplateDialog):

    def __init__(self, parent, previous_comment=None):
        self.label_str = None
        self.read_comment_area = None
        self.add_comment_area = None
        self.add_comment_btn = None
        if not previous_comment:
            previous_comment = ''
        self.previous_comment = previous_comment
        super().__init__(parent)

    def body(self, parent):
        self.title = 'Choose from list'

        self.read_comment_area = DisplayText(master=parent, height=20, width=100)
        self.read_comment_area.update_text(self.previous_comment)
        self.add_comment_area = DefaultText(master=parent, height=10, width=100)

        Label(parent, text='Previous comment(s)').pack(expand=1, fill=BOTH, side=TOP, padx=self.default_pad[0], pady=self.default_pad[1])

        self.read_comment_area.pack(fill=BOTH, expand=1, padx=5, pady=10, side=TOP)
        Label(parent, text='Add new comment').pack(expand=1, fill=BOTH, side=TOP, padx=self.default_pad[0], pady=self.default_pad[1])
        self.add_comment_area.pack(fill=BOTH, expand=1, padx=5, pady=10, side=TOP)

        # add the default ok and cancel button
        self.ok_cancel_button(parent)

    # def add_new_comment(self):
    #     new_comment = self.add_comment_area.get(1.0, END)
    #     if new_comment:
    #         if not self.results:
    #             self.results = []
    #         self.results.append(new_comment)
    #         self.add_comment_area.clear_text()
    #         self.read_comment_area.update_text(new_comment, delete_flag=False)

    def ok(self, event=None):
        new_comment = self.add_comment_area.get(1.0, END)
        if new_comment:
            self.results = new_comment
        self.destroy()


class BidsTSVDialog(TemplateDialog):

    max_lines = 20
    max_columns = 10
    bln_color = {'True': 'green', 'False': 'red', True: 'green', False: 'red', 'good': 'green', 'bad': 'red'}

    def __init__(self, parent, tsv_table, title=None):
        if not isinstance(tsv_table, bids.BidsTSV) or len(tsv_table) == 1:
            error_str = 'Second input should be a non empty BidsTSV instance'
            messagebox.showerror('Wrong input', error_str)
            return
        self.idx = 0
        self.idx_col = 0
        self.str_title = title
        self.orig_order = [line[0] for line in tsv_table[1:]]
        self.main_brick = type(tsv_table)()  # copy the table  so reordering does not affect BidsTSV
        self.main_brick.copy_values(tsv_table)
        self.n_lines = len(tsv_table) - 1
        self.n_columns = len(tsv_table.header)
        self.key_button = {key: '' for key in tsv_table.header}
        self.next_btn = None
        self.prev_btn = None
        self.next_col_btn = None
        self.prev_col_btn = None
        self.max_lines = min(self.n_lines, self.max_lines)
        self.max_columns = min(self.n_columns, self.max_columns)
        self.key_labels = [[] for k in range(0, self.max_lines)]
        self.n_pages = (self.n_lines + self.max_lines - 1) // self.max_lines
        self.n_pages_columns = (self.n_columns + self.max_columns - 1) // self.max_columns
        self.page_label_var = StringVar()
        self.page_label = None
        self.clmn_width = 0
        self.row_height = 0
        self.table2show = tsv_table[1:self.max_lines + 1]
        super().__init__(parent)

    def body(self, parent):
        if self.n_pages_columns == 1:
            self.make_header(parent)
            self.max_columns = self.n_columns
        self.make_table(parent)
        self.page_label = Label(parent, textvariable=self.page_label_var)
        try:
            self.page_label.grid(row=self.max_lines+1, column=0, columnspan=self.n_columns-2, sticky=W+E)
        except:
            pass
        if not self.n_pages == 1:
            self.prev_btn = Button(parent, text='Previous', state=DISABLED,
                                   command=lambda prnt=parent, stp=-1: self.change_page(prnt, stp))
            self.prev_btn.grid(row=self.max_lines + 1, column=self.n_columns - 2, sticky=W + E)
            self.next_btn = Button(parent, text='Next', command=lambda prnt=parent, stp=1: self.change_page(prnt, stp))
            self.next_btn.grid(row=self.max_lines+1, column=self.n_columns-1, sticky=W+E)
            self.update_page_number()
        if not self.n_pages_columns == 1:
            self.key_button = {key: '' for key in self.main_brick.header[0:self.max_columns]}
            self.make_header(parent)
            self.prev_col_btn = Button(parent, text='Previous Columns', state=DISABLED, command=lambda prnt=parent, stp=-1: self.change_column_page(prnt, stp))
            self.prev_col_btn.grid(row=self.max_lines+1, column=0, sticky=W + E)
            self.next_col_btn = Button(parent, text='Next Columns', command=lambda prnt=parent, stp=1: self.change_column_page(prnt, stp))
            self.next_col_btn.grid(row=self.max_lines+1, column=1, sticky=W + E)
        self.ok_cancel_button(parent, row=self.max_lines+2)
        # for i in range(self.max_lines):
        #     self.body_widget.grid_rowconfigure(i, weight=1, uniform='test')

    def make_header(self, parent):
        for cnt, key in enumerate(self.key_button):
            self.key_button[key] = Button(parent, text=key, command=lambda k=key, prnt=parent: self.reorder(k, prnt))
            self.key_button[key].grid(row=0, column=cnt, sticky=W+E)

    def make_table(self, parent):
        for line in range(0, min(self.max_lines, len(self.table2show))):
            for clmn in range(0, min(self.max_columns, self.n_columns)):
                lbl = self.table2show[line][clmn]
                self.key_labels[line].append(Label(parent, text=lbl, relief=RIDGE))
                self.key_labels[line][-1].grid(row=line+1, column=clmn, sticky=W+E)
                if isinstance(self.main_brick, (bids.ParticipantsTSV, bids.ChannelsTSV)) \
                        and lbl in self.bln_color.keys():
                    self.key_labels[line][-1].config(fg='white', bg=self.bln_color[lbl])
                if isinstance(self.main_brick, bids.ChannelsTSV) and self.main_brick.header[clmn] == 'status':
                    self.key_labels[line][-1].bind('<Double-Button-1>',
                                                   lambda event, l=line, c=clmn: self.switch_chan_status(l, c, event))
                if isinstance(self.main_brick, bids.ParticipantsTSV) and \
                        list(self.key_button.keys())[clmn] == 'participant_id':
                    flagProcess = False
                    stradd=''
                    if isinstance(self.main_brick, bids.ParticipantsProcessTSV):
                        flagProcess = True
                        stradd = 'Process'
                    self.parent.bidsdataset.is_subject_present(self.key_labels[line][clmn]['text'], flagProcess)
                    sub = self.parent.bidsdataset.curr_subject['Subject'+stradd]
                    if 'Subject'+stradd in self.parent.key_disabled:
                        disabl = sub.keylist
                    else:
                        disabl = None

    def modify_participants_tsv(self, lin, ev=None):
        #line = line.num
        req_keys_idx = [self.main_brick[0].index(key) for key in self.main_brick[0] if key in bids.Subject.required_keys or key.endswith('_integrity') or key.endswith('_ready')]
        modification = ModifDialog(self, self.table2show[lin], req_keys_idx)
        if modification.results:
            self.parent.parent.curr_bids['ParticipantsTSV'].update_subject(modification.sub, modification.results)
            self.main_brick.update_subject(modification.sub, modification.results)
            self.parent.parent.curr_bids['ParticipantsTSV'].write_file()

    def switch_chan_status(self, lin, col, ev=None):
        lbl_orig = self.key_labels[lin][col]['text']
        if lbl_orig == 'good':
            lbl = 'bad'
        else:
            lbl = 'good'
        self.key_labels[lin][col].config(text=lbl, fg='white', bg=self.bln_color[lbl])
        self.main_brick[1+self.idx*self.max_lines+lin][col] = lbl
        self.results = self.main_brick

    def update_table(self):
        for line in range(0, min(self.max_lines, len(self.table2show))):
            for clmn in range(0, min(self.max_columns, len(self.table2show[0]))):
                lbl = self.table2show[line][clmn]
                self.key_labels[line][clmn]['text'] = lbl
                if isinstance(self.main_brick, (bids.ParticipantsTSV, bids.ChannelsTSV))\
                        and lbl in self.bln_color.keys():
                    self.key_labels[line][clmn].config(fg='white', bg=self.bln_color[lbl])

    def change_page(self, parent, pg_step):
        self.clear_table()
        self.idx += pg_step
        self.update_page_number()
        start_idx = 1+self.idx*self.max_lines
        end_idx = start_idx + self.max_lines
        start_col = self.idx_col * self.max_columns
        end_col = start_col + self.max_columns
        if end_idx > self.n_lines+1:
            end_idx = self.n_lines+1
        if end_col > self.n_columns:
            end_col = self.n_columns
        self.table2show = [line[start_col:end_col] for line in self.main_brick[start_idx:end_idx]]
        self.update_table()

    def change_column_page(self, parent, column_step):
        # Erase header button
        for cnt, key in enumerate(self.key_button):
            self.key_button[key].destroy()
        self.clear_table()
        self.idx_col += column_step
        start_col = self.idx_col*self.max_columns
        if self.idx_col > 1:
            start_col = start_col - (self.idx_col - 1)

        end_col = start_col+self.max_columns - 1
        start_idx = 1+self.idx * self.max_lines
        end_idx = start_idx + self.max_lines
        self.next_col_btn.config(state=NORMAL)
        self.prev_col_btn.config(state=NORMAL)
        if start_col == 0:
            self.prev_col_btn.config(state=DISABLED)
            end_col = start_col + self.max_columns
            self.key_button = {}
        if end_idx > self.n_lines+1:
            end_idx = self.n_lines+1
        if end_col > self.n_columns:
            end_col = self.n_columns
            self.next_col_btn.config(state=DISABLED)
        if start_col > 0:
            self.key_button = {self.main_brick.header[0]: ''}
        self.key_button.update({key: '' for key in self.main_brick.header[start_col:end_col]})
        self.make_header(parent)
        self.table2show = []
        for line in self.main_brick[start_idx:end_idx]:
            if start_col > 0:
                self.table2show.append([line[0]])
            else:
                self.table2show.append([])
            self.table2show[-1].extend(line[start_col:end_col])
        self.update_table()

    def ok(self, event=None):
        # first, the table has to be reordered
        new_chan = [line[0] for line in self.main_brick[1:]]
        if not new_chan == self.orig_order:
            idx_list = [new_chan.index(ch) for ch in self.orig_order]
            tmp_brick = [self.main_brick.header]
            tmp_brick += [self.main_brick[idx + 1] for idx in idx_list]
            self.main_brick = type(self.main_brick)()
            self.main_brick.copy_values(tmp_brick)
        self.results = self.main_brick
        self.destroy()

    def update_page_number(self):
        if self.n_pages == 1:
            return
        self.page_label_var.set('Page ' + str(self.idx + 1) + '/' + str(self.n_pages))
        if self.idx == self.n_pages-1:
            self.next_btn.config(state=DISABLED)
            if self.prev_btn['state'] == DISABLED:
                self.prev_btn.config(state=NORMAL)
        elif self.idx == 0:
            self.next_btn.config(state=NORMAL)
            self.prev_btn.config(state=DISABLED)
        elif self.idx > 0:
            if self.next_btn['state'] == DISABLED:
                self.next_btn.config(state=NORMAL)
            if self.prev_btn['state'] == DISABLED:
                self.prev_btn.config(state=NORMAL)
        else:
            self.prev_btn.config(state=DISABLED)

    def reorder(self, key, parent):
        self.idx = 0
        self.update_page_number()
        self.clear_table()
        key_idx = self.main_brick.header.index(key)
        tmp_list = [line[key_idx] for line in self.main_brick[1:]]
        sorted_idx = sorted(range(len(tmp_list)), key=tmp_list.__getitem__)
        tmp_brick = [self.main_brick.header]
        tmp_brick += [self.main_brick[idx+1] for idx in sorted_idx]
        self.main_brick = type(self.main_brick)()
        self.main_brick.copy_values(tmp_brick)
        self.table2show = [self.main_brick[idx+1] for idx in range(0, self.max_lines)]
        self.update_table()

    def clear_table(self):
        for line in range(0, min(self.max_lines, len(self.table2show))):
            for clmn in range(0, min(self.max_columns, len(self.table2show[0]))):
                # self.key_labels[line][clmn].grid_forget()
                self.key_labels[line][clmn]['text'] = ''
                if self.prev_col_btn:
                    self.key_labels[line][clmn].config(fg='black', bg=self.prev_col_btn.cget("bg"))
            # self.key_labels[line] = []


class ParticipantsTSVDialog(BidsTSVDialog):

    def make_table(self, parent):

        for line in range(0, min(self.max_lines, len(self.table2show))):
            for clmn in range(0, min(self.max_columns, self.n_columns)):
                lbl = self.table2show[line][clmn]
                self.key_labels[line].append(Label(parent, text=lbl, relief=RIDGE))
                self.key_labels[line][-1].grid(row=line + 1, column=clmn, sticky=W + E)
                if lbl in self.bln_color.keys():
                    self.key_labels[line][-1].config(fg='white', bg=self.bln_color[lbl])
                if list(self.key_button.keys())[clmn] == 'participant_id':

                    self.key_labels[line][clmn].bind('<Double-Button-1>', lambda event, li=line, co=clmn: self.what2domenu(line=li, clmn=co, event=event))
                    #                                 lambda event, li=line, co=clmn:
                    #                                 self.open_subject_info(ln=li, cm=co))
                if list(self.key_button.keys())[clmn].endswith('_ready'):
                    self.key_labels[line][clmn].bind('<Double-Button-1>',
                                                     lambda event: print('To be implemented'))

    def open_subject_info(self, ln, cm):
        self.parent.bidsdataset.is_subject_present(self.key_labels[ln][cm]['text'].replace('sub-', ''))
        sub = self.parent.bidsdataset.curr_subject['Subject']
        if 'Subject' in self.parent.key_disabled:
            disabl = sub.keylist
        else:
            disabl = None
        BidsBrickDialog(self, sub, disabled=disabl, title=sub.classname() + ': ' + sub['sub'])

    def what2domenu(self, line, clmn, event):
        pop_menu = Menu(self.master, tearoff=0)
        pop_menu.add_command(label='Open subject dataset', command=lambda li=line, co=clmn:
                                                     self.open_subject_info(ln=li, cm=co))
        pop_menu.add_command(label='Modify this participant"s line', command=lambda li=line: self.modify_participants_tsv(li))
        pop_menu.post(event.x_root, event.y_root)


class ModifDialog(TemplateDialog):

    def __init__(self, parent, tableline, required_idx):
        self.line = tableline
        self.required = [0] + required_idx
        self.line_modification = {}
        self.sub = tableline[0]
        self.header = parent.main_brick.header
        self.requirements = parent.parent.parent.curr_bids.requirements['Requirements']['Subject']['keys']
        super().__init__(parent)

    def body(self, parent):
        for cnt, elt in enumerate(self.line):
            key = self.header[cnt]
            if cnt in self.required:
                self.line_modification[key] = Label(parent, text=elt)
            elif isinstance(self.requirements[key], list):
                val_temp = self.requirements[key]
                self.line_modification[key] = ttk.Combobox(parent, values=val_temp)
            else:
                self.line_modification[key] = Entry(parent, textvariable=key)
                self.line_modification[key].insert(END, elt)
            self.line_modification[key].grid(row=1, column=cnt)
        self.ok_cancel_button(parent, row=2)

    def ok(self):
        self.results = dict()
        for cnt, elt in enumerate(self.line_modification):
            if not cnt in self.required:
                if self.line_modification[elt].get():
                    self.results[elt] = self.line_modification[elt].get()
        for key in self.line_modification:
            if isinstance(self.line_modification[key], Entry):
                self.line_modification[key].delete(0, END)
        self.destroy()

    def cancel(self):
        for key in self.line_modification:
            if isinstance(self.line_modification[key], Entry):
                self.line_modification[key].delete(0, END)
        if self.parent is not None:
            self.parent.focus_set()
        self.results = None
        self.destroy()


class FormDialog(TemplateDialog):

    def __init__(self, parent, input_dict, disabled=None, options=None, required_keys=None, required_protocol_keys=None, title=None):
        def init_dict(keylist, list_attr):
            for att in list_attr:
                setattr(self, att, {key: '' for key in keylist})

        if not isinstance(input_dict, dict):
            error_str = 'Second input should be a dictionary'
            raise TypeError(error_str)
        self.input_dict = input_dict
        self.str_title = title
        init_dict(input_dict.keys(), ['key_labels', 'key_disabled', 'key_entries', 'key_opt_menu', 'options'])
        # [StringVar()]*len(input_dict) duplicate the StringVar(), a change in one will change the other one as well,
        #  not the wanted behaviour. This is the solution
        self.key_opt_var = {key: StringVar() for key in input_dict.keys()}
        self.required_keys = required_keys
        self.required_protocol_keys = required_protocol_keys
        if options:
            for key in options:
                if key in self.options.keys():
                    if options[key]:
                        if not isinstance(options[key], list):
                            self.options[key] = [options[key]]
                        else:
                            self.options[key] = options[key]
        if isinstance(disabled, list):
            for key in disabled:
                    self.key_disabled[key] = DISABLED
        if not required_keys:
            self.required_keys = []
        super().__init__(parent)

    def body(self, parent):
        self.main_form(parent)
        self.ok_cancel_button(parent, row=len(self.input_dict))
        self.results = self.input_dict

    def main_form(self, parent):
        if isinstance(self.str_title, str):
            self.title(self.str_title)
        else:
            self.title('Please fill up the form')
        frame_main_info = VerticalScrollbarFrame(parent, grid_row=0)
        for cnt, key in enumerate(self.input_dict.keys()):
            if key in self.required_keys:
                color = 'red'
            elif self.required_protocol_keys and key in self.required_protocol_keys:
                color = 'orange'
            else:
                color = 'black'
            #Ici pour potentiellement ajpouter frame scrollbar pour info linique
            #Voir aussi pour l'affichage dans Entry des fichiers
            self.key_labels[key] = Label(frame_main_info.frame, text=key, fg=color)
            self.key_labels[key].grid(row=cnt, sticky=W, padx=self.default_pad[0], pady=self.default_pad[1])
            if self.key_disabled[key]:
                self.key_entries[key] = Label(frame_main_info.frame, text=self.input_dict[key])
            else:
                self.key_entries[key] = Entry(frame_main_info.frame, justify=CENTER)
                self.key_entries[key].insert(END, self.input_dict[key])
            self.key_entries[key].grid(row=cnt, column=1, sticky=W, padx=self.default_pad[0], pady=self.default_pad[1])

            if key in self.options.keys() and self.options[key]:
                self.key_opt_menu[key] = OptionMenu(frame_main_info.frame, self.key_opt_var[key], *self.options[key],
                                                    command=lambda opt, k=key: self.update_entry(opt, k))
                self.key_opt_menu[key].config(width=self.key_entries[key]['width'])
                self.key_opt_menu[key].grid(row=cnt, column=2, sticky=W+E, padx=self.default_pad[0],
                                            pady=self.default_pad[1])

            frame_main_info.update_scrollbar()

    def update_entry(self, idx, key):
        self.key_entries[key].delete(0, END)
        self.key_entries[key].insert(0, idx)

    def ok(self, event=None):
        self.results = {key: self.input_dict[key] for key in self.input_dict.keys()}
        for key in self.input_dict.keys():
            if isinstance(self.key_entries[key], Entry):
                self.results[key] = self.key_entries[key].get()
        self.destroy()


class BidsBrickDialog(FormDialog):
    bidsdataset = None
    meta_brick = None

    def __init__(self, parent, input_dict, disabled=None, options=None, required_keys=None, title=None, flag_process=False, addelements=False):
        if not isinstance(input_dict, (bids.BidsBrick, bids.BidsJSON)):
            raise TypeError('Second input should be a BidsBrick instance.')
        if isinstance(input_dict, (bids.BidsDataset, bids.Data2Import)):
            if not addelements:
                BidsBrickDialog.meta_brick = input_dict.classname()  # meta_brick is either bids.BidsDataset or bids.Data2Import
            self.attr_dict = input_dict['DatasetDescJSON']
            self.input_dict = dict()
            if not flag_process:
                self.input_dict['Subject'] = input_dict['Subject']
                self.input_dict['Derivatives'] = input_dict['Derivatives']
            else:
                self.input_dict['SubjectProcess'] = input_dict['SubjectProcess']
            title = input_dict.classname() + ': ' + input_dict['DatasetDescJSON']['Name']
            if disabled is None:
                disabled = []
            if isinstance(input_dict, bids.BidsDataset) and not addelements:
                BidsBrickDialog.bidsdataset = input_dict
                if not flag_process:
                    self.input_dict['ParticipantsTSV'] = input_dict['ParticipantsTSV']
                else:
                    self.input_dict['ParticipantsProcessTSV'] = input_dict['ParticipantsProcessTSV']
                disabled = input_dict.keylist
                disabled += self.attr_dict.keylist
        elif isinstance(input_dict, bids.BidsJSON):
            self.attr_dict = input_dict
            self.input_dict = dict()
        else:
            self.attr_dict = input_dict.get_attributes()
            self.input_dict = input_dict
            if isinstance(input_dict, bids.Subject):
                title = 'Subject: ' + input_dict['sub']
            else:
                title = os.path.basename(input_dict['fileLoc'])
        self.main_brick = input_dict
        self.key_button_lbl = {key: '' for key in self.input_dict.keys()
                               if key in bids.BidsBrick.get_list_subclasses_names() +
                               bids.BidsSidecar.get_list_subclasses_names()}
        self.key_listw = {key: '' for key in self.input_dict.keys()
                          if key in bids.BidsBrick.get_list_subclasses_names() +
                          bids.BidsSidecar.get_list_subclasses_names()}
        self.key_button = {key: '' for key in self.input_dict.keys()
                           if key in bids.BidsBrick.get_list_subclasses_names() +
                           bids.BidsSidecar.get_list_subclasses_names()}
        # # [StringVar()]*len(input_dict) duplicate the StringVar(), a change in one will change the other one as well,
        # #  not the wanted behaviour. This is the solution
        # self.key_opt_var = {key: StringVar() for key in input_dict.keys()}
        super().__init__(parent, input_dict=self.attr_dict, options=options,
                         required_keys=input_dict.required_keys, required_protocol_keys=input_dict.required_protocol_keys, disabled=disabled, title=title)

    def body(self, parent):
        self.main_form(parent)
        cnt_tot = len(self.input_dict)
        # remember input_dict corresponds only to the attributes
        if any(key in bids.ModalityType.get_list_subclasses_names() for key in self.key_button_lbl):
            VertFrame = VerticalScrollbarFrame(parent, grid_row=1)
            body_frame = VertFrame.frame
        else:
            body_frame = parent
        for cnt, key in enumerate(self.key_button_lbl.keys()):
            if not self.meta_brick == 'Data2Import':
                if key not in bids.BidsSidecar.get_list_subclasses_names() and not self.main_brick[key]:
                    # only show none empty BidsBricks but let the JSON and TSV in case you want to add more
                    continue

            setting_list = {"row": cnt + cnt_tot, "column": 1, "columnspan": 2, "sticky": W + E,
                            "padx": self.default_pad[0],
                            "pady": self.default_pad[1]}
            setting_label = {"row": cnt + cnt_tot, "sticky": W, "padx": self.default_pad[0],
                             "pady": self.default_pad[1]}
            # if key == 'Subject':
            #     # increase subject list layout length
            #     setting_list['rowspan'] = 6
            #     setting_label['rowspan'] = 6
            #     cnt_tot += setting_list['rowspan'] - 1
            self.key_button_lbl[key] = Label(body_frame, text=key, fg="black")
            self.key_button_lbl[key].grid(**setting_label)
            if key.startswith('Subject'):
                ht = 8
                wd = 20
            elif key in bids.BidsSidecar.get_list_subclasses_names():
                ht = 1
                wd = 20
            else:
                ht = 3
                wd = 40
            if isinstance(self.main_brick, (bids.ModalityType, bids.GlobalSidecars)):
                setting_list['columnspan'] = 1
            self.key_listw[key] = Listbox(body_frame, height=ht, width=wd) #Voir si modifie cela
            if not (key.startswith('Subject') or key == 'Derivatives') or (key not in self.key_disabled or not self.key_disabled[key] == DISABLED):
                self.key_listw[key].bind('<Double-Button-1>', lambda event, k=key: self.open_new_window(k, event))
                self.key_listw[key].bind('<Return>', lambda event, k=key: self.open_new_window(k, event))
            else:
                self.key_listw[key].bind('<Double-Button-1>', lambda event, k=key: self.call_menu(k, event))
            self.populate_list(self.key_listw[key], self.main_brick[key])
            self.key_listw[key].grid(**setting_list)

            # if key not in bids.BidsSidecar.get_list_subclasses_names() and \
            #         (key not in self.key_disabled or not self.key_disabled[key] == DISABLED):
            if key not in self.key_disabled or not self.key_disabled[key] == DISABLED:
                if key in bids.BidsSidecar.get_list_subclasses_names():
                    btn_str = 'Modify '
                elif key == 'Derivatives':
                    btn_str = 'Set '
                else:
                    btn_str = 'Add '
                self.key_button[key] = Button(body_frame, text=btn_str + key, justify=CENTER,
                                              command=lambda k=key: self.add_new_brick(k))
                self.key_button[key].grid(row=cnt+cnt_tot, column=3, sticky=W+E, padx=self.default_pad[0],
                                          pady=self.default_pad[1])
        self.ok_cancel_button(parent, row=cnt_tot+len(self.key_button_lbl))
        if len(self.key_button_lbl):
            for i in range(self.body_widget.grid_size()[0]):
                self.body_widget.grid_columnconfigure(i, weight=1, uniform='test')
        self.results = self.input_dict
        if 'VertFrame' in locals():
            VertFrame.update_scrollbar()
            if 'btn_str' in locals():
                self.body_widget.grid_columnconfigure(1, weight=5, uniform='test')

    def call_menu(self, key, event):
        pop_menu = Menu(self.key_listw[key], tearoff=0)
        pop_menu.add_command(label='Show {}'.format(key), command=lambda ev=event, k=key: self.open_new_window(k, ev))
        pop_menu.add_command(label='Delete {}'.format(key), command=lambda k=key: self.remove_element(k))
        pop_menu.post(event.x_root, event.y_root)

    @staticmethod
    def populate_list(list_obj, list_of_bbricks):
        list_obj.delete(0, END)
        if not list_of_bbricks:
            return
        list_of_elmts = []
        if isinstance(list_of_bbricks, (bids.ParticipantsTSV, bids.SrcDataTrack)):
            list_of_elmts.append(list_of_bbricks.filename)
        elif isinstance(list_of_bbricks, bids.BidsSidecar):
            list_of_elmts.append(list_of_bbricks.modality_field + list_of_bbricks.extension)
        elif isinstance(list_of_bbricks[0], (bids.ModalityType, bids.GlobalSidecars)):
            for mod_brick in list_of_bbricks:
                list_of_elmts.append(os.path.basename(mod_brick['fileLoc']))
        elif isinstance(list_of_bbricks[0], bids.Subject):
            for sub in list_of_bbricks:
                list_of_elmts.append(sub['sub'])
        elif isinstance(list_of_bbricks[0], bids.Derivatives):
            for ppln in list_of_bbricks[0]['Pipeline']:
                list_of_elmts.append(ppln['name'])
        elif isinstance(list_of_bbricks[0], bids.Scans):
            for scan in list_of_bbricks:
                list_of_elmts.append(scan['fileLoc'])
        else:
            raise TypeError('not allowed object type')
        BidsManager.populate_list(list_obj, list_of_elmts)

    def open_new_window(self, key, event):
        if not self.key_listw[key].curselection():
            return
        curr_idx = self.key_listw[key].curselection()[0]
        if key == 'Subject' or key == 'SubjectProcess':
            sub = self.main_brick[key][curr_idx]
            if key in self.key_disabled:
                disabl = sub.keylist
            else:
                disabl = None
            BidsBrickDialog(self, sub, disabled=disabl,
                            title=sub.classname() + ': ' + sub['sub'])
        elif key == 'Derivatives':
            pip = self.main_brick[key][0]['Pipeline'][curr_idx]
            if isinstance(self.main_brick, bids.Data2Import):
                addelements=True
            else:
                addelements=False
            if 'Derivatives' in self.key_disabled:
                disabl = pip.keylist
            else:
                disabl = None
            BidsBrickDialog(self, pip, disabled=disabl,
                            title=pip.classname() + ': ' + pip['name'], flag_process=True, addelements=addelements)
            self.main_brick.save_as_json()
        elif key == 'Scans':
            sdcr_file = self.main_brick['Scans'][curr_idx]['ScansTSV']
            title=None
            BidsTSVDialog(self, sdcr_file, title=title).apply()
        elif key in bids.BidsJSON.get_list_subclasses_names():
            sdcr_file = self.main_brick[key]
            # pop_menu = Menu(self.body_widget, tearoff=0)
            # pop_menu.post(event.x_root, event.y_root)
            BidsBrickDialog(self, sdcr_file, disabled=list(sdcr_file.keys()),
                            title=sdcr_file.classname())
        elif key in bids.ModalityType.get_list_subclasses_names() + bids.GlobalSidecars.get_list_subclasses_names():
            mod_brick = self.main_brick[key][curr_idx]
            fname = mod_brick['fileLoc']
            pop_menu = Menu(self.body_widget, tearoff=0)
            if not mod_brick['modality'] in ['electrodes', 'coordsystem']:
                pop_menu.add_command(label='Open file',
                                     command=lambda f=fname: self.open_file(f))
            if mod_brick.classname() in self.key_disabled:
                disbl = mod_brick.keylist
            else:
                disbl = [key for key in mod_brick.keylist if key in bids.BidsTSV.get_list_subclasses_names()]
                # pop_menu.add_command(label='Remove',
                #                      command=lambda idx=curr_idx, k=key: self.remove_element(k, idx))
            pop_menu.add_command(label='Show attributes',
                                 command=lambda brick=mod_brick, dsbl=disbl: BidsBrickDialog(self, brick,
                                                                                             disabled=dsbl))
            if BidsBrickDialog.meta_brick == 'BidsDataset':  # allow remove file in bidsdataset
                pop_menu.add_command(label='Remove file',
                                     command=lambda brick=mod_brick, idx=curr_idx, k=key:
                                     self.remove_file(brick, k, idx))
            pop_menu.post(event.x_root, event.y_root)
        elif key == 'ParticipantsTSV':
            ptpts_tsv = self.main_brick[key]
            title = 'participants.tsv'
            ParticipantsTSVDialog(self, ptpts_tsv, title=title)

        elif key in bids.BidsTSV.get_list_subclasses_names():
            sdcr_file = self.main_brick[key]
            title = None
            if isinstance(self.main_brick, bids.ModalityType):
                title = os.path.splitext(os.path.basename(self.main_brick['fileLoc']).replace(
                    self.main_brick['modality'], self.main_brick[key].modality_field))[0]
            sdcr_file_new = BidsTSVDialog(self, sdcr_file, title=title).apply()

            if sdcr_file_new and not sdcr_file_new == sdcr_file:
                sdcr_file.clear()
                sdcr_file.copy_values(sdcr_file_new)
                filename, dirname, ext = self.main_brick.create_filename_from_attributes()
                if sdcr_file_new.modality_field:
                    fname = filename.replace(self.main_brick['modality'],
                                             sdcr_file.modality_field)
                else:
                    fname = filename
                fname2bewritten = os.path.join(bids.BidsDataset.dirname, dirname, fname +
                                               sdcr_file_new.extension)
                sdcr_file.write_file(fname2bewritten)
                self.main_brick.write_log(fname + ' was modified.')
        else:
            print('coucou')

    @staticmethod
    def open_file(fname):
        if platform.system() == 'Linux':
            os.system("xdg-open " + os.path.normpath(os.path.join(bids.BidsBrick.cwdir, fname)))
        else:
            os.startfile(os.path.normpath(os.path.join(bids.BidsBrick.cwdir, fname)))

    def remove_file(self, mod_brick, key, index):
        if BidsBrickDialog.meta_brick == 'BidsDataset' and \
                messagebox.askyesno('Remove File', 'Are you sure you want to remove ' + mod_brick['fileLoc'] + '?'):
            self.config(cursor="wait")
            BidsBrickDialog.bidsdataset.remove(mod_brick, with_issues=True)
            BidsBrickDialog.bidsdataset.check_requirements(specif_subs=mod_brick['sub'])
            self.populate_list(self.key_listw[key], self.main_brick[key])
            self.config(cursor="")

    def remove_element(self, key):
        in_deriv = None
        if not self.key_listw[key].curselection():
            return
        curr_idx = self.key_listw[key].curselection()[0]
        if key == 'Derivatives':
            input_dict = self.main_brick[key][0]['Pipeline'][curr_idx]
            to_display = input_dict['name']
        else:
            input_dict = self.main_brick[key][curr_idx]
            to_display = input_dict['sub']
        if key == 'SubjectProcess':
            in_deriv = self.main_brick['name']
            to_display += ' in '+ in_deriv + 'folder'
        if (BidsBrickDialog.meta_brick == 'BidsDataset' or BidsBrickDialog.meta_brick == 'Pipeline') and \
            messagebox.askyesno('Remove {}'.format(key), 'Are you sure you want to remove ' + to_display + ' from the dataset?'):
            self.config(cursor="wait")
            BidsBrickDialog.bidsdataset.remove(input_dict, in_deriv=in_deriv)
            self.populate_list(self.key_listw[key], self.main_brick[key])
            self.config(cursor="")

    def add_new_brick(self, key):
        self.update_fields()
        opt = None
        disbld = ['sub', 'fileLoc']
        flag_process=False
        addelements=False
        try:
            if isinstance(self.main_brick, (bids.BidsDataset, bids.Data2Import)):
                if key =='Derivatives':
                    if not isinstance(self.main_brick[key], bids.Derivatives) and not self.main_brick[key]:
                        self.main_brick[key] = bids.Derivatives()
                    sublist = [sub['sub'] for sub in self.main_brick['Subject']]
                    dname = filedialog.askdirectory(title='Please select a derivatives directory', initialdir=bids.BidsDataset.dirname)
                    pip_name = os.path.basename(dname)
                    self.main_brick.is_pipeline_present(pip_name)
                    if self.main_brick.curr_pipeline['isPresent']:
                        idx = self.main_brick.curr_pipeline['index']
                        new_brick = self.main_brick[key][-1]['Pipeline'][idx]
                    else:
                        new_brick = bids.Pipeline(name=pip_name)
                    for sub in sublist:
                        new_brick.is_subject_present(sub, flagProcess=True)
                        if not new_brick.curr_subject['isPresent']:
                            new_brick['SubjectProcess'].append(bids.SubjectProcess())
                            new_brick['SubjectProcess'][-1]['sub'] = sub
                    flag_process = True
                    disbld=None
                    opt=None
                    addelements=True
                elif key.startswith('Subject'):
                    dname = filedialog.askdirectory(title='Please select a subject directory', initialdir=bids.BidsDataset.dirname)
                    sub_name = os.path.basename(dname).split('-')[1]
                    if isinstance(self.main_brick, bids.Pipeline):
                        self.main_brick.is_subject_present(sub_name, flagProcess=True)
                        str = 'Process'
                        flag_process = True
                    else:
                        self.main_brick.is_subject_present(sub_name, flagProcess=False)
                        str =''
                        flag_process = False
                    if self.main_brick.curr_subject['isPresent']:
                        new_brick = self.main_brick.curr_subject['Subject'+str]
                    else:
                        new_brick = getattr(bids, key)()
                        new_brick['sub'] = sub_name
                    addelements=True
                    disbld = None
                    opt = None
                else:
                    messagebox.showerror('Not implemented', "Not implemented for now.")
                    return
            elif isinstance(self.main_brick, bids.Subject):

                flag, miss_str = self.main_brick.has_all_req_attributes(nested=False)
                if not flag:
                    messagebox.showerror('Incomplete subject', miss_str)
                    return
                if key in bids.GlobalSidecars.get_list_subclasses_names():
                    fname = filedialog.askopenfilename(title='Please select a file',
                                                       filetypes=[
                                                           ('sidecar', "*.tsv;*.json"),
                                                           ('photo', "*" + ";*".join(bids.Photo.allowed_file_formats))],
                                                       initialdir=bids.BidsBrick.cwdir)
                elif key in bids.Imaging.get_list_subclasses_names():
                    fname = filedialog.askdirectory(title='Please select a file', initialdir=bids.BidsBrick.cwdir)
                elif key in bids.ImagingProcess.get_list_subclasses_names():
                    fname = filedialog.askdirectory(title='Please select a file', initialdir=bids.BidsBrick.cwdir)
                else:
                    file_formats = [formt for formt in getattr(bids, key).readable_file_formats
                                    if formt not in getattr(bids, key).allowed_file_formats]
                    fname = filedialog.askopenfilename(title='Please select a file',
                                                       filetypes=[(key, "*" + ";*".join(file_formats))],
                                                       initialdir=bids.BidsBrick.cwdir)

                if not fname:
                    return
                if not os.path.normpath(os.path.dirname(fname)) == os.path.normpath(bids.BidsBrick.cwdir):
                    messagebox.showerror('File not in data2import folder', "File should be in " + bids.BidsBrick.cwdir
                                         + ".")
                    return
                if key in bids.GlobalSidecars.get_list_subclasses_names():
                    new_brick = getattr(bids, key)(fname)
                    disbld.append('modality')
                else:
                    new_brick = getattr(bids, key)()
                    new_brick['fileLoc'] = os.path.basename(fname)
                    if bids.BidsDataset.requirements:
                        if isinstance(new_brick, bids.Process):
                            flag_process =True
                        else:
                            flag_process = False
                        # use requirements.json to propose via drop down menu
                        opt = bids.BidsDataset.requirements.make_option_dict(key, flag_process)
                        if not 'modality' in opt.keys():
                            opt['modality'] = new_brick.allowed_modalities
                    else:
                        opt = dict()
                        opt['modality'] = new_brick.allowed_modalities

                new_brick['sub'] = self.main_brick['sub']
            elif isinstance(self.main_brick, bids.ModalityType) and key in bids.BidsSidecar.get_list_subclasses_names():
                new_brick = getattr(bids, key)()
                if key in bids.BidsJSON.get_list_subclasses_names():
                    new_brick['FileComment'] = bids.BidsJSON.bids_default_unknown
                elif key in bids.BidsTSV.get_list_subclasses_names():
                    raise NotImplementedError('Modification of TSV files has not yet being handled ')
                    # new_brick.append({key: bids.BidsSidecar.bids_default_unknown for key in new_brick.header})
                new_brick.copy_values(self.main_brick[key], simplify_flag=False)
            else:
                new_brick = getattr(bids, key)()
            result_brick = BidsBrickDialog(self, new_brick, disabled=disbld, options=opt,
                                           required_keys=new_brick.required_keys, title=new_brick.classname(), flag_process=flag_process, addelements=addelements).apply()
            if result_brick is not None:
                if key == 'Derivatives':
                    new_brick['DatasetDescJSON'].copy_values(result_brick)
                else:
                    new_brick.copy_values(result_brick)
                # still issue with JSON since has_all_req_attributes does not return anything... but updates
                # self.is_complete
                flag, miss_str = new_brick.has_all_req_attributes()
                if not isinstance(new_brick, (bids.BidsJSON, bids.BidsTSV)) and not flag:
                    messagebox.showerror('Missing attributes', miss_str)
                    return
                if key == 'Derivatives':
                    self.main_brick.is_pipeline_present(pip_name)
                    if not self.main_brick.curr_pipeline['isPresent']:
                        self.main_brick[key][0]['Pipeline'].append(new_brick)
                elif key.startswith('Subject'):
                    self.main_brick.is_subject_present(result_brick['sub'], flagProcess=flag_process)
                    if not self.main_brick.curr_subject['isPresent']:
                        self.main_brick[key].append(new_brick)
                else:
                    self.main_brick[key] = new_brick
                self.populate_list(self.key_listw[key], self.main_brick[key])
        except Exception as err:
            messagebox.showerror('Error Occurred!', str(err))

    def update_fields(self):
        for key in self.key_entries.keys():
            if isinstance(self.main_brick, (bids.BidsDataset, bids.Data2Import)):
                if isinstance(self.key_entries[key], Entry) and not \
                        self.key_entries[key].get() == self.main_brick['DatasetDescJSON'][key]:
                    self.main_brick['DatasetDescJSON'][key] = self.key_entries[key].get()
            else:
                if isinstance(self.key_entries[key], Entry) and not self.key_entries[key].get() == self.main_brick[key]:
                    self.main_brick[key] = self.key_entries[key].get()


class SmallDialog(TemplateDialog):

    def __init__(self, parent, list_value, title, select_str):
        self.list_value = list_value
        self.var = IntVar()
        self.str_title = title
        self.label_question = select_str
        super().__init__(parent)

    def body(self, parent):
        self.title(self.str_title)
        Label(parent, text=self.label_question, font=('Helvetica', '14')).pack()
        for i, val in enumerate(self.list_value):
            Radiobutton(parent, text=val, variable=self.var, value=i).pack()
        self.ok_cancel_button(parent)

    def ok(self, event=None):
        self.results = {'flag': False, 'value':''}
        if self.var.get() is not None:
            self.results['flag'] = True
            self.results['value'] = self.list_value[self.var.get()]
        self.destroy()


def make_cmd4pop(curr_issue, deriv_folder=None):
    cmd = 'pop=True, in_bids=False'
    if deriv_folder:
        cmd += ' , in_deriv="' + deriv_folder + '"'
    curr_issue.add_action(desc='Remove from element to import.', command=cmd)


def prepare_chg_attr(elmt_brick, curr_bids, in_bids_flg, deriv_folder=None):
    if isinstance(elmt_brick, bids.DatasetDescJSON):
        bids_dict = type(elmt_brick)()
        if deriv_folder:
            curr_bids.is_pipeline_present(deriv_folder)
            bids_dict.copy_values(curr_bids.curr_pipeline['Pipeline']['DatasetDescJSON'])
        else:
            bids_dict.copy_values(curr_bids['DatasetDescJSON'])
        imp_dict = elmt_brick
    elif isinstance(elmt_brick, bids.BidsBrick):
        curr_bids.is_subject_present(elmt_brick['sub'])
        fp = ''
        if deriv_folder:
            curr_bids.is_pipeline_present(deriv_folder)
            curr_pip = curr_bids['Derivatives'][-1]['Pipeline'][curr_bids.curr_pipeline['index']]
            curr_pip.is_subject_present(elmt_brick['sub'], flagProcess=True)
            curr_bids.curr_subject = curr_pip.curr_subject
            fp ='Process'
        if isinstance(elmt_brick, bids.Subject):
            bids_dict = curr_bids.curr_subject['Subject'+fp].get_attributes(['alias', 'upload_date'])
        else:
            fname, dirn, ext = elmt_brick.create_filename_from_attributes()
            if deriv_folder:
                dirn = os.path.join('derivatives', deriv_folder, dirn)
            bids_obj = curr_bids.get_object_from_filename(os.path.join(dirn, fname + ext))
            if bids_obj:
                bids_dict = bids_obj.get_attributes('fileLoc')
                if 'run' in bids_dict.keys():
                    tmp_brick = type(elmt_brick)()
                    tmp_brick.copy_values(bids_dict)
                    if deriv_folder:
                        _, highest = curr_pip.get_number_of_runs(tmp_brick, flag_process=True)
                    else:
                        _, highest = curr_bids.get_number_of_runs(tmp_brick)
                    if highest:
                        bids_dict['run'] = highest + 1
                if 'ses' in bids_dict.keys():
                    if deriv_folder:
                        _, ses_list = curr_pip.get_number_of_session4subject(bids_dict['sub'], flag_process=True)
                    else:
                        _, ses_list = curr_bids.get_number_of_session4subject(bids_dict['sub'])
                    bids_dict['ses'] = ses_list
                if 'modality' in bids_dict:
                    bids_dict['modality'] = elmt_brick.allowed_modalities
            else:
                bids_dict = curr_bids.requirements.make_option_dict(elmt_brick.classname())
        imp_dict = elmt_brick.get_attributes(['alias', 'upload_date', 'fileLoc'])
    else:
        return None, None

    if in_bids_flg:
        input_dict = bids_dict
        option_dict = imp_dict
    else:
        input_dict = imp_dict
        option_dict = bids_dict

    return input_dict, option_dict


def make_cmd4chg_attr(curr_issue, elmt_brick, input_dict, modif_brick, in_bids_flg, deriv_folder=None):

    if isinstance(elmt_brick, bids.DatasetDescJSON) and 'Authors' in modif_brick and \
            not isinstance(modif_brick['Authors'], list):
        # tkinter modifies the author list ['NR' , 'FB', 'CGB'] into a string '{NR} {FB} {CGB}'
        tmp_str = modif_brick['Authors'].replace('} {', ', ')
        tmp_str = tmp_str.replace('{', '').replace('}', '')
        modif_brick['Authors'] = tmp_str

    if in_bids_flg:
        dir_str = ' in BIDS dir'
    else:
        dir_str = ' in import dir'
    if isinstance(elmt_brick, bids.GlobalSidecars):
        input_brick = type(elmt_brick)(elmt_brick['fileLoc'])
        output_brick = type(elmt_brick)(elmt_brick['fileLoc'])
    else:
        input_brick = type(elmt_brick)()
        output_brick = type(elmt_brick)()
    input_brick.copy_values(input_dict)

    output_brick.copy_values(modif_brick)
    if deriv_folder:
        cmd = input_brick.write_command(output_brick, {'in_bids': in_bids_flg, 'in_deriv': deriv_folder})
    else:
        cmd = input_brick.write_command(output_brick, {'in_bids': in_bids_flg})
    curr_issue.add_action(desc='Modify attrib. into ' + str(modif_brick) + dir_str, command=cmd)


def prepare_chg_eletype(curr_iss, mismtch_elec):
    input_dict = {'type': mism_elec['type'] for mism_elec in curr_iss['MismatchedElectrodes']
                  if mism_elec['name'] == mismtch_elec}
    opt_dict = {'type': eval('bids.'+ curr_iss['mod'] +'.channel_type')}

    return input_dict, opt_dict


def make_cmd4electypechg(output_dict, input_dict, curr_iss, mismtch_elec):
    str_info = 'Change electrode type of ' + mismtch_elec + ' from ' + input_dict['type'] + ' to ' + \
               output_dict['type'] + ' in the electrode file related to ' + \
               os.path.basename(curr_iss['fileLoc']) + '.\n'
    # self.pack_element(self.main_frame['text'], side=LEFT, remove_previous=False)
    # to fancy, used for others
    # command = ', '.join([str(k + '="' + output_dict[k] + '"') for k in output_dict])
    command = 'type="' + output_dict['type'] + '"'
    curr_iss.add_action(str_info, command, elec_name=mismtch_elec)


def make_cmd4elecnamechg(new_name, curr_iss, mismtch_elec):
            str_info = mismtch_elec + ' has to be renamed as ' + new_name + ' in the files related to ' + \
                       os.path.basename(curr_iss['fileLoc']) + ' (channels.tsv, events.tsv, .vmrk and .vhdr).\n'
            command = 'name="' + new_name + '"'
            curr_iss.add_action(str_info, command, elec_name=mismtch_elec)


# class BidsSelectDialog(TemplateDialog):
#     bidsdataset = None
#     select_subject = None
#     #subject_list = {'SubjectToAnalyse': []}
#
#     def __init__(self, parent, input_dict, analysis_dict):
#
#         if isinstance(input_dict, bids.BidsDataset):
#             BidsSelectDialog.bidsdataset = input_dict
#         elif analysis_dict and not isinstance(analysis_dict, pip.PipelineSetting):
#             raise TypeError('Third input should be a pipeline analysis')
#         else:
#             raise TypeError('Second input should be a bids dataset')
#
#         #init variable
#         self.subject_dict =dict()
#
#         self.participants = BidsSelectDialog.bidsdataset['ParticipantsTSV']
#         self.vars = self.select_criteria(self.participants)
#
#         self.subject_dict['Subject'] = []
#         for sub in BidsSelectDialog.bidsdataset['Subject']:
#             self.subject_dict['Subject'].append(sub['sub'])
#
#         self.software = analysis_dict
#         try:
#             self.param_vars, self.input_vars = self.software.create_parameter_to_inform()
#             self.param_script = IntVar()
#             self.param_gui = IntVar()
#             self.param_file = []
#         except EOFError as err:
#             messagebox.showerror('ERROR', err)
#             return
#
#         if self.input_vars:
#             req_keys = [key for key in pip.SubjectToAnalyse.keylist if not key == 'sub']
#             for clef in self.input_vars:
#                 if self.input_vars[clef]['modality']['attribut'] == 'Label':
#                     modality = [self.input_vars[clef]['modality']['value']]
#                 else:
#                     modality = self.input_vars[clef]['modality']['value']
#                 for sub in BidsSelectDialog.bidsdataset['Subject']:
#                     for mod in sub:
#                         if mod and mod in modality:
#                             keys = [elt for elt in req_keys if elt in eval('bids.'+mod+'.keylist')]
#                             if mod in bids.Imaging.get_list_subclasses_names():
#                                 keys.append('modality')
#                             for key in keys:
#                                 value = [elt[key] for elt in sub[mod]]
#                                 value = sorted(list(set(value)))
#                                 if value and value[0] is not '':
#                                     if not key in self.input_vars[clef]:
#                                         self.input_vars[clef][key] = {}
#                                         self.input_vars[clef][key]['value'] = value
#                                         self.input_vars[clef][key]['attribut'] = 'IntVar'
#                                     elif key == 'modality' and self.input_vars[clef][key]['attribut'] == 'Label':
#                                         self.input_vars[clef][key]['value'] = value
#                                         self.input_vars[clef][key]['attribut'] = 'IntVar'
#                                     else:
#                                         self.input_vars[clef][key]['value'].extend(value)
#                                     self.input_vars[clef][key]['value'] = sorted(list(set(self.input_vars[clef][key]['value'])))
#                                     if len(self.input_vars[clef][key]['value']) > 1:
#                                         self.input_vars[clef][key]['attribut'] = 'Variable'
#
#         super().__init__(parent)
#
#     def body(self, parent):
#
#         self.title('Select Subjects and parameters')
#         self.All_sub = IntVar()
#         self.Id_sub = IntVar()
#         self.Crit_sub = IntVar()
#         frame_subject = Frame(parent,  relief=GROOVE, borderwidth=2)
#         Label(frame_subject, text='Select subjects for analysis', font='bold', fg='#1F618D').pack(side=TOP)
#         frame_subject.pack(side=LEFT)
#         frame_sub_check = Frame(frame_subject)
#         All_sub_butt = Checkbutton(frame_sub_check, text='All subjects', variable=self.All_sub)
#         All_sub_butt.pack(side=LEFT)
#         Id_sub_butt = Checkbutton(frame_sub_check, text='Select subject(s) Id(s)', variable=self.Id_sub, command=lambda: enable_frames(Frame_list, self.Id_sub))
#         Id_sub_butt.pack(side=LEFT)
#         Crit_sub_butt = Checkbutton(frame_sub_check, text='Select subjects by criteria', variable=self.Crit_sub, command=lambda: enable_frames(Frame_criteria, self.Crit_sub))
#         Crit_sub_butt.pack(side=LEFT)
#         Frame_list = Frame(frame_subject)
#         Frame_criteria = Frame(frame_subject)
#         Label(Frame_criteria, text='Select criteria for multiple subjects analysis:', font='bold', fg='#1F618D').grid(row=0)
#
#         #Subject list
#         self.subject = Label(Frame_list, text='Subject', font='bold', fg='#1F618D')
#         self.subject.grid(row=0, sticky=W)
#         list_choice = Variable(Frame_list, self.subject_dict['Subject'])
#         self.select_subject = Listbox(Frame_list, exportselection=0, listvariable=list_choice, selectmode=MULTIPLE)
#         self.select_subject.grid(row=1, column=1, sticky=W + E)
#
#         #Criteria to select subjects
#         max_crit, cntC = self.create_button(Frame_criteria, self.vars)
#
#         #place the frame
#         if cntC < 1:
#             cntC = 1
#         frame_sub_check.pack(side=TOP)
#         Frame_list.pack(side=LEFT)#.grid(row=1, column=0, columnspan=1, rowspan=cntR + cntC)
#         enable(Frame_list, 'disabled')
#         Frame_criteria.pack(side=LEFT)#.grid(row=cntR+1, column=1, rowspan=cntC, columnspan=max_crit)
#         enable(Frame_criteria, 'disabled')
#         frame_subject.pack(side=LEFT)
#
#         frame_parameters = Frame(parent, relief=GROOVE, borderwidth=2)
#         if self.input_vars:
#             frame_input_criteria = Frame(frame_parameters)
#             Label(frame_input_criteria, text='Select input criteria:', font='bold', fg='#1F618D').pack()
#             frame_dict= dict()
#             for cnt, key in enumerate(self.input_vars):
#                 frame_dict[key] = Frame(frame_input_criteria)
#                 Label(frame_dict[key], text='{0}'.format(' '.join(key.split('_')[1:]))).grid(row=0)
#                 max_req, cntR = self.create_button(frame_dict[key], self.input_vars[key])
#                 frame_dict[key].pack(side=LEFT)
#             frame_input_criteria.pack(side=TOP)
#         Label(frame_parameters, text='Select parameters for analysis', font='bold', fg='#1F618D').pack(side=TOP)
#         frame_param_check = Frame(frame_parameters)
#         frame_param_check.pack(side=TOP)
#         frame_param_select = Frame(frame_parameters)
#         frame_param_select.pack(side=TOP)
#         param_file = Button(frame_param_check, text='Filename path', command=lambda: self.ask4file(self.param_file))
#         import_param_button = Checkbutton(frame_param_check, text='Select your script with parameters values', variable=self.param_script, command=lambda: param_file.configure(state='active'))
#         import_param_button.pack(side=LEFT)
#         param_file.pack(side=LEFT)
#         param_file.configure(state='disabled')
#         select_param_button = Checkbutton(frame_param_check, text='Use the GUI to determine analysis parameters', variable=self.param_gui, command=lambda: enable_frames(frame_param_select, self.param_gui))
#         select_param_button.pack(side=LEFT)
#         max_param, cntP = self.create_button(frame_param_select, self.param_vars)
#
#         enable(frame_param_select, 'disabled')
#         frame_parameters.pack(side=LEFT)
#
#         #row_okcancel = max(length, cntR, cntC)+1
#         frame_okcancel = Frame(parent)
#         frame_okcancel.pack(side=BOTTOM)
#         self.ok_cancel_button(frame_okcancel)
#
#     def ok(self):
#         self.subject_selected = self.get_the_subject_id()
#         if self.param_script.get():
#             self.analysis_param = self.param_file[0]
#         else:
#             self.analysis_param = self.get_parameter_from_gui(self.param_vars)
#         self.input_param = {}
#         for inp in self.input_vars:
#             self.input_param[inp[6:]] = self.get_parameter_from_gui(self.input_vars[inp])
#         self.destroy()
#         self.vars = {}
#         self.input_vars = {}
#         self.param_vars = {}
#
#     def select_criteria(self, participant_dict):
#
#         def check_numerical_value(element):
#             is_numerical = False
#             punctuation = ',.?!:'
#             temp = element.translate(str.maketrans('', '', punctuation))
#             temp = temp.strip('YymM ')
#             if temp.isnumeric():
#                 is_numerical = True
#             return is_numerical
#
#         display_dict = dict()
#         req_keys = self.bidsdataset.requirements['Requirements']['Subject']['keys']
#         for key, value in req_keys.items():
#             if value:
#                 display_dict[key] = value
#             elif 'age' in key:
#                 display_dict[key] = value
#             elif 'duration' in key:
#                 display_dict[key] = value
#         criteria = participant_dict.header
#         key_list = display_dict.keys()
#
#         var_dict = dict()
#         for key in key_list:
#             idx = criteria.index(key)
#             is_string = False
#             display_value = []
#             for val_part in participant_dict[1::]:
#                 is_number = check_numerical_value(val_part[idx])
#                 if is_number and display_dict[key]:
#                     display_value.append(val_part[idx])
#                 elif is_number:
#                     display_value.append('min_' + key)
#                     display_value.append('max_' + key)
#                     is_string = True
#                 else:
#                     l_elt = val_part[idx].split(', ')
#                     for l in l_elt:
#                         display_value.append(l)
#             display_value = list(set(display_value))
#             if is_string:
#                 var_dict[key] = {}
#                 display_value = sorted(display_value, reverse=True)
#                 var_dict[key]['attribut'] = 'StringVar'
#                 var_dict[key]['value'] = [value for value in display_value]
#             elif display_value:
#                 display_value = list(set(display_value).intersection(set(display_dict[key])))
#                 if len(display_value) == 1 and not 'n/a' in display_value:
#                     var_dict[key] = {}
#                     var_dict[key]['attribut'] = 'Label'
#                     var_dict[key]['value'] = [value for value in display_value]
#                 elif len(display_value) > 1:
#                     var_dict[key] = {}
#                     var_dict[key]['attribut'] = 'Variable'
#                     var_dict[key]['value'] = [value for value in display_value]
#
#         return var_dict
#
#     def get_parameter_from_gui(self, var_dict):
#         res_dict = dict()
#         for key in var_dict:
#             att_type = var_dict[key]['attribut']
#             val_temp = var_dict[key]['value']
#             if att_type == 'Variable':
#                 for val in var_dict[key]['results']:
#                     if val.get():
#                         idx = var_dict[key]['results'].index(val)
#                         try:
#                             res_dict[key].append(val_temp[idx])
#                         except:
#                             res_dict[key] = []
#                             res_dict[key].append(val_temp[idx])
#             elif att_type == 'StringVar':
#                 num_value = False
#                 if isinstance(val_temp, list):
#                     for id_var in val_temp:
#                         if id_var.get().isalnum():
#                             if id_var._name.startswith('min'):
#                                 minA = int(id_var.get())
#                                 num_value = True
#                             elif id_var._name.startswith('max'):
#                                 maxA = int(id_var.get())
#                                 num_value = True
#                             else:
#                                 res_dict[key] = id_var.get()
#                     if num_value:
#                         res_dict[key] = range(minA, maxA)
#                 else:
#                     res_dict[key] = val_temp.get()
#             elif att_type == 'IntVar':
#                 if isinstance(val_temp, list):
#                     for id_var in val_temp:
#                         if id_var.get():
#                             try:
#                                 res_dict[key].append(id_var._name)
#                             except:
#                                 res_dict[key] = []
#                                 res_dict[key].append(id_var._name)
#                 else:
#                     if val_temp.get():
#                         res_dict[key] = val_temp._name
#             elif att_type == 'Listbox':
#                 res_dict[key] = val_temp.get()
#             elif att_type == 'Bool':
#                 if val_temp.get() == True:
#                     res_dict[key] = True
#             elif att_type == 'Label':
#                 res_dict[key] = val_temp
#             elif att_type == 'File':
#                 if val_temp:
#                     res_dict[key] = val_temp[0]
#
#         return res_dict
#
#     def get_the_subject_id(self):
#
#         def get_subject_list_from_criteria(bids_dialog, input_dict, subject_list):
#             for elt in bids_dialog.participants[1::]:
#                 elt_in = []
#                 for key, value in input_dict.items():
#                     idx_key = bids_dialog.participants.header.index(key)
#                     if isinstance(value, range):
#                         elt[idx_key] = elt[idx_key].replace(',', '.')
#                         age_p = round(float(elt[idx_key].rstrip('YyMm ')))
#                         if age_p in value:
#                             elt_in.append(True)
#                     elif isinstance(value, list):
#                         for val in value:
#                             if val in elt[idx_key]:
#                                 elt_in.append(True)
#                             else:
#                                 elt_in.append(False)
#                     elif isinstance(value, str):
#                         if value in elt[idx_key]:
#                             elt_in.append(True)
#                         else:
#                             elt_in.append(False)
#                 elt_in = list(set(elt_in))
#                 if len(elt_in) == 1 and elt_in[0] is True:
#                     subject_list.append(elt[0])
#
#         subject_list = []
#         res_dict = {}
#         if self.All_sub.get():
#             subject_list = self.subject_dict['Subject']
#         elif self.Id_sub.get():
#             for index in self.select_subject.curselection():
#                 subject_list.append(self.select_subject.get(index))
#         elif self.Crit_sub.get():
#             res_dict = self.get_parameter_from_gui(self.vars)
#             get_subject_list_from_criteria(self, res_dict, subject_list)
#
#         return {'sub': subject_list}
#
#     def create_button(self, frame, var_dict, max_col=None):
#         if not max_col:
#             max_col = 1
#         label_dict = {clef: '' for clef in var_dict.keys()}
#         for cnt, key in enumerate(var_dict):
#             label_dict[key] = Label(frame, text=key)
#             label_dict[key].grid(row=cnt + 1, sticky=W)
#             att_type = var_dict[key]['attribut']
#             val_temp = var_dict[key]['value']
#             if att_type == 'StringVar':
#                 if isinstance(val_temp, str):
#                     var_dict[key]['value'] = StringVar()
#                     var_dict[key]['value']._name = val_temp
#                     l = Entry(frame, textvariable=val_temp)
#                     l.insert(END, val_temp)
#                     l.grid(row=cnt + 1, column=max_col, sticky=W + E)
#                 elif isinstance(val_temp, list):
#                     idx_var =0
#                     while idx_var < len(val_temp):
#                         temp = val_temp[idx_var]
#                         var_dict[key]['value'][idx_var] = StringVar()
#                         var_dict[key]['value'][idx_var]._name = temp
#                         l = Entry(frame, textvariable=temp)
#                         l.insert(END, temp)
#                         l.grid(row=cnt + 1, column=idx_var + 1, sticky=W + E)
#                         idx_var += 1
#                     max_col = max(max_col, idx_var)
#             elif att_type == 'Listbox': #A revoir
#                 l = ttk.Combobox(frame, values=val_temp)
#                 l.grid(row=cnt + 1, column=max_col, sticky=W + E)
#                 var_dict[key]['value'] = l
#             elif att_type == 'Variable':
#                 var_dict[key]['results'] = CheckbuttonList(frame, val_temp, row_list=cnt + 1, col_list=max_col).variable_list
#             elif att_type == 'IntVar':
#                 if isinstance(val_temp, list):
#                     idx_var = 0
#                     while idx_var < len(val_temp):
#                         temp = var_dict[key]['value'][idx_var]
#                         var_dict[key]['value'][idx_var] = IntVar()
#                         var_dict[key]['value'][idx_var]._name = temp
#                         l = Checkbutton(frame, text=temp, variable=var_dict[key]['value'][idx_var])
#                         l.grid(row=cnt + 1, column=idx_var + 1, sticky=W + E)
#                         idx_var += 1
#                     max_col = max(max_col, idx_var)
#                 elif isinstance(val_temp, str):
#                     var_dict[key]['value'] = IntVar()
#                     l = Checkbutton(frame, text=val_temp, variable=var_dict[key]['value'])
#                     l.insert(END, val_temp)
#                     l.grid(row=cnt + 1, column=max_col, sticky=W + E)
#             elif att_type == 'Bool':
#                 if val_temp:
#                     val = True
#                 else:
#                     val = False
#                 var_dict[key]['value'] = BooleanVar()
#                 var_dict[key]['value'].set(val)
#                 l = Checkbutton(frame, text='True', variable=var_dict[key]['value'])
#                 l.grid(row=cnt + 1, column=max_col, sticky=W + E)
#             elif att_type == 'Label':
#                 l = Label(frame, text=val_temp)
#                 l.grid(row=cnt + 1, column=max_col, sticky=W + E)
#             elif att_type == 'File':
#                 l = Button(frame, text='Browse', command=lambda: self.ask4file(var_dict[key]['value']))
#                 l.grid(row=cnt + 1, column=max_col, sticky=W + E)
#
#         return max_col, cnt
#
#     def ask4file(self, file):
#         filename = filedialog.askopenfilename(title='Select file', initialdir=self.bidsdataset.cwdir)
#         file.append(filename)


class RequirementsDialog(TemplateDialog):

    def __init__(self, parent, bids_dir, filename=None):
        self.subject_key = ['keys', 'required_keys']
        self.info_key_label = []
        self.info_value_label = []
        self.req_button = []
        self.import_req = IntVar()
        self.create_req = IntVar()
        self.load_add = IntVar()
        self.info_button = []
        self.modality_required_key = []
        self.modality_required_value = []
        self.modality_required_name = []
        self.modality_required_amount = []
        self.modality_required_button = []
        self.modality_required_label = []
        self.modality_key = []
        self.modality_value = []
        self.modality_name = []
        self.modality_button = []
        self.modality_label = []
        self.modality_list = bids.Imaging.get_list_subclasses_names() + bids.Electrophy.get_list_subclasses_names() + bids.GlobalSidecars.get_list_subclasses_names()
        self.req_name=''
        self.elec_name=''
        self.imag_name=''
        self.bids_dir = bids_dir
        self.error_str=''
        self.modif_file = filename
        self.info_val_removed = []
        self.mod_required_removed = []
        self.mod_removed = []
        super().__init__(parent)

    def ask4path(self, file_type, display=None):
        self.attributes("-topmost", False)
        if file_type == 'req':
            self.req_name = filedialog.askopenfilename(title='Select requirements type',
                                                       filetypes=[('req.', "*.json")])
            if display:
                display.delete(0,END)
                display.insert(END, self.req_name)
        elif file_type == 'elec':
            self.elec_name = filedialog.askopenfilename(title='Select converter for electrophy. data type (AnyWave)')
            if display:
                display.delete(0, END)
                display.insert(END, self.elec_name)
        elif file_type == 'imag':
            self.imag_name = filedialog.askopenfilename(title='Select converter for Imaging data type (dicm2nii)')
            if display:
                display.delete(0, END)
                display.insert(END, self.imag_name)
        self.attributes("-topmost", True)

    def body(self, parent):
        # width = round(self.monitor_width * 9/10)
        height = round(self.monitor_height * 9/10)
        width = self.monitor_width
        self.geometry('{}x{}'.format(width, height))
        smallfont = font.Font(family="Segoe UI", size=9)
        self.option_add('*Font', smallfont)
        if not self.modif_file:
            placement = Frame(parent)
            toolbar = Frame(placement)
            import_req_button = Checkbutton(placement, text='Select your Requirements', variable=self.import_req, command=lambda: enable_frames(toolbar, self.import_req))
            import_req_button.pack(side=LEFT)
            entry_path = Entry(toolbar, state=DISABLED)
            req_path = Button(toolbar, text='Filename path', command=lambda: self.ask4path(file_type='req', display=entry_path), state=DISABLED)
            req_path.pack(side=LEFT)
            entry_path.pack(side=LEFT)
            toolbar.pack(side=LEFT)
            placement.pack(side=TOP)
            loadbar = Frame(parent)
            addbar = Frame(loadbar)
            load_req_button = Checkbutton(loadbar, text='Load your Requirements to do modifications', variable=self.load_add, command=lambda: enable_frames([addbar, self.frame_subject_info.frame, self.frame_required.frame, self.frame_modality.frame], self.load_add))
            load_req_button.pack(side=LEFT)
            entry_load = Entry(addbar, state=DISABLED)
            req_load = Button(addbar, text='Filename path', command=lambda: self.read_modify_gui(filename=None, entry_load=entry_load), state=DISABLED)
            req_load.pack(side=LEFT)
            entry_load.pack(side=LEFT)
            addbar.pack(side=LEFT)
            loadbar.pack(side=TOP)
            create_req_button = Checkbutton(parent, text='Create your Requirements', variable=self.create_req, command=lambda: enable_frames([self.frame_subject_info.frame, self.frame_required.frame, self.frame_modality.frame], self.create_req))
            create_req_button.pack(side=TOP)


        Frame_path = Frame(parent)
        Frame_path.pack(side=LEFT, fill=BOTH)
        Label(Frame_path, text='Indicate the path of the converters').pack(side=TOP, anchor=N)

        #Scrollbar the subject's frame
        self.frame_subject_info = DoubleScrollbarFrame(parent)
        Label(self.frame_subject_info.frame, text='Indicate the subjects information you need', justify='center', fg='#17657D').grid(row=0, column=0, columnspan=3)
        Label(self.frame_subject_info.frame, text='Label').grid(row=1, column=0)
        Label(self.frame_subject_info.frame, text='Possible Values').grid(row=1, column=1)

        # Scrollbar the frame with canvas
        self.frame_required = DoubleScrollbarFrame(parent)
        Label(self.frame_required.frame, text='Indicate the modality required in the dataset', justify='center', fg='#17657D').grid(row=0, column=0, columnspan=3)

        #Scrollbar the modality's frame
        self.frame_modality = DoubleScrollbarFrame(parent)
        Label(self.frame_modality.frame, text='Indicate the different possible values for all modalities', justify='center', fg='#17657D').grid(row=0, column=0, columnspan=3)
        self.frame_modality.frame.pack(side=LEFT, fill=BOTH, expand=True)

        #initiate the first button
        #self.subject_info_button(self.frame_subject_info.frame)
        l4 = Button(self.frame_subject_info.frame, text='+', command=lambda: self.add_lines_command())
        l4.grid(row=1, column=2)
        self.frame_subject_info.update_scrollbar()

        #initiate the modality button
        m1 = ttk.Combobox(self.frame_required.frame, values=self.modality_list)
        m1.grid(row=1, column=0)
        m2 = Button(self.frame_required.frame, text='+', command=lambda: self.add_lines_command(mod=self.modality_list[m1.current()], required=True))
        m2.grid(row=1, column=1)
        self.frame_required.update_scrollbar()

        m3 = ttk.Combobox(self.frame_modality.frame, values=self.modality_list)
        m3.grid(row=1, column=0)
        m4 = Button(self.frame_modality.frame, text='+', command=lambda: self.add_lines_command(mod=self.modality_list[m3.current()]))
        m4.grid(row=1, column=1)
        self.frame_modality.update_scrollbar()

        #path in frame path
        Label(Frame_path, text='Select the Electrophisiology converters').pack(anchor='w')
        entry_elec = Entry(Frame_path)
        Button(Frame_path, text='Electrophysiology converters', command=lambda: self.ask4path(file_type='elec', display=entry_elec)).pack(anchor='center')#grid(row=3)
        entry_elec.pack()
        Label(Frame_path, text='Select the Imaging converters').pack(anchor='w')
        entry_imag = Entry(Frame_path)
        Button(Frame_path, text='Imaging converters', command=lambda: self.ask4path(file_type='imag', display=entry_imag)).pack(anchor='center')#.grid(row=7)
        entry_imag.pack()

        if self.modif_file:
            self.read_modify_gui(filename=self.modif_file)
            self.load_add.set(1)
        else:
            enable(self.frame_subject_info.frame, 'disabled')
            enable(self.frame_required.frame, 'disabled')
            enable(self.frame_modality.frame, 'disabled')

        self.ok_cancel_button(Frame_path)
        self.attributes("-topmost", True)

    def subject_info_button(self, key=None, val=None, req=False):
        self.info_key_label.append(StringVar())
        if key:
            self.info_key_label[-1].set(key)
        self.info_value_label.append(StringVar())
        if val:
            if isinstance(val, list):
                self.info_value_label[-1].set(', '.join(val))
            else:
                self.info_value_label[-1].set(val)
        self.req_button.append(IntVar())
        if req:
            self.req_button[-1].set(1)
        cnt = len(self.info_key_label) + 1
        l1 = Entry(self.frame_subject_info.frame, textvariable=self.info_key_label[-1])
        l1.grid(row=cnt, column=0)
        self.info_button.append(l1)
        idx_beg = len(self.info_button) - 1
        l2 = Entry(self.frame_subject_info.frame, textvariable=self.info_value_label[-1])
        l2.grid(row=cnt, column=1)
        self.info_button.append(l2)
        l3 = Checkbutton(self.frame_subject_info.frame, text='required', variable=self.req_button[-1])
        l3.grid(row=cnt, column=2)
        self.info_button.append(l3)
        idx_beg = self.info_button.index(l1)
        idx_val = len(self.info_key_label)-1
        l5 = Button(self.frame_subject_info.frame, text='-', command=lambda: self.remove_lines_command(idx_val))
        l5.grid(row=cnt, column=3)
        self.info_button.append(l5)

    def ok_cancel_button(self, parent, row=None):
        self.btn_ok = Button(parent, text='OK', command=self.ok, height=self.button_size[0],
                             width=self.button_size[1])

        self.btn_cancel = Button(parent, text='Cancel', command=self.cancel, height=self.button_size[0],
                                 width=self.button_size[1], default=ACTIVE)
        self.btn_ok.pack(side=LEFT, anchor='sw', expand=1, padx=10, pady=5)
        self.btn_cancel.pack(side=RIGHT, anchor='se', expand=1, padx=10, pady=5)

    def remove_lines_command(self, idx_val, mod=False, required=False):
        if mod:
            if required:
                req = 'required_'
            else:
                req = ''
            keys = eval('self.modality_'+req+'key')
            button = eval('self.modality_'+req+'button')
            label = eval('self.modality_'+req+'label')
            idx_val_removed = eval('self.mod_' + req + 'removed')
            try:
                number_line = len(keys[idx_val])
                num = -1
                for i in range(0, len(keys), 1):
                    num = num + len(keys[i]) + 1
                    if idx_val > i and i in idx_val_removed:
                        num = num - len(keys[i]) - 1
                    elif idx_val <= i:
                        break
                idx_button = num - number_line
                idx = 1
                while idx <= number_line + 1:
                    button[idx_button].grid_forget()
                    del button[idx_button]
                    idx += 1
                for key in keys[idx_val].keys():
                    keys[idx_val][key].grid_forget()
                label[idx_val].grid_forget()
                idx_val_removed.append(idx_val)
                if not required:
                    self.modality_name[idx_val] = ''
            except IndexError:
                self.attributes("-topmost", False)
                messagebox.showerror('Error', 'There are no buttons to delete')
                self.attributes("-topmost", True)
        else:
            idx = 1
            num = 3
            #self.info_butt_removed.append(idx_button)
            if idx_val != 0:
                for i in range(1, idx_val, 1):
                    if i not in self.info_val_removed:
                        num += 4
            idx_button = num - 3
            while idx < 5:
                self.info_button[idx_button].grid_forget()
                del self.info_button[idx_button]
                idx += 1
            self.info_val_removed.append(idx_val)

    def add_lines_command(self, mod=None, required=False, dict_val=None, flag_first=True):

        def number_line(list_cnt):
            number = 0
            i=0
            for elt in list_cnt:
                i = list_cnt.index(elt)+1
                number = number + i*len(elt)
            if i == 0:
                autre_num = 2
            else:
                autre_num = i + 3
            return number, autre_num

        if mod:
            if required and flag_first:
                if mod not in self.modality_name:
                    parent_list = [self.frame_required, self.frame_modality]
                else:
                    parent_list = [self.frame_required]
            elif required and not flag_first:
                parent_list = [self.frame_required]
            elif not required and mod in self.modality_name:
                self.attributes("-topmost", False)
                messagebox.showinfo('Information', '{} is already presents.'.format(mod))
                self.attributes("-topmost", True)
                return
            else:
                parent_list = [self.frame_modality]
            required_value = {nbr: {} for nbr in range(0, len(parent_list), 1)}
            required_key = {nbr: {} for nbr in range(0, len(parent_list), 1)}
            m = {nbr: '' for nbr in range(0, len(parent_list), 1)}
            idx_val = {nbr: 0 for nbr in range(0, len(parent_list), 1)}
            idx_butt = {nbr: 0 for nbr in range(0, len(parent_list), 1)}
            required_dict = {nbr: required for nbr in range(0, len(parent_list), 1)}
            for nbr, parent in enumerate(parent_list):
                if mod in bids.GlobalSidecars.get_list_subclasses_names():
                    key_label = eval('bids.'+mod+'.keylist')
                    key_photo = [lab for lab in bids.Photo.keylist if not lab in key_label]
                    if 'modality' in key_label:
                        idx = key_label.index('modality')
                        for elt in key_photo:
                            key_label.insert(idx, elt)
                            idx +=1
                else:
                    key_label = eval('bids.'+mod+'.keylist')

                for elt in key_label:
                    if elt not in bids.BidsJSON.get_list_subclasses_names() + bids.BidsTSV.get_list_subclasses_names() + bids.BidsFreeFile.get_list_subclasses_names() + bids.BidsBrick.required_keys + ['fileLoc']:
                        if elt == 'modality':
                            mod_list = eval('bids.'+mod+'.allowed_modalities')
                            if required:
                                required_value[nbr][elt] = mod_list
                                required_key[nbr][elt] = ''
                        else:
                            required_value[nbr][elt] = StringVar()
                            required_key[nbr][elt] = ''
                            if dict_val:
                                val = ''
                                if 'type' in dict_val:
                                    if isinstance(dict_val['type'], dict) and elt in dict_val['type']:
                                        val = dict_val['type'][elt]
                                    elif isinstance(dict_val['type'], list):
                                        val = []
                                        for type in dict_val['type']:
                                            if elt in type:
                                                val.append(type[elt])
                                        val = list(set(val))
                                elif elt in dict_val:
                                    val = dict_val[elt]
                                if isinstance(val, list):
                                    val = ', '.join(val)
                                required_value[nbr][elt].set(val)

                if required and parent == self.frame_required:
                    line_num, init_num = number_line(self.modality_required_value)
                    req = 'required_'
                    required_value[nbr]['amount'] = StringVar()
                    if dict_val and dict_val['amount']:
                        required_value[nbr]['amount'].set(str(dict_val['amount']))
                    else:
                        required_value[nbr]['amount'].set('1')
                    required_key[nbr]['amount'] = ''
                else:
                    line_num, init_num = number_line(self.modality_value)
                    req = ''
                    required_dict[nbr] = False
                    if 'modality' in required_key[nbr]:
                        del required_key[nbr]['modality']
                        del required_value[nbr]['modality']

                lab = Label(parent.frame, text=mod+':')
                lab.grid(row=line_num + init_num)
                for cnt, key in enumerate(required_key[nbr].keys()):
                    required_key[nbr][key] = Label(parent.frame, text=key)
                    required_key[nbr][key].grid(row=line_num + cnt + init_num+1, sticky=W)
                    if key == 'modality':
                        l = Listbox(parent.frame, exportselection=0, selectmode=MULTIPLE, height=3)
                        for item in required_value[nbr][key]:
                            l.insert(END, item)
                        if dict_val:
                            if isinstance(dict_val['type'], dict) and key in dict_val['type']:
                                val = dict_val['type'][key]
                                if val != '_':
                                    idx = required_value[nbr][key].index(val)
                                    l.selection_set(idx)
                            elif isinstance(dict_val['type'], list):
                                val = []
                                for type in dict_val['type']:
                                    if key in type:
                                        idx = required_value[nbr][key].index(type[key])
                                        l.selection_set(idx)

                        required_value[nbr][key] = l
                    else:
                        l = Entry(parent.frame, textvariable=required_value[nbr][key])
                    l.grid(row=line_num + cnt + init_num+1, column=1)
                    eval('self.modality_' + req + 'button.append(l)')

                eval('self.modality_' + req + 'value.append(required_value[nbr])')
                eval('self.modality_' + req + 'key.append(required_key[nbr])')
                eval('self.modality_' + req + 'name.append(mod)')
                eval('self.modality_' + req + 'label.append(lab)')
                idx_val[nbr] = len(eval('self.modality_' + req + 'label')) - 1
                idx_butt[nbr] = len(eval('self.modality_' + req + 'button'))
                m[nbr] = Button(parent.frame, text='-', command=lambda val=idx_val[nbr], mod_bool=True, req_bool=required_dict[nbr]: self.remove_lines_command(val, mod=mod_bool, required=req_bool))
                m[nbr].grid(row=line_num + init_num, column=2)
                eval('self.modality_' + req + 'button.append(m[nbr])')

        else:
            self.subject_info_button()
            parent_list = [self.frame_subject_info]
        for parent in parent_list:
            parent.frame.update_idletasks()
            parent.canvas.config(scrollregion=parent.canvas.bbox("all"))

    def read_modify_gui(self, filename=None, entry_load=None):
        if not filename:
            self.ask4path(file_type='req', display=entry_load)
            filename = self.req_name
            self.req_name = ''
        req_dict = bids.Requirements(filename)
        # fill the subject info
        #self.remove_lines_command(0, 0)
        for key, value in req_dict['Requirements']['Subject']['keys'].items():
            req=False
            if 'required_keys' in req_dict['Requirements']['Subject'] and key in req_dict['Requirements']['Subject']['required_keys']:
                req=True
            self.subject_info_button(key=key, val=value, req=req)
        self.frame_subject_info.frame.update_idletasks()
        self.frame_subject_info.canvas.config(scrollregion=self.frame_subject_info.canvas.bbox("all"))
        #fill the required modality
        for mod in req_dict['Requirements']['Subject']:
            if mod not in ['keys', 'required_keys']:
                for elt in req_dict['Requirements']['Subject'][mod]:
                    self.add_lines_command(mod=mod, required=True, dict_val=elt, flag_first=False)
        #fill the possible modalities
        for mod in req_dict['Requirements']:
            if mod not in ['Subject']:
                self.add_lines_command(mod=mod, required=False, dict_val=req_dict['Requirements'][mod]['keys'], flag_first=False)
        if 'Converters' in req_dict:
            self.elec_name = req_dict['Converters']['Electrophy']['path']
            self.imag_name = req_dict['Converters']['Imaging']['path']

    def ok(self):
        def call_raise(parent, error):
            parent.attributes("-topmost", False)
            messagebox.showerror('Error', error)
            parent.attributes("-topmost", True)

        self.error_str = ''
        if not self.elec_name or 'AnyWave' not in os.path.basename(self.elec_name):
            self.error_str += 'Bids Manager requires AnyWave to convert electrophy data.\n'
        if not self.imag_name or '2nii'not in os.path.basename(self.imag_name):
            self.error_str += 'Bids Manager requires dcm2niix or dicm2nii to convert Imaging data.\n'

        if self.error_str:
            call_raise(self, self.error_str)
            return

        if self.import_req.get():
            if not self.req_name:
                error = 'Bids Manager requires a requirements.json file to be operational.\n'
                call_raise(self, error)
                return
            else:
                req_dict = bids.Requirements(self.req_name)
        elif self.create_req.get() or self.load_add.get():
            req_dict = bids.Requirements()
            req_dict['Requirements']['Subject'] = dict()
            req_dict['Converters'] = dict()
            req_dict['Converters']['Imaging'] = dict()
            req_dict['Converters']['Electrophy'] = dict()
            keys = {}
            required_keys = []

            for i, elt in enumerate(self.info_key_label):
                if i not in self.info_val_removed:
                    value = self.info_value_label[i].get()
                    key = elt.get()
                    if not key:
                        if not self.req_name:
                            error = 'Subject"s information are missing.\n'
                            call_raise(self, error)
                            return
                    else:
                        if ' ' in key and not key.endswith(' '):
                            key = key.replace(' ', '_')

                    if ',' not in value:
                        keys[key] = value
                    else:
                        list_val = value.split(',')
                        keys[key] = []
                        for val in list_val:
                            if ' ' in val:
                                keys[key].append(val.replace(' ', ''))
                            else:
                                keys[key].append(val)
                    if self.req_button[i].get():
                        required_keys.append(key)

            req_dict['Requirements']['Subject']['keys'] = keys
            req_dict['Requirements']['Subject']['required_keys'] = required_keys

            #to get the required modality for the database
            #self.del_from_list(flag_req=True)
            verif_type = {mod: [] for mod in list(set(self.modality_required_name))}
            for i, mod in enumerate(self.modality_required_key):
                if i not in self.mod_required_removed:
                    if self.modality_required_name[i] not in req_dict['Requirements']['Subject'].keys():
                        req_dict['Requirements']['Subject'][self.modality_required_name[i]] = []
                    mod_dict = {}
                    type_list = []
                    type_dict = {}
                    for j, key in enumerate(mod):
                        if isinstance(self.modality_required_value[i][key], StringVar):
                            value = self.modality_required_value[i][key].get()
                        elif isinstance(self.modality_required_value[i][key], Listbox):
                            value = [self.modality_required_value[i][key].get(ind_sel) for ind_sel in self.modality_required_value[i][key].curselection()]
                        if key == 'amount' and value:
                            mod_dict['amount'] = int(value)
                        elif key == 'run' and value:
                            if value.isdigit() or value is '_':
                                type_dict[key] = value
                            else:
                                error = 'Run should be numerical value or "_" in required mod {}.\n'.format(self.modality_required_name[i])
                                call_raise(self, error)
                                return
                        elif value and isinstance(value, list):
                            for v, val in enumerate(value):
                                type_list.append({clef: type_dict[clef] for clef in type_dict})
                                type_list[v][key] = val
                            verif_type[self.modality_required_name[i]].append(key)
                        elif value:
                            type_dict[key] = value
                            verif_type[self.modality_required_name[i]].append(key)
                    if len(type_list) > 1:
                        mod_dict['type'] = type_list
                    elif len(type_list) == 1:
                        mod_dict['type'] = type_list[0]
                    else:
                        mod_dict['type'] = type_dict
                        if not 'modality' in mod_dict['type'].keys():
                            mod_dict['type']['modality'] = '_'
                    if self.modality_required_name[i] in bids.GlobalSidecars.get_list_subclasses_names():
                        if isinstance(mod_dict['type'], dict):
                            if 'space' in mod_dict['type'].keys() and 'acq' in mod_dict['type'].keys():
                                error = 'For the modality GlobalSidecars, you cannot have both space and acq.\n "acq" goes with Photo, and "space" goes with electrodes or coordsystem.\n'
                                call_raise(self, error)
                                return
                        elif isinstance(mod_dict['type'], list):
                            for elt in mod_dict['type']:
                                if 'space' in elt.keys() and 'acq' in elt.keys():
                                    error = 'For the modality GlobalSidecars, you cannot have both space and acq.\n "acq" goes with Photo, and "space" goes with electrodes or coordsystem.\n'
                                    call_raise(self, error)
                                    return
                    req_dict['Requirements']['Subject'][self.modality_required_name[i]].append(mod_dict)
            #self.del_from_list(flag_mod=True)
            #To get the possible keys in modality
            for i, mod in enumerate(self.modality_name):
                if i not in self.mod_removed:
                    if mod not in req_dict['Requirements'].keys():
                        req_dict['Requirements'][mod] = {}
                        key_dict = {}
                    else:
                        key_dict = req_dict['Requirements'][mod]['keys']
                    for key in self.modality_key[i]:
                        value = self.modality_value[i][key].get()
                        if value:
                            if key not in key_dict.keys():
                                key_dict[key] = []
                            if ',' not in value:
                                key_dict[key].append(value)
                            else:
                                list_val = value.split(',')
                                for val in list_val:
                                    if ' ' in val:
                                        key_dict[key].append(val.replace(' ', ''))
                                    else:
                                        key_dict[key].append(val)
                            key_dict[key] = list(set(key_dict[key]))
                        else:
                            if mod in verif_type:
                                if key in verif_type[mod] and key != 'run':
                                    error = 'Be carefull, in {0} required {1} is mentionned but not in possible modalities.\n'.format(mod, key)
                                    call_raise(self, error)
                                    return
                    if any(mod not in list(self.modality_name) for mod in verif_type):
                        error = 'Error: Some required modalities (2nd column) are not in possible modalities (3rd column).\n'
                        call_raise(self, error)
                    req_dict['Requirements'][mod]['keys'] = key_dict
        else:
            error = 'Bids Manager requires a requirements.json file to be operational.\n'
            call_raise(self, error)

        bids.BidsDataset.converters['Imaging']['path'] = self.imag_name
        req_dict['Converters']['Imaging']['path'] = self.imag_name
        req_dict['Converters']['Imaging']['ext'] = ['.nii']
        bids.BidsDataset.converters['Electrophy']['path'] = self.elec_name
        req_dict['Converters']['Electrophy']['path'] = self.elec_name
        req_dict['Converters']['Electrophy']['ext'] = ['.vhdr', '.vmrk', '.eeg']
        bids.BidsDataset.dirname = self.bids_dir
        if self.modif_file:
            self.attributes("-topmost", False)
            flag = messagebox.askyesno('Modify Requirements', 'Do you really want to change your requirements file?')
            self.attributes("-topmost", True)
            if flag:
                req_dict.save_as_json()
        else:
            req_dict.save_as_json()
        self.destroy()
        return

    def del_from_list(self, flag_info=False, flag_mod=False, flag_req=False):
        if flag_info and self.info_val_removed:
            self.info_val_removed.sort(reverse=True)
            for val in self.info_val_removed:
                del self.info_value_label[val]
                del self.info_key_label[val]
                del self.req_button[val]
            self.info_val_removed = []
        if flag_mod and self.mod_removed:
            self.mod_removed.sort(reverse=True)
            for val in self.mod_removed:
                del self.modality_key[val]
                del self.modality_name[val]
                del self.modality_value[val]
                del self.modality_label[val]
            self.mod_removed = []
        if flag_req and self.mod_required_removed:
            self.mod_required_removed.sort(reverse=True)
            for val in self.mod_required_removed:
                del self.modality_required_key[val]
                del self.modality_required_name[val]
                del self.modality_required_value[val]
                del self.modality_required_label[val]
            self.mod_required_removed = []

    def cancel(self, event=None):
        self.error_str += 'You cancel before to indicate your requirements.json.\n Bids Manager requires a requirements.json file to be operational.'
        self.destroy()


class TableForStatsDialog(TemplateDialog):

    def __init__(self, parent, deriv_dir):
        self.derivatives_dir = deriv_dir
        reject_dir = ['parsing', 'log']
        self.deriv_list = [entry for entry in os.listdir(deriv_dir) if not os.path.isfile(os.path.join(deriv_dir,entry)) and not entry in reject_dir]
        self.deriv_button = {key: IntVar() for key in self.deriv_list}
        self.display_button = {key: None for key in self.deriv_list}
        #self.display_button = {'display_'+key: '' for key in self.deriv_list}
        super().__init__(parent)

    def body(self, parent):
        self.title('Select directories to create your statistical table')
        self.geometry('800x600')
        double_frame = Frame(parent)
        double_frame.pack(side=TOP)
        folder_frame = Frame(double_frame, relief='groove')
        folder_frame.pack(side=LEFT)
        display_frame = HorizontalScrollbarFrame(double_frame)
        display_frame.frame.pack(side=LEFT, fill=BOTH, expand=True, anchor='nw')
        okcancel_frame = Frame(parent)
        okcancel_frame.pack(side=BOTTOM)
        for cnt, key in enumerate(self.deriv_button):
            l = Checkbutton(folder_frame, text=key,  variable=self.deriv_button[key])
            l.grid(row=cnt+1, column=0)
            self.display_button[key] = Button(folder_frame, text='display '+key, command=lambda fm=display_frame, dname=key: self.display_dataset(fm, dname))
            self.display_button[key].grid(row=cnt+1, column=1)
        display_frame.update_scrollbar()
        self.ok_cancel_button(okcancel_frame)

    def display_dataset(self, frame2display, deriv_name):
        def deletewidgetframe(frame2delete):
            for w in frame2delete.winfo_children():
                w.destroy()
        deletewidgetframe(frame2display.frame)
        dataset_file = os.path.join(self.derivatives_dir, deriv_name, 'dataset_description.json')
        datastore = bids.DatasetDescJSON()
        datastore.read_file(jsonfilename=dataset_file)
        temp_text = ''
        #canvas_id = frame2display.create_text(10, 10, anchor='nw', font=('Helvetica', 12))
        for key in datastore:
            temp_text = temp_text + '{0} : {1}\n'.format(key, datastore[key])
            #frame2display.insert(canvas_id, END, temp_text)
        lab = Label(frame2display.frame, text=temp_text, anchor='nw', bg='white', font=('Helvetica', 12), justify='left')
        lab.grid(row=0, column=0)
        frame2display.update_scrollbar()

    def ok(self):
        self.results = [key for key in self.deriv_button if self.deriv_button[key].get()]
        self.destroy()


class SelectHowToCreateTable(TemplateDialog):

    def __init__(self, parent, select_deriv):
        self.select_deriv = {key: {} for key in select_deriv}
        self.multiple_choice = ['Average', 'Maximum', 'All']
        super().__init__(parent)

    def body(self, parent):
        self.title('What to do if multiple files by participants?')
        value_radio = len(self.select_deriv)*len(self.multiple_choice)
        values=list(range(2, value_radio+2, 1))
        a=0
        for key in self.select_deriv:
            self.select_deriv[key]['frame'] = Frame(parent, relief=GROOVE, borderwidth=2)
            self.select_deriv[key]['value'] = []
            #self.select_deriv[key]['button'] = []
            Label(self.select_deriv[key]['frame'], text=key).pack(side=TOP)
            for val in self.multiple_choice:
                self.select_deriv[key]['value'].append(IntVar())
                b = Radiobutton(self.select_deriv[key]['frame'], variable=self.select_deriv[key]['value'][-1], text=val, value=values[a])
                b.pack(side=LEFT, expand=1)
                #self.select_deriv[key]['button'].append(b)
                a=+1
                #self.select_deriv[key]['value'].append(b)
            self.select_deriv[key]['frame'].pack(side=TOP)
        self.ok_cancel_button(parent)

    def ok(self):
        self.results = {key: '' for key in self.select_deriv}
        for key in self.select_deriv:
            for cnt, val in enumerate(self.select_deriv[key]['value']):
                if val.get():
                    self.results[key] = self.multiple_choice[cnt]
        self.destroy()


class VerticalScrollbarFrame(Frame):

    def __init__(self, parent, grid_row=None):
        self.Frame_to_scrollbar = Frame(parent, relief=GROOVE, borderwidth=2)
        if grid_row is None:
            self.Frame_to_scrollbar.pack(side=LEFT, fill=BOTH, expand=True)
        else:
            self.Frame_to_scrollbar.grid(row=grid_row, column=0, columnspan=3, sticky='nesw')
            self.Frame_to_scrollbar.columnconfigure(0, weight=1)
            self.Frame_to_scrollbar.columnconfigure(1, weight=1)
        self.vsb = Scrollbar(self.Frame_to_scrollbar, orient="vertical")
        self.vsb.pack(side=RIGHT, fill=Y)
        self.canvas = Canvas(self.Frame_to_scrollbar, yscrollcommand=self.vsb.set)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.frame = Frame(self.canvas)#, relief=GROOVE, borderwidth=2)
        self.frame.pack(side=LEFT, fill=BOTH, expand=True)

    def update_scrollbar(self):
        def myfunction(canvas):
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.canvas.create_window(0, 0, window=self.frame, anchor='nw') #scrollregion=self.canvas.bbox("all"),
        self.canvas.pack()
        self.frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.vsb.configure(command=self.canvas.yview)
        self.frame.bind('<Configure>', myfunction(self.canvas))


class HorizontalScrollbarFrame(Frame):

    def __init__(self, parent):
        self.Frame_to_scrollbar = Frame(parent, relief=GROOVE, borderwidth=2)
        self.Frame_to_scrollbar.pack(side=LEFT, fill=BOTH, expand=True)
        self.hsb = Scrollbar(self.Frame_to_scrollbar, orient="horizontal")
        self.hsb.pack(side=BOTTOM, fill=X)
        self.canvas = Canvas(self.Frame_to_scrollbar, xscrollcommand=self.hsb.set)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.frame = Frame(self.canvas, bg='white')#, relief=GROOVE, borderwidth=2)
        self.frame.pack()

    def update_scrollbar(self):
        def myfunction(canvas):
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.canvas.create_window(0, 0, window=self.frame, anchor='nw') #scrollregion=self.canvas.bbox("all"),
        self.canvas.pack()
        self.frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.hsb.configure(command=self.canvas.xview)
        self.frame.bind('<Configure>', myfunction(self.canvas))


class DoubleScrollbarFrame(Frame):
    def __init__(self, parent):
        self.Frame_to_scrollbar = Frame(parent, relief=GROOVE, borderwidth=2)
        self.Frame_to_scrollbar.pack(side=LEFT, fill=BOTH, expand=True)
        self.vsb = Scrollbar(self.Frame_to_scrollbar, orient="vertical")
        self.vsb.pack(side=RIGHT, fill=Y)
        self.hsb = Scrollbar(self.Frame_to_scrollbar, orient="horizontal")
        self.hsb.pack(side=BOTTOM, fill=X)
        self.canvas = Canvas(self.Frame_to_scrollbar, xscrollcommand=self.hsb.set, yscrollcommand=self.vsb.set)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.frame = Frame(self.canvas)#, relief=GROOVE, borderwidth=2)
        self.frame.pack()

    def update_scrollbar(self):
        def myfunction(canvas):
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.canvas.create_window(0, 0, window=self.frame, anchor='nw') #scrollregion=self.canvas.bbox("all"),
        self.canvas.pack()
        self.frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.hsb.configure(command=self.canvas.xview)
        self.vsb.configure(command=self.canvas.yview)
        self.frame.bind('<Configure>', myfunction(self.canvas))


class CheckbuttonList(Frame):
    variable_list = None

    def __init__(self, parent, variable_list, row_list, col_list):
        self.frame_button = None
        self.hidden = False
        self.test_frame = None
        self.parent = parent
        self.variable_string = variable_list
        self.variable_list = []
        self.frame = Frame(parent, width=150, height=25, bg='white')
        self.frame.grid(row=row_list, column=col_list)
        self.combo_entry = Entry(self.frame)
        self.combo_entry.pack(side=LEFT)
        self.create_checkbutton_list()
        self.list_button = Button(parent, text='v', command=lambda: self.call_checkbutton_list())
        self.list_button.grid(row=row_list, column=col_list+1)

    def create_checkbutton_list(self):
        self.combo_entry.toplevel = Toplevel()
        self.combo_entry.toplevel.overrideredirect(1)
        self.combo_entry.toplevel.transient()
        self.return_button = Button(self.combo_entry.toplevel, text='v', command=lambda: self.call_checkbutton_list())
        self.return_button.pack(side=TOP, anchor='ne')
        self.frame_button = VerticalScrollbarFrame(self.combo_entry.toplevel)
        self.frame_button.update_scrollbar()

        idx_var = 0
        while idx_var < len(self.variable_string):
            temp = self.variable_string[idx_var]
            self.variable_list.append(IntVar())
            #self.variable_list[idx_var]._name = temp
            l = Checkbutton(self.frame_button.frame, text=temp, variable=self.variable_list[-1])
            l.grid(row=idx_var, sticky='nsw')
            idx_var += 1
        self.frame_button.frame.update_idletasks()
        self.frame_button.canvas.config(scrollregion=self.frame_button.canvas.bbox("all"))
        self.combo_entry.toplevel.withdraw()

    def call_checkbutton_list(self):
        def grab_set_master(parent):
            if isinstance(parent.master, Frame) or isinstance(parent.master, Canvas):
                grab_set_master(parent.master)
            else:
                parent.master.grab_set()

        but_width = self.return_button.winfo_reqwidth()
        self.combo_entry.toplevel.geometry("%dx%d+%d+%d" % (self.combo_entry.winfo_reqwidth()+but_width, 125, self.combo_entry.winfo_rootx(),
                             self.combo_entry.winfo_rooty()))
        if not self.hidden:
            self.hidden =True
            self.combo_entry.toplevel.deiconify()
            self.combo_entry.toplevel.grab_set()
        else:
            self.combo_entry.delete(0, END)
            for var in self.variable_list:
                if var.get():
                    idx = self.variable_list.index(var)
                    self.combo_entry.insert(END, self.variable_string[idx])
                    self.combo_entry.insert(END, ' ')
            self.hidden = False
            self.combo_entry.toplevel.withdraw()
            #self.parent.master.master.master.grab_set()
            grab_set_master(self.parent)


def enable(frame, state):
    for child in frame.winfo_children():
        try:
            child.configure(state=state)
        except:
            pass

def enable_frames(frame, button):
    if isinstance(button, int):
        button_value = button
    else:
        button_value = button.get()
    if button_value == 1:
        if isinstance(frame, list):
            for fr in frame:
                enable(fr, 'normal')
        else:
            enable(frame, 'normal')
    elif button_value == 0:
        if isinstance(frame, list):
            for fr in frame:
                enable(fr, 'disabled')
        else:
            enable(frame, 'disabled')


def make_splash():
    splash = [r" ____  _     _               _,---._",
              r"| __ )(_) __| |___         /'  ,`.  `\ ",
              r"|  _ \| |/ _` / __|       /'`,,'   ;   )",
              r"| |_) | | (_| \__ \      (_   ;  ,-,---'",
              r"|____/|_|\__,_|___/       (;;,,;/--'",
              r"                           \;;;/",
              r" _    _                      /",
              r"|  \/  | __ _ _ __   __ _  __ _  ___ _ __",
              r"| |\/| |/ _` | '_ \ / _` |/ _` |/ _ \ '__|",
              r"| |  | | (_| | | | | (_| | (_| |  __/ |",
              r"|_|  |_|\__,_|_| |_|\__,_|\__, |\___|_|",
              r"                          |___/"]

    return splash + ['Version ' + BidsManager.version]


def run_app():
    from time import sleep

    splsh = make_splash()
    for line in splsh:
        print(line)
        sleep(0.05)
    sleep(0.05)
    notice_license = 'BIDS Manager  Copyright (C) 2018-2020  Aix-Marseille University, INSERM, INS.\n' \
                     'This program is free software: you can redistribute it and/or modify it under the terms of the\n' \
                     'GNU General Public License as published by the Free Software Foundation, either version 3 of the License,\n' \
                     'or any later version.\n'
    print(notice_license)
    sleep(0.2)
    if platform.system() == 'Windows':
        windll.shcore.SetProcessDpiAwareness(1)
    root = Tk()
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.option_add("*Font", "10")
    my_gui = BidsManager(root, width, height)
    root.protocol("WM_DELETE_WINDOW", my_gui.close_window)
    if platform.system() == 'Windows':
        root.state("zoomed")
    elif platform.system() == 'Linux':
        root.attributes('-zoomed', True)
    # MyDialog(root)
    # The following three commands are needed so the window pops
    # up on top on Windows...
    # root.iconify()
    # root.update()
    # root.deiconify()
    root.mainloop()

if __name__ == '__main__':
    run_app()
