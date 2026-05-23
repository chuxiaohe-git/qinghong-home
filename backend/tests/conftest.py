import pytest
import tempfile
import os
import shutil
import atexit
import bcrypt

# 必须在 import app 之前设置测试环境变量
_TEST_TMP = tempfile.mkdtemp()

# 保存原始环境变量，测试结束时恢复
_ORIG_ENV = {
    'DATABASE_URL': os.environ.get('DATABASE_URL'),
    'SECRET_KEY': os.environ.get('SECRET_KEY'),
    'JWT_SECRET_KEY': os.environ.get('JWT_SECRET_KEY'),
    'INSTANCE_DIR': os.environ.get('INSTANCE_DIR'),
    'UPLOAD_DIR': os.environ.get('UPLOAD_DIR'),
    'BACKUP_DIR': os.environ.get('BACKUP_DIR'),
}

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test-secret'
os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret'
os.environ['INSTANCE_DIR'] = os.path.join(_TEST_TMP, 'instance')
os.environ['UPLOAD_DIR'] = os.path.join(_TEST_TMP, 'uploads')
os.environ['BACKUP_DIR'] = os.path.join(_TEST_TMP, 'backups')

def _cleanup():
    # 恢复原始环境变量
    for k, v in _ORIG_ENV.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    # 删除临时目录
    shutil.rmtree(_TEST_TMP, ignore_errors=True)

atexit.register(_cleanup)

from app import create_app
from extensions import db as _db
from models.user import User


@pytest.fixture(scope='function')
def app():
    _app = create_app()
    _app.config['TESTING'] = True
    _app.config['SERVER_NAME'] = 'localhost'
    return _app


@pytest.fixture(scope='function')
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture(scope='function')
def auth_headers(client):
    # 登录（admin 由 create_app 自动创建）
    res = client.post('/api/auth/login', json={
        'username': 'admin', 'password': 'admin123',
    })
    data = res.get_json()
    assert data['code'] == 0, f'登录失败: {data}'
    token = data['data']['token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture(scope='function')
def group(client, auth_headers):
    res = client.post('/api/groups', json={
        'name': '测试分组', 'icon': '',
    }, headers=auth_headers)
    return res.get_json()['data']


@pytest.fixture(scope='function')
def bookmark(client, auth_headers, group):
    res = client.post('/api/bookmarks', json={
        'group_id': group['id'], 'title': '测试书签', 'url': 'https://example.com',
    }, headers=auth_headers)
    return res.get_json()['data']
