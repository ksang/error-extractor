#!/usr/bin/python

'''Configurations'''
PARSER_DEFINITION_FILE      = 'parsers.xml'

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
        for idx, line in enumerate(data_list):
            if self.__line_parse(line):
                file_output.append((idx, line))
        if len(file_output) > 0:
            self.__output(log_file, file_output, display)
            file_output = []

    def __time_parse(self, data):
        res = []
        for line in data:
            ts = self.__line_timestamp(line)
            print "ts: %s | line: %s" % (ts, line)
            if ts is not None:
                if self.timeutil.is_in_window(ts):
                    res.append(line)
        return res

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

