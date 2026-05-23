from extensions import db
from datetime import datetime, timezone


class MusicPlaylistItem(db.Model):
    __tablename__ = 'music_playlist'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    songid = db.Column(db.String(20), nullable=False, index=True)  # 歌曲海 play ID
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), default='')
    source = db.Column(db.String(20), default='gequhai')
    url = db.Column(db.String(512), default='')             # 缓存的播放地址
    lrc = db.Column(db.Text, default='')                    # 缓存歌词
    sort_order = db.Column(db.Integer, default=0)
    fetched_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'songid': self.songid,
            'title': self.title,
            'author': self.author,
            'source': self.source,
            'url': self.url,
            'lrc': self.lrc,
            'sort_order': self.sort_order,
            'fetched_at': self.fetched_at.isoformat() if self.fetched_at else None,
        }
