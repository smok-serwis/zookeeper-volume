#!/bin/bash

docker build -t smok-serwis/zookeeper-volume .
ID=$(docker create smok-serwis/zookeeper-volume true)
mkdir rootfs
docker export $id | tar -x -C rootfs/ && docker plugin create smok-serwis/zookeeper-volume .
docker plugin push smok-serwis/zookeeper-volume

