# Changelog
All notable changes to BIDS Manager-Pipeline will be documented in this file.

## [Unreleased]
- Adding the possibility to Export/Merge BIDS dataset (in progress)

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