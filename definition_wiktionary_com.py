from definition_base import BaseDataSource
import logging
import re       # For regex parsing

api_work_host = 'wiktionary.org_xml'
api_url_fmt = 'http://en.wiktionary.org/w/api.php?format=xml&action=query&titles=%s&prop=revisions&rvprop=content'

work_host = api_work_host   # Required by word_definition.py

html_work_host = 'wiktionary.org_html'
html_url_fmt = 'http://en.wiktionary.org/wiki/%s'

LOGGER = logging.getLogger('def.wiki')
LOGGER.addFilter(logging.Filter('def.wiki.noun'))

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

    parsed_data = {'_word' : word}    # Output dictionary
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

        # FIXME: Some lines contain escaped HTML entities, replace them
        #        Following approach seems broken b/c of non-ascii chars
        # import HTMLParser
        # h = HTMLParser.HTMLParser()
        # line = h.unescape(line)

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

def parse_german_noun_for_anki(parsed_data):
    logNoun = logging.getLogger('def.wiki.noun')

    # FIXME: Some Nouns are the plural form of another word, log those instances somewhere

    # TODO: Log the related terms, derived terms to expand vocabulary

    #
    # A Second stage parsing should: query specific definitions (i.e. Noun, only), add Etymology info,
    # replace interlinks [[word]], templates {{de-noun|g=n}}, or numbered lists (#), remove quotes (#*)
    #

    word = parsed_data['_word']

    if 'German' not in parsed_data :
        # TODO: Should print in a file, or log it some where
        logNoun.critical('%s %s %s : NOT FOUND' % ('=' * 10, word, '=' * 10))
        return False

    german_def = parsed_data['German']

    #
    # List sections for debugging purposes
    def output_section(data_dict, lvl=''):
        for section in [ k for k in data_dict if k[0] != '_' ] :
            logNoun.debug(lvl + section)
            output_section(data_dict[section], lvl + '-')
    #output_section( german_def )

    # TODO
    #if 'Etymology' in german_def :
    #    print '\nEtymology:'
    #    print '\n'.join( german_def['Etymology']['_text'])
    #    print '-=-' * 15

    template_finder = re.compile('{{([^}]+)}}')
    if not 'Noun' in german_def :
        logNoun.error('%s has only: %s' %
                (word, '/'.join([s for s in german_def if s[0] != '_'])) )
    else :
        print '\t', '=' * 10, word, '=' * 10

        noun_def = german_def['Noun']['_text']
        no_quot_noun = [ l for l in noun_def if not l.startswith('#*') ]

        logNoun.info('(%d) -> %d' % (len(noun_def), len(no_quot_noun)) )

        for line_text in noun_def :
            if line_text.startswith('#*') : continue    # Skip quotations
            if line_text.startswith('#:') : continue    # Skip sample sentences
            if re.match('^-+$', line_text) is not None : continue    # Skip dash 'separators'

            # Process Templates as in {{name|word|param=etwas}}
            template_processor = Templates()
            while True :
                match = template_finder.search(line_text)
                if match is None : break

                logNoun.debug('Found template: -%s-' % match.group(1))

                template_args = match.group(1).split('|')
                name = template_args.pop(0)
                list_args = []
                kw_args = {}
                for param in template_args :
                    if '=' not in param :
                        list_args.append(param)
                    else :
                        kw_name, kw_value = param.split('=')    # Should fail if several '='
                        kw_args[kw_name] = kw_value

                logNoun.debug('Would process template: %s with %r and %r' % (name, list_args, kw_args))

                try :
                    replacement = getattr(template_processor, name.replace('-', '_'))(*list_args, **kw_args)
                except AttributeError :
                    logNoun.error('Template processor "%s" not found!' % name)
                    replacement = ''

                line_text = line_text[0:match.start()] + replacement + line_text[match.end():]

            if len(line_text) == 0 : continue   # de-noun template if parsed_head : skip

            print line_text

class Templates(object):
    @staticmethod
    def de_noun(*args, **kw_args):
        #
        # gender: g, g1, g2
        # genitive: gen*, -s, {{{1}}}
        # plural: pl*, -en, {{{2}}}
        #
        print 'test_passed %d %-30r %s' % (len(args), sorted(kw_args.keys()), args)
        return ''

    @staticmethod
    def term(*args, **kw_args):
        interlink   = args[0]
        disp_text   = args[1] if len(args) >= 2 else ''
        translation = args[2] if len(args) >= 3 else ''

        if disp_text == '' : disp_text = interlink
        if translation == '' :
            return disp_text
        else :
            return '%s ("%s")' % (disp_text, translation)
