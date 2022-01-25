#  BIDS Manager-Pipeline ![BM](bids_manager/bids_manager.ico "BIDS_Manager")
Package to collect, organise, manage and process neuroscience data in Brain Imaging Data Structure (BIDS) format.

## Version
BIDS Manager v0.3.4 BIDS Manager-Pipeline v1.1.0

## How to cite
* Roehri, N., Medina-Villalon, S., Jegou, A., Colombet, B., Giusiano, B., Ponz, A., & Bénar, C. G., Transfer, collection and organisation of electrophysiological and imaging data for multicenter studies. (submitted)

## Features
* Collect data in differents format:
  * DICOM
  * Nifti
  * Micromed (.trc)
  * Brain products (.vhdr)
  * EDF+ (.edf)
  * EEGLAB (.set)
  * 4D neuroimaging 
* Organise data in BIDS format
* Offer graphical interface to visualise/manage BIDS dataset

## Main Requirements
* Python 3.7
* AnyWave, available here: http://meg.univ-amu.fr/wiki/AnyWave
* dicm2nii.exe (is a Windows compiled version of dicm2nii.m https://github.com/xiangruili/dicm2nii) and requires the version 9.5 (R2018b) of the MATLAB Runtime (http://www.mathworks.com/products/compiler/mcr/index.html)
  or dcm2niix, available here: https://www.nitrc.org/plugins/mwiki/index.php/dcm2nii:MainPage
  
## Python library required
* pydicom
* PyQt5
* bids-validator
* nibabel
* xlrd
* paramiko
* tkcalendar
* pywin32
* pysimplegui

## Tutorial video
A tutorial video explaining you how to convert the example dataset and how to launch analysis is available [HERE](https://www.youtube.com/watch?v=oFFJy5q6e3o)

## Authors
* BIDS Manager developper: Nicolas Roehri <roehri.nicolas@gmail.com>
* BIDS Manager-Pipeline developper: Aude Jegou <jegou.aude@gmail.com>
* BIDS Uploader developper: Samuel Medina (generic_uploader) <samuel.medinavillalon@gmail.com>, 

## License
This project is licensed under the GPLv3 license.

## Comment
If you wish to compile these scripts using PyInstaller 4.0 or above, use the command below:
```
pyinstaller --onefile --icon=bids_manager.ico --hidden-import PyQt5.sip bids_manager\\bids_manager.py
```
An **example dataset** is available here: https://figshare.com/articles/Example_Dataset_for_BIDS_Manager/11687064
An **example BIDS dataset** is available here: https://figshare.com/articles/dataset/BIDS_dataset_for_BIDS_Manager-Pipeline/19046345

# BIDS Uploader
Package to transfer data and prepare them for importation in BIDS Dataset. It can be used in local through BIDS Manager
or it can be used in sFTP mode to send data to another center.

## sFTP Mode
To distribute BIDS uploader to different center, you have to compile it with the good information (host(IP), port, ssh key, protocole name, and secret key). These informations have to be filled in the code
generic_uploader\\generic_uploader.py at the lines 239-249. Then, you can compile it with the command below:
```
pyinstaller --onefile --name BIDS_Uploader generic_uploader\\generic_uploader.py
```
The executable BIDS_uploader.exe can be distributed to the centers with the following files (stored in "config" folder):
* config\\requirements.json (Requirements of the BIDS dataset)
* config\\private_ssh_key

## BIDS Manager-Pipeline
To test BMP, you can use the AnyWave's plugins (i.e. H2, ICA, spectral, etc) or filter_data in the directory software_test

## Compiled version
You can download a compile version here: https://figshare.com/articles/software/BIDS_Manager-Pipeline_compiled_verison/19062312
