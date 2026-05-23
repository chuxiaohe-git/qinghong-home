from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.todo import Todo
from utils.response import success, error
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)

todo_bp = Blueprint('todo', __name__, url_prefix='/api/todos')


# ── 查询（右侧并集：用户自建 + 今日日历） ──

@todo_bp.route('', methods=['GET'])
@jwt_required()
def list_todos():
    user_id = int(get_jwt_identity())
    done_filter = request.args.get('done', type=int)
    note_id_filter = request.args.get('note_id', type=int)
    notebook_id_filter = request.args.get('notebook_id', type=int)
    today = date.today()

    query = Todo.query.filter_by(user_id=user_id)

    # 如果指定了 note_id 筛选，只查关联该笔记的待办
    if note_id_filter is not None:
        query = query.filter_by(note_id=note_id_filter)
    elif notebook_id_filter is not None:
        query = query.filter_by(notebook_id=notebook_id_filter)
    else:
        # 返回并集：date IS NULL（无日期/自建）OR date = today（今日日历）
        query = query.filter(
            db.or_(Todo.date.is_(None), Todo.date == today)
        )

    if done_filter is not None:
        query = query.filter_by(done=bool(done_filter))

    todos = query.order_by(Todo.done.asc(), Todo.sort_order, Todo.created_at.desc()).all()
    return success([t.to_dict() for t in todos])


# ── 新建 ──

@todo_bp.route('', methods=['POST'])
@jwt_required()
def create_todo():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    title = data.get('title', '').strip()
    if not title:
        return error('待办内容不能为空')

    max_order = Todo.query.filter_by(user_id=user_id).count()
    color = data.get('color')
    if not color:
        # 从前端 NOTE_COLORS 调色板选一个，保证跨面板一致
        COLORS = ['#FF6B6B','#FDCB6E','#A29BFE','#2ECC71','#4ECDC4',
                  '#FF9FF3','#74B9FF','#FAB1A0','#DDA0DD','#FFEAA7']
        color = COLORS[len(title) % len(COLORS)]
    todo = Todo(
        user_id=user_id,
        title=title,
        sort_order=0,
        color=color,
        priority=data.get('priority', 0),
        note_id=data.get('note_id'),
        notebook_id=data.get('notebook_id'),
        selected_text=data.get('selected_text'),
        highlight_start=data.get('highlight_start'),
    )
    if 'date' in data:
        try:
            todo.date = datetime.strptime(data['date'], '%Y-%m-%d').date() if data['date'] else None
        except ValueError:
            return error('日期格式错误，需 YYYY-MM-DD')
    Todo.query.filter_by(user_id=user_id).update(
        {Todo.sort_order: Todo.sort_order + 1}
    )
    db.session.add(todo)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"todo: create error: {e}")
        return error('创建待办失败', status=500)
    return success(todo.to_dict(), '待办创建成功', 201)


# ── 排序 ──

@todo_bp.route('/reorder', methods=['POST'])
@jwt_required()
def reorder_todos():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not isinstance(data, list):
        return error('参数格式错误，需为数组')

    for item in data:
        tid = item.get('id')
        order = item.get('sort_order')
        if tid is None or order is None:
            continue
        todo = Todo.query.filter_by(id=tid, user_id=user_id).first()
        if todo:
            todo.sort_order = order
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"todo: reorder error: {e}")
        return error('排序失败', status=500)
    return success(message='排序已更新')


# ── 更新 ──

@todo_bp.route('/<int:todo_id>', methods=['PUT'])
@jwt_required()
def update_todo(todo_id):
    user_id = int(get_jwt_identity())
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    if not todo:
        return error('待办不存在', 404)

    data = request.get_json()
    if 'title' in data:
        todo.title = data['title']
    if 'done' in data:
        todo.done = data['done']
    if 'priority' in data:
        todo.priority = data['priority']
    if 'color' in data:
        todo.color = data['color']
    if 'label' in data:
        todo.label = data['label']
    if 'sort_order' in data:
        todo.sort_order = data['sort_order']
    if 'date' in data:
        try:
            todo.date = datetime.strptime(data['date'], '%Y-%m-%d').date() if data['date'] else None
        except ValueError:
            return error('日期格式错误，需 YYYY-MM-DD')
    if 'note_id' in data:
        todo.note_id = data['note_id']
    if 'notebook_id' in data:
        todo.notebook_id = data['notebook_id']
    if 'selected_text' in data:
        todo.selected_text = data['selected_text']
    if 'highlight_start' in data:
        todo.highlight_start = data['highlight_start']
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"todo: update error: {e}")
        return error('更新待办失败', status=500)
    return success(todo.to_dict())


# ── 删除 ──

@todo_bp.route('/<int:todo_id>', methods=['DELETE'])
@jwt_required()
def delete_todo(todo_id):
    user_id = int(get_jwt_identity())
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    if not todo:
        return error('待办不存在', 404)
    db.session.delete(todo)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"todo: delete error: {e}")
        return error('删除待办失败', status=500)
    return success(message='待办已删除')


# ── 按笔记查询关联待办 ──

@todo_bp.route('/by-note/<int:note_id>', methods=['GET'])
@jwt_required()
def get_todos_by_note(note_id):
    """查询某笔记关联的所有待办"""
    user_id = int(get_jwt_identity())
    todos = Todo.query.filter_by(user_id=user_id, note_id=note_id) \
        .order_by(Todo.done.asc(), Todo.sort_order, Todo.created_at.desc()).all()
    return success([t.to_dict() for t in todos])


# ── 批量按笔记查询关联待办 ──

@todo_bp.route('/by-note-batch', methods=['GET'])
@jwt_required()
def get_todos_by_note_batch():
    """批量查询，返回 {note_id: [todo,...]} 格式"""
    user_id = int(get_jwt_identity())
    note_ids_str = request.args.get('note_ids', '')
    if not note_ids_str:
        return success({})

    try:
        note_ids = [int(x) for x in note_ids_str.split(',') if x.strip()]
    except ValueError:
        return error('note_ids 参数格式错误，需为逗号分隔的数字')

    todos = Todo.query.filter(
        Todo.user_id == user_id,
        Todo.note_id.in_(note_ids)
    ).order_by(Todo.done.asc(), Todo.sort_order, Todo.created_at.desc()).all()

    # 按 note_id 分组
    result = {}
    for t in todos:
        nid = t.note_id
        if nid not in result:
            result[nid] = []
        result[nid].append(t.to_dict())

    return success(result)
