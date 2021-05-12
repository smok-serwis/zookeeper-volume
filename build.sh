#!/bin/bash
set -x    # Show every command executed
set -e    # Stop on error

if [ -d "rootfs" ]; then
    rm -rf rootfs
fi

docker build -t smokserwis/zookeeper-volume .
ID=$(docker create smokserwis/zookeeper-volume true)
mkdir rootfs
docker export $ID | tar -x -C rootfs/ && docker plugin create smokserwis/zookeeper-volume .
docker rm $ID

if [[ ! -v DEBUG ]]; then
  echo "Enabling debugging mode"
  docker plugin set smokserwis/zookeeper-volume DEBUG=1
fi

docker plugin enable smokserwis/zookeeper-volume

