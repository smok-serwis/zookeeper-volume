import logging

from .app import app, DEBUG
from . import __version__
import zookeeper_plugin.handlers
import zookeeper_plugin.exceptions

logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)

logging.getLogger(__name__).warning('smokserwis/zookeeper-volume v%s starting', __version__)

__all__ = ['app']
