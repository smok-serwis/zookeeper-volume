import json
from flask import request, Response
from satella.coding import wraps


def get_json():
    data = request.data.decode('utf-8')
    return json.loads(data)


def as_json(c):
    @wraps(c)
    def inner(*args, **kwargs):
        d = c(*args, **kwargs)
        if isinstance(d, tuple):
            data, return_code = d
        else:
            data, return_code = d, 200
        return Response(response=json.dumps(data), status=return_code,
                        content_type='application/vnd.docker.plugins.v1+json')
    return inner
