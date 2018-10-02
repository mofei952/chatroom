#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Author  : mofei
# @Time    : 2018/10/1 22:13
# @File    : models.py
# @Software: PyCharm


from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)
    profile_picture = db.Column(db.String(50))


class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)


class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class in_chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    enter_time = db.Column(db.DateTime, primary_key=True)
    leave_time = db.Column(db.DateTime, primary_key=True)
    is_chat = db.Column(db.Boolean, primary_key=True)
