#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Author  : mofei
# @Time    : 2018/10/1 23:01
# @File    : manager.py
# @Software: PyCharm

from app import create_app, socketio

app = create_app()


@app.cli.command('dev')
def dev():
    from livereload import Server

    live_server = Server(app.wsgi_app)
    live_server.watch('**/*.*')
    live_server.serve(open_url=True)


@app.cli.command('test')
def test():
    pass


@app.cli.command('deploy')
def deploy():
    pass


@app.cli.command('init_db')
def init_db():
    from app import db, models

    db.create_all()


@app.cli.command('recreate_db')
def recreate_db():
    """重建数据库，会删除所有数据"""
    from app import db, models

    db.drop_all()
    db.create_all()


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
