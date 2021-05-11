# zookeeper-volume-plugin
[![docker hub plugin](https://img.shields.io/badge/docker%20hub%20plugin-1.0-green)](https://hub.docker.com/r/smokserwis/zookeeper-volume)

A Docker volume as a ZooKeeper tree volume plugin

# Installation

To install just type:

```bash
docker plugin smokserwis/zookeeper-volume
docker plugin enable smokserwis/zookeeper-volume
```

# Defining volumes

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

# Running

It got to be mounted with two volumes:

The first volume is the Docker socket plugin, most feasibly
located at `/var/run/docker/plugins/zookeeper-volume.sock`

The second volume is where the ZooKeeper volumes will be mounted via fuse.
Please mount it at `/zookeeper` and pass a single command line argument:
the path where it resides on the host. Thank you.

# Creating volumes

Volume must have at least a single option:

* either `host` for an address and a port name` 
  or `hosts` for multiple of those, separated by a `,`

Other options can be optionally given:

* `path`: zookeeper path to mount as root
* `mode`: [zookeeper-fuse](https://github.com/borowskk/zookeeper-fuse/blob/master/README) access mode 
    (default is DIR)
* `auth`: zookeeper authentication string (by default none given)

# Building from source

Just check this repo out on a normal UNIX platform (sorry, only UNIXes supported for the time being)
and invoke `build.sh`.
`build.sh` will automatically install and enable the plugin.

# Thanks and credits

Special thanks to [borowskk's zookeeper-fuse](https://github.com/borowskk/zookeeper-fuse.git), 
without which this plugin wouldn't happen to exist.
