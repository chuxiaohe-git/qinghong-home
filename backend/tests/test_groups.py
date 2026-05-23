"""分组 API 测试"""

def test_create_group(client, auth_headers):
    """创建分组"""
    res = client.post('/api/groups', json={
        'name': '工作',
    }, headers=auth_headers)
    d = res.get_json()
    assert d['code'] == 0
    assert d['data']['name'] == '工作'
    assert d['data']['display_mode'] == 'large'


def test_list_groups(client, auth_headers):
    """列出分组"""
    client.post('/api/groups', json={'name': 'A'}, headers=auth_headers)
    client.post('/api/groups', json={'name': 'B'}, headers=auth_headers)
    res = client.get('/api/groups', headers=auth_headers)
    d = res.get_json()
    assert len(d['data']) == 2


def test_update_group(client, auth_headers, group):
    """更新分组"""
    res = client.put(f'/api/groups/{group["id"]}', json={
        'name': '改名字',
        'display_mode': 'small',
    }, headers=auth_headers)
    d = res.get_json()
    assert d['data']['name'] == '改名字'
    assert d['data']['display_mode'] == 'small'


def test_delete_group(client, auth_headers, group):
    """删除分组"""
    res = client.delete(f'/api/groups/{group["id"]}', headers=auth_headers)
    assert res.get_json()['code'] == 0
    # 验证确实删了
    res2 = client.get('/api/groups', headers=auth_headers)
    assert len(res2.get_json()['data']) == 0


def test_delete_group_not_found(client, auth_headers):
    """删除不存在的分组"""
    res = client.delete('/api/groups/99999', headers=auth_headers)
    assert res.status_code == 404


def test_group_data_isolation(client, auth_headers):
    """多用户数据隔离"""
    client.post('/api/groups', json={'name': 'A的分组'}, headers=auth_headers)

    # 用 admin 登录（这是默认只有一个用户的情况下的测试）
    # 创建一个新用户直插数据库
    import bcrypt
    from models.user import User
    from extensions import db
    pw = bcrypt.hashpw(b'pass_b', bcrypt.gensalt()).decode()
    ub = User(username='user_b', password_hash=pw, role='user', is_active=True)
    db.session.add(ub)
    db.session.commit()

    res_b = client.post('/api/auth/login', json={'username': 'user_b', 'password': 'pass_b'})
    headers_b = {'Authorization': f'Bearer {res_b.get_json()["data"]["token"]}'}

    res = client.get('/api/groups', headers=headers_b)
    assert len(res.get_json()['data']) == 0
