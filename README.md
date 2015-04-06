Error Extractor
---------------

A tool targeted to extract error messages from logs within a location in any format.
User can specify time window for the error messages. 

####Requirements:
    dateutil == 1.5

####Usage:
    err_extractor.py [-h] -p PATH [-d DEFINITION] [-w START_TIME END_TIME]
                            [-o OUTPUT]

            Error Extractor, get error messages from log files.

    optional arguments:
      -h, --help            show this help message and exit
      -p PATH, --path PATH  Log file root folder location.
      -d DEFINITION, --definition DEFINITION
                            Parser definition file, default is 'parsers.xml'
      -w START_TIME END_TIME, --window START_TIME END_TIME
                            Start time and end time in YYYY-MM-DD HH:MM:SS
      -o OUTPUT, --output OUTPUT
                            Save report to a html file, provide filename.