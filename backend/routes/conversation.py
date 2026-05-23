from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.conversation import Conversation
from utils.response import success, error
import logging

logger = logging.getLogger(__name__)

conversation_bp = Blueprint('conversation', __name__, url_prefix='/api/conversations')


@conversation_bp.route('', methods=['GET'])
@jwt_required()
def list_conversations():
    user_id = int(get_jwt_identity())
    try:
        convs = Conversation.query.filter_by(user_id=user_id)\
            .order_by(Conversation.updated_at.desc()).limit(50).all()
    except Exception as e:
        logger.error(f"[conversation]: query error: {e}")
        return error('查询失败', status=500)
    return success([c.to_dict() for c in convs])


@conversation_bp.route('', methods=['POST'])
@jwt_required()
def create_conversation():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    title = data.get('title', '新对话')
    conv = Conversation(user_id=user_id, title=title)
    try:
        db.session.add(conv)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[conversation]: DB error: {e}")
        return error('操作失败', status=500)
    return success(conv.to_dict())


@conversation_bp.route('/<int:conv_id>', methods=['GET'])
@jwt_required()
def get_conversation(conv_id):
    user_id = int(get_jwt_identity())
    try:
        conv = Conversation.query.filter_by(id=conv_id, user_id=user_id).first()
    except Exception as e:
        logger.error(f"[conversation]: query error: {e}")
        return error('查询失败', status=500)
    if not conv:
        return error('对话不存在', 404)
    return success({
        **conv.to_dict(),
        'messages': conv.get_messages(),
    })


@conversation_bp.route('/<int:conv_id>', methods=['PUT'])
@jwt_required()
def update_conversation(conv_id):
    user_id = int(get_jwt_identity())
    try:
        conv = Conversation.query.filter_by(id=conv_id, user_id=user_id).first()
    except Exception as e:
        logger.error(f"[conversation]: query error: {e}")
        return error('查询失败', status=500)
    if not conv:
        return error('对话不存在', 404)
    data = request.get_json()
    if 'title' in data:
        conv.title = data['title']
    if 'messages' in data:
        conv.set_messages(data['messages'])
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[conversation]: DB error: {e}")
        return error('操作失败', status=500)
    return success(conv.to_dict())


@conversation_bp.route('/<int:conv_id>', methods=['DELETE'])
@jwt_required()
def delete_conversation(conv_id):
    user_id = int(get_jwt_identity())
    try:
        conv = Conversation.query.filter_by(id=conv_id, user_id=user_id).first()
    except Exception as e:
        logger.error(f"[conversation]: query error: {e}")
        return error('查询失败', status=500)
    if not conv:
        return error('对话不存在', 404)
    try:
        db.session.delete(conv)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[conversation]: DB error: {e}")
        return error('操作失败', status=500)
    return success(message='已删除')
