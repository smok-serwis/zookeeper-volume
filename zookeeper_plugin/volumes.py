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

from .exceptions import MountException
from .app import DEBUG


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

    def volume_exists(self, name: str) -> bool:
        return name in self.volumes

    def get_volume(self, name: str,
                   hosts: tp.Optional[str] = None,
                   path: tp.Optional[str] = None,
                   mode: str = 'DIR',
                   auth: tp.Optional[str] = None) -> Volume:
        """
        The volume factory function.

        It will either return a currently existing volume or make a new one.
        However, in order to make a new one you will need to provide extra arguments.

        :param name: volume name
        :param hosts: only mandatory if the volume does not yet exist
        :param path: only mandatory if the volume does not yet exist
        :param mode: only mandatory if the volume does not yet exist
        :param auth: only mandatory if the volume does not yet exist
        :return: a Volume instance
        """
        if name not in self.volumes:
            if hosts is None or path is None:
                raise KeyError('The volume is not present and extra data is required to make it')
            vol = Volume(hosts, name, path, mode, auth)
            self.volumes[name] = vol
            return vol
        else:
            return self.volumes[name]

    def close(self) -> None:
        logger.warning('zookeeper-volume terminating')
        while self.volumes:
            key, vol = self.volumes.popitem()
            vol.close()

    def sync_to_disk(self) -> None:
        data = [vol.to_dict() for vol in self.get_all_volumes()]
        write_json_to_file(STATE_FILE, data)


class Volume(Closeable):
    def __init__(self, hosts: str, name: str, path: str,
                 mode: str = 'DIR', auth: tp.Optional[str] = None):
        super().__init__()
        self.monitor = Monitor()
        self.hosts = hosts
        self.name = name
        self._path = path
        self.refcount = 0
        self.volume_id = str(volume_id_assigner.allocate_int())
        self.process = None
        self.mode = mode
        self.auth = auth
        self.fds_to_close = []
        self.last_rc_code = None

    def mount(self) -> None:
        path = self.path
        if not os.path.exists(path):
            os.mkdir(path)
        commandline = ['/usr/bin/zookeeperfuse', '-o', 'auto_unmount', '-f', path]
        kwargs = {'stdout': subprocess.DEVNULL,
                  'stderr': subprocess.DEVNULL}
        if DEBUG:
            commandline.extend(['-o', 'debug'])
            self.fds_to_close = [open(f'/log/zookeeper-volume/{self.name}.stdout.txt', 'w'),
                                 open(f'/log/zookeeper-volume/{self.name}.stderr.txt', 'w')]
            kwargs.update(stdout=self.fds_to_close[0],
                          stderr=self.fds_to_close[1])
        commandline.append('--')
        commandline.extend(['--zooHosts', self.hosts, '--zooPath', self._path])
        if self.mode != 'DIR':
            commandline.extend(['--leafMode', self.mode])
        if self.auth:
            commandline.extend(['--zooAuthentication', self.auth])
        if DEBUG:
            commandline.extend(['--logLevel', 'DEBUG'])
        logger.debug('calling subprocess.Popen(%s, stdin=DEVNULL, preexec_fn=os.setsid, %s)',
                     commandline, kwargs)
        self.process = subprocess.Popen(commandline, stdin=subprocess.DEVNULL,
                                        preexec_fn=os.setsid,
                                        **kwargs)

        time.sleep(2)
        if not self.alive:
            logger.error('Process died shortly after creation, RC=%s, '
                         'subprocess.Popen was called with (%s, stdin=DEVNULL, '
                         'preexec_fn=os.setsid, %s)', self.last_rc_code, commandline, kwargs)
            raise MountException('process died shortly after startup RC=%s' % (self.last_rc_code, ))

    @silence_excs(subprocess.TimeoutExpired)
    def wait(self, timeout=1):
        self.process.wait(timeout=timeout)

    def unmount(self) -> None:
        self.wait()
        if self.alive:
            self.process.terminate()
            self.wait(10)

            if self.alive:
                pgid = os.getpgid(self.process.pid)
                logger.warning('Forcibly terminating PID %s PGID %s', self.process.pid, pgid)
                os.killpg(pgid)
                self.wait(10)

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
        if self.refcount:
            raise RuntimeError('Volume is still mounted!')
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
        self.wait(0)
        a = self.process.returncode is None
        if not a:
            while self.fds_to_close:
                self.fds_to_close.pop().close()

            if self.process.returncode:
                logger.error('zookeeperfuse terminated with RC of %s', self.process.returncode)
            self.last_rc_code = self.process.returncode
            self.process = None
        return a

    @classmethod
    def load_from_dict(cls, data) -> Volume:
        return Volume(data['hosts'], data['name'], data['path'],
                      data.get('mode', 'DIR'), data.get('auth'))
