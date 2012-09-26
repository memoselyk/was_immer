from definition_base import BaseDataSource
import logging

work_host = 'wiktionary.org'
url_fmt_str = 'http://en.wiktionary.org/w/api.php?format=xml&action=query&titles=%s&prop=revisions&rvprop=content'
url_browser = 'http://en.wiktionary.org/wiki/%s'

LOGGER = logging.getLogger('def.wiki')

class WiktionaryDataSource(BaseDataSource):
    def __init__(self):
        BaseDataSource.__init__(self, work_host, url_fmt_str)

def get_definition(word, on_browser=False):
    page = WiktionaryDataSource()._retrieve(word)
    for line in page :
        LOGGER.critical("->(%s)%s" % (type(line), line[:-1].decode("utf-8")))
    page.close()
    if on_browser :
        import webbrowser
        webbrowser.open_new_tab(url_browser % word)
