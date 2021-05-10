from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select,WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup as bs

import unittest, time, re, random, os, shutil, requests, sys, subprocess, datetime
#import urllib2
import urllib.request as urllib2
from time import ctime, sleep, time
from operator import itemgetter

from pyvirtualdisplay import Display
from datetime import date

import zipfile
import binascii
import statistics
import numpy as np
import ssdeep
from colorama import init
from colorama import Fore

c_extensions = ['c', 'cpp', 'h', 'hpp', 'c++', 'c#']

def LOGD(string, attr = (), depths = 0, color = 0):
    if color == 0:
        print(Fore.WHITE + ' ' * depths + '[%s] ' % (ctime()) + string % (attr))
    elif color == 1:
        print(Fore.RED + ' ' * depths + '[%s] ' % (ctime()) + string % (attr))
    fp = open("logs.txt","a")
    fp.write(' ' * depths + '[%s] ' % (ctime()) + string % (attr) + '\n')
    fp.close()

class Maintain_Parser:
    def __init__(self):
        fp = open("logs.txt", 'w')
        fp.close()
        self.driver_wait_time = 5
        self.sleep_time = 1
        self.Months = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
        if not os.path.exists('raw_data'):
            os.mkdir('raw_data')
        self.urlList = {}
        self.display = Display(visible=0, size=(800,600))
        self.display.start()
        self.driver = webdriver.Firefox()
        fp = open('CVERecorder.csv', 'w')
        fp.close()
        self.BaseChangedFile = 30
        self.Patchcodes = {}
        self.Vulncodes = {}
        if not os.path.exists('tmp'):
            os.mkdir('tmp')

    def Destroy(self):
        self.driver.quit()
        self.display.stop()

    def readCSV(self, filename):
        fp = open(filename, 'r', encoding='utf-8', errors='ignore')
        lines = fp.readlines()
        fp.close()
        for line in lines:
            line = line.replace('\n','').split(',')
            if line[1] == '':
                continue
            """
            counter = 0
            while True:
                if line[0] + str(counter) not in self.urlList:
                    break
                counter = counter + 1
            self.urlList[line[0] + str(counter)] = {'URL': line[1], 'Lang': line[3]}
            LOGD("Parsed %s", (line[0] + str(counter)), 2)
            """
            self.urlList[line[0]] = {'URL': line[1], 'Lang': line[3]}

    def searchFiles(self, dirname, filepath):
        filenames = os.listdir(dirname)
        for filename in filenames:
            full_filename = os.path.join(dirname, filename)
            if os.path.isdir(full_filename):
                filepath = self.searchFiles(full_filename, filepath)
            else:
                filepath.append(full_filename)
        return filepath

    def removeSpecialChar(self, line):
        return line.replace('\n','').replace('{','').replace('}','').replace(';','').replace('(','').replace(')','').replace('\t','')
    
    def readDatafromFile(self, filename):
        fp = open(filename, 'r')
        lines = fp.readlines()
        fp.close()
        data = []
        for line in lines:
            line = self.removeSpecialChar(line)
            if line == '':
                continue
            data.append(line)
        return data

    def VulnerabilityContentsParser(self):
        # Patch code Parser
        filepath = self.searchFiles('CVEPatch', [])
        for filename in filepath:
            data = self.readDatafromFile(filename)
            self.Patchcodes[filename.split('/')[-1]] = data
        # Vulnerable code parser
        filepath = self.searchFiles('CVEVuln', [])
        for filename in filepath:
            data = self.readDatafromFile(filename)
            self.Vulncodes[filename.split('/')[-1]] = data

    def readForkingDate(self, filename):
        fp = open(filename, 'r', encoding='utf-8', errors='ignore')
        lines = fp.readlines()
        fp.close()
        for line in lines:
            line = line.replace('\n','').split(',')
            self.urlList[line[0]]['Forking_date'] = line[1]
            self.urlList[line[0]]['Forking_hash'] = line[3].split('/')[-1]
    
    def OpenURL(self, url):
        self.driver.get(url)
        self.driver.implicitly_wait(self.driver_wait_time)
        sleep(self.sleep_time)

    def FindAll(self, code):
        html = self.driver.page_source#.encode('utf-8')
        soup = bs(html, 'html.parser')
        self.driver.implicitly_wait(30)
        return soup.find_all(code)

    def GetCommitNum(self):
        codes = self.FindAll('ul')
        dictionary = {}
        for code in codes:
            code = code#.encode('utf-8')#.replace(' ','').replace('\n','')
            #print code
            if '"commits"' in code:
                code = code.split('emphasized">')
                for index in range(1, len(code)):
                    tmp = code[index].split('</span>')[0].replace('\n','').replace(' ','').replace(',','')
                    dictionary[code[index].split('</span>')[1].split('</a>')[0].replace('\n','').replace(' ','')] = tmp
        if 'commits' in dictionary.keys():
            return int(dictionary['commits'])
        return -1

    def SearchLastPage(self, symbol):
        codes = self.FindAll('a')
        nextPageURL = self.findOlderPage(codes)
        if nextPageURL == 0:
            return -1
        url = nextPageURL
        while True:
            if nextPageURL == 0:
                return -1
            self.OpenURL(nextPageURL)
            codes = self.FindAll('div')
            for code in codes:
                code = code.encode('utf-8')
                if 'div class="commits-listing commits-listing-padded' in code:
                    lines = code.split('commit-group-title')
                    for partial in lines:
                        if 'Commits on ' not in partial:
                            continue
                        tmp = partial.split('Commits on ')[1].split('</div>')[0].replace('\n', '').replace(' ', '')
                        date = tmp.split(',')[1] + self.Months.get(tmp[:3], '13') + '0' * (2 - len(tmp[3:].split(',')[0])) + tmp[3:].split(',')[0]
                        if date >= self.urlList[symbol]['Forking_date']:
                            url = nextPageURL
                        else:
                            self.OpenURL(url)
                            return -1
                    break
            codes = self.FindAll('a')
            nextPageURL = self.findOlderPage(codes)
 
    def findNewerPage(self, codes):
        for line in codes:
            line = line#.encode('utf-8')
            #print(line)
            #print('===========================================================\n\n\n\n')
            if 'Newer</a>' in line:
                return line.split('Newer</a>')[0].split('href="')[-1].split('"')[0]
        return 0

    def findOlderPage(self, codes):
        for line in codes:
            line = line.encode('utf-8')
            if 'Older</a>' in line:
                return line.split('Older</a>')[0].split('href="')[-1].split('"')[0]
        return 0

    def CVEChecker(self):
        LOGD("Start CVE Checker.", (), 1)
        for symbol in self.urlList:
            if symbol == 'BTC0':
                continue  
            if not (0 <= list(self.urlList.keys()).index(symbol) < 55):
                continue
            if self.urlList[symbol]['Lang'] not in c_extensions:
                continue
            #if symbol != 'DGB0':
            #    continue
            LOGD("Target coin: %s (%d/%d)", (symbol, list(self.urlList.keys()).index(symbol) + 1, len(self.urlList.keys())), 2)
            LOGD("Open URL: %s", (self.urlList[symbol]['URL']), 3)
            #self.OpenURL(self.urlList[symbol]['URL'])
            #CommitNum = self.GetCommitNum()
            #if CommitNum == -1:
            #    LOGD("Page disappeared. Symbol: %s", (symbol), 10, 1)
            #    continue
            #self.OpenURL(self.urlList[symbol]['URL'] + '/commits')
            #LOGD("Commit num: %d", (CommitNum), 3)
            #self.driver.find_elements_by_xpath('//*[@id="js-repo-pjax-container"]/div[3]/div/div[2]/ul/li[1]/a').click()
            #sleep(1)
            
            #self.SearchLastPage(symbol)
            #self.OpenURL('https://github.com/ripple/rippled/commits/develop?after=2913847925ec8cabde868e6502a55610a768736f+12414&branch=develop')
            fp = open('hash_list.csv', 'r', encoding='utf-8', errors='ignore')
            lines = fp.readlines()
            fp.close()
            total_t = 0
            total_t2 = 0
            for line in lines:
                line = line.replace('\n','')
                hashed = line.split('/')[-1].split('.')[0]
                commit_num = int(line.split(',')[-1])
                print(hashed, commit_num)
                self.OpenURL('https://github.com/carboncointrust/CarboncoinCore/commit/' + hashed)
                CVEList = self.MakeCVEList()
                CVEList, tt, tt2 = self.ComparewithDiff(CVEList, commit_num)
                total_t += tt
                total_t2 += tt2
            print(total_t, total_t2)
            sys.exit(2)
            LOGD("Parsing Start Page URL: %s", (self.driver.current_url.encode('utf-8')), 3)
            self.SearchCVE(symbol)

    def MakeCVEList(self):
        fp = open('CVEList.txt', 'r', encoding='utf-8', errors='ignore')
        names = fp.readlines()
        fp.close()
        lists = {}
        for name in names:
            name = name.replace('\n','')
            lists[name] = False
            if name == 'CVE-2012-2459':
                lists[name] = True
        return lists

    def SearchCVE(self, symbol):
        LOGD("Search CVE...", (), 4)
        current_url = self.driver.current_url#.encode('utf-8')
        fp = open("raw_data/" + symbol + '.csv', 'w')
        fp.write('Date, datetime, CVE, Appear/Disappear,\n')
        FirstCommit = True
        CVEList = self.MakeCVEList()
        while True:
            print(self.driver.current_url)#.encode('utf-8'))
            codes = self.FindAll('div')
            for code in codes:
                code = code#.encode('utf-8')
                print(code)
                sys.exit(1)
                if 'div class="commits-listing commits-listing-padded' in code:
                    lines = code.split('commit-group-title')
                    for partial in lines[::-1]:
                        if 'Commits on ' not in partial:
                            continue
                        tmp = partial.split('Commits on ')[1].split('</div>')[0].replace('\n', '').replace(' ', '')
                        date = tmp.split(',')[1] + self.Months.get(tmp[:3], '13') + '0' * (2 - len(tmp[3:].split(',')[0])) + tmp[3:].split(',')[0]
                        if date < self.urlList[symbol]['Forking_date']:
                            continue
                        commits = partial.split('class="table-list-cell"')
                        for commit in commits[::-1][:-1]:
                            datetime = commit.split('datetime="')[1].split('T')[0].replace('-', '')
                            if 'data-pjax="true"' in commit:
                                boxes = commit.split('class="commit-title')[1].split('class="hidden-text')[0].split('data-pjax="true" href="')
                            else:
                                boxes = commit.split('class="commit-title')[1].split('href="')
                            #### Counting addition lines ###
                            commit_url = boxes[1].split('"')[0]
                            if 'https://' not in commit_url:
                                commit_url = 'https://github.com' + commit_url
                            LOGD("%s", (commit_url), 0)
                            if FirstCommit:
                                hashed_value = commit_url.split('/')[-1]
                                if hashed_value != self.urlList[symbol]['Forking_hash']:
                                    continue
                                self.OpenURL(commit_url.replace('/commit/','/tree/'))
                                CVEList = self.DownloadAndCompareCVE(CVEList, commit_url.replace('/commit/','/tree/'))
                                FirstCommit = False
                            else:
                                ChangedFileNum = self.GetChangedFiles(commit_url)
                                if ChangedFileNum == -1:
                                    LOGD("Error Commit Page. url: %s", (commit_url), 10, 1)
                                else:
                                    if ChangedFileNum <= self.BaseChangedFile:
                                        CVEList = self.ComparewithDiff(CVEList, ChangedFileNum)
                                    else:
                                        self.OpenURL(commit_url.replace('/commit/','/tree/'))
                                        CVEList = self.DownloadAndCompareCVE(CVEList, commit_url.replace('/commit/','/tree/'))
                            #print addition_lines
                            #fp.write('%s, %s, %d, %d, %s, %s, "%s", "%s",\n' % (date, datetime, addition_lines, deletion_lines, contributor, commit_url, title, contents))
                            #if addition_lines == -1:
                            #    LOGD("Addition line Error.. %s", (commit_url), 10, 1)
                            #if deletion_lines == -1:
                            #    LOGD("Deletion line Error.. %s", (commit_url), 10, 1)
                            if CVEList == -1:
                                fp.write("-1,-1,-1,Error\n")
                                continue
                            for CVEname in CVEList:
                                if CVEList[CVEname]:
                                    fp.write('%s,%s,%s,Appear\n' % (date, datetime, CVEname))
                                else:
                                    fp.write('%s,%s,%s,Not appear\n' % (date, datetime, CVEname))
                    break
            new_url = self.findNewerPage(codes)
            print(new_url)
            print()
            if new_url == 0:
                break
            if current_url != new_url:
                current_url = new_url
                self.OpenURL(new_url)
        fp.close()
        return -1

    def DownloadAndCompareCVE(self, CVEList, current_url):
        # Download
         # Search Download Path
        zip_addr = current_url.replace('/tree/','/archive/') + '.zip'
         # Download
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
                LOGD("Zip downloading error. # of trials = %d", (countTries), 10, 1)
                LOGD("Error: %s", (e), 10, 1)
                countTries = countTries + 1
        downpath = 'tmp/tmp.zip'
        zipFile = open(downpath, 'wb')
        zipFile.write(f.read())
        zipFile.close()
        f.close()
        # Unzip
        if not os.path.exists('tmp/file'):
            os.mkdir('tmp/file')
        try:
            unzipFile = zipfile.ZipFile(downpath)
            unzipFile.extractall('tmp/file/')
            unzipFile.close()
        except Exception as e:
            LOGD("Unzip error... %s", (downpath), 10, 1)
            LOGD("%s", (e), 10, 1)
            return -1
        # Compare
        filepath = self.searchFiles('tmp/file/', [])
        changedChecker = {}
        for CVEname in CVEList:
            changedChecker[CVEname] = False
        for filename in filepath:
            data = self.readDatafromFile(filename)
            CVEList, changedChecker = self.CompareContents(CVEList, data, changedChecker)
        # Del files
        os.system('rm -rf tmp/*')
        return CVEList

    def CompareContents(self, CVEList, data, changedChecker):
        for CVEname in CVEList:
            if changedChecker[CVEname]:
                continue
            if CVEList[CVEname]:
                result = list(set(data)&set(self.Patchcodes[CVEname]))
                if result != []:
                    CVEList[CVEname] = False
                    changedChecker[CVEname] = True
            else:
                result = list(set(data)&set(self.Vulncodes[CVEname]))
                if result != []:
                    CVEList[CVEname] = True
                    changedChecker[CVEname] = True
        return CVEList, changedChecker

    def ComparewithDiff(self, CVEList, fileNumber):
        # Read changed lines
        # Click diff
        base_base = '/html/body/div[4]/div/main/div[2]/div/div[4]/div[%d]'
        base_index = 1
        base = base_base % (base_index) + '/div[%d]'
        base_index += 1
        index = 1
        no_errors = False
        #print(self.driver.find_element_by_xpath('/html/body/div[4]/div/main/div[2]/div/div[4]/div[2]/div[42]/div[62]/div[1]/div[2]').text)
        #print('=======================================================================')
        #print(self.driver.find_element_by_xpath('/html/body/div[4]/div/main/div[2]/div/div[4]/div[2]/div[38]/div[2]').text)
        #print('=======================================================================')
        #print(self.driver.find_element_by_xpath('/html/body/div[4]/div/main/div[2]/div/div[4]/div[2]/div[42]/div[62]/div[59]/div[2]').text)
        #print(self.driver.find_element_by_xpath('/html/body/div[4]/div/main/div[2]/div/div[4]/div[2]/div[42]/div[62]/div[1]').text)
        #print('========================================================================')
        #print(self.driver.find_element_by_xpath('/html/body/div[4]/div/main/div[2]/div/div[4]/div[2]/div[42]/div[62]/div[2]').text)
        #print(self.driver.find_element_by_xpath('/html/body/div[4]/div/main/div[2]/div/div[4]/div[1]/div[1]/div[1]').text)
        #print('========================================================================')
        #print(self.driver.find_element_by_xpath('/html/body/div[4]/div/main/div[2]/div/div[4]/div[1]/div[1]/div[2]').text)
        #print('========================================================================')
        #print(self.driver.find_element_by_xpath('/html/body/div[4]/div/main/div[2]/div/div[4]/div[1]/div[2]/div[2]/div/table/tbody/tr[4]/td[3]/span').get_attribute('data-code-marker'))
        #print('========================================================================')
        #print(self.driver.find_element_by_xpath('/html/body/div[4]/div/main/div[2]/div/div[4]/div[1]/div[2]/div[2]/div/table/tbody/tr[1]/td[3]/span').get_attribute('data-code-marker'))
        #sys.exit()
        tables = []
        clicked = 0
        while True:
            try:
                text = self.driver.find_element_by_xpath(base % (index) + '/div[2]').text
            except Exception as e:
                #print('error:', e)
                try:
                    text = self.driver.find_element_by_xpath(base % (index) + '/div[1]').text
                    base = base % (index) + '/div[%d]'
                    index = 1
                    if no_errors:
                        break
                    no_errors = True
                    continue
                except Exception as e:
                    #print('error2:', e)
                    base = base_base % (base_index) + '/div[%d]'
                    base_index += 1
                    index = 1
                    if no_errors:
                        break
                    no_errors = True
                    continue
            if 'Binary file not shown.' == text or (re.match(r'^@@ ', text) is not None) or (re.match(r'^Load diff', text) is not None):
                no_errors = False
                try:
                    self.driver.find_element_by_xpath(base % (index)).click()
                    self.driver.implicitly_wait(10)
                    clicked += 1
                    if 'Binary file not shown.' != text:
                        tables.append(base % (index))
                    print(base % (index), 'click... %d' % (clicked))
                    index += 1
                except Exception as e:
                    print('error:', e)
                    break
            else:
                #print('None:', text)
                base = base % (index) + '/div[%d]'
                index = 1
                if no_errors:
                    break
                no_errors = True
        print("Click done")
        st = time()
        delLine = []
        addLine = []
        for code in tables:
            print(code, tables.index(code), '/', len(tables))
            index = 2
            while True:
                try:
                    text = self.driver.find_element_by_xpath(code + '/div[2]/div/table/tbody/tr[%d]/td[3]/span' % (index)).text
                    attr = self.driver.find_element_by_xpath(code + '/div[2]/div/table/tbody/tr[%d]/td[3]/span' % (index)).get_attribute('data-code-marker')
                    index += 1
                    #print(attr, text)
                    if attr == '+':
                        #print('+', text)
                        addLine.append(self.removeSpecialChar(text))
                    elif attr == '-':
                        #print('-', text)
                        delLine.append(self.removeSpecialChar(text))
                    elif attr == ' ':
                        pass
                    else:
                        LOGD("Parse Error... #1.", (), 10, 1)
                        LOGD("Contents: %s, %s", (attr, text), 10, 1)
                        LOGD("URL: %s", (self.driver.current_url), 10, 1)
                except Exception as e:
                    index += 1
                    try:
                        text = self.driver.find_element_by_xpath(code + '/div[2]/div/table/tbody/tr[%d]/td[3]/span' % (index)).text
                        attr = self.driver.find_element_by_xpath(code + '/div[2]/div/table/tbody/tr[%d]/td[3]/span' % (index)).get_attribute('data-code-marker')
                    except Exception as e:
                        break
        # Compare
        st2 = time()
        changedChecker = {}
        for CVEname in CVEList:
            changedChecker[CVEname] = False
        CVEList, changedChecker = self.CompareContents(CVEList, addLine, changedChecker)
        en = time()
        return CVEList, (en-st), (en-st2)

    def GetChangedFiles(self, commit_url):
        self.OpenURL(commit_url)
        codes = self.FindAll('div')
        for code in codes:
            code = code#.encode('utf-8')
            if 'toc-diff-stats' in code and 'changed file' in code:
                return int(code.split(' changed file')[0].split(' ')[-1].replace(',','').replace('\n',''))
        return -1

    def GetAdditionLines(self):
        codes = self.FindAll('div')
        for code in codes:
            code = code#.encode('utf-8')
            if 'toc-diff-stats' in code:
                if 'additions</strong>' in code:
                    if 'changed file' in code.split('<strong>')[1]:
                        addition = int(code.split('additions</strong>')[0].split('<strong>')[-1].replace(',','').replace(' ',''))
                    else:
                        addition = int(code.split('additions</strong>')[0].split('<strong>')[-1].replace(',','').replace(' ',''))
                elif 'addition' in code:
                    addition = int(code.split('addition</strong>')[0].split('<strong>')[-1].replace(',', '').replace(' ',''))
                if 'deletions</strong>' in code:
                    if 'changed file' in code.split('<strong>')[1]:
                        deletion = int(code.split('deletions</strong>')[0].split('<strong>')[-1].replace(',','').replace(' ',''))
                    else:
                        deletion = int(code.split('deletions</strong>')[0].split('<strong>')[-1].replace(',','').replace(' ',''))
                elif 'deletion' in code:
                    deletion = int(code.split('deletion</strong>')[0].split('<strong>')[-1].replace(',','').replace(' ',''))
                #except Exception as e:
                #    continue
                return addition, deletion
        return -1, -1

if __name__ == '__main__':
    LOGD("Program Starting! Name: %s", (os.path.basename(__file__)))
    handler = Maintain_Parser()
    handler.readCSV('custom_coin_list.csv')
    handler.readForkingDate('ForkingPoint.csv')
    handler.VulnerabilityContentsParser()
    handler.CVEChecker()
    handler.Destroy()
    LOGD("Program End!")
