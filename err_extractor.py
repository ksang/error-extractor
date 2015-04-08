#!/usr/bin/python

'''Configuration'''
# Max number of lines for timestamp backtracking.
BACKTRACK_MAX               = 50
# When doing timestamp parsing, how many lines of logs will be transfered if they don't 
# have timestamp for further processing after a successful parse of line.
# this setting is designed for error message such as java exceptions.
NOTIMESTAMP_MAX             = 30

'''Global Data'''
LINE_OPERATOR               = {}
SECTION_STARTER             = {}
LINE_FILTER                 = {}
TIMESTAMP_FORMATTER         = {}

import os,sys
import argparse
import xml.etree.ElementTree as ET

from lib.data import DataUtil
from lib.timestamp import TimeUtil
from lib.html import HTMLGen

class ArgParser:
    def parse(self):
        # Parse arguments from cli
        import argparse
        from argparse import RawTextHelpFormatter
        __parser = argparse.ArgumentParser(formatter_class = RawTextHelpFormatter)
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
        __parser.add_argument('-o', '--output',
                              type = str,
                              help = 'Save report to a html file, provide filename.')
        __parser.add_argument('-f', '--fast',
                              action = 'store_true',
                              required = False,
                              help = 'Run timestamp parsing in fast mode, better for large logs.')

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

    def _load_section_starter(self):
        for pid in LINE_OPERATOR.keys():
            starter = LINE_OPERATOR[pid].get('starter')
            if starter is not None:
                SECTION_STARTER[pid] = LINE_OPERATOR[pid]

    def run(self):
        root = self._load_file()
        self._load_line_operator(root)
        self._load_line_filter(root)
        self._load_timestamp_formatter(root)
        self._load_section_starter()

class ErrorExtractor:
    datautil = DataUtil()
    log_files = []
    htmlgen = HTMLGen()

    def _get_log_files(self, path):
        self.log_files = self.datautil.get_text_files(path)

    def _print_filename(self, fn, count):
        print "File: %s" % fn
        print "(%s errors)" % count

    def _print_error(self, lineno, error):
        ln = str(lineno)
        ln = (8 - len(ln)) * ' ' + ln
        print "%s: %s" % (ln, error.strip())

    def _open_report_file(self, filename):
        try:
            outfile = open(filename, 'a')
        except Exception, err:
            sys.stderr.write("Failed to open output report file %s, error: %s" % (output, err))
            sys.exit(1)
        return outfile

    def _write_report_file(self, fd, data):
        try:
            fd.write(data)
        except Exception, err:
            sys.stderr.write("Failed to write output report file %s, error: %s" % (output, err))
            sys.exit(1)

    def _check_report_file(self, filename):
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception, err:
                sys.stderr.write("Failed to cleanup output report file %s, error: %s" % (output, err))
                sys.exit(1)

    def _get_relative_path(self, full_path, root_path):
        if len(full_path) > len(root_path):
            return full_path[len(root_path):]
        else:
            return full_path

class LineErrorExtractor(ErrorExtractor):

    timeutil = None

    def __output(self, fn, err_list, display, output):
        if display:
            self._print_filename(fn, len(err_list))
            for err in err_list:
                self._print_error(err[0]+1, err[1])
        if output is not None:
            outfile = self._open_report_file(output)
            report = ''
            report += self.htmlgen.bold(fn) + '\n'
            report += self.htmlgen.bold("(%s errors)" % len(err_list))
            data_list = []
            for err in err_list:
                data_list.append((err[0]+1, self.htmlgen.raw(err[1])))
            report += self.htmlgen.gen_table_from_list(data_list, escape=False)
            self._write_report_file(outfile, report)

    def __line_filter(self, line):
        for ft in LINE_FILTER.values():
            if ft.get('case_sensitive') == 'false':
                line = line.lower()
            key = ft.get('value')
            if line.find(key) != -1:
                return True
        return False

    def _line_timestamp(self, line, get_id=False):
        for parser_id in TIMESTAMP_FORMATTER.keys():

            fm = TIMESTAMP_FORMATTER[parser_id]
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
                    if get_id:
                        return parser_id
                    else:
                        return date
        return None

    def _line_parse(self, line, dictionary=LINE_OPERATOR):
        for op in dictionary.values():
            if op.get('case_sensitive') == 'false':
                line = line.lower()
            key = op.get('value')
            if line.find(key) != -1:
                if not self.__line_filter(line):
                    return True
        return False

    def _data_parse(self, data_list, log_file, kwargs):
        file_output = []
        display = kwargs.get('display')
        output = kwargs.get('output')
        root_path = kwargs.get('path')
        if len(data_list) == 0:
            return
        if type(data_list[0]) is tuple:
            for line in data_list:
                if self._line_parse(line[1]):
                    file_output.append((line[0], line[1]))
        else:
            for idx, line in enumerate(data_list):
                if self._line_parse(line):
                    file_output.append((idx, line))
        if len(file_output) > 0:
            fn = self._get_relative_path(log_file, root_path)
            self.__output(fn, file_output, display, output)
            file_output = []

    def _find_prev_timestamp(self, data, idx, imin):
        '''
        find prev line in data from idx to after or equal imin that it's timestamp can be parsed. 
        the maximum find range is defined by BACKTRACK_MAX
        return (lineidx, timestamp)
        '''
        if idx >= imin and imin >= 0:
            if idx == imin:
                ts = self._line_timestamp(data[idx])
                return (idx, ts)
            low = max(imin, idx-BACKTRACK_MAX)
            for ri in range(low, idx):
                i = idx + low - ri
                ts = self._line_timestamp(data[i])
                if ts is not None:
                    return (i, ts)
        return (None, None)

    def _find_next_timestamp(self, data, idx, imax):
        '''
        find next line in data from idx to after or equal imin that it's timestamp can be parsed. 
        the maximum find range is defined by BACKTRACK_MAX
        return (lineidx, timestamp)
        '''
        if idx <= imax and idx >= 0:
            if idx == imax:
                ts = self._line_timestamp(data[idx])
                return (idx, ts)
            for i in range(idx, min(imax, idx+BACKTRACK_MAX, len(data)-1)):
                ts = self._line_timestamp(data[i])
                if ts is not None:
                    return (i, ts)
        return (None, None)

    def _line_timestamp_with_id(self, line, parser_id):
        fm = TIMESTAMP_FORMATTER[parser_id]
        token = fm.get('token')
        locations = fm.get('locations')
        ignore = fm.get('ignore')
        msreplace = fm.get('msreplace')

        buf = line.split(token)
        buf = [e for e in buf if e != '']
        if len(buf) < 2:
            return None
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
                timestamp += sec
                if token == ' ':
                    timestamp += token
            if len(timestamp) < 10:
                break
        date = self.timeutil.parse(timestamp.strip())
        return date

    def __get_first_ts_parser_id(self, data):
        assert type(data) is list
        for i in range(0, min(BACKTRACK_MAX, len(data)-1)):
            parser_id = self._line_timestamp(data[i], get_id=True)
            if parser_id is not None:
                return (i ,parser_id)
        return (None, None)

    def __time_parse(self, data):
        res = []
        last_line_in_store = float("-inf")
        if len(data) == 0:
            return res
        (istart, ts_parser_id) = self.__get_first_ts_parser_id(data)
        #print (istart, ts_parser_id) 
        if ts_parser_id is None:
            return res
        for i in range(istart, len(data)):
            ts = self._line_timestamp_with_id(data[i], ts_parser_id)
            if ts is not None:
                if self.timeutil.is_in_window(ts):
                    res.append((i, data[i]))
                    if self._line_parse(data[i], SECTION_STARTER):
                        last_line_in_store = i
            else:
                if i - last_line_in_store <= NOTIMESTAMP_MAX:
                    res.append((i, data[i]))
        return res

    def parse(self, kwargs):
        window = kwargs.get('window')
        if window is not None:
            self.timeutil = TimeUtil(window[0], window[1])
            for log_file in self.log_files:
                data = open(log_file, 'r').readlines()
                data = self.__time_parse(data)
                self._data_parse(data, log_file, kwargs)
        else:
            for log_file in self.log_files:
                data = open(log_file, 'r').readlines()
                self._data_parse(data, log_file, kwargs)

    def run(self, **kwargs):
        out = kwargs.get('output')
        if out is not None:
            self._check_report_file(out)
        path = kwargs.get('path')
        self._get_log_files(path)
        self.parse(kwargs)

class FastLineErrorExtractor(LineErrorExtractor):

    def __get_mid(self, a, b):
        if b - a == 1:
            return a
        else:
            return (a + b) / 2

    def __find_start_in_win(self, data, imin, imax):
        if imin > imax:
            return None
        mid = self.__get_mid(imin, imax)
        line = data[mid]
        (pos, ts) = self._find_prev_timestamp(data, mid, imin)
        if ts is None:
            (pos, ts)  = self._find_next_timestamp(data, mid, imax)
        if ts is not None:
            if self.timeutil.is_in_window(ts):
                if pos <= imin or pos >= imax:
                    return pos
                (i, prev_ts) = self._find_prev_timestamp(data, pos, imin)
                if prev_ts is not None:
                    if not self.timeutil.is_in_window(prev_ts):
                        return pos
                    else:
                        return self.__find_start_in_win(data, imin, i)
                else:
                    return pos
            else:
                if self.timeutil.is_after_window(ts):
                    return self.__find_start_in_win(data, imin, pos)
                else:
                    return self.__find_start_in_win(data, pos+1, imax)

    def __find_end_in_win(self, data, imin, imax):
        if imin > imax:
            return None
        mid = self.__get_mid(imin, imax)
        line = data[mid]
        (pos, ts) = self._find_next_timestamp(data, mid, imax)
        if ts is None:
            (pos, ts) = self._find_prev_timestamp(data, mid, imin)
        if ts is not None:
            if self.timeutil.is_in_window(ts):
                if pos <= imin or pos >= imax:
                    return pos
                (i, next_ts) = self._find_next_timestamp(data, mid, imax)
                if next_ts is not None:
                    if not self.timeutil.is_in_window(next_ts):
                        return pos
                    else:
                        return self.__find_end_in_win(data, pos, imax)
                else:
                    return pos
            else:
                if self.timeutil.is_before_window(ts):
                    return self.__find_end_in_win(data, pos+1, imax)
                else:
                    return self.__find_end_in_win(data, imin, pos-1)


    def __get_logs_in_win(self, data):
        # return line number range (start, end) for logs in time window
        nol = len(data)
        assert nol > 0
        start = end = None
        (fid, first_ts) = self._find_next_timestamp(data, 0, nol-1)
        (lid, last_ts) = self._find_prev_timestamp(data, nol-1, 0)
        #print "first_ts:%s, last_ts:%s, fid:%s, lid:%s" % (first_ts, last_ts, fid, lid)
        if first_ts is None:
            return(None, None)
        else:
            if self.timeutil.is_after_window(first_ts):
                return (None, None)
            # if all the logs in this file is in window
            if self.timeutil.is_in_window(first_ts):
                start = fid
            if last_ts is not None:
                if self.timeutil.is_in_window(last_ts):
                    end = lid
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
        for i in range(win[0], min(win[1]+NOTIMESTAMP_MAX, len(data))):
            res.append((i, data[i]))
        return res

    def parse(self, kwargs):
        window = kwargs.get('window')
        if window is not None:
            self.timeutil = TimeUtil(window[0], window[1])
            for log_file in self.log_files:
                data = open(log_file, 'r').readlines()
                if len(data) <= 0:
                    pass
                data = self.__prototype_time_parse(data)
                self._data_parse(data, log_file, kwargs)
        else:
            for log_file in self.log_files:
                data = open(log_file, 'r').readlines()
                self._data_parse(data, log_file, kwargs)  

if __name__ == '__main__':
    args = ArgParser().parse()
    ParserLoader(args.definition).run()
    if args.output is None: dis = True
    else: dis = False
    if args.fast:
        ee = FastLineErrorExtractor()
    else:
        ee = LineErrorExtractor()
    ee.run( path=args.path,
            window=args.window,
            output=args.output,
            display=dis)
