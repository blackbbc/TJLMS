# -*- coding: utf-8 -*-

import os

from werkzeug.contrib.fixers import ProxyFix

from flask import Flask
from api import bp

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.register_blueprint(bp, url_prefix='/api')

# app.wsgi_app = ProxyFix(app.wsgi_app)
