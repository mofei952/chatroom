#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Author  : mofei
# @Time    : 2018/10/1 15:53
# @File    : __init__.py.py
# @Software: PyCharm
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app import views

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config')
    db.init_app(app)
    views.init_app(app)
    return app
