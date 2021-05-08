import os
import logging
from satella.instrumentation import Traceback

from zookeeper_plugin.app import app
from zookeeper_plugin.json import as_json

logger = logging.getLogger(__name__)


class MountException(Exception):
    pass


@app.errorhandler(Exception)
@as_json
def handle_exception(e):
    if os.environ.get('DEBUG', '0') != '0':
        logger.error(Traceback().pretty_print(), exc_info=e)
    return {'Err': str(e)}, 500

