# smokserwis/zookeeper-volume
[![docker hub plugin](https://img.shields.io/badge/docker%20hub%20plugin-1.0-green)](https://hub.docker.com/r/smokserwis/zookeeper-volume)
[![Maintainability](https://api.codeclimate.com/v1/badges/a60480b7e2fe114fd794/maintainability)](https://codeclimate.com/github/smok-serwis/zookeeper-volume/maintainability)

A Docker volume as a ZooKeeper tree volume plugin

# Installation

To install just type:

```bash
docker plugin install smokserwis/zookeeper-volume
docker plugin enable smokserwis/zookeeper-volume
```

Note that if you keep your Docker root in other place than
`/var/lib/docker`, best install from source, before which 
change the path in `config.json`

## Building from source

Just check this repo out on a normal UNIX platform (sorry, only UNIXes supported for the time being)
and invoke `build.sh`.
`build.sh` will automatically install and enable the plugin.

If you set the env `DEBUG` during `build.sh`'s run,
debugging mode will be enabled on the plugin. You can later change it.

## Debugging

To enable debug logs just type:

```bash
docker plugin set smokserwis/zookeeper-volume DEBUG=1
```

They will be dumped at `/var/log/daemon.log` or the usual place where your Docker drops it's logs.
Note that setting the env `DEBUG` during a run of `build.sh` will
automatically set the variable to 1.
The variable is kept at default 0 in `config.json`.

Note that the output from zookeeper-fuse, which is normally redirected to /dev/null,
will be redirected to zookeeper-volume's stdout.

# Usage

To define a volume just type

```bash
docker volume create -d smokserwis/zookeeper-volume -ohost=192.168.2.237 -opath=/zk-child zookeeper
```

You can also omit path to use the default root.
You can specify multiple hosts by using `hosts` option, such as:

```bash
docker volume create -d smokserwis/zookeeper-volume -ohosts=192.168.2.237:2181,192.168.2.238:2000 zookeeper
```

Note that it's mandatory to provide a port number.

## Creating volumes

Volume must have at least a single option:

* either `host` for an address and a port name` 
  or `hosts` for multiple of those, separated by a `,`

Other options can be optionally given:

* `path`: zookeeper path to mount as root
* `mode`: [zookeeper-fuse](https://github.com/smok-serwis/zookeeper-fuse/blob/master/README) access mode 
    (default is DIR), HYBRID is recommended for best impersonation of a filesystem
    due to how zookeeper's filesystem behaves. Read the appropriate [README](https://github.com/smok-serwis/zookeeper-fuse/blob/master/README)
    to figure out how exactly HYBRID works.
* `auth`: zookeeper authentication string (by default none given)

# Thanks and credits

Special thanks to [borowskk's zookeeper-fuse](https://github.com/borowskk/zookeeper-fuse.git), 
without which this plugin wouldn't happen to exist.
