Attack of the Clones: Measuring the Originality and Security of Bitcoin 'Forks' in the Wild
=============================================================================================

This repository contains the source code of measurement tools used in 'Attack of the Clones.'

The tools consist of 3 parts; Maintenance, originality, and security.

# Code maintenance activity analysis

The source code is in the 'Maintenance' directory.

The data collection process is as follows.

1. Run `python3 Maintain_Parser.py [coin url file].csv [start date] [end date]`

    1.1. `[start date]` and `[end date]` format is `%Y%m%d` like `20180101`.
    1.2. `[coin url file].csv` should be csv file. The example filename is `coin_list_git.csv`.

2. Run `python3 CombineOne.py [output filename] [start date] [mid date] [third date] [end date]`

    2.1. `[output filename]` is the output filename. The default is `Maintenance.csv`.
    2.2. `[start date]` format is `%Y%m%d` like `20180101`.
    2.3 `[mid date]` format is `%Y%m%d` like `20180701` for 6 months data.
    2.4 `[third date]` format is `%Y%m%d` like `20181001` for 3 months data.
    2.5 `[end date]` format is `%Y%m%d` like `20181201` for 12 months data.

# Code similarity analysis

The source code is in the 'Originality' directory.

To measure the similarity, each component will be used.

1. `dataset`

    1.1 In this directory, the dataset files are placed. The examples are `coin_list_git.csv.`
    1.2 There is no source code, but data for the other programs will be placed in these directories.
  
2. `download_latest_altcoin`

    2.1 `Bitcoin_downloader.py` collects the Bitcoin information (e.g., Commit hash, commit date, and zip file) for all commits.
    2.2 `Altcoin_downloader.py` downloads the altcoin's latest commit. It is working with `python3 Altcoin_download.py [target_date]`. `[target_date]` format is `%Y%m%d` like `20190903`. If the latest version fo altcoin is older than the `[target_date],` the latest commit will be downloaded.
  
3. `determine_forking_time`

    3.1 `determine_forking.py` determines the forking time candidates with the Heuristic method 1 and 2 (the detailed is shown in the paper).
    3.2 `final_choice_forking_time.py` determines the forking time with a threshold fixed in `dtermine_forking.py` results.
  
4. `unzip_coins`

    4.1 `unzip_altcoins.py` unzips the altcoins. The zipped files are placed in the `determine_forking_time/Coins` directory, and the directory is a result of `final_choice_forking_time.py.`
    4.2 `unzip_bitcoins.py` unzips all versions of Bitcoin. The zipped files are placed in the `download_latest_altcoin/BTC_versions` directory, and the directory is a result of `Bitcoin_downloader.py.`
  
5. `compare_all_altcoins`

    5.1 `compare_latest_to_latest.py` compares the latest versions of altcoins.
    5.2 `compare_forking_to_latest.py` compares the past versions (forked version) of altcoins with the Bitcoin. The program can be run `python3 compare_forking_to_latest.py  [ray number]`. `[ray number]` is the number of processes that are run at the same time. The default is 1.

# Security vulnerability analysis

The source code is in the 'Security' directory.

To measure the security, run `python3 CVE_Checker.py` with the patch and vulnerable codes.

The dataset files are the same as the dataset, which is used in measuring maintenance and similarity.
