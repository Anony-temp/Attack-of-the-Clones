from selenium import webdriver
from bs4 import BeautifulSoup as bs

import time, random, os, shutil, requests, sys, subprocess
from datetime import timedelta
from datetime import datetime as dt
import urllib.request as urllib2
from time import ctime, sleep, time
from operator import itemgetter
import operator

from pyvirtualdisplay import Display
from datetime import date

import statistics
import numpy as np
import zipfile
import ssdeep
import getopt

from colorama import init
from colorama import Fore
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from lib.jplagHash import compare_two_cryptocurrency

c_extensions = ['c', 'cpp', 'h', 'hpp', 'c++', 'h++']
go_extensions = ['go', 'Go']

def LOGD(string, attr = (), depths = 0, color = 0):
    if color == 0:
        print(Fore.WHITE + ' ' * depths + '[%s] ' % (ctime()) + string % (attr))
    elif color == 1:
        print(Fore.RED + ' ' * depths + '[%s] ' % (ctime()) + string % (attr))
    fp = open("logs.txt","a")
    fp.write(' ' * depths + '[%s] ' % (ctime()) + string % (attr) + '\n')
    fp.close()

class Determine_Forking:
    def __init__(self):
        fp = open("logs.txt", 'w')
        fp.close()
        self.driver_wait_time = 5
        self.sleep_time = 2 
        self.download_folder = "Coins"
        self.Months = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
        if not os.path.exists(self.download_folder):
            os.mkdir(self.download_folder)
        if not os.path.exists('raw_data'):
            os.mkdir('raw_data')
        self.urlList = {}
        self.display = Display(visible=0, size=(800,600))
        self.display.start()
        self.driver = webdriver.Firefox()
        self.BTC_logs = []
        self.first_n = 30
        self.BTC_logs_title = []
        self.BTC_hash_order = []

    def Destroy(self):
        self.driver.quit()
        self.display.stop()

    def Download(self, lang):
        LOGD("Start Downloading commits.", (), 1)
        LOGD("Parse existing forking point log.", (), 2)
        fp = open('../00_Dataset/Total_point.csv', 'r', encoding='utf-8', errors='ignore')
        lines = fp.readlines()
        fp.close()
        forkinglogs = {}
        for line in lines:
            line = line.replace('\n','').split(',')
            forkinglogs[line[0]] = line[-1]
        LOGD("Parse existing BTC/ETH logs.", (), 2)
        self.ReadBTCLogs(lang)
        add_symbols = []
        count = 0
        chk=True
        LOGD("Start find forking point.", (), 2)
        dirnames = sorted(list(self.urlList.keys()))
        for symbol in dirnames:
            if self.urlList[symbol]['Lang'] not in lang:
                continue
            if symbol == 'BTC0' or symbol == 'ETH0':
                continue
            if symbol not in forkinglogs.keys() or 'Case1:Log' in forkinglogs[symbol]:
                continue
            count = count + 1
            LOGD("Target coin: %s (%d/%d) %d", (symbol, dirnames.index(symbol) + 1, len(dirnames), count), 3)
            LOGD("Open URL: %s", (self.urlList[symbol]['URL']), 3)
            self.OpenURL(self.urlList[symbol]['URL'])
            CommitNum = self.GetCommitNum()
            if CommitNum == -1:
                LOGD("Page disappeared. Symbol: %s", (symbol), 10, 1)
                continue
            self.OpenURL(self.urlList[symbol]['URL'] + '/commits')
            LOGD("Commit num: %d", (CommitNum), 3)
            self.SearchLastPage(CommitNum)
            LOGD("Last Page URL: %s", (self.driver.current_url), 3)
            self.FindForking(symbol, lang)

    def FindForking(self, symbol, lang):
        LOGD("Finding forking time...", (), 4)
        current_url = self.driver.current_url
        new_url = current_url
        case1_checker = True
        case2_checker = True
        max_insertion = -1
        max_hash = ''
        max_data = {'Date':'', 'datetime':'', 'Log title':'', 'Log contents':''}
        ith = 0
        wrong_cnt = 0
        fork_point = []
        fp = open("raw_data/" + symbol + '.csv', 'w')
        fp.write('Date, datetime, addition lines, URL, Log title, Log contents,\n')
        chk_last = False
        while True:
            codes = self.FindAll('div')
            for code in codes:
                code = code.decode()
                if 'div class="commits-listing commits-listing-padded' in code:
                    lines = code.split('commit-group-title')
                    for partial in lines[::-1]:
                        if 'Commits on ' not in partial:
                            continue
                        tmp = partial.split('Commits on ')[1].split('</div>')[0].replace('\n', '').replace(' ', '')
                        date = tmp.split(',')[1] + self.Months.get(tmp[:3], '13') + '0' * (2 - len(tmp[3:].split(',')[0])) + tmp[3:].split(',')[0]
                        commits = partial.split('class="table-list-cell"')
                        for commit in commits[::-1][:-1]:
                            datetime = commit.split('datetime="')[1].split('T')[0].replace('-', '')
                            title = ''
                            if 'data-pjax="true"' in commit:
                                boxes = commit.split('class="commit-title')[1].split('class="hidden-text')[0].split('data-pjax="true" href="')
                            else:
                                boxes = commit.split('class="commit-title')[1].split('href="')

                            for box in boxes[1:]:
                                title += box.split('">')[1].split('</a>')[0].replace(',','').replace(' ','').replace('\n','').replace('"', '')
                            contents = commit.split('a aria-label=')[1].split(' class=')[0].replace(',','').replace(' ','').replace('\n','').replace('"','').replace('\t','')
                            if case1_checker:
                                if contents in self.BTC_logs_title:
                                    ith+=1
                                else:
                                    wrong_cnt+=1
                                    fork_point.append({'Date': date, 'datetime': datetime, 'Log title': title, 'Log contents': contents})
                                    if ith >= self.first_n and wrong_cnt >= 5:
                                        LOGD("Forking date: %s, datetime: %s, title: %s", (date, datetime, contents), 5)
                                        commit_url = boxes[1].split('"')[0]
                                        if 'https://' not in commit_url:
                                            commit_url = 'https://github.com' + commit_url
                                        fp.write('%s, %s, None, %s, "%s", "%s",\n' % (date, datetime, commit_url, title, contents))
                                        fp.close()
                                        self.DownloadProcess(date, symbol, commit_url, self.download_folder)
                                        return self.forking_log(symbol, date, datetime, commit_url, title, contents, "Case1:Log")
                                    if wrong_cnt >= 5:
                                        case1_checker = False

                            #### Counting addition lines ###
                            commit_url = boxes[1].split('"')[0]
                            if 'https://' not in commit_url:
                                commit_url = 'https://github.com' + commit_url
                                addition_lines = self.GetAdditionLines(commit_url)
                                fp.write('%s, %s, %d, %s, "%s", "%s",\n' % (date, datetime, addition_lines, commit_url, title, contents))
                                if addition_lines == -1:
                                    LOGD("Addition line Error.. %s", (commit_url), 10, 1)
                                else:
                                    if max_insertion < addition_lines:
                                        max_current_url = new_url
                                        max_insertion = addition_lines
                                        max_hash = commit_url
                                        max_data['Date'] = date
                                        max_data['datetime'] = datetime
                                        max_data['Log title'] = title
                                        max_data['Log contents'] = contents

                    break
            if chk_last:
                break
            new_url = self.findNewerPage(codes)
            if new_url == 0:
                break
            if current_url != new_url:
                current_url = new_url
                self.OpenURL(new_url)
        fp.close()
        if max_hash == '':
            LOGD("ERRORRRRRRRRRRRRRRRRRRRRRRRRRRRRR", (), 20, 1)
            return -1
        self.OpenURL(max_current_url)
        base = self.DownloadProcess(max_data['Date'], symbol, max_hash, 'tmp')
        ret = self.UnzipFile(base, 'Unzip/Target_Origin')
        if ret == -1:
            return -1
        hashValue = self.searchHash(max_data['Date'], max_data['datetime'])
        if 'go' in lang:
            if not os.path.exists('BTC_past/ETH0_' + hashValue + '.zip'):
                os.system('wget https://github.com/ethereum/go-ethereum/archive/' + hashValue + '.zip')
                os.system('mv ' + hashValue + '.zip BTC_past/ETH0_' + hashValue + '.zip')
            ret = self.UnzipFile('BTC_past/ETH0_' + hashValue + '.zip', 'Unzip/Target_base')
        else:
            if not os.path.exists('BTC_past/BTC0_' + hashValue + '.zip'):
                os.system('wget https://github.com/Bitcoin/Bitcoin/archive/' + hashValue + '.zip')
                os.system('mv ' + hashValue + '.zip BTC_past/BTC0_' + hashValue + '.zip')
            ret = self.UnzipFile('BTC_past/BTC0_' + hashValue + '.zip', 'Unzip/Target_base')
        if ret == -1:
            LOGD("BTC/ETH... %s", (hashValue), 10, 1)
            return -1
        fp = open('raw_data/' + symbol + '_similarity.csv', 'w')
        fp.write('Hash, similarity,\n')
        base_similarity = compare_two_cryptocurrency('Unzip/Target_Origin', 'Unzip/Target_base', lang)
        LOGD("Old: %g, %s", (base_similarity, max_hash.split('/')[-1]), 10, 1)
        if base_similarity == -1:
            os.system('rm -rf Unzip/*')
            return -1
        fp.write('%s,%g,\n' % (hashValue, base_similarity))
        index = self.BTC_hash_order.index(hashValue) - 1
        os.system('rm -rf Unzip/Target_base/*')
        while True:
            if index == -1:
                break
            hashValue = self.BTC_hash_order[index]
            if 'go' in lang:
                if not os.path.exists('BTC_past/ETH0_' + hashValue + '.zip'):
                    os.system('wget https://github.com/ethereum/go-ethereum/archive/' + hashValue + '.zip')
                    os.system('mv ' + hashValue + '.zip BTC_past/ETH0_' + hashValue + '.zip')
                ret = self.UnzipFile('BTC_past/ETH0_' + hashValue + '.zip', 'Unzip/Target_base')
            else:
                if not os.path.exists('BTC_past/BTC0_' + hashValue + '.zip'):
                    os.system('wget https://github.com/Bitcoin/Bitcoin/archive/' + hashValue + '.zip')
                    os.system('mv ' + hashValue + '.zip BTC_past/BTC0_' + hashValue + '.zip')
                ret = self.UnzipFile('BTC_past/BTC0_' + hashValue + '.zip', 'Unzip/Target_base')
            if ret == -1:
                LOGD("BTC/ETH... %s", (hashValue), 10, 1)
                return -1
            new_base_similarity = compare_two_cryptocurrency('Unzip/Target_Origin', 'Unzip/Target_base', lang)
            os.system('rm -rf Unzip/Target_base/*')
            LOGD("Old: %g, New: %g, %s", (base_similarity, new_base_similarity, hashValue), 10, 1)
            fp.write('%s,%g,\n' % (hashValue, new_base_similarity))
            if new_base_similarity < base_similarity or new_base_similarity == 0:
                break
            base_similarity = new_base_similarity
            index = index - 1
        LOGD("Addition lines: %d, date: %s, datetime: %s, title: %s", (max_insertion, max_data['Date'], max_data['datetime'], max_data['Log title']))
        os.system('rm -rf Unzip/*')
        fp.close()
        os.system('mv ' + base + ' Coins/')
        return self.forking_log(symbol, max_data['Date'], max_data['datetime'], max_hash, max_data['Log title'], max_data['Log contents'], "Case2:MAX," + hashValue)

    def searchHash(self, date, datetime):
        hashValue = -1
        while True:
            hashValue = self.searchHashinLog(date, datetime)
            if hashValue != -1:
                break
            date = (dt.strptime(date, '%Y%m%d').date() - timedelta(days=1)).strftime('%Y%m%d')
        return hashValue

    def searchHashinLog(self, date, datetime):
        start = 0
        end = len(self.BTC_logs)
        while start < end - 1:
            middle = int((start + end)/2)
            if date == self.BTC_logs[middle]['Date']:
                return self.BTC_logs[middle]['Hash']
            elif date > self.BTC_logs[middle]['Date']:
                start = middle
            else:
                end = middle
        return -1
 
    def UnzipFile(self, filepath, targetDir):
        try:
            unzipFile = zipfile.ZipFile(filepath)
            unzipFile.extractall(targetDir + '/')
            unzipFile.close()
        except Exception as e:
            LOGD("UNZIP ERRORR........ %s", (filepath), 10, 1)
            return -1
        return 0

    def forking_log(self, symbol, date, datetime, url, title, contents, cases):
        fp = open('ForkingPoint.csv', 'a')
        fp.write('%s,%s,%s,%s,"%s","%s",%s\n' % (symbol, date, datetime, url, title, contents, cases))
        fp.close()
        return 1

    def GetAdditionLines(self, commit_url):
        self.OpenURL(commit_url)
        codes = self.FindAll('div')
        for code in codes:
            code = code.decode()
            if 'toc-diff-stats' in code:
                if 'additions</strong>' in code:
                    if 'changed file' in code.split('<strong>')[1]:
                        return int(code.split('additions</strong>')[0].split('<strong>')[-1].replace(',','').replace(' ',''))
                    else:
                        return int(code.split('additions</strong>')[0].split('<strong>')[-1].replace(',','').replace(' ',''))
                elif 'addition' in code:
                    return int(code.split('addition</strong>')[0].split('<strong>')[-1].replace(',', '').replace(' ',''))
        return -1

    def ReadBTCLogs(self, lang):
        LOGD("Read BTC/ETH Logs...", (), 2)
        fp = open('BTC_logs.csv', 'r', encoding='utf-8', errors='ignore')
        lines = fp.readlines()
        fp.close()
        self.BTC_logs = []
        self.BTC_logs_title = []
        for line in lines[1:]:
            line = line.split(',')
            self.BTC_logs.append({'Date': line[0], 'datetime': line[1], 'Log title': line[4].replace('"','').replace(' ','').replace('\n',''), 'Log contents': line[4], 'Hash': line[2].replace(' ','')})
            self.BTC_logs_title.append(line[4].replace('"','').replace(' ','').replace('\n','').replace("\t",'').replace(',',''))
            self.BTC_hash_order.append(line[2].replace(' ',''))

    def RecordBTCLog(self):
        LOGD("Recording BTC mode...", (), 4)
        self.SearchLastPage(20000)
        fp = open("BTC_logs.csv", 'w')
        fp.write('Date, datetime, Hash, Log title, Log contents, \n')
        current_url = self.driver.current_url
        while True:
            codes = self.FindAll('div')
            for code in codes:
                code = code.decode()
                if 'div class="commits-listing commits-listing-padded' in code:
                    lines = code.split('commit-group-title')
                    for partial in lines[::-1]:
                        if 'Commits on ' not in partial:
                            continue
                        tmp = partial.split('Commits on ')[1].split('</div>')[0].replace('\n','').replace(' ','')
                        date = tmp.split(',')[1] + self.Months.get(tmp[:3], '13') + '0' * (2 - len(tmp[3:].split(',')[0])) + tmp[3:].split(',')[0]
                        commits = partial.split('class="table-list-cell"')
                        for commit in commits[::-1][:-1]:
                            datetime = commit.split('datetime="')[1].split('T')[0].replace('-','')
                            title = ''
                            if 'data-pjax="true"' in commit:
                                boxes = commit.split('class="commit-title')[1].split('class="hidden-text')[0].split('href="')
                            else:
                                boxes = commit.split('class="commit-title')[1].split('href="')
                            boxes = commit.split('class="commit-title')[1].split('class="hidden-text')[0].split('data-pjax="true" href="')
                            for box in boxes[1:]:
                                title += box.split('">')[1].split('</a>')[0].replace(',','').replace(' ','').replace('\n','').replace('"', '')
                            return
                            contents = commit.split('a aria-label=')[1].split(' class=')[0].replace(',','').replace(' ','').replace('\n','').replace('"','')
                            fp.write('%s, %s, %s, "%s", "%s"\n' % (date, datetime, boxes[1].split('"')[0].split('/')[-1], title, contents))
                            LOGD('Obtain data::%s, %s, "%s"', (date, datetime, title), 5)
                    break
            new_url = self.findNewerPage(codes)
            if new_url == 0:
                break
            if current_url != new_url:
                current_url = new_url
                self.OpenURL(new_url)
        fp.close()

    def DownloadProcess(self, date, symbol, url, downloadFolder):
        zip_addr = '/'.join(url.split('/')[:-2]) + '/archive/' + url.split('/')[-1] + '.zip'
        if zip_addr == -1:
            LOGD("Finding the download button failed...", (), 10, 1)
            return -1
        downpath = self.DownZip(zip_addr, date, symbol, url.split('/')[-1], downloadFolder)
        if downpath == -1:
            LOGD("Downloading is failed...", (), 10, 1)
            return -1
        return downpath

    def DownZip(self, zip_addr, date, symbol, hashed, DownloadFolder):
        downpath = DownloadFolder + '/' + symbol + '_' + date + '_' + hashed + '.zip'
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
                countTries+=1
        zipFile = open(downpath, 'wb')
        zipFile.write(f.read())
        zipFile.close()
        f.close()
        return downpath

    def FindDownloadZipButton(self):
        codes = self.FindAll('a')
        for code in codes:
            code = code.decode()
            if 'Download ZIP' in code and 'btn btn-outline' in code:
                return 'https://github.com' + code.split('href="')[1].split('"')[0]
        return -1

    def findNewerPage(self, codes):
        for line in codes:
            line = line.decode()
            if 'Newer</a>' in line:
                return line.split('Newer</a>')[0].split('href="')[-1].split('"')[0]
        return 0

    def OpenURL(self, url):
        self.driver.get(url)
        self.driver.implicitly_wait(self.driver_wait_time)
        sleeping = random.randrange(1,self.sleep_time) 
        sleep(sleeping)

    def SearchLastPage(self, CommitNum):
        codes = self.FindAll('a')
        nextPageURL = self.findOlderPage(codes)
        if nextPageURL == 0:
            return -1
        if CommitNum >= 300:
            nextPageURL = nextPageURL.split('+')[0] + '+' + str(CommitNum-300)
        while True:
            if nextPageURL == 0:
                return
            self.OpenURL(nextPageURL)
            codes = self.FindAll('a')
            nextPageURL = self.findOlderPage(codes)
    
    def findOlderPage(self, codes):
        for line in codes:
            line = line.decode()
            if 'Older</a>' in line:
                return line.split('Older</a>')[0].split('href="')[-1].split('"')[0]
        return 0

    def GetCommitNum(self):
        codes = self.FindAll('ul')
        dictionary = {}
        for code in codes:
            code = code.decode()
            if '"commits"' in code or '"commit"' in code:
                code = code.split('emphasized">')
                for index in range(1, len(code)):
                    tmp = code[index].split('</span>')[0].replace('\n','').replace(' ','').replace(',','')
                    dictionary[code[index].split('</span>')[1].split('</a>')[0].replace('\n','').replace(' ','')] = tmp
        if 'commits' in dictionary.keys():
            return int(dictionary['commits'])
        elif 'commit' in dictionary.keys():
            return int(dictionary['commit'])
        return -1

    def FindAll(self, code):
        html = self.driver.page_source
        soup = bs(html, 'html.parser')
        return soup.find_all(code)

    def readCSV(self, filename):
        fp = open(filename, 'r', encoding='utf-8', errors='ignore')
        lines = fp.readlines()
        fp.close()
        for line in lines:
            line = line.replace('\n','').split(',')
            if line[1] == '':
                continue
            self.urlList[line[0]] = {'URL': line[1], 'Lang': line[3]}

if __name__ == '__main__':
    LOGD("Program Starting! Name: %s", (os.path.basename(__file__)))
    argv = sys.argv
    try:
        opts, etc_args = getopt.getopt(argv[1:], "hb", ["help", "bitcoin"])
    except getopt.GetoptError:
        print(argv[0], "-b [optional]")
        sys.exit(2)
    log_parser = False
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(argv[0], '-b [optional]')
        elif opt in ('-b', '--bitcoin'):
            log_parser=True
    handler = Determine_Forking()
    if log_parser:
        handler.RecordBTCLogs()
    else:
        handler.readCSV('../dataset/coin_list_git.csv')
        handler.Download(c_extensions)
    handler.Destroy()
    LOGD("Program End!")
