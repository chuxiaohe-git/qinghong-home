import requests
import random
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


@scrape_bp.route('/favicon', methods=['GET'])
def fetch_favicon():
    """从网址页面抓取真实的 favicon 地址"""
    url = request.args.get('url', '').strip()
    if not url:
        return error('请提供网址', 400)

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        from urllib.parse import urlparse
        domain = urlparse(url).hostname
        if domain:
            # 用 favicon.im 获取图标（国内可用的第三方服务）
            return success({'favicon': f'https://favicon.im/{domain}'})
        resp = requests.get(url, headers=HEADERS, timeout=8)
        domain = urlparse(url).netloc

        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'lxml')
            # 查找 <link rel="icon"> 或 <link rel="shortcut icon">
            icon_link = (
                soup.find('link', rel=lambda v: v and 'icon' in v.lower())
                or soup.find('link', attrs={'rel': 'apple-touch-icon'})
            )
            if icon_link:
                href = icon_link.get('href', '')
                if href:
                    # 处理相对路径
                    if href.startswith('//'):
                        href = 'https:' + href
                    elif href.startswith('/'):
                        parsed = urlparse(url)
                        href = f'{parsed.scheme}://{parsed.netloc}{href}'
                    elif not href.startswith(('http://', 'https://')):
                        parsed = urlparse(url)
                        href = f'{parsed.scheme}://{parsed.netloc}/{href.lstrip("/")}'
                    return success({'favicon': href})

        # 兜底：直接尝试 /favicon.ico
        fallback = f'https://{domain}/favicon.ico'
        return success({'favicon': fallback})

    except Exception as e:
        # 出错了也返回兜底地址
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        return success({'favicon': f'https://{domain}/favicon.ico'})
