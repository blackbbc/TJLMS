from mongoengine import *

from bson.objectid import ObjectId

class Question(EmbeddedDocument):
    _id = ObjectIdField(required=True, default=lambda: ObjectId())
    text = StringField()

    def to_json(self):
        return {
            'id': str(self._id),
            'text': self['text']
        }
