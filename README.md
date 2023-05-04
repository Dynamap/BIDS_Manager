![bids manager](icons/bids_manager_icon.png "Bids Manager")

#  BIDS Manager
Package to collect, organise, manage, and analyse neuroscience data in Brain Imaging Data Structure (BIDS) format.

## Version
BIDS Manager version 1.4.3

## Compiled version
You can download a compiled version from [here](https://github.com/Dynamap/BIDS_Manager/releases/download/v1.4.3/bids_manager_1.4.3.zip).

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
* Run analysis with BIDS Manager-Pipeline

## Main Requirements
* Python >= 3.7
* AnyWave, available here: http://meg.univ-amu.fr/wiki/AnyWave
* dicm2nii.exe (is a Windows compiled version of dicm2nii.m https://github.com/xiangruili/dicm2nii) and requires the version 9.5 (R2018b) of the MATLAB Runtime (http://www.mathworks.com/products/compiler/mcr/index.html)

## Dependencies
* pydicom
* PyQt5
* bids-validator
* nibabel
* xlrd
* paramiko
* tkcalendar
* pywin32
* pysimplegui
* scipy
* openpyxl

## How to debug it
1. Take the following folders from ./app_utils folder and move them to the root folder of the project:
   1. deface_needs
   2. SoftwarePipeline
2. Run the script bids_manager.py to start the app.

## Pipelines
You can to do data analysis with softwares defined in SoftwarePipeline. There are two files .json (as templates) for computing ICA and power spectral density with Anywave, but you can add your own software as soon as it works with command line executions. 


## Authors & Maintainers
* BIDS Manager developper: Nicolas Roehri <roehri.nicolas@gmail.com>
* BIDS Uploader developper: Samuel Medina <samuel.medinavillalon@gmail.com>
* BIDS Manager-Pipeline developper: Aude Jegou <jegou.aude@gmail.com>     
* Maintainer: Christian Ferreyra <chrisferreyra13@gmail.com>
* Maintainer: Maria Fratello <maria.fratello97@gmail.com>

## How to cite
* Roehri, N., Medina-Villalon, S., Jegou, A., Colombet, B., Giusiano, B., Ponz, A., & Bénar, C. G., Transfer, collection and organisation of electrophysiological and imaging data for multicenter studies.

## License
This project is licensed under the GPLv3 license.

An **example dataset** is available here: https://figshare.com/articles/Example_Dataset_for_BIDS_Manager/11687064

# BIDS Uploader
Package to transfer data and prepare them for importation in BIDS Dataset. It can be used in local through BIDS Manager
or it can be used in sFTP mode to send data to another center.

## sFTP Mode
To distribute BIDS uploader to different center, you have to compile it with the good information (host(IP), port, ssh key, protocole name, and secret key). These informations have to be filled in the code
generic_uploader\\generic_uploader.py at the lines 239-249. Then, you can compile it with the command below:
```
pyinstaller --onefile --name BIDS_Uploader generic_uploader\\generic_uploader.py
```
To compile bids_uploader for another version of python (windows 32bits) change your python path in Environment Variable

The executable BIDS_uploader.exe can be distributed to the centers with the following files (stored in "config" folder):
* config\\requirements.json (Requirements of the BIDS dataset)
* config\\private_ssh_key