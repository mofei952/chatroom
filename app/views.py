#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Author  : mofei
# @Time    : 2018/10/1 15:53
# @File    : view.py
# @Software: PyCharm

import base64
import json
import os
import re
import time

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required, login_user
from flask_wtf import FlaskForm
from sqlalchemy import select
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, ValidationError

from app import db, login_manager
from app.models import ChatRoom, Friendships, User

bp = Blueprint('web', __name__, url_prefix='')


login_manager.login_view = 'web.login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class RegisterForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    password = StringField('password', validators=[DataRequired()])
    confirm_password = StringField(
        'confirm_password',
        validators=[DataRequired(), EqualTo('password', '密码填入的不一致')],
    )
    submit = SubmitField('提交')

    def validate_name(self, field):
        user = User.query.filter_by(name=field.data).first()
        if user:
            raise ValidationError('该用户名已经被使用')


@bp.route('/')
@login_required
def index():
    """首页"""
    chatrooms = db.session.execute(select(ChatRoom)).scalars().all()
    friends = (
        db.session.execute(
            select(User).where(
                User.id.in_(
                    select(Friendships.friend_id).where(
                        Friendships.user_id == current_user.id
                    )
                )
            )
        )
        .scalars()
        .all()
    )
    return render_template(
        'index.html',
        chatrooms=chatrooms,
        friends=friends,
        tab=request.args.get('tab', 'chatroom'),
    )


@bp.route('/login', methods=['GET', 'POST'])
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
            return redirect(url_for('web.index'))
        else:
            return render_template('login.html')


@bp.route('/register', methods=['GET', 'POST'])
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
            return redirect(url_for('web.login'))
        else:
            return render_template('register.html', form=form)


@bp.route('/upload/', methods=['GET', 'POST'])
def upload():
    """ueditor请求后端处理，上传图片，上传涂鸦"""
    action = request.args.get('action')
    with open(
        os.path.join(current_app.static_folder, 'ueditor', 'php', 'config.json'),
        encoding='utf-8',
    ) as fp:
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
        save_folder = os.path.join(current_app.root_path, 'media', dir)
        url = os.path.join('/media/', dir, save_file_name)
        file.save(os.path.join(save_folder, save_file_name))
        result = {
            'state': 'SUCCESS',
            'url': url,
            'title': save_file_name,
            'original': file.filename,
        }
    elif action == 'uploadscrawl':
        dir = 'scrawl'
        data = request.form['upfile']
        data = base64.b64decode(data)
        extension = '.jpg'
        save_file_name = str(round(time.time() * 1000)) + extension
        save_path = os.path.join(current_app.root_path, 'media', dir, save_file_name)
        url = os.path.join('/media/', dir, save_file_name)
        with open(save_path, 'wb+') as f:
            f.write(data)
        result = {
            'state': 'SUCCESS',
            'url': url,
            'title': save_file_name,
            'original': save_file_name,
        }
    return json.dumps(result)


@bp.route('/media/<path:filename>')
def media_file(filename):
    """访问media下的文件"""
    return send_from_directory('media', filename)
