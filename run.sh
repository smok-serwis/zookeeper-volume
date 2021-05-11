#!/bin/bash

exec /usr/local/bin/gunicorn -w 1 --threads 4 --bind unix:/run/docker/plugins/zookeeper-volume.sock zookeeper_plugin.run:app
