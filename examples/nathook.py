#!/usr/bin/env python
# coding: utf-8
# © 2015 Instacart
# Published as part of http://tech.instacart.com/ahab/
from contextlib import contextmanager
import logging
from pprint import pformat
from random import randint
import subprocess

from ahab import Ahab
import iptc


log = logging.getLogger()


def main():
    logging.basicConfig(level=logging.INFO)
    listener = Ahab(handlers=[nat_handler])
    listener.listen()


def nat_handler(event, data):
    log.info('Event:\n%s', pformat(event))
    if 'Config' in data and 'Hostname' in data['Config']:
        ident = data['Id']
        f = {
            'start': create_nat,      # On 'start', we create the NAT rules
            'die': clear_nat                     # On 'die', we remove them
        }.get(event['status'])
        # The 'start' and 'die' events are the only ones relevant for
        # managing our NAT rules.
        if f is None:
            return
        host = data['Config']['Hostname']
        ip = data['NetworkSettings']['IPAddress']
        # We make a few attempts at the IP Tables operaiont, in case
        # there is overlap with another event handler trying to do the
        # same thing for another container.
        for n in range(1, 5):
            try:
                f(host, ip)
                break
            except iptc.IPTCError as e:
                if 'Resource temporarily unavailable' not in str(e):
                    log.error('IP Tables trouble for %s during NAT '
                              'setup, not continuing: %s', ident, e)
                    break
            except Exception as e:
                log.error('Unexpected error while handling NAT for %s: '
                          '%s', ident, e)
                break
                # No matter what happens, we don't error out, because that
                # would crash other handlers that might be in the midst of
                # configuring other containers.


def create_nat(host, container_ip):
    with table(iptc.Table.NAT) as nat:
        free_ips = list(secondary_ips() - ips_in_use())
        free = free_ips[randint(1, len(free_ips)) - 1]
        # Send packets that come in on the outer IP to the inner IP.
        dnat = iptc.Rule()
        dnat.dst = free
        target = dnat.create_target('DNAT')
        target.to_destination = container_ip
        comment = dnat.create_match('comment')
        comment.comment = 'ahab//' + host
        iptc.Chain(nat, 'DOCKER').insert_rule(dnat)
        # Rewrite packets from the inner IP so they go out on the outer IP.
        snat = iptc.Rule()
        snat.src = container_ip
        target = snat.create_target('SNAT')
        target.to_source = free
        comment = snat.create_match('comment')
        comment.comment = 'ahab//' + host
        iptc.Chain(nat, 'POSTROUTING').insert_rule(snat)


def clear_nat(host, container_ip):
    del container_ip                           # Could be used for sanity check
    with table(iptc.Table.NAT) as nat:
        token = 'ahab//' + host
        chains = ['DOCKER', 'POSTROUTING']
        for chain in [iptc.Chain(nat, name) for name in chains]:
            for rule in chain.rules:
                comments = [m for m in rule.matches if m.name == 'comment']
                if any(c.comment == token for c in comments):
                    chain.delete_rule(rule)


def ips_in_use():
    with table(iptc.Table.NAT) as nat:
        ips = set()
        token = 'ahab//'
        chains = ['DOCKER', 'POSTROUTING']
        for chain in [iptc.Chain(nat, name) for name in chains]:
            for rule in chain.rules:
                comments = [m for m in rule.matches if m.name == 'comment']
                if any(c.comment.startswith(token) for c in comments):
                    if rule.dst is not None:
                        ips |= set([rule.dst.split('/')[0]])
        log.info('IPs in use: %s', ips)
        return ips


def secondary_ips():
    secondary_ips = []
    script = 'ip addr list dev eth0 | fgrep secondary'
    text = subprocess.check_output(['sh', '-c', script])
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 2:
            continue
        secondary_ips += [fields[1].split('/')[0]]
    return set(secondary_ips)


open_tables = {}


@contextmanager
def table(tab):
    """Access IPTables transactionally in a uniform way.

    Ensures all access is done without autocommit and that only the outer
    most task commits, and also ensures we refresh once and commit once.
    """
    global open_tables
    if tab in open_tables:
        yield open_tables[tab]
    else:
        open_tables[tab] = iptc.Table(tab)
        open_tables[tab].refresh()
        open_tables[tab].autocommit = False
        yield open_tables[tab]
        open_tables[tab].commit()
        del open_tables[tab]


if __name__ == '__main__':
    main()
