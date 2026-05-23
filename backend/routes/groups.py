from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.group import Group
from models.bookmark import Bookmark
from utils.response import success, error
import logging

logger = logging.getLogger(__name__)

groups_bp = Blueprint('groups', __name__, url_prefix='/api/groups')


@groups_bp.route('', methods=['GET'])
@jwt_required()
def list_groups():
    user_id = int(get_jwt_identity())
    try:
        groups = Group.query.filter_by(user_id=user_id).order_by(Group.sort_order).all()
    except Exception as e:
        logger.error(f"[groups]: query error: {e}")
        return error('查询失败', status=500)
    return success([g.to_dict() for g in groups])


@groups_bp.route('', methods=['POST'])
@jwt_required()
def create_group():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    name = data.get('name', '').strip()
    if not name:
        return error('分组名称不能为空')

    try:
        max_sort = db.session.query(db.func.max(Group.sort_order)).filter_by(user_id=user_id).scalar() or 0
        group = Group(user_id=user_id, name=name, sort_order=max_sort + 1)
        db.session.add(group)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[groups]: DB error: {e}")
        return error('操作失败', status=500)
    return success(group.to_dict(), '分组创建成功', 201)


@groups_bp.route('/<int:group_id>', methods=['PUT'])
@jwt_required()
def update_group(group_id):
    user_id = int(get_jwt_identity())
    try:
        group = Group.query.filter_by(id=group_id, user_id=user_id).first()
    except Exception as e:
        logger.error(f"[groups]: query error: {e}")
        return error('查询失败', status=500)
    if not group:
        return error('分组不存在', 404)

    data = request.get_json()
    if 'name' in data:
        group.name = data['name']
    if 'icon' in data:
        group.icon = data['icon']
    if 'display_mode' in data:
        group.display_mode = data['display_mode']
    if 'guest_visible' in data:
        group.guest_visible = bool(data['guest_visible'])
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[groups]: DB error: {e}")
        return error('操作失败', status=500)
    return success(group.to_dict())


@groups_bp.route('/<int:group_id>', methods=['DELETE'])
@jwt_required()
def delete_group(group_id):
    user_id = int(get_jwt_identity())
    try:
        group = Group.query.filter_by(id=group_id, user_id=user_id).first()
    except Exception as e:
        logger.error(f"[groups]: query error: {e}")
        return error('查询失败', status=500)
    if not group:
        return error('分组不存在', 404)

    try:
        Bookmark.query.filter_by(group_id=group_id, user_id=user_id).delete()
        db.session.delete(group)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[groups]: DB error: {e}")
        return error('操作失败', status=500)
    return success(message='分组已删除')


@groups_bp.route('/sort', methods=['PUT'])
@jwt_required()
def sort_groups():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    order = data.get('order', [])
    try:
        for idx, gid in enumerate(order):
            Group.query.filter_by(id=gid, user_id=user_id).update({'sort_order': idx})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[groups]: DB error: {e}")
        return error('操作失败', status=500)
    return success(message='排序已更新')
