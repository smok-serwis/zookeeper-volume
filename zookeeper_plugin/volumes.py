from __future__ import annotations

import logging
import atexit
import os
import subprocess
import time
import typing as tp

from satella.coding import Closeable, Monitor, silence_excs, for_argument
from satella.coding.concurrent import IDAllocator
from satella.coding.structures import Singleton
from satella.json import write_json_to_file, read_json_from_file

from .exceptions import MountException


def to_hosts(items: tp.Union[tp.Sequence[str]]) -> str:
    if isinstance(items, (list, tuple)):
        return ','.join(sorted(items))
    elif isinstance(items, str):
        return items
    raise TypeError('Invalid type for items')


logger = logging.getLogger(__name__)

volume_id_assigner = IDAllocator()
BASE_PATH = '/mnt/volumes'
STATE_FILE = '/state/zookeeper-volume-state.json'


@Singleton
class VolumeDatabase(Monitor):
    def __init__(self):
        super().__init__()
        atexit.register(self.close)
        self.volumes = {}  # type: tp.Dict[str, Volume]

        with silence_excs(OSError):
            data = read_json_from_file(STATE_FILE)
            for vol in data:
                volume = Volume.load_from_dict(vol)
                self.add_volume(volume)

    def get_all_volumes(self) -> tp.Iterator[Volume]:
        return self.volumes.values()

    def add_volume(self, vol: Volume) -> None:
        name = vol.name
        self.volumes[name] = vol

    def rm_volume(self, vol: Volume) -> None:
        vol = self.volumes.pop(vol.name)
        vol.delete()
        vol.close()

    @for_argument(None, to_hosts)
    def volume_exists(self, name: str) -> bool:
        return name in self.volumes

    @for_argument(None, to_hosts)
    def get_volume(self, name: str,
                   hosts: tp.Optional[tp.Sequence[str]] = None,
                   path: tp.Optional[str] = None,
                   mode: str = 'DIR',
                   auth: tp.Optional[str] = None) -> Volume:
        if name not in self.volumes:
            if hosts is None or path is None:
                raise KeyError()
            vol = Volume(hosts, name, path, mode, auth)
            self.volumes[name] = vol
            return vol
        else:
            return self.volumes[name]

    def close(self) -> None:
        while self.volumes:
            key, vol = self.volumes.popitem()
            vol.close()

    def sync_to_disk(self) -> None:
        data = [vol.to_dict() for vol in self.get_all_volumes()]
        write_json_to_file(STATE_FILE, data)


class Volume(Closeable):
    def __init__(self, hosts: tp.Sequence[str], name: str, path: str,
                 mode: str = 'DIR', auth: tp.Optional[str] = None):
        super().__init__()
        self.monitor = Monitor()
        self.hosts = to_hosts(hosts)
        self.name = name
        self._path = path
        self.refcount = 0
        self.volume_id = str(volume_id_assigner.allocate_int())
        self.process = None
        self.mode = mode
        self.auth = auth

    def mount(self) -> None:
        path = self.path
        if not os.path.exists(path):
            os.mkdir(path)
        commandline = ['/usr/bin/zookeeperfuse', '-o', 'auto_unmount', '-f', path, '--',
                       '--zooHosts', self.hosts, '--zooPath', self._path]
        if self.mode == 'FILE':
            commandline.extend(['--leafMode', self.mode])
        if self.auth:
            commandline.extend(['--zooAuthentication', self.auth])
        self.process = subprocess.Popen(commandline, stdin=subprocess.DEVNULL,
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)

        time.sleep(1)
        if not self.alive:
            raise MountException('process died shortly after startup')

    def unmount(self) -> None:
        self.process.terminate()
        with silence_excs(subprocess.TimeoutExpired):
            self.process.wait(timeout=1)

        if self.process.returncode is None:
            logger.warning('Forcibly terminating PID %s', self.process.pid)
            self.process.kill()
            self.process.wait(timeout=1)

        self.process = None
        path = self.path
        if os.path.exists(path):
            os.rmdir(path)

    def on_mount(self) -> None:
        with self.monitor:
            if not self.refcount and self.process is None:
                self.mount()
            self.refcount += 1

    def on_unmount(self) -> None:
        with self.monitor:
            if self.refcount == 1 and self.process is not None:
                self.unmount()
            self.refcount -= 1

    @property
    def path(self) -> str:
        return os.path.join(BASE_PATH, self.volume_id)

    def close(self) -> None:
        if super().close():
            if self.process is not None:
                self.unmount()
            volume_id_assigner.mark_as_free(int(self.volume_id))

    def delete(self) -> None:
        # since Docker has a nasty habit of not calling Unmount when container finishes
        self.close()

    def to_dict(self) -> dict:
        a = {
            'hosts': self.hosts,
            'name': self.name,
            'path': self._path,
            'mode': self.mode
        }
        if self.auth:
            a['auth'] = self.auth
        return a

    @property
    def alive(self) -> bool:
        if self.process is None:
            return False
        with silence_excs(subprocess.TimeoutExpired):
            self.process.wait(0)
        if self.process.returncode is not None:
            self.process = None
            return False
        else:
            return True

    @classmethod
    def load_from_dict(cls, data) -> Volume:
        return Volume(data['hosts'], data['name'], data['path'],
                      data.get('mode', 'DIR'), data.get('auth'))
