from flask.json import JSONEncoder

from mongoengine.base import BaseDocument
from mongoengine.queryset.base import BaseQuerySet
from bson.objectid import ObjectId
import datetime
import bson

class MongoJSONEncoder(JSONEncoder):
    def serialize_mongo_doc(self, doc):
        serialize_fields = None
        if '_serializable_fields' in doc:
            serialize_fields = doc._serializable_fields
        return self.serialize_dict(doc.to_mongo(fields=serialize_fields).to_dict())
    def serialize_dict(self, dct):
        ret = {}
        items = dct.items()
        for key, value in items:
            ret[key] = self.serialize(value)
        return ret
    def serialize_list(self, lst):
        ret = []
        for value in lst:
            ret.append(self.serialize(value))
        return ret
    def serialize(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            millis = bson._datetime_to_millis(obj)
            print(millis)
            return millis
        if isinstance(obj, BaseDocument):
            return self.serialize_mongo_doc(obj)
        if isinstance(obj, BaseQuerySet):
            return self.serialize_list([self.serialize_mongo_doc(element) for element in obj])
        if isinstance(obj, (list, tuple)):
            return self.serialize_list(obj)
        if isinstance(obj, dict):
            return self.serialize_dict(obj)
        return obj

    def default(self, obj):
        return self.serialize(obj)
