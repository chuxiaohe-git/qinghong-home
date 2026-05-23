from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.user import User
from models.group import Group
from utils.response import success, error
import bcrypt
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


def require_admin():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return None
    return user


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    admin = require_admin()
    if not admin:
        return error('无权限', 403)

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    pagination = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return success({
        'items': [u.to_dict() for u in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    })


@admin_bp.route('/users', methods=['POST'])
@jwt_required()
def add_user():
    admin = require_admin()
    if not admin:
        return error('无权限', 403)

    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    nickname = data.get('nickname', '').strip()
    role = data.get('role', 'user')

    if not username or not password:
        return error('用户名和密码不能为空')

    if len(password) < 6:
        return error('密码至少6位')

    if User.query.filter_by(username=username).first():
        return error('用户名已存在')

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(username=username, password_hash=hashed,
                nickname=nickname or username, role=role)
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[admin]: DB error: {e}")
        return error('操作失败', status=500)

    return success(user.to_dict(), '用户创建成功', 201)


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def edit_user(user_id):
    admin = require_admin()
    if not admin:
        return error('无权限', 403)

    user = User.query.get(user_id)
    if not user:
        return error('用户不存在', 404)

    data = request.get_json()
    if 'username' in data:
        new_username = data['username'].strip()
        if new_username and new_username != user.username:
            if User.query.filter_by(username=new_username).first():
                return error('用户名已存在')
            user.username = new_username
    if 'nickname' in data:
        user.nickname = data['nickname']
    if 'role' in data:
        user.role = data['role']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[admin]: DB error: {e}")
        return error('操作失败', status=500)
    return success(user.to_dict())


@admin_bp.route('/users/<int:user_id>/toggle', methods=['PUT'])
@jwt_required()
def toggle_user(user_id):
    admin = require_admin()
    if not admin:
        return error('无权限', 403)

    if user_id == admin.id:
        return error('不能禁用自己')

    user = User.query.get(user_id)
    if not user:
        return error('用户不存在', 404)

    user.is_active = not user.is_active
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[admin]: DB error: {e}")
        return error('操作失败', status=500)
    return success(user.to_dict())


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['PUT'])
@jwt_required()
def reset_password(user_id):
    admin = require_admin()
    if not admin:
        return error('无权限', 403)

    user = User.query.get(user_id)
    if not user:
        return error('用户不存在', 404)

    data = request.get_json()
    new_password = data.get('new_password', '')
    if len(new_password) < 6:
        return error('新密码至少6位')

    user.password_hash = bcrypt.hashpw(new_password.encode('utf-8'),
                                        bcrypt.gensalt()).decode('utf-8')
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[admin]: DB error: {e}")
        return error('操作失败', status=500)
    return success(message='密码已重置')


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    admin = require_admin()
    if not admin:
        return error('无权限', 403)

    if user_id == admin.id:
        return error('不能删除自己')

    user = User.query.get(user_id)
    if not user:
        return error('用户不存在', 404)

    # 删除用户的关联数据
    from models.bookmark import Bookmark
    from models.group import Group
    from models.todo import Todo
    from models.setting import Setting
    from models.menu import UserMenu
    from models.gallery import GalleryImage

    Bookmark.query.filter_by(user_id=user_id).delete()
    Group.query.filter_by(user_id=user_id).delete()
    Todo.query.filter_by(user_id=user_id).delete()
    Setting.query.filter_by(user_id=user_id).delete()
    UserMenu.query.filter_by(user_id=user_id).delete()
    GalleryImage.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[admin]: DB error: {e}")
        return error('操作失败', status=500)

    return success(message='用户已删除')
