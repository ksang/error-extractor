#!/usr/bin/python
from lib.timestamp import TimeUtil
from err_extractor import LINE_OPERATOR
from err_extractor import SECTION_STARTER
from err_extractor import LINE_FILTER
from err_extractor import TIMESTAMP_FORMATTER
from err_extractor import ParserLoader
from err_extractor import LineErrorExtractor


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

        return __parser.parse_args()

class ParserTester:

    def _print_dict(self, data):
        for key in data.keys():
            print "%s: %s" % (key, data[key])

    def print_parser_content(self):
        print 'LINE_OPERATOR:'
        self._print_dict(LINE_OPERATOR)
        print 'SECTION_STARTER:'
        self._print_dict(SECTION_STARTER)
        print 'LINE_FILTER:'
        self._print_dict(LINE_FILTER)
        print 'TIMESTAMP_FORMATTER:'
        self._print_dict(TIMESTAMP_FORMATTER)

    def print_ts_parse_result(self, line, ts, pid):
        print "Row Log: %s" % line.strip()
        print "Parsed timestamp: %s, ts_parser_id: %s" %(ts, pid)

    def _data_parse(self, data, fn, kwargs):
        self.lee._data_parse(data, fn, kwargs)

    def _time_parse(self, data, filename):
        print "%s:" % filename
        for line in data:
            if len(line) <= 8:
                continue
            ts = self.lee._line_timestamp(line)
            pid = self.lee._line_timestamp(line, True)
            self.print_ts_parse_result(line, ts, pid)

    def parse(self, kwargs):
        win = kwargs.get("window")
        print "\nStart Parsing:\n"
        if win is not None:
            self.lee.timeutil = TimeUtil(win[0], win[1])
            self.lee.timeutil.print_window()
            for filename in self.lee.log_files:
                data = open(filename, 'r').readlines()
                data = self._time_parse(data, filename)
        else:
            for log_file in self.lee.log_files:
                data = open(log_file, 'r').readlines()
                self._data_parse(data, log_file, kwargs)

    def run(self, **kwargs):
        self.print_parser_content()
        self.lee = LineErrorExtractor()
        path = kwargs.get("path")
        self.lee._get_log_files(path)
        self.parse(kwargs)

if __name__ == '__main__':
    args = ArgParser().parse()
    ParserLoader(args.definition).run()
    ParserTester().run( path=args.path,
                        window=args.window,
                        display=True)
