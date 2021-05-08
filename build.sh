#!/bin/bash

if [ -d "rootfs" ]; then
    rm -rf rootfs
fi

docker build -t smokserwis/zookeeper-volume .
ID=$(docker create smokserwis/zookeeper-volume true)
mkdir rootfs
docker export $ID | tar -x -C rootfs/ && docker plugin create smokserwis/zookeeper-volume .
docker rm $ID
docker plugin set smokserwis/zookeeper-volume DEBUG=1
docker plugin enable smokserwis/zookeeper-volume
#docker plugin push smokserwis/zookeeper-volume

