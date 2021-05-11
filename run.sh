#!/bin/bash

mkdir -p /run/docker/plugins
exec gunicorn -w 1 --threads 4 --bind unix:/run/docker/plugins/zookeeper-volume.sock zookeeper_plugin.run:app
