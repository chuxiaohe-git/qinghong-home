from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.groups import groups_bp
from routes.bookmarks import bookmarks_bp
from routes.todo import todo_bp
from routes.settings import settings_bp
from routes.gallery import gallery_bp

from routes.scrape import scrape_bp
from routes.backup import backup_bp
from routes.scratch_note import scratch_note_bp

__all__ = ['auth_bp', 'admin_bp', 'groups_bp', 'bookmarks_bp', 'todo_bp', 'settings_bp',
           'gallery_bp', 'scrape_bp', 'backup_bp', 'scratch_note_bp']
