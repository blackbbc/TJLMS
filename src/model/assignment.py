# -*- coding: utf-8 -*-

from mongoengine import *
from model import basedoc

class Assignment(basedoc.JsonDocument, Document):
    name = StringField()
    begin_at = DateTimeField()
    end_at = DateTimeField()
    visible = BooleanField()

    """
    def to_json(self):
        return {
            'id': str(self['id']),
            'name': self['name'],
            'begin_at': self['begin_at'].isoformat(),
            'end_at': self['end_at'].isoformat(),
            'visible': self['visible'],
        }
    """
