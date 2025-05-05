from datetime import datetime

from flask import request
from flask_login import current_user, login_required
from flask_restx import Namespace, Resource, abort, fields, marshal
from sqlalchemy import select, update

from app import db, socketio
from app.apis.serializer import TimeAgo
from app.apis.socketio import user_id_and_sid_list
from app.models import FriendMessage, Friendships, User

ns = Namespace('friends', description='好友相关操作')

friend_model = ns.model(
    'friend model',
    {
        'id': fields.Integer(attribute='friend_id'),
        'name': fields.String(attribute='friend_name'),
        'last_active_time': TimeAgo()
    },
)

friend_message_model = ns.model(
    'friend message model',
    {
        'id': fields.Integer(),
        'type': fields.String(),
        'content': fields.String(),
        'sender_id': fields.Integer(),
        'sender_name': fields.String(),
        'receiver_id': fields.Integer(),
        'created_at': fields.String(),
    },
)


def send_friend_message(message):
    """发送好友消息"""

    # 发送给自己
    sids = [
        user_id_and_sid_list[message.sender_id],
    ]
    # 接收人在线的话要发送
    if message.receiver_id in user_id_and_sid_list:
        sids.append(user_id_and_sid_list[message.receiver_id])

    serialized_message = marshal(message, friend_message_model)
    for sid in sids:
        socketio.send(serialized_message, json=True, room=sid, namespace='/websocket')


def send_friend_recalled_message(message):
    """发送好友撤回消息"""

    # 发送给自己
    sids = [
        user_id_and_sid_list[message.sender_id],
    ]
    # 接收人在线的话要发送
    if message.receiver_id in user_id_and_sid_list:
        sids.append(user_id_and_sid_list[message.receiver_id])

    serialized_message = marshal(message, friend_message_model)
    for sid in sids:
        socketio.emit(
            'message_recalled', serialized_message, room=sid, namespace='/websocket'
        )


@login_required
@ns.route('')
class FriendList(Resource):
    @ns.marshal_with(friend_model)
    def get(self):
        """获取好友列表"""
        friends = db.session.scalars(
            select(Friendships).where(
                Friendships.user_id == current_user.id,
                Friendships.is_deleted.is_(False),
            )
        ).all()
        return friends

    @ns.expect(friend_model)
    @ns.marshal_with(friend_model)
    def post(self):
        """添加好友"""
        data = ns.payload
        friend_name = data['name']

        friend = db.session.scalars(
            select(User).where(User.name == friend_name)
        ).first()
        if not friend:
            abort(400, '找不到此用户')

        friendship = db.session.scalars(
            select(Friendships).where(
                Friendships.user_id == current_user.id,
                Friendships.friend_id == friend.id,
                Friendships.is_deleted.is_(False),
            )
        ).first()
        if friendship:
            abort(409, '你们已经是好友了')

        friendship = Friendships(user_id=current_user.id, friend_id=friend.id)
        db.session.add(friendship)
        friendship = Friendships(user_id=friend.id, friend_id=current_user.id)
        db.session.add(friendship)
        db.session.commit()
        return friend


@login_required
@ns.route('/<int:user_id>/messages')
class FriendMessageList(Resource):
    @ns.marshal_with(friend_message_model)
    def get(self, user_id):
        """获取好友聊天列表"""

        # 最后一条已加载消息的时间
        last_message_time = request.args.get('last_message_time')
        # 加载条数（首次加载20条，之后每次10条）
        limit = 10 if last_message_time else 20

        # 构建基础查询，按照创建时间倒序
        query = (
            select(FriendMessage)
            .where(
                (FriendMessage.sender_id == current_user.id)
                & (FriendMessage.receiver_id == user_id)
                | (FriendMessage.sender_id == user_id)
                & (FriendMessage.receiver_id == current_user.id)
            )
            .order_by(FriendMessage.created_at.desc())
            .limit(limit)
        )

        # 增加创建时间的筛选条件，没有传时间表示首次加载
        if last_message_time:
            last_message_time = datetime.strptime(
                last_message_time, '%Y-%m-%d %H:%M:%S'
            )
            query = query.where(FriendMessage.created_at < last_message_time)

        # 执行查询
        message_list = db.session.scalars(query).all()

        return message_list

    def post(self, user_id):
        """好友发送消息"""
        user = db.session.scalars(
            select(User).where(User.id == user_id)
        ).first()
        if not user:
            abort(400, '该用户不存在')

        # 添加消息记录
        content = request.form.get('content')
        chat = FriendMessage(
            content=content,
            sender_id=current_user.id,
            receiver_id=user_id,
        )
        db.session.add(chat)
        
        # 更新好友关系的活跃时间
        db.session.execute(
            update(Friendships).where(
                (FriendMessage.sender_id == current_user.id)
                & (FriendMessage.receiver_id == user_id)
                | (FriendMessage.sender_id == user_id)
                & (FriendMessage.receiver_id == current_user.id)
            ).values(last_active_time=datetime.now())
        )

        db.session.commit()

        # 发送实时消息
        send_friend_message(chat)


@login_required
@ns.route('/<int:user_id>/messages/<int:message_id>')
class FriendOneMessage(Resource):
    def delete(self, user_id, message_id):
        """撤回好友消息"""
        user = db.session.scalars(
            select(User).where(User.id == user_id)
        ).first()
        if not user:
            abort(400, '该用户不存在')

        message = db.session.scalars(
            select(FriendMessage).where(FriendMessage.id == message_id)
        ).first()
        if not message:
            abort(400, '该消息不存在')

        # 权限检查
        if message.sender_id != current_user.id:
            abort(403, '只能撤回自己发送的消息')

        # 发送时间检查
        now = datetime.now()
        if (now - message.created_at).total_seconds() > 60:
            abort(400, '发送超过1分钟无法撤回')

        # 撤回消息
        message.is_recalled = True
        message.recall_time = now

        db.session.commit()

        # 实时撤回消息
        send_friend_recalled_message(message)
