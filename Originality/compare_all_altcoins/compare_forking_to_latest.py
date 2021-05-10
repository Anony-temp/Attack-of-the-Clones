import sys, os, ray
import datetime
from time import sleep
from jplagHash import compare_two_cryptocurrency
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from libs.logging import LOGD, initLog
from libs.seleniumCustom import custom_selenium
from libs.simpleFunctions import searchFiles, readCSV, custom_replace, DownZip, UnzipFile

ray.init()

lang = ['c', 'cpp', 'h', 'hpp', 'c++', 'h++']
Months = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}

def makeSkipList():
    skipList = []
    for idx in range(0):
        fp = open('SimilarityComparison_' + str(int(idx/10)) + str(idx%10) + '.csv', 'r', encoding = 'utf-8', errors = 'ignore')
        lines = fp.readlines()
        fp.close()
        for line in lines[1:]:
            line = line.split(',')
            skipList.append(line[0])
    return skipList

def initResults():
    fp = open('SimilarityComparison.csv', 'w')
    fp.write('Symbol, Sim. Score, ForkingTime, Bitcoin Hash, Alt Hash,\n')
    fp.close()

def makeResults(symbol, sim, ForkingTime, BTCHash, AltHash):
    fp = open('SimilarityComparison.csv', 'a')
    fp.write('%s, %g, %s, %s, %s,\n' % (symbol, sim, ForkingTime, BTCHash, AltHash))
    fp.close()

def initRawData(symbol):
    fp = open('raw_data/' + symbol + '.csv', 'w')
    fp.write('Symbol\'s hash, Symbol\'s date, Bitcoin\'s hash, sim,\n')
    fp.close()

def makeRawData(symbol, TargetHash, date, BitcoinHash, sim):
    fp = open('raw_data/' + symbol + '.csv', 'a')
    fp.write('%s, %s, %s, %g,\n' % (TargetHash, date, BitcoinHash, sim))
    fp.close()

def CompareBitcoin(symbol, TargetPath, TargetHash, date, BitcoinList, BitcoinHash, BitcoinDateHash, ith):
    TargetPath = TargetPath + os.listdir(TargetPath)[0]
    before = 180
    before_date = int((datetime.datetime(int(date/10000), int(date/100)%100, date%100) - datetime.timedelta(days=before)).strftime("%Y%m%d"))
    LOGD("Symbol: %s is start from %d", (symbol, before_date), 3, 1)
    CombinationList = []
    for Bitcoin_date in BitcoinDateHash:
        if before_date < Bitcoin_date and Bitcoin_date <= date:
            for hashValue in BitcoinDateHash[Bitcoin_date]:
                if hashValue not in BitcoinHash:
                    continue
                BTC_Path = BitcoinList[hashValue]
                sim = compare_two_cryptocurrency(TargetPath, '../03_Unzip_Current_Past/BTC_versions/' + BTC_Path, ['c', 'cpp', 'h', 'hpp', 'c++', 'h++'], ith)
                LOGD("Symbol: %s, Hash: %s, sim: %g, date: %d/%d (%d)", (symbol, hashValue, sim, Bitcoin_date, date, ith), 4) 
                makeRawData(symbol, TargetHash, Bitcoin_date, BTC_Path.split('_')[-1], sim)
                CombinationList.append([TargetHash, Bitcoin_date, BTC_Path.split('_')[-1], sim])
    return CombinationList

def getAllCombinations(symbol, date, BitcoinList, BitcoinHash, BitcoinDateHash, ith):
    current_url = handler.driver.current_url
    new_url = current_url
    CombinationList = []
    while True:
        codes = handler.FindAll('div')
        for code in codes:
            code = code.decode()
            if 'div class="commits-listing commits-listing-padded' in code:
                lines = code.split('commit-group-title')
                for partial in lines[::-1]:
                    if 'Commits on ' not in partial:
                        continue
                    tmp = partial.split('Commits on ')[1].split('</div>')[0].replace('\n', '').replace(' ','')
                    date = tmp.split(',')[1] + Months.get(tmp[:3], '13') + '0' * (2 - len(tmp[3:].split(',')[0])) + tmp[3:].split(',')[0]
                    commits = partial.split('<li class="commit')
                    for commit in commits[::-1][:-1]:
                        boxes = commit.split('class="commit-title')[1].split('class="hidden-text')[0].split('data-pjax="true" href="')
                        datetime = commit.split('datetime="')[1].split('T')[0].replace('-', '')
                        commitLink = boxes[1].split('"')[0]
                        hashValue = commitLink.split('/')[-1]
                        down_path = DownZip(url + '/archive/' + hashValue + '.zip', 'temp/' + hashValue + '.zip')
                        if down_path == -1:
                            LOGD("ERROR... Hash value: %s, URL: %s", (hashValue, commitLink), 10, 1)
                            makeRawData(symbol, hashValue, datetime, '', -1)
                            continue
                        unzip_path = UnzipFile('temp/' + hashValue + '.zip', 'unzip/')
                        if unzip_path == -1:
                            makeRawData(symbol, hashValue, datetime, '', -1)
                            continue
                        if hashValue in BitcoinHash:
                            CombinationList.append([hashValue, date, hashValue, 100])
                        else:
                            CombinationList = CompareBitcoin(symbol, unzip_path, hashValue, datetime, BitcoinList, ith, CombinationList)
                        os.system('rm temp/' + hashValue + '.zip')
                        os.system('rm -rf unzip/*')
                break
        new_url = handler.FindNewerPage(codes)
        if new_url == 0:
            break
        if current_url != new_url:
            current_url = new_url
            handler.OpenURL(new_url)
    return CombinationList

@ray.remote
def parse(urlList, BitcoinList, ith, BitcoinHash, BitcoinDateHash):
    skipList = makeSkipList()
    if not os.path.exists('tmp' + str(ith)):
        os.mkdir('tmp' + str(ith))
    partialList = sorted(os.listdir('CoinsList'))
    dirnames_folder = sorted(os.listdir('CoinsList'))
    sleep(ith + 1)
    while True:
        if len(dirnames_folder) <= 0:
            break
        symbol = dirnames_folder[0]
        dirnames_folder.pop(0)
        try:
            os.remove('CoinsList/' + symbol)
        except:
            continue
        if symbol in skipList:
            continue
        initRawData(symbol)
        LOGD("Symbol: %s (%d/%d) - %d process", (symbol, partialList.index(symbol) + 1, len(partialList), ith), 1)
        LOGD("Forked commit download...", (), 2)
        filepathes = os.listdir('../03_Unzip_Current_Past/Unzip/')
        for filenames in filepathes:
            if filenames.split('_')[0] in symbol:
                unzip_path = '../03_Unzip_Current_Past/Unzip/' + filenames + '/'
                break
        CombinationList = CompareBitcoin(symbol, unzip_path, urlList[symbol]['URL'].split('/')[-1], urlList[symbol]['Date'], BitcoinList, BitcoinHash, BitcoinDateHash, ith)
        CombinationList = sorted(CombinationList, key=lambda x: (-x[3], x[1]))
        makeResults(symbol, CombinationList[0][3], CombinationList[0][1], CombinationList[0][2], CombinationList[0][0])
    LOGD("Process %d is finished...", (ith), 10, 1)
    return

if __name__ == '__main__':
    initLog()
    if os.path.exists('SimilarityComparison.csv'):
        LOGD("Please backup the result file.")
        sys.exit()
    initResults()
    if not os.path.exists('raw_data'):
        os.mkdir('raw_data')
    if not os.path.exists('temp'):
        os.mkdir('temp')
    if not os.path.exists('unzip'):
        os.mkdir('unzip')
    LOGD("Program Starting! Name: %s", (os.path.basename(__file__)))
    BitcoinList_tmp = os.listdir('../03_Unzip_Current_Past/BTC_versions/')
    BitcoinHash = []
    for filename in BitcoinList_tmp:
        BitcoinHash.append(filename.split('_')[-1].split('.')[0])
    BitcoinList = {}
    for filename in BitcoinList_tmp:
        BitcoinList[filename.split('_')[-1].split('.')[0]] = filename
    fp = open('../01_Download_Current_190903/BTC_logs.csv', 'r', encoding='utf-8', errors='ignore')
    lines = fp.readlines()
    fp.close()
    BitcoinDateHash = {}
    for line in lines[1:]:
        line = line.replace('\n','').split(',')
        if int(line[0]) not in list(BitcoinDateHash.keys()):
            BitcoinDateHash[int(line[0])] = []
        BitcoinDateHash[int(line[0])].append(line[2])
    urlList = {}
    fp = open('../00_Dataset/Total_point.csv', 'r', encoding='utf-8', errors='ignore')
    lines = fp.readlines()
    fp.close()
    for line in lines:
        line = line.replace('\n','').split(',')
        if 'BTG0' in line[0]:
            urlList[line[0]] = {'Date': int(line[1]), 'Datetime': int(line[2]), 'URL': 'https://github.com/BTCGPU/BTCGPU/commit/a56f8b0be3700d608a5634af8c862910f4be2191'}
        else:
            urlList[line[0]] = {'Date': int(line[1]), 'Datetime': int(line[2]), 'URL': line[3]}
    partialList = list(urlList.keys())
    for symbol in partialList:
        fp = open('CoinsList/' + symbol, 'w')
        fp.close()
    ray.get([parse.remote(urlList, BitcoinList, ith, BitcoinHash,BitcoinDateHash) for ith in range(mass)])
    LOGD("Program End! Name: %s", (os.path.basename(__file__)))

