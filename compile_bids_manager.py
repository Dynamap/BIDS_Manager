"""App compiler"""

# Authors: Nicolas Roehri, 2018-2019
#          Aude Jegou, 2019-2020
#          Christian Ferreyra, 2022
#          Maria Fratello, 2022

import os
import shutil

# script params
CREATE_LOCAL_RELEASE = True

# ----------------

# script config
APP_ICON = 'bids_manager\\bids_manager.ico'
APP_LOCATION = 'bids_manager\\bids_manager.py'
EXE_NAME = 'bids_manager'
APP_UTILS = 'app_utils'
VERSION = '_1.4.3'
LOCAL = os.path.abspath(os.curdir)
# ----------------


def _create_release(source_path, dest_path):
    """Create the release by copying the executable from the source.

    Also add the SoftwarePipeline and deface_needs folders.

    Parameters
    ----------
    source_path : str
        Source of the executable.
    dest_path : str
        Destination to copy the executable.
    """
    # creating dir release
    if not os.path.exists(dest_path):
        try:
            os.mkdir(dest_path)
        except Exception as ex:
            raise ex

    try:
        shutil.copy2(os.path.join(source_path, 'dist',
                     EXE_NAME+VERSION+'.exe'), dest_path)
        shutil.copytree(os.path.join(source_path, APP_UTILS, 'SoftwarePipeline'), os.path.join(
            dest_path, 'SoftwarePipeline'), dirs_exist_ok=True)
        shutil.copytree(os.path.join(source_path, APP_UTILS, 'deface_needs'), os.path.join(
            dest_path, 'deface_needs'), dirs_exist_ok=True)
        # for connection with BIDS Manager Server (internal use)
        config_folder = os.path.join(source_path, APP_UTILS, 'config')
        if os.path.exists(config_folder):
            shutil.copytree(config_folder, os.path.join(
                dest_path, 'config'), dirs_exist_ok=True)
    except Exception as ex:
        raise ex


def compile_bmp():
    """Compile bids manager app."""
    # windowed is to prevent the command line to show up
    cmd_line = 'pyinstaller --onefile --name '+EXE_NAME+VERSION \
        + ' --windowed' \
        + ' -F --hidden-import=pydicom.encoders.gdcm --hiddenimport=pydicom.encoders.pylibjpeg --hidden-import "babel.numbers" ' \
        + '--icon='+APP_ICON+' '+APP_LOCATION
    try:
        os.system(cmd_line)
    except Exception as ex:
        print("[ERROR]: The compilation failed")
        return

    print('[INFO]: Conversion is done')

    # creating release
    if CREATE_LOCAL_RELEASE:
        release_path = os.path.join(LOCAL, 'releases', VERSION[1:])

        try:
            _create_release(LOCAL, release_path)
        except Exception as ex:
            print('[ERROR]: Failed to create local release')
            print(ex)

    print('[INFO]: Ready!')


if __name__ == '__main__':
    compile_bmp()
