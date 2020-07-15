#coding:utf8 -*-
from flask import Blueprint,request,session,redirect,make_response
from flask import render_template,url_for
from datetime import timedelta
import time
from .models import Users,Admin_Log
from .forms import LoginForm
from .decorators import login_required,admin_auth
from exts import db
from io import BytesIO
import config
import memcache
from utils.captcha import create_validate_code

bp = Blueprint('admin',__name__,url_prefix='/admin')

@bp.route('/login',methods=['GET','POST'])
def login():
    error = None
    if request.method == 'GET':
        return render_template('admin/login.html')
    else:
        form = LoginForm(request.form)
        if form.validate():
            captcha = request.form.get('captcha')
            user = request.form.get('username')
            pwd = request.form.get('password')
            online = request.form.get('online')
            mc = memcache.Client(['192.168.75.60:11220'],debug=True)
            if mc.get('image'):
                captcha_code = mc.get('image').lower()
            else:
                captcha_code = str(session.get('image')).lower()
            if captcha_code != captcha.lower():
                return render_template('admin/login.html',message = '验证码错误!')
            else:
                users = Users.query.filter_by(username = user).first()
                if users:
                    if user == users.username and users.check_password(pwd):
                        session[config.ADMIN_USER_ID] = users.uid
                        #纪录操作，生成日志
                        user_id = session.get(config.ADMIN_USER_ID)
                        op_log = Admin_Log(
                            admin_id=user_id,
                            ip=request.remote_addr,
                            time=time.time(),
                            operate='用户：' + users.username + '进行了登录操作！'
                        )
                        db.session.add(op_log)
                        db.session.commit()
                        #保持登录状态
                        if online:
                            #虚拟环境中是以venv\Lib\site-packages\flask\app.py里的默认permanent_session_lifetime决定的！MD卡了好久
                            session.permanent = True
                            bp.permanent_session_lifetime = timedelta(days=5)
                        return redirect(url_for('admin.index'))
                    else:
                        error = '用户名或密码错误!'
                        return render_template('admin/login.html',message = error)
                else:
                    return render_template('admin/login.html',message = '该用户不存在！')
        else:
            if 'username' in form.errors:
                if 'password' in form.errors:
                    message = form.errors['username'] + form.errors['password']
                    result = message[0] + '且' + message[1]
                    return render_template('admin/login.html',message = result)
                else:
                    message = form.errors['username']
                    result = message[0]
                    return render_template('admin/login.html',messags = result)
            else:
                message = form.errors['password']
                result = message[0]
                return render_template('admin/login.html',message = result)
@bp.route('/')
@login_required
def index():
    return render_template('admin/index.html')

@bp.route('/code')
def get_code():
    code_img, strs = create_validate_code()
    buf = BytesIO()
    code_img.save(buf,'JPEG')
    buf_str = buf.getvalue()
    response = make_response(buf_str)
    response.headers['Content-Type'] = 'image/jpeg'
    session['image'] = strs
    mc = memcache.Client(['192.168.75.60:11220'],debug=True)
    if mc.get('image') == None:
        mc.add('image',strs,time=300)
    else:
        mc.replace('image',strs,time=300)
    return response

#登录页视图
@bp.route('/welcome')
@login_required
def welcome():
    return render_template('admin/welcome.html')

#注销函数
@bp.route('/logout')
@login_required
def logout():
    #纪录操作，生成日志
    user_id = session.get(config.ADMIN_USER_ID)
    users = Users.query.filter(Users.uid == user_id).first()
    op_log = Admin_Log(
        admin_id=user_id,
        ip = request.remote_addr,
        time = time.time(),
        operate='用户：' + users.username + '进行了注销操作'
    )
    db.session.add(op_log)
    db.session.commit()
    session.pop(config.ADMIN_USER_ID,None)
    return redirect(url_for('admin.login'))

#个人信息页视图
@bp.route('/profile')
@login_required
def profile():
    #根据session获取个人信息
    if config.ADMIN_USER_ID in session:
        user_id = session.get(config.ADMIN_USER_ID)
        user = Users.query.get(user_id)
    return render_template('admin/profile.html',user=user)

@bp.route('/editpwd',methods=['GET','POST'])
@login_required
def editpwd():
    if request.method == 'GET':
        return render_template('admin/profile.html')
    else:
        oldpwd = request.form.get('oldpwd')
        newpwd1 = request.form.get('newpwd1')
        newpwd2 = request.form.get('newpwd2')
        print(oldpwd)
        user_id = session.get(config.ADMIN_USER_ID)
        user = Users.query.filter(Users.uid == user_id).first()
        user.password = newpwd1
        db.session.commit()
        return render_template('admin/edit_pwd.html',message = '密码修改成功')