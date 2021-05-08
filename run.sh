#!/bin/bash

exec gunicorn -w 4 --bind unix:/run/docker/plugins/zookeeper-volume.sock zookeeper_plugin.run:app
