from extensions import db
from datetime import datetime, timezone


class Setting(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    theme = db.Column(db.String(20), default='system')  # system / light / dark
    language = db.Column(db.String(10), default='zh-CN')
    wallpaper = db.Column(db.Text, default='')
    layout_config = db.Column(db.Text, default='{}')  # JSON string
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'theme': self.theme,
            'language': self.language,
            'wallpaper': self.wallpaper,
            'layout_config': self.layout_config,
        }
