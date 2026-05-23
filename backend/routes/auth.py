from extensions import db
from models.user import User
from flask import Blueprint, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from utils.response import success, error
from config import Config
import bcrypt
import os
import uuid
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return error('请提供登录信息')

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return error('用户名和密码不能为空')

    user = User.query.filter_by(username=username).first()
    if not user:
        return error('用户名或密码错误')

    if not user.is_active:
        return error('账号已被禁用，请联系管理员')

    if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return error('用户名或密码错误')

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'token_version': user.token_version or 0}
    )
    return success({
        'token': access_token,
        'user': user.to_dict(),
    })


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return error('用户不存在', 404)
    return success(user.to_dict())


@auth_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return error('用户不存在', 404)

    data = request.get_json()
    old_pw = data.get('old_password', '')
    new_pw = data.get('new_password', '')

    if not old_pw or not new_pw:
        return error('请提供旧密码和新密码')

    if len(new_pw) < 6:
        return error('新密码至少6位')

    if not bcrypt.checkpw(old_pw.encode('utf-8'), user.password_hash.encode('utf-8')):
        return error('旧密码错误')

    user.password_hash = bcrypt.hashpw(new_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user.token_version = (user.token_version or 0) + 1
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[auth]: DB error: {e}")
        return error('操作失败', status=500)
    return success(message='密码修改成功')


@auth_bp.route('/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if 'file' not in request.files:
        return error('请选择头像文件')

    file = request.files['file']
    if not file.filename:
        return error('无效的文件')

    ALLOWED = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED:
        return error(f'不支持的文件格式，允许: {", ".join(ALLOWED)}')

    filename = f'avatar_{uuid.uuid4().hex}.{ext}'
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(filepath)

    # 自动压缩到 200x200 以内
    try:
        from PIL import Image
        img = Image.open(filepath)
        max_size = 200
        if img.width > max_size or img.height > max_size:
            ratio = min(max_size / img.width, max_size / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            # 保持原格式
            kwargs = {}
            if ext in ('jpg', 'jpeg'):
                kwargs['quality'] = 85
            img.save(filepath, **kwargs)
    except ImportError:
        pass  # 没有 Pillow 就不压缩

    # 删除旧头像文件
    if user.avatar:
        old_path = os.path.join(Config.UPLOAD_FOLDER, user.avatar)
        if os.path.exists(old_path):
            os.remove(old_path)

    user.avatar = filename
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[auth]: DB error: {e}")
        return error('操作失败', status=500)

    return success(data={'avatar': filename, 'url': f'/uploads/{filename}'})
