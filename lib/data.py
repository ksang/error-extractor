# -*- coding: utf-8 -*-
import os,sys

class DataUtil:

    def __init__(self):
        self.textchars = bytearray([7,8,9,10,12,13,27]) + bytearray(range(0x20, 0x100))

    def __is_binary_string(self, string):
        return bool(string.translate(None, self.textchars))

    def _is_valid_text_file(self, filename):
        try:
            string = open(filename, 'rb').read(256)
        except Exception, err:
            sys.stderr.write("Open file error, filename: %s, error: %s\n" % (filename, err))
        else:
            if len(string) > 0 and not self.__is_binary_string(string):
                return True
        return False

    def get_text_files(self, path):
        file_list = []
        list_dirs = os.walk(os.path.normpath(path))
        for root, dirs, files in list_dirs:
            for f in files:
                filename = os.path.join(root, f)
                if self._is_valid_text_file(filename):
                    file_list.append(filename)
        return file_list
