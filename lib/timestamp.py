'''
Timestamp util for parsing logs
'''



import datetime,sys
from dateutil.parser import parser

class TimeUtil:
    def __init__(self, start_win=None, end_win=None):
        self.parser = parser()
        try:
            self.start_win = datetime.datetime.fromtimestamp(start_win)
            self.end_win = datetime.datetime.fromtimestamp(end_win)
        except TypeError:
            try:
                self.start_win = self.parser.parse(start_win, fuzzy=True)
                self.end_win = self.parser.parse(end_win, fuzzy=True)
            except Exception, err:
                sys.stderr.write("Invalid window, start: %s, end: %s, error: %s\n"
                                    % (start_win, end_win, err))
        if  self.start_win > self.end_win:
            sys.stderr.write("Bad window, start: %s, end: %s, start > end\n"
                                % (start_win, end_win))

    def is_before_window(self, timestamp):
        if type(timestamp) is datetime.datetime:
            time = timestamp
        else:
            time = self.parse(timestamp)
        if time is not None:
            if self.start_win > time:
                return True
        return False

    def is_after_window(self, timestamp):
        if type(timestamp) is datetime.datetime:
            time = timestamp
        else:
            time = self.parse(timestamp)
        if time is not None:
            if self.end_win < time:
                return True
        return False

    def is_in_window(self, timestamp):
        if type(timestamp) is datetime.datetime:
            time = timestamp
        else:
            time = self.parse(timestamp)
        if time is not None:
            try:
                if self.start_win <= time and time <= self.end_win:
                    return True
            except Exception:
                return False
        return False

    def is_in_window_or_unsure(self, timestamp):
        if type(timestamp) is datetime.datetime:
            time = timestamp
        else:
            time = self.parse(timestamp)
        time = self.parse(timestamp)
        if time is not None:
            try:
                if self.start_win > time or time > self.end_win:
                    return False
            except Exception:
                return True
        return True

    def is_timestamp(self, timestamp):
        try:
            res = self.parser.parse(timestamp)
        except ValueError, err:
            return False
        return True

    def parse(self, timestamp):
        try:
            res = self.parser.parse(timestamp)
        except ValueError, err:
            return None
        else:
            return res