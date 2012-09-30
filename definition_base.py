import logging
from logging.handlers import SocketHandler
import os
import socket
import urllib
import time

#
# This has become a common module, adding the network logger client here
rootLogger = logging.getLogger('')
rootLogger.setLevel(logging.DEBUG)

class SocketOrBasicHandler(SocketHandler):
    def __init__(self, host, port):
        SocketHandler.__init__(self, host, port)
        #
        # Attemt to create the socket and let flow up the exception
        self.sock = self.makeSocket()

try :
    socketHandler = SocketOrBasicHandler('localhost',
                    logging.handlers.DEFAULT_TCP_LOGGING_PORT)
    # don't bother with a formatter, since a socket handler sends the event as
    # an unformatted pickle
    rootLogger.addHandler(socketHandler)
except socket.error :
    print '\n', '#' * 60, '\n'
    print 'Could not create Socket Handler, falling back to basic config'
    print ' you may like to start the logging server located in network_logger'
    print '\n', '#' * 60, '\n'
    logging.basicConfig(format="%(message)s")

class CustomUserAgentOpener(urllib.FancyURLopener):
    logger = logging.getLogger('custom_UserAgent')
    version = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1 (KHTML, like Gecko) Ubuntu/11.04 Chromium/14.0.825.0 Chrome/14.0.825.0 Safari/535.1"
    #version = "Mozilla/5.0 (iPod; U; CPU like Mac OS X; en) AppleWebKit/420.1 (KHTML, like Gecko) Version/3.0 Mobile/3A101a Safari/419.3"

    def __init__(self, *args, **kwargs):
        urllib.FancyURLopener.__init__(self, *args, **kwargs)
        self.__next_download_after = 0.0

    def open(self, fullurl, data=None):
        self.logger.debug('Our very open was called')
        #
        # TODO: Change User-Agent 'dynamically'
        #
        self.logger.info('Using pre-set headers: %r' % self.addheaders)
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
            self.logger.debug('With Length %s' % size)
            control_speed = 2.5 * 1024    # Speed in B/s
            ideal_time = float(size) / control_speed
            actual_time = time_end - time_start
            actual_speed = float(size) / actual_time
            self.logger.info('Download at %.3f KB/s, took %.3f instead of %.3f, next after %.3f from now' % (actual_speed/1024, actual_time, ideal_time, (time_start + ideal_time) - time.time()))
            self.__next_download_after = time_start + ideal_time
        except Exception as reason:
            self.logger.warn('Dunno SIZE, %s' % reason)
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
    _file_mode = True
    _cache_dir = 'cache'    # Subfolder in os.curdir
    logger = logging.getLogger('def.base')

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
                self.logger.debug(headers) # Print HEADERS

            if filename != filen :
                self.logger.warn(" UNEXPECTED Filename change: '%s' to '%s'" % (filename, filen))

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

