import os
import urllib
import definition_wordreference_com

_file_mode = False

class CustomUserAgentOpener(urllib.FancyURLopener):
	version = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1 (KHTML, like Gecko) Ubuntu/11.04 Chromium/14.0.825.0 Chrome/14.0.825.0 Safari/535.1"
#	version = "Mozilla/5.0 (iPod; U; CPU like Mac OS X; en) AppleWebKit/420.1 (KHTML, like Gecko) Version/3.0 Mobile/3A101a Safari/419.3"

#FIXME: Urllib errors are not handled
def retrieve( url, filename ) :
	urllib._urlopener = CustomUserAgentOpener() #TODO: Can this be a common code?
	if _file_mode :
		#TODO: Make sure file doesn't exists
		headers = None
		filen = filename
		if not os.path.isfile( filename ) : # Assume is not a directory
			(filen, headers) = urllib.urlretrieve( url, filename )
		if headers : 
			pass
			#print rres[1] # Print HEADERS
		if filename != filen : 
			print " UNEXPECTED Filename change:", filen
			#filename = rres[0]
		return open(filen, 'r')
	else :
		return urllib.urlopen( url )

def get_definition(word) :
	print 'Getting definition of word : %s' % word
	print '-' * 20 , 'Wordreference.com'
	definition_wordreference_com.get_definition( word )

def main() :
	word = raw_input('Enter word to search definition: ')
	get_definition(word)
	print '-' * 60
	print 'Done!'

if __name__ == "__main__" :
	main()

