# -*- coding: utf-8 -*-

import os
import datetime
import hashlib, binascii

import functools

from werkzeug.contrib.fixers import ProxyFix
from flask import Flask, session, request, render_template, redirect, url_for, escape

from bson.objectid import ObjectId

from mongoengine import connect

import error
from model import answer, assignment, problem, question, role, submission, submission_history, user


# Connect to mongodb://localhost:27017/tjlms without username && password
# http://docs.mongoengine.org/guide/connecting.html#guide-connecting
connect('tjlms')

app = Flask(__name__)

# app.wsgi_app = ProxyFix(app.wsgi_app)

def hash(data, salt):
    return binascii.hexlify(hashlib.pbkdf2_hmac('sha256', data.encode(), salt, 100000)).decode()

def check_roles(roles=[role.ADMIN, role.TA, role.STUDENT]):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if 'role' in session and session['role'] in roles:
                return func(*args, **kwargs)
            else:
                return redirect(url_for('login'))
        return wrapper
    return decorator

@app.route('/user/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        username = request.form['username']
        password = request.form['password']

        udoc = user.User.objects(username=username).first()
        if udoc and hash(password, udoc['salt']) == udoc['password_hash']:
            session['id'] = str(udoc['id'])
            session['role'] = udoc['role']
            return redirect(url_for('show_assignment_list'))
        else:
            return render_template('login.html',
                    error = error.LoginError())

@app.route('/user/logout')
def logout():
    session.pop('id')
    session.pop('role')
    return redirect(url_for('show_assignment_list'))

@app.route('/assignment')
def show_assignment_list():
    adocs = assignment.Assignment.objects(visible=True).all()
    return render_template('assignment_list.html', adocs=adocs)

@app.route('/assignment/<string:assignment_id>')
def show_assignment_detail(assignment_id):
    adoc = assignment.Assignment.objects(id=ObjectId(assignment_id)).first()
    return render_template('assignment_detail.html', adoc=adoc)

@app.route('/assignment/<string:assignment_id>/<string:problem_id>', methods=['GET'])
def show_problem(assignment_id, problem_id):
    pdoc = problem.Problem.objects(id=ObjectId(problem_id))
    return render_template('problem_detail', pdoc=pdoc)

@app.route('/assignment/<string:assignment_id>/<string:problem_id>', methods=['POST'])
@check_roles([role.ADMIN, role.STUDENT, role.ADMIN])
def submit_problem(assignment_id, problem_id):
    return "Submit Problem"

@app.route('/manage/user')
@check_roles([role.ADMIN])
def show_users():
    udocs = user.User.objects().all()
    return render_template('user_list.html', udocs=udocs)

@app.route('/manage/user/create', methods=['GET', 'POST'])
@check_roles([role.ADMIN])
def create_user():
    if request.method == 'GET':
        return render_template('user_create.html')
    else:
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        salt = os.urandom(16)
        password_hash = hash(password, salt)


        if not username:
            return render_template('user_create.html', error=error.FieldEmptyError('username'))

        if not password:
            return render_template('user_create.html', error=error.FieldEmptyError('password'))

        udoc = user.User.objects(username=username).first()
        if udoc:
            return render_template('user_create.html', error=error.UserAlreadyExistError(username))

        udoc = user.User(username=username, password_hash=password_hash, salt=salt, role=role)
        udoc.save()

        return redirect(url_for('show_users'))

@app.route('/manage/assignment')
@check_roles([role.ADMIN, role.TA])
def show_assignment_manage_list():
    adocs = assignment.Assignment.objects().all()
    return render_template('assignment_manage_list.html', adocs=adocs)

@app.route('/manage/create/assignment', methods=['GET', 'POST'])
@check_roles([role.ADMIN, role.TA])
def create_assignment():
    if request.method == 'GET':
        return render_template('assignment_manage_create.html')
    else:
        name = request.form['name']
        if not name:
            return render_template('assignment_manage_create.html', error=error.FieldEmptyError('name'))

        try:
            begin_at = datetime.datetime.strptime(request.form['begin_at'], "%Y-%m-%dT%H:%M")
            end_at = datetime.datetime.strptime(request.form['end_at'], "%Y-%m-%dT%H:%M")
        except:
            return render_template('assignment_manage_create.html', error=error.DateTimeInvalidError())

        if begin_at > end_at:
            return render_template('assignment_manage_create.html', error=error.DateTimeInvalidError())

        visible = request.form['visible']
        if visible == 'true':
            visible = True
        else:
            visible = False

        adoc = assignment.Assignment(name=name, begin_at=begin_at, end_at=end_at, visible=visible)
        adoc.save()

        return redirect(url_for('show_assignment_manage_list'))

@app.route('/manage/assignment/<string:assignment_id>')
@check_roles([role.ADMIN, role.TA])
def manage_assignment(assignment_id):
    adoc = assignment.Assignment.objects(id=ObjectId(assignment_id)).first()
    return render_template('assignment_manage_detail.html', adoc=adoc)

app.secret_key = os.urandom(24)
