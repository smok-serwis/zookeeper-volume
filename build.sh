#!/bin/bash

if [ -d "rootfs" ]; then
    rm -rf rootfs
fi

docker build -t smok-serwis/zookeeper-volume .
ID=$(docker create smok-serwis/zookeeper-volume true)
mkdir rootfs
docker export $ID | tar -x -C rootfs/ && docker plugin create smok-serwis/zookeeper-volume .
docker plugin set smok-serwis/zookeeper-volume DEBUG=1
docker plugin enable smok-serwis/zookeeper-volume
#docker plugin push smok-serwis/zookeeper-volume

