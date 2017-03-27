# -*- coding: utf-8 -*-

from mongoengine import *

class Assignment(Document):
    name = StringField()
    begin_at = DateTimeField()
    end_at = DateTimeField()
    visible = BooleanField()
