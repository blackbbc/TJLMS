# -*- coding: utf-8 -*-

from mongoengine import *

from model import answer
from model import basedoc

class SubmissionHistory(basedoc.JsonDocument, Document):
    user_id = ObjectIdField()
    assignment_id = ObjectIdField()
    problem_id = ObjectIdField()
    answers = ListField(EmbeddedDocumentField(answer.Answer))
