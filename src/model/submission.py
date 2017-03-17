# -*- coding: utf-8 -*-

from mongoengine import *

from model import answer

class Submission(Document):
    user_id = ObjectIdField()
    assignment_id = ObjectIdField()
    problem_id = ObjectIdField()
    answers = ListField(EmbeddedDocumentField(answer.Answer))
    acc_score = IntField(default = 0)

    def to_json(self):
        return {
            'id': str(self['id']),
            'answers': [adoc.to_json() for adoc in self['answers']],
            'acc_score': sum([adoc['score']] for adoc in self['answers'])
        }
