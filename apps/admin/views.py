#coding:utf8 -*-
from flask import Blueprint,request,session,redirect,make_response,jsonify,flash
from flask import render_template,url_for
from flask_wtf.csrf import generate_csrf
from datetime import timedelta
from sqlalchemy import func
from sqlalchemy import and_
import time
from .models import Users,Admin_Log,Articles_Cat,Articles
from .forms import LoginForm,Article_cat,Article
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
            html += tr_td.format(class_name='top_menu',title=title,cat_id=cat_id)
            html += build_table(row['child'],row['cat_name'])
        else:
            html += tr_td.format(class_name='top_menu',title=title,cat_id=cat_id)
    return html

#添加分类


@bp.route('/article_cat_add',methods = ['GET','POST'])
@login_required
def article_cat_add():
    if request.method == 'GET':
        categories = Articles_Cat.query.all()
        data = {}
        list = []
        for cat in categories:
            data = dict(cat_id=cat.cat_id,cat_name=cat.cat_name,parent_id=cat.parent_id)
            list.append(data)
        data = build_tree(list,0,0)
        html = build_table(data,parent_title='顶级菜单')
        return render_template('admin/article_cat.html',message=html)
    else:
        form = Article_cat(request.form)
        p = Pinyin()
        dir = request.form.get('dir')
        if form.validate():
            parent_id = request.form.get('parent_id')
            cat_name = request.form.get('cat_name')
            dir= request.form.get('dir')
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
            return '校验没通过'


#创建分类列表
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
            <td align="left"><a href="article_cat_edit/{cat_id}">编辑</a>|<a href="article_cat_del/{cat_id}" onClick="rec();return false">删除</a></td>
        </tr>
        """
        if row['child']:
            html += tr_td.format(class_name='',title=title,cat_id=cat_id,description=description,dir=dir,cat_sort=cat_sort)
            html += create_cat_list(row['child'],row['cat_name'])
        else:
            html += tr_td.format(class_name='-',title=title,cat_id=cat_id,description= description,dir=dir,cat_sort=cat_sort)
        #print(html)
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

#编辑分类栏
@bp.route('/article_cat_edit/<id>',methods=['GET'])
@login_required
def article_cat_edit(id):
    if request.method == 'GET':
        cat_list = Articles_Cat.query.filter(Articles_Cat.cat_id == id).first()
        categories = Articles_Cat.query.all()
        list = []
        data = {}
        for cat in categories:
            data = dict(cat_id=cat.cat_id,parent_id=cat.parent_id,cat_name=cat.cat_name)
            list.append(data)
        data = build_tree(list,0,0)
        html = build_table(data,parent_title='顶级菜单')
        return render_template('admin/article_cat_edit.html',content=cat_list,message=html)

@bp.route('/article_cat_del/<id>',methods=['GET','POST'])
@login_required
def article_cat_del(id):
    cat = Articles_Cat.query.filter(Articles_Cat.cat_id == id).first()
    db.session.delete(cat)
    db.session.commit()
    return redirect(url_for('admin.article_cat_list'))

@bp.route('/article_cat_save)',methods=['POST'])
@login_required
def article_cat_save():
    form = Article_cat(request.form)
    p = Pinyin()
    if form.validate():
        cat_id = request.form.get('cat_id')
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
        Articles_Cat.query.filter(Articles_Cat.cat_id == cat_id).update({Articles_Cat.parent_id:parent_id, Articles_Cat.cat_name:cat_name, Articles_Cat.dir:dir,\
                                                                         Articles_Cat.keywords:keywords, Articles_Cat.description:description,Articles_Cat.cat_sort:cat_sort,\
                                                                         Articles_Cat.status:status})
        db.session.commit()
        return redirect(url_for('admin.article_cat_list'))

#文章列表
@bp.route('/article_list',methods=['GET','POST'])
def article_list():
    if request.method == 'GET':
        rows = db.session.query(Articles).filter(Articles.is_delete == 0).all()
        #print(rows)
        #获取总记录
        total = db.session.query(func.count(Articles.aid)).filter(Articles.is_delete == 0).scalar()
        #print(total)
        per_page = 5
        page = request.args.get('page')
        if not page:
            page = 1
        else:
            page = int(page)
        pagination = Articles.query.filter(Articles.is_delete == 0).order_by(Articles.aid).paginate(page,per_page,False)
        #print(pagination.pages)
        news1 = pagination.items
        for i in news1:
            result = Articles_Cat.query.filter(Articles_Cat.cat_id == i.cat_id).first()
            cat_names = result.cat_name
            #print(cat_names)
        return render_template('admin/article-list.html',pagination=pagination,news1=news1,rows=rows,total=total)

#添加文章
@bp.route('/article_add',methods=['GET','POST'])
@login_required
@admin_auth
def article_add():
    if request.method == 'GET':
        categories = Articles_Cat.query.all()
        data = {}
        list = []
        for cat in categories:
            data = dict(cat_id=cat.cat_id,parent_id=cat.parent_id, cat_name=cat.cat_name)
            list.append(data)
        data = build_tree(list,0,0)
        html = build_table(data,parent_title='顶级菜单')
        #print(html)
        return render_template('admin/article-add.html',cat=html)
    else:
        form = Article(request.form)
        if form.validate():
            title = request.form['title']
            shorttitle = request.form['shorttitle']
            cat_id = request.form['cat_id']
            keywords = request.form['keywords']
            description = request.form['description']
            user_id = session.get(config.ADMIN_USER_ID)
            author_id = user_id
            source = request.form['source']
            allowcomments = request.form['allowcomments']
            status = request.form.get('status')
            picture = request.form.get('picture')
            body = request.form['editorValue']
            article1 = Articles(title=title,shorttitle=shorttitle,cat_id=cat_id,keywords=keywords,description=description,author_id=author_id,\
                                source=source,allowcomments=allowcomments,status=status,picture=picture,body=body)
            db.session.add(article1)
            db.session.commit()
            page = 1
            per_page = 3
            rows = Articles.query.filter(Articles.status == 0).all()
            pagination = Articles.query.filter(Articles.is_delete == 0).order_by(Articles.aid.desc()).paginate(page,per_page,False)
            news1 = pagination.items
            return render_template('admin/article-list.html',rows=rows,pagination=pagination,news1=news1)
        else:
            errors = form.errors
            return render_template('admin/article-add.html',errors=errors)

#修改文章
@bp.route('/article_edit/<id>',methods=['GET'])
def article_edit(id):
    if request.method == 'GET':
        article = Articles.query.filter(Articles.aid == id).first()
        categories = Articles_Cat.query.all()
        list = []
        data = {}
        for cat in categories:
            data = dict(cat_id=cat.cat_id,cat_name=cat.cat_name,parent_id=cat.parent_id)
            list.append(data)
        data = build_tree(list,0,0)
        html = build_table(data,parent_title='顶级菜单')
        user = Users.query.filter(Users.uid == article.author_id).first()
        if user:
            username = user.username
        else:
            username = 'admin'
        return render_template('admin/article-edit.html',article=article,username=username,cat=html)

#保存编辑后的文章
@bp.route('/article_edit_save',methods=['POST'])
def article_edit_save():
    if request.method == 'POST':
        form = Article(request.form)
        if form.validate():
            id = request.form['article_id']
            title = request.form['title']
            shorttitle = request.form['shorttitle']
            cat_id = request.form['cat_id']
            keywords = request.form['keywords']
            description = request.form['description']
            author_id = request.form['author_id_new']
            source = request.form['source']
            allowcomments = request.form['allowcomments']
            status = request.form['status']
            picture = request.form['picture']
            body = request.form['editorValue']
            Articles.query.filter(Articles.aid == id).update(
                {Articles.title:title, Articles.shorttitle:shorttitle, Articles.cat_id:cat_id, Articles.keywords:keywords, Articles.description:description,\
                 Articles.author_id:author_id, Articles.source:source, Articles.allowcomments:allowcomments, Articles.status:status, Articles.picture:picture,\
                 Articles.body:body}
            )
            db.session.commit()
            return redirect(url_for('admin.article_list'))
        else:
            flash(form.errors,'error')
            id = request.form['article_id']
            return redirect(url_for('admin.article_edit',id))

#删除单条文章
@bp.route('/article_del',methods=['POST'])
def article_del():
    if request.method == 'POST':
        id = request.values.get('aid')
        db.session.query(Articles).filter(Articles.aid == id).update({Articles.is_delete: 1})
        db.session.commit()
        data = {
            'mes': '保存成功',
            'success': 1
        }
    return jsonify(data)

#批量删除文章
@bp.route('/article_all_del',methods=['POST','GET'])
def article_all_del():
    if request.method == 'POST':
        id = request.values.get('aid')
        articles = db.session.query(Articles).filter(Articles.aid.in_(id)).all()
        for art in articles:
            art.is_delete = 1
            db.session.commit()
        data = {
            'mes': "保存成功",
            'success': 1
        }
    return jsonify(data)

#搜索处理
@bp.route('/search_list',methods=['GET','POST'])
def search_list():
    PAGESIZE = 2
    current_page = 1
    count = 0
    total_page = 0
    if request.method == 'GET':
        current_page = request.args.get('p','')
        key = request.args.get('key','')
        show_shouye_status = 0
        if current_page == '':
            current_page = 1
        else:
            current_page = int(current_page)
            if current_page > 1:
                show_shouye_status = 1
        #获取总记录数
        count = db.session.query(func.count(Articles.aid)).filter(Articles.status == 0).filter(Articles.title.like('%'+key+'%')).scalar()
        #获取分页数
        zone = int(count%PAGESIZE)
        if zone == 0:
            total_page = int(count/PAGESIZE)
        else:
            total_page = int(count/PAGESIZE + 1)
        arts = db.session.query(Articles).filter(Articles.status == 0).filter(Articles.title.like('%'+key+'%')).limit(PAGESIZE).offset((int(current_page) - 1) * PAGESIZE).all()
        data = {
            'user_list': 'admin/search_list',
            'p': int(current_page),
            'total': total_page,
            'count': count,
            'show_shouye_status': show_shouye_status,
            'dic_list': arts
        }
        return render_template('admin/search_list.html',data=data,key=key)

#下架文章
@bp.route('/article_stop',methods=['POST'])
def article_stop():
    di = int(request.values.get('aid'))
    db.session.query(Articles).filter(Articles.aid == id).update({Articles.status: -1})
    data = {
        'msg': '修改成功',
        'success': 1,
        'errors': '错误'
    }
    return jsonify(data)

#资讯审核发布
@bp.route('/article_start',methods=['GET','PPOST'])
def article_start():
    id = int(request.args.get('aid'))
    db.session.query(Articles).filter(Articles.aid == id).update({Articles.status: 0})
    data = {
        'msg': '修改成功',
        'success': 1,
        'errors': '错误'
    }
    return jsonify(data)

@bp.after_request
def after_request(response):
    csrf_token = generate_csrf()
    #通过cookie将值传给前端
    response.set_cookie("csrf_token",csrf_token)
    return response

@bp.route('/test',methods=['GET'])
def test():
    return render_template('admin/test.html')
