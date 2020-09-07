from selenium import webdriver
from bs4 import BeautifulSoup as bs

import os, sys
import getopt
from time import ctime, sleep

from pyvirtualdisplay import Display
from random import randrange

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
    def __init__(self,sd='20180101',ed='20181231',display_visible=False):
        self.driver_wait_time = 5
        self.sleep_time = 2
        self.Months = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
        if not os.path.exists('raw_data'):
            os.mkdir('raw_data')
        self.urlList = {}
        self.dp_visible = display_visible
        if not display_visible:
            self.display = Display(visible=0, size=(800,600))
            self.display.start()
        self.driver = webdriver.Firefox()
        self.startDate = sd
        self.endDate = ed

    def Destroy(self):
        if not self.dp_visible:
            self.display.stop()
        self.driver.quit()

    def readCSV(self, filename):
        fp = open(filename, 'r')
        lines = fp.readlines()
        fp.close()
        for line in lines:
            line = line.replace('\n','').split(',')
            if line[1] == '':
                continue
            self.urlList[line[0]] = {'URL': line[1], 'Lang': line[3]}
    
    def OpenURL(self, url):
        while True:
            self.driver.get(url)
            self.driver.implicitly_wait(self.driver_wait_time)
            sleep(randrange(1,self.sleep_time + 1))
            check_whoa = self.FindAll('div')
            check_whoa_tf = False
            for code in check_whoa:
                code = code.decode()
                if 'Whoa there!' in code:
                    check_whoa_tf = True
            if not check_whoa_tf:
                break
            sleep(15)

    def FindAll(self, code):
        html = self.driver.page_source
        soup = bs(html, 'html.parser')
        return soup.find_all(code)

    def GetCommitNum(self, url):
        codes = self.FindAll('ul')
        dictionary = {}
        for code in codes:
            code = code.decode()
            if '"commits"' in code or '"commit"' in code:
                code = code.split('emphasized">')
                for index in range(1, len(code)):
                    tmp = code[index].split('</span>')[0].replace('\n','').replace(' ','').replace(',','')
                    dictionary[code[index].split('</span>')[1].split('</a>')[0].replace('\n','').replace(' ','')] = tmp
            if 'pagehead-actions' in code:
                code = code.split('<li>')
                for index in range(1, len(code)):
                    if 'Watch' in code[index] or 'Star' in code[index] or 'Fork' in code[index]:
                        tmp = code[index].split('</a>')[1].split('">')[-1].replace('\n','').replace(' ','').replace(',','')
                        dictionary[code[index].split('</a>')[0].split('svg>')[-1].replace('"','').replace(' ','').replace('\n','')] = tmp
        codes = self.FindAll('nav')
        for code in codes:
            code = code.decode()
            if '"Repository"' in code:
                code = code.split('</svg>')
                for index in range(2, (4 if 4 < len(code) else len(code))):
                    if 'Issues' in code[index] or 'Pull requests' in code[index]:
                        tmp = code[index].split('</span>')[1].split('">')[-1].replace(',','')
                        dictionary[code[index].split('</span>')[0].split('">')[-1]] = tmp
        self.OpenURL(url + '/issues')
        codes = self.FindAll('div')
        for code in codes:
            code = code.decode()
            if 'Open' in code and 'Closed' in code and 'octicon-issue-opened' in code:
                tmp = code.split('</a>')[0].split('</svg>')[-1].split('Open')[0].replace(' ','').replace('\n','').replace('"','').replace(',','')
                dictionary['Open'] = tmp
                tmp = code.split('</a>')[1].split('</svg>')[-1].split('Closed')[0].replace(' ','').replace('\n','').replace('"','').replace(',','')
                dictionary['Closed'] = tmp
        commits = -1
        branches = -1
        releases = -1
        contributors = -1
        watch = -1
        star = -1
        fork = -1
        issues = 0
        pull = 0
        openi = 0
        closedi = 0
        if 'commits' in dictionary.keys():
            commits = int(dictionary['commits'])
        elif 'commit' in dictionary.keys():
            commits = int(dictionary['commit'])
        if 'branches' in dictionary.keys():
            branches = int(dictionary['branches'])
        elif 'branch' in dictionary.keys():
            branches = int(dictionary['branch'])
        if 'releases' in dictionary.keys():
            releases = int(dictionary['releases'])
        elif 'release' in dictionary.keys():
            releases = int(dictionary['release'])
        if 'contributors' in dictionary.keys():
            contributors = int(dictionary['contributors'])
        elif 'contributor' in dictionary.keys():
            contributors = int(dictionary['contributor'])
        if 'Watch' in dictionary.keys():
            if 'k' in dictionary['Watch']:
                watch = int(float(dictionary['Watch'].split('k')[0]) * 1000)
            else:
                watch = int(dictionary['Watch'])
        if 'Star' in dictionary.keys():
            if 'k' in dictionary['Star']:
                star = int(float(dictionary['Star'].split('k')[0]) * 1000)
            else:
                star = int(dictionary['Star'])
        if 'Fork' in dictionary.keys():
            if 'k' in dictionary['Fork']:
                fork = int(float(dictionary['Fork'].split('k')[0]) * 1000)
            else:
                fork = int(dictionary['Fork'])
        if 'Issues' in dictionary.keys():
            issues = int(dictionary['Issues'])
        if 'Pull requests' in dictionary.keys():
            pull = int(dictionary['Pull requests'])
        if 'Open' in dictionary.keys():
            openi = int(dictionary['Open'])
        if 'Closed' in dictionary.keys():
            closedi = int(dictionary['Closed'])
        return commits, branches, releases, contributors, watch, star, fork, issues, pull, openi, closedi

    def SearchLastPage(self):
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
                code = code.decode()
                if 'div class="commits-listing commits-listing-padded' in code:
                    lines = code.split('commit-group-title')
                    for partial in lines:
                        if 'Commits on ' not in partial:
                            continue
                        tmp = partial.split('Commits on ')[1].split('</div>')[0].replace('\n', '').replace(' ', '')
                        date = tmp.split(',')[1] + self.Months.get(tmp[:3], '13') + '0' * (2 - len(tmp[3:].split(',')[0])) + tmp[3:].split(',')[0]
                        if date >= self.startDate:
                            url = nextPageURL
                        else:
                            self.OpenURL(url)
                            return -1
                    break
            codes = self.FindAll('a')
            nextPageURL = self.findOlderPage(codes)
 
    def findNewerPage(self, codes):
        for line in codes:
            line = line.decode()
            if 'Newer</a>' in line:
                return line.split('Newer</a>')[0].split('href="')[-1].split('"')[0]
        return 0

    def findOlderPage(self, codes):
        for line in codes:
            line = line.decode()
            if 'Older</a>' in line:
                return line.split('Older</a>')[0].split('href="')[-1].split('"')[0]
        return 0

    def Parse(self):
        LOGD("Start Maintain Parser.", (), 1)
        for symbol in self.urlList:
            LOGD("Target coin: %s (%d/%d)", (symbol, list(self.urlList.keys()).index(symbol) + 1, len(list(self.urlList.keys()))), 2)
            LOGD("Open URL: %s", (self.urlList[symbol]['URL']), 3)
            self.OpenURL(self.urlList[symbol]['URL'])
            CommitNum, Branches, Releases, Contributors, Watch, Star, Fork, Issues, Pull, Open, Closed = self.GetCommitNum(self.urlList[symbol]['URL'])
            if CommitNum == -1:
                LOGD("Page disappeared. Symbol: %s", (symbol), 10, 1)
                continue
            self.OpenURL(self.urlList[symbol]['URL'] + '/commits')
            LOGD("Commit num: %d", (CommitNum), 3)
            LOGD("Branches: %d, Releases: %d, Contributors: %d", (Branches, Releases, Contributors), 4)
            LOGD("Watch: %d, Star: %d, Fork: %d", (Watch, Star, Fork), 4)
            LOGD("Issues: %d, Pull: %d, Open issues: %d, Closed issues: %d", (Issues, Pull, Open, Closed), 4)
            self.SearchLastPage()
            LOGD("Parsing Start Page URL: %s", (self.driver.current_url), 3)
            fp = open('raw_data/' + symbol + '.csv', 'w')
            fp.write('Commits, Branches, Releases, Contributors, Watch, Star, Fork, Issues, Pull, Open issues, Closed issues,\n')
            fp.write('%d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d,\n' % (CommitNum, Branches, Releases, Contributors, Watch, Star, Fork, Issues, Pull, Open, Closed))
            fp.write('Date, datetime, addition lines, deletion lines, Contributor, URL, Log title, Log contents,\n')
            fp.close()
            self.ParseMaintain(symbol, 'raw_data/' + symbol + '.csv')

    def ParseMaintain(self, symbol, fp_in):
        LOGD("Parsing Maintain value...", (), 4)
        current_url = self.driver.current_url
        do_again = False
        do_count = 0
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
                        if date < self.startDate:
                            continue
                        if date > self.endDate:
                            fp.close()
                            return -1
                        commits = partial.split('<li class="commit')
                        for commit in commits[::-1][:-1]:
                            contributor = commit.split('"AvatarStack-body"')[0].split('aria-label="')[-1].split('"')[0]
                            if ',' in contributor:
                                contributor = contributor.split(',')[0]
                            if ' and ' in contributor:
                                contributor = contributor.split(' and ')[0]
                            datetime = commit.split('datetime="')[1].split('T')[0].replace('-', '')
                            title = ''
                            boxes = commit.split('class="commit-title')[1].split('class="hidden-text')[0].split('data-pjax="true" href="')
                            for box in boxes[1:]:
                                title += box.split('">')[1].split('</a>')[0].replace(',','').replace(' ','').replace('\n','').replace('"', '')
                            contents = commit.split('a aria-label=')[1].split(' class=')[0].replace(',','').replace(' ','').replace('\n','').replace('"','')
                            if len(boxes) >= 2:
                                commit_url = boxes[1].split('"')[0]
                            else:
                                commit_url = commit.split("btn btn-outline")[-1].split('href="')[1].split('"')[0]
                            if 'https://' not in commit_url:
                                commit_url = 'https://github.com' + commit_url
                            if '/tree/' in commit_url:
                                commit_url = commit_url.replace('/tree/', '/commit/')
                            addition_lines, deletion_lines = self.GetAdditionLines(commit_url)
                            fp = open(fp_in,'a')
                            fp.write('%s, %s, %d, %d, %s, %s, "%s", "%s",\n' % (date, datetime, addition_lines, deletion_lines, contributor, commit_url, title, contents))
                            fp.close()
                            if addition_lines == -1:
                                LOGD("Addition line Error.. %s", (commit_url), 10, 1)
                            if deletion_lines == -1:
                                LOGD("Deletion line Error.. %s", (commit_url), 10, 1)
                                do_again = True
                                break
                            do_count = 0
                    break
            if do_again:
                sleep(15)
                do_again = False
                do_count+=1
                if do_count < 5:
                    self.OpenURL(current_url)
                    continue
                do_count = 0
            new_url = self.findNewerPage(codes)
            if new_url == 0:
                break
            if current_url != new_url:
                current_url = new_url
                self.OpenURL(new_url)
            while True:
                check_whoa = self.FindAll('div')
                check_whoa_tf = False
                for code in check_whoa:
                    if 'Whoa there!' in code:
                        check_whoa_tf = True
                if not check_whoa_tf:
                    break
                sleep(15)
                self.OpenURL(new_url)
        return -1

    def GetAdditionLines(self, commit_url):
        self.OpenURL(commit_url)
        for code in codes:
            code = code.decode()
            if 'toc-diff-stats' in code:
                if 'additions</strong>' in code:
                    if 'changed file' in code.split('<strong>')[1]:
                        addition = int(code.split('<strong>')[2].split('additions</strong>')[0].replace(',','').replace(' ',''))
                    else:
                        addition = int(code.split('<strong>')[1].split('additions</strong>')[0].replace(',','').replace(' ',''))
                elif 'addition' in code:
                    addition = int(code.split('addition</strong>')[0].split('<strong>')[-1].replace(',', '').replace(' ',''))
                if 'deletions</strong>' in code:
                    if 'changed file' in code.split('<strong>')[1]:
                        deletion = int(code.split('<strong>')[3].split('deletions</strong>')[0].replace(',','').replace(' ',''))
                    else:
                        deletion = int(code.split('<strong>')[2].split('deletions</strong>')[0].replace(',','').replace(' ',''))
                elif 'deletion' in code:
                    deletion = int(code.split('deletion</strong>')[0].split('<strong>')[-1].replace(',','').replace(' ',''))
                return addition, deletion
        return -1, -1

if __name__ == '__main__':
    LOGD("Program Starting! Name: %s", (os.path.basename(__file__)))
    argv = sys.argv
    try:
        opts, etc_args = getopt.getopt(argv[1:], "hf:s:e:v", ["help", "file=", "start=", "end=", "visible"])
    except getopt.GetoptError:
        print(argv[0], '-f <coin url file name> -s <start date> -e <end date> -o <output filename>')
        sys.exit(2)
    filename = ''
    start_date = ''
    end_date = ''
    dp_visible = False
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(argv[0], '-f <coin url file name> -s <start date> -e <end date> -o <output filename>')
            sys.exit()
        elif opt in ("-f", "--file"):
            filename = arg
        elif opt in ("-s", "--start"):
            start_date = arg
        elif opt in ("-e", "--end"):
            end_date = arg
        elif opt in ("-v", "--visible"):
            dp_visible = True
    if len(filename) < 1:
        filename = 'coin_list_git.csv'
    if len(start_date) < 1:
        start_date = '20180101'
    if len(end_date) < 1:
        end_date = '20181231'
    handler = Maintain_Parser(sd = start_date,ed = end_date,dp_visible=dp_visible)
    handler.readCSV(filename)
    handler.Parse()
    handler.Destroy()
    LOGD("Program End!")
