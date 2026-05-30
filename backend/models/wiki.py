from extensions import db
from datetime import datetime, timezone


class WikiDoc(db.Model):
    __tablename__ = 'wiki_docs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False, default='')
    content = db.Column(db.Text, default='')
    icon = db.Column(db.String(10), default='📄')
    summary = db.Column(db.String(200), default='')
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self, include_content=True):
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'icon': self.icon or '📄',
            'summary': self.summary or '',
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_content:
            result['content'] = self.content
        return result
