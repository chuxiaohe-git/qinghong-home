import requests
import random
import os
import time
import io
from flask import Blueprint, request
from bs4 import BeautifulSoup
from utils.response import success, error

scrape_bp = Blueprint('scrape', __name__, url_prefix='/api/scrape')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

ARCHIVE_KEYWORDS = [
    'star', 'heart', 'home', 'user', 'book', 'mail', 'clock', 'cloud',
    'search', 'link', 'image', 'folder', 'map', 'flag', 'bell', 'cog',
    'chart', 'tool', 'globe', 'message', 'photo', 'music', 'video',
    'lock', 'key', 'calendar', 'download', 'upload', 'shield', 'fire',
    'light', 'moon', 'sun', 'eye', 'cart', 'gift', 'pen', 'phone',
    'arrow', 'camera', 'tag', 'basket', 'pencil', 'wifi', 'print',
    'dog', 'cat', 'fish', 'bird', 'tree', 'flower', 'mountain', 'ocean',
    'car', 'plane', 'train', 'ship', 'bike', 'rocket', 'bulb', 'coffee',
    'cup', 'food', 'cake', 'candy', 'ball', 'trophy', 'medal', 'hat',
    'shoe', 'bag', 'glass', 'ring', 'lamp', 'bed', 'sofa', 'table',
    'robot', 'alien', 'ghost', 'diamond', 'crown', 'key', 'gear',
    'house', 'shop', 'bank', 'school', 'hospital', 'church', 'castle',
    'rain', 'snow', 'sun', 'moon', 'cloud', 'leaf', 'egg', 'bone',
]

ARCHIVE_CATEGORIES = [
    'animals', 'food', 'music', 'sport', 'business', 'technology',
    'nature', 'people', 'transport', 'game', 'love', 'halloween',
    'christmas', 'medical', 'mobile', 'social-network', 'flags',
    'cartoon', 'emoji', 'mini',
]


@scrape_bp.route('/icons', methods=['GET'])
def scrape_icons():
    """抓取 IconArchive 彩色图标（多源随机）"""
    source = request.args.get('source', 'archive')

    if source != 'archive':
        return error('不支持的来源', 400)

    session = requests.Session()
    all_icons = []
    seen_urls = set()

    # 1. 从标签页随机挑 8 个语义词
    words = random.sample(ARCHIVE_KEYWORDS, min(8, len(ARCHIVE_KEYWORDS)))
    for word in words:
        try:
            resp = session.get(
                f'https://www.iconarchive.com/tag/{word}',
                headers=HEADERS,
                timeout=8,
            )
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, 'lxml')
            for a in soup.select('a[href*="/show/"]'):
                img = a.find('img')
                if not img:
                    continue
                src = img.get('src', '')
                alt = img.get('alt', '') or ''
                if not src or 'iconarchive' not in src:
                    continue
                if src in seen_urls:
                    continue
                seen_urls.add(src)
                thumbnail = src.replace('/128/', '/64/')
                all_icons.append({
                    'name': alt,
                    'url': src,
                    'thumbnail': thumbnail,
                })
        except Exception:
            continue

    # 2. 从分类页随机挑 3 个
    cats = random.sample(ARCHIVE_CATEGORIES, min(3, len(ARCHIVE_CATEGORIES)))
    for cat in cats:
        try:
            resp = session.get(
                f'https://www.iconarchive.com/category/{cat}-icons.html',
                headers=HEADERS,
                timeout=8,
            )
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, 'lxml')
            for a in soup.select('a[href*="/show/"]'):
                img = a.find('img')
                if not img:
                    continue
                src = img.get('src', '')
                alt = img.get('alt', '') or ''
                if not src or 'iconarchive' not in src:
                    continue
                if src in seen_urls:
                    continue
                seen_urls.add(src)
                thumbnail = src.replace('/128/', '/64/')
                all_icons.append({
                    'name': alt,
                    'url': src,
                    'thumbnail': thumbnail,
                })
        except Exception:
            continue

    if not all_icons:
        return success({'icons': []})

    random.shuffle(all_icons)
    icons = all_icons[:30]

    return success({'icons': icons})


FAVICON_SIZE = 50  # 固定裁剪尺寸


def _resize_favicon(img):
    """将图标居中裁剪为正方形并缩放到 FAVICON_SIZE"""
    from PIL import Image
    w, h = img.size
    # 转 RGBA 统一处理（兼容 ico / 带 alpha 的 png）
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    # 居中裁切正方形
    min_dim = min(w, h)
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    img = img.crop((left, top, left + min_dim, top + min_dim))
    # 超过目标尺寸才缩放
    if min_dim > FAVICON_SIZE:
        img = img.resize((FAVICON_SIZE, FAVICON_SIZE), Image.LANCZOS)
    return img


@scrape_bp.route('/favicon', methods=['GET'])
def fetch_favicon():
    """从网址获取图标，大图自动裁剪到 50x50 并存到本地"""
    # 延迟导入，避免没装 Pillow 时整个服务崩掉
    from config import Config

    url = request.args.get('url', '').strip()
    if not url:
        return error('请提供网址', 400)

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        from urllib.parse import urlparse
        domain = urlparse(url).hostname
        if not domain:
            return error('无法解析域名', 400)

        # 收集候选图标 URL
        candidates = []

        # ① 尝试从 HTML 中解析声明的 icon
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'lxml')
                icon_link = (
                    soup.find('link', rel=lambda v: v and 'icon' in v.lower())
                    or soup.find('link', attrs={'rel': 'apple-touch-icon'})
                )
                if icon_link:
                    href = icon_link.get('href', '')
                    if href:
                        if href.startswith('//'):
                            href = 'https:' + href
                        elif href.startswith('/'):
                            href = f'https://{domain}{href}'
                        elif not href.startswith(('http://', 'https://')):
                            href = f'https://{domain}/{href.lstrip("/")}'
                        candidates.append(href)
        except Exception:
            pass

        # ② favicon.im 第三方服务
        candidates.append(f'https://favicon.im/{domain}')

        # ③ 标准 /favicon.ico
        candidates.append(f'https://{domain}/favicon.ico')

        # 检查 Pillow 是否可用
        try:
            from PIL import Image as _PILImage
        except ImportError:
            _PILImage = None

        # 逐个尝试下载并处理
        for candidate in candidates:
            try:
                img_resp = requests.get(candidate, headers=HEADERS, timeout=6)
                if img_resp.status_code != 200:
                    continue
                # 有 Pillow 就裁剪保存，没有就直接返回 URL
                if _PILImage is not None:
                    img = _PILImage.open(io.BytesIO(img_resp.content))
                    img = _resize_favicon(img)
                    ext = 'png'
                    filename = f'fav_{domain}_{int(time.time())}.{ext}'
                    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
                    img.save(filepath, 'PNG')
                    return success({'favicon': f'/uploads/{filename}'})
                else:
                    return success({'favicon': candidate})
            except Exception:
                continue

        # 全部失败，返回原始 URL 让前端自己显示
        return success({'favicon': f'https://favicon.im/{domain}'})

    except Exception as e:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        return success({'favicon': f'https://favicon.im/{domain}'})
