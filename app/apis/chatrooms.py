import json

from flask import request
from flask_login import current_user, login_required
from flask_restx import Namespace, Resource, abort, fields

from app import db, socketio
from app.models import Chat, ChatRoom
from app.utils import AlchemyEncoder

ns = Namespace('chatrooms', description='聊天室相关操作')

chatroom_model = ns.model(
    'chatroom model',
    {
        'id': fields.Integer(),
        'name': fields.String(required=True),
    },
)


chat_model = ns.model(
    'chat model',
    {
        'id': fields.Integer(),
        'type': fields.String(),
        'content': fields.String(),
        'sender_id': fields.Integer(),
        'sender_name': fields.String(),
        'receiver_id': fields.Integer(),
        'chat_room_id': fields.Integer(),
    },
)


def send_room_message(chat):
    """发送聊天室消息，进入聊天室的客户端会收到此消息"""
    chat.sender_name = chat.sender.name
    socketio.send(
        json.dumps(chat, cls=AlchemyEncoder),
        room='room' + str(chat.chat_room_id),
        namespace='/websocket',
    )


@login_required
@ns.route('')
class ChatRoomList(Resource):
    @ns.marshal_with(chatroom_model)
    def get(self):
        """获取聊天室列表"""
        chat_room_list = ChatRoom.query.all()
        return chat_room_list

    @ns.expect(chatroom_model)
    @ns.marshal_with(chatroom_model)
    def post(self):
        """创建聊天室"""
        data = ns.payload
        chat_room = ChatRoom.query.filter_by(name=data['name']).first()
        if chat_room:
            abort(400, '该名称已经被使用')

        chat_room = ChatRoom(name=data['name'])
        db.session.add(chat_room)
        db.session.commit()
        return chat_room


@login_required
@ns.route('/<int:chat_room_id>/chats')
class ChatList(Resource):
    @ns.marshal_with(chat_model)
    def get(self, chat_room_id):
        """获取某个聊天室的聊天列表"""
        chat_list = Chat.query.filter_by(chat_room_id=chat_room_id).all()
        for chat in chat_list:
            chat.sender_name = chat.sender.name
        return chat_list

    def post(self, chat_room_id):
        """聊天室发送内容"""
        content = request.form.get('content')
        chat = Chat(
            content=content,
            sender_id=current_user.id,
            chat_room_id=chat_room_id,
        )
        db.session.add(chat)
        db.session.commit()
        send_room_message(chat)
