# -*- coding: utf-8 -*-

import os

from werkzeug.contrib.fixers import ProxyFix

from flask import Flask, render_template
from api import bp
from util import json

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.json_encoder = json.MongoJSONEncoder
app.register_blueprint(bp, url_prefix='/api')

# app.wsgi_app = ProxyFix(app.wsgi_app)

@app.route("/")
def index():
    return render_template('index.html')
