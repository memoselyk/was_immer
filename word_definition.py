
##import definition_wordreference_com

def get_definition(word) :
	print 'Getting definition of word : %s' % word
	print '-' * 20 , 'Wordreference.com'
	##definition_wordreference_com.get_definition( word )

def main() :
	word = raw_input('Enter word to search definition: ')
	get_definition(word)
	print '-' * 60
	print 'Done!'

if __name__ == "__main__" :
	main()

