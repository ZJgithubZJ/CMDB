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
class Article_cat(Form):
    parent_id = StringField(validators=[Length(1,20,message='父栏目长度为1-20位')])
    cat_name = StringField(validators=[Length(1,100,message='栏目名字长度为1-100位')])
    dir = StringField(validators=[Length(0,100,message='别名长度为0-100位')])
    keywords = StringField(validators=[Length(1,100,message='关键字长度为1-100位')])
    description = StringField(validators=[Length(1,100,message='栏目描述长度为1-100位')])
    cat_sort = StringField(validators=[Length(1,100,message='栏目排序长度为1-5位')])