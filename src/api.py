# -*- coding: utf-8 -*-

import os
import datetime
import hashlib, binascii
import sys

import functools

from flask import session, request, render_template, redirect, url_for, escape, jsonify, Blueprint

from bson.objectid import ObjectId

from mongoengine import connect
from mongoengine import errors

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
                return jsonify(code=401, reason='您未登录或无权限访问此页')
        return wrapper
    return decorator

def require(*required_args):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for arg in required_args:
                if arg not in request.json:
                    return jsonify(code=400, reason='Invalid arguments.')
            return func(*args, **kwargs)
        return wrapper
    return decorator

@bp.errorhandler(errors.ValidationError)
def handle_mongo_validation_error(error):
    return jsonify(code=400, reason='无效输入：' + str(error))

@bp.errorhandler(Exception)
def handle_all_exceptions(error):
    return jsonify(code=500, reason='Server internal error: ' + str(error))

@bp.route('/user/login', methods=['POST'])
@require('username', 'password')
def login():
    username = request.json['username']
    password = request.json['password']

    udoc = user.User.objects(username=username).first()
    if udoc and hash(password, udoc['salt']) == udoc['password_hash']:
        session.permanent = True
        session['id'] = str(udoc['id'])
        session['role'] = udoc['role']
        return jsonify(code=200, data=udoc)
    else:
        return jsonify(code=401, reason='用户名或密码错误')

@bp.route('/user/logout')
@check_roles()
def logout():
    session.pop('id', None)
    session.pop('role', None)
    return jsonify(code=200)

@bp.route('/user/status')
@check_roles()
def status():
    udoc = user.User.objects(id=ObjectId(session['id'])).first()
    return jsonify(code=200, data=udoc)

@bp.route('/user/changePassword', methods=['POST'])
@require('password')
@check_roles()
def change_password():
    password = request.json['password']
    if not password:
        return jsonify(code=402, reason='密码不能为空')

    udoc = user.User.objects(id=ObjectId(session['id'])).first()

    salt = os.urandom(16)
    password_hash = hash(password, salt)
    udoc['salt'] = salt
    udoc['password_hash'] = password_hash
    udoc['first'] = False
    udoc.save()

    return jsonify(code=200)

@bp.route('/assignment')
@check_roles()
def show_assignment_list():
    adocs = (assignment.Assignment
        .objects(visible=True)
        .order_by('-end_at')
        .all())
    return jsonify(code=200, data=adocs)

@bp.route('/assignment/<string:assignment_id>')
@check_roles()
def show_assignment_detail(assignment_id):
    adoc = (assignment.Assignment
        .objects(id=ObjectId(assignment_id),
                 visible=True)
        .first())
    if not adoc:
        return jsonify(code=403, reason='作业未找到')
    if datetime.datetime.now() < adoc.begin_at:
        return jsonify(code=403, reason='作业还未开放')

    adoc = adoc.to_mongo()
    adoc['problems'] = problem.Problem.objects(
        assignment_id=assignment_id,
        visible=True).order_by('+order').all()
    adoc['submissions'] = submission.Submission.objects(
        user_id=ObjectId(session['id']),
        assignment_id=assignment_id).all()

    return jsonify(code=200, data=adoc)

@bp.route('/assignment/<string:assignment_id>/<string:problem_id>')
@check_roles()
def show_problem(assignment_id, problem_id):
    adoc = (assignment.Assignment
        .objects(id=ObjectId(assignment_id),
                 visible=True)
        .first())
    if not adoc:
        return jsonify(code=403, reason='作业未找到')
    if datetime.datetime.now() < adoc.begin_at:
        return jsonify(code=403, reason='作业还未开放')

    pdoc = problem.Problem.objects(
        id=ObjectId(problem_id),
        assignment_id=assignment_id,
        visible=True).first()
    if not pdoc:
        return jsonify(code=403, reason='题目未找到')

    pdoc = pdoc.to_mongo()
    pdoc['submission'] = submission.Submission.objects(
        user_id=ObjectId(session['id']),
        assignment_id=assignment_id,
        problem_id=problem_id).first()
    pdoc['read_only'] = (datetime.datetime.now() > adoc.end_at)
    return jsonify(code=200, data=pdoc)

@bp.route('/assignment/<string:assignment_id>/<string:problem_id>', methods=['POST'])
@require('answers')
@check_roles()
def submit_problem(assignment_id, problem_id):
    now = datetime.datetime.now()

    adoc = assignment.Assignment.objects(
        id=ObjectId(assignment_id),
        visible=True).first()
    if not adoc:
        return jsonify(code=403, reason='作业未找到')
    if now < adoc.begin_at:
        return jsonify(code=403, reason='作业还未开放')
    if now > adoc.end_at:
        return jsonify(code=403, read_only=True, reason='作业已过截止时间')

    pdoc = problem.Problem.objects(
        id=ObjectId(problem_id),
        assignment_id=assignment_id,
        visible=True).first()
    if not pdoc:
        return jsonify(code=403, reason='题目未找到')

    answers = request.json['answers']
    adocs = [answer.Answer(
        question_id=adoc['question_id'],
        text=adoc['text']) for adoc in answers]

    sdoc = (submission.Submission
        .objects(user_id=ObjectId(session['id']),
                 assignment_id=assignment_id,
                 problem_id=problem_id)
        .upsert_one(set_on_insert__created_at=now,
                    set__updated_at=now,
                    set__answers=adocs))

    shdoc = submission_history.SubmissionHistory(
        submit_at=now,
        user_id=ObjectId(session['id']),
        assignment_id=assignment_id,
        problem_id=problem_id,
        answers=adocs)
    shdoc.save()

    return jsonify(code=200, data=sdoc)

@bp.route('/assignment/history/list/<string:assignment_id>/<string:problem_id>')
@check_roles()
def show_submission_history_list(assignment_id, problem_id):
    sbdocs = (submission_history.SubmissionHistory
        .objects(user_id=ObjectId(session['id']),
                 assignment_id=assignment_id,
                 problem_id=problem_id)
        .order_by('-submit_at')
        .exclude('answers')
        .all())
    return jsonify(code=200, data=sbdocs)

@bp.route('/assignment/history/detail/<string:history_id>')
@check_roles()
def show_submission_history_detail(history_id):
    sbdoc = (submission_history.SubmissionHistory
        .objects(id=history_id,
                 user_id=ObjectId(session['id']))
        .first())
    return jsonify(code=200, data=sbdoc)

@bp.route('/manage/user')
@check_roles([role.ADMIN])
def show_users():
    udocs = user.User.objects().all()
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
        return jsonify(code=402, reason='Username cannot be empty.')

    if not password:
        return jsonify(code=402, reason='Password cannot be empty.')

    udoc = user.User.objects(username=username).first()
    if udoc:
        return jsonify(code=411, reason='User already exist.')

    udoc = user.User(username=username, password_hash=password_hash, salt=salt, role=role, first=True)
    udoc.save()

    return jsonify(code=200)

@bp.route('/manage/assignment')
@check_roles([role.ADMIN, role.TA])
def show_assignment_manage_list():
    adocs = assignment.Assignment.objects().all()
    return jsonify(code=200, data=adocs)

@bp.route('/manage/create/assignment', methods=['POST'])
@require('name', 'begin_at', 'end_at', 'visible')
@check_roles([role.ADMIN, role.TA])
def create_assignment():
    name = request.json['name']
    if not name:
        return jsonify(code=402, reason='Name cannot be empty.')

    try:
        begin_at = datetime.datetime.fromtimestamp(request.json['begin_at'] / 1000)
        end_at = datetime.datetime.fromtimestamp(request.json['end_at'] / 1000)
    except:
        return jsonify(code=403, reason='Invalid datetime.')

    if begin_at > end_at:
        return jsonify(code=403, reason='Invalid datetime, begin_at should be less than end_at.')

    adoc = assignment.Assignment(
        name=name,
        begin_at=begin_at,
        end_at=end_at,
        visible=request.json['visible'])
    adoc.save()

    return jsonify(code=200, data=adoc)

@bp.route('/manage/update/assignment/<string:assignment_id>', methods=['POST'])
@require('name', 'begin_at', 'end_at', 'visible')
@check_roles([role.ADMIN, role.TA])
def update_assignment(assignment_id):
    name = request.json['name']
    if not name:
        return jsonify(code=402, reason='Name cannot be empty.')

    try:
        begin_at = datetime.datetime.fromtimestamp(request.json['begin_at'] / 1000)
        end_at = datetime.datetime.fromtimestamp(request.json['end_at'] / 1000)
    except:
        return jsonify(code=403, reason='Invalid datetime.')

    if begin_at > end_at:
        return jsonify(code=403, reason='Invalid datetime, begin_at should be less than end_at.')

    adoc = assignment.Assignment.objects(id=ObjectId(assignment_id)).first()
    if not adoc:
        return jsonify(code=403, reason='Invalid assignment')

    adoc['name'] = name
    adoc['begin_at'] = begin_at
    adoc['end_at'] = end_at
    adoc['visible'] = request.json['visible']
    adoc.save()

    return jsonify(code=200, data=adoc)

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
def manage_get_assignment(assignment_id):
    adoc = assignment.Assignment.objects(id=ObjectId(assignment_id)).first()
    if adoc:
        adoc = adoc.to_mongo()
        adoc['problems'] = problem.Problem.objects(
            assignment_id=assignment_id).order_by('+order').all()
    return jsonify(code=200, data=adoc)

def get_submission_status(sdoc, qdocs):
    n = 0
    adocs_by_qid = { str(adoc.question_id): adoc for adoc in sdoc.answers }
    for qdoc in qdocs:
        if str(qdoc._id) in adocs_by_qid and len(adocs_by_qid[str(qdoc._id)].text.strip()) >= 1:
            n = n + 1
    return n / len(qdocs)

@bp.route('/manage/assignment/<string:assignment_id>/submissions')
@check_roles([role.ADMIN, role.TA])
def manage_get_assignment_submissions(assignment_id):
    adoc = (assignment.Assignment
        .objects(id=assignment_id)
        .first())
    pdocs = (problem.Problem
        .objects(assignment_id=assignment_id)
        .order_by('+order')
        .exclude('text')
        .exclude('questions.text')
        .all())
    pdocs_by_id = { str(pdoc.id): pdoc for pdoc in pdocs }
    udocs = (user.User
        .objects()
        .order_by('+_id')
        .all())
    udocs_by_id = { str(udoc.id): udoc for udoc in udocs }
    sdocs = (submission.Submission
        .objects(assignment_id=assignment_id)
        .all())

    ssdocs = [{
        '_id': str(sdoc.id),
        'problem_id': str(sdoc.problem_id),
        'user_id': str(sdoc.user_id),
        'complete': get_submission_status(sdoc, pdocs_by_id[str(sdoc.problem_id)].questions),
    } for sdoc in sdocs]

    data = {}
    data['adoc'] = adoc
    data['ssdocs'] = ssdocs
    data['pdocs'] = pdocs
    data['udocs'] = udocs

    return jsonify(code=200, data=data)

@bp.route('/manage/submission/<string:submission_id>')
@check_roles([role.ADMIN, role.TA])
def manage_get_submission(submission_id):
    sdoc = (submission.Submission
        .objects(id=submission_id)
        .first())
    if not sdoc:
        return jsonify(code=403, reason='Invalid submission')
    udoc = (user.User
        .objects(id=sdoc.user_id)
        .first())
    if not udoc:
        return jsonify(code=403, reason='Broken submission. User not found.')
    adoc = (assignment.Assignment
        .objects(id=sdoc.assignment_id)
        .first())
    if not adoc:
        return jsonify(code=403, reason='Broken submission. Assignment not found.')
    pdoc = (problem.Problem
        .objects(id=sdoc.problem_id)
        .first())
    if not pdoc:
        return jsonify(code=403, reason='Broken submission. Problem not found.')

    data = {};
    data['sdoc'] = sdoc
    data['adoc'] = adoc
    data['pdoc'] = pdoc
    data['udoc'] = udoc

    return jsonify(code=200, data=data)

@bp.route('/manage/create/problem/<string:assignment_id>', methods=['POST'])
@require('order', 'text', 'questions', 'visible')
@check_roles([role.ADMIN, role.TA])
def create_problem(assignment_id):
    questions = request.json['questions']
    qdocs = [question.Question(_id=q['_id'], text=q['text']) for q in questions]
    pdoc = problem.Problem(
        order=int(request.json['order']),
        assignment_id=ObjectId(assignment_id),
        text=request.json['text'],
        questions=qdocs,
        visible=request.json['visible'])
    pdoc.save()
    return jsonify(code=200, data=pdoc)

@bp.route('/manage/update/problem/<string:problem_id>', methods=['POST'])
@require('questions', 'text', 'order', 'visible')
@check_roles([role.ADMIN, role.TA])
def update_problem(problem_id):
    questions = request.json['questions']
    pdoc = problem.Problem.objects(id=ObjectId(problem_id)).first()
    if not pdoc:
        return jsonify(code=403, reason='Invalid problem')
    pdoc['order'] = request.json['order']
    pdoc['visible'] = request.json['visible']
    pdoc['text'] = request.json['text']
    pdoc['questions'] = [question.Question(_id=q['_id'], text=q['text']) for q in questions]
    pdoc.save()
    return jsonify(code=200, data=pdoc)

@bp.route('/manage/delete/problem/<string:problem_id>', methods=['POST'])
@require()
@check_roles([role.ADMIN, role.TA])
def delete_problem(problem_id):
    pdoc = problem.Problem.objects(id=ObjectId(problem_id)).first()
    if not pdoc:
        return jsonify(code=403, reason='Invalid problem')
    pdoc.delete()
    return jsonify(code=200)

@bp.route('/manage/rearrange/problem', methods=['POST'])
@require('problems')
@check_roles([role.ADMIN, role.TA])
def rearrange_problem():
    problems = request.json['problems']
    for p in problems:
        pdoc = problem.Problem.objects(id=ObjectId(p['_id'])).first()
        if pdoc:
            pdoc['order'] = p['order']
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
