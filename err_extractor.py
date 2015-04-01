#!/usr/bin/python

'''Configuration'''

BACKTRACK_MAX               = 50

'''Global Data'''
LINE_OPERATOR               = {}
LINE_FILTER                 = {}
TIMESTAMP_FORMATTER         = {}

import os,sys
import argparse
import xml.etree.ElementTree as ET

from lib.data import DataUtil
from lib.timestamp import TimeUtil

class ArgParser:
    def parse(self):
        # Parse arguments from cli
        import argparse
        from argparse import RawTextHelpFormatter
        __parser = argparse.ArgumentParser(description= '\tError Extractor, get error messages from log files.',
                                           formatter_class = RawTextHelpFormatter)
        __parser.add_argument('-p', '--path',
                              type = str,
                              required = True,
                              help = 'Log file root folder location.')
        __parser.add_argument('-d', '--definition',
                              type = str,
                              default = 'parsers.xml',
                              help = 'Parser definition file, default is \'parsers.xml\'')
        __parser.add_argument('-w', '--window',
                              type = str,
                              nargs = 2,
                              metavar = ('START_TIME','END_TIME'),
                              help = 'Start time and end time in YYYY-MM-DD HH:MM:SS')

        return __parser.parse_args()

class ParserLoader:
    def __init__(self, dfile):
        self.file = dfile

    def __row_loader(self, row, storage):
        if row.tag != 'Row':
            return
        temp = {}
        for v in row.getchildren():
            if temp.has_key(v.tag):
                if type(temp[v.tag]) is list:
                    temp[v.tag].append(v.text)
                else:
                    buf = []
                    buf.append(temp[v.tag])
                    buf.append(v.text)
                    temp[v.tag] = buf
            else:
                temp[v.tag] = v.text
        if temp.has_key('id'):
            key = int(temp['id'])
            temp.pop('id')
            storage[key] = temp

    def __section_loader(self, root, sect_name, storage):
        assert(root is not None)
        if root.tag != 'Parsers':
            return
        for child in root.getchildren():
            if child.tag == sect_name:
                for row in child.getchildren():
                    self.__row_loader(row, storage)        

    def _load_line_operator(self, root):
        self.__section_loader(root, 'LineOperator', LINE_OPERATOR)

    def _load_line_filter(self, root):
        self.__section_loader(root, 'LineFilter', LINE_FILTER)

    def _load_timestamp_formatter(self, root):
        self.__section_loader(root, 'TimeStamp', TIMESTAMP_FORMATTER)

    def _load_file(self):
        try:
            f = open(self.file, 'r')
            root = ET.fromstring(f.read())
        except Exception, err:
            sys.stderr.write("Failed to load parser definition file: %s, error: %s\n" % (self.file, err))
            sys.exit(1)
        return root

    def run(self):
        root = self._load_file()
        self._load_line_operator(root)
        self._load_line_filter(root)
        self._load_timestamp_formatter(root)

class ErrorExtractor:
    datautil = DataUtil()
    log_files = []

    def _get_log_files(self, path):
        self.log_files = self.datautil.get_text_files(path)

    def _print_filename(self, fn, count):
        print "File: %s" % fn
        print "(%s errors)" % count

    def _print_error(self, lineno, error):
        print "%s: %s" % (lineno, error.strip())

class LineErrorExtractor(ErrorExtractor):

    timeutil = None

    def __output(self, fn, err_list, display):
        if display:
            self._print_filename(fn, len(err_list))
            for err in err_list:
                self._print_error(err[0], err[1])

    def __line_filter(self, line):
        for ft in LINE_FILTER.values():
            if ft.get('case_sensitive') == 'false':
                line = line.lower()
            key = ft.get('value')
            if line.find(key) != -1:
                return True
        return False

    def __line_timestamp(self, line):
        for fm in TIMESTAMP_FORMATTER.values():

            token = fm.get('token')
            locations = fm.get('locations')
            ignore = fm.get('ignore')
            msreplace = fm.get('msreplace')

            buf = line.split(token)
            buf = [e for e in buf if e != '']
            #print buf
            if len(buf) < 2:
                continue
            if type(locations) == str:
                locations = [locations]
            if type(ignore) == str:
                ignore = [ignore]
            for loc in locations:
                loc = loc.split(',')
                timestamp = ''
                for pos in loc:
                    if int(pos) > len(buf) - 1:
                        break
                    sec = buf[int(pos)]
                    if ignore is not None:
                        for ig in ignore:
                            sec = sec.replace(ig, '')

                    if msreplace is not None:
                        sec = sec.replace(',','.')
                    if not self.timeutil.is_timestamp(sec.strip()):
                        break
                    timestamp += sec
                    if token == ' ':
                        timestamp += token
                if len(timestamp) < 10:
                    break
                #print timestamp
                date = self.timeutil.parse(timestamp.strip())
                if date is not None:
                    return date
        return None

    def __line_parse(self, line):
        for op in LINE_OPERATOR.values():
            if op.get('case_sensitive') == 'false':
                line = line.lower()
            key = op.get('value')
            if line.find(key) != -1:
                if not self.__line_filter(line):
                    return True
        return False

    def __data_parse(self, data_list, log_file, kwargs):
        file_output = []
        display = kwargs.get('display')
        if len(data_list) == 0:
            return
        if type(data_list[0]) is tuple:
            for line in data_list:
                if self.__line_parse(line[1]):
                    file_output.append(line[0], line[1])
        else:
            for idx, line in enumerate(data_list):
                if self.__line_parse(line):
                    file_output.append((idx, line))
        if len(file_output) > 0:
            self.__output(log_file, file_output, display)
            file_output = []

    def __find_prev_timestamp(self, data, idx, imin):
        if idx <= 0:
            return None;
        for i in range(idx-1, max(imin, idx-BACKTRACK_MAX)):
            ts = self.__line_timestamp(data[i])
            if ts is not None:
                return (i, ts)
        return (None, None)

    def __find_next_timestamp(self, data, idx, imax):
        for i in range(idx+1, min(imax, idx+BACKTRACK_MAX)):
            ts = self.__line_timestamp(data[i])
            if ts is not None:
                return ts
        return None            

    def __find_start_in_win(self, data, imin, imax):
        if imin > imax:
            return None
        mid = (imin + imax) / 2
        print "imin:%s imax:%s mid:%s" %(str(imin), str(imax), str(mid))
        line = data[mid]
        ts = self.__line_timestamp(line)
        if ts is None:
            return self.__find_start_in_win(data, imin, imax - 1)
        else:
            if self.timeutil.is_in_window(ts):
                if mid <= imin:
                    return mid
                (i, prev_ts) = self.__find_prev_timestamp(data, mid, imin)
                if prev_ts is not None:
                    if not self.timeutil.is_in_window(prev_ts):
                        return mid
                    else:
                        return self.__find_start_in_win(data, imin, mid-1)
                else:
                    return mid
            else:
                return self.__find_start_in_win(data, mid+1, imax)
        return None

    def __find_end_in_win(self, data, imin, imax):
        if imin > imax:
            return None
        mid = (imin + imax) / 2
        line = data[mid]
        ts = self.__line_timestamp(line)
        if ts is None:
            return self.__find_end_in_win(data, imin, imax - 1)
        else:
            if self.timeutil.is_in_window(ts):
                if mid == imin:
                    return mid
                next_ts = self.__find_next_timestamp(data, mid, imax)
                if next_ts is not None:
                    if not self.timeutil.is_in_window(next_ts):
                        return mid
                    else:
                        return self.__find_end_in_win(data, mid+1, imax)
                else:
                    return mid
            else:
                return self.__find_end_in_win(data, imin, mid-1)
        return None

    def __get_logs_in_win(self, data):
        # return line number range (start, end) for logs in time window
        nol = len(data)
        assert nol > 0
        start = end = None
        first_ts = self.__line_timestamp(data[0])
        last_ts = self.__line_timestamp(data[nol-1])
        print "first_ts:%s, last_ts:%s" % (first_ts, last_ts)
        if first_ts is None:
            return(start, end)
        else:
            if self.timeutil.is_after_window(first_ts):
                return (start, end)
            # if all the logs in this file is in window
            if self.timeutil.is_in_window(first_ts):
                start = 0
            if last_ts is not None:
                if self.timeutil.is_in_window(last_ts):
                    end = nol - 1
            if start is None:
                start = self.__find_start_in_win(data, 0, nol-1)
            if end is None:
                end = self.__find_end_in_win(data, 0, nol-1)
            return(start, end)

    def __prototype_time_parse(self, data):
        res = []
        win = self.__get_logs_in_win(data)
        if win[0] is None or win[1] is None:
            return res
        for i in range(win[0], win[1])
            ts = self.__line_timestamp(data[i])
            #print "ts: %s | line: %s" % (ts, line)
            if ts is not None:
                if self.timeutil.is_in_window(ts):
                    res.append((i, data[i])))
        return res

    def _time_parse(self, data):
        if len(data) == 0:
            return

    def parse(self, kwargs):
        window = kwargs.get('window')
        if window is not None:
            self.timeutil = TimeUtil(window[0], window[1])
            for log_file in self.log_files:
                data = open(log_file, 'r').readlines()
                data = self.__time_parse(data)
                self.__data_parse(data, log_file, kwargs)
        else:
            for log_file in self.log_files:
                data = open(log_file, 'r').readlines()
                self.__data_parse(data, log_file, kwargs)

    def run(self, path, **kwargs):
        self._get_log_files(path)
        self.parse(kwargs)

if __name__ == '__main__':
    args = ArgParser().parse()
    ParserLoader(args.definition).run()
    LineErrorExtractor().run(args.path, window=args.window, display=True)

