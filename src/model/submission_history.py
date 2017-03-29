# -*- coding: utf-8 -*-

from mongoengine import *

from model import answer

class SubmissionHistory(Document):
    user_id = ObjectIdField()
    assignment_id = ObjectIdField()
    problem_id = ObjectIdField()
    answers = ListField(EmbeddedDocumentField(answer.Answer))
    submit_at = DateTimeField()
