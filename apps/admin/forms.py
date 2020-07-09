#coding:utf8 -*-
from wtforms import Form
from wtforms import StringField,BooleanField
from wtforms.validators import InputRequired,Length,Email,DataRequired

class LoginForm(Form):
    username = StringField(label='用户名',
                           validators=[
                               DataRequired(message='用户名不能为空'),
                               Length(4,20,message='用户名长度为4~20位')
                           ])
    password = StringField(label='密码',
                           validators=[
                               DataRequired(message='密码不能为空'),
                               Length(6,9,message='密码长度为6~9位')
                           ])