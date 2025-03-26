# JRA-3Q_WRF_download
Python code that downloads data from JRA-3Q reanalysis (https://rda.ucar.edu/datasets/d640000/) and converts it to WRF intermediate format, which is accepted by the metgrid. When running WPS ungrib should be skipped.

geopotential.nc landmask.nc and JRA_names.txt files have to be stored in the var_path directory.

Raw *.nc files are downloaded to the save_path directory.

Output files are stored in the output_path directory.

Soil porosity is assumed constant (0.43 by default) and can be changed.

By default output filenames contain only dates. pref can be changed to give prefix to the filenames.

Modified METGRID.TBL file is provided.

Output contains 46 pressure levels and 7 soil levels.
