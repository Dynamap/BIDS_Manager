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
#     Authors: Samuel Medina, 2018-2020

import struct


def anonymize_micromed(file):
    with open(file, "r+b") as f:
        f.seek(175)
        data = f.read(1)
        header_type = struct.unpack('B', data)
        if header_type[0] in [0, 1]:
            f.seek(186 + 3 + 3)
            blank = [0] * 42
            f.write(struct.pack('B' * len(blank), *blank))
        if header_type[0] in [2, 3, 4]:
            f.seek(64)
            blank = [0] * 45
            f.write(struct.pack('B' * len(blank), *blank))
        f.close()