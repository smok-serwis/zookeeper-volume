# zookeeper-volume-plugin
A Docker volume as a ZooKeeper tree volume plugin

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
