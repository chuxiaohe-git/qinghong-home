from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.setting import Setting
from utils.response import success, error
import logging

logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')


@settings_bp.route('', methods=['GET'])
@jwt_required()
def get_settings():
    user_id = int(get_jwt_identity())
    try:
        setting = Setting.query.filter_by(user_id=user_id).first()
        if not setting:
            setting = Setting(user_id=user_id)
            db.session.add(setting)
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[settings]: DB error: {e}")
        return error('操作失败', status=500)
    return success(setting.to_dict())


@settings_bp.route('', methods=['PUT'])
@jwt_required()
def update_settings():
    user_id = int(get_jwt_identity())
    try:
        setting = Setting.query.filter_by(user_id=user_id).first()
        if not setting:
            setting = Setting(user_id=user_id)
            db.session.add(setting)

        data = request.get_json()
        if 'theme' in data:
            setting.theme = data['theme']
        if 'language' in data:
            setting.language = data['language']
        if 'wallpaper' in data:
            setting.wallpaper = data['wallpaper']
        if 'layout_config' in data:
            setting.layout_config = data['layout_config']

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[settings]: DB error: {e}")
        return error('操作失败', status=500)
    return success(setting.to_dict())
