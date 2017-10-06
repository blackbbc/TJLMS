# -*- coding: utf-8 -*-

from mongoengine import *

from model import question

class Problem(Document):
    order = IntField()
    assignment_id = ObjectIdField()
    text = StringField()
    questions = ListField(EmbeddedDocumentField(question.Question))
    visible = BooleanField()
    meta = {
        'indexes': [
            ('assignment_id', 'visible', 'order'),
        ]
    }
