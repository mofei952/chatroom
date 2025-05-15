import time
from datetime import datetime

from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room, send

from app import redis_client, socketio
from app.apis.serializer import ShortTime


@socketio.on('connect', namespace='/websocket')
def connect():
    """客户端连接"""

    # 将当前用户信息存储到redis
    redis_client.hset('online_users', current_user.id, request.sid)
    redis_client.set(f'user:{current_user.id}', 1, ex=60)

    # 广播用户上线通知
    emit(
        'user_online',
        {'user_id': current_user.id, 'username': current_user.name},
        broadcast=True,
    )


@socketio.on('disconnect', namespace='/websocket')
def disconnect():
    """客户端断开连接"""

    # 将当前用户信息从redis中删除
    redis_client.hdel('online_users', current_user.id)

    # 广播用户下线通知
    emit(
        'user_offline',
        {'user_ids': [current_user.id]},
        broadcast=True,
    )


@socketio.on('heartbeat', namespace='/websocket')
def handle_heartbeat():
    """心跳机制保持在线状态"""
    redis_client.set(f'user:{current_user.id}', 1, ex=60)


def check_inactive_users():
    """检查不活跃用户"""
    while True:
        try:
            all_user_ids = redis_client.hkeys('online_users')

            # 统计不活跃用户列表
            inactive_users = []
            for user_id in all_user_ids:
                if not redis_client.exists(f'user:{user_id}'):
                    redis_client.hdel('online_users', user_id)
                    inactive_users.append(user_id)

            # 通知所有客户端这些用户已离线
            if inactive_users:
                socketio.emit(
                    'user_offline',
                    {'user_ids': inactive_users},
                    namespace='/websocket',
                )

        except Exception as e:
            print(f'检查不活跃用户失败：{e}')

        time.sleep(30)


@socketio.on('join_chatroom', namespace='/websocket')
def join_chatroom(data):
    """客户端加入聊天室"""
    room = 'room' + str(data.get('room'))
    join_room(room)
    now = datetime.now()
    message = {
        'chatroom_id': data.get('room'),
        'content': current_user.nickname + '进入了聊天室',
        'created_at': now.strftime('%Y-%m-%d %H:%M:%S'),
        'send_time': ShortTime().format(now),
    }
    send(message, json=True, room=room)


@socketio.on('leave_chatroom', namespace='/websocket')
def leave_chatroom(data):
    """客户端离开聊天室"""
    room = 'room' + str(data.get('room'))
    leave_room(room)
    now = datetime.now()
    message = {
        'chatroom_id': data.get('room'),
        'content': current_user.nickname + '离开了聊天室',
        'created_at': now.strftime('%Y-%m-%d %H:%M:%S'),
        'send_time': ShortTime().format(now),
    }
    send(message, json=True, room=room)
