Download Latest Bitcoin & Altcoins
==================================

This folder contains the source code of originality measurement tools.

# Downloading source codes

These codes download all version of the crypto projects using selenium.

1. `Bitcoin_downloader.py` collects the Bitcoin information (e.g., Commit hash, commit date, and zip file) for all commits.
    
2. `Altcoin_downloader.py` downloads the altcoin's latest commit. It is working with `python3 Altcoin_download.py -t [target_date] [-v:optional]`. 
    
    2.1. `[target_date]` format is `%Y%m%d` like `20190903`. If the latest version fo altcoin is older than the `[target_date],` the latest commit will be downloaded.

    2.2. `[-v:optional]` is the option. If you want to see the steps of selenium, you adds `-v` option.

### Bitcoin_downloader.py

`Bitcoin_downloader.py` code downloads all commit of Bitcoin into `BTC_versions` folder.

This code requires large storage because Bitcoin has more 20,000 commits and we download more 20,000 ZIP files.

This is used to discover the historical change of Bitcoin.

### Altcoin_downloader.py

`Altcoin_downloader.py` code downloads the commit which is uploaded at the time we want.

The commit is downloaded in `Coins` folder.
