from definition_base import BaseDataSource
import logging

api_work_host = 'wiktionary.org_xml'
api_url_fmt = 'http://en.wiktionary.org/w/api.php?format=xml&action=query&titles=%s&prop=revisions&rvprop=content'

work_host = api_work_host   # Required by word_definition.py

html_work_host = 'wiktionary.org_html'
html_url_fmt = 'http://en.wiktionary.org/wiki/%s'

LOGGER = logging.getLogger('def.wiki')

class WiktionaryDataSource(BaseDataSource):
    def __init__(self):
        BaseDataSource.__init__(self, api_work_host, api_url_fmt)

class HtmlWiktionaryDataSource(BaseDataSource):
    def __init__(self):
        BaseDataSource.__init__(self, html_work_host, html_url_fmt)

def get_definition(word, on_browser=False):
    page = WiktionaryDataSource()._retrieve(word)
    for line in page :
        LOGGER.critical("->(%s)%s" % (type(line), line[:-1].decode("utf-8")))
    page.close()


    if on_browser :
        import webbrowser
        html_page = HtmlWiktionaryDataSource()._retrieve(word)
        cache_url = html_page.name
        html_page.close()
        webbrowser.open_new_tab(cache_url)
