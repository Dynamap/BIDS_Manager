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
#     Authors: Aude Jegou, 2018-2020


def anonymize_edf(file):
    """Anonymizes a EDF file (from Nicolet One)
      WARNING overwrites the file !
    """
    f = open(file, 'r+b')
    f.seek(88)
    if f.read(9).decode('ascii') != 'Startdate':
        print("No Startdate in file : probably not EDF -> no anonymization !")
        return
    f.seek(8)
    f.write(''.ljust(80, ' ').encode('ascii'))
    f.close()


def get_patient_info(file):
    f = open(file, 'r+b')
    f.seek(192)
    isEdfPlus = False
    if f.read(4).decode('ascii') == 'EDF+':
        isEdfPlus = True
    f.seek(8)
    patientInfo = f.read(80).decode('ascii')
    if isEdfPlus:
        patientInfo = patientInfo.split(' ', 3)
        patBirthdate = patientInfo[2]
        patName = patientInfo[3]
    else:
        patientInfo = patientInfo.split(' ', 4)
        patName = ''
        for elt in patientInfo:
            if any(e.isdigit() for e in elt):
                patBirthdate = elt
            elif len(elt) > 1:
                patName += '-' + elt
                patBirthdate = ''
    patBirthdate = patBirthdate.split('-')
    for val in patBirthdate:
        if val:
            if val.isnumeric() and len(val) == 2:
                day = val
            elif val.isnumeric() and len(val) == 4:
                year = val
            elif val.lower().startswith('jan'):
                month = '01'
            elif val.lower().startswith('feb') or val.lower().startswith('fev'):
                month = '02'
            elif val.lower().startswith('mar'):
                month = '03'
            elif val.lower().startswith('apr') or val.lower().startswith('avr'):
                month = '04'
            elif val.lower().startswith('may') or val.lower().startswith('mai'):
                month = '05'
            elif val.lower().startswith('jun') or val.lower().startswith('juin'):
                month = '06'
            elif val.lower().startswith('jul') or val.lower().startswith('juil'):
                month = '07'
            elif val.lower().startswith('aug') or val.lower().startswith('aou'):
                month = '08'
            elif val.lower().startswith('sep'):
                month = '09'
            elif val.lower().startswith('oct'):
                month = '10'
            elif val.lower().startswith('nov'):
                month = '11'
            elif val.lower().startswith('dec'):
                month = '12'
    try:
        birthday = day+month+year
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
