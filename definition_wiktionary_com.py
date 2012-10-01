from definition_base import BaseDataSource
import logging
import re       # For regex parsing

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

    #
    # Fist parsing stage, would parse the structure of the document based on the section (==German==) lines
    #
    xml_finder = re.compile('(<[^>]+>)+')   # Should find xml portion
    section_finder = re.compile('^(?P<depth>=+)(?P<name>[^=]+)(?P=depth)$')
    inter_links = re.compile('^\[\[[^\]]+\]\]$')

    parsed_data = {}    # Output dictionary
    content_lines = []  # Temporary buffer for the content
    section_path = []   # Path of sections being parsed

    def _flush_lines() :
        target_dict = parsed_data
        for section in section_path :
            if section not in target_dict : target_dict[section] = {}
            target_dict = target_dict[section]
        target_dict['_text'] = content_lines[:]
        LOGGER.debug(' -> '.join(section_path) + ' (%d)' % len(content_lines))
        for i in range(len(content_lines)) : content_lines.pop()    # Clear content lines

    for line in page :
        line = line.strip() # Remove new line at the end

        xml_result = xml_finder.search(line)
        if xml_result :
            xml_portion = xml_result.group()
            #
            # True if the word is not found, this can be safely excecuted on the tail portion of the XML
            is_missing = re.search('<page(?= )(?: [^=]+="[^"]*")* missing=""', xml_portion) is not None
            parsed_data['_missing'] = is_missing
            LOGGER.debug('is_missing : %s' % is_missing)
            #
            # Strip the xml portion of the line
            line = line[0:xml_result.start()] + line[xml_result.end():]

        if inter_links.match(line) :
            # Skip this lines like [[Category:de:blah]] or [[de:blah]] since this links are displayed outside of content
            if ':' not in line : LOGGER.warn("Skipped line with link :'%s'" % line)
            continue

        if len(line) == 0 : continue # Skip empty lines

        section_match = section_finder.match(line)
        if section_match :
            _flush_lines()# Flush lines into previous path

            section_level = len(section_match.group('depth')) - 2
            section_name = section_match.group('name')

            section_path = section_path[:section_level] + [section_name]
            continue

        content_lines.append(line)

    _flush_lines()  # Add the last parsed section

    page.close()

    if on_browser :
        import webbrowser
        html_page = HtmlWiktionaryDataSource()._retrieve(word)
        cache_url = html_page.name
        html_page.close()
        webbrowser.open_new_tab(cache_url)

    return parsed_data
