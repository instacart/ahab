# coding: utf-8
# © 2015 Instacart
import logging
import logging.handlers
import os
import sys


app = __package__
log = logging.getLogger(app)


def configure(console=None, syslog=None, logger=log, extended=True):
    global handlers
    console = norm_level(console)
    syslog = norm_level(syslog)
    if console is None and syslog is None:
        console, syslog = default_levels()
    if console and console != logging.NOTSET and handlers['console'] is None:
        handlers['console'] = logging.StreamHandler()
    if handlers['console'] is not None:
        handlers['console'].setLevel(console)
        configure_console_format(handlers['console'], extended)
        logger.addHandler(handlers['console'])
    if syslog and syslog != logging.NOTSET and handlers['syslog'] is None:
        fmt = app + '[%(process)d]: %(name)s %(message)s'
        handler = logging.handlers.SysLogHandler(address=default_syslog())
        handler.setFormatter(logging.Formatter(fmt=fmt))
    if handlers['syslog'] is not None:
        handlers['syslog'].setLevel(syslog)
        logger.addHandler(handlers['syslog'])
    logger.setLevel(min(level for level in [console, syslog]
                        if level is not None))


def default_levels():
    if sys.stdout.isatty():
        return logging.INFO, None
    else:
        return None, logging.INFO


handlers = {'console': None, 'syslog': None}


def default_syslog():
    if os.path.exists('/var/run/syslog'):
        return '/var/run/syslog'
    return '/dev/log'


def configure_console_format(handler, extended=True):
    extended_fmt = ('%(asctime)s.%(msecs)03d  %(levelname)7s  %(name)s\n'
                    '  %(message)s')
    spartan_fmt = '%(asctime)s.%(msecs)03d %(message)s'
    if extended:
        fmt = logging.Formatter(fmt=extended_fmt, datefmt='%H:%M:%S')
    else:
        fmt = logging.Formatter(fmt=spartan_fmt, datefmt='%H:%M:%S')
    handler.setFormatter(fmt)


def norm_level(level):
    if level is None:
        return level
    if isinstance(level, basestring):
        return logging._levelNames[level.upper()]
    else:
        logging._levelNames[level]                         # Raise if not found
        return level


def levels():
    return {_ for _ in logging._levelNames.keys() if isinstance(_, basestring)}


def ensure_null_handler(logger=log):
    try:
        cls = logging.NullHandler                # This was only defined as 2.7
    except:
        class NullHandler(logging.Handler):
            def emit(self, record):
                pass
        cls = NullHandler
    logger.addHandler(cls())


ensure_null_handler()
