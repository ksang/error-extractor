'''
HTML format generator
'''

class HTMLGen:
    'convert input to html syntax'
    def __init__(self):
        self.html_escape_table = {
                    "&": "&amp;",
                    '"': "&quot;",
                    "'": "&apos;",
                    ">": "&gt;",
                    "<": "&lt;",
                }
        self.tab = ' '*4

    def __check_supported_tag(self, data):
        '''
        check if text contains support html tag, if yes, return:
        (text, prefix tag, suffic tag)
        '''
        pre = suf = ''
        s = 0
        e = len(data)
        if data.find('<b>') > -1:
            pre += '<b>'
            suf = '</b>' + suf
            s = max(s, data.find('<b>') + 3)
            e -= 4
        if data.find('<pre>') > -1:
            pre += '<pre>'
            suf = '</pre>' + suf
            s = max(s, data.find('<pre>') + 5)
            e -= 6
        return (data[s:e], pre , suf)

    def __escape(self, data):
        (data, p, s) = self.__check_supported_tag(data)
        escaped = "".join(self.html_escape_table.get(c,c) for c in data)
        return p + escaped + s

    def escape(self, data):
        return "".join(self.html_escape_table.get(c,c) for c in data)        

    def unescape(self, data):
        data = data.replace("&lt;", "<")
        data = data.replace("&gt;", ">")
        data = data.replace("&#xD;", "")
        data = data.replace("&amp;", "&")
        return data

    def gen_table_from_list(self, data_list=None, escape=True):
        '''
        'data_list' is the input data, list elements are equal length tuples
        corresponding to each row of table.
        '''
        res = ''
        res += '<table>\n'
        for row in data_list:
            res += self.tab + '<tr>\n'
            for item in row:
                if escape:
                    res += self.tab*2 + '<td>' + self.__escape(str(item)) + '</td>\n'
                else:
                    res += self.tab*2 + '<td>' + str(item) + '</td>\n'
            res += self.tab + '</tr>\n'
        res += '</table>\n'
        return res

    def bold(self, str):
        return '<b>' + self.__escape(str) + '</b>'

    def raw(self, str):
        return '<pre>' + self.__escape(str) + '</pre>'

    def error(self, str):
        return '<b><p style="color:red">' + self.__escape(str) + '</p></b>'

    def success(self, str):
        return '<b><p style="color:blue>' + self.__escape(str) + '</p></b>'