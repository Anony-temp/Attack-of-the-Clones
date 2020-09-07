import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from libs.logging import LOGD, initLog
from libs.seleniumCustom import custom_selenium
from libs.simpleFunctions import searchFiles, readCSV, custom_replace, DownloadProcess, DownZip

def initResults():
    fp = open('BTC_logs.csv', 'w')
    fp.close()

def Downloader(handler):
    LOGD("Open the URL: https://github.com/bitcoin/bitcoin", (), 1)
    handler.OpenURL('https://github.com/bitcoin/bitcoin')
    commitNum = handler.GetCommitNum()
    if commitNum == -1:
        LOGD("Error: get commit number. Symbol: BTC", (), 10, 1)
    LOGD("The number of commits is %d.", (commitNum), 1)
    LOGD("Open the commit list page.", (), 1)
    handler.OpenURL('https://github.com/bitcoin/bitcoin/commits')
    LOGD("Searching a last page...", (), 1)
    handler.SearchLastPage(commitNum)
    LOGD("Last page URL is %s", (handler.driver.current_url), 1)
    LOGD("Downloading all versions of bitcoin...", (), 1)
    current_url = handler.driver.current_url
    new_url = current_url
    while True:
        codes = handler.FindAll('div')
        for code in codes:
            code = code.decode()
            if 'div class="commits-listing commits-listing-padded' in code:
                lines = code.split('commit-group-title')
                for partial in lines[::-1]:
                    if 'Commits on ' not in partial:
                        continue
                    tmp = custom_replace(partial.split('Commits on ')[1].split('</div>')[0], '\n ')
                    commits = partial.split('<li class="commit')
                    for commit in commits[::-1][:-1]:
                        boxes = commit.split('class="commit-title')[1].split('class="hidden-text')[0].split('data-pjax="true" href="')
                        commitLink = boxes[1].split('"')[0]
                        hashValue = commitLink.split('/')[-1]
                        down_path = DownZip('https://github.com/bitcoin/bitcoin/archive/' + hashValue + '.zip', 'BTC_versions/BTC_' + hashValue + '.zip')
                        if down_path == -1:
                            LOGD("ERROR.... Hash value: %s, URL: %s", (hashValue, commitLink), 10, 1)
                            continue
                        LOGD("Downloaded... in %s.", ('BTC_' + hashValue + '.zip'), 2)
                break
        new_url = handler.FindNewerPage(codes)
        if new_url == 0:
            return -1
        if current_url != new_url:
            current_url = new_url
            handler.OpenURL(new_url)
            LOGD("New URL %s", (new_url), 1)

if __name__ == '__main__':
    initLog()
    if not os.path.exists('BTC_versions'):
        os.mkdir('BTC_versions')
    if os.path.exists('BTC_logs.csv'):
        LOGD("Please backup the result file.")
        sys.exit()
    initResults()
    LOGD("Program Starting! Name: %s", (os.path.basename(__file__)))
    LOGD("Open selenium drivers")
    handler = custom_selenium(sleep_time = 2)
    LOGD("Into the downloading process...")
    Downloader(handler)
    handler.Destroy()
    LOGD("Program End! Name: %s", (os.path.basename(__file__)))
