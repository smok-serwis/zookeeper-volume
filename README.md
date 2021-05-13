# smokserwis/zookeeper-volume
[![docker hub plugin](https://img.shields.io/badge/docker%20hub%20plugin-1.1-green)](https://hub.docker.com/r/smokserwis/zookeeper-volume)
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

If you logs are stored somewhere else than `/var/log`, you best
do it too.

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

Note that the output from zookeeper-fuse is in:
 
* non-debug cases redirected to /dev/null.
* in debug cases it will be redirected to 
  `/var/log/zookeeper-volume/volumename.stdout.txt` and
  `/var/log/zookeeper-volume/volumename.stderr.txt`

# Usage

To define a volume just type

```bash
docker volume create -d smokserwis/zookeeper-volume -ohosts=192.168.2.237:2181 -opath=/zk-child zookeeper
```

The thing that you provide in `hosts` option is a ZooKeeper connection string.
This is the lists of hosts with ports separated with a comma.
As so, it is mandatory to provide port number.

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

## HYBRID mode

Since zookeeper-fuse's default access modes of DIR and FILE do not permit to use ZooKeeper systems as a valid filesystem (ie. once you create a file it becomes a directory) and does not support symlinks I have extended [zookeeper-fuse](https://github.com/smok-serwis/zookeeper-fuse.git) to add symlink support and if you create a file it stays a file. Basically it remembers what you have done while creating that file. I've also filed a [pull request](https://github.com/borowskk/zookeeper-fuse/pull/5).

Note however that cache invalidation is not yet supported, so if you process files with new names you are going to run into trouble. If you however keep on processing the same files, you should be OK.

What hybrid mode supports:

* files once created as files stay files. Directories created as directories start as directories. Note that this however applies to a single machine only, so if you create an empty file on one machine it's going to be seen as a directory on another.
* Symlinks are supported. However, in HYBRID mode `__symlinks__` is an invalid file name, since this is the file in which symlink information is stored at the root.
* `cp` is supported, `mv` is not.

# Changelog

# v1.1 

* HYBRID mode is fully supported
