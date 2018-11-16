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
    def __init__(self,
                 url='unix:///var/run/docker.sock', handlers=[], since=None):
        self.url = url
        self.handlers = handlers if len(handlers) > 0 else [Ahab.default]
        self.data = defaultdict(dict)
        self.since = since

    def listen(self):
        client = docker.APIClient(base_url=self.url, version=docker_client_version)

        # the 'since' flag is to start reading from a particular event.
        # see the docker SDK docs:
        # https://docker-py.readthedocs.io/en/stable/client.html#docker.client.DockerClient.events
        for event in client.events(decode=True, since=self.since):
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
            # mark the last event seen so we can restart this listener
            # without dropping events. the caller must be responsible for
            # ensuring that handlers do not drop events, because they are
            # fire-and-forget from this point.
            self.since = get_time_nano(event)

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


def get_time_nano(event):
    time_nano = None
    for k in ['timeNano', 'timenano']:
        if k in event:
            time_nano = event[k]
            break
    return time_nano


__version__ = version()
