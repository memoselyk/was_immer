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
    _cache_dir = 'cache'    # Subfolder in os.curdir

    def __init__(self, work_host=None, url_base=None):
        self._host = work_host
        self._url = url_base

    def _retrieve(self, word):
        url = self._url_for_word(word)
        #FIXME: Urllib errors are not handled
        if BaseDataSource._file_mode :

            self._check_cache_dir()
            filename = os.path.join(self._cache_dir, self._tempfilename(word))

            headers = None
            filen = filename

            if not os.path.isfile( filename ) : # Assume is not a directory
                (filen, headers) = urllib.urlretrieve( url, filename )

            if headers :
                print headers # Print HEADERS

            if filename != filen :
                print " UNEXPECTED Filename change: '%s' to '%s'" % (filename, filen)

            return open(filen, 'r')
        else :
            return urllib.urlopen( url )

    def _check_cache_dir(self):
        """Verifies that cache dir is an existing directory or creates it
        """
        if not os.path.exists(self._cache_dir) :
            os.mkdir(self._cache_dir)
            return

        if not os.path.isdir(self._cache_dir):
            raise Exception('Path %s exists but is not a directory' % self._cache_dir)

    def _url_for_word(self, word):
        return self._url % (word)

    def _tempfilename(self, word):
        try :
            #
            # Assume word comes UTF-8 encoded , decode it
            word = word.decode('utf8')
        except :
            pass
        return '.'.join( ('_' + self._host, word.encode('ascii', 'xmlcharrefreplace').replace('&#', ';') , 'tmp') )

