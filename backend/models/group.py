from extensions import db
from datetime import datetime, timezone


class Group(db.Model):
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(256), default='')
    sort_order = db.Column(db.Integer, default=0)
    display_mode = db.Column(db.String(10), default='large')  # 'large' | 'small'
    guest_visible = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    bookmarks = db.relationship('Bookmark', backref='group', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'icon': self.icon,
            'sort_order': self.sort_order,
            'display_mode': self.display_mode or 'large',
            'guest_visible': bool(self.guest_visible),
        }
