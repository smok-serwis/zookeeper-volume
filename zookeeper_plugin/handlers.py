import logging

from .app import app
from .json import get_json, as_json
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
    data = get_json()
    logger.debug('VolumeDriver.Create(%s)', data)
    name = data['Name']
    options = data.get('Opts', {})
    if 'host' in options:
        hosts = [options['host']]
    elif 'hosts' in options:
        hosts = options['hosts'].split(',')
    else:
        return {'Err': 'expected host or hosts in options'}, 400

    path = options.get('path', '/')
    zdb = VolumeDatabase()
    if zdb.volume_exists(name):
        return {'Err': 'volume already exists'}, 409
    vol = zdb.get_volume(name, hosts, path)
    zdb.add_volume(vol)
    zdb.sync_to_disk()
    return {'Err': ''}


@app.route('/VolumeDriver.Remove', methods=['POST'])
@as_json
def volume_remove():
    data = get_json()
    logger.debug('VolumeDriver.Remove(%s)', data)

    name = data['Name']
    zdb = VolumeDatabase()
    try:
        vol = zdb.get_volume(name)
    except KeyError:
        return {'Err': 'volume does not exist'}, 404
    zdb.rm_volume(vol)
    zdb.sync_to_disk()
    return {'Err': ''}


@app.route('/VolumeDriver.Mount', methods=['POST'])
@as_json
def volume_mount():
    data = get_json()
    logger.debug('VolumeDriver.Mount(%s)', data)
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
    return {'Mountpoint': vol.path,
            'Err': ''}


@app.route('/VolumeDriver.Unmount', methods=['POST'])
@as_json
def volume_unmount():
    data = get_json()
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
    logger.debug('VolumeDriver.List()')
    zdb = VolumeDatabase()
    for volume in zdb.get_all_volumes():
        result.append({'Name': volume.name,
                       'Mountpoint': volume.path})
    return {'Err': '',
            'Volumes': result}


@app.route('/VolumeDriver.Path', methods=['POST'])
@as_json
def volume_path():
    data = get_json()
    logger.debug('VolumeDriver.Path(%s)', data)
    name = data['Name']
    zdb = VolumeDatabase()
    try:
        vol = zdb.get_volume(name)
    except KeyError:
        return {'Err': 'volume does not exist',
                'Mountpoint': ''}, 404

    return {'Mountpoint': vol.path,
            'Err': ''}


@app.route('/VolumeDriver.Get', methods=['POST'])
@as_json
def volume_get():
    data = get_json()
    logger.debug('VolumeDriver.Get(%s)', data)
    name = data['Name']
    zdb = VolumeDatabase()
    try:
        vol = zdb.get_volume(name)
    except KeyError:
        return {'Err': 'volume does not exist',
                'Mountpoint': ''}, 404

    return {'Volume': {
        'Name': vol.name,
        'Mountpoint': vol.path,
    }, 'Err': ''
    }


@app.route('/VolumeDriver.Capabilities', methods=['POST'])
@as_json
def capabilities_get():
    logger.debug('VolumeDriver.Capabilities')
    return {'Capabilities': {'Scope': 'global'}}
