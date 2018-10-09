#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Author  : mofei
# @Time    : 2018/10/2 16:19
# @File    : forms.py
# @Software: PyCharm

from flask_wtf import Form, FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, ValidationError

from app.models import User, ChatRoom


class RegisterForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    password = StringField('password', validators=[DataRequired()])
    confirm_password = StringField('confirm_password', validators=[DataRequired(), EqualTo('password', '密码填入的不一致')])
    submit = SubmitField('提交')

    def validate_name(self, field):
        user = User.query.filter_by(name=field.data).first()
        if user:
            raise ValidationError('该用户名已经被使用')


class CreateChatRoomForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])

    def validate_name(self, field):
        chat_room = ChatRoom.query.filter_by(name=field.data).first()
        if chat_room:
            raise ValidationError('该名称已经被使用')