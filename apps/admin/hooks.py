#coding:utf8 -*-
from flask import g,session
import config
from .views import bp
from .models import Users

@bp.before_request
def before_request():
    if config.ADMIN_USER_ID in session:
        user_id = session.get(config.ADMIN_USER_ID)
        user = Users.query.get(user_id)
        print(user.username)
        if user:
            g.admin_user = user.username