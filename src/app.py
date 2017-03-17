# -*- coding: utf-8 -*-

import os
import datetime
import hashlib, binascii
import sys

import functools

from werkzeug.contrib.fixers import ProxyFix
from flask import Flask, session, request, render_template, redirect, url_for, escape, jsonify

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
            token = request.cookies.get('token')
            if token:
                udoc = user.User.verify_auth_token(token, app.secret_key)
                if udoc and udoc['role'] in roles:
                    return func(*args, **kwargs)
                else:
                    return jsonify(code=401, msg='Require roles.')
            else:
                return jsonify(code=401, msg='Require roles.')
        return wrapper
    return decorator

def require(*required_args):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for arg in required_args:
                if arg not in request.json:
                    return jsonify(code=400, msg='Invalid arguments.')
            return func(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/user/login', methods=['POST'])
@require('username', 'password')
def login():
    username = request.json['username']
    password = request.json['password']

    udoc = user.User.objects(username=username).first()
    if udoc and hash(password, udoc['salt']) == udoc['password_hash']:
        token = udoc.generate_auth_token(app.secret_key)
        return jsonify(code=200, token=token)
    else:
        return jsonify(code=410, msg='Invalid username or password')

@app.route('/user/logout')
def logout():
    token = user.User.invalidate()
    return jsonify(code=200, token=token)

@app.route('/assignment')
def show_assignment_list():
    adocs = assignment.Assignment.objects(visible=True).all()
    adocs = [adoc.to_json() for adoc in adocs]
    return jsonify(code=200, data=adocs)

@app.route('/assignment/<string:assignment_id>')
def show_assignment_detail(assignment_id):
    try:
        adoc = assignment.Assignment.objects(id=ObjectId(assignment_id)).first()
        if adoc:
            pdocs = problem.Problem.objects(assignment_id=assignment_id).order_by('+order').all()

            data = adoc.to_json()
            data['problems'] = [pdoc.to_json() for pdoc in pdocs]

            return jsonify(code=200, data=data)
        else:
            return jsonify(code=200, data=None)
    except:
        return jsonify(code=200, data=None)

@app.route('/assignment/<string:assignment_id>/<string:problem_id>')
def show_problem(assignment_id, problem_id):
    try:
        pdoc = problem.Problem.objects(id=ObjectId(problem_id)).first()
        if pdoc:
            return jsonify(code=200, data=pdoc.to_json())
        else:
            return jsonify(code=200, data=None)
    except:
        return jsonify(code=200, data=None)

# @app.route('/assignment/<string:assignment_id>/<string:problem_id>', methods=['POST'])
# @check_roles([role.ADMIN, role.STUDENT, role.ADMIN])
# def submit_problem(assignment_id, problem_id):
#     user_id = session['id']
#     atexts = request.form.getlist('atext')
#     qids = request.form.getlist('qid')
#     adocs = []
#     for atext, qid in zip(atexts, qids):
#         adoc = answer.Answer()
#         adoc = answer.Answer(question_id=qid, text=atext)
#         adocs.append(adoc)
#     sdoc = submission.Submission(user_id=user_id, assignment_id=assignment_id, problem_id=problem_id, answers=adocs)
#     shdoc = submission_history.SubmissionHistory(user_id=user_id, assignment_id=assignment_id, problem_id=problem_id, answers=adocs)
#     sdoc.save()
#     shdoc.save()
#     return redirect(url_for('show_assignment_detail', assignment_id=assignment_id))

@app.route('/manage/user')
@check_roles([role.ADMIN])
def show_users():
    udocs = user.User.objects().all()
    udocs = [udoc.to_json() for udoc in udocs]
    return jsonify(code=200, data=udocs)

@app.route('/manage/user/create', methods=['POST'])
@require('username', 'password', 'role')
@check_roles([role.ADMIN])
def create_user():
    username = request.json['username']
    password = request.json['password']
    role = request.json['role']
    salt = os.urandom(16)
    password_hash = hash(password, salt)

    if not username:
        return jsonify(code=402, msg='Username cannot be empty.')

    if not password:
        return jsonify(code=402, msg='Password cannot be empty.')

    udoc = user.User.objects(username=username).first()
    if udoc:
        return jsonify(code=403, msg='User already exist.')

    udoc = user.User(username=username, password_hash=password_hash, salt=salt, role=role)
    udoc.save()

    return jsonify(code=200)

@app.route('/manage/assignment')
@check_roles([role.ADMIN, role.TA])
def show_assignment_manage_list():
    adocs = assignment.Assignment.objects().all()
    adocs = [adoc.to_json() for adoc in adocs]
    return jsonify(code=200, data=adocs)
#
# @app.route('/manage/create/assignment', methods=['GET', 'POST'])
# @check_roles([role.ADMIN, role.TA])
# def create_assignment():
#     if request.method == 'GET':
#         return render_template('assignment_manage_create.html')
#     else:
#         name = request.form['name']
#         if not name:
#             return render_template('assignment_manage_create.html', error=error.FieldEmptyError('name'))
#
#         try:
#             begin_at = datetime.datetime.strptime(request.form['begin_at'], "%Y-%m-%dT%H:%M")
#             end_at = datetime.datetime.strptime(request.form['end_at'], "%Y-%m-%dT%H:%M")
#         except:
#             return render_template('assignment_manage_create.html', error=error.DateTimeInvalidError())
#
#         if begin_at > end_at:
#             return render_template('assignment_manage_create.html', error=error.DateTimeInvalidError())
#
#         visible = request.form['visible']
#         if visible == 'true':
#             visible = True
#         else:
#             visible = False
#
#         adoc = assignment.Assignment(name=name, begin_at=begin_at, end_at=end_at, visible=visible)
#         adoc.save()
#
#         return redirect(url_for('show_assignment_manage_list'))
#
# def sort_submission(x, y):
#     if x['problem']['order'] == y['problem']['order'] and x['user']['id'] == y['user']['id']:
#         return 0
#     if x['problem']['order'] < y['problem']['order'] \
#             or x['problem']['order'] == y['problem']['order'] and x['user']['id'] < y['user']['id']:
#                 return -1
#     else:
#         return 1
#
# @app.route('/manage/assignment/<string:assignment_id>')
# @check_roles([role.ADMIN, role.TA])
# def manage_assignment(assignment_id):
#     sdocs = submission.Submission.objects(assignment_id=assignment_id).all()
#     ssdocs = []
#
#     for index in range(0, len(sdocs)):
#         sdoc = {}
#         sdoc['user'] = user.User.objects(id=sdocs[index]['user_id']).first()
#         sdoc['problem'] = problem.Problem.objects(id=sdocs[index]['problem_id']).first()
#         sdoc['answers'] = sdocs[index]['answers']
#         ssdocs.append(sdoc)
#
#     ssdocs.sort(key=functools.cmp_to_key(sort_submission))
#
#     return render_template('assignment_manage_detail.html', sdocs=ssdocs)
#
# @app.route('/manage/create/problem/<string:assignment_id>', methods=['GET', 'POST'])
# @check_roles([role.ADMIN, role.TA])
# def create_problem(assignment_id):
#     if request.method == 'GET':
#         return render_template('problem_create.html')
#     else:
#         qtexts = request.form.getlist('qtext')
#         qdocs = []
#         for qtext in qtexts:
#             qdoc = question.Question(text=qtext)
#             qdocs.append(qdoc)
#         pdoc = problem.Problem(order=int(request.form['order']), assignment_id=ObjectId(assignment_id), text=request.form['ptext'], questions=qdocs)
#         pdoc.save()
#         return redirect(url_for('show_assignment_list'))

app.secret_key = os.urandom(24)
