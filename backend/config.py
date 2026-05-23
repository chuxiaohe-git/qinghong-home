import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    BASE_DIR = BASE_DIR
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
    BACKUP_DIR = os.path.join(BASE_DIR, 'backups')

    SECRET_KEY = os.environ.get('SECRET_KEY', 'qinghong-default-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(INSTANCE_DIR, "qinghong.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'qinghong-jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = 2592000  # 30 days
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    UPLOAD_FOLDER = UPLOAD_DIR
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'ico'}
