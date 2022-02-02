from datetime import datetime as dt
from time import ctime, sleep
import json, os, zipfile, wget, math, sys

sequence = sys.argv[1]
def unzip(filename, foldername):
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(foldername)
    return foldername

def bar_custom(current, total, width=80):
    width = 30
    avail_dots = width-2
    shaded_dots = int(math.floor(float(current) / total * avail_dots))
    percent_bar = '[' + '■' * shaded_dots + ' ' * (avail_dots-shaded_dots) + ']'
    progress = "%d%% %s [%d / %d]" % (current / total * 100, percent_bar, current, total)

def download(url, filename):
    wget.download(url, filename, bar=bar_custom)
    return filename

jplag = 'jplag-2.12.1-SNAPSHOT-jar-with-dependencies.jar'
threshold = 92.9
cut_threshold = 70

bitcoin_commits = {}
with open('BTC_logs.csv', 'r', encoding='utf-8', errors='ignore') as file:
    lines = file.readlines()

for line in lines[1:]:
    line = line.strip().split(',')
    datetime = dt(int(line[0].strip()[:4]), int(line[0].strip()[4:6]), 1)
    if datetime not in bitcoin_commits:
        bitcoin_commits[datetime] = [line[2].strip()]
    else:
        bitcoin_commits[datetime].append(line[2].strip())

unzip_path = 'compare_heu2/%s/' % (sequence)
if not os.path.exists(unzip_path):
    os.makedirs(unzip_path)

uniquestr1 = "UNIQUESTRING1"
uniquestr2 = "UNIQUESTRING2"

def compare_two_cryptocurrency(filepath):
    temp_results = 'temp_results_%s/' % (sequence)
    results_filename = 'results_%s.txt' % (sequence)
    while True:
        os.system('java -jar %s -l c/c++ -r %s -s %s > %s' % (jplag, temp_results, filepath, results_filename))
        fp = open(results_filename, 'r', encoding='utf-8', errors='ignore')
        parse_checker = False
        while True:
            line = fp.readline()
            if line == '':
                break
            if 'parser errors!' in line or 'parser error!' in line:
                if '0 parser errors!' in line:
                    parse_checker = True
                break
            elif 'nothing to parse for submission' in line:
                fp.close()
                os.system('rm "%s"' % (results_filename))
                os.system('rm -rf "%s"' % (temp_results))
                if line.split('"')[1] == uniquestr1:
                    return -2
                return -1
        if line == '':
            fp.close()
            os.system('rm "%s"' % (results_filename))
            os.system('rm -rf "%s"' % (temp_results))
            return -1
        if parse_checker:
            while True:
                line = fp.readline()
                if line == '':
                    fp.close()
                    os.system('rm "%s"' % (results_filename))
                    os.system('rm -rf "%s"' % (temp_results))
                    return -1
                elif 'Comparing' in line:
                    point = float(line.split(':')[-1].replace('\n','').replace(' ',''))
                    fp.close()
                    os.system('rm "%s"' % (results_filename))
                    os.system('rm -rf "%s"' % (temp_results))
                    return point
        else:
            while True:
                line = fp.readline()
                if line == '':
                    break
                elif 'nothing to parse for submission' in line:
                    fp.close()
                    os.system('rm "%s"' % (results_fileanme))
                    os.system('rm -rf "%s"' % (temp_results))
                    if line.split('"')[1] == uniquestr1:
                        return -2
                    return -1
                elif '[' in line and ']' in line and (uniquestr1 in line or uniquestr2 in line):
                    folder_name = line.replace('[','').replace(']','').replace('\n','')
                    line = fp.readline()
                    filename = line.split(':')[0].split("'")[1]
                    os.system('rm "%s%s/%s"' % (filepath, folder_name, filename))
        fp.close()

base_path = 'Coins/'
coin_list = os.listdir(base_path)

skip_list = []
with open('skip_list.csv', 'r', encoding='utf-8', errors='ignore') as file:
    lines = file.readlines()
for coin in lines:
    skip_list.append(coin.strip())

comparison_file = 'commit_comparison/'
#fp_r = open('child_coin_heu02.csv', 'w')
current_coin_list = os.listdir('Coins_current/')
if not os.path.exists('occupied/'):
    os.makedirs('occupied/')
if not os.path.exists('done/'):
    os.makedirs('done/')
coin_list.sort()
for coin in coin_list[:int(len(coin_list)/4*3)]:
    if coin.split('_')[0] in skip_list:
        continue
    if os.path.exists('occupied/' + coin) or os.path.exists('done/' + coin):
        continue
    fp = open('occupied/' + coin, 'w')
    fp.close()
    target_date = dt(int(coin.split('_')[1][:4]), int(coin.split('_')[1][4:6]), int(coin.split('_')[1][6:]))
    target_hash = coin.split('_')[2].split('.')[0]
    unzip_filename = unzip(base_path + coin, unzip_path + uniquestr1)
    max_point = 0
    finished = False
    if not os.path.exists(comparison_file + target_hash):
        os.makedirs(comparison_file + target_hash)
    for datetime in bitcoin_commits:
        bit_date = datetime
        if bit_date <= target_date:
            for bit_hash in bitcoin_commits[datetime]:
                if not os.path.exists(comparison_file + bit_hash):
                    os.makedirs(comparison_file + bit_hash)
                if os.path.exists(comparison_file + target_hash + '/' + bit_hash + '.json'):
                    with open(comparison_file + target_hash + '/' + bit_hash + '.json', 'r') as json_file:
                        point = json.load(json_file)
                        point = point['point']
                        if point == -1:
                            if not os.path.exists('BTC_versions/BTC_%s.zip' % (bit_hash)):
                                download_name = download('https://github.com/bitcoin/bitcoin/archive/%s.zip' % (bit_hash), 'BTC_versions/BTC_%s.zip' % (bit_hash))
                            download_name = 'BTC_versions/BTC_%s.zip' % (bit_hash)
                            unzip_filename = unzip(download_name, unzip_path + uniquestr2)
                            point = compare_two_cryptocurrency(unzip_path)
                            print('%s - %s (%d/%d) - Bitcoin (%d/%d): %d (%d/%d)' % (sequence, coin.split('_')[0], coin_list.index(coin), len(coin_list), list(bitcoin_commits.keys()).index(datetime), len(list(bitcoin_commits.keys())), point, bitcoin_commits[datetime].index(bit_hash), len(bitcoin_commits[datetime])))
                            os.system('rm -rf "%s"' % (unzip_path + uniquestr2))
                            with open(comparison_file + target_hash + '/' + bit_hash + '.json', 'w') as json_file:
                                json.dump({'point': point}, json_file)
                            with open(comparison_file + bit_hash + '/' + target_hash + '.json', 'w') as json_file:
                                json.dump({'point': point}, json_file)
                            if max_point < point:
                                max_point = point
                                max_date = bit_date
                                max_hash = bit_hash
                        elif max_point < point:
                            max_point = point
                            max_date = bit_date
                            max_hash = bit_hash
                            print('%s - %s (%d/%d) - Bitcoin (%d/%d): %d (%d/%d)' % (sequence, coin.split('_')[0], coin_list.index(coin), len(coin_list), list(bitcoin_commits.keys()).index(datetime), len(list(bitcoin_commits.keys())), point, bitcoin_commits[datetime].index(bit_hash), len(bitcoin_commits[datetime])))
                        else:
                            print('%s - %s (%d/%d) - Bitcoin (%d/%d): %d (%d/%d)' % (sequence, coin.split('_')[0], coin_list.index(coin), len(coin_list), list(bitcoin_commits.keys()).index(datetime), len(list(bitcoin_commits.keys())), point, bitcoin_commits[datetime].index(bit_hash), len(bitcoin_commits[datetime])))
 
                else:
                    if not os.path.exists('BTC_versions/BTC_%s.zip' % (bit_hash)):
                        download_name = download('https://github.com/bitcoin/bitcoin/archive/%s.zip' % (bit_hash), 'BTC_versions/BTC_%s.zip' % (bit_hash))
                    download_name = 'BTC_versions/BTC_%s.zip' % (bit_hash)
                    unzip_filename = unzip(download_name, unzip_path + uniquestr2)
                    point = compare_two_cryptocurrency(unzip_path)
                    print('%s - %s (%d/%d) - Bitcoin (%d/%d): %d (%d/%d)' % (sequence, coin.split('_')[0], coin_list.index(coin), len(coin_list), list(bitcoin_commits.keys()).index(datetime), len(list(bitcoin_commits.keys())), point, bitcoin_commits[datetime].index(bit_hash), len(bitcoin_commits[datetime])))
                    os.system('rm -rf "%s"' % (unzip_path + uniquestr2))
                    with open(comparison_file + target_hash + '/' + bit_hash + '.json', 'w') as json_file:
                        json.dump({'point': point}, json_file)
                    with open(comparison_file + bit_hash + '/' + target_hash + '.json', 'w') as json_file:
                        json.dump({'point': point}, json_file)
                    if max_point < point:
                        max_point = point
                        max_date = bit_date
                        max_hash = bit_hash
                    if point == -2:
                        finished = True
                if point < cut_threshold:
                    break
        if finished:
            break
    if max_point >= threshold:
        os.system('rm -rf "%s"' % (unzip_path + uniquestr1))
        for curr in current_coin_list:
            symbol = curr.split('_')[0]
            if symbol == coin.split('_')[0]:
                unzip_filename = unzip('Coins_current/' + curr, unzip_path + uniquestr1)
                unzip_filename = unzip('BTC_versions/BTC_%s.zip' % (max_hash), unzip_path + uniquestr2)
                point = compare_two_cryptocurrency(unzip_path)
                break
        fp_r = open('child_coin_heu02.csv', 'a')
        fp_r.write('%s,%g,%g,%s\n' % (coin.split('_')[0], max_point, point, max_date.strftime("%Y%m%d")))
        fp_r.close()
    os.system('rm -rf "%s"' % (unzip_path))
    os.system('mv "occupied/%s" done/' % (coin))
#fp_r.close()
