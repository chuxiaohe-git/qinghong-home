import logging

from flask import Blueprint, request

from models.group import Group
from models.bookmark import Bookmark
from models.user import User
from models.setting import Setting
from utils.response import success, error
import json

logger = logging.getLogger(__name__)

guest_bp = Blueprint('guest', __name__, url_prefix='/api/guest')


def _get_admin():
    """获取第一个超级管理员"""
    return User.query.filter_by(role='admin').first()


def _is_guest_mode_enabled(admin):
    """检查管理员是否开启了访客模式"""
    if not admin:
        return False
    setting = Setting.query.filter_by(user_id=admin.id).first()
    if not setting:
        return False
    try:
        config = json.loads(setting.layout_config or '{}')
        return bool(config.get('guest_mode', False))
    except (json.JSONDecodeError, TypeError):
        return False


@guest_bp.route('/status', methods=['GET'])
def guest_status():
    """返回访客模式状态"""
    admin = _get_admin()
    enabled = _is_guest_mode_enabled(admin) if admin else False
    return success(data={
        'enabled': enabled,
        'has_admin': admin is not None,
    })


@guest_bp.route('/groups', methods=['GET'])
def guest_groups():
    """返回访客可见的分组及其书签（无需登录）"""
    admin = _get_admin()
    if not admin or not _is_guest_mode_enabled(admin):
        return success(data=[])

    groups = Group.query.filter_by(
        user_id=admin.id, guest_visible=True
    ).order_by(Group.sort_order).all()

    result = []
    for g in groups:
        bms = Bookmark.query.filter_by(
            user_id=admin.id, group_id=g.id
        ).order_by(Bookmark.sort_order).all()
        result.append({
            'group': g.to_dict(),
            'bookmarks': [b.to_dict() for b in bms],
        })

    return success(data=result)
