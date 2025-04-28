#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Author  : mofei
# @Time    : 2018/10/1 15:53
# @File    : __init__.py.py
# @Software: PyCharm

from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()
async_mode = None


def create_app():
    app = Flask(__name__)
    app.config.from_object('config')

    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, async_mode=async_mode)

    from app.views import bp as web_bp
    from app.apis import bp as api_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    return app
