from flask import Flask
import os

app = Flask(__name__)

DEBUG = os.environ.get('DEBUG', '0') != '0'
