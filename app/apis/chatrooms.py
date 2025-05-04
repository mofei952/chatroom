from datetime import datetime, timedelta, UTC

from flask import current_app, request, url_for
from flask_login import current_user, login_required
from flask_restx import Namespace, Resource, abort, fields, marshal
import jwt
from sqlalchemy import select

from app import db, socketio
from app.models import Chatroom, ChatroomMember, ChatroomMessage, User
from dateutil.relativedelta import relativedelta

ns = Namespace('chatrooms', description='聊天室相关操作')


class TimeAgo(fields.Raw):
    def format(self, value):
        now = datetime.now()
        if now <= value:
            return '刚刚'
        diff = relativedelta(now, value)
        if diff.years > 0:
            return f'{diff.years}年前'
        if diff.months > 0:
            return f'{diff.months}个月前'
        if diff.days > 0:
            return f'{diff.days}天前'
        if diff.hours > 0:
            return f'{diff.hours}小时前'
        if diff.minutes > 0:
            return f'{diff.minutes}分钟前'
        return f'{diff.seconds}秒前'


chatroom_model = ns.model(
    'chatroom model',
    {
        'id': fields.Integer(),
        'name': fields.String(required=True),
        'is_private': fields.Boolean(required=True),
        'last_active_time': TimeAgo(),
    },
)


chatroom_member_model = ns.model(
    'chatroom member model',
    {
        'id': fields.Integer(),
        'name': fields.String(),
        'nickname': fields.String(),
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
            select(Chatroom)
            .where(
                Chatroom.is_deleted.is_(False),
                Chatroom.is_private.is_(False)
                | (
                    Chatroom.is_private.is_(True)
                    & Chatroom.id.in_(
                        select(ChatroomMember.chatroom_id).where(
                            ChatroomMember.user_id == current_user.id
                        )
                    )
                ),
            )
            .order_by(Chatroom.last_active_time.desc())
        ).all()
        return chatrooms

    @ns.expect(chatroom_model)
    @ns.marshal_with(chatroom_model)
    def post(self):
        """创建聊天室"""
        data = ns.payload
        name, is_private = data['name'], data['is_private']

        chatroom = db.session.scalars(
            select(Chatroom).where(
                Chatroom.name == name, Chatroom.is_deleted.is_(False)
            )
        ).first()
        if chatroom:
            abort(400, '该名称已经被使用')

        user_id = current_user.id
        chatroom = Chatroom(name=name, is_private=is_private, creator_id=user_id)
        db.session.add(chatroom)
        db.session.flush()

        chatroom_member = ChatroomMember(chatroom_id=chatroom.id, user_id=user_id)
        db.session.add(chatroom_member)

        db.session.commit()

        return chatroom


@login_required
@ns.route('/<int:chatroom_id>/members')
class ChatroomMembers(Resource):
    @ns.marshal_with(chatroom_member_model)
    def get(self, chatroom_id):
        """查询聊天室的成员列表"""
        members = db.session.scalars(
            select(User).where(
                User.id.in_(
                    select(ChatroomMember.user_id).where(
                        ChatroomMember.chatroom_id == chatroom_id,
                        ChatroomMember.is_deleted.is_(False),
                    )
                )
            )
        ).all()
        return members


@login_required
@ns.route('/<int:chatroom_id>/invitation_link')
class ChatroomInvitationLink(Resource):
    def get(self, chatroom_id):
        """生成聊天室的邀请链接"""
        valid_days = int(request.args.get('valid_days'))
        if valid_days > 365:
            abort(400, '有效期最长为365天')

        payload = {
            'chatroom_id': chatroom_id,
            'exp': datetime.now(UTC) + timedelta(days=valid_days),
        }
        key = current_app.config['SECRET_KEY']
        join_token = jwt.encode(payload, key, algorithm='HS256')
        print(join_token, type(join_token))

        return url_for('web.index', join_token=join_token, _external=True)


@login_required
@ns.route('/join')
class JoinChatroom(Resource):
    @ns.marshal_with(chatroom_model)
    def post(self):
        """通过邀请链接加入聊天室"""
        join_token = request.json.get('join_token')

        try:
            key = current_app.config['SECRET_KEY']
            payload = jwt.decode(join_token.encode(), key, algorithms='HS256')
        except jwt.ExpiredSignatureError:
            abort(400, '邀请链接已过期')

        chatroom_id = payload['chatroom_id']
        chatroom = db.session.scalars(
            select(Chatroom).where(Chatroom.id == chatroom_id)
        ).first()
        if not chatroom:
            abort(400, '该聊天室不存在')

        # 添加新成员
        user_id = current_user.id
        chatroom_member = ChatroomMember(chatroom_id=chatroom_id, user_id=user_id)
        db.session.add(chatroom_member)

        # 新增“新成员加入聊天室”的系统消息
        message = ChatroomMessage(
            content=f'新成员【{current_user.name}】加入了聊天室',
            chatroom_id=chatroom_id,
        )
        db.session.add(message)

        # 更新聊天室活跃时间
        chatroom.last_active_time = datetime.now()

        db.session.commit()

        # 发送实时消息
        send_room_message(message)

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
        """聊天室发送消息"""
        chatroom = db.session.scalars(
            select(Chatroom).where(Chatroom.id == chatroom_id)
        ).first()
        if not chatroom:
            abort(400, '该聊天室不存在')

        # 添加消息记录
        content = request.form.get('content')
        message = ChatroomMessage(
            content=content,
            sender_id=current_user.id,
            chatroom_id=chatroom_id,
        )
        db.session.add(message)

        # 更新聊天室活跃时间
        chatroom.last_active_time = datetime.now()

        db.session.commit()

        # 发送实时消息
        send_room_message(message)
