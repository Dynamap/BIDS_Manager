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
#     Authors: Samuel Medina, 2018-2021

import shutil
import paramiko
import os
import hashlib
import time


def upload_files(ssh_channel, sftp_channel, original_dir, target_dir):
    # upload
    orig_dir = os.path.basename(original_dir)
	# =============================
	# ===== trouver un moyen de savoir si linux based or windows based server_root_path
	# ask something to it to see if error or not???
	# =============================
    new_target = target_dir + "/" + orig_dir
    sftp_channel.mkdir(new_target)
    sftp_channel.chmod(new_target, 0o777)
    from_dir = os.path.normpath(original_dir)
    from_dir_linux_like = "/" + os.path.normpath(original_dir).replace("\\", "/").strip("/")
    for items in os.listdir(from_dir):
        max_by_folder = len(os.listdir(from_dir))
        from_path = os.path.join(from_dir, items)
        new_path = new_target + "/" + items
        new_path_4shell = '"' + new_target + "/" + items + '"'
        if os.path.isfile(from_path):
            sftp_channel.put(from_path, new_path, confirm=True)
            stdin, stdout, stderr = ssh_channel.exec_command(('sha256sum ' + new_path_4shell))
            target_shasum = stdout.readlines()[0]
            target_shasum = target_shasum.split(' ')[0]
            sha256_hash = hashlib.sha256()
            with open(from_path, 'rb') as f:
                # toto = f.read()
                # Read and update hash string value in blocks of 1000K
                for byte_block in iter(lambda: f.read(1024 * 1024), b""):
                    sha256_hash.update(byte_block)
            # source_shasum = hashlib.sha256(toto).hexdigest()
            source_shasum = sha256_hash.hexdigest()
            attempt_number = 0
            if target_shasum != source_shasum and attempt_number < 4:
                attempt_number += 1
                time.sleep(2*attempt_number)
                state, sent_file_number = upload_files(ssh_channel, sftp_channel, original_dir, target_dir)
            if attempt_number > 3:
                # w = QtWidget.QWidget(self)
                # QtWidget.QMessageBox.critical(w, "Error", "Problème de transfert. Réessayer plus tard")
                return 0
        # else:
		#	 upload_files(sftp, from_path, to_path + "/" + items, total_to_send)
        #    state, sent_file_number = upload_files(ssh_channel, sftp_channel, from_path, new_target)
    return True


def data_transfert_sftp(host, port, username, private_key_path, password, forlder2send, target_dir):
    if not private_key_path and not password:
        error_message = "no key or password for connection"
        return error_message
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if private_key_path:
        key = paramiko.RSAKey.from_private_key_file(private_key_path)
        ssh.connect(host, port, username, pkey=key)
    else:
        if password:
            ssh.connect(host, port, username, password=password)
    try:
        ssh.get_transport().is_active()
        sftp = ssh.open_sftp()
		# --------------------------------------
		# tester si linux or wondows based server ??
        stdin, stdout, stderr = ssh.exec_command('uname')
        os_type = stdout.readlines()[0].replace('\n', '')
        if os_type.lower() == 'linux' or os_type.lower() == 'darwin':
            separator = '/'
        elif os_type.lower() == 'msys':
            separator = '\\'
		# --------------------------------------
        # zipper le dossier/fichier et envoyer le zip
        folder_filename = os.path.split(forlder2send)[1]
        new_folder_dest = os.path.join(forlder2send, folder_filename)
        shutil.make_archive(forlder2send, 'tar', forlder2send)
        for files in os.listdir(forlder2send):
            if os.path.isdir(os.path.join(forlder2send, files)):
                shutil.rmtree(os.path.join(forlder2send, files))
            else:
                os.remove(os.path.join(forlder2send, files))
        shutil.move(forlder2send + ".tar", new_folder_dest + ".tar")
        # =========================================================================
        stdin, stdout, stderr = ssh.exec_command('pwd')
        server_root_path = stdout.readlines()[0].replace('\n', '')
        # try:
        uploaded_folder = server_root_path + separator + target_dir
        stdin, stdout, stderr = ssh.exec_command('[ -d ' + uploaded_folder + ' ] && echo 1')
        existing_dir = stdout.readlines()
        if not existing_dir:
            ssh.exec_command("mkdir -m 777 " + uploaded_folder)
        upload_status = upload_files(ssh, sftp, forlder2send, uploaded_folder)
        # =========================================================================
        # Dezipper le fichier une fois bien transférer
        if upload_status:
            stdin, stdout, stderr = ssh.exec_command(
                'tar -xf ' + uploaded_folder + separator + folder_filename + separator + folder_filename + ".tar" + " -C " + uploaded_folder + separator + folder_filename)
            message = stderr.readlines()
            if not message:
                stdin, stdout, stderr = ssh.exec_command(
                    'rm -r ' + uploaded_folder + separator + folder_filename + separator + folder_filename + ".tar")
                message = stderr.readlines()
                shutil.rmtree(forlder2send)
        # =========================================================================
    except Exception as e:
        print(e)
        try:
            sftp.close()
            ssh.close()
        except:
            pass
        return e
