#!/usr/bin/env python
import definition_wiktionary_com as definition_provider
import sys

def get_definition(word) :
	print 'Getting definition of word : %s' % word
	print '-' * 20 , definition_provider.work_host
	definition_provider.get_definition( word )

def main() :
	#
	# With no arguments, prompt the user for the word to search
	if len(sys.argv) == 1 :
		word = raw_input('Enter word to search definition: ')
		get_definition(word)
		print '-' * 60
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
				print type(word), WiktionaryDataSource()._tempfilename(word)
	else :
		print 'Too many arguments, punkt!'
	print 'Done!'

if __name__ == "__main__" :
	main()

