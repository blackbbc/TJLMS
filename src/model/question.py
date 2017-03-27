from mongoengine import *

from bson.objectid import ObjectId

class Question(EmbeddedDocument):
    _id = ObjectIdField(required=True, default=lambda: ObjectId())
    order = IntField()
    text = StringField()
