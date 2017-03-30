# -*- coding: utf-8 -*-

from mongoengine import *

from model import answer

class Submission(Document):
    user_id = ObjectIdField()
    assignment_id = ObjectIdField()
    problem_id = ObjectIdField()
    answers = ListField(EmbeddedDocumentField(answer.Answer))
    acc_score = IntField(default = 0)
    created_at = DateTimeField()
    updated_at = DateTimeField()
