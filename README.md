# zookeeper-volume-plugin
A Docker volume as a ZooKeeper tree volume plugin

# Installation

To install just type:

```bash
docker plugin smok-serwis/zookeeper-volume
docker pugin enable smok-serwis/zookeeper-volume
```

# Defining volumes

To define a volume just type

```bash
docker volume create -d smok-serwis/zookeeper-volume -ohost=192.168.2.237 -opath=/zk-child zookeeper
```

You can also omit path to use the default root.
You can specify multiple hosts by using `hosts` option, such as:

```bash
docker volume create -d smok-serwis/zookeeper-volume -ohosts=192.168.2.237,192.168.2.238:2000 zookeeper
```

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

It accepts also a `path` argument, which is the address of the z-node to 
mount as root.

# Thanks and credits

Special thanks to [borowskk's zookeeper-fuse](https://github.com/borowskk/zookeeper-fuse.git), 
without which this plugin wouldn't happen to exist.
