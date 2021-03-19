# Filter data: software example
Software to apply pass band filter to electrophisiology data. This software can be used by BIDS_pipeline because is callable in command line.

## Version 
filter_data v0.1

## Main requirements
* MATLAB Runtime (http://www.mathworks.com/products/compiler/mcr/index.html)
* To use it with BIDS_pipeline, json file describing its parameters. (available in SoftwarePipeline folder)

## Command line
filter_data.exe *input_file* eegfilename *output_directory* outputdirname *low_frequency* 2 *high_frequency* 50 *filter_type* bandpassfir *filter_order* 20

## Comment
You can use this software as an example in BIDS_pipeline.