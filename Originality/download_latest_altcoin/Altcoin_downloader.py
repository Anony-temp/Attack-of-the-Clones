from selenium import webdriver
from bs4 import BeautifulSoup as bs

import os, sys
import getopt
import urllib.request as urllib2
from time import ctime, sleep, time

from pyvirtualdisplay import Display

from colorama import init
from colorama import Fore

def LOGD(string, attr = (), depths = 0, color = 0):
    if color == 0:
        print(Fore.WHITE + ' ' * depths + '[%s] ' % (ctime()) + string % (attr))
    elif color == 1:
        print(Fore.RED + ' ' * depths + '[%s] ' % (ctime()) + string % (attr))
    fp = open("logs.txt", "a")
    fp.write(' ' * depths + '[%s] ' % (ctime()) + string % (attr) + '\n')
    fp.close()

class Downloader:
    def __init__(self, target_date, display_visible = False):
        fp = open("logs.txt", 'w')
        fp.close()
        self.driver_wait_time = 5
        self.sleep_time = 1
        self.todayDate = [target_date]
        self.download_folder = "Coins"
        self.Months = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
        if not os.path.exists(self.download_folder):
            os.mkdir(self.download_folder)
        self.urlList = {}
        self.dp_visible = display_visible
        if not display_visible:
            self.display = Display(visible=0, size=(800, 600))
            self.display.start()
        self.driver = webdriver.Firefox()

    def Destroy(self):
        self.driver.quit()
        if not self.dp_visible:
            self.display.stop()
    
    def OpenURL(self, url):
        self.driver.get(url)
        self.driver.implicitly_wait(self.driver_wait_time)
        sleep(self.sleep_time)

    def readCSV(self, filename):
        # Symbol, Url, Note, Lang
        fp = open(filename, 'r', encoding='utf-8', errors='ignore')
        lines = fp.readlines()
        fp.close()
        for line in lines:
            line = line.replace('\n','').split(',')
            if line[1] == '':
                continue
            counter = 0
            while True:
                if line[0] + str(counter) not in self.urlList:
                    break
                counter = counter + 1
            self.urlList[line[0] + str(counter)] = {'URL': line[1],'Lang': line[3]}

    def Download(self):
        LOGD("Start downloading commits.", (), 1)
        count = 0
        for symbol in self.urlList:
            LOGD("Target coin: %s", (symbol), 2)
            LOGD("Open URL: %s", (self.urlList[symbol]['URL']), 3)
            self.OpenURL(self.urlList[symbol]['URL'])
            date = self.SearchDatetime()
            if date == -1:
                LOGD("Page disappeared.", (), 10, 1)
                continue
            LOGD("Current commit date: %s", (date), 3)
            if int(date) > int(self.todayDate[0]):
                LOGD("Start to find commit lists.", (), 4)
                listURL = self.urlList[symbol]['URL'] + '/commits'
                for today in self.todayDate:
                    if int(date) > int(today):
                        self.OpenURL(listURL)
                        LOGD("Start sequential searching.", (), 4)
                        listURL = self.SequentialSearch(today)
                        if listURL == -1:
                            continue
                        date = self.SearchDatetime()
                        if date == -1:
                            LOGD("Commit page disappeared... %s", (self.driver.current_url.encode('utf-8')), 10, 1)
                    count = self.DownloadProcess(count, date, symbol)
            else:
                count = self.DownloadProcess(count, date, symbol)
        LOGD("Total downloaded coins: %d", (count), 1)

    def DownloadProcess(self, count, date, symbol):
        LOGD("Page URL: %s", (self.driver.current_url.encode('utf-8')), 3)
        LOGD("Get the download zip addr.", (), 3)
        zip_addr = self.FindDownloadZipButton()
        if zip_addr == -1:
            LOGD("Finding the download button failed...", (), 10, 1)
            return count
        downpath = self.DownZip(zip_addr, date, symbol)
        if downpath == -1:
            LOGD("Downloading is failed...", (), 10, 1)
            return count
        return count + 1

    def DownZip(self, zip_addr, date, symbol):
        downpath = self.download_folder + '/' + symbol + '_' + date + '_current.zip'
        countTries = 0
        while True:
            if countTries >= 5:
                LOGD("zipAddr: %s", (zip_addr), 10, 1)
                return -1
            try:
                r = urllib2.Request(zip_addr)
                f = urllib2.urlopen(r)
                if f.getcode() == 200:
                    break
            except Exception as e:
                LOGD("Zip downloading error. # of trial = %d", (countTries), 10, 1)
                LOGD("Error: %s", (e), 10, 1)
                countTries = countTries + 1
        zipFile = open(downpath, 'wb')
        zipFile.write(f.read())
        zipFile.close()
        f.close()
        return downpath

    def FindDownloadZipButton(self):
        codes = self.FindAll('a')
        for code in codes:
            code = code.encode('utf-8')
            if 'Download ZIP' in code and 'btn btn-outline' in code:
                return 'https://github.com' + code.split('href="')[1].split('"')[0]
        return -1

    def SearchDatetime(self):
        codes = self.FindAll('relative-time')
        for code in codes:
            code = code.encode('utf-8')
            if 'datetime' in code:
                return code.split('datetime="')[1].split('T')[0].replace('-','')
        return -1

    def FindAll(self, code):
        html = self.driver.page_source.encode('utf-8')
        soup = bs(html, 'html.parser')
        return soup.find_all(code)

    def SequentialSearch(self, today):
        current_url = self.driver.current_url.encode('utf-8')
        while True:
            codes = self.FindAll('div')
            for line in codes:
                line = line.encode('utf-8')
                if 'div class="commits-listing commits-listing-padded' in line:
                    newLines = line.split('commit-group-title')
                    for partial in newLines:
                        if 'Commits on ' not in partial:
                            continue
                        tmp = partial.split('Commits on ')[1].split('</div>')[0].replace('\n','').replace(' ','')
                        date = tmp.split(',')[1] + self.Months.get(tmp[:3], '13') + '0' * (2-len(tmp[3:].split(',')[0])) + tmp[3:].split(',')[0]
                        if int(date) <= int(today):
                            partial = partial.split("ol class=")[1].split('li class')[1:]
                            for filelink in partial:
                                if 'class="commit-links-cell' not in filelink or 'class="btn btn-outline' not in filelink or 'href="' not in filelink:
                                    continue
                                filelink = filelink.split('class="commit-links-cell')[1].split('class="btn btn-outline tooltipped tooltipped-sw')[1].split('href="')[1].split('"')[0]
                                hashed_value = filelink.split('/')[-1]
                                self.OpenURL('https://github.com' + '/'.join(filelink.split('/')[:3]) + '/tree/' + hashed_value)
                                return current_url
                    break
            newAddr = self.findOlderPage(codes)
            if newAddr == 0:
                return -1
            if current_url == newAddr:
                return -1
            current_url = newAddr
            self.OpenURL(newAddr)

    def findOlderPage(self, codes):
        for line in codes:
            line = line.encode('utf-8')
            if 'div class="pagination">' in line and '"disabled">older' in line:
                return 0
        for line in codes:
            line = line.encode('utf-8')
            if 'Older</a>' in line:
                return line.split('Older</a>')[0].split('href="')[-1].split('"')[0]
            if 'older</a>' in line:
                return line.split("older</a>")[0].split('href="')[-1].split('"')[0]
        return 0

if __name__ == '__main__':
    LOGD("Program Starting! Name: %s", (os.path.basename(__file__)))
    argv = sys.argv
    try:
        opts, etc_args = getopt.getopt(argv[1:], "ht:v", ["help", "tdate=", "visible"])
    except getopt.GetoptError:
        print(argv[0], "-t <target date> -v")
        sys.exit(2)
    target_date = '20190903'
    dp_visible = False
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(argv[0], '-t <target date> -v')
        elif opt in ('-t', '--tdate'):
            target_date = arg
        elif opt in ('-v', '--visible'):
            dp_visible = True
    handler = Downloader(target_date = target_date, display_visible=dp_visible)
    handler.readCSV('../00_Dataset/coin_list_git.csv')
    handler.Download()
    handler.Destroy()
    LOGD("Program End!")
