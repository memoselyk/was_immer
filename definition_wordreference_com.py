import word_definition
import urlparse
from HTMLParser import HTMLParser
import sys

printf = sys.stdout.write

work_host = 'wordreference.com'
url_prefix = 'http://www.wordreference.com/definition/'

class WordreferenceParser(HTMLParser):

	inSense = False
	senseDepth = 0
	senseGpDepth = 0
	psg_c = 0 # psg_counter
	nextData = None

	def handle_starttag(self, tag, attrs):
		if tag == 'div' :
			if ('class', 'sense') in attrs: 
				self.inSense = True
		if self.inSense :
			self.senseDepth += 1
			#print 'Processing : %s' % self.get_starttag_text()
		if tag == 'span' :
			if ('class', 'hw') in attrs: self.nextData = 'hw'
			if ('class', 'ph') in attrs: self.nextData = 'ph'
			if ('class', 'ps') in attrs: self.nextData = 'ps'
			if ('class', 'psg') in attrs: 
				self.psg_c = 1
				self.nextData = 'psg'
			elif self.psg_c > 0 : self.psg_c += 1
			if ('class', 'senseGP') in attrs: self.senseGpDepth = 1
			elif self.senseGpDepth > 0 : self.senseGpDepth += 1
			#print 'SPAN (senseGP depth):', self.senseGpDepth

	def handle_endtag(self, tag):
		if self.inSense :
			self.senseDepth -= 1
			if self.senseDepth == 0 : self.inSense = False
			if tag == 'span' and self.senseGpDepth > 0 :
				self.senseGpDepth -= 1
				if self.senseGpDepth == 0 : printf('\n')
			if tag == 'span' and self.psg_c > 0 :
				self.psg_c -= 1
				if self.psg_c == 0 : printf('\n')
			if tag == 'li' :
				printf('\n')

	def handle_data(self, data) :
		if self.inSense :
			if self.nextData is None :
				if self.senseGpDepth > 0 : printf(data)
				else : pass #print 'SNSE :', repr(data)
			elif self.nextData == 'ps' :
				print '\n -> %s' % data,
		else :
			if self.nextData is None :
				pass #print 'Data :', repr(data)
			elif self.nextData == 'hw' :
				print 'Definition of %s' % data
		self.nextData = None

	def handle_charref(self, name) :
		pass
#		self.job.description += chr(int(name))

	def handle_entityref(self, name) :
		pass
#		if self.inDesc :
#			if name == 'bull' : self.job.description += '  - ' 
#			elif name == 'amp' : self.job.description += '&' 
#			elif name == 'nbsp' : self.job.description += ' ' 
#			elif name == 'quot' : self.job.description += '"'
#			elif name == 'rdquo' : self.job.description += '"'
#			elif name == 'ldquo' : self.job.description += '"'
#			elif name == 'ndash' : self.job.description += '-'
#			elif name == 'mdash' : self.job.description += '--'
#			elif name == 'hellip' : self.job.description += '...' 
#			elif name == 'rsquo' : self.job.description += "'"
#			elif name == 'lsquo' : self.job.description += "'"
#			else : print 'EntityRef :', name, 'not processed'

	def feed(self, line) :
		if 'clickable' in line :
			HTMLParser.feed(self, line)

def get_definition(word) :
	wurl = url_prefix + word
	tempf = '.'.join( ('_' + word, work_host, 'tmp') )
#	rres = None # url Retrieve RESponse
#	if not os.path.isfile( tempf ) : # Assume is not a directory
#		rres = word_definition.retrieve( wurl, tempf )
#
#	if not rres is None :
#		if rres[1] : 
#			pass
#			#print rres[1] # Print HEADERS
#		if tempf != rres[0] : 
#			print " UNEXPECTED Filename change:", rres[0]
#			tempf = rres[0]
#	page = open( tempf, 'r')
	# Parse and Extract info, from file
	page = word_definition.retrieve( wurl, tempf )
	pars = WordreferenceParser()
	for line in page :
		pars.feed( line )
	# Close
	pars.close()
	page.close()

def main() :
	if len(sys.argv) < 1 :
		print 'Missing arguments! (word-to-fetch)'
		exit( -2 )
	word = sys.argv[1]
	print '-' * 60
	get_definition(word)
	print '-' * 60
	print 'Done!'

if __name__ == "__main__" :
	main()

