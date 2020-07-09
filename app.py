#coding:utf8 -*-
from flask import Flask
from exts import db
from apps.admin import bp as admin_bp
from apps.front import bp as front_bp
from apps.common import bp as common_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(admin_bp)
    app.register_blueprint(front_bp)
    app.register_blueprint(common_bp)
    app.config.from_object('config')
    db.init_app(app)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run()