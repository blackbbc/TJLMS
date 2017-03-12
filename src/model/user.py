# -*- coding: utf-8 -*-

from mongoengine import *

class User(Document):
    username = StringField()
    password_hash = StringField()
    salt = BinaryField()
    role = StringField()
    student_number = IntField()
    realname = StringField()
