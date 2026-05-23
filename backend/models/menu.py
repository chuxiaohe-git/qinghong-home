from extensions import db
from datetime import datetime, timezone


class UserMenu(db.Model):
    __tablename__ = 'user_menus'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    menus = db.Column(db.JSON, default=dict)  # {"今天吃什么？": [...], "今天喝什么？": [...], ...}
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
