import os
import csv
import time
import logging
import platform

# Level    Numeric value
# CRITICAL 50
# ERROR    40
# WARNING  30
# INFO     20
# DEBUG    10
# NOTSET   0

class LogConfigure:
    # basename for clients
    logname = None

    # message format
    msgfmt = [
        '%(levelname)s',
        '%(asctime)s',
        '%(name)s',
        '%(filename)s:%(lineno)d',
        '%(message)s',
    ]
    msgsep = ' '

    def __new__(cls):
        if cls.logname is None:
            # log level
            level = logging.DEBUG

            # message format
            msgfmt = cls.msgsep.join(cls.msgfmt)

            # date format
            mdy = [ 'm', 'd' ]
            hms = [ 'H', 'M', 'S' ]
            datesep_intra = ''
            datesep_inter = '.'

            mdyhms = [[ '%' + x for x in y ] for y in [ mdy, hms ]]
            datefmt = datesep_inter.join(map(datesep_intra.join, mdyhms))

            # configure!
            logging.basicConfig(level=level, format=msgfmt, datefmt=datefmt)
            cls.logname = '.'.join(map(str, [ platform.node(), os.getpid() ]))

        return cls.logname

def get_logger(root=False):
    elements = [ LogConfigure() ]
    if not root:
        elements.append(str(os.getpid()))
    name = '.'.join(elements)

    return logging.getLogger(name)

def readlog(fp, message_only=False):
    reader = csv.reader(fp, delimiter=LogConfigure.msgsep)
    msg = len(LogConfigure.msgfmt) - 1

    for row in reader:
        if not row.isspace():
            yield row[msg:] if message_only else row

#
# Log messages periodically. Handy for when the alternative is just
# too much. Not thread safe!
#
class PeriodicLogger:
    def __init__(self, periods):
        self.periods = periods
        self.last = time.time()

    def emit(self, msg, log_method=None):
        now = time.time()
        if now - self.last > self.periods:
            self.last = now
            if log_method is None:
                log_method = getlogger().info
            log_method(msg)
