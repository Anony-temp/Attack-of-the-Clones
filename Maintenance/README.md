Maintenance Measurement
=======================

This repository contains the source code of maintenance measurement tools.

# Running order

To obtain the maintenance feature values, you need to run the code in the following order.

1. Run `python3 Maintain_Parser.py -f [coin url file].csv -s [start date] -e [end date] [-v:option]`

    1.1. `[start date]` and `[end date]` format is `%Y%m%d` like `20180101`.
    
    1.2. `[coin url file].csv` should be csv file. The example filename is `coin_list_git.csv`.

    1.3. `[-v:option]` is the option. If you want to see the steps of selenium, you adds `-v` option.

2. Run `python3 CombineOne.py -o [output filename] -s [start date] -h [mid date] -t [third date] -e [end date]`

    2.1. `[output filename]` is the output filename. The default is `Maintenance.csv`.
    
    2.2. `[start date]` format is `%Y%m%d` like `20180101`.
    
    2.3. `[mid date]` format is `%Y%m%d` like `20180701` for 6 months data.
    
    2.4. `[third date]` format is `%Y%m%d` like `20181001` for 3 months data.
    
    2.5. `[end date]` format is `%Y%m%d` like `20181201` for 12 months data.

### Maintain_Parser.py

`Maintain_Parser.py` code crawls the feature values each from the target repositories' GitHub webpage.

The raw data is written in `raw_data` folder.

### CombineOne.py

`CombineOne.py` code unions the raw data to one result file.

The result file has 32 features with several crypto projects.
