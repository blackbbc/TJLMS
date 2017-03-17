# -*- coding: utf-8 -*-

from mongoengine import *

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired

class User(Document):
    username = StringField()
    password_hash = StringField()
    salt = BinaryField()
    role = StringField()
    student_number = IntField()
    realname = StringField()

    def to_json(self):
        return {
            'username': self['username'],
            'role': self['role'],
            'student_number': self['student_number'],
            'realname': self['realname']
        }

    # def generate_auth_token(self, secret_key, expiration = 600):
    #     s = Serializer(secret_key, expires_in = expiration)
    #     return s.dumps({
    #         'id': str(self['id']),
    #     }).decode()

    # @staticmethod
    # def invalidate():
    #     s = Serializer(secret_key, expires_in = expiration)
    #     return s.dumps({
    #         'id': None
    #     }).decode()

    # @staticmethod
    # def verify_auth_token(token, secret_key):
    #     s = Serializer(secret_key)
    #     try:
    #         data = s.loads(token)
    #     except SignatureExpired:
    #         return None
    #     except BadSignature:
    #         return None
    #     user = User.objects(id=data['id']).first()
    #     return user
