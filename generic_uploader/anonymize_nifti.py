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
#     Authors: Samuel Medina, Nicolas Hemmer, 2022

import nibabel as nib
import os


def anonymize_nifti(file):
    img = nib.load(file)
    #header = img.header
    keys_to_clear = ["db_name", "aux_file"]
    img.header[keys_to_clear] = ""
    filename, ext = os.path.splitext(file)
    new_file = filename + '_copy' + ext
    nib.save(img, new_file)
    os.remove(file)
    os.rename(new_file, file)
