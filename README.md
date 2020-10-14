#  BIDS Manager ![BM](bids_manager/bids_manager.ico "BIDS_Manager")
Package to collect, organise and manage neuroscience data in Brain Imaging Data Structure (BIDS) format.

## Version
BIDS Manager v0.2.8

This version of BIDS Manager uses a version of BIDS Uploader which does not yet handle data transfer via SFTP, the SFTP transfer will me publicly available soon.

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

## Tutorial video
A tutorial video explaining you how to convert the example dataset is available [HERE](https://youtu.be/HvJjr6WZNQA)

## Authors
* Main developper: Nicolas Roehri <nicolas.roehri@etu.univ-amu.fr>
* Developpers: Samuel Medina (generic_uploader) <samuel.medinavillalon@gmail.com>, 
		Aude Jegou <aude.jegou@univ-amu.fr>

## License
This project is licensed under the GPLv3 license.

## Comment
If you wish to compile these scripts using PyInstaller 4.0 or above, use the command below:
```
pyinstaller --onefile --icon=bids_manager\\bids_manager.ico --hidden-import PyQt5.sip bids_manager\\bids_manager.py
```
An **example dataset** is available here: https://figshare.com/articles/Example_Dataset_for_BIDS_Manager/11687064
