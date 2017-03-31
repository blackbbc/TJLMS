# -*- coding: utf-8 -*-

import os

from werkzeug.contrib.fixers import ProxyFix

from flask import Flask, render_template, redirect, url_for
from api import bp
from util import json

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.json_encoder = json.MongoJSONEncoder
app.register_blueprint(bp, url_prefix='/api')

app.wsgi_app = ProxyFix(app.wsgi_app)

# @app.route("/")
# def index():
    # return render_template('index.html')

# @app.errorhandler(404)
# def page_not_found(e):
    # return redirect(url_for("index"))

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template("index.html")
