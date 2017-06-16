# coding: utf-8
# © 2015 Instacart
from collections import defaultdict
from datetime import datetime
import json

import docker
from magiclog import log

from .version import version


docker_client_version = '1.24'


class Ahab(object):
    def __init__(self, url='unix:///var/run/docker.sock', handlers=[]):
        self.url = url
        self.handlers = handlers if len(handlers) > 0 else [Ahab.default]
        self.data = defaultdict(dict)

    def listen(self):
        client = docker.APIClient(base_url=self.url, version=docker_client_version)
        for event in client.events(decode=True):
            for k in ['time', 'Time']:
                if k in event:
                    event[k] = datetime.fromtimestamp(event[k])
            log.debug('Event: %s', event)
            data = {}
            i = get_id(event)
            if i is not None:
                try:
                    if 'from' in event or 'From' in event:
                        data = client.inspect_container(i)
                    else:
                        data = client.inspect_image(i)
                    self.data[i] = data
                except docker.errors.NotFound:
                    data = self.data[i]
            self.handle(event, data)

    def handle(self, event, data):
        for handler in self.handlers:
            handler(event, data)

    @staticmethod
    def default(event, data):
        """The default handler prints basic event info."""
        messages = defaultdict(lambda: 'Avast:')
        messages['start'] = 'Thar she blows!'
        messages['tag'] = 'Thar she blows!'
        messages['stop'] = 'Away into the depths:'
        messages['destroy'] = 'Away into the depths:'
        messages['delete'] = 'Away into the depths:'
        status = get_status(event)
        message = messages[status] + ' %s/%s'
        log.info(message, status, get_id(event))
        log.debug('"data": %s', form_json(data))


def form_json(data):
    return json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))


def get_status(event):
    for k in ['status', 'Status']:
        if k in event:
            return event[k]


def get_id(event):
    for k in ['id', 'ID', 'Id']:
        if k in event:
            return event[k]


__version__ = version()
