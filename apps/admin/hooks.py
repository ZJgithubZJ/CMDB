#coding:utf8 -*-
from flask import g,session
import config
from .models import Users
from .views import bp

@bp.before_request
def before_request():
    if config.ADMIN_USER_ID in session:
        user_id = session.get(config.ADMIN_USER_ID)
        user = Users.query.get(user_id)
        if user:
            g.admin_user = user.username