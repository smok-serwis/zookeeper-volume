import logging
import os

from .app import app

import zookeeper_plugin.handlers
import zookeeper_plugin.exceptions

if os.environ.get('DEBUG', '0') == '0':
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.DEBUG)

