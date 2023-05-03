# -*- coding: utf-8 -*-

#     BIDS Uploader collect, creates the data2import requires by BIDS Manager
#     and transfer data if in sFTP mode.
#     Copyright © 2018-2020 Aix-Marseille University, INSERM, INS
#
#     This file is part of BIDS Uploader.
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
#     Authors: Aude Jegou, 2018-2020


def anonymize_edf(file):
    """Anonymizes a EDF file (from Nicolet One)
      WARNING overwrites the file !
    """
    f = open(file, 'r+b')
    # f.seek(88)
    # if f.read(9).decode('ascii') != 'Startdate':
    #     print("No Startdate in file : probably not EDF -> no anonymization !")
    #     return
    try:
        f.seek(8)
        f.write(''.ljust(80, ' ').encode('ascii'))
        f.close()
    except:
        print("probably not EDF -> no anonymization !")
        return


def get_patient_info(file):
    f = open(file, 'r+b')
    f.seek(192)
    isEdfPlus = False
    isSpecial = False
    if f.read(4).decode('ascii') == 'EDF+':
        isEdfPlus = True
    f.seek(8)
    try:
        patientInfo = f.read(80).decode('ascii').rstrip()
        if isEdfPlus:
            patientInfo = patientInfo.split(' ')
            patBirthdate = patientInfo[2]
            patName = patientInfo[3]
        else:
            patientInfo = patientInfo.split(' ')
            patName = ''
            for elt in patientInfo:
                if any(e.isdigit() for e in elt):
                    patBirthdate = elt
                elif len(elt) > 1:
                    patName += '-' + elt
                    patBirthdate = ''
    except:
        f.seek(8)
        patientInfo = f.read(80).decode('latin-1').rstrip()
        isEdfPlus = False
        isSpecial = True
        if isSpecial:
            patientInfo = patientInfo.split(' ')
            patName = '-'.join(patientInfo[0:2])
            patBirthdate = patientInfo[2]
    patBirthdate = patBirthdate.split('-')
    for val in patBirthdate:
        if val:
            if val.isnumeric() and len(val) == 2:
                day = val
            elif val.isnumeric() and len(val) == 4:
                year = val
            elif val.lower().startswith('jan') or val.lower().startswith('janv.'):
                month = '01'
            elif val.lower().startswith('feb') or val.lower().startswith('fev') or val.lower().startswith('févr.'):
                month = '02'
            elif val.lower().startswith('mar') or val.lower().startswith('mars.'):
                month = '03'
            elif val.lower().startswith('apr') or val.lower().startswith('avr') or val.lower().startswith('avri.'):
                month = '04'
            elif val.lower().startswith('may') or val.lower().startswith('mai') or val.lower().startswith('mai.'):
                month = '05'
            elif val.lower().startswith('jun') or val.lower().startswith('juin') or val.lower().startswith('juin.'):
                month = '06'
            elif val.lower().startswith('jul') or val.lower().startswith('juil') or val.lower().startswith('juil.'):
                month = '07'
            elif val.lower().startswith('aug') or val.lower().startswith('aou') or val.lower().startswith('août.'):
                month = '08'
            elif val.lower().startswith('sep') or val.lower().startswith('sept.'):
                month = '09'
            elif val.lower().startswith('oct') or val.lower().startswith('octo.'):
                month = '10'
            elif val.lower().startswith('nov') or val.lower().startswith('nove.'):
                month = '11'
            elif val.lower().startswith('dec') or val.lower().startswith('déce.'):
                month = '12'
    try:
        birthday = day + month + year
    except:
        birthday = '11111111'
    try:
        if '-' in patName:
            [lastname, firstname] = patName.split('-')
        elif ',' in patName:
            [lastname, firstname] = patName.split(',')
        elif ' ' in patName:
            [lastname, firstname] = patName.split(' ')
        elif '_' in patName:
            [lastname, firstname] = patName.split('_')
    except:
        lastname = patName
        firstname = ''

    return lastname, firstname, birthday
