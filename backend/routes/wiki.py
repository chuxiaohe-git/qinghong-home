import os
import uuid
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.wiki import WikiDoc
from config import Config
from utils.response import success, error
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

wiki_bp = Blueprint('wiki', __name__, url_prefix='/api/wiki')

ALLOWED_IMG = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}


@wiki_bp.route('/docs', methods=['GET'])
@jwt_required()
def list_docs():
    """获取当前用户所有 WIKI 文档（不含 content）"""
    user_id = int(get_jwt_identity())
    try:
        docs = WikiDoc.query.filter_by(user_id=user_id) \
            .order_by(WikiDoc.sort_order, WikiDoc.created_at.desc()).all()
    except Exception as e:
        logger.error(f"[wiki]: query error: {e}")
        return error('查询失败', status=500)
    return success([d.to_dict(include_content=False) for d in docs])


@wiki_bp.route('/docs/<int:doc_id>', methods=['GET'])
@jwt_required()
def get_doc(doc_id):
    """获取文档详情（含 content）"""
    user_id = int(get_jwt_identity())
    try:
        doc = WikiDoc.query.filter_by(id=doc_id, user_id=user_id).first()
    except Exception as e:
        logger.error(f"[wiki]: query error: {e}")
        return error('查询失败', status=500)
    if not doc:
        return error('文档不存在', 404)
    return success(doc.to_dict(include_content=True))


@wiki_bp.route('/docs', methods=['POST'])
@jwt_required()
def create_doc():
    """创建文档 {title?, content?}"""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    title = data.get('title', '').strip() or '未命名文档'

    try:
        max_order = db.session.query(
            db.func.coalesce(db.func.max(WikiDoc.sort_order), -1)
        ).filter_by(user_id=user_id).scalar()

        doc = WikiDoc(
            user_id=user_id,
            title=title,
            content=data.get('content', ''),
            sort_order=max_order + 1,
        )
        db.session.add(doc)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[wiki]: DB error: {e}")
        return error('操作失败', status=500)
    return success(doc.to_dict(include_content=True), '文档创建成功', 201)


@wiki_bp.route('/docs/<int:doc_id>', methods=['PUT'])
@jwt_required()
def update_doc(doc_id):
    """更新文档 {title?, content?}"""
    user_id = int(get_jwt_identity())
    try:
        doc = WikiDoc.query.filter_by(id=doc_id, user_id=user_id).first()
    except Exception as e:
        logger.error(f"[wiki]: query error: {e}")
        return error('查询失败', status=500)
    if not doc:
        return error('文档不存在', 404)

    data = request.get_json() or {}
    if 'title' in data:
        doc.title = data['title']
    if 'content' in data:
        doc.content = data['content']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[wiki]: DB error: {e}")
        return error('操作失败', status=500)
    return success(doc.to_dict(include_content=True), '文档已更新')


@wiki_bp.route('/docs/<int:doc_id>', methods=['DELETE'])
@jwt_required()
def delete_doc(doc_id):
    """删除文档"""
    user_id = int(get_jwt_identity())
    try:
        doc = WikiDoc.query.filter_by(id=doc_id, user_id=user_id).first()
    except Exception as e:
        logger.error(f"[wiki]: query error: {e}")
        return error('查询失败', status=500)
    if not doc:
        return error('文档不存在', 404)

    try:
        db.session.delete(doc)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[wiki]: DB error: {e}")
        return error('操作失败', status=500)
    return success(message='文档已删除')


@wiki_bp.route('/docs/<int:doc_id>/upload-image', methods=['POST'])
@jwt_required()
def upload_doc_image(doc_id):
    """上传文档图片（粘贴/拖拽插入）"""
    user_id = int(get_jwt_identity())

    try:
        doc = WikiDoc.query.filter_by(id=doc_id, user_id=user_id).first()
    except Exception as e:
        logger.error(f"[wiki]: query error: {e}")
        return error('查询失败', status=500)
    if not doc:
        return error('文档不存在', 404)

    if 'image' not in request.files:
        return error('没有上传文件')

    file = request.files['image']
    if file.filename == '':
        return error('文件名为空')

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'png'
    if ext not in ALLOWED_IMG:
        return error('不支持的图片格式')

    filename = f'{uuid.uuid4().hex}.{ext}'
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(filepath)

    url = f'/uploads/{filename}'
    logger.info(f"[wiki] 图片上传: doc_id={doc_id}, url={url}, user_id={user_id}")
    return success(data={'url': url}, message='图片已上传')
