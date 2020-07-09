#coding:utf8 -*-
from flask import Blueprint

bp = Blueprint('common',__name__)

@bp.route('/common')
def index():
    return '这里是公共部分首页'