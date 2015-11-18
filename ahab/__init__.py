# coding: utf-8
# © 2015 Instacart
from collections import defaultdict
from datetime import datetime
import json

import docker

from .version import version
from .logger import log


class Ahab(object):
    def __init__(self, url='unix:///var/run/docker.sock', handlers=[]):
        self.url = url
        self.handlers = handlers if len(handlers) > 0 else [Ahab.default]
        self.data = defaultdict(dict)

    def listen(self):
        client = docker.Client(base_url=self.url)
        for event in client.events(decode=True):
            if 'time' in event:
                event['time'] = datetime.fromtimestamp(event['time'])
            log.debug('Event: %s', event)
            try:
                if 'from' in event:
                    data = client.inspect_container(event['id'])
                else:
                    data = client.inspect_image(event['id'])
                self.data[event['id']] = data
            except docker.errors.NotFound:
                data = self.data[event['id']]
            self.handle(event, data)

    def handle(self, event, data):
        for handler in self.handlers:
            handler(event, self.data[event['id']])

    @staticmethod
    def default(event, data):
        """The default handler prints basic event info."""
        messages = defaultdict(lambda: 'Avast:')
        messages['start'] = 'Thar she blows!'
        messages['tag'] = 'Thar she blows!'
        messages['stop'] = 'Away into the depths:'
        messages['destroy'] = 'Away into the depths:'
        messages['delete'] = 'Away into the depths:'
        message = messages[event['status']] + ' %s/%s'
        log.info(message, event['status'], event['id'])
        log.debug('"data": %s', form_json(data))


def form_json(data):
    return json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))


__version__ = version()
