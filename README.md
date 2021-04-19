#  BIDS Manager ![BM](bids_manager.ico "BIDS_Manager")
Package to collect, organise and manage neuroscience data in Brain Imaging Data Structure (BIDS) format.


## Version
BIDS Manager v0.2.8

This version of BIDS Manager uses a version of BIDS Uploader which does not yet handle data transfer via SFTP, the SFTP transfer will me publicly available soon.

## How to cite
* Roehri, N., Medina Villalon, S., Jegou, A. et al. Transfer, Collection and Organisation of Electrophysiological and Imaging Data for Multicentre Studies. Neuroinform (2021). https://doi.org/10.1007/s12021-020-09503-6

## Features
* Collect data in differents format:
  * DICOM
  * Micromed (.trc)
  * Brain products (.vhdr)
  * EDF+ (.edf)
  * 4D neuroimaging 
* Organise data in BIDS format
* Offer graphical interface to visualise/manage BIDS dataset

## Main Requirements
* Python 3.7
* AnyWave, available here: http://meg.univ-amu.fr/wiki/AnyWave
* dicm2nii.exe (is a Windows compiled version of dicm2nii.m https://github.com/xiangruili/dicm2nii) and requires the version 9.5 (R2018b) of the MATLAB Runtime (http://www.mathworks.com/products/compiler/mcr/index.html)

## Python library required
* future
* pydicom
* PyQt5

## Compiled Version for Windows 10
The compile version of BIDS Manager can be downloaded here: https://figshare.com/articles/BIDS_Manager/11728872

## Example dataset
An **example dataset** is available here: https://figshare.com/articles/Example_Dataset_for_BIDS_Manager/11687064

## Tutorial video
A tutorial video explaining you how to convert the example dataset is available [HERE](https://youtu.be/HvJjr6WZNQA)

## Authors
* Main developer: Nicolas Roehri <roehri.nicolas@gmail.com>
* Developers: Samuel Medina (generic_uploader) <samuel.medinavillalon@gmail.com>, 
		      Aude Jegou <aude.jegou@univ-amu.fr>

## License
This project is licensed under the GPLv3 license.

## Comment
If you wish to compile these scripts using PyInstaller 4.0 or above, use the command below:
```
pyinstaller --onefile --icon=bids_manager.ico --hidden-import PyQt5.sip bids_manager\\bids_manager.py
```

# BIDS Uploader
Package to transfer data and prepare them for importation in BIDS Dataset. It can be used in local through BIDS Manager
or it can be used in sFTP mode to send data to another center.

## sFTP Mode
To distribute BIDS uploader to different center, you have to compile it with the good information (host(IP), port, ssh key, protocole name, and secret key). These informations have to be filled in the code
generic_uploader\\generic_uploader.py at the lines 239-249. Then, you can compile it with the command below:
```
pyinstaller --onefile --name BIDS_Uploader generic_uploader/generic_uploader.py
```
The executable BIDS_uploader.exe can be distributed to the centers with the following files (stored in "config" folder):
* config\\requirements.json (Requirements of the BIDS dataset)
* config\\private_ssh_key