# -*- coding: utf-8 -*-

from mongoengine import *

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired

class User(Document):
    _serializable_fields = ['username', 'role', 'student_number', 'realname', 'first']
    username = StringField()
    password_hash = StringField()
    salt = BinaryField()
    role = StringField()
    student_number = IntField()
    realname = StringField()
    first = BooleanField(default=True)
