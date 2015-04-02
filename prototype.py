from err_extractor import LineErrorExtractor
from err_extractor import ArgParser
from err_extractor import ParserLoader

class LineErrorExtractorPrototype(LineErrorExtractor):

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
        for i in range(win[0], win[1]):
            ts = self.__line_timestamp(data[i])
            #print "ts: %s | line: %s" % (ts, line)
            if ts is not None:
                if self.timeutil.is_in_window(ts):
                    res.append((i, data[i]))
        return res

    def parse(self, kwargs):
        window = kwargs.get('window')
        if window is not None:
            self.timeutil = TimeUtil(window[0], window[1])
            for log_file in self.log_files:
                data = open(log_file, 'r').readlines()
                data = self.__prototype_time_parse(data)
                self.__data_parse(data, log_file, kwargs)
        else:
            for log_file in self.log_files:
                data = open(log_file, 'r').readlines()
                self.__data_parse(data, log_file, kwargs)  

if __name__ == '__main__':
    args = ArgParser().parse()
    ParserLoader(args.definition).run()
    LineErrorExtractorPrototype().run(args.path, window=args.window, display=True)
