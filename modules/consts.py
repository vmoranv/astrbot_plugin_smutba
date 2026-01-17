"""
SmutBase API 常量定义
"""

import re

# 基础URL
ROOT_URL = "https://smutba.se"
API_SEARCH = "/search/"
MODEL_URL = "/project/"

# HTTP请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# 正则表达式模式
# 从URL提取ID: https://smutba.se/project/b8c7264b-29e7-4091-bb73-3eac2fddb350/ -> UUID
REGEX_MODEL_ID = re.compile(r"/project/([a-f0-9-]{36})")
REGEX_MODEL_ID_ALT = re.compile(r"/project/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})")

# 从页面提取信息
REGEX_TITLE = re.compile(r'<h1 class="model-title[^"]*"[^>]*>([^<]+)</h1>', re.IGNORECASE)
REGEX_AUTHOR = re.compile(r'Support\s+<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', re.IGNORECASE)
REGEX_VIEWS = re.compile(r'<strong>Views</strong>\s*<br[^>]*>\s*(\d+)', re.IGNORECASE | re.DOTALL)
REGEX_DOWNLOADS = re.compile(r'<strong>Downloads</strong>\s*<br[^>]*>\s*(\d+)', re.IGNORECASE | re.DOTALL)
REGEX_POSTED = re.compile(r'<strong>Posted</strong>\s*<br[^>]*>\s*([^<]+)<', re.IGNORECASE | re.DOTALL)
REGEX_PUBLISHED = re.compile(r'<strong>Published</strong>\s*<br[^>]*>\s*([^<]+)<', re.IGNORECASE | re.DOTALL)
REGEX_UPDATED = re.compile(r'<strong>Updated</strong>\s*<br[^>]*>\s*([^<]+)<', re.IGNORECASE | re.DOTALL)
REGEX_CATEGORY = re.compile(r'<strong>Category</strong>\s*<br[^>]*>\s*<a[^>]*>([^<]+)</a>', re.IGNORECASE | re.DOTALL)
REGEX_THUMBNAIL = re.compile(r'<img[^>]*class="[^"]*model-thumbnail[^"]*"[^>]*src="([^"]+)"', re.IGNORECASE)
REGEX_THUMBNAIL_ALT = re.compile(r'<meta\s+property="og:image"\s+content="([^"]+)"', re.IGNORECASE)

# 搜索结果页面提取
REGEX_SEARCH_ITEM = re.compile(
    r'<a[^>]*href="(/project/[a-f0-9-]+/)"[^>]*class="[^"]*model-card[^"]*"[^>]*>.*?'
    r'<img[^>]*src="([^"]+)"[^>]*>.*?'
    r'<h\d[^>]*class="[^"]*model-title[^"]*"[^>]*>([^<]+)</h\d>',
    re.IGNORECASE | re.DOTALL
)

# 分页信息
REGEX_PAGINATION = re.compile(r'<a[^>]*href="[^"]*\?page=(\d+)"[^>]*>\s*(\d+|»)\s*</a>', re.IGNORECASE)
REGEX_TOTAL_PAGES = re.compile(r'<a[^>]*href="[^"]*\?page=(\d+)"[^>]*>\s*\d+\s*</a>(?=.*?<a[^>]*>»</a>)', re.IGNORECASE | re.DOTALL)

# 分类枚举
class Category:
    ANY = "any"
    MODELS = "1"
    TEXTURES = "2"
    SCENERIES = "3"
    HDRIS = "4"
    OTHER = "5"
    
    @classmethod
    def all(cls):
        return {
            "any": cls.ANY,
            "models": cls.MODELS,
            "textures": cls.TEXTURES,
            "sceneries": cls.SCENERIES,
            "hdris": cls.HDRIS,
            "other": cls.OTHER,
        }

# 排序选项
class SortBy:
    LAST_UPDATED = "last_updated"
    NEWEST = "newest"
    OLDEST = "oldest"
    MOST_VIEWED = "most_viewed"
    MOST_DOWNLOADED = "most_downloaded"
    
    @classmethod
    def all(cls):
        return {
            "last_updated": cls.LAST_UPDATED,
            "newest": cls.NEWEST,
            "oldest": cls.OLDEST,
            "most_viewed": cls.MOST_VIEWED,
            "most_downloaded": cls.MOST_DOWNLOADED,
        }