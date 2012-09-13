import os
import urllib

class CustomUserAgentOpener(urllib.FancyURLopener):
    version = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1 (KHTML, like Gecko) Ubuntu/11.04 Chromium/14.0.825.0 Chrome/14.0.825.0 Safari/535.1"
    #version = "Mozilla/5.0 (iPod; U; CPU like Mac OS X; en) AppleWebKit/420.1 (KHTML, like Gecko) Version/3.0 Mobile/3A101a Safari/419.3"

#
# Insert our customized UserAgent opener
#
urllib._urlopener = CustomUserAgentOpener()

class BaseDataSource(object):
    #
    # File mode, caches the page to a temp file
    #
    _file_mode = False

    def __init__(self, work_host=None, url_base=None):
        self._host = work_host
        self._url = url_base

    def _retrieve(self, word):
        url = self._url_for_word(word)
        #FIXME: Urllib errors are not handled
        if BaseDataSource._file_mode :
            raise Exception('"File Mode" is under implementation')
            filename = self._tempfilename(word)
            #TODO: Make sure file doesn't exists
            headers = None
            filen = filename
            if not os.path.isfile( filename ) : # Assume is not a directory
                (filen, headers) = urllib.urlretrieve( url, filename )
            if headers :
                print headers # Print HEADERS
                pass
            if filename != filen :
                print " UNEXPECTED Filename change:", filen
                #filename = rres[0]
            return open(filen, 'r')
        else :
            return urllib.urlopen( url )

    def _url_for_word(self, word):
        return self._url % (word)

    def _tempfilename(self, word):
        return '.'.join( ('_' + self._host, word, 'tmp') )

