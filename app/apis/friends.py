import json
from flask import request
from flask_login import current_user, login_required
from flask_restx import Namespace, Resource, abort, fields
from sqlalchemy import select

from app import db, socketio
from app.models import Chat, Friendships, FriendChat, User
from app.apis.socketio import user_id_and_sid_list
from app.utils import AlchemyEncoder

ns = Namespace('friends', description='好友相关操作')

friend_model = ns.model(
    'friend model',
    {
        'id': fields.Integer(),
        'name': fields.String(),
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


def send_message(chat):
    """发送个人消息"""
    sids = [
        user_id_and_sid_list[chat.sender_id],
        user_id_and_sid_list[chat.receiver_id],
    ]
    chat.sender_name = chat.sender.name
    for sid in sids:
        socketio.send(
            json.dumps(chat, cls=AlchemyEncoder), room=sid, namespace='/websocket'
        )


@login_required
@ns.route('')
class FriendList(Resource):
    @ns.marshal_with(friend_model)
    def get(self):
        """获取好友列表"""
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
        return friends

    @ns.expect(friend_model)
    @ns.marshal_with(friend_model)
    def post(self):
        """添加好友"""
        data = ns.payload
        friend_name = data['name']

        friend = (
            db.session.execute(select(User).where(User.name == friend_name))
            .scalars()
            .first()
        )
        if not friend:
            abort(400, '找不到此用户')

        friendship = (
            db.session.execute(
                select(Friendships).where(
                    Friendships.user_id == current_user.id,
                    Friendships.friend_id == friend.id,
                )
            )
            .scalars()
            .first()
        )
        if friendship:
            abort(409, '你们已经是好友了')

        friendship = Friendships(user_id=current_user.id, friend_id=friend.id)
        db.session.add(friendship)
        friendship = Friendships(user_id=friend.id, friend_id=current_user.id)
        db.session.add(friendship)
        db.session.commit()
        return friend


@login_required
@ns.route('/<int:user_id>/chats')
class FriendChatList(Resource):
    @ns.marshal_with(chat_model)
    def get(self, user_id):
        """获取好友聊天列表"""
        chat_list = (
            db.session.execute(
                select(FriendChat).where(
                    (FriendChat.sender_id == user_id)
                    | (FriendChat.receiver_id == user_id)
                )
            )
            .scalars()
            .all()
        )
        for chat in chat_list:
            chat.sender_name = chat.sender.name
        return chat_list

    def post(self, user_id):
        """好友发送内容"""
        content = request.form.get('content')
        chat = FriendChat(
            content=content,
            sender_id=current_user.id,
            receiver_id=user_id,
        )
        db.session.add(chat)
        db.session.commit()
        send_message(chat)
