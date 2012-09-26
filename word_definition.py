#!/usr/bin/env python
import logging
import definition_wiktionary_com as definition_provider
import sys
import types

LOGGER = logging.getLogger('MAIN')

def get_definition(word) :
	if type(word) is types.UnicodeType :
		word = word.encode('utf8')
	LOGGER.info('Getting definition of word : %r' % word)
	LOGGER.warn('%s %s' %('-' * 20 , definition_provider.work_host))
	definition_provider.get_definition( word )

def main() :
	#
	# With no arguments, prompt the user for the word to search
	if len(sys.argv) == 1 :
		word = raw_input('Enter word to search definition: ')
		get_definition(word)
		LOGGER.info('-' * 60)
	#
	# Support an optional argument (a file with a list of Words to search)
	elif len(sys.argv) == 2 :
		import codecs
		words_file = sys.argv[1]
		with codecs.open(words_file, 'r', 'utf-8') as f :
			#
			# Assume one word per line
			#
			for line in f :
				word = line.strip()
				from definition_wiktionary_com import WiktionaryDataSource
				LOGGER.debug('%s %s' % (type(word), WiktionaryDataSource()._tempfilename(word)))
				get_definition(word)
				LOGGER.info('-' * 60)
	else :
		LOGGER.error('Too many arguments, punkt!')
	LOGGER.warn('Done!')

if __name__ == "__main__" :
	main()

