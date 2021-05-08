import logging
import os

from .app import app

import zookeeper_plugin.volume
import zookeeper_plugin.handshake
import zookeeper_plugin.exceptions

print('Gunicorn started')

if os.environ.get('DEBUG', '0') != '0':
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

