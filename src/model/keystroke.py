# -*- coding: utf-8 -*-

from mongoengine import *

from model import question

class Keystroke(Document):
    assignment_id = ObjectIdField()
    problem_id = ObjectIdField()
    question_id = StringField()
    user_id = ObjectIdField()
    timestamp = IntField()
    event_type = IntField()
    keycode = IntField()
    meta = {
        'indexes': [
            ('user_id', 'question_id', 'event_type', 'timestamp'),
        ]
    }
