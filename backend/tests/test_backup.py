"""书签 HTML 导入解析器测试"""
import io

from routes.backup import _parse_bookmark_map, import_bookmarks_html
from app import create_app
from extensions import db as _db


class TestParseBookmarkMap:
    """_parse_bookmark_map 单元测试（不依赖 Flask）"""

    def test_simple_folder(self):
        html = '''<DL><p>
            <DT><H3>工作</H3>
            <DL><p>
                <DT><A HREF="https://work.com">工作台</A>
                <DT><A HREF="https://mail.com">邮箱</A>
            </DL><p>
        </DL><p>'''
        m = _parse_bookmark_map(html)
        assert m['https://work.com'] == '工作'
        assert m['https://mail.com'] == '工作'

    def test_multiple_folders(self):
        html = '''<DL><p>
            <DT><H3>工作</H3>
            <DL><p>
                <DT><A HREF="https://work.com">工作台</A>
            </DL><p>
            <DT><H3>娱乐</H3>
            <DL><p>
                <DT><A HREF="https://game.com">游戏</A>
            </DL><p>
        </DL><p>'''
        m = _parse_bookmark_map(html)
        assert m['https://work.com'] == '工作'
        assert m['https://game.com'] == '娱乐'

    def test_nested_folders(self):
        html = '''<DL><p>
            <DT><H3>书签栏</H3>
            <DL><p>
                <DT><A HREF="https://a.com">直放链接</A>
                <DT><H3>工作</H3>
                <DL><p>
                    <DT><A HREF="https://work.com">工作台</A>
                    <DT><H3>子文件夹</H3>
                    <DL><p>
                        <DT><A HREF="https://sub.com">嵌套链接</A>
                    </DL><p>
                </DL><p>
            </DL><p>
        </DL><p>'''
        m = _parse_bookmark_map(html)
        assert m['https://a.com'] == '书签栏'
        assert m['https://work.com'] == '工作'
        assert m['https://sub.com'] == '子文件夹'

    def test_loose_bookmarks_become_uncategorized(self):
        html = '''<DL><p>
            <DT><H3>工作</H3>
            <DL><p>
                <DT><A HREF="https://work.com">工作台</A>
            </DL><p>
            <DT><A HREF="https://loose.com">未分类链接</A>
        </DL><p>'''
        m = _parse_bookmark_map(html)
        assert m['https://work.com'] == '工作'
        assert m['https://loose.com'] == '未分类'

    def test_skip_place_and_javascript(self):
        html = '''<DL><p>
            <DT><A HREF="place:folder">占位</A>
            <DT><A HREF="javascript:void(0)">JS</A>
            <DT><A HREF="https://real.com">真实链接</A>
        </DL><p>'''
        m = _parse_bookmark_map(html)
        assert 'place:folder' not in m
        assert 'javascript:void(0)' not in m
        assert 'https://real.com' in m

    def test_chrome_full_export(self):
        """模拟真实的 Chrome 书签导出结构"""
        html = '''<!DOCTYPE NETSCAPE-Bookmark-file-1>
        <META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
        <TITLE>Bookmarks</TITLE>
        <H1>Bookmarks</H1>
        <DL><p>
            <DT><H3 ADD_DATE="123" PERSONAL_TOOLBAR_FOLDER="true">书签栏</H3>
            <DL><p>
                <DT><A HREF="https://jd.com" ADD_DATE="123">京东</A>
                <DT><A HREF="https://weibo.com" ADD_DATE="456">微博</A>
                <DT><H3 ADD_DATE="789">工具</H3>
                <DL><p>
                    <DT><A HREF="https://github.com" ADD_DATE="101">GitHub</A>
                </DL><p>
            </DL><p>
        </DL><p>'''
        m = _parse_bookmark_map(html)
        assert m['https://jd.com'] == '书签栏'
        assert m['https://weibo.com'] == '书签栏'
        assert m['https://github.com'] == '工具'

    def test_multiline_a_tag(self):
        """多行属性不应当影响解析"""
        html = '''<DL><p>
            <DT><H3>工作</H3>
            <DL><p>
                <DT><A HREF="https://work.com"
                      ADD_DATE="123" ICON="data:png">工作台</A>
            </DL><p>
        </DL><p>'''
        m = _parse_bookmark_map(html)
        assert m['https://work.com'] == '工作'

    def test_empty_folder_name_skipped(self):
        html = '''<DL><p>
            <DT><H3></H3>
            <DL><p>
                <DT><A HREF="https://x.com">X</A>
            </DL><p>
            <DT><A HREF="https://y.com">Y</A>
        </DL><p>'''
        m = _parse_bookmark_map(html)
        # 空文件夹名被跳过，链接归上一级
        assert 'https://y.com' in m


class TestBookmarkImportEndpoint:
    """书签导入 API 集成测试"""

    def test_import_bookmarks_file(self, client, auth_headers):
        """上传书签 HTML 文件"""
        html_content = '''<DL><p>
            <DT><H3>工作</H3>
            <DL><p>
                <DT><A HREF="https://work.com">工作台</A>
                <DT><A HREF="https://mail.com">公司邮箱</A>
            </DL><p>
            <DT><H3>娱乐</H3>
            <DL><p>
                <DT><A HREF="https://game.com">游戏</A>
            </DL><p>
        </DL><p>'''
        data = {'file': (io.BytesIO(html_content.encode()), 'bookmarks.html')}
        res = client.post('/api/import/bookmarks', data=data,
                          content_type='multipart/form-data',
                          headers=auth_headers)
        d = res.get_json()
        assert d['code'] == 200
        assert d['data']['imported'] == 3
        assert d['data']['groups_created'] == 2

    def test_import_non_html_rejected(self, client, auth_headers):
        data = {'file': (io.BytesIO(b'not html'), 'bookmarks.txt')}
        res = client.post('/api/import/bookmarks', data=data,
                          headers=auth_headers)
        d = res.get_json()
        assert d['code'] != 200

    def test_import_no_file_rejected(self, client, auth_headers):
        res = client.post('/api/import/bookmarks', headers=auth_headers)
        assert res.get_json()['code'] != 200

    def test_import_requires_auth(self, client):
        data = {'file': (io.BytesIO(b'<html></html>'), 'b.html')}
        res = client.post('/api/import/bookmarks', data=data)
        assert res.status_code == 401

    def test_real_chrome_bookmarks(self, client, auth_headers):
        """模拟真实的 Chrome 书签文件，包含嵌套 + 多文件夹"""
        html = '''<!DOCTYPE NETSCAPE-Bookmark-file-1>
        <META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
        <TITLE>Bookmarks</TITLE>
        <H1>Bookmarks</H1>
        <DL><p>
            <DT><H3 ADD_DATE="123" PERSONAL_TOOLBAR_FOLDER="true">书签栏</H3>
            <DL><p>
                <DT><A HREF="https://jd.com">京东</A>
                <DT><A HREF="https://baidu.com">百度</A>
                <DT><H3 ADD_DATE="456">工具</H3>
                <DL><p>
                    <DT><A HREF="https://github.com">GitHub</A>
                    <DT><A HREF="https://stackoverflow.com">StackOverflow</A>
                </DL><p>
                <DT><H3 ADD_DATE="789">代理</H3>
                <DL><p>
                    <DT><A HREF="https://google.com">Google</A>
                </DL><p>
            </DL><p>
        </DL><p>'''
        data = {'file': (io.BytesIO(html.encode()), 'chrome_bookmarks.html')}
        res = client.post('/api/import/bookmarks', data=data,
                          headers=auth_headers)
        d = res.get_json()
        assert d['code'] == 200
        assert d['data']['imported'] == 5
        assert d['data']['groups_created'] == 3

        # 验证书签已入库且分组正确
        groups_res = client.get('/api/groups', headers=auth_headers)
        group_names = [g['name'] for g in groups_res.get_json()['data']]
        assert '工具' in group_names
        assert '代理' in group_names

        bm_res = client.get('/api/bookmarks?group_id=' + str(
            [g for g in groups_res.get_json()['data'] if g['name'] == '工具'][0]['id']
        ), headers=auth_headers)
        bm_titles = [b['title'] for b in bm_res.get_json()['data']]
        assert 'GitHub' in bm_titles
        assert 'StackOverflow' in bm_titles
