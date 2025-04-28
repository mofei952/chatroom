from flask import Blueprint
from flask_restx import Api
from app.apis.chatrooms import ns as chatrooms_ns
from app.apis.friends import ns as friends_ns

bp = Blueprint('api', __name__)
api = Api(
    app=bp,
    version='1.0',
    title='CHATROOM API',
    description='CHATROOM API Document',
    doc='/swagger',
)

api.add_namespace(chatrooms_ns)
api.add_namespace(friends_ns)
