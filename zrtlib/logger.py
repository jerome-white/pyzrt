import os
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
    logname = None # basename for clients
    
    def __new__(cls):
        if not cls.logname:
            # log level
            level = logging.DEBUG

            # message format
            msgfmt = [
                '%(levelname)s %(asctime)s',
                '%(name)s',
                '%(filename)s:%(lineno)d',
                '%(message)s',
            ]
            msgsep = ' '
            msgfmt = msgsep.join(msgfmt)

            # date format
            mdy = [ 'Y', 'm', 'd' ]
            hms = [ 'H', 'M', 'S' ]
            datesep_intra = ''
            datesep_inter = ','

            mdyhms = [ [ '%' + x for x in y ] for y in [mdy, hms] ]
            datefmt = datesep_inter.join(map(datesep_intra.join, mdyhms))

            # configure!
            logging.basicConfig(level=level, format=msgfmt, datefmt=datefmt)
            cls.logname = '.'.join(map(str, [ platform.node(), os.getpid() ]))
            
        return cls.logname

def getlogger(root=False):
    elements = [ LogConfigure() ]
    if not root:
        elements.append(str(os.getpid()))
    name = '.'.join(elements)
    
    return logging.getLogger(name)

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
