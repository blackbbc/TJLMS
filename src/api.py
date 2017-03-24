# -*- coding: utf-8 -*-

import os
import datetime
import hashlib, binascii
import sys

import functools

from flask import session, request, render_template, redirect, url_for, escape, jsonify, Blueprint

from bson.objectid import ObjectId

from mongoengine import connect

import error
from model import answer, assignment, problem, question, role, submission, submission_history, user


# Connect to mongodb://localhost:27017/tjlms without username && password
# http://docs.mongoengine.org/guide/connecting.html#guide-connecting
connect('tjlms')

bp = Blueprint('api', __name__, template_folder='templates')

def hash(data, salt):
    return binascii.hexlify(hashlib.pbkdf2_hmac('sha256', data.encode(), salt, 100000)).decode()

def check_roles(roles=[role.ADMIN, role.TA, role.STUDENT]):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if 'role' in session and session['role'] in roles:
                return func(*args, **kwargs)
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

@bp.route('/user/login', methods=['POST'])
@require('username', 'password')
def login():
    username = request.json['username']
    password = request.json['password']

    udoc = user.User.objects(username=username).first()
    if udoc and hash(password, udoc['salt']) == udoc['password_hash']:
        session['id'] = str(udoc['id'])
        session['role'] = udoc['role']
        return jsonify(code=200)
    else:
        return jsonify(code=410, msg='Invalid username or password')

@bp.route('/user/logout')
def logout():
    session.pop('id', None)
    session.pop('role', None)
    return jsonify(code=200)

@bp.route('/user/status')
@check_roles()
def status():
    udoc = user.User.objects(id=ObjectId(session['id'])).first().to_json()
    return jsonify(code=200, data=udoc)

@bp.route('/assignment')
def show_assignment_list():
    adocs = assignment.Assignment.objects(visible=True).all()
    adocs = [adoc.to_json() for adoc in adocs]
    return jsonify(code=200, data=adocs)

@bp.route('/assignment/<string:assignment_id>')
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

@bp.route('/assignment/<string:assignment_id>/<string:problem_id>')
def show_problem(assignment_id, problem_id):
    try:
        pdoc = problem.Problem.objects(id=ObjectId(problem_id)).first()
        if pdoc:
            return jsonify(code=200, data=pdoc.to_json())
        else:
            return jsonify(code=200, data=None)
    except:
        return jsonify(code=200, data=None)

@bp.route('/assignment/<string:assignment_id>/<string:problem_id>', methods=['POST'])
@require('answers')
@check_roles()
def submit_problem(assignment_id, problem_id):
    answers = request.json['answers']
    adocs = []
    for adoc in answers:
        adoc = answer.Answer(question_id=adoc['question_id'], text=adoc['text'])
        adocs.append(adoc)
    sdoc = submission.Submission(user_id=ObjectId(session['id']), assignment_id=assignment_id, problem_id=problem_id, answers=adocs)
    shdoc = submission_history.SubmissionHistory(user_id=ObjectId(session['id']), assignment_id=assignment_id, problem_id=problem_id, answers=adocs)
    sdoc.save()
    shdoc.save()
    return jsonify(code=200)

@bp.route('/manage/user')
@check_roles([role.ADMIN])
def show_users():
    udocs = user.User.objects().all()
    udocs = [udoc.to_json() for udoc in udocs]
    return jsonify(code=200, data=udocs)

@bp.route('/manage/user/create', methods=['POST'])
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
        return jsonify(code=411, msg='User already exist.')

    udoc = user.User(username=username, password_hash=password_hash, salt=salt, role=role)
    udoc.save()

    return jsonify(code=200)

@bp.route('/manage/assignment')
@check_roles([role.ADMIN, role.TA])
def show_assignment_manage_list():
    adocs = assignment.Assignment.objects().all()
    adocs = [adoc.to_json() for adoc in adocs]
    return jsonify(code=200, data=adocs)

@bp.route('/manage/create/assignment', methods=['POST'])
@require('name', 'begin_at', 'end_at', 'visible')
@check_roles([role.ADMIN, role.TA])
def create_assignment():
        name = request.json['name']
        if not name:
            return jsonify(code=402, msg='Name cannot be empty.')

        try:
            begin_at = datetime.datetime.strptime(request.json['begin_at'], "%Y-%m-%dT%H:%M:%S")
            end_at = datetime.datetime.strptime(request.json['end_at'], "%Y-%m-%dT%H:%M:%S")
        except:
            return jsonify(code=403, msg='Invalid datetime.')

        if begin_at > end_at:
            return jsonify(code=403, msg='Invalid datetime.')

        visible = request.json['visible']

        adoc = assignment.Assignment(name=name, begin_at=begin_at, end_at=end_at, visible=visible)
        adoc.save()

        return jsonify(code=200)

def sort_submission(x, y):
    if x['problem']['order'] == y['problem']['order'] and x['user']['id'] == y['user']['id']:
        return 0
    if x['problem']['order'] < y['problem']['order'] \
            or x['problem']['order'] == y['problem']['order'] and x['user']['id'] < y['user']['id']:
                return -1
    else:
        return 1

@bp.route('/manage/assignment/<string:assignment_id>')
@check_roles([role.ADMIN, role.TA])
def manage_assignment(assignment_id):
    sdocs = submission.Submission.objects(assignment_id=assignment_id).all()
    ssdocs = []

    for index in range(0, len(sdocs)):
        sdoc = {}
        sdoc['user'] = user.User.objects(id=sdocs[index]['user_id']).first().to_json()
        sdoc['problem'] = problem.Problem.objects(id=sdocs[index]['problem_id']).first().to_json()
        ssdocs.append(sdoc)

    ssdocs.sort(key=functools.cmp_to_key(sort_submission))

    return jsonify(code=200, data=ssdocs)

@bp.route('/manage/create/problem/<string:assignment_id>', methods=['POST'])
@require('order', 'ptext', 'qtexts')
@check_roles([role.ADMIN, role.TA])
def create_problem(assignment_id):
    qtexts = request.json['qtexts']
    qdocs = []
    for qtext in qtexts:
        qdoc = question.Question(text=qtext)
        qdocs.append(qdoc)
    pdoc = problem.Problem(order=int(request.json['order']), assignment_id=ObjectId(assignment_id), text=request.json['ptext'], questions=qdocs)
    pdoc.save()
    return jsonify(code=200)

@bp.route('/grade/<string:submission_id>', methods=['POST'])
@require('grades')
@check_roles([role.ADMIN, role.TA])
def grade(submission_id):
    grades = request.json['grades']
    sdoc = submission.Submission.objects(id=ObjectId(submission_id)).first()
    answers = sdoc['answers']
    for answer in answers:
        for grade in grades:
            if grade['answer_id'] == str(answer['_id']):
                answer['score'] = grade['score']
                break
    sdoc.save()
    return jsonify(code=200)
