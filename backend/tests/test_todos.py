"""待办 API 测试"""

TODO = {'title': '写周报', 'done': False}


def test_create_todo(client, auth_headers):
    res = client.post('/api/todos', json=TODO, headers=auth_headers)
    d = res.get_json()
    assert d['code'] == 0
    assert d['data']['title'] == '写周报'


def test_list_todos(client, auth_headers):
    client.post('/api/todos', json=TODO, headers=auth_headers)
    client.post('/api/todos', json={'title': '开会', 'done': False}, headers=auth_headers)
    res = client.get('/api/todos', headers=auth_headers)
    assert len(res.get_json()['data']) == 2


def test_toggle_done(client, auth_headers):
    res = client.post('/api/todos', json=TODO, headers=auth_headers)
    tid = res.get_json()['data']['id']

    client.put(f'/api/todos/{tid}', json={'done': True}, headers=auth_headers)
    res2 = client.get('/api/todos', headers=auth_headers)
    todo = res2.get_json()['data'][0]
    assert todo['done'] is True


def test_delete_todo(client, auth_headers):
    res = client.post('/api/todos', json=TODO, headers=auth_headers)
    tid = res.get_json()['data']['id']

    client.delete(f'/api/todos/{tid}', headers=auth_headers)
    res2 = client.get('/api/todos', headers=auth_headers)
    assert len(res2.get_json()['data']) == 0
