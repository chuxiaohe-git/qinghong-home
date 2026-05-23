from extensions import db
from datetime import datetime, timezone


class Bookmark(db.Model):
    __tablename__ = 'bookmarks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(512), nullable=False)
    description = db.Column(db.String(200), default='')
    icon = db.Column(db.String(256), default='')
    bg_color = db.Column(db.String(20), default='')
    open_method = db.Column(db.String(10), default='_blank')  # _blank / _self
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'group_id': self.group_id,
            'title': self.title,
            'url': self.url,
            'description': self.description,
            'icon': self.icon,
            'bg_color': self.bg_color,
            'open_method': self.open_method,
            'sort_order': self.sort_order,
        }
