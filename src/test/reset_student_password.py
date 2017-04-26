import os
import hashlib, binascii

import model.role
import model.user

from mongoengine import connect

connect('tjlms')

def hash(data, salt):
    return binascii.hexlify(hashlib.pbkdf2_hmac('sha256', data.encode(), salt, 100000)).decode()

def add_student():
    username = input('Username:')
    role = model.role.STUDENT
    salt = os.urandom(16)
    password_hash = hash(username, salt)

    udoc = model.user.User.objects(username=username).first()
    if (udoc):
        udoc['password_hash'] = password_hash
        udoc['salt'] = salt
        udoc['first'] = True
        udoc.save()
        print("Reset student password success!")
    else:
        print("Student does not exist!")

if __name__ == '__main__':
    add_student()
