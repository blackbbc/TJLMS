# -*- coding: utf-8 -*-

from mongoengine import *

from model import question

class Problem(Document):
    order = IntField()
    assignment_id = ObjectIdField()
    text = StringField()
    questions = ListField(EmbeddedDocumentField(question.Question))

    def to_json(self):
        return {
            'id': str(self['id']),
            'order': self['order'],
            'text': self['text'],
            'questions': [qdoc.to_json() for qdoc in self['questions']]
        }
