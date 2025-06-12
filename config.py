#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Author  : mofei
# @Time    : 2018/9/22 12:49
# @File    : confg.py
# @Software: PyCharm
import os
from os import path

SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret'

basepath = path.abspath(path.dirname(__file__))

DEBUG = True

DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/chatroom?charset=utf8mb4'

SQLALCHEMY_COMMIT_ON_TEARDOWN = True
SQLALCHEMY_TRACK_MODIFICATIONS = True

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')