from flask import Flask
from flask_json import FlaskJSON

app = Flask(__name__)
FlaskJSON(app)

