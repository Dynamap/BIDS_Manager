# -*- coding: utf-8 -*-

#     BIDS Uploader collect, creates the data2import requires by BIDS Manager
#     and transfer data if in sFTP mode.
#     Copyright © 2018-2020 Aix-Marseille University, INSERM, INS
#
#     This file is main file of BIDS Uploader.
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

import datetime
import unicodedata
import re
import hashlib


#Put the fonction outside of the classes to call them in other scripts
def valide_date(d):
    try:
        dd = datetime.datetime.strptime(d, '%d/%m/%Y')
    except:
        return False
    else:
        if (dd < datetime.datetime(year=1800, month=1, day=1)) or (dd > datetime.datetime.now()):
            return False
        else:
            return dd.strftime('%d%m%Y')


def valide_mot(mot):
    nfkd_form = unicodedata.normalize('NFKD', mot)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')  # supprime les accents et les diacritiques
    only_ascii_string = only_ascii.decode('ASCII').upper()  # reconvertit les bytes en string
    only_az = re.sub('[^A-Z]', '', only_ascii_string)  # supprime tout ce qui n'est pas [A-Z]
    return only_az


def hash_object(obj):
    clef256 = hashlib.sha256(obj.encode())
    clef_digest = clef256.hexdigest()
    clef = clef_digest[0:12]
    return clef
