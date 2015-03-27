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
        except Exception, err:
            sys.stderr.write("Invalid window, start: %s, end: %s, error: %s\n"
                                % (start_win, end_win, err))

    def is_in_window(self, timestamp):
        time = self.parse(timestamp)
        if time is not None:
            if self.start_win <= time and time <= self.end_win:
                return True
        return False

    def is_in_window_or_unsure(self, timestamp):
        time = self.parse(timestamp)
        if time is not None:
            if self.start_win > time or time > self.end_win:
                return False
        return True

    def parse(self, timestamp):
        try:
            res = self.parser.parse(timestamp, fuzzy=True)
        except ValueError, err:
            sys.stderr.write("Failed to parse timestamp: %s, error: %s\n" % (timestamp, err))
            return None
        else:
            return res