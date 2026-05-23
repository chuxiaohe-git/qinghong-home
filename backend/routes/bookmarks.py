from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.bookmark import Bookmark
from utils.response import success, error
import logging

logger = logging.getLogger(__name__)

bookmarks_bp = Blueprint('bookmarks', __name__, url_prefix='/api/bookmarks')


@bookmarks_bp.route('', methods=['GET'])
@jwt_required()
def list_bookmarks():
    user_id = int(get_jwt_identity())
    group_id = request.args.get('group_id', type=int)
    query = Bookmark.query.filter_by(user_id=user_id)
    if group_id:
        query = query.filter_by(group_id=group_id)
    try:
        bookmarks = query.order_by(Bookmark.sort_order).all()
    except Exception as e:
        logger.error(f"[bookmarks]: query error: {e}")
        return error('查询失败', status=500)
    return success([b.to_dict() for b in bookmarks])


@bookmarks_bp.route('/search', methods=['GET'])
@jwt_required()
def search_bookmarks():
    user_id = int(get_jwt_identity())
    q = request.args.get('q', '').strip()
    if not q:
        return success([])

    try:
        bookmarks = Bookmark.query.filter(
            Bookmark.user_id == user_id,
            Bookmark.title.ilike(f'%{q}%')
        ).order_by(Bookmark.sort_order).all()
    except Exception as e:
        logger.error(f"[bookmarks]: query error: {e}")
        return error('查询失败', status=500)
    return success([b.to_dict() for b in bookmarks])


@bookmarks_bp.route('', methods=['POST'])
@jwt_required()
def create_bookmark():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    title = data.get('title', '').strip()
    url = data.get('url', '').strip()
    group_id = data.get('group_id')

    if not title or not url:
        return error('标题和链接不能为空')
    if not group_id:
        return error('请选择分组')

    # verify group belongs to user
    from models.group import Group
    group = Group.query.filter_by(id=group_id, user_id=user_id).first()
    if not group:
        return error('分组不存在', 404)

    try:
        max_sort = db.session.query(db.func.max(Bookmark.sort_order)).filter_by(
            user_id=user_id, group_id=group_id
        ).scalar() or 0

        bookmark = Bookmark(
            user_id=user_id, group_id=group_id, title=title, url=url,
            description=data.get('description', ''),
            icon=data.get('icon', ''),
            bg_color=data.get('bg_color', ''),
            open_method=data.get('open_method', '_blank'),
            sort_order=max_sort + 1,
        )
        db.session.add(bookmark)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[bookmarks]: DB error: {e}")
        return error('操作失败', status=500)
    return success(bookmark.to_dict(), '收藏创建成功', 201)


@bookmarks_bp.route('/<int:bookmark_id>', methods=['PUT'])
@jwt_required()
def update_bookmark(bookmark_id):
    user_id = int(get_jwt_identity())
    try:
        bookmark = Bookmark.query.filter_by(id=bookmark_id, user_id=user_id).first()
    except Exception as e:
        logger.error(f"[bookmarks]: query error: {e}")
        return error('查询失败', status=500)
    if not bookmark:
        return error('收藏不存在', 404)

    data = request.get_json()
    try:
        for field in ('title', 'url', 'description', 'icon', 'bg_color', 'open_method', 'group_id'):
            if field in data:
                setattr(bookmark, field, data[field])
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[bookmarks]: DB error: {e}")
        return error('操作失败', status=500)
    return success(bookmark.to_dict())


@bookmarks_bp.route('/<int:bookmark_id>', methods=['DELETE'])
@jwt_required()
def delete_bookmark(bookmark_id):
    user_id = int(get_jwt_identity())
    try:
        bookmark = Bookmark.query.filter_by(id=bookmark_id, user_id=user_id).first()
    except Exception as e:
        logger.error(f"[bookmarks]: query error: {e}")
        return error('查询失败', status=500)
    if not bookmark:
        return error('收藏不存在', 404)

    try:
        db.session.delete(bookmark)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[bookmarks]: DB error: {e}")
        return error('操作失败', status=500)
    return success(message='收藏已删除')


@bookmarks_bp.route('/reorder', methods=['PUT'])
@jwt_required()
def reorder_bookmarks():
    """批量调整排序：传入分组 ID 和该分组下书签 ID 的有序数组"""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    group_id = data.get('group_id')
    ids = data.get('ids', [])

    if not group_id or not isinstance(ids, list):
        return error('缺少 group_id 或 ids')

    try:
        # 验证这些书签都属于该用户和该分组
        existing = Bookmark.query.filter(
            Bookmark.id.in_(ids),
            Bookmark.user_id == user_id,
            Bookmark.group_id == group_id
        ).all()

        if len(existing) != len(ids):
            return error('部分书签不存在', 400)

        for sort_order, bid in enumerate(ids):
            Bookmark.query.filter_by(id=bid).update({'sort_order': sort_order})

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[bookmarks]: DB error: {e}")
        return error('操作失败', status=500)
    return success(message='排序已更新')
