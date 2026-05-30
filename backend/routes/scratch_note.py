import os
import uuid
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.scratch_note import Notebook, Note
from models.todo import Todo
from config import Config
from utils.response import success, error
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

scratch_note_bp = Blueprint('scratch_note', __name__, url_prefix='/api')


# ═══════════════════════════════════════════
#  Notebook API
# ═══════════════════════════════════════════

@scratch_note_bp.route('/notebooks', methods=['GET'])
@jwt_required()
def list_notebooks():
    """获取当前用户所有笔记本（按 sort_order 排序）"""
    user_id = int(get_jwt_identity())
    try:
        notebooks = Notebook.query.filter_by(user_id=user_id) \
            .order_by(Notebook.sort_order, Notebook.created_at.desc()).all()
    except Exception as e:
        logger.error(f"[scratch_note]: query error: {e}")
        return error('查询失败', status=500)
    return success([nb.to_dict() for nb in notebooks])


@scratch_note_bp.route('/notebooks', methods=['POST'])
@jwt_required()
def create_notebook():
    """创建笔记本 {title, color, color2}"""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    if not title:
        return error('笔记本名称不能为空')

    try:
        # 计算新 sort_order（放到末尾）
        max_order = db.session.query(
            db.func.coalesce(db.func.max(Notebook.sort_order), -1)
        ).filter_by(user_id=user_id).scalar()

        notebook = Notebook(
            user_id=user_id,
            title=title,
            color=data.get('color', '#8B4513'),
            color2=data.get('color2', '#5C2E0A'),
            sort_order=max_order + 1,
        )
        db.session.add(notebook)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[scratch_note]: DB error: {e}")
        return error('操作失败', status=500)
    return success(notebook.to_dict(), '笔记本创建成功', 201)


@scratch_note_bp.route('/notebooks/<int:notebook_id>', methods=['PUT'])
@jwt_required()
def update_notebook(notebook_id):
    """重命名笔记本 {title}"""
    user_id = int(get_jwt_identity())
    try:
        notebook = Notebook.query.filter_by(id=notebook_id, user_id=user_id).first()
    except Exception as e:
        logger.error(f"[scratch_note]: query error: {e}")
        return error('查询失败', status=500)
    if not notebook:
        return error('笔记本不存在', 404)

    data = request.get_json() or {}
    if 'title' in data:
        title = data['title'].strip()
        if not title:
            return error('笔记本名称不能为空')
        notebook.title = title
    if 'color' in data:
        notebook.color = data['color']
    if 'color2' in data:
        notebook.color2 = data['color2']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[scratch_note]: DB error: {e}")
        return error('操作失败', status=500)
    return success(notebook.to_dict(), '笔记本已更新')


@scratch_note_bp.route('/notebooks/reorder', methods=['PUT'])
@jwt_required()
def reorder_notebooks():
    """拖拽排序 {ordered_ids: [3, 1, 2]}"""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    ordered_ids = data.get('ordered_ids')

    if not isinstance(ordered_ids, list):
        return error('参数格式错误，ordered_ids 需为数组')

    try:
        for idx, nb_id in enumerate(ordered_ids):
            notebook = Notebook.query.filter_by(id=nb_id, user_id=user_id).first()
            if notebook:
                notebook.sort_order = idx
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[scratch_note]: DB error: {e}")
        return error('操作失败', status=500)
    return success(message='笔记本排序已更新')


@scratch_note_bp.route('/notebooks/<int:notebook_id>', methods=['DELETE'])
@jwt_required()
def delete_notebook(notebook_id):
    """删除笔记本（级联删除 notes）"""
    user_id = int(get_jwt_identity())
    try:
        notebook = Notebook.query.filter_by(id=notebook_id, user_id=user_id).first()
    except Exception as e:
        logger.error(f"[scratch_note]: query error: {e}")
        return error('查询失败', status=500)
    if not notebook:
        return error('笔记本不存在', 404)
    try:
        db.session.delete(notebook)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[scratch_note]: DB error: {e}")
        return error('操作失败', status=500)
    return success(message='笔记本已删除')


# ═══════════════════════════════════════════
#  Note API
# ═══════════════════════════════════════════

@scratch_note_bp.route('/notes', methods=['GET'])
@jwt_required()
def list_notes():
    """获取笔记列表（不含 content，按 sort_order）"""
    user_id = int(get_jwt_identity())
    notebook_id = request.args.get('notebook_id', type=int)
    if not notebook_id:
        return error('缺少 notebook_id 参数')

    # 验证笔记本归属
    try:
        notebook = Notebook.query.filter_by(id=notebook_id, user_id=user_id).first()
        if not notebook:
            return error('笔记本不存在', 404)

        notes = Note.query.filter_by(notebook_id=notebook_id, user_id=user_id) \
            .order_by(Note.sort_order, Note.created_at.desc()).all()
    except Exception as e:
        logger.error(f"[scratch_note]: query error: {e}")
        return error('查询失败', status=500)
    return success([n.to_dict(include_content=False) for n in notes])


@scratch_note_bp.route('/notes/<int:note_id>', methods=['GET'])
@jwt_required()
def get_note(note_id):
    """获取笔记详情（含 content）"""
    user_id = int(get_jwt_identity())
    try:
        note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    except Exception as e:
        logger.error(f"[scratch_note]: query error: {e}")
        return error('查询失败', status=500)
    if not note:
        return error('笔记不存在', 404)
    return success(note.to_dict(include_content=True))


@scratch_note_bp.route('/notes', methods=['POST'])
@jwt_required()
def create_note():
    """创建笔记 {notebook_id, title, content?}"""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    notebook_id = data.get('notebook_id')
    title = data.get('title', '').strip()

    if not notebook_id:
        return error('缺少 notebook_id 参数')

    try:
        # 验证笔记本归属
        notebook = Notebook.query.filter_by(id=notebook_id, user_id=user_id).first()
        if not notebook:
            return error('笔记本不存在', 404)

        # 计算新 sort_order
        max_order = db.session.query(
            db.func.coalesce(db.func.max(Note.sort_order), -1)
        ).filter_by(notebook_id=notebook_id, user_id=user_id).scalar()

        note = Note(
            notebook_id=notebook_id,
            user_id=user_id,
            title=title,
            content=data.get('content', ''),
            sort_order=max_order + 1,
        )
        db.session.add(note)

        # 更新笔记本的 updated_at
        notebook.updated_at = datetime.now(timezone.utc)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[scratch_note]: DB error: {e}")
        return error('操作失败', status=500)
    return success(note.to_dict(include_content=True), '笔记创建成功', 201)


@scratch_note_bp.route('/notes/<int:note_id>', methods=['PUT'])
@jwt_required()
def update_note(note_id):
    """更新笔记 {title?, content?}"""
    user_id = int(get_jwt_identity())
    try:
        note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    except Exception as e:
        logger.error(f"[scratch_note]: query error: {e}")
        return error('查询失败', status=500)
    if not note:
        return error('笔记不存在', 404)

    data = request.get_json() or {}
    if 'title' in data:
        note.title = data['title']
    if 'content' in data:
        note.content = data['content']

    # 更新笔记本的 updated_at
    notebook = Notebook.query.filter_by(id=note.notebook_id, user_id=user_id).first()
    if notebook:
        notebook.updated_at = datetime.now(timezone.utc)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[scratch_note]: DB error: {e}")
        return error('操作失败', status=500)
    return success(note.to_dict(include_content=True), '笔记已更新')


@scratch_note_bp.route('/notes/reorder', methods=['PUT'])
@jwt_required()
def reorder_notes():
    """拖拽排序 {ordered_ids: [5, 3, 8]}"""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    ordered_ids = data.get('ordered_ids')

    if not isinstance(ordered_ids, list):
        return error('参数格式错误，ordered_ids 需为数组')

    try:
        for idx, note_id in enumerate(ordered_ids):
            note = Note.query.filter_by(id=note_id, user_id=user_id).first()
            if note:
                note.sort_order = idx
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[scratch_note]: DB error: {e}")
        return error('操作失败', status=500)
    return success(message='笔记排序已更新')


@scratch_note_bp.route('/notes/<int:note_id>', methods=['DELETE'])
@jwt_required()
def delete_note(note_id):
    """删除笔记（级联解除关联待办）"""
    user_id = int(get_jwt_identity())
    try:
        note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    except Exception as e:
        logger.error(f"[scratch_note]: query error: {e}")
        return error('查询失败', status=500)
    if not note:
        return error('笔记不存在', 404)

    try:
        # 级联解除关联：删除笔记前先置空关联此笔记的 todos
        Todo.query.filter_by(note_id=note_id, user_id=user_id).update(
            {Todo.note_id: None}
        )

        db.session.delete(note)

        # 更新笔记本的 updated_at
        notebook = Notebook.query.filter_by(id=note.notebook_id, user_id=user_id).first()
        if notebook:
            notebook.updated_at = datetime.now(timezone.utc)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[scratch_note]: DB error: {e}")
        return error('操作失败', status=500)
    return success(message='笔记已删除')


# ═══════════════════════════════════════════
#  Note Image Upload
# ═══════════════════════════════════════════

ALLOWED_IMG = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}


@scratch_note_bp.route('/notes/<int:note_id>/upload-image', methods=['POST'])
@jwt_required()
def upload_note_image(note_id):
    """上传笔记图片（粘贴/拖拽插入）"""
    user_id = int(get_jwt_identity())

    # 验证笔记归属
    try:
        note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    except Exception as e:
        logger.error(f"[scratch_note]: query error: {e}")
        return error('查询失败', status=500)
    if not note:
        return error('笔记不存在', 404)

    if 'image' not in request.files:
        return error('没有上传文件')

    file = request.files['image']
    if file.filename == '':
        return error('文件名为空')

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'png'
    if ext not in ALLOWED_IMG:
        return error('不支持的图片格式，仅支持 png/jpg/gif/webp/bmp')

    filename = f'{uuid.uuid4().hex}.{ext}'
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(filepath)

    url = f'/uploads/{filename}'
    logger.info(f"[scratch_note] 笔记图片上传: note_id={note_id}, url={url}, user_id={user_id}")
    return success(data={'url': url}, message='图片已上传')
