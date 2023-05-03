# Changelog
All notable changes to BIDS Manager will be documented in this file.

## [v1.4.3] 2023-02-24 (and previous 1.4.x versions)
### Added
- Integration with BIDS Manager server.
- Config folder for configuration files like server information and remote databases.
- Inconsistencies when parsing database.
- The possibility to put multiple values in the participants tsv (delimiter is ;).
- Concurrency managment when multiple users connect to the same database.
### Changed
- Nothing
### Fixed
- Command line for Anywave convertion.
- Statistical table when there are two tsv files and is unstack.

## [v1.3.3] 2022-11-14
### Added
- Nothing added in this version.
### Changed
- Taking anywave montage file
### Fixed
- Nifti anonymization 

## [v1.3.1] 2022-07-25
In this version we get back to the previous app name, Bids Manager.
### Added
- Nothing added in this version.
### Changed
- Names and versions in BIDS Manager's app labels.
- Improved compiler file.
- bmp_utils is now app_utils.
  
### Fixed
- Excel .xlsx file compatibility.
- Statistical table with gardel regions. Now the excel without column names is catched.
- Nifti files anonymisation.
- Moving MEG files for anywave.
- Select subjects in listbox.
- Saving statistical table in different location
- Importation error when modality appears in the name.

## [v1.3.0] 2022-06-28
In this new release, master and bids_with_pipelines branches are unified. 
Therefore the versioning is unified in one version code.
For now on the last 3 compiled versions will be saved in releases folder.
Also, the new versions will be available at gitlab's releases.

### Added
- New version of ica.json file for taking into account the different modalities
- bmp_utils folder is the ground truth for the configuration files (requirements, SoftwarePipeline, etc)
- Releases folder with the last 3 compiled versions

### Changed
- SoftwarePipeline and config folders in project's root path is for running in debug mode (dev)
  
### Fixed
- Remove method for MEG folder
- Multiple pop-ups warnings for MEG files in the anonymization stage during importation
- Vhdr checking during importation (issue #74)
- Interface for statistic table (issue #73)
 
## [v0.3.4] - [v1.2.0] 2022-03-14
### Added
- Possibility to create a stack or unstcak statistical table
- Saving the dirname of the derivatives in the Parsing (i.e. need to parse with this version)
- Adding the type montage as input, possibility to take from raw or derivatives
- Adding comments in bids_pipeline script
- Move anywave files during refresh

### Fixed
- Refreshing of the interface, it is now blocked while clicking on checkbuttonlist
- Some bugs in display of the interface to select subject and parameters
- Problem in getting boolean value to create the interface
- Problem by using temporary folder to analyse with AnyWave plugin while the user don't have the permission to write

## [v0.3.4] - [v1.1.0] 2022-01-24
### Added
- Parsing the anywave folder now

### Changed
- To create the statistic table, user must choose the analysis folder that should appear in the table.

### Fixed
- Refresh data in GUI for Analysis

## [v0.3.4] - [v1.0.0] 2021-11-29
### Added
- Menu AnyWave, in this menu, you can access to AnyWave website to download the last version. There is also button to handle
the AnyWave files saved in derivatives
- Button to "Add Module", meaning creating the json file describing the pipeline and adding it to the list
- Add montage and 4D as "Type" in Input for json description of software

### Changed
- Standardized the keys of the json file to describe software in BIDS-Pipeline
- The way to handle the folder "common" in derivatives/anywave, now the AnyWave files are not automatically copied in


## [v0.3.3] - 2021-10-29
### Added
- possibility to chose as input MEG folder or MEG file for pipeline analysis
- function to read and extract information from vhdr, and vmrk files

### Fixed
- AnyWave plugin: while the input files are in derivatives, it creates the required files to do the analysis(using montage file, channel file and events file)
- Name to save the log file
- Combination mode to mix multiple inputs has been improved
- Improving the way to compare dataset-description of pipelines to choose the good output folder
- Fixed issue while user don't have full controle of the dataset, is still able to run pipeline (plugin Anywave)

## [v0.3.2] - 2021-08-06
### Added
- Progress bar to see the progression of the analysis (required PySimpleGUI library)
- Check in data2import to avoid special character in the name

## [v0.3.1] - 2021-04-30
### Added
- Possibility to apply the change of the name or type of the electrode on multiple files
- Extension '.mtg' and '.mrk' to be parsed in derivatives and called as input in BP
- Management of multiple access to the database
- Write the command line used for the process in derivatives/bids_pipeline/command_line
- Interface Dynamical, the parameters are updated according to the subject selection
- Possibility to write the results of the analysis in local directory
- Possibility to select subject that has not been done in previous analysis, and write automatically the results in this
folder
- Can limited the events write in the electrophysiology data by creating a file names markers_nomenclatures.json
- Command line used to launch the software are now saved in derivatives/bids_pipeline/command_line
- If an analysis requires to read the events files of each subject, the events are saved in a json file in derivatievs/bids_pipeline/elements_by_subject

### Fixed
- Taking into account multiple session to check the integrity of electrode names

### Changed
- During parsing, anywave files are saved in a derivatives folder anywave/username
- Possibility to run analysis on multiple combination of inputs, for that you need to add the key 'combinationmode' in
the dict input of your json file (describing the software) and set it at true.

## [v0.3.0] - 2021-03-10
### Added
- Deface with SPM

## [v0.2.9] - 2021-02-19
### Added
- BiDS Uploader can transfer data in sFTP mode, possibility to compile only BIDS Uploader to give to other center
- Export/Merge button, it can be used to export data or merge 2 BIDS dataset

### Fixed
- While subject is removed in derivatives folder, it is also removed from the dataset_decription.json
- Once the analysis is done, the dataset_description is updated with the subject analysed and the empty folders are removed
- When no subject are selected, ask the user if he wants to do analysis on all subject
- In batch mode, can now launch the same process one after the other

## [v0.2.8] - 2020-10-14
### Added
- PET modality
- Anonymisation of EDF format
- Scrollbar in BIDS Uploader
- Tutorial video
- Possibility to take freesurfer files as input of process (BIDS Pipeline)
- Possibility to rename the variant of the derivatives folder (pipelinename-variant)
- Specificity to anywave plugin to take into account montage file in the process


### Fixed
- Issue with phantom subject (If error in subject importation, subject won't be in the parsing)
- Adapting the GUI to small monitor
- Issue while comparing the pipeline folders to find the good one to write the results
- Sort the elements from list in the requirements file


### Changed
- Arguments for boolean in json file describing the pipeline should be written as {"default":true/false, "incommandline": true/false}
=> if "incommandline":true, the parameter will be displayed in the command line like this "pipeline param true/false"
=> if "incommandline":false, the parameter will be displayed in the command line only if its value is true, else it won't be displayed like this "pipeline param" or "pipeline"

