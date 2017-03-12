# -*- coding: utf-8 -*-

from mongoengine import *

class Answer(EmbeddedDocument):
    question_id = ObjectIdField()
    text = StringField()
    score = IntField(default = 0)
