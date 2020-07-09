#coding:utf8 -*-
from flask import Blueprint,request,session,redirect
from flask import render_template,url_for
from .models import Users
import config

bp = Blueprint('admin',__name__,url_prefix='/admin')

@bp.route('/login',methods=['GET','POST'])
def login():
    error = None
    if request.method == 'GET':
        return render_template('login.html')
    else:
        user = request.form.get('username')
        pwd = request.form.get('password')
        users = Users.query.filter_by(username=user).first()
        if users:
            if user == users.username and users.check_password(pwd):
                session[config.ADMIN_USER_ID] = users.uid
                print('密码正确')
                return redirect(url_for('admin.index'))
            else:
                error = '用户名或密码错误!'
                return render_template('login.html', message=error)
        else:
            return render_template('login.html', message='该用户不存在!')


@bp.route('/')
def index():
    return render_template('index.html')