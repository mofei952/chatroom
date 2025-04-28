import json
from flask import request
from flask_login import current_user
from flask_socketio import join_room, leave_room, send
from app import socketio


user_id_and_sid_list = {}


@socketio.on('connect', namespace='/websocket')
def connect():
    """客户端连接"""
    user_id_and_sid_list[current_user.id] = request.sid


@socketio.on('join_chat_room', namespace='/websocket')
def join_chat_room(data):
    """客户端加入聊天室"""
    name = data.get('name')
    room = 'room' + str(data.get('room'))
    join_room(room)
    data = {
        'sender_name': 'admin',
        'chat_room_id': data.get('room'),
        'content': name + '进入了聊天室',
    }
    send(json.dumps(data), room=room)


@socketio.on('leave_chat_room', namespace='/websocket')
def leave_chat_room(data):
    """客户端离开聊天室"""
    name = data.get('name')
    room = 'room' + str(data.get('room'))
    leave_room(room)
    data = {
        'sender_name': 'admin',
        'chat_room_id': data.get('room'),
        'content': name + '离开了聊天室',
    }
    send(json.dumps(data), room=room)
