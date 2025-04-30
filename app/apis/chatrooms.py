from datetime import datetime

from flask import request
from flask_login import current_user, login_required
from flask_restx import Namespace, Resource, abort, fields, marshal
from sqlalchemy import select

from app import db, socketio
from app.models import Chatroom, ChatroomMessage

ns = Namespace('chatrooms', description='聊天室相关操作')

chatroom_model = ns.model(
    'chatroom model',
    {
        'id': fields.Integer(),
        'name': fields.String(required=True),
    },
)


chatroom_message_model = ns.model(
    'chatroom message model',
    {
        'id': fields.Integer(),
        'type': fields.String(),
        'content': fields.String(),
        'sender_id': fields.Integer(),
        'sender_name': fields.String(),
        'chatroom_id': fields.Integer(),
        'created_at': fields.String(),
    },
)


def send_room_message(message):
    """发送聊天室消息，进入聊天室的客户端会收到此消息"""
    serialized_message = marshal(message, chatroom_message_model)
    socketio.send(
        serialized_message,
        json=True,
        room='room' + str(message.chatroom_id),
        namespace='/websocket',
    )


@login_required
@ns.route('')
class ChatroomList(Resource):
    @ns.marshal_with(chatroom_model)
    def get(self):
        """获取聊天室列表"""
        chatrooms = db.session.scalars(
            select(Chatroom).where(Chatroom.is_deleted.is_(False))
        ).all()
        return chatrooms

    @ns.expect(chatroom_model)
    @ns.marshal_with(chatroom_model)
    def post(self):
        """创建聊天室"""
        data = ns.payload
        chatroom = db.session.scalars(
            select(Chatroom).where(
                Chatroom.name == data['name'],
                Chatroom.is_deleted.is_(False)
            )
        ).first()
        if chatroom:
            abort(400, '该名称已经被使用')

        chatroom = Chatroom(name=data['name'])
        db.session.add(chatroom)
        db.session.commit()
        return chatroom


@login_required
@ns.route('/<int:chatroom_id>/messages')
class ChatroomMessageList(Resource):
    @ns.marshal_with(chatroom_message_model)
    def get(self, chatroom_id):
        """获取某个聊天室的聊天列表"""

        # 最后一条已加载消息的时间
        last_message_time = request.args.get('last_message_time')
        # 加载条数（首次加载20条，之后每次10条）
        limit = 10 if last_message_time else 20

        # 构建基础查询，按照创建时间倒序
        query = (
            select(ChatroomMessage)
            .where(ChatroomMessage.chatroom_id == chatroom_id)
            .order_by(ChatroomMessage.created_at.desc())
            .limit(limit)
        )

        # 增加创建时间的筛选条件，没有传时间表示首次加载
        if last_message_time:
            last_message_time = datetime.strptime(
                last_message_time, '%Y-%m-%d %H:%M:%S'
            )
            query = query.where(ChatroomMessage.created_at < last_message_time)

        # 执行查询
        message_list = db.session.scalars(query).all()

        return message_list

    def post(self, chatroom_id):
        """聊天室发送内容"""
        content = request.form.get('content')
        message = ChatroomMessage(
            content=content,
            sender_id=current_user.id,
            chatroom_id=chatroom_id,
        )
        db.session.add(message)
        db.session.commit()
        send_room_message(message)
