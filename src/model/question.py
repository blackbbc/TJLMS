from mongoengine import *

class Question(EmbeddedDocument):
    text = StringField()
