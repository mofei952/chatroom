#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Author  : mofei
# @Time    : 2018/10/1 23:01
# @File    : manager.py
# @Software: PyCharm
from flask_script import Server, Manager

from app import create_app

app = create_app()
manager = Manager(app)
# server = Server(host="0.0.0.0", port=8001)
manager.add_command('runserver', Server())


@manager.command
def dev():
    from livereload import Server
    live_server = Server(app.wsgi_app)
    live_server.watch('**/*.*')
    live_server.serve(open_url=True)


@manager.command
def test():
    pass


@manager.command
def deploy():
    pass


@manager.command
def init_db():
    from app import db
    from app import models
    db.create_all()


if __name__ == '__main__':
    manager.run()
