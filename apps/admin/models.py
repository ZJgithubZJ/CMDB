#coding:utf8 -*-
from werkzeug.security import generate_password_hash,check_password_hash
from exts import db
from datetime import datetime

class Users(db.Model):
    __table_name__ = 'user'
    uid = db.Column(db.Integer,primary_key=True,autoincrement=True)
    username = db.Column(db.String(50),nullable=False)
    password = db.Column(db.String(100),nullable=False)
    _password = db.Column(db.String(100),nullable=False)
    email = db.Column(db.String(100),nullable=False,unique=True)
    time = db.Column(db.DateTime(),default=datetime.now)
    __table_args__ = {
        'mysql_charset': 'utf8'
    }
    def __init__(self,username,password,email):
        self.username = username
        self.password = password
        self.email = email

    @property
    def password(self):
        return self._password
    @password.setter
    def password(self,raw_password):
        self._password = generate_password_hash(raw_password)
    def check_password(self,raw_password):
        result = check_password_hash(self._password,raw_password)
        return result