'''
MarkDown format generator for Quasar Parsers
'''

class MarkDown:

    'convert raw text to markdown syntax'

    def __init__(self):
        self.escape_table = {"\\": "\\\\",  "`": "\`", 
                             "*": "\*",     "_": "\_",
                             "{": "\{",     "}": "\}", 
                             "[": "\[",     "]": "\]",
                             "(": "\(",     ")": "\)",
                             "#": "\#",     "+": "\+",
                             "-": "\-",     ".": "\.",
                             "|": "\|"
                             }

    def __escape(self, data):
        return "".join(self.escape_table.get(c,c) for c in data)

    def __convert_lines(self, text='', prefix='', suffix='', olist=False):
        if type(text) is str:
            if olist:
                return '1.   ' + self.__escape(text)
            else:
                return prefix + self.__escape(text) + suffix
        elif type(text) is list:
            for idx, t in enumerate(text):
                if olist:
                    nt = str(idx+1) + '.   ' + self.__escape(t)
                else:
                    nt = prefix + self.__escape(t) + suffix
                text[idx] = nt
            return text
        return ''

    def text(self, text):
        return self.__convert_lines(text)

    def error(self, text):
        return self.__convert_lines(text)        

    def title(self, text):
        return self.__convert_lines(text, '##')
    
    def subtitle(self, text):
        return self.__convert_lines(text, '###')

    def ssubtitle(self, text):
        return self.__convert_lines(text, '####')

    def bold(self, text):
        return self.__convert_lines(text, '**', '**')

    def line_breaker(self, count=1):
        if count > 1:
            ret = []
            for i in range(0,count):
                ret.append("-------------")
            return ret
        return "-------------"

    def reference(self, text):
        return self.__convert_lines(text, '>')

    def ordered_list(self, data):
        return self.__convert_lines(data, olist=True)

    def unordered_list(self, data):
        return self.__convert_lines(data, '-   ')