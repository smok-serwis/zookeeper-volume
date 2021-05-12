from flask import Flask
import os

app = Flask(__name__)

DEBUG = os.environ.get('DEBUG', '0') != '0'

if not os.path.exists('/log/zookeeper-volume'):
    os.mkdir('/log/zookeeper-volume')
