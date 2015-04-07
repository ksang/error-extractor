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

from err_extractor import LineErrorExtractor
from err_extractor import ArgParser
from err_extractor import ParserLoader

from lib.timestamp import TimeUtil

class LineErrorExtractorPrototype(LineErrorExtractor):

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
    LineErrorExtractorPrototype().run(  path=args.path,
                                        window=args.window,
                                        display=True)
