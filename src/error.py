# -*- coding: utf-8 -*-

class Error(Exception):
    @property
    def message(self):
        return "An error has occured."

class LoginError(Error):
    @property
    def message(self):
        return "Invalid username or password."

class UserAlreadyExistError(Error):
    def __init__(self, username):
        self.username = username

    @property
    def message(self):
        return "User {} already exist.".format(self.username)

class FieldEmptyError(Error):
    def __init__(self, field):
        self.field = field

    @property
    def message(self):
        return "Field {} can not be empty.".format(self.field)

class DateTimeInvalidError(Error):
    @property
    def message(self):
        return "Datetime is invalid."
