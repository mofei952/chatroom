import os
import time

from flask import current_app
from flask_login import current_user, login_required
from flask_restx import Namespace, Resource, fields, reqparse
from werkzeug.datastructures import FileStorage

from app import db

ns = Namespace('users', description='用户相关操作')


user_model = ns.model(
    'user model',
    {
        'id': fields.Integer(),
        'name': fields.String(),
        'nickname': fields.String(),
        'avatar': fields.String(),
    },
)
update_userinfo_parser = reqparse.RequestParser()
update_userinfo_parser.add_argument('nickname', location='form', required=True)
update_userinfo_parser.add_argument(
    'avatar', location='files', type=FileStorage, required=False
)


@login_required
@ns.route('/me')
class Users(Resource):
    @ns.marshal_with(user_model)
    def get(self):
        """获取个人信息"""
        return current_user

    def post(self):
        """修改个人信息"""
        args = update_userinfo_parser.parse_args()
        nickname = args['nickname']
        avatar = args['avatar']
        
        current_user.nickname = nickname
        
        if avatar:
            # 保存头像文件
            save_folder = os.path.join(current_app.root_path, 'media', 'avatar')
            extension = os.path.splitext(avatar.filename)[1]
            save_file_name = str(round(time.time() * 1000)) + extension
            avatar.save(os.path.join(save_folder, save_file_name))
            # 更新头像访问url
            avatar_url = os.path.join('/media/', 'avatar', save_file_name)
            current_user.avatar = avatar_url

        db.session.commit()
