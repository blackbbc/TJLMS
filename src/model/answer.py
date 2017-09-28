# -*- coding: utf-8 -*-

from mongoengine import *

from bson.objectid import ObjectId

class Answer(EmbeddedDocument):
    _id = ObjectIdField(required=True, default=lambda: ObjectId())
    question_id = StringField()
    text = StringField()
    score = IntField(default = 0)
