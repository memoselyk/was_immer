import logging

class AnsiColorFormatter(logging.Formatter):

    def color(self, level=None):
        codes = {\
            None:       (0,   0),
            'DEBUG':    (0,  34),
            'INFO':     (0,  32),
            'WARNING':  (1,  33),
            'ERROR':    (1,  31),
            'CRITICAL': (1, 101),
            }
        return (chr(27)+'[%d;%dm') % codes[level]

    def format(self, record):
        retval = logging.Formatter.format(self, record)
        return self.color(record.levelname) + retval + self.color()
