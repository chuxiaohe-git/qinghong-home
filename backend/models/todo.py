from extensions import db
from datetime import datetime, timezone


class Todo(db.Model):
    __tablename__ = 'todos'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)
    priority = db.Column(db.Integer, default=0)
    sort_order = db.Column(db.Integer, default=0)
    color = db.Column(db.String(7), nullable=True)
    label = db.Column(db.String(50), nullable=True)
    date = db.Column(db.Date, nullable=True, index=True)           # YYYY-MM-DD, NULL=无日期(右侧), 有值=日历待办
    reminder_at = db.Column(db.DateTime, nullable=True)             # 提醒时间
    reminded = db.Column(db.Boolean, default=False)                 # 是否已提醒
    # ── 笔记关联字段（摸鱼笔记 ↔ 待办栏双向联动） ──
    note_id = db.Column(db.Integer, db.ForeignKey('notes.id', ondelete='SET NULL'), nullable=True)
    notebook_id = db.Column(db.Integer, db.ForeignKey('notebooks.id', ondelete='SET NULL'), nullable=True)
    selected_text = db.Column(db.Text, nullable=True)
    highlight_start = db.Column(db.Integer, nullable=True)  # 选中文本在笔记内容中的起始偏移
    # ── 关联 ──
    note = db.relationship('Note', backref='todos')
    # ── / ──
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'done': self.done,
            'priority': self.priority,
            'sort_order': self.sort_order,
            'color': self.color,
            'label': self.label,
            'date': self.date.isoformat() if self.date else None,
            'reminder_at': self.reminder_at.isoformat() if self.reminder_at else None,
            'reminded': self.reminded,
            'note_id': self.note_id,
            'notebook_id': self.notebook_id,
            'selected_text': self.selected_text,
            'highlight_start': self.highlight_start,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
