#coding:utf8 -*-
from flask import Blueprint,request,session,redirect,make_response
from flask import render_template,url_for
from .models import Users
from .forms import LoginForm
from io import BytesIO
import config
import memcache
from utils.captcha import create_validate_code

bp = Blueprint('admin',__name__,url_prefix='/admin')

@bp.route('/login',methods=['GET','POST'])
def login():
    error = None
    if request.method == 'GET':
        return render_template('login.html')
    else:
        form = LoginForm(request.form)
        if form.validate():
            captcha = request.form.get('captcha')
            user = request.form.get('username')
            pwd = request.form.get('password')
            mc = memcache.Client(['192.168.75.60:11220'],debug=True)
            if mc.get('image'):
                captcha_code = mc.get('image').lower()
            else:
                captcha_code = str(session.get('image')).lower()
            if captcha_code != captcha.lower():
                return render_template('login.html',message = '验证码错误!')
            else:
                users = Users.query.filter_by(username = user).first()
                if users:
                    if user == users.username and users.check_password(pwd):
                        session[config.ADMIN_USER_ID] = users.uid
                        print('密码对了...')
                        return redirect(url_for('admin.index'))
                    else:
                        error = '用户名或密码错误！'
                        return render_template('login.html',message = error)
                else:
                    return render_template('login.html',message = '该用户不存在！')
        else:
            if 'username' in form.errors:
                if 'password' in form.errors:
                    message = form.errors['username'] + form.errors['password']
                    result = message[0] + '且' + message[1]
                    return render_template('login.html',message = result)
                else:
                    message = form.errors['username']
                    result = message[0]
                    return render_template('login.html',messags = result)
            else:
                message = form.errors['password']
                result = message[0]
                return render_template('login.html',message = result)
@bp.route('/')
def index():
    return render_template('index.html')

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