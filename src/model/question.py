from mongoengine import *

from bson.objectid import ObjectId

class Question(EmbeddedDocument):
    _id = StringField(required=True)
    order = IntField()
    text = StringField()
