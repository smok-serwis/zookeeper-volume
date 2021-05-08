import os
import logging
from satella.instrumentation import Traceback

from zookeeper_plugin.app import app
from zookeeper_plugin.json import as_json

logger = logging.getLogger(__name__)


class MountException(Exception):
    pass


@app.errorhandler(KeyError)
@as_json
def handle_key_errors(e):
    logger.debug('KeyError: %s', e, exc_info=Traceback().pretty_print())
    return {'Err': f'Key error {e}'}, 400


@app.errorhandler(TypeError)
@as_json
def handle_type_errors(e):
    logger.debug('TypeError: %s', e, exc_info=Traceback().pretty_print())
    return {'Err': f'Type error {e}'}, 400


@app.errorhandler(Exception)
@as_json
def handle_exceptions(e):
    logger.debug('Exception: %s', e, exc_info=Traceback().pretty_print())
    return {'Err': str(e)}, 500

