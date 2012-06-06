from definition_base import BaseDataSource

work_host = 'wiktionary.org'
url_fmt_str = 'http://en.wiktionary.org/w/api.php?format=xml&action=query&titles=%s&prop=revisions&rvprop=content'

class WiktionaryDataSource(BaseDataSource):
    def __init__(self):
        BaseDataSource.__init__(self, work_host, url_fmt_str)


def get_definition(word):
    page = WiktionaryDataSource()._retrieve(word)
    for line in page :
        print "->(%s)%s" % (type(line), line[:-1].decode("utf-8")) 
    page.close()
