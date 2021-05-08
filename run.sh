#!/bin/bash

exec gunicorn --bind unix:/socket/zookeeper-volume zookeeper_plugin.run:app
