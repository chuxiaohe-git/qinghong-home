from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.todo import Todo
from utils.response import success, error
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

calendar_bp = Blueprint('calendar', __name__, url_prefix='/api/calendar')


# ── 按日期范围查询（日历视图） ──

@calendar_bp.route('/todos', methods=['GET'])
@jwt_required()
def list_todos():
    user_id = int(get_jwt_identity())
    start_str = request.args.get('start')
    end_str = request.args.get('end')

    query = Todo.query.filter_by(user_id=user_id)
    if start_str:
        query = query.filter(Todo.date >= datetime.strptime(start_str, '%Y-%m-%d').date())
    if end_str:
        query = query.filter(Todo.date <= datetime.strptime(end_str, '%Y-%m-%d').date())

    items = query.order_by(Todo.date, Todo.sort_order, Todo.created_at).all()
    return success([t.to_dict() for t in items])


# ── 新建日历待办 ──

@calendar_bp.route('/todos', methods=['POST'])
@jwt_required()
def create_todo():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    title = data.get('title', '').strip()
    if not title:
        return error('待办内容不能为空')

    try:
        todo_date = datetime.strptime(data['date'], '%Y-%m-%d').date() if data.get('date') else None
    except ValueError:
        return error('日期格式错误，需 YYYY-MM-DD')

    todo = Todo(
        user_id=user_id,
        date=todo_date,
        title=title,
        color=data.get('color', '#FFEAA7'),
    )
    try:
        db.session.add(todo)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[calendar]: DB error: {e}")
        return error('操作失败', status=500)
    return success(todo.to_dict(), '待办创建成功', 201)


# ── 更新 ──

@calendar_bp.route('/todos/<int:todo_id>', methods=['PUT'])
@jwt_required()
def update_todo(todo_id):
    user_id = int(get_jwt_identity())
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    if not todo:
        return error('待办不存在', 404)

    data = request.get_json()
    if 'date' in data:
        try:
            todo.date = datetime.strptime(data['date'], '%Y-%m-%d').date() if data['date'] else None
        except ValueError:
            return error('日期格式错误')
    if 'title' in data:
        todo.title = data['title']
    if 'done' in data:
        todo.done = bool(data['done'])
    if 'color' in data:
        todo.color = data['color']
    if 'sort_order' in data:
        todo.sort_order = data['sort_order']
    if 'reminder_at' in data:
        raw = data['reminder_at']
        if raw:
            try:
                todo.reminder_at = datetime.strptime(raw, '%Y-%m-%d %H:%M')
                todo.reminded = False
            except ValueError:
                return error('提醒时间格式错误，需 YYYY-MM-DD HH:MM')
        else:
            todo.reminder_at = None
            todo.reminded = False
    if 'reminded' in data:
        todo.reminded = bool(data['reminded'])

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[calendar]: DB error: {e}")
        return error('操作失败', status=500)
    return success(todo.to_dict())


# ── 删除 ──

@calendar_bp.route('/todos/<int:todo_id>', methods=['DELETE'])
@jwt_required()
def delete_todo(todo_id):
    user_id = int(get_jwt_identity())
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    if not todo:
        return error('待办不存在', 404)
    try:
        db.session.delete(todo)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[calendar]: DB error: {e}")
        return error('操作失败', status=500)
    return success(message='待办已删除')


# ── 获取待触发的提醒 ──

@calendar_bp.route('/reminders', methods=['GET'])
@jwt_required()
def list_reminders():
    user_id = int(get_jwt_identity())
    now = datetime.utcnow()
    items = Todo.query.filter(
        Todo.user_id == user_id,
        Todo.done == False,
        Todo.reminder_at.isnot(None),
        Todo.reminder_at > now,
        Todo.reminded == False,
    ).order_by(Todo.reminder_at).all()
    return success([t.to_dict() for t in items])


# ── 保留同步接口（向后兼容，空操作） ──

@calendar_bp.route('/sync-today', methods=['POST'])
@jwt_required()
def sync_today():
    return success(message='已无需同步')
