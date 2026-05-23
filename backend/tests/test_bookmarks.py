"""书签 API + 搜索测试"""

def test_create_bookmark(client, auth_headers, group):
    """创建书签"""
    res = client.post('/api/bookmarks', json={
        'group_id': group['id'],
        'title': 'GitHub',
        'url': 'https://github.com',
    }, headers=auth_headers)
    d = res.get_json()
    assert d['code'] == 0
    assert d['data']['title'] == 'GitHub'


def test_list_bookmarks(client, auth_headers, group):
    """列出书签"""
    client.post('/api/bookmarks', json={
        'group_id': group['id'], 'title': 'A', 'url': 'https://a.com'
    }, headers=auth_headers)
    client.post('/api/bookmarks', json={
        'group_id': group['id'], 'title': 'B', 'url': 'https://b.com'
    }, headers=auth_headers)
    res = client.get('/api/bookmarks', headers=auth_headers)
    assert len(res.get_json()['data']) == 2


def test_search_bookmarks(client, auth_headers, group):
    """搜索书签"""
    client.post('/api/bookmarks', json={
        'group_id': group['id'], 'title': '京东商城', 'url': 'https://jd.com',
    }, headers=auth_headers)
    client.post('/api/bookmarks', json={
        'group_id': group['id'], 'title': '淘宝', 'url': 'https://taobao.com',
    }, headers=auth_headers)

    res = client.get('/api/bookmarks/search?q=京东', headers=auth_headers)
    data = res.get_json()['data']
    assert len(data) == 1
    assert data[0]['title'] == '京东商城'


def test_pinyin_search(client, auth_headers, group):
    """模糊搜索支持（后端只做 LIKE，前端做拼音匹配）"""
    client.post('/api/bookmarks', json={
        'group_id': group['id'], 'title': '哔哩哔哩', 'url': 'https://bilibili.com',
    }, headers=auth_headers)

    # 后端只做 SQL LIKE，搜"哔哩"能匹配
    res = client.get('/api/bookmarks/search?q=哔哩', headers=auth_headers)
    assert len(res.get_json()['data']) == 1


def test_update_bookmark(client, auth_headers, bookmark):
    """更新书签"""
    res = client.put(f'/api/bookmarks/{bookmark["id"]}', json={
        'title': '新标题',
        'url': 'https://new.com',
    }, headers=auth_headers)
    assert res.get_json()['data']['title'] == '新标题'


def test_delete_bookmark(client, auth_headers, bookmark):
    """删除书签"""
    client.delete(f'/api/bookmarks/{bookmark["id"]}', headers=auth_headers)
    res = client.get('/api/bookmarks', headers=auth_headers)
    assert len(res.get_json()['data']) == 0


def test_delete_group_cascades_bookmarks(client, auth_headers, group):
    """删除分组时级联删除书签"""
    client.post('/api/bookmarks', json={
        'group_id': group['id'], 'title': 'A', 'url': 'https://a.com',
    }, headers=auth_headers)
    client.delete(f'/api/groups/{group["id"]}', headers=auth_headers)
    res = client.get('/api/bookmarks', headers=auth_headers)
    assert len(res.get_json()['data']) == 0
