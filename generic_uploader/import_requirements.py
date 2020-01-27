# -*- coding: utf-8 -*-

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

import os
import json


def requirements_extration(requirements_path):
    # read requirements file and try to extract key and values
    # requirements_path = os.path.join(r"C:\softwares\bids_manager\requirements_templates", "requirements_RHU.json")
    with open(requirements_path) as f:
        data = json.load(f)
    print(data)
    ieeg_requirements = data["Requirements"]["Subject"]["Ieeg"]
    anat_requirements = data["Requirements"]["Subject"]["Anat"]
    dwi_requirements = data["Requirements"]["Subject"]["Dwi"]
    protocole_requirements = "protocole"
    return ieeg_requirements, anat_requirements, dwi_requirements, protocole_requirements
    # rajouter dans le requirements le nom du protocole?
