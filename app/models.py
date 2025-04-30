#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Author  : mofei
# @Time    : 2018/10/1 22:13
# @File    : models.py
# @Software: PyCharm


from datetime import datetime

from sqlalchemy import DateTime, Integer

from app import db


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(Integer, primary_key=True)
    created_at = db.Column(DateTime, default=datetime.now)
    updated_at = db.Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(DateTime)

    def delete(self, soft=True):
        if soft:
            self.is_deleted = True
            self.deleted_at = datetime.now()
            db.session.commit()
        else:
            db.session.delete(self)
            db.session.commit()


class User(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)
    profile_picture = db.Column(db.String(50))

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id


class Chatroom(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)


class ChatroomMessage(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    chatroom_id = db.Column(db.Integer, db.ForeignKey('chatroom.id'))

    sender = db.relationship('User', foreign_keys=[sender_id])
    chatroom = db.relationship('Chatroom', backref='chats')

    __table_args__ = (
        db.Index('idx_chatroom_id_create_at', 'chatroom_id', 'created_at'),
    )


class Friendships(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class FriendMessage(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

    __table_args__ = (
        db.Index(
            'idx_sender_receiver_create_at', 'sender_id', 'receiver_id', 'created_at'
        ),
        db.Index('idx_receiver_sender_create_at', 'sender_id', 'created_at'),
    )
