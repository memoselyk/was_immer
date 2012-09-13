import os
import urllib
import time

class CustomUserAgentOpener(urllib.FancyURLopener):
    version = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1 (KHTML, like Gecko) Ubuntu/11.04 Chromium/14.0.825.0 Chrome/14.0.825.0 Safari/535.1"
    #version = "Mozilla/5.0 (iPod; U; CPU like Mac OS X; en) AppleWebKit/420.1 (KHTML, like Gecko) Version/3.0 Mobile/3A101a Safari/419.3"

    def __init__(self, *args, **kwargs):
        urllib.FancyURLopener.__init__(self, *args, **kwargs)
        self.__next_download_after = 0.0

    def open(self, fullurl, data=None):
        print 'Our very open was called'
        #
        # TODO: Change User-Agent 'dynamically'
        #
        print 'Using pre-set headers: %r' % self.addheaders
        time_start = time.time()
        if time_start < self.__next_download_after :
            #
            # Wait enough time before the next download and ...
            time.sleep(self.__next_download_after - time_start)
            #
            # ... recalculate the start time
            time_start = time.time()
        ret = urllib.FancyURLopener.open(self, fullurl, data)
        time_end = time.time()
        headers = ret.info()
        try :
            size = int(headers["Content-Length"]) + 65 # Content + (arbitrary) size of headers
            print 'With Length ', size
            control_speed = 2.5 * 1024    # Speed in B/s
            ideal_time = float(size) / control_speed
            actual_time = time_end - time_start
            actual_speed = float(size) / actual_time
            print 'Download at %.3f KB/s, took %.3f instead of %.3f, next after %.3f from now' % (actual_speed/1024, actual_time, ideal_time, (time_start + ideal_time) - time.time())
            self.__next_download_after = time_start + ideal_time
        except Exception as reason:
            print 'Dunno SIZE, ', reason
            #
            # If cannot determine the ideal download time, then assume a 500 ms wait
            self.__next_download_after = time_end + 0.5
        return ret

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

