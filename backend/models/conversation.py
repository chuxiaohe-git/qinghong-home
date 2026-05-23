from extensions import db
from datetime import datetime, timezone


class Conversation(db.Model):
    """AI 对话记录"""
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(100), default='新对话')
    messages = db.Column(db.Text, default='[]')  # JSON array
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title or '新对话',
            'message_count': len(self.get_messages()),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def get_messages(self):
        import json
        try:
            return json.loads(self.messages or '[]')
        except (json.JSONDecodeError, TypeError):
            return []

    def set_messages(self, msgs):
        import json
        self.messages = json.dumps(msgs, ensure_ascii=False)

    def add_message(self, role, content):
        msgs = self.get_messages()
        msgs.append({'role': role, 'content': content})
        self.set_messages(msgs)
