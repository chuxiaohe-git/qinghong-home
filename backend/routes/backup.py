from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.group import Group
from models.bookmark import Bookmark
from models.todo import Todo
from models.setting import Setting
from models.user import User
from config import Config
from utils.response import success, error
import json
import os
import shutil
import tempfile
import random
import logging
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def random_color():
    """生成随机 RGB 颜色，与前端 getRandomColor 一致"""
    return '#%02x%02x%02x' % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

backup_bp = Blueprint('backup', __name__, url_prefix='/api')


def get_export_data(user_id):
    """收集当前用户的所有可导出数据"""
    groups = Group.query.filter_by(user_id=user_id).order_by(Group.sort_order).all()
    bookmarks = Bookmark.query.filter_by(user_id=user_id).order_by(Bookmark.sort_order).all()
    todos = Todo.query.filter_by(user_id=user_id).all()
    settings = Setting.query.filter_by(user_id=user_id).all()

    return {
        'export_time': datetime.utcnow().isoformat(),
        'groups': [g.to_dict() for g in groups],
        'bookmarks': [b.to_dict() for b in bookmarks],
        'todos': [t.to_dict() for t in todos],
        'settings': [s.to_dict() for s in settings],
    }


# ── 导出配置 ──
@backup_bp.route('/export', methods=['GET'])
@jwt_required()
def export_config():
    user_id = get_jwt_identity()
    data = get_export_data(user_id)
    return success(data=data)


# ── 导入配置 ──
@backup_bp.route('/import', methods=['POST'])
@jwt_required()
def import_config():
    user_id = get_jwt_identity()
    body = request.get_json(force=True)
    if not body:
        return error('无效的导入数据')

    data = body.get('data') or body
    mode = body.get('mode', 'append')  # overwrite | append | merge
    imported = {'groups': 0, 'bookmarks': 0, 'todos': 0, 'settings': 0}
    skipped = {'groups': 0, 'bookmarks': 0}
    group_id_map = {}  # old_id -> new_id

    try:
        # ── 全量覆盖：清空现有数据 ──
        if mode == 'overwrite':
            Bookmark.query.filter_by(user_id=user_id).delete()
            Group.query.filter_by(user_id=user_id).delete()
            Todo.query.filter_by(user_id=user_id).delete()

        # ── 导入分组 ──
        for g in data.get('groups', []):
            name = g.get('name', '').strip()
            if not name:
                continue
            old_id = g.get('id')

            if mode == 'overwrite':
                new_g = Group(user_id=user_id, name=name, icon=g.get('icon', ''), sort_order=g.get('sort_order', 0))
                db.session.add(new_g)
                db.session.flush()
                if old_id: group_id_map[old_id] = new_g.id
                imported['groups'] += 1

            elif mode == 'append':
                # 同名则重命名 append_1/append_2...
                final_name = name
                counter = 1
                while Group.query.filter_by(user_id=user_id, name=final_name).first():
                    final_name = f'{name}_{counter}'
                    counter += 1
                max_sort = db.session.query(db.func.max(Group.sort_order)).filter_by(user_id=user_id).scalar() or 0
                new_g = Group(user_id=user_id, name=final_name, icon=g.get('icon', ''), sort_order=max_sort + 1)
                db.session.add(new_g)
                db.session.flush()
                if old_id: group_id_map[old_id] = new_g.id
                imported['groups'] += 1

            else:  # merge — 按名称匹配分组，同名直接复用
                exists = Group.query.filter_by(user_id=user_id, name=name).first()
                if exists:
                    if old_id: group_id_map[old_id] = exists.id
                    continue
                new_g = Group(user_id=user_id, name=name, icon=g.get('icon', ''), sort_order=g.get('sort_order', 0))
                db.session.add(new_g)
                db.session.flush()
                if old_id: group_id_map[old_id] = new_g.id
                imported['groups'] += 1

        # ── 导入书签 ──
        for b in data.get('bookmarks', []):
            title = b.get('title', '').strip()
            url = b.get('url', '').strip()
            if not title or not url:
                continue

            gid = group_id_map.get(b.get('group_id'))

            if mode == 'merge' and gid:
                # 按分组+URL 去重
                exists = Bookmark.query.filter_by(user_id=user_id, group_id=gid, url=url).first()
                if exists:
                    exists.title = title
                    exists.description = b.get('description', exists.description)
                    exists.icon = b.get('icon', exists.icon)
                    exists.bg_color = b.get('bg_color', exists.bg_color)
                    skipped['bookmarks'] += 1
                    continue

            new_b = Bookmark(
                user_id=user_id,
                group_id=gid,
                title=title,
                url=url,
                description=b.get('description', ''),
                icon=b.get('icon', ''),
                bg_color=b.get('bg_color') or random_color(),
                sort_order=b.get('sort_order', 0),
            )
            db.session.add(new_b)
            imported['bookmarks'] += 1

        # ── 导入待办 ──
        for t in data.get('todos', []):
            title = t.get('title') or t.get('content', '')
            if not title:
                continue
            new_t = Todo(user_id=user_id, title=title, done=t.get('done', False), priority=t.get('priority', 0))
            db.session.add(new_t)
            imported['todos'] += 1

        # ── 导入设置（覆盖式） ──
        for s in data.get('settings', []):
            existing = Setting.query.filter_by(user_id=user_id).first()
            if existing:
                for k, v in s.items():
                    if k not in ('id', 'user_id', 'updated_at', 'created_at') and hasattr(existing, k):
                        setattr(existing, k, v)
            else:
                new_s = Setting(user_id=user_id)
                for k, v in s.items():
                    if k not in ('id', 'user_id', 'updated_at', 'created_at') and hasattr(new_s, k):
                        setattr(new_s, k, v)
                db.session.add(new_s)
            imported['settings'] += 1

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"backup: import DB error: {e}")
        return error('导入失败', status=500)

    return success(
        data={'imported': imported, 'skipped': skipped},
        message=f'导入完成（新增 {imported["groups"]} 分组 / {imported["bookmarks"]} 书签）'
    )


def _parse_bookmark_map(content):
    """
    基于位置事件排序解析书签 HTML，建立 dict[url] = folder_name。
    不依赖 DOM 解析器（lxml/html.parser 都会破坏书签 HTML），
    而是按位置扫描全文事件并追踪文件夹嵌套栈。
    对任意 Chrome/Firefox 导出的 Netscape 书签格式通用。
    """
    import re
    events = []

    # 收集三类事件及其在文件中的位置
    for m in re.finditer(r'<H3[^>]*>(.*?)</H3>', content, re.IGNORECASE | re.DOTALL):
        name = m.group(1).strip()
        if name and name != 'Bookmarks':
            events.append((m.start(), 'open', name))
    for m in re.finditer(r'</DL>', content, re.IGNORECASE):
        events.append((m.start(), 'close', None))
    for m in re.finditer(r'<A\s+HREF="([^"]*)"', content, re.IGNORECASE):
        url = m.group(1).strip()
        if url and not url.startswith(('place:', 'javascript:')):
            events.append((m.start(), 'link', url))

    # 按位置排序，顺序处理
    events.sort(key=lambda x: x[0])
    folder_stack = ['未分类']
    url_to_folder = {}
    for _pos, typ, data in events:
        if typ == 'open':
            folder_stack.append(data)
        elif typ == 'close':
            if len(folder_stack) > 1:
                folder_stack.pop()
        elif typ == 'link':
            url_to_folder[data] = folder_stack[-1]

    return url_to_folder


def _extract_domain(url):
    """从 URL 提取域名"""
    try:
        from urllib.parse import urlparse
        return urlparse(url).hostname or ''
    except Exception:
        return ''


# ── 浏览器书签导入 ──
@backup_bp.route('/import/bookmarks', methods=['POST'])
@jwt_required()
def import_bookmarks_html():
    user_id = get_jwt_identity()
    if 'file' not in request.files:
        return error('请上传书签 HTML 文件')

    file = request.files['file']
    if not file.filename.endswith('.html'):
        return error('仅支持 HTML 格式的书签文件')

    try:
        content = file.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return error(f'文件解析失败：{str(e)}')

    # 用正则解析书签文件夹结构（lxml 会破坏书签 HTML，不能用 DOM 解析）
    url_to_folder = _parse_bookmark_map(content)
    if not url_to_folder:
        return error('未在文件中找到书签链接，请确认是 Chrome/Firefox 导出的书签 HTML')

    # 用 BeautifulSoup 提取 <A> 标签详情（只用于找标签本身，不建树）
    soup = BeautifulSoup(content, 'html.parser')
    imported = 0
    skipped_dup = 0
    skipped_invalid = 0
    groups_created = 0
    errors = []

    try:
        for a in soup.find_all('a'):
            try:
                title = a.get_text(strip=True)
                url = a.get('href', '').strip()
                if not title or not url or url.startswith(('place:', 'javascript:')):
                    skipped_invalid += 1
                    continue

                # 从正则映射取文件夹名
                folder_name = url_to_folder.get(url, '未分类')
                # 创建或复用分组
                group = Group.query.filter_by(user_id=user_id, name=folder_name).first()
                if not group:
                    group = Group(user_id=user_id, name=folder_name, icon='', sort_order=0)
                    db.session.add(group)
                    db.session.flush()
                    groups_created += 1

                # 按 URL 去重
                exists = Bookmark.query.filter_by(user_id=user_id, url=url).first()
                if exists:
                    skipped_dup += 1
                    continue

                # 默认图标
                domain = _extract_domain(url)
                default_icon = f'https://favicon.im/{domain}' if domain else ''

                max_sort = Bookmark.query.filter_by(user_id=user_id, group_id=group.id).count()
                bk = Bookmark(
                    user_id=user_id,
                    group_id=group.id,
                    title=title,
                    url=url,
                    description='',
                    icon=default_icon,
                    bg_color=random_color(),
                    sort_order=max_sort,
                )
                db.session.add(bk)
                imported += 1
            except Exception as e:
                errors.append(str(e))

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"backup: import bookmarks DB error: {e}")
        return error('书签导入失败', status=500)

    parts = [f'成功导入 {imported} 个书签']
    if groups_created:
        parts.append(f'新建 {groups_created} 个分组')
    if skipped_dup:
        parts.append(f'跳过 {skipped_dup} 个重复链接')
    if skipped_invalid:
        parts.append(f'忽略 {skipped_invalid} 个无效条目')

    if errors:
        parts.append(f'警告：{len(errors)} 个解析错误（{errors[0]}）')

    return success(
        message='，'.join(parts),
        data={
            'imported': imported,
            'groups_created': groups_created,
            'skipped_dup': skipped_dup,
            'skipped_invalid': skipped_invalid,
            'errors': errors[:5],
        }
    )


# ── 创建备份 ──
@backup_bp.route('/backup', methods=['POST'])
@jwt_required()
def create_backup():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'super_admin':
        return error('仅超级管理员可创建备份', status=403)

    try:
        os.makedirs(Config.BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'backup_{timestamp}.db'
        backup_path = os.path.join(Config.BACKUP_DIR, backup_name)

        # 获取数据库路径
        db_path = db.engine.url.database
        if not db_path or db_path == ':memory:':
            return error('仅支持文件数据库的备份', status=500)

        shutil.copy2(db_path, backup_path)
        size = os.path.getsize(backup_path)
    except Exception as e:
        logger.error(f"backup: create backup error: {e}")
        return error('备份创建失败', status=500)

    return success(
        data={'name': backup_name, 'size': size, 'time': timestamp},
        message='备份成功'
    )


# ── 备份列表 ──
@backup_bp.route('/backups', methods=['GET'])
@jwt_required()
def list_backups():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'super_admin':
        return error('仅超级管理员可查看备份', status=403)

    try:
        os.makedirs(Config.BACKUP_DIR, exist_ok=True)
        backups = []
        for f in sorted(os.listdir(Config.BACKUP_DIR), reverse=True):
            if f.endswith('.db'):
                path = os.path.join(Config.BACKUP_DIR, f)
                backups.append({
                    'name': f,
                    'size': os.path.getsize(path),
                    'time': datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S'),
                })
    except Exception as e:
        logger.error(f"backup: list backups error: {e}")
        return error('读取备份列表失败', status=500)

    return success(data=backups)


# ── 下载备份 ──
@backup_bp.route('/backup/<filename>/download', methods=['GET'])
@jwt_required()
def download_backup(filename):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'super_admin':
        return error('仅超级管理员可下载备份', status=403)

    path = os.path.join(Config.BACKUP_DIR, filename)
    if not os.path.exists(path):
        return error('备份文件不存在', status=404)

    return send_file(path, as_attachment=True, download_name=filename)


# ── 恢复备份 ──
@backup_bp.route('/restore', methods=['POST'])
@jwt_required()
def restore_backup():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'super_admin':
        return error('仅超级管理员可恢复备份', status=403)

    upload_type = request.form.get('type', 'file')

    try:
        if upload_type == 'file':
            if 'file' not in request.files:
                return error('请上传备份文件')
            f = request.files['file']
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            f.save(tmp.name)
            restore_path = tmp.name
        elif upload_type == 'local':
            name = request.form.get('name', '').strip()
            if not name:
                return error('请指定备份文件名')
            restore_path = os.path.join(Config.BACKUP_DIR, name)
            if not os.path.exists(restore_path):
                return error('备份文件不存在', status=404)
        else:
            return error('无效的恢复类型')

        # 替换数据库文件
        db_path = db.engine.url.database
        if not db_path or db_path == ':memory:':
            return error('仅支持文件数据库的恢复', status=500)

        # 关闭当前连接，替换文件
        db.session.close()
        db.engine.dispose()
        shutil.copy2(restore_path, db_path)

        if upload_type == 'file':
            os.unlink(restore_path)
    except Exception as e:
        logger.error(f"backup: restore error: {e}")
        return error('恢复操作失败', status=500)

    return success(message='恢复成功，请刷新页面')
