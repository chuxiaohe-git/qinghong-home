from extensions import db
from datetime import datetime, timezone


class GalleryImage(db.Model):
    __tablename__ = 'gallery_images'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    filename = db.Column(db.String(256), nullable=False)
    original_name = db.Column(db.String(256), default='')
    filepath = db.Column(db.String(512), nullable=False)
    image_type = db.Column(db.String(20), default='wallpaper')  # wallpaper / icon
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'original_name': self.original_name,
            'filepath': self.filepath,
            'image_type': self.image_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'url': f'/uploads/{self.filename}',
        }
