"""备份恢复 + 配置导入导出测试"""
import json


class TestExportImport:
    """配置导出/导入"""

    def test_export(self, client, auth_headers):
        """导出配置"""
        # 先创建一些数据
        client.post('/api/groups', json={'name': '工作'}, headers=auth_headers)
        client.post('/api/todos', json={'title': '写周报', 'done': False}, headers=auth_headers)

        res = client.get('/api/export', headers=auth_headers)
        d = res.get_json()
        assert d['code'] == 200
        data = d['data']
        assert len(data['groups']) >= 1
        assert len(data['todos']) >= 1
        assert 'export_time' in data

    def test_import_append(self, client, auth_headers):
        """append 模式：追加，不覆盖"""
        # 导出空配置作为模板
        export_res = client.get('/api/export', headers=auth_headers)
        export_data = export_res.get_json()['data']

        # 先创建一个分组
        client.post('/api/groups', json={'name': '原始分组'}, headers=auth_headers)

        # 往导出数据里加一个新分组
        export_data['groups'].append({
            'name': '导入分组', 'icon': '', 'sort_order': 0
        })

        res = client.post('/api/import', json={
            'data': export_data, 'mode': 'append',
        }, headers=auth_headers)
        d = res.get_json()
        assert d['code'] == 200

        # 验证原来是 1 个 + 导入新增 = 2 个
        groups_res = client.get('/api/groups', headers=auth_headers)
        names = [g['name'] for g in groups_res.get_json()['data']]
        assert '原始分组' in names
        assert '导入分组' in names

    def test_import_overwrite(self, client, auth_headers):
        """overwrite 模式：清空后替换"""
        client.post('/api/groups', json={'name': '老数据'}, headers=auth_headers)

        export_res = client.get('/api/export', headers=auth_headers)
        export_data = export_res.get_json()['data']
        export_data['groups'] = [{'name': '新数据', 'icon': '', 'sort_order': 0}]
        export_data['bookmarks'] = []
        export_data['todos'] = []
        export_data['settings'] = []

        client.post('/api/import', json={
            'data': export_data, 'mode': 'overwrite',
        }, headers=auth_headers)

        groups_res = client.get('/api/groups', headers=auth_headers)
        names = [g['name'] for g in groups_res.get_json()['data']]
        assert '新数据' in names
        assert '老数据' not in names

    def test_import_merge_skips_duplicates(self, client, auth_headers, group):
        """merge 模式：URL 去重"""
        # 已有书签
        client.post('/api/bookmarks', json={
            'group_id': group['id'], 'title': '京东', 'url': 'https://jd.com',
        }, headers=auth_headers)

        export_res = client.get('/api/export', headers=auth_headers)
        export_data = export_res.get_json()['data']
        # 加一个同 URL 但标题不同的书签（merge 应该覆盖）
        for b in export_data['bookmarks']:
            if b['url'] == 'https://jd.com':
                b['title'] = '京东商城'

        # 加一个全新书签
        export_data['bookmarks'].append({
            'group_id': group['id'], 'title': '百度', 'url': 'https://baidu.com',
            'description': '', 'icon': '', 'bg_color': '#fff', 'sort_order': 0,
        })

        client.post('/api/import', json={
            'data': export_data, 'mode': 'merge',
        }, headers=auth_headers)

        bm_res = client.get('/api/bookmarks', headers=auth_headers)
        bms = bm_res.get_json()['data']
        titles = [b['title'] for b in bms]
        assert '京东商城' in titles  # 覆盖了
        assert '百度' in titles       # 新增了

    def test_import_invalid_data(self, client, auth_headers):
        """无效数据返回错误"""
        res = client.post('/api/import', json={}, headers=auth_headers)
        assert res.status_code == 400

    def test_export_requires_auth(self, client):
        res = client.get('/api/export')
        assert res.status_code == 401

    def test_import_requires_auth(self, client):
        res = client.post('/api/import', json={'data': {}})
        assert res.status_code == 401


class TestBackupRestore:
    """数据库备份/恢复（仅 super_admin）"""

    def test_create_backup(self, client, auth_headers):
        """创建备份需要 super_admin"""
        # admin 角色是 admin，不是 super_admin，所以应该被拒绝
        res = client.post('/api/backup', headers=auth_headers)
        d = res.get_json()
        assert d['code'] != 200  # 403

    def test_list_backups(self, client, auth_headers):
        res = client.get('/api/backups', headers=auth_headers)
        d = res.get_json()
        assert d['code'] != 200  # 403

    def test_restore_requires_admin(self, client, auth_headers):
        res = client.post('/api/restore', json={
            'type': 'local', 'name': 'nonexistent.db',
        }, headers=auth_headers)
        d = res.get_json()
        assert d['code'] != 200  # 403
