import os
import urllib

#
# File mode, caches the page to a temp file
#
_file_mode = False

class CustomUserAgentOpener(urllib.FancyURLopener):
    version = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1 (KHTML, like Gecko) Ubuntu/11.04 Chromium/14.0.825.0 Chrome/14.0.825.0 Safari/535.1"
    #version = "Mozilla/5.0 (iPod; U; CPU like Mac OS X; en) AppleWebKit/420.1 (KHTML, like Gecko) Version/3.0 Mobile/3A101a Safari/419.3"

class BaseDataSource(object):

    def retrieve(self, url, filename = None):
        #FIXME: Urllib errors are not handled
        urllib._urlopener = CustomUserAgentOpener() #TODO: Can this be a common code?
        if _file_mode :
            if filename is None :
                raise Exception('"File Mode" requires a filename to work')
            raise Exception('"File Mode" is under implementation')
            #TODO: Make sure file doesn't exists
            headers = None
            filen = filename
            if not os.path.isfile( filename ) : # Assume is not a directory
                (filen, headers) = urllib.urlretrieve( url, filename )
            if headers :
                #print headers # Print HEADERS
                pass
            if filename != filen :
            print " UNEXPECTED Filename change:", filen
            #filename = rres[0]
            return open(filen, 'r')
        else :
            return urllib.urlopen( url )


