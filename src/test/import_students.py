# -*- coding: utf-8 -*-
import xlrd
import os
import hashlib, binascii

import model.role
import model.user

from mongoengine import connect

connect('tjlms')

def hash(data, salt):
    return binascii.hexlify(hashlib.pbkdf2_hmac('sha256', data.encode(), salt, 100000)).decode()

def add_student(username, password, realname):
    role = model.role.STUDENT
    salt = os.urandom(16)
    password_hash = hash(password, salt)

    user = model.user.User(username=username, password_hash=password_hash, salt=salt, role=role, realname=realname)
    user.save()
    print(username, realname)

def import_students():
    xls = xlrd.open_workbook("./test/students.xls")

    sh = xls.sheet_by_index(0)
    for rx in range(sh.nrows):
        value = sh.cell_value(rowx=rx, colx=0)
        username = str(int(float(str(value).replace('*', ''))))
        realname = str(sh.cell_value(rowx=rx, colx=1))
        add_student(username, username, realname)

if __name__ == '__main__':
    import_students()
