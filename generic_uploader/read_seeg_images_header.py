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
#     Authors: Samuel Medina, 2018-2020

import struct
import os
import pydicom
import nibabel as nib
from .anonymize_edf import get_patient_info


def read_headers(file, modality):
    filename, file_extension = os.path.splitext(str(file))
    file_extension = file_extension.lower()
    if file_extension == ".trc":
        with open(file, "rb") as f:
            f.seek(175)
            data = f.read(1)
            header_type = struct.unpack('B', data)
            if header_type[0] in [0, 1]:
                f.seek(186 + 3 + 3)
                lastname = f.read(22)
                lastname = struct.unpack('22s', lastname)
                lastname = lastname[0].decode('ASCII')
                firstname = f.read(20)
                firstname = struct.unpack('20s', firstname)
                firstname = firstname[0].decode('ASCII')
                birthdate = f.read(3)
                A = struct.unpack('3s', birthdate)
            if header_type[0] in [2, 3, 4]:
                f.seek(64)
                lastname = f.read(22)
                lastname = struct.unpack('22s', lastname)
                lastname = lastname[0].decode('ASCII')
                firstname = f.read(20)
                firstname = struct.unpack('20s', firstname)
                firstname = firstname[0].decode('ASCII')
                birthdate0 = f.read(3)
                A = struct.unpack('3B', birthdate0)
            if A[1] < 10:
                day= "0" + str(A[1])
            else:
                day = str(A[1])
            if A[0] < 10:
                month = "0" + str(A[0])
            else:
                month = str(A[0])
            year = str(A[2] + 1900)
            birthdate = day + month + year
            f.close()
            lastname.replace(' ', '')
            firstname.replace(' ', '')
            lastname.replace('  ', '')
            firstname.replace(' ', '')
            # return lastname, firstname, birthdate
    elif file_extension == ".eeg":
        with open(file, "rb") as f:
            f.seek(290)
            while True:
                header = f.read(8)
                values = struct.unpack("II", header)
                if values[0] == 0xCAFD0301:
                    # get pos
                    pos = f.tell()
                    patient = f.read(50)
                    lastname = struct.unpack('50s', patient)[0].decode('ASCII')
                    lastname = lastname.replace(' ', '')
                    prenom = f.read(30)
                    firstname = struct.unpack('30s', prenom)[0].decode('ASCII')
                    date = f.read(10)
                    origbirthdate = struct.unpack('10s', date)[0].decode('ASCII')
                    origbirthdate = origbirthdate.replace(' ', '')
                    origbirthdate = origbirthdate.replace("/", "")
                    birthdate = origbirthdate[0:4] + origbirthdate[4:8]
                    break
    elif file_extension.lower() == ".edf":
        lastname, firstname, birthdate = get_patient_info(file)
    elif (file_extension == ".dcm" or file_extension == "" or file_extension == ".ima") and (not os.path.isdir(file) and modality != 'Meg'):
        dataset = pydicom.read_file(filename + file_extension)
        name = str(dataset.data_element("PatientName").value)
        A = name.split("^")
        if A.__len__() > 1:
            lastname = A[0]
            firstname = A[1]
        else:
            lastname = firstname = A[0]
        try:
            MRIbirthdate = dataset.data_element("PatientBirthDate")
            birth = str(MRIbirthdate).split("DA:")
            B = birth[1]
            B = B.replace(" ", "")
            B = B.replace("'", "")
            birthdate = B[6:8] + B[4:6] + B[0:4]
        except:
            birthdate = "1111111"
        lastname = lastname.lower()
        firstname = firstname.lower()
    elif file_extension == ".nii":
        # ajouter ici la lecture des niftii
        img = nib.load(file)
        header = img.header
        idx_of_name = [idx for idx in list(range(0, len(header.keys()))) if header.keys()[idx] == 'db_name']
        idx_of_name = idx_of_name[0]
        header_info_list = header.structarr.tolist()
        lastname = header_info_list[idx_of_name].decode("utf-8")
        firstname = ''
        birthdate = ''
    else:                                                     # prendre en compte aussi les .vhdr
        lastname = firstname = ""
        birthdate = "1111111"
    # rajouter ici la lecture du .vhdr

    return lastname, firstname, birthdate
