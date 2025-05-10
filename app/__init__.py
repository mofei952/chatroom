#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Author  : mofei
# @Time    : 2018/10/1 15:53
# @File    : __init__.py.py
# @Software: PyCharm

from threading import Thread
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()
async_mode = None
redis_client = FlaskRedis(decode_responses=True)


def create_app():
    app = Flask(__name__)
    app.config.from_object('config')

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app, async_mode=async_mode)
    redis_client.init_app(app)

    from app.apis import bp as api_bp
    from app.views import bp as web_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    from app.apis.socketio import check_inactive_users
    Thread(target=check_inactive_users, daemon=True).start()
    
    return app
