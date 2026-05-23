import logging
from flask import Blueprint, Response, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone
from extensions import db
from models.music_playlist import MusicPlaylistItem
from utils.response import success, error

logger = logging.getLogger(__name__)

music_bp = Blueprint('music', __name__, url_prefix='/api/music')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
}


@music_bp.route('/radio/random')
def radio_random():
    """代理网易云随机电台 API"""
    try:
        r = requests.get('https://api.52vmy.cn/api/music/wy/rand', headers=HEADERS, timeout=8)
        resp = Response(r.content, r.status_code, {
            'Content-Type': r.headers.get('Content-Type', 'application/json'),
            'Access-Control-Allow-Origin': '*',
        })
        return resp
    except Exception as e:
        logger.error(f"music: radio_random error: {e}")
        return error(str(e), status=500)


@music_bp.route('/lyric')
def lyric():
    """代理网易云歌词 API"""
    song_id = request.args.get('id', '')
    if not song_id:
        return error('缺少 id')

    try:
        r = requests.get(
            f'https://music.163.com/api/song/lyric?id={song_id}&lv=-1&kv=-1&tv=-1',
            headers={**HEADERS, 'Referer': 'https://music.163.com/'},
            timeout=8
        )
        data = r.json()
        lrc = ''
        if data.get('lrc', {}).get('lyric'):
            lrc = data['lrc']['lyric']
        elif data.get('tlyric', {}).get('lyric'):
            lrc = data['tlyric']['lyric']

        body, st = success(data={'lyric': lrc})
        return body, st, {'Access-Control-Allow-Origin': '*'}
    except Exception as e:
        logger.error(f"music: lyric error: {e}")
        return error(str(e), status=500)


# ── 歌曲海搜索 ──
@music_bp.route('/gequhai/search')
def gequhai_search():
    keyword = request.args.get('keyword', '')
    if not keyword:
        return error('请输入关键词')

    url = f'https://www.gequhai.com/s/{requests.utils.quote(keyword)}'
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        songs = []

        # 查找搜索结果表格中的歌曲行
        for tr in soup.select('table tbody tr'):
            tds = tr.find_all('td')
            if len(tds) < 3:
                continue
            # 第二列（索引1）：歌曲标题 + 链接
            a = tds[1].find('a') if tds[1] else None
            if not a:
                continue
            href = a.get('href', '')
            title = a.get_text(strip=True)
            match = re.search(r'/play/(\d+)', href)
            if not match:
                continue

            # 第三列（索引2）：歌手
            author = tds[2].get_text(strip=True) if len(tds) > 2 else ''

            songs.append({
                'songid': match.group(1),
                'title': title,
                'author': author,
                'source': 'gequhai',
            })

        return success(data=songs)
    except Exception as e:
        logger.error(f"music: gequhai_search error: {e}")
        return error(str(e), status=500)


# ── 歌曲海音频代理（解决 CORS + 支持 Range 请求） ──
@music_bp.route('/gequhai/proxy')
def gequhai_proxy():
    url = request.args.get('url', '')
    if not url:
        return error('缺少 URL')

    try:
        # 获取请求中的 Range 头（浏览器用来跳转进度）
        range_header = request.headers.get('Range', '')
        req_headers = dict(HEADERS)
        if range_header:
            req_headers['Range'] = range_header

        r = requests.get(url, headers=req_headers, stream=True, timeout=30)

        # 构建响应头，保留关键信息
        resp_headers = {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': r.headers.get('Content-Type', 'audio/mpeg'),
        }
        # 透传 Range 相关头（让浏览器能跳转进度）
        for h in ('Content-Range', 'Accept-Ranges', 'Content-Length'):
            if h in r.headers:
                resp_headers[h] = r.headers[h]

        return Response(
            r.iter_content(chunk_size=8192),
            status=r.status_code,
            headers=resp_headers,
        )
    except Exception as e:
        logger.error(f"music: gequhai_proxy error: {e}")
        return error(str(e), status=500)


# ── 歌曲海获取播放链接 ──
@music_bp.route('/gequhai/url', methods=['POST'])
def gequhai_url():
    data = request.get_json() or {}
    song_id = data.get('id', '')
    if not song_id:
        return error('缺少歌曲 ID')

    try:
        # 第一步：爬播放页，提取 play_id
        play_page = requests.get(f'https://www.gequhai.com/play/{song_id}', headers=HEADERS, timeout=10)
        play_page.encoding = 'utf-8'
        match = re.search(r"play_id\s*=\s*'([^']+)'", play_page.text)
        if not match:
            return error('无法获取播放凭证', status=500)
        real_id = requests.utils.unquote(match.group(1))  # URL 解码

        # 第二步：用 play_id 调 API 获取真实音源 URL
        r = requests.post('https://www.gequhai.com/api/music', data={
            'id': real_id,
            'type': 0,
        }, headers={
            **HEADERS,
            'X-Requested-With': 'XMLHttpRequest',
            'X-Custom-Header': 'SecretKey',
            'Referer': f'https://www.gequhai.com/play/{song_id}',
        }, timeout=10)

        result = r.json()
        if result.get('code') == 200:
            mp3_url = result['data']['url']
            # 转 HTTPS
            mp3_url = mp3_url.replace('http://', 'https://')
            return success(data={'url': mp3_url})
        else:
            return error(result.get('msg', '获取失败'), status=500)
    except Exception as e:
        logger.error(f"music: gequhai_url error: {e}")
        return error(str(e), status=500)


# ── 歌曲海获取歌词 ──
@music_bp.route('/gequhai/lyric')
def gequhai_lyric():
    song_id = request.args.get('id', '')
    if not song_id:
        return error('缺少歌曲 ID')

    try:
        r = requests.get(f'https://www.gequhai.com/play/{song_id}', headers=HEADERS, timeout=10)
        r.encoding = 'utf-8'
        # 从 HTML 中提取 LRC 格式歌词行 [MM:SS.xx]...
        lrc_lines = re.findall(r'\[\d+:\d+\.?\d*\].*', r.text)
        if lrc_lines:
            # 去掉 HTML 标签（<br /> 等）
            lyric = '\n'.join([re.sub(r'<[^>]+>', '', l) for l in lrc_lines])
            return success(data={'lyric': lyric})
        else:
            return success(data={'lyric': ''})
    except Exception as e:
        logger.error(f"music: gequhai_lyric error: {e}")
        return error(str(e), status=500)


# ── 播放列表 CRUD ──
@music_bp.route('/playlist', methods=['GET'])
@jwt_required()
def get_playlist():
    user_id = int(get_jwt_identity())
    items = MusicPlaylistItem.query.filter_by(user_id=user_id).order_by(MusicPlaylistItem.sort_order).all()
    return success(data=[item.to_dict() for item in items])


@music_bp.route('/playlist', methods=['POST'])
@jwt_required()
def add_to_playlist():
    user_id = int(get_jwt_identity())
    body = request.get_json() or {}
    songid = body.get('songid', '')
    if not songid:
        return error('缺少 songid')

    # 去重：同用户+同songid不重复添加
    exists = MusicPlaylistItem.query.filter_by(user_id=user_id, songid=songid).first()
    if exists:
        return success(data=exists.to_dict(), message='已在列表中')

    max_sort = db.session.query(db.func.max(MusicPlaylistItem.sort_order)).filter_by(user_id=user_id).scalar() or 0

    item = MusicPlaylistItem(
        user_id=user_id,
        songid=songid,
        title=body.get('title', ''),
        author=body.get('author', ''),
        source=body.get('source', 'gequhai'),
        url=body.get('url', ''),
        lrc=body.get('lrc', ''),
        sort_order=max_sort + 1,
        fetched_at=datetime.now(timezone.utc),
    )
    try:
        db.session.add(item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"music: add_to_playlist DB error: {e}")
        return error('操作失败', status=500)
    return success(data=item.to_dict())


@music_bp.route('/playlist/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remove_from_playlist(item_id):
    user_id = int(get_jwt_identity())
    item = MusicPlaylistItem.query.filter_by(id=item_id, user_id=user_id).first()
    if not item:
        return error('未找到', status=404)
    try:
        db.session.delete(item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"music: remove_from_playlist DB error: {e}")
        return error('操作失败', status=500)
    return success(message='已移除')


@music_bp.route('/playlist/refresh', methods=['POST'])
@jwt_required()
def refresh_playlist_url():
    """刷新某首歌的播放地址（失效时重新爬）"""
    user_id = int(get_jwt_identity())
    body = request.get_json() or {}
    item_id = body.get('id', '')
    song_id = body.get('songid', '')

    if item_id:
        item = MusicPlaylistItem.query.filter_by(id=item_id, user_id=user_id).first()
    elif song_id:
        item = MusicPlaylistItem.query.filter_by(user_id=user_id, songid=song_id).first()
    else:
        return error('缺少 id 或 songid', status=400)

    if not item:
        return error('未找到', status=404)

    target_id = item.songid

    # 重新爬播放地址
    try:
        play_page = requests.get(f'https://www.gequhai.com/play/{target_id}', headers=HEADERS, timeout=10)
        play_page.encoding = 'utf-8'
        match = re.search(r"play_id\s*=\s*'([^']+)'", play_page.text)
        if not match:
            return error('无法获取播放凭证', status=500)
        real_id = requests.utils.unquote(match.group(1))

        r = requests.post('https://www.gequhai.com/api/music', data={
            'id': real_id, 'type': 0,
        }, headers={
            **HEADERS, 'X-Requested-With': 'XMLHttpRequest',
            'X-Custom-Header': 'SecretKey',
            'Referer': f'https://www.gequhai.com/play/{target_id}',
        }, timeout=10)

        result = r.json()
        if result.get('code') == 200:
            mp3_url = result['data']['url'].replace('http://', 'https://')
            item.url = mp3_url
            item.fetched_at = datetime.now(timezone.utc)
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"music: refresh_playlist_url DB error: {e}")
                return error('操作失败', status=500)
            return success(data={'url': mp3_url, 'item': item.to_dict()})
        else:
            return error(result.get('msg', '刷新失败'), status=500)
    except Exception as e:
        logger.error(f"music: refresh_playlist_url error: {e}")
        return error(str(e), status=500)
