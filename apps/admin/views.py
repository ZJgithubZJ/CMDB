#coding:utf8 -*-
from flask import Blueprint,request,session,redirect,make_response,jsonify
from flask import render_template,url_for
from datetime import timedelta
from sqlalchemy import func
from sqlalchemy import and_
import time
from .models import Users,Admin_Log,Articles_Cat,Articles
from .forms import LoginForm,Article_cat
from .decorators import login_required,admin_auth
from exts import db
from io import BytesIO
from xpinyin import Pinyin
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
        if user:
            return render_template('admin/profile.html',user = user)

@bp.route('/editpwd',methods=['GET','POST'])
@login_required
def editpwd():
    if request.method == 'GET':
        return render_template('admin/edit_pwd.html')
    else:
        oldpwd = request.form.get('oldpwd')
        newpwd1 = request.form.get('newpwd1')
        newpwd2 = request.form.get('newpwd2')
        user_id = session.get(config.ADMIN_USER_ID)
        user = Users.query.filter(Users.uid == user_id).first()
        user.password = newpwd1
        db.session.commit()
        return render_template('admin/edit_pwd.html', message = '密码修改成功！')

@bp.route('/checkpwd')
@login_required
def checkpwd():
    oldpwd = request.args.get('oldpwd')
    if config.ADMIN_USER_ID in session:
        user_id = session.get(config.ADMIN_USER_ID)
        user = Users.query.filter(Users.uid == user_id).first()
        if user.check_password(oldpwd):
            data = {
                'name': user.email,
                'status': 11
            }
        else:
            data = {
                'name': None,
                'status': 00
            }
    return jsonify(data)


def build_tree(data,p_id,level=0):
    '''
    生成树菜单
    :param data: 数据
    :param p_id: 上级分类
    :param level: 当前级别
    :return:
    '''
    tree = []
    for row in data:
        if row['parent_id'] == p_id:
            row['level'] = level
            child = build_tree(data,row['cat_id'],level+1)
            row['child'] = []
            if child:
                row['child'] += child
            tree.append(row)
    return tree

def build_table(data,parent_title='顶级菜单'):
    html = ''
    for row in data:
        splice = '├'
        cat_id = row['cat_id']
        title = splice * row['level'] + row['cat_name']
        tr_td = """<option value={cat_id}>{title}</option>"""
        if row['child']:
            html += tr_td.format(class_name='top_menu', title = title,cat_id = cat_id)
            html += build_table(row['child'],row['cat_name'])
        else:
            html += tr_td.format(class_name='',title=title,cat_id=cat_id)
    return html

@bp.route('/article_cat_add',methods = ['GET','POST'])
@login_required
def article_cat_add():
    if request.method == 'GET':
        categories = Articles_Cat.query.all()
        list = []
        data = {}
        for cat in categories:
            data = dict(cat_id=cat.cat_id,parent_id=cat.parent_id,cat_name=cat.cat_name)
            list.append(data)
        data = build_tree(list,0,0)
        print(data)
        html = build_table(data,parent_title='顶级菜单')
        return render_template('admin/article_cat.html',message=html)
    else:
        form = Article_cat(request.form)
        p = Pinyin()
        dir = request.form.get('dir')
        if form.validate():
            parent_id = request.form.get('parent_id')
            cat_name = request.form.get('cat_name')
            dir = request.form.get('dir')
            check = request.form.get('check')
            if check:
                dir = request.form.get('cat_name')
                dir = p.get_pinyin(dir,'')
            else:
                if dir:
                    dir = request.form.get('dir')
                else:
                    dir = request.form.get('cat_name')
                    dir = p.get_pinyin(dir,'')
            keywords = request.form.get('keywords')
            description = request.form.get('description')
            cat_sort = request.form.get('cat_sort')
            status = request.form.get('status')
            insert = Articles_Cat(parent_id=parent_id,cat_name=cat_name,dir=dir,keywords=keywords,description=description,cat_sort=cat_sort,status=status)
            db.session.add(insert)
            db.session.commit()
            return redirect(url_for('admin.article_cat_list'))
        else:
            #print()
            return '校验没通过'

def create_cat_list(data,parent_title='顶级菜单'):
    html = ''
    for row in data:
        splice = '-- '
        cat_id = row['cat_id']
        cat_sort = row['cat_sort']
        title = splice * row['level'] + row['cat_name']
        description = row['description']
        dir= row['dir']
        tr_td = """
        <tr>
            <td align='left'><a href='article.php?cat_id={cat_id}'></a>{title}</td>
            <td>{dir}</td>
            <td>{description}</td>
            <td align="left">{cat_sort}</td>
            <td align="left"><a href="../article_cat_edit/{cat_id}">编辑</a>|<a href="../article_cat_del/{cat_id}" onClick="red();return false">删除</a></td>
        </tr>
        """
        if row['child']:
            html += tr_td.format(class_name='',title=title,cat_id=cat_id,description=description,dir=dir,cat_sort=cat_sort)
            html += create_cat_list(row['child'],row['cat_name'])
        else:
            html += tr_td.format(class_name='-',title=title,cat_id=cat_id,description= description,dir=dir,cat_sort=cat_sort)
    return html

#栏目列表
@bp.route('/article_cat_list',methods=['GET'])
@login_required
def article_cat_list():
    if request.method == 'GET':
        categories = Articles_Cat.query.all()
        list = []
        data = {}
        for cat in categories:
            data = dict(cat_id = cat.cat_id,parent_id = cat.parent_id,cat_name = cat.cat_name,description = cat.description,dir = cat.dir,cat_sort = cat.cat_sort)
            list.append(data)
        data = build_tree(list,0,0)
        html = create_cat_list(data,parent_title='顶级菜单')
        return render_template('admin/article_cat_list.html',message = html)



@bp.route('/article_list',methods=['GET','POST'])
def article_list():
    if request.method == 'GET':
        rows = db.session.query(Articles).filter(Articles.is_delete == 0).first()
        #获取总记录
        total = db.session.query(func.count(Articles.aid)).filter(Articles.is_delete == 0).scalar()
        #新增分页
        per_page = 3    #每页显示三条
        page = request.args.get('page')
        if not page:
            page = 1
        else:
            page = int(page)
        pagination = Articles.query.filter(Articles.is_delete == 0).order_by(Articles.aid.desc()).paginate(page,per_page,False)
        news1 = pagination.items
        return render_template('admin/article-list.html',pagination=pagination,news1=news1,rows=rows,total=total)














