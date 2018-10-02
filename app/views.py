#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Author  : mofei
# @Time    : 2018/10/1 15:53
# @File    : view.py
# @Software: PyCharm
import json

from flask import render_template


from app.utils import AlchemyEncoder


def init_app(app):
    @app.route('/')
    def index():
        from app.models import ChatRoom
        chat_room_list = ChatRoom.query.all()
        return render_template('index.html', chat_room_list=chat_room_list)

    @app.route('/get_chat_room_list')
    def get_chat_room_list():
        from app.models import ChatRoom
        chat_room_list = ChatRoom.query.all()
        return json.dumps(chat_room_list, cls=AlchemyEncoder)

    @app.route('/get_friend_list')
    def get_friend_list():
        return json.dumps([])

    @app.route('/get_chat_list/<int:chat_room_id>')
    def get_chat_list(chat_room_id):
        from app.models import Chat
        chat_list = Chat.query.filter_by(chat_room_id=chat_room_id).all()
        return json.dumps(chat_list, cls=AlchemyEncoder)

    def send(chat_room_id, content):
        pass
