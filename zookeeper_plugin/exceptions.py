import os
import logging
import ujson
from flask import Response
from satella.instrumentation import Traceback

from zookeeper_plugin.app import app

logger = logging.getLogger(__name__)


def response(data, status_code=200):
    if 'status' in data:
        data['status'] = str(data['status'])
    return Response(ujson.dumps(data), status_code,
                    content_type='application/json')


class MountException(Exception):
    pass


@app.errorhandler(Exception)
def handle_exception(e):
    if os.environ.get('DEBUG', '0') != '0':
        logger.error(Traceback().pretty_print(), exc_info=e)
    return response({'status': e.message}, 500)

