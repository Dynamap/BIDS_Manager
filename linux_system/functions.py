#!/usr/bin/python3
# -*-coding:Utf-8 -*

import os


def chmod_recursive(this_path, mode, debug=False):
    if os.getuid() == os.stat(this_path).st_uid:
        os.chmod(this_path, mode)
    elif debug:
        print(" Changing permission denied because the directory doesn't belong to the current user !")
    for root, dirs, files in os.walk(this_path):
        for this_dir in [os.path.join(root, d) for d in dirs]:
            if os.getuid() != os.stat(this_dir).st_uid:
                if debug:
                    print("{} can not change permissions of {} belonging to {}".format(os.getuid(), this_dir, os.stat(this_dir).st_uid))
                continue
            else:
                os.chmod(this_dir, mode)
                print("{} changed privileges to {}".format(this_dir, mode))
        for this_file in [os.path.join(root, f) for f in files]:
            if os.getuid() != os.stat(this_file).st_uid:
                if debug:
                    print("{} belongs to {}. So, {} can not set its permissions ".format(this_file, os.stat(this_file).st_uid, os.getuid()))
                continue
            else:
                os.chmod(this_file, mode)
                print("{} changed its privileges to {}".format(this_file, mode))
