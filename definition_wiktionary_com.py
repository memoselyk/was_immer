from definition_base import BaseDataSource
import logging
import itertools
import re       # For regex parsing

api_work_host = 'wiktionary.org_xml'
api_url_fmt = 'http://en.wiktionary.org/w/api.php?format=xml&action=query&titles=%s&prop=revisions&rvprop=content'

work_host = api_work_host   # Required by word_definition.py

html_work_host = 'wiktionary.org_html'
html_url_fmt = 'http://en.wiktionary.org/wiki/%s'

LOGGER = logging.getLogger('def.wiki')
#LOGGER.addFilter(logging.Filter('def.wiki.noun'))

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
        #
        # FIXME If the section is repeated serveral times (as in Wurm) the it would be nice if each section is put
        #    in a different dictionary with a prefix
        #
        target_dict = parsed_data
        for section in section_path :
            if section not in target_dict : target_dict[section] = {}
            target_dict = target_dict[section]
        if '_text' not in target_dict : target_dict['_text'] = []
        target_dict['_text'] += content_lines[:]
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
    return parse_german_data_for_anki(parsed_data, part_of_speech='noun')

def parse_german_verb_for_anki(parsed_data):
    return parse_german_data_for_anki(parsed_data, part_of_speech='verb')

def parse_german_data_for_anki(parsed_data, part_of_speech=None) :
    logGerman = logging.getLogger('wiki.german')

    # TODO: Log the related terms, derived terms to expand vocabulary

    #
    # A Second stage parsing should: query specific definitions (i.e. Noun, only), add Etymology info,
    # replace interlinks [[word]], templates {{de-noun|g=n}}, or numbered lists (#), remove quotes (#*)
    #

    word = parsed_data['_word']

    if 'German' not in parsed_data :
        # TODO: Should print in a file, or log it some where
        logGerman.critical('%s %s %s : NOT FOUND' % ('=' * 10, word, '=' * 10))
        print '\t', '?' * 10, word, '?' * 10, ': NOT FOUND'
        return False

    german_def = parsed_data['German']

    #
    # List sections for debugging purposes
    def output_section(data_dict, lvl=''):
        #for section in [ k for k in data_dict if k[0] != '_' ] :
        for section in data_dict :
            if isinstance(data_dict[section], list) :
                logGerman.info('%s%s : %s (%d)' % (lvl, section, type(data_dict[section]), len(data_dict[section])))
            else :
                logGerman.info('%s%s : %s' % (lvl, section, type(data_dict[section])))

            if section == 'Conjugation' :
                logGerman.debug('%r' % data_dict[section])

            if section[0] != '_' :
                output_section(data_dict[section], lvl + '-')
    output_section( german_def )

    posToFunc = {
        'verb' : _parse_german_verb_for_anki,
        'noun' : _parse_german_noun_for_anki,
    }

    dataParser = posToFunc.get(part_of_speech.lower())
    if dataParser is None :
        raise ValueError('Parser for POS=%s not found!' % part_of_speech)
    else :
        dataParser(german_def, word)

def _parse_german_verb_for_anki(german_def, word):
    logVerb = logging.getLogger('wiki.verb')

    # Find all Verbs in sub-levels
    verbsList = []
    def findAllVerbSubDicts(data_dict, path=()) :
        # Add the found Verb to the results
        if 'Verb' in data_dict :
            verbsList.append((path, data_dict['Verb'], ))
        # Process recursively sub-levels
        for k in data_dict :
            if k[0] == '_' or k == 'Verb' : continue    # Skip 'Verb' and '_text'
            findAllVerbSubDicts(data_dict[k], path + (k, ))
    findAllVerbSubDicts(german_def)

    if len(verbsList) == 0 :
        logVerb.error('Word:%s, is not a verb' % word) 
        print '\t', '>' * 10, word, '>' * 10, 'NOT Verb', '/'.join([s for s in german_def if s[0] != '_'])
        return

    logVerb.info('Word: %s, has %d verbs' % (word, len(verbsList), ))

    # Validate a couple of assumptions
    verbInBase = filter(lambda p : len(p[0]) == 0, verbsList)
    assert len(verbInBase) <= 1     # At most 1 verb in base
    if len(verbInBase) == 1 :
        assert len(verbsList) == 1     # If verbInBase, it should be the only one

    missingConjugation = False
    expectedConjTables = 0
    for from_path, verb_def in verbsList :
        from_name = '.'.join(from_path) if from_path else 'BASE'
        logVerb.info('Processing verb in "%s"' % from_name)

        # Validate that each Verb has conjugation (in XML)
        if 'Conjugation' not in verb_def :
            logVerb.warn('Word:%s, verb at %s does not have conjugation' % (word, from_name, ))
            print '\t', '@' * 10, word, '@' * 10, 'NO Conjugation for Verb at %s' % from_name
            missingConjugation = True
        else :
            expectedConjTables += 1

    # Process the definition from parsed_data TODO

    # Get the conjugation from html source

    # Prefer BeautifulSoup v4 over BeautifulSoup v3
    try :
        from bs4 import BeautifulSoup
    except ImportError :
        from BeautifulSoup import BeautifulSoup

    html_page = HtmlWiktionaryDataSource()._retrieve(word)
    allPage = html_page.read()
    html_page.close()


    logVerb.info('Fetched html, with %d bytes, and %d lines' % (len(allPage), len(allPage.splitlines()), ))
    #logVerb.debug("HTML: Has %d    id='Conjugation'      tags" % len(verbSoup.findAll(attrs={'id':'Conjugation'})))
    #logVerb.debug("HTML: Has %d class='inflection-table' tags" % len(verbSoup.findAll(attrs={'class':'inflection-table'})))

    allPage = allPage.decode('utf8')
    verbSoup = BeautifulSoup(allPage)

    # Find all Language headers, h2 with span of class mw-headline
    langH2Tags = filter(
            lambda t : t.findChild('span',attrs={'class':'mw-headline'}),
            verbSoup.findAll('h2'))
    logVerb.info("HTML: Has %d lang h2 header(s)" % len(langH2Tags))
    
    # Find the German's H2
    germanHead = None
    for num, h2Tag in enumerate(langH2Tags) :
        logVerb.debug('-- %02d, H2 Lang id=%s' % (num, h2Tag.findChild('span',attrs={'class':'mw-headline'})['id'], ))
        if h2Tag.findChild('span',attrs={'class':'mw-headline'})['id'] == 'German' :
            germanHead = h2Tag
    assert germanHead is not None

    # Find the next Language H2 tag
    germanIndex  = langH2Tags.index(germanHead)
    nextLangHead = langH2Tags[germanIndex+1] if germanIndex+1 < len(langH2Tags) else None
    logVerb.debug('German Lang head set to %d, next to %s' % (
            germanIndex,
            nextLangHead if nextLangHead is None else nextLangHead.findChild('span',attrs={'class':'mw-headline'})['id'],
        ))

    def findConjuationTablesAfterTag(startTag) :
        def getConjugationTable(navHead):
            if navHead.next != 'conjugation of ' :
                return None
            navContent = navHead.findNext('div', attrs={'class':'NavContent'})
            if navContent is None :
                return None
            return navContent.findChild('table')

        return filter(lambda n : n is not None,
                map(getConjugationTable, startTag.findAllNext('div', attrs={'class':'NavHead'})))

    # Find conjugations in German section
    conjugationsAfterDE = findConjuationTablesAfterTag(germanHead)
    if nextLangHead is None :
        germanConjugations = conjugationsAfterDE
        logVerb.info('Conjugation in German: %d, NO next lang' % len(germanConjugations))
    else :
        nextLangConjugations = findConjuationTablesAfterTag(nextLangHead)
        if len(nextLangConjugations) == 0 :
            germanConjugations = conjugationsAfterDE
        else :
            germanConjugations = conjugationsAfterDE[:-1*len(nextLangConjugations)]
        logVerb.info('Conjugation in German: %d; After DE %d, Next lang %d' % (
                len(germanConjugations), len(conjugationsAfterDE), len(nextLangConjugations)))

    logVerb.info('VerbList %d, expectedConjTables %d, GermanConjugations %d' % (
            len(verbsList), expectedConjTables, len(germanConjugations)))
    assert len(germanConjugations) == expectedConjTables

    if missingConjugation : # Stop processing this Word
        return

    # Helper functions to process the conjugation table
    def getTagContents(tag):
        """Get all direct children (contents) that are tag, not NavigableString
        """
        return filter(lambda c : not isinstance(c,basestring), tag.contents)

    def processConjugationCell(cell):
        """Return the extracted words from the given cell as a single string,
        each word is comma separated.
        """
        # Data words are wrapped in <a> tag, if the word is the same of the definition
        # it is in strong tag.
        childRelevantTags = [ t.text for t in cell.findChildren('a') + cell.findChildren('strong') ]
        if len(childRelevantTags) != 0 :
            return ', '.join(childRelevantTags)
        else : 
            # Fallback
            return cell.text

    def processConjugationRow(row) :
        """Return the extracted text from the processed conjugation rows as a list of String"""
        # Use the consistent formatting in the HTML, data cells are 'td', and headers are 'th'
        conjCells = row.findChildren('td')
        if len(conjCells) == 4 :
            # "Normal" conjugation cells
            pass
        elif len(conjCells) == 3 :
            # Imperative conjugation cells
            pass
        elif len(conjCells) == 1 :
            # Single word definition, such as infinitive, auxiliary, past participle, etc
            pass
        else :
            raise ValueError('Conjugation cells have %d items, expected 3 or 4' % len(conjCells))
        return filter(lambda x: len(x) != 0,   # Remove empty cells
                [processConjugationCell(c).encode('utf8') for c in conjCells])

    # Process each definition and its conjugation table, fist validate we have enough conjugation tables.
    assert len(germanConjugations) == len(verbsList)

    for num, verbPathDict, conjugationTable in zip(itertools.count(), verbsList, germanConjugations) :
        verbFromPath, verbDefinitionDict = verbPathDict

        tableRows = conjugationTable.findChildren('tr')
        if not len(tableRows) == 14 :
            logVerb.warn('Conjugation table%s has %d rows' % (
                    '' if len(germanConjugations) == 1 else (' (%d)' % (num+1)),
                    len(tableRows)))

        assert len(tableRows) == 14

        imperativeTense = {}
        presentTense    = {}
        preteriteTense  = {} 
        conjugationDict = {
                'imperative': imperativeTense,
                'present'   : presentTense,
                'preterite' : preteriteTense,
            }

        rowsIter = iter(tableRows)
        rowsIter.next() # Skip infinitive, since it is in TH not TD tags 
        (conjugationDict['PresentParticiple'], ) = processConjugationRow(rowsIter.next())  # present participle
        (conjugationDict['PastParticiple'], ) = processConjugationRow(rowsIter.next())  # past participle
        (conjugationDict['Auxiliary'], ) = processConjugationRow(rowsIter.next())  # auxiliary
        rowsIter.next() # Skip indicative, subjuntive headers
        presentTense['1P_S'], presentTense['1P_Pl'], _, _ = processConjugationRow(rowsIter.next())  # present 1st person, no subjunctive
        presentTense['2P_S'], presentTense['2P_Pl'], _, _ = processConjugationRow(rowsIter.next())  # present 2nd person, no subjunctive
        presentTense['3P_S'], presentTense['3P_Pl'], _, _ = processConjugationRow(rowsIter.next())  # present 3rd person, no subjunctive
        rowsIter.next() # Skip separator row
        preteriteTense['1P_S'], preteriteTense['1P_Pl'], _, _ = processConjugationRow(rowsIter.next())  # preterite 1st person, no subjunctive
        preteriteTense['2P_S'], preteriteTense['2P_Pl'], _, _ = processConjugationRow(rowsIter.next())  # preterite 2nd person, no subjunctive
        preteriteTense['3P_S'], preteriteTense['3P_Pl'], _, _ = processConjugationRow(rowsIter.next())  # preterite 3rd person, no subjunctive
        rowsIter.next() # Skip separator row
        imperativeTense['2P_S'], imperativeTense['2P_Pl'] = processConjugationRow(rowsIter.next())  # imperative

        #print '%r' % conjugationDict
        print 'Verb:', word, 'from', verbFromPath
        print 'Present perfect:', '(%s) %s' % (conjugationDict['Auxiliary'], conjugationDict['PastParticiple'], )
        print 'Present Tense:', '|'.join(presentTense['%dP_%s' % (p, n)]
                for n in ['S', 'Pl'] for p in [1,2,3] ) # First all Singular, then all Plural, with person from 1st to 3rd
        print 'Preterite Tense:', '|'.join(preteriteTense['%dP_%s' % (p, n)]
                for n in ['S', 'Pl'] for p in [1,2,3] ) # First all Singular, then all Plural, with person from 1st to 3rd
        print 'Imperative:', '|'.join([imperativeTense['2P_S'], imperativeTense['2P_Pl']])

        print 'Definition:'
        for line in verbDefinitionDict['_text'] :
            print ' -', line

        formatDefinitionAsHtml(verbDefinitionDict['_text'], logVerb, word)

def _parse_german_noun_for_anki(german_def, word):
    logNoun = logging.getLogger('wiki.noun')

    # FIXME: Some Nouns are the plural form of another word, log those instances somewhere

    # TODO
    #if 'Etymology' in german_def :
    #    print '\nEtymology:'
    #    print '\n'.join( german_def['Etymology']['_text'])
    #    print '-=-' * 15

    #
    # Find Noun definitions in sub-levels, as under Etimology 1/Etimology 2
    noun_def = []
    def merge_all_nouns(data_dict, path=[]) :
        if 'Noun' in data_dict :
            if len(path) > 0 : noun_def.append('\tFrom %s :' % '.'.join(path))
            noun_def.extend(data_dict['Noun']['_text'])
        for section in [ k for k in data_dict if k[0] != '_' ] : merge_all_nouns(data_dict[section], path + [section])
    merge_all_nouns(german_def)

    if not noun_def :
        logNoun.error('%s has only: %s' %
                (word, '/'.join([s for s in german_def if s[0] != '_'])) )
        print '\t', '>' * 10, word, '>' * 10, 'NOT Noun', '/'.join([s for s in german_def if s[0] != '_'])
    else :
        if not 'Noun' in german_def : logNoun.warn('%s, Noun in down-levels' % word)

        print '\t', '=' * 10, word, '=' * 10

        no_quot_noun = [ l for l in noun_def if not l.startswith('#*') ]

        logNoun.info('(%d) -> %d' % (len(noun_def), len(no_quot_noun)) )

        formatDefinitionAsHtml(noun_def, logNoun, word)


def formatDefinitionAsHtml(noun_def, logNoun, word) :
        listItemsCount = len(filter(lambda l : l.startswith('# '),
                noun_def))

        numbered_list_counter = 0
        for line_text in noun_def :
            if line_text.startswith('#*') : continue    # Skip quotations
            if line_text.startswith('#:') : continue    # Skip sample sentences
            if re.match('^-+$', line_text) is not None : continue    # Skip dash 'separators'

            if line_text.startswith('# ') :
                # FIXME: This omit the first element if more than one list is present
                numbered_list_counter += 1
                # Omit the number if there is only one element, and this is the first element
                # The second condition seems redundant, but in case the listItemsCount is
                # incorrectly calculated, the number will be omitted only in the first item
                if listItemsCount == 1 and numbered_list_counter == 1 :
                    line_text = line_text[2:]
                else :
                    line_text = ('%d.'%numbered_list_counter) + line_text[2:]
            else :
                numbered_list_counter = 0

            #
            while re.search('\[\[[^\]]+\]\]', line_text) :
                line_text = re.sub('\[\[([^\|\]]+\|)*([^\]]+)\]\]', r'\2', line_text)

            # Process Templates as in {{name|word|param=etwas}}
            template_finder = re.compile('{{([^}]+)}}')
            template_processor = Templates()
            last_found_end = 0
            while True :
                match = template_finder.search(line_text, last_found_end)
                if match is None : break

                logNoun.debug('Found template: -%s-' % match.group(1))

                template_args = match.group(1).split('|')
                name = template_args.pop(0)
                list_args = []
                kw_args = { } #'_ALL_' : match.group(1), '_DEF_': word }

                #
                # Special handler for de-noun parameters
                if name == 'de-noun' :
                    #
                    # Convert the first 4 positional arguments to the special named arguments in pos_name
                    pos_count = 0
                    pos_name  = ['g0', 'gen0', 'pl0', 'dim0']
                    kw_args['_word'] = word
                    for param in template_args :
                        if '=' not in param :
                            pos_count += 1
                            try :
                                kw_args[pos_name[pos_count-1]] = param
                            except :
                                list_args.append(param)
                        else :
                            kw_name, kw_value = param.split('=')    # Should fail if several '='
                            kw_args[kw_name] = kw_value
                            if kw_name.startswith('dim')   : pos_count = 4
                            elif kw_name.startswith('pl')  : pos_count = 3
                            elif kw_name.startswith('gen') : pos_count = 2
                            elif kw_name.startswith('g')   : pos_count = 1
                else :
                    for param in template_args :
                        if '=' not in param :
                            list_args.append(param)
                        else :
                            kw_name, kw_value = param.split('=')    # Should fail if several '='
                            kw_args[kw_name] = kw_value

                logNoun.debug('Would process template: %s with %r and %r' % (name, list_args, kw_args))

                name = name.replace('-', '_').replace(' ', '_')
                try :
                    replacement = getattr(template_processor, name)(logNoun, *list_args, **kw_args)
                except AttributeError :
                    logNoun.critical('Template processor "%s" not found!' % name)
                    replacement = match.group(0)#''

                line_text = line_text[0:match.start()] + replacement + line_text[match.end():]
                last_found_end = match.end()

            # Some lines have templates that generate other lines, and the final string is empty
            # Skip those lines
            if len(line_text) == 0 : continue

            print line_text

class Templates(object):

    def __getattr__(self, name):
        #
        # Special handler for contextual named attributes
        if name in [
                'anatomy', 'architecture', 'astronomy',
                'chess', 'Christianity', 'colloquial',
                'figuratively', 'finance', 'football', 'geography', 'geometry', 'grammar', 'graph theory',
                'heraldry', 'historical',
                'legal', 'linguistics',
                'meteorology', 'nautical', 'obsolete', 'poetry', 'printing', 'software', 'sports',
                'textiles'] :
            return lambda l, *a, **k : Templates.context(l, *([name]+list(a)), **k)
        elif name in [ 'de_verb', 'de_verb_irregular', 'de_verb_strong', 'de_verb_weak' ] :
            return Templates._SkipTemplate
        else :
            raise AttributeError

    @staticmethod
    def _SkipTemplate(log, *args, **kw_args) :
        return ''

    @staticmethod
    def context(log, *args, **kw_args):
        kw_args.pop('lang', '')
        args_list = list(args)
        if 'or' in args_list : args_list.remove('or')
        return ('<span style="font-style:italic;color:#808080;">'
                '&lt;%s&gt;</span>' % ', '.join(args_list + [ '%s=%s' % (k,kw_args[k]) for k in kw_args ]))

    @staticmethod
    def de_noun(log, *args, **kw_args):
        #
        # gender: g, g1, g2
        # genitive: gen*, -s, {{{1}}}
        # plural: pl*, -en, {{{2}}}
        #
        # Extracted categories
        prop_gender = []
        prop_plural = []
        prop_genitive = []
        prop_diminutive = []

        headword = kw_args.pop('_word')

        #
        # Process the numbered arguments
        for num, arg in enumerate(args) :
            type_ = 'UNDEF'
            print 'de_noun:[%d]%s=%s' % (num, type_, arg)

        gender_colors = {
            'm':'der|0000ff',
            'f':'die|ff3399',
            'n':'das|009900',
        }

        for arg_name in sorted(kw_args.keys()) :
            cat_list = None
            if arg_name.startswith('pl')    :   cat_list = prop_plural
            elif arg_name.startswith('dim') :   cat_list = prop_diminutive
            elif arg_name.startswith('gen') :   cat_list = prop_genitive
            elif arg_name.startswith('g')   :   cat_list = prop_gender

            if cat_list is not None : cat_list.append(kw_args[arg_name])
            else :
                log.error('Unknown category : %s' % arg_name)
                print 'de_noun:%s=%s' % (arg_name, kw_args[arg_name])
                continue

        #
        # Add genitive according to the template rule:
        # headword + s if it's masculine or neuter, and to the headword alone if it's feminine
        if not prop_genitive or '' in prop_genitive :
            if '' in prop_genitive : prop_genitive.remove('')
            default_genitive = '<not available>'
            if not prop_gender : default_genitive = '<no gender>'
            elif prop_gender[0] in ['m', 'n'] : default_genitive = '%ss*' % headword
            elif prop_gender[0] in ['f']      : default_genitive = '%s*' % headword
            else : default_genitive = '<unknown gender(%s)>' % prop_gender[0]
            prop_genitive.append(default_genitive)
        #
        # Modify plurals according to the template rule:
        # If left empty, it defaults to the headword + en,
        # It can also be set to - to indicate there is no plural form for this noun.
        if not prop_plural or '' in prop_plural :
            if '' in prop_plural : prop_plural.remove('')
            prop_plural.append('%sen' % headword)

        #
        # Clean-up diminutives
        while '' in prop_diminutive : prop_diminutive.remove('')

        #
        # Convert genders from m,f,n to der/die/das
        prop_gender = [ gender_colors.get(i,'*%s*' % i) for i in prop_gender ]

        print 'de_noun GENDER(s)     = %s' % ','.join(prop_gender)
        print 'de_noun PLURAL(s)     = %s' % ','.join(prop_plural)
        #print 'de_noun GENITIVE(s)   = %s' % ','.join(prop_genitive)   # Omit until it is used
        if prop_diminutive :
            print 'de_noun DIMINUTIVE(s) = %s' % ','.join(prop_diminutive)

        return ''

    @staticmethod
    def non_gloss_definition(log, *args, **kw_args):
        args_list = list(args)
        return '/'.join('<span style="font-style:italic;">'
                '%s</span>' % arg for arg in (args_list + [ '<b>%s</b>=%s' % (k,kw_args[k]) for k in kw_args ]) )

    @staticmethod
    def gloss(log, *args, **kw_args):
        return ' '.join(
                ['(%s)' % t for t in args] + 
                ['gloss:%s="%s"' % (k, kw_args[k]) for k in kw_args ])

    @staticmethod
    def term(log, *args, **kw_args):
        interlink   = args[0]
        disp_text   = args[1] if len(args) >= 2 else ''
        translation = args[2] if len(args) >= 3 else ''

        if disp_text == '' : disp_text = interlink
        if translation == '' :
            return disp_text
        else :
            return '%s ("%s")' % (disp_text, translation)

    @staticmethod
    def qualifier(log, *args, **kw_args):
        return ' '.join(
                ['(<i>%s</i>)' % t for t in args] + 
                ['qualifier:%s="%s"' % (k, kw_args[k]) for k in kw_args ])
