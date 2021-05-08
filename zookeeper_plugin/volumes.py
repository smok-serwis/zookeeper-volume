from __future__ import annotations

import logging
import atexit
import os
import subprocess
import time
import typing as tp

from satella.coding import Closeable, Monitor, silence_excs
from satella.coding.concurrent import IDAllocator
from satella.coding.structures import Singleton
from satella.json import write_json_to_file, read_json_from_file

from zookeeper_plugin.exceptions import MountException


def to_hosts(items: tp.Sequence[str]) -> str:
    return ','.join(sorted(items))

logger = logging.getLogger(__name__)

volume_id_assigner = IDAllocator()
BASE_PATH = '/mnt/volumes'
STATE_FILE = '/state/zookeeper-volume-state.json'


@Singleton
class VolumeDatabase(Monitor):
    def __init__(self):
        super().__init__()
        atexit.register(self.close)
        self.volumes = {}   # type: tp.Dict[str, Volume]

        with silence_excs(OSError):
            data = read_json_from_file(STATE_FILE)
            for vol in data:
                volume = Volume.load_from_dict(vol)
                self.add_volume(volume)

    def get_all_volumes(self) -> tp.Iterator[Volume]:
        return self.volumes.values()

    def add_volume(self, vol: Volume):
        name = vol.name
        self.volumes[name] = vol

    def rm_volume(self, vol: Volume):
        vol = self.volumes.pop(vol.name)
        vol.delete()
        vol.close()

    def volume_exists(self, name: str) -> bool:
        return name in self.volumes

    def get_volume(self, name: str,
                   hosts: tp.Optional[tp.Sequence[str]] = None,
                   path: tp.Optional[str] = None):
        if name not in self.volumes:
            try:
                vol = Volume.load_from_disk(name)
            except KeyError:
                if hosts is None:
                    raise KeyError('Cannot obtain an empty volume!')
                assert path is not None

                vol = Volume(hosts, name, path)
            self.volumes[name] = vol
            return vol
        else:
            return self.volumes[name]

    def close(self):
        while self.connections:
            key, conn = self.connections.popitem()
            conn.close()

    def sync_to_disk(self) -> None:
        data = [vol.to_dict() for vol in self.get_all_volumes()]
        write_json_to_file(STATE_FILE, data)


class Volume(Closeable):
    hosts = 'name', 'hosts', 'path', 'volume_id', 'process', 'reference_count', 'monitor'

    def __init__(self, hosts: tp.Sequence[str], name: str, path: str):
        Closeable.__init__(self)
        self.monitor = Monitor()
        self.hosts = to_hosts(hosts)
        self.name = name
        self.path = path
        self.reference_count = 0
        self.volume_id = str(volume_id_assigner.allocate_int())
        self.process = None

    def mount(self):
        path = self.to_path()
        if not os.path.exists(path):
            os.mkdir(path)
        self.process = subprocess.Popen(f'zookeeperfuse {path} -- '
                                        f'--zooPath {self.path} --zooHosts {self.handler.hosts}')
        time.sleep(1)
        if not self.alive:
            raise MountException()

    def unmount(self):
        self.process.terminate()

        if self.process.returncode is None:
            logger.warning(f'Forcibly terminating PID {self.process.pid}')

        self.process = None
        path = self.to_path()
        if os.path.exists(path):
            os.rmdir(path)

    def on_mount(self):
        with self.monitor:
            if self.reference_count == 0 and self.process is None:
                self.mount()
            self.reference_count += 1

    def on_unmount(self):
        with self.monitor:
            if self.reference_count == 1:
                self.unmount()
            self.reference_count -= 1

    def to_path(self) -> str:
        return os.path.join(BASE_PATH, self.volume_id)

    def close(self):
        if super().close():
            if self.process is not None:
                self.unmount()
            volume_id = int(self.volume_id)
            volume_id_assigner.mark_as_free(volume_id)

    def to_dict(self) -> dict:
        return {
            'hosts': self.hosts,
            'name': self.name,
            'path': self.path
        }

    @property
    def alive(self) -> bool:
        if self.process is None:
            return False
        return self.process.returncode is None

    @classmethod
    def load_from_dict(cls, data) -> Volume:
        return Volume(data['hosts'], data['name'], data['path'])
