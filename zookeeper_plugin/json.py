import ujson
from flask import request, Response
from satella.coding import wraps


def get_json():
    data = request.data.decode('utf-8')
    return ujson.loads(data)


def as_json(c):
    @wraps(c)
    def inner(*args, **kwargs):
        d = c(*args, **kwargs)
        if isinstance(d, tuple):
            return_code = d[1]
            data = d[0]
        else:
            return_code = 200
            data = d
        return Response(response=ujson.dumps(data), status=return_code,
                        content_type='application/vnd.docker.plugins.v1+json')
    return inner
