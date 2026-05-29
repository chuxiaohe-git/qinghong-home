import os
import uuid
from flask import Blueprint, request, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.gallery import GalleryImage
from models.bookmark import Bookmark
from config import Config
from utils.response import success, error
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

gallery_bp = Blueprint('gallery', __name__, url_prefix='/api/gallery')

ALLOWED = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'ico'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED


@gallery_bp.route('', methods=['GET'])
@jwt_required()
def list_images():
    user_id = int(get_jwt_identity())
    image_type = request.args.get('type', '')  # wallpaper / icon / all
    try:
        query = GalleryImage.query.filter_by(user_id=user_id)
        if image_type and image_type != 'all':
            query = query.filter_by(image_type=image_type)
        images = query.order_by(GalleryImage.created_at.desc()).all()
    except Exception as e:
        logger.error(f"[gallery]: query error: {e}")
        return error('查询失败', status=500)
    return success([img.to_dict() for img in images])


@gallery_bp.route('', methods=['POST'])
@jwt_required()
def upload_image():
    user_id = int(get_jwt_identity())
    if 'file' not in request.files:
        return error('请选择文件')

    file = request.files['file']
    if file.filename == '':
        return error('文件名为空')

    if not allowed_file(file.filename):
        return error('不支持的文件格式')

    image_type = request.form.get('type', 'wallpaper')
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f'{uuid.uuid4().hex}.{ext}'
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)

    file.save(filepath)

    img = GalleryImage(
        user_id=user_id,
        filename=filename,
        original_name=secure_filename(file.filename),
        filepath=filepath,
        image_type=image_type,
    )
    try:
        db.session.add(img)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[gallery]: DB error: {e}")
        return error('操作失败', status=500)

    return success(img.to_dict(), '上传成功', 201)


@gallery_bp.route('/<int:image_id>', methods=['DELETE'])
@jwt_required()
def delete_image(image_id):
    user_id = int(get_jwt_identity())
    try:
        img = GalleryImage.query.filter_by(id=image_id, user_id=user_id).first()
    except Exception as e:
        logger.error(f"[gallery]: query error: {e}")
        return error('查询失败', status=500)
    if not img:
        return error('图片不存在', 404)

    # 删除文件
    if os.path.exists(img.filepath):
        os.remove(img.filepath)

    try:
        db.session.delete(img)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[gallery]: DB error: {e}")
        return error('操作失败', status=500)
    return success(message='图片已删除')


@gallery_bp.route('/<int:image_id>/file', methods=['GET'])
@jwt_required(optional=True)
def serve_image_file(image_id):
    try:
        img = GalleryImage.query.get(image_id)
    except Exception as e:
        logger.error(f"[gallery]: query error: {e}")
        return error('查询失败', status=500)
    if not img:
        return error('图片不存在', 404)
    if os.path.exists(img.filepath):
        return send_from_directory(Config.UPLOAD_FOLDER, img.filename)
    return error('文件不存在', 404)


@gallery_bp.route('/cleanup-unused', methods=['POST'])
@jwt_required()
def cleanup_unused_icons():
    """一键删除当前用户未被任何书签引用的图标（type=icon）"""
    user_id = int(get_jwt_identity())

    try:
        # 1. 获取用户所有 icon 类型的图库记录
        icon_images = GalleryImage.query.filter_by(user_id=user_id, image_type='icon').all()
        if not icon_images:
            return success({'deleted': 0}, '没有需要清理的图标')

        # 2. 获取用户所有书签的 icon 字段值集合
        user_bookmarks = Bookmark.query.filter_by(user_id=user_id).all()
        used_icon_paths = set()
        for bm in user_bookmarks:
            if bm.icon and bm.icon.strip():
                used_icon_paths.add(bm.icon.strip())
                # 同时支持 /uploads/filename 和纯 filename 格式
                if bm.icon.startswith('/uploads/'):
                    used_icon_paths.add(bm.icon[len('/uploads/'):])

        # 3. 筛出未被引用的图标
        deleted_count = 0
        deleted_files = []
        for img in icon_images:
            # 判断该图标是否被任何书签引用
            is_used = False
            possible_refs = [
                f'/uploads/{img.filename}',
                img.filename,
            ]
            for ref in possible_refs:
                if ref in used_icon_paths:
                    is_used = True
                    break

            if not is_used:
                # 删除物理文件
                if os.path.exists(img.filepath):
                    try:
                        os.remove(img.filepath)
                        deleted_files.append(img.filename)
                    except Exception as fe:
                        logger.warning(f"[gallery] 删除文件失败: {img.filepath} - {fe}")
                # 删除数据库记录
                db.session.delete(img)
                deleted_count += 1

        db.session.commit()

        logger.info(f"[gallery] 清理未使用图标: 用户{user_id} 删除了 {deleted_count} 个")
        return success({
            'deleted': deleted_count,
            'files': deleted_files,
        }, f'已清理 {deleted_count} 个未使用的图标')

    except Exception as e:
        db.session.rollback()
        logger.error(f"[gallery] 清理失败: {e}")
        return error(f'清理失败: {str(e)}', status=500)
