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

def anonymize_deltamed(file):
    with open(file, "r+b") as f:
        f.seek(290)
        while True:
            header = f.read(8)
            values = struct.unpack("II", header)
            if values[0] == 0xCAFD0301:
                # get pos
                pos = f.tell()
                patient = f.read(50)
                name = struct.unpack('50s', patient)
                #print name
                f.seek(pos)
                blank = [0] * 90
                f.write(struct.pack('B'*len(blank), *blank))
                f.flush()
                f.close()
                break
            if values[0] == 0xCAFD0300:
                continue
            if values[1]:
                f.read(values[1])

