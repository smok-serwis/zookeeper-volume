from flask_json import as_json

from zookeeper_plugin.app import app


@app.route('/Plugin.Activate')
@as_json
def activate():
    return {
        'Implements': ['VolumeDriver']
    }

