#coding:utf8 -*-
from functools import wraps
from flask import session,request,url_for,redirect
from .models import Users,Auth,Role
import config

def login_required(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
        if session.get(config.ADMIN_USER_ID):
            return func(*args,**kwargs)
        else:
            return redirect(url_for('admin.login'))
    return wrapper

def admin_auth(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
        user_id = session.get(config.ADMIN_USER_ID)
        admin = Users.query.join(Role).filter(Role.id == Users.role_id,Users.uid == user_id).first()
        auths = admin.jq_role.auths
        auths_list1 = auths.split(',')
        auths_list2 = []
        for i,val1 in enumerate(auths_list1):
            auths_list2.append(int(val1))
        auths_list3 = []
        auth_list = Auth.query.all()
        for i in auth_list:
            for v in auths_list2:
                if v == i.id:
                    auths_list3.append(i.url)
        rule = str(request.url_rule)
        if rule not in auths_list3:
            return '对不起，您无权访问，您拥有的权限为{}，现在访问的为{}'.format(auths_list3,rule)
        return func(*args,**kwargs)
    return wrapper