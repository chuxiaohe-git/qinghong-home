import os
import sys
import logging
from flask import Flask, send_from_directory
from config import Config
from extensions import db, jwt, cors, migrate
from models import User
from models.menu import UserMenu
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.groups import groups_bp
from routes.bookmarks import bookmarks_bp
from routes.todo import todo_bp
from routes.settings import settings_bp
from routes.gallery import gallery_bp
from routes.scrape import scrape_bp
from routes.music import music_bp
from routes.menu import menu_bp
from routes.backup import backup_bp
from routes.calendar import calendar_bp
from routes.scratch_note import scratch_note_bp
from routes.guest import guest_bp
from routes.ai import ai_bp
from routes.conversation import conversation_bp
from routes.wiki import wiki_bp
import bcrypt

logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__, static_folder='../dist', static_url_path='')
    app.config.from_object(Config)

    # Ensure instance dir exists
    os.makedirs(Config.INSTANCE_DIR, exist_ok=True)
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.BACKUP_DIR, exist_ok=True)

    # Init extensions
    db.init_app(app)
    jwt.init_app(app)

    # JWT token 版本验证：改密码后旧 token 自动失效
    @jwt.token_in_blocklist_loader
    def check_token_version(jwt_header, jwt_payload):
        user_id = int(jwt_payload['sub'])
        version = jwt_payload.get('token_version', 0)
        user = db.session.get(User, user_id)
        if user is None:
            return True
        return (user.token_version or 0) != version

    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(bookmarks_bp)
    app.register_blueprint(todo_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(gallery_bp)
    app.register_blueprint(scrape_bp)
    app.register_blueprint(music_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(backup_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(scratch_note_bp)
    app.register_blueprint(wiki_bp)
    app.register_blueprint(guest_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(conversation_bp)

    # Serve frontend static files
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/assets/<path:path>')
    def serve_assets(path):
        return send_from_directory(os.path.join(app.static_folder, 'assets'), path)

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(app.static_folder, 'favicon.ico')

    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        return send_from_directory(Config.UPLOAD_FOLDER, filename)

    @app.route('/tinymce/<path:path>')
    def serve_tinymce(path):
        return send_from_directory(os.path.join(app.static_folder, 'tinymce'), path)

    # Catch-all for SPA routes
    @app.errorhandler(404)
    def not_found(e):
        path = e.description if hasattr(e, 'description') else ''
        if path and path.startswith('/api/'):
            from utils.response import error
            return error('接口不存在', 404)
        return send_from_directory(app.static_folder, 'index.html')

    # Create tables and seed admin
    with app.app_context():
        db.create_all()
        _migrate_columns()
        _seed_admin()

    return app


def _seed_admin():
    """Create default admin if no admin exists."""
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        hashed = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin = User(
            username='admin',
            password_hash=hashed,
            nickname='超级管理员',
            role='admin',
        )
        db.session.add(admin)
        db.session.commit()
        logger.info('✅ 默认管理员已创建：admin / admin123')


def _migrate_columns():
    """为已有表添加新字段（ALTER TABLE，try/except 处理重复执行）"""
    from sqlalchemy import text
    engine = db.engine
    migrations = [
        'ALTER TABLE todos ADD COLUMN sort_order INTEGER DEFAULT 0',
        'ALTER TABLE todos ADD COLUMN color VARCHAR(7)',
        'ALTER TABLE todos ADD COLUMN label VARCHAR(50)',
        'ALTER TABLE users ADD COLUMN token_version INTEGER DEFAULT 0',
        'ALTER TABLE wiki_docs ADD COLUMN icon VARCHAR(10) DEFAULT \'📄\'',
        'ALTER TABLE wiki_docs ADD COLUMN summary VARCHAR(200) DEFAULT \'\'',
    ]
    for sql in migrations:
        try:
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
        except Exception:
            pass  # 列已存在则跳过


if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=False)
else:
    app = create_app()
