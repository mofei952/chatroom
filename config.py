#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Author  : mofei
# @Time    : 2018/9/22 12:49
# @File    : confg.py
# @Software: PyCharm
from os import path

basepath = path.abspath(path.dirname(__file__))

DEBUG = True

SQLALCHEMY_DATABASE_URI = 'mysql://root:mofei@47.104.222.115:3306/chatroom'
SQLALCHEMY_COMMIT_ON_TEARDOWN = True
SQLALCHEMY_TRACK_MODIFICATIONS = True