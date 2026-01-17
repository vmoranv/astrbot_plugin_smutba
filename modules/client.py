"""
SmutBase API 客户端
"""

import html
import re
import asyncio
import aiohttp
import logging
from typing import Optional
from urllib.parse import urlencode
from bs4 import BeautifulSoup

from .consts import (
    ROOT_URL, HEADERS, Category, SortBy,
    REGEX_MODEL_ID, REGEX_MODEL_ID_ALT, REGEX_AUTHOR,
    REGEX_VIEWS, REGEX_DOWNLOADS, REGEX_POSTED,
    REGEX_PUBLISHED, REGEX_UPDATED, REGEX_CATEGORY,
    REGEX_THUMBNAIL_ALT,
)
from .errors import (
    InvalidModelID,
    ModelNotFound, NetworkError,
)
from .model import Model, Author, SearchResult


class Client:
    """SmutBase API 客户端"""
    
    def __init__(
        self,
        proxy: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        初始化客户端
        
        Args:
            proxy: 代理地址，如 "http://127.0.0.1:7890"
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.proxy = proxy
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.logger = logging.getLogger("SmutBase.Client")
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建HTTP会话"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(ssl=False)
            self._session = aiohttp.ClientSession(
                headers=HEADERS,
                timeout=self.timeout,
                connector=connector,
                trust_env=True,
            )
        return self._session
    
    async def close(self):
        """关闭HTTP会话"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def _fetch(self, url: str, **kwargs) -> str:
        """
        发送HTTP GET请求
        
        Args:
            url: 请求URL
            **kwargs: 传递给aiohttp的额外参数
            
        Returns:
            响应文本内容
        """
        session = await self._get_session()
        
        for attempt in range(self.max_retries):
            try:
                async with session.get(
                    url,
                    proxy=self.proxy,
                    **kwargs
                ) as response:
                    if response.status == 404:
                        raise ModelNotFound(f"页面不存在: {url}")
                    if response.status != 200:
                        raise NetworkError(f"HTTP {response.status}: {url}")
                    
                    text = await response.text()
                    return html.unescape(text)
                    
            except aiohttp.ClientError as e:
                self.logger.warning(f"请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise NetworkError(f"网络请求失败: {e}")
                await asyncio.sleep(1 * (attempt + 1))
        
        raise NetworkError(f"请求失败: {url}")
    
    def _parse_model_page(self, html_content: str, model: Model) -> Model:
        """
        解析模型详情页面
        
        Args:
            html_content: HTML内容
            model: 要更新的Model对象
            
        Returns:
            更新后的Model对象
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 解析标题
        title_elem = soup.find('h1')
        if title_elem:
            model.title = title_elem.get_text(strip=True)
        
        # 解析作者信息
        author_match = REGEX_AUTHOR.search(html_content)
        if author_match:
            author_url = author_match.group(1)
            author_name = author_match.group(2).strip()
            model.author = Author(name=author_name, url=author_url)
        
        # 解析缩略图
        thumbnail_match = REGEX_THUMBNAIL_ALT.search(html_content)
        if thumbnail_match:
            model.thumbnail = thumbnail_match.group(1)
        else:
            # 尝试从页面中查找大图
            img_tags = soup.find_all('img')
            for img in img_tags:
                src = img.get('src', '')
                if 'project' in src or 'thumbnail' in src.lower():
                    model.thumbnail = src
                    break
        
        # 解析统计信息
        views_match = REGEX_VIEWS.search(html_content)
        if views_match:
            try:
                model.views = int(views_match.group(1).replace(',', ''))
            except ValueError:
                pass
        
        downloads_match = REGEX_DOWNLOADS.search(html_content)
        if downloads_match:
            try:
                model.downloads = int(downloads_match.group(1).replace(',', ''))
            except ValueError:
                pass
        
        # 解析日期信息
        posted_match = REGEX_POSTED.search(html_content)
        if posted_match:
            model.posted = posted_match.group(1).strip()
        
        published_match = REGEX_PUBLISHED.search(html_content)
        if published_match:
            model.published = published_match.group(1).strip()
        
        updated_match = REGEX_UPDATED.search(html_content)
        if updated_match:
            model.updated = updated_match.group(1).strip()
        
        # 解析分类
        category_match = REGEX_CATEGORY.search(html_content)
        if category_match:
            model.category = category_match.group(1).strip()
        
        # 解析许可证
        licence_elem = soup.find(string=re.compile(r'Creative Commons|CC BY|CC0|License', re.I))
        if licence_elem:
            parent = licence_elem.find_parent()
            if parent:
                model.licence = parent.get_text(strip=True)[:100]
        
        # 解析标签
        tag_links = soup.find_all('a', href=re.compile(r'/tag/'))
        model.tags = [tag.get_text(strip=True) for tag in tag_links[:10]]
        
        # 保存原始HTML
        model._html_content = html_content
        
        return model
    
    def _parse_search_results(self, html_content: str) -> SearchResult:
        """
        解析搜索结果页面
        
        Args:
            html_content: HTML内容
            
        Returns:
            SearchResult对象
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        result = SearchResult()
        
        # 查找所有模型卡片
        # SmutBase 使用 UUID 格式的项目ID
        model_cards = soup.find_all('a', href=re.compile(r'/project/[a-f0-9-]+/'))
        
        seen_ids = set()
        for card in model_cards:
            href = card.get('href', '')
            # 尝试匹配 UUID 格式
            match = REGEX_MODEL_ID.search(href) or REGEX_MODEL_ID_ALT.search(href)
            if not match:
                # 尝试更宽松的匹配
                uuid_match = re.search(r'/project/([^/]+)/', href)
                if not uuid_match:
                    continue
                model_id = uuid_match.group(1)
            else:
                model_id = match.group(1)
            
            if model_id in seen_ids:
                continue
            seen_ids.add(model_id)
            
            # 创建模型对象
            model = Model.from_id(model_id)
            
            # 尝试获取标题
            title_elem = card.find(['h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div'])
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                if title_text and len(title_text) > 2:
                    model.title = title_text
            
            # 如果没有找到标题，尝试从card本身获取
            if not model.title:
                card_text = card.get_text(strip=True)
                if card_text and len(card_text) < 100:
                    model.title = card_text[:50]
            
            # 尝试获取缩略图
            img = card.find('img')
            if img:
                model.thumbnail = img.get('src', '') or img.get('data-src', '')
            
            # 尝试获取作者信息
            author_elem = card.find_next('a', href=re.compile(r'/member/|/user/|patreon'))
            if author_elem:
                author_name = author_elem.get_text(strip=True)
                author_url = author_elem.get('href', '')
                if author_name:
                    model.author = Author(name=author_name, url=author_url)
            
            result.models.append(model)
        
        # 解析分页信息
        pagination = soup.find_all('a', href=re.compile(r'\?page=\d+'))
        if pagination:
            max_page = 1
            for page_link in pagination:
                page_match = re.search(r'page=(\d+)', page_link.get('href', ''))
                if page_match:
                    page_num = int(page_match.group(1))
                    max_page = max(max_page, page_num)
            result.total_pages = max_page
        
        # 获取当前页
        current_page_elem = soup.find('a', class_=re.compile(r'active|current'))
        if current_page_elem:
            page_match = re.search(r'page=(\d+)', current_page_elem.get('href', ''))
            if page_match:
                result.current_page = int(page_match.group(1))
        
        return result
    
    async def get_model(self, model_id: str) -> Model:
        """
        获取模型详情
        
        Args:
            model_id: 模型ID或URL
            
        Returns:
            Model对象
        """
        try:
            model = Model.from_id(model_id)
        except ValueError as e:
            raise InvalidModelID(str(e))
        
        html_content = await self._fetch(model.full_url)
        
        # 检查是否是404页面
        if "Page not Found" in html_content or "页面不存在" in html_content:
            raise ModelNotFound(f"模型不存在: {model_id}")
        
        return self._parse_model_page(html_content, model)
    
    async def search(
        self,
        query: str = "",
        category: str = Category.ANY,
        sort_by: str = SortBy.LAST_UPDATED,
        page: int = 1,
        furry: bool = False,
    ) -> SearchResult:
        """
        搜索模型
        
        Args:
            query: 搜索关键词
            category: 分类筛选
            sort_by: 排序方式
            page: 页码
            furry: 是否包含furry内容
            
        Returns:
            SearchResult对象
        """
        params = {}
        
        if query:
            params['q'] = query
        
        if category != Category.ANY:
            params['category'] = category
        
        if sort_by != SortBy.LAST_UPDATED:
            params['sort'] = sort_by
        
        if page > 1:
            params['page'] = str(page)
        
        if furry:
            params['furry'] = 'on'
        
        url = ROOT_URL + "/"
        if params:
            url += "?" + urlencode(params)
        
        html_content = await self._fetch(url)
        result = self._parse_search_results(html_content)
        result.query = query
        result.current_page = page
        
        return result
    
    async def get_latest(self, page: int = 1, category: str = Category.ANY) -> SearchResult:
        """
        获取最新模型
        
        Args:
            page: 页码
            category: 分类筛选
            
        Returns:
            SearchResult对象
        """
        return await self.search(
            query="",
            category=category,
            sort_by=SortBy.NEWEST,
            page=page,
        )
    
    async def get_popular(self, page: int = 1, category: str = Category.ANY) -> SearchResult:
        """
        获取热门模型
        
        Args:
            page: 页码
            category: 分类筛选
            
        Returns:
            SearchResult对象
        """
        return await self.search(
            query="",
            category=category,
            sort_by=SortBy.MOST_VIEWED,
            page=page,
        )
    
    async def get_random(self) -> Optional[Model]:
        """
        获取随机模型
        
        Returns:
            随机Model对象或None
        """
        import random
        
        # 先获取首页看看有多少页
        result = await self.search()
        
        if not result.models:
            return None
        
        # 随机选择一个页面
        random_page = random.randint(1, min(result.total_pages, 50))
        
        # 获取该页的模型
        page_result = await self.search(page=random_page)
        
        if not page_result.models:
            return random.choice(result.models) if result.models else None
        
        # 随机选择一个模型并获取详情
        random_model = random.choice(page_result.models)
        return await self.get_model(random_model.model_id)
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()