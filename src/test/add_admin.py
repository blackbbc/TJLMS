import os
import hashlib, binascii

import model.role
import model.user

from mongoengine import connect

connect('tjlms')

def hash(data, salt):
    return binascii.hexlify(hashlib.pbkdf2_hmac('sha256', data.encode(), salt, 100000)).decode()

def add_admin():
    username = 'admin'
    password = 'admin'
    role = model.role.ADMIN
    salt = os.urandom(16)
    password_hash = hash(password, salt)

    user = model.user.User(username=username, password_hash=password_hash, salt=salt, role=role)
    user.save()

    print("Add admin success!")

if __name__ == '__main__':
    add_admin()
