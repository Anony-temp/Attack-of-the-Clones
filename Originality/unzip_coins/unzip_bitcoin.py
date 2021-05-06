import os, sys
import zipfile, getopt
from time import ctime
from colorama import init
from colorama import Fore
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from lib.searchFiles import searchFiles

def LOGD(string, attr = (), depths = 0, color = 0):
    if color == 0:
        print(Fore.WHITE + ' ' * depths + '[%s] ' % (ctime()) + string % (attr))
    elif color == 1:
        print(Fore.RED + ' ' * depths + '[%s] ' % (ctime()) + string % (attr))
    fp = open('logs.txt', 'a')
    fp.write(' ' * depths + '[%s] ' % (ctime()) + string % (attr) + '\n')
    fp.close()

class UnzipFiles:
    def __init__(self):
        fp = open('logs.txt', 'w')
        fp.close()
        if not os.path.exists('tmp'):
            os.mkdir('tmp')
        self.unzip_folder = 'Unzip'
        if not os.path.exists('Unzip'):
            os.mkdir('Unzip')
        self.symbol = {}
        self.symbol2 = []

    def Destroy(self):
        self.DelFiles('tmp')

    def DelFiles(self, filepath):
        print(filepath)
        os.system('rm -r "' + filepath.replace('$','\$') + '"')

    def UnzipFile(self, filepath, targetDir):
        try:
            unzipFile = zipfile.ZipFile(filepath)
            unzipFile.extractall(targetDir + '/')
            unzipFile.close()
        except Exception as e:
            LOGD("Unzip error... %s", (filepath), 10, 1)
            return -1
        return 0

    def Unzip(self, target_folder, middle, last, lang):
        LOGD("Get filenames from %s", (target_folder), 1)
        filepath = searchFiles(target_folder, [], ['zip'])
        LOGD("Unzip start.", (), 1)
        if not os.path.exists(self.unzip_folder + '/' + middle):
            os.mkdir(self.unzip_folder + '/' + middle)
        if not os.path.exists(self.unzip_folder + '/' + middle + '/' + last):
            os.mkdir(self.unzip_folder + '/' + middle + '/' + last)
        for filename in filepath:
            folder_name = filename.split('/')[-1].split('.')[0]#.replace('$','\$')
            LOGD("Target file: %s", (folder_name), 2)
            #if self.symbol[folder_name.split('_')[0]] not in lang:
            #    continue
            #if '$PAC0' in folder_name:
            #    continue
            if folder_name.split('_')[0] not in self.symbol2:
                continue
            if not os.path.exists(self.unzip_folder + '/' + middle + '/' + last + '/' + folder_name):
                os.mkdir(self.unzip_folder + '/' + middle + '/' + last + '/' + folder_name)
            ret = self.UnzipFile(filename, self.unzip_folder + '/' + middle + '/' + last + '/' + folder_name)
            if ret == -1:
                LOGD("Unzip failed... %s", (folder_name), 10, 1)
                #self.DelFiles(self.unzip_folder + '/' + middle + '/' + last + '/' + folder_name)
                self.DelFiles(filename)
                continue
            folder_path = searchFiles(self.unzip_folder + '/' + middle + '/' + last + '/' + folder_name, [], lang)
            if folder_path == []:
                LOGD("None C/C++ coins. %s", (folder_name), 10, 1)
                self.DelFiles(self.unzip_folder + '/' + middle + '/' + last + '/' + folder_name)
            LOGD("Done target: %s.", (folder_name), 2)
        LOGD("Done unzip.", (), 1)

    def parse(self, filename):
        fp = open(filename, 'r', encoding='utf-8', errors='ignore')
        lines = fp.readlines()
        fp.close()
        for line in lines:
            line = line.split(',')
            count = 0
            while True:
                if line[0] + str(count) not in list(self.symbol.keys()):
                    self.symbol[line[0] + str(count)] = line[-2]
                    break
                count = count + 1
            #print(line[0] + ' - ' + line[-2])
    def parse2(self, filename):
        fp = open(filename, 'r', encoding='utf-8', errors='ignore')
        lines = fp.readlines()
        fp.close()
        for line in lines:
            line = line.split(',')
            self.symbol2.append(line[0])

if __name__ == '__main__':
    LOGD("Program Starting! Name: %s", (os.path.basename(__file__)))
    argv = sys.argv
    try:
        opts, etc_args = getopt.getopt(argv[1:], "ht:", ["help", "target="])
    except getopt.GetoptError:
        print(argv[0], "-t <target folder path>")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(argv[0], '-t <target folder path>')
        elif opt in ('-t', '--target'):
            target_path = arg
    handler = UnzipFiles()
    handler.parse('../dataset/coin_list_git.csv')
    handler.parse2('../determine_forking_time/Total_point.csv')
    handler.Unzip(target_path, 'Bitcoin', 'Current', ['c', 'cpp', 'h', 'hpp', 'c++', 'h++'])
    handler.Destroy()
