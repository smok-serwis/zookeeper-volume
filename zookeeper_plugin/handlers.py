import logging
from flask import request
from flask_json import as_json

from .app import app
from .volumes import VolumeDatabase
from .exceptions import MountException


logger = logging.getLogger(__name__)


@app.route('/Plugin.Activate', methods=['POST'])
@as_json
def activate():
    return {
        'Implements': ['VolumeDriver']
    }


@app.route('/VolumeDriver.Create', methods=['POST'])
@as_json
def volume_create():
    data = request.get_json()
    logger.warning(request)
    logger.warning(request.data)
    logger.warning(dir(request))
    for key in request.__dict__:
        logger.warning('%s=%s', key, request.__dict__[key])
    name = data['Name']
    options = data.get('Options', {})
    if 'host' not in options:
        return {'Err': 'expected host in options'}, 400
    if 'host' in options:
        hosts = options['host']
    elif 'hosts' in options:
        hosts = options['hosts'].split(',')

    path = options.get('path', '/')
    zdb = VolumeDatabase()
    if zdb.volume_exists(name):
        return {'Err': 'volume already exists'}, 409
    vol = zdb.get_volume(hosts, name, path)
    zdb.add_volume(vol)
    zdb.sync_to_disk()
    return {'Err': ''}


@app.route('/VolumeDriver.Remove', methods=['POST'])
@as_json
def volume_remove():
    data = request.get_json()
    name = data['Name']
    zdb = VolumeDatabase()
    try:
        vol = zdb.get_volume(name)
    except KeyError:
        return {'Err': 'volume does not exist',
                'Mountpoint': ''}, 404
    zdb.rm_volume(vol)
    zdb.sync_to_disk()
    return {'Err': ''}


@app.route('/VolumeDriver.Mount', methods=['POST'])
@as_json
def volume_mount():
    data = request.get_json()
    name = data['Name']
    zdb = VolumeDatabase()
    try:
        vol = zdb.get_volume(name)
    except KeyError:
        return {'Err': 'volume does not exist',
                'Mountpoint': ''}, 404
    try:
        vol.on_mount()
    except MountException:
        return {'Err': 'Exception on mounting',
                'Mountpoint': ''}, 500
    return {'Mountpoint': vol.to_path(),
            'Err': ''}


@app.route('/VolumeDriver.Unmount', methods=['POST'])
@as_json
def volume_unmount():
    data = request.get_json()
    name = data['Name']
    zdb = VolumeDatabase()
    try:
        vol = zdb.get_volume(name)
    except KeyError:
        return {'Err': 'volume does not exist',
                'Mountpoint': ''}, 404

    vol.on_unmount()
    return {'Err': ''}


@app.route('/VolumeDriver.List', methods=['POST'])
@as_json
def volumes_list():
    result = []
    zdb = VolumeDatabase()
    for volume in zdb.get_all_volumes():
        result.append({'Name': volume.name,
                       'Mountpoint': volume.to_path()})
    return {'Err': '',
            'Volumes': result}


@app.route('/VolumeDriver.Path', methods=['POST'])
@as_json
def volume_path():
    data = request.get_json()
    name = data['Name']
    zdb = VolumeDatabase()
    try:
        vol = zdb.get_volume(name)
    except KeyError:
        return {'Err': 'volume does not exist',
                'Mountpoint': ''}, 404

    return {'Mountpoint': vol.to_path(),
            'Err': ''}


@app.route('/VolumeDriver.Get', methods=['POST'])
@as_json
def volume_get():
    data = request.get_json()
    name = data['Name']
    zdb = VolumeDatabase()
    try:
        vol = zdb.get_volume(name)
    except KeyError:
        return {'Err': 'volume does not exist',
                'Mountpoint': ''}, 404

    return {'Volume': {
        'Name': vol.name,
        'Mountpoint': vol.to_path(),
    }, 'Err': ''
    }


@app.route('/VolumeDriver.Capabilities', methods=['POST'])
@as_json
def capabilities_get():
    return {'Capabilities': {'Scope': 'global'}}
