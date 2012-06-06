
import definition_wiktionary_com as definition_provider

def get_definition(word) :
	print 'Getting definition of word : %s' % word
	print '-' * 20 , definition_provider.work_host
	definition_provider.get_definition( word )

def main() :
	word = raw_input('Enter word to search definition: ')
	get_definition(word)
	print '-' * 60
	print 'Done!'

if __name__ == "__main__" :
	main()

