# -*- coding: utf-8 -*-

from mongoengine import *

from bson.objectid import ObjectId

def json_default(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime.datetime):
        millis = bson._datetime_to_millis(obj)
        return millis
    return obj

class JsonDocument():
    def to_json(self):
        return super().to_json(default=json_default)
