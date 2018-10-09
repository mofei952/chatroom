#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Author  : mofei
# @Time    : 2018/10/1 15:53
# @File    : view.py
# @Software: PyCharm

import base64
import json
import random
import threading

import os

import re

import time
from flask import render_template, request, session, redirect, url_for, send_from_directory
from flask_login import login_user, login_required, current_user
from flask_socketio import emit, join_room, send, leave_room

from app import db, login_manager, socketio
from app.forms import RegisterForm, CreateChatRoomForm
from app.models import User, ChatRoom, Chat
from app.utils import AlchemyEncoder


def init_app(app):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """登录"""
        if request.method == 'GET':
            return render_template('login.html')
        else:
            name = request.form.get('name')
            password = request.form.get('password')
            user = User.query.filter_by(name=name, password=password).first()
            if user:
                login_user(user)
                return redirect(url_for('index'))
            else:
                return render_template('login.html')

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """注册"""
        form = RegisterForm()
        if request.method == 'GET':
            return render_template('register.html', form=form)
        else:
            if form.validate_on_submit():
                name = request.form.get('name')
                password = request.form.get('password')
                user = User(name=name, password=password, nickname=name)
                db.session.add(user)
                db.session.commit()
                return redirect(url_for('login'))
            else:
                return render_template('register.html', form=form)

    @app.route('/')
    @login_required
    def index():
        """首页"""
        chat_room_list = ChatRoom.query.all()
        return render_template('index.html', chat_room_list=chat_room_list, form=CreateChatRoomForm())

    @app.route('/get_chat_room_list')
    @login_required
    def get_chat_room_list():
        """获取聊天室列表"""
        chat_room_list = ChatRoom.query.all()
        return json.dumps(chat_room_list, cls=AlchemyEncoder)

    @app.route('/create_chat_room', methods=['POST'])
    @login_required
    def create_chat_room():
        """创建聊天室"""
        form = CreateChatRoomForm()
        if form.validate():
            chat_room = ChatRoom(name=form.data.get('name'))
            db.session.add(chat_room)
            db.session.commit()
        else:
            return json.dumps(form.errors)
        return json.dumps('true')

    @app.route('/get_chat_list/<int:chat_room_id>')
    @login_required
    def get_chat_list(chat_room_id):
        """获取某个聊天室的聊天列表"""
        chat_list = Chat.query.filter_by(chat_room_id=chat_room_id).all()
        for chat in chat_list:
            chat.sender_name = chat.sender.name
        return json.dumps(chat_list, cls=AlchemyEncoder)

    @app.route('/chat_room_send/<int:chat_room_id>', methods=['POST'])
    @login_required
    def chat_room_send(chat_room_id):
        """聊天室发送内容"""
        content = request.form.get('content')
        # import cgi
        # content = cgi.escape(content)
        chat = Chat(
            type='chat_room',
            content=content,
            sender_id=current_user.id,
            chat_room_id=chat_room_id,
        )
        db.session.add(chat)
        db.session.commit()
        send_room_message(chat)
        return json.dumps('true')

    @app.route('/get_friend_list')
    @login_required
    def get_friend_list():
        """获取好友列表，未实现"""
        return json.dumps([])

    @app.route('/get_friend_chat_list/<int:user_id>')
    @login_required
    def get_friend_chat_list(user_id):
        """获取好友聊天列表"""
        chat_list = Chat.query.filter_by(receiver_id=user_id).all()
        return json.dumps(chat_list, cls=AlchemyEncoder)

    @app.route('/friend_send/<int:user_id>', methods=['POST'])
    def friend_send(user_id):
        """好友发送内容"""
        content = request.form.get('content')
        chat = Chat(
            type='chat_room',
            content=content,
            sender_id=current_user.id,
            receiver_id=user_id,
        )
        db.session.add(chat)
        db.session.commit()
        return json.dumps('true')

    user_id_and_sid_list = {}

    @socketio.on('connect', namespace='/websocket')
    def connect():
        """客户端连接"""
        user_id_and_sid_list[current_user.id] = request.sid

    @socketio.on('join_chat_room', namespace='/websocket')
    def join_chat_room(data):
        """客户端加入聊天室"""
        name = data.get('name')
        room = 'room' + str(data.get('room'))
        join_room(room)
        data = {'sender_name': 'admin', 'content': name + '进入了聊天室'}
        send(json.dumps(data), room=room)

    @socketio.on('leave_chat_room', namespace='/websocket')
    def leave_chat_room(data):
        """客户端离开聊天室"""
        name = data.get('name')
        room = 'room' + str(data.get('room'))
        leave_room(room)
        data = {'sender_name': 'admin', 'content': name + '离开了聊天室'}
        send(json.dumps(data), room=room)

    def send_room_message(chat):
        """发送聊天室消息，进入聊天室的客户端会收到此消息"""
        chat.sender_name = chat.sender.name
        chat_room_id = chat.chat_room_id
        chat = json.dumps(chat, cls=AlchemyEncoder)
        socketio.send(chat, room='room' + str(chat_room_id), namespace='/websocket')

    def send_message(receiver_id, content):
        """发送个人消息"""
        sid = user_id_and_sid_list[current_user.id]
        send(content, room=sid)

    @app.route('/upload/', methods=['GET', 'POST'])
    def upload():
        """ueditor请求后端处理，上传图片，上传涂鸦"""
        action = request.args.get('action')
        with open(os.path.join(app.static_folder, 'ueditor', 'php', 'config.json'), encoding='utf-8') as fp:
            try:
                CONFIG = json.loads(re.sub(r'\/\*.*\*\/', '', fp.read()))
            except:
                CONFIG = {}
        if action == 'config':
            result = CONFIG
        elif action == 'uploadimage':
            dir = 'image'
            file = request.files['upfile']
            extension = os.path.splitext(file.filename)[1]
            save_file_name = str(round(time.time() * 1000)) + extension
            save_folder = os.path.join(app.root_path, 'media', dir)
            url = os.path.join('/media/', dir, save_file_name)
            file.save(os.path.join(save_folder, save_file_name))
            result = {
                "state": "SUCCESS",
                "url": url,
                "title": save_file_name,
                "original": file.filename
            }
        elif action == 'uploadscrawl':
            dir = 'scrawl'
            data = request.form['upfile']
            data = base64.b64decode(data)
            extension = '.jpg'
            save_file_name = str(round(time.time() * 1000)) + extension
            save_path = os.path.join(app.root_path, 'media', dir, save_file_name)
            url = os.path.join('/media/', dir, save_file_name)
            with open(save_path, 'wb+') as f:
                f.write(data)
            result = {
                "state": "SUCCESS",
                "url": url,
                "title": save_file_name,
                "original": save_file_name
            }
        return json.dumps(result)

    @app.route('/media/<path:filename>')
    def media_file(filename):
        """访问media下的文件"""
        return send_from_directory('media', filename)
