from mongoengine import *

from bson.objectid import ObjectId
from model import basedoc

class Question(basedoc.JsonDocument, EmbeddedDocument):
    _id = ObjectIdField(required=True, default=lambda: ObjectId())
    order = IntField()
    text = StringField()

    """
    def to_json(self):
        return {
            'id': str(self._id),
            'order': self['order'],
            'text': self['text'],
        }
    """
