import os, sys
import getopt
import statistics
from time import ctime
from datetime import datetime, timedelta
from colorama import init
from colorama import Fore

def LOGD(string, attr=(), depths=0, color=0):
    if color == 0:
        print(Fore.WHITE + ' ' * depths + '[%s] ' % (ctime()) + string % (attr))
    elif color == 1:
        print(Fore.RED + ' ' * depths + '[%s] ' % (ctime()) + string % (attr))
    fp = open("logs.txt", 'a')
    fp.write(' ' * depths + '[%s] ' % (ctime()) + string % (attr) + '\n')
    fp.close()

class CombineOne:
    def __init__(self, ofile, sd, md, fd, ed):
        fp = open("logs.txt", 'w')
        fp.close()
        self.log_filename = ofile
        fp = open(self.log_filename, 'w')
        fp.write('Symbol,Commits,Branches,Releases,Contributors,Watch,Star,Fork,Issues,Pull requests,Open Issues,Closed Issues,')
        fp.write('3M ave. add,3M std. add,3M ave. del,3M std. del,3M ave. update,3M std. update,')
        fp.write('6M ave. add,6M std. add,6M ave. del,6M std. del,6M ave. update,6M std. update,')
        fp.write('12M ave. add,12M std. add,12M ave. del,12M std. del,12M ave. update,12M std. update,')
        fp.write('MDE3,MDE6,MDE12,3M commits,6M commits,12M commits')
        fp.write('\n')
        fp.close()
        self.sd = sd
        self.md = md
        self.fd = fd
        self.ed = ed

    def searchFiles(self, dirname, filepath):
        filenames = os.listdir(dirname)
        for filename in filenames:
            full_filename = os.path.join(dirname, filename)
            if os.path.isdir(full_filename):
                filepath = self.searchFiles(full_filename, filepath)
            else:
                filepath.append(full_filename)
        return filepath

    def Gather(self):
        filepath = self.searchFiles('raw_data', [])
        for filename in filepath:
            fp = open(filename, 'r')
            lines = fp.readlines()
            fp.close()
            fp = open(self.log_filename,'a')
            symbol = filename.split('/')[-1].split('.')[0]
            LOGD("Symbol: %s", (symbol), 1)
            fp.write('%s,%s' % (symbol, lines[1].replace('\n','').replace(' ','')))
            LOGD("Commits...: %s", (lines[1].replace('\n','').replace(' ','')), 2)
            add3M = []
            del3M = []
            update3M = []
            add6M = []
            del6M = []
            update6M = []
            add12M = []
            del12M = []
            update12M = []
            cont_total = [[],[],[],[], \
                          [],[],[],[], \
                          [],[],[],[]]
            com3M = 0
            com6M = 0
            com12M = 0
            for line in lines[3:]:
                line = line.replace(' ','').replace('\n','').split(',')
                if self.td <= line[0] <= self.ed:
                    add3M.append(int(line[2]))
                    del3M.append(int(line[3]))
                    update3M.append(line[0])
                    com3M+=1
                if self.md <= line[0] <= self.ed:
                    add6M.append(int(line[2]))
                    del6M.append(int(line[3]))
                    update6M.append(line[0])
                    com6M+=1
                add12M.append(int(line[2]))
                del12M.append(int(line[3]))
                update12M.append(line[0])
                cont_total[int(line[0][4:6]) - 1].append(line[4])
                com12M+=1
            #### 3M ####
            ave_add, std_add = self.stat_ave_std(add3M)
            ave_del, std_del = self.stat_ave_std(del3M)
            update = []
            before = datetime.strptime(self.td, '%Y%m%d').date()
            for date in update3M:
                update.append((datetime.strptime(date, '%Y%m%d').date() - before).days)
                before = datetime.strptime(date, '%Y%m%d').date()
            if before == datetime.strptime(self.td, '%Y%m%d').date():
                update.append((datetime.strptime('30000101', '%Y%m%d').date() - before).days)
            else:
                update.append((datetime.strptime(self.ed, '%Y%m%d').date() - before).days)
            ave_update, std_update = self.stat_ave_std(update)
            fp.write('%g,%g,%g,%g,%g,%g,' % (ave_add, std_add, ave_del, std_del, ave_update, std_update))
            #### 6M ####
            ave_add, std_add = self.stat_ave_std(add6M)
            ave_del, std_del = self.stat_ave_std(del6M)
            update = []
            before = datetime.strptime(self.md, '%Y%m%d').date()
            for date in update6M:
                update.append((datetime.strptime(date, '%Y%m%d').date() - before).days)
                before = datetime.strptime(date, '%Y%m%d').date()
            if before == datetime.strptime(self.md, '%Y%m%d').date():
                update.append((datetime.strptime('30000101', '%Y%m%d').date() - before).days)
            else:
                update.append((datetime.strptime(self.ed, '%Y%m%d').date() - before).days)
            ave_update, std_update = self.stat_ave_std(update)
            fp.write('%g,%g,%g,%g,%g,%g,' % (ave_add, std_add, ave_del, std_del, ave_update, std_update))
            #### 12M ####
            ave_add, std_add = self.stat_ave_std(add12M)
            ave_del, std_del = self.stat_ave_std(del12M)
            update = []
            before = datetime.strptime(self.sd, '%Y%m%d').date()
            for date in update12M:
                update.append((datetime.strptime(date, '%Y%m%d').date() - before).days)
                before = datetime.strptime(date, '%Y%m%d').date()
            if before == datetime.strptime(self.sd, '%Y%m%d').date():
                update.append((datetime.strptime('30000101', '%Y%m%d').date() - before).days)
            else:
                update.append((datetime.strptime(self.ed, '%Y%m%d').date() - before).days)
            ave_update, std_update = self.stat_ave_std(update)
            fp.write('%g,%g,%g,%g,%g,%g,' % (ave_add, std_add, ave_del, std_del, ave_update, std_update))
            #### MDE ####
            total_dev = []
            for index in range(0, 12):
                total_dev = total_dev + cont_total[index]
            num_total_dev = len(list(set(total_dev)))
            if num_total_dev == 0:
                fp.write('0,0,0,')
            else:
                for num in [3, 6, 12]:
                    mde = 0.0
                    for start in range(0, 12, int(12/num)):
                        emptyList = []
                        for index in range(start, start+int(12/num)):
                            emptyList = emptyList + cont_total[index]
                        mde = mde + (float(len(list(set(emptyList))))/float(num_total_dev))
                    fp.write('%g,' % (mde/float(num)))
            fp.write('%d,%d,%d,' % (com3M, com6M, com12M))
            fp.write('\n')
            fp.close()

    def stat_ave_std(self, lst):
        if len(lst) == 0:
            ave = 0
        else:
            ave = float(sum(lst))/float(len(lst))
        if len(lst) < 2:
            std = 99999
        else:
            std = statistics.stdev(lst)
        return ave, std

if __name__ == '__main__':
    argv = sys.argv
    try:
        opt, etc_args = getopt.getopt(argv[1:], "Ho:s:h:t:e:", ["Help", "ofile=", "start=", "mid=", "third=", "end="])
    except getopt.GetoptError:
        print(argv[0], '-o <output filename> -s <start date> -h <mid date> -t <third date> -e <end date>')
        sys.exit(2)
    ofile = 'Maintenance.csv'
    start_date = '20180101'
    mid_date = '20180701'
    third_date = '20181001'
    end_date = '20181231'
    for opt, arg in opts:
        if opt in ('-H', '--Help'):
            print(os.path.basename(__file__), '-s <start date> -h <mid date> -t <third date> -e <end date>')
            sys.exit()
        elif opt in ('-o', '--ofile'):
            ofile = arg
        elif opt in ('-s', '--start'):
            start_date = arg
        elif opt in ('-m', '--mid'):
            mid_date = arg
        elif opt in ('-t', '--third'):
            third_date = arg
        elif opt in ('-e', '--end'):
            end_date = arg
    LOGD("Program Starting! Name: %s", (os.path.basename(__file__)))
    handler = CombineOne(ofile = ofile, sd = start_date, md = arg, td = third_date, ed = end_date)
    handler.Gather()
    LOGD("Program End!")
