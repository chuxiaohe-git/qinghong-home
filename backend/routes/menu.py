from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.menu import UserMenu
from utils.response import success, error
import logging

logger = logging.getLogger(__name__)

menu_bp = Blueprint('menu', __name__, url_prefix='/api/menu')


@menu_bp.route('', methods=['GET'])
@jwt_required()
def get_menus():
    """获取当前用户的所有菜单"""
    user_id = get_jwt_identity()
    try:
        record = UserMenu.query.filter_by(user_id=user_id).first()
    except Exception as e:
        logger.error(f"[menu]: query error: {e}")
        return error('查询失败', status=500)
    menus = record.menus if record else {}
    return success({'menus': menus})


@menu_bp.route('', methods=['PUT'])
@jwt_required()
def save_menus():
    """保存当前用户的所有菜单"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    menus = data.get('menus', {})

    if not isinstance(menus, dict):
        return error('menus 必须是对象')

    try:
        record = UserMenu.query.filter_by(user_id=user_id).first()
        if record:
            record.menus = menus
        else:
            record = UserMenu(user_id=user_id, menus=menus)
            db.session.add(record)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[menu]: DB error: {e}")
        return error('操作失败', status=500)
    return success({'menus': menus})
