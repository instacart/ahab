#!/usr/bin/env python
# coding: utf-8
# © 2015 Instacart
from argh import arg, dispatch_command
import sys

from . import Ahab
from .logger import log
from . import logger


@arg('connection', help='Docker connection string.', nargs='?',
     default=Ahab().url)
@arg('--console', help='Override default console log level.')
@arg('--syslog', help='Override default syslog log level.')
def ahab(connection, console=None, syslog=None):
    logger.configure(console=console, syslog=syslog)
    log.info('Under weigh.')
    try:
        Ahab(connection).listen()
    except KeyboardInterrupt:
        log.warning("It's CTRL-C!")
    except Exception:
        log.exception("It wasn't unexpected!")
        sys.exit(2)
    log.info('Hove to.')


def main():
    dispatch_command(ahab)


if __name__ == '__main__':
    main()
