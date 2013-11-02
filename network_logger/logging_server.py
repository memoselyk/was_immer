import cPickle
import logging
import logging.handlers
import SocketServer
import struct

from color_formatter import AnsiColorFormatter

class LogRecordStreamHandler(SocketServer.StreamRequestHandler):
    """Handler for a streaming logging request.

    This basically logs the record using whatever logging policy is
    configured locally.
    """

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while 1:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack(">L", chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.unPickle(chunk)
            record = logging.makeLogRecord(obj)
            self.handleLogRecord(record)

    def unPickle(self, data):
        return cPickle.loads(data)

    def handleLogRecord(self, record):
        # if a name is specified, we use the named logger rather than the one
        # implied by the record.
        if self.server.logname is not None:
            name = self.server.logname
        else:
            name = record.name
        logger = logging.getLogger(name)
        # N.B. EVERY record gets logged. This is because Logger.handle
        # is normally called AFTER logger-level filtering. If you want
        # to do filtering, do it at the client end to save wasting
        # cycles and network bandwidth!
        logger.handle(record)

class LogRecordSocketReceiver(SocketServer.ThreadingTCPServer):
    """simple TCP socket-based logging receiver suitable for testing.
    """

    allow_reuse_address = True

    def __init__(self, host='localhost',
                 port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
                 handler=LogRecordStreamHandler):
        SocketServer.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = 0
        self.timeout = 1
        self.logname = None

    def serve_until_stopped(self):
        import select
        abort = 0
        while not abort:
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [],
                                       self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort

def main(logLevel, colored_output=True):
    # TODO: Colored output is relies on ANSI color codes, Windows needs to be supported somehow
    if colored_output :
        colored_console = logging.StreamHandler()
        colored_console.setLevel(logLevel)
        colored_console.setFormatter(AnsiColorFormatter("%(relativeCreated)5d %(name)-15s %(levelname)-8s %(message)s"))
        logging.getLogger().addHandler(colored_console)
    else :
        logging.basicConfig(
            format="%(relativeCreated)5d %(name)-15s %(levelname)-8s %(message)s")
    tcpserver = LogRecordSocketReceiver()
    print "About to start TCP server..."
    tcpserver.serve_until_stopped()

if __name__ == "__main__":
    import sys
    defaultLevel  = logging.WARNING  # Default log level (just print errors)
    logLevelToSet = None
    if len(sys.argv) >= 2 :
        levelArg = sys.argv[1]
        validLogLevels = [
                "DEBUG",
                "INFO",
                "WARNING",
                "ERROR",
                "CRITICAL",
            ]
        possibleLevels = filter(lambda l : l.startswith(levelArg.upper()), validLogLevels)
        if len(possibleLevels) > 0 :
            try :
                logLevelToSet = getattr(logging, possibleLevels[0])
                print 'LogLevel set to %s from argument %s' % (possibleLevels[0], levelArg)
            except AttributeError :
                pass

    if logLevelToSet is None :
        logLevel = defaultLevel
        print 'LogLevel defaulted to WARNING'
    else :
        logLevel = logLevelToSet

    main(logLevel)
