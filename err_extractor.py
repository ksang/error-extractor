#!/usr/bin/python
import argparse

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
        return __parser.parse_args()

if __name__ == '__main__':
    args = ArgParser().parse()
    print args.path