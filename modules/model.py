"""
SmutBase 数据模型类定义
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List
from urllib.parse import urljoin

from .consts import ROOT_URL, REGEX_MODEL_ID


@dataclass
class Author:
    """作者/上传者模型"""
    name: str
    url: str = ""
    
    @property
    def profile_url(self) -> str:
        """获取作者主页完整URL"""
        if self.url.startswith("http"):
            return self.url
        return urljoin(ROOT_URL, self.url) if self.url else ""
    
    def __str__(self) -> str:
        return self.name


@dataclass
class Model:
    """3D模型数据类"""
    model_id: str
    url: str
    title: str = ""
    author: Optional[Author] = None
    thumbnail: str = ""
    views: int = 0
    downloads: int = 0
    posted: str = ""
    published: str = ""
    updated: str = ""
    category: str = ""
    licence: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    
    # 原始HTML内容（用于进一步解析）
    _html_content: str = field(default="", repr=False)
    
    @classmethod
    def from_id(cls, model_id: str) -> "Model":
        """从模型ID创建Model对象"""
        model_id = str(model_id).strip()
        
        # UUID 格式验证
        uuid_pattern = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', re.I)
        
        if uuid_pattern.match(model_id):
            # 已经是有效的UUID
            url = f"{ROOT_URL}/project/{model_id}/"
            return cls(model_id=model_id, url=url)
        
        # 可能是URL，尝试提取ID
        match = REGEX_MODEL_ID.search(model_id)
        if match:
            model_id = match.group(1)
            url = f"{ROOT_URL}/project/{model_id}/"
            return cls(model_id=model_id, url=url)
        
        # 尝试更宽松的匹配
        loose_match = re.search(r'/project/([^/]+)/', model_id)
        if loose_match:
            model_id = loose_match.group(1)
            url = f"{ROOT_URL}/project/{model_id}/"
            return cls(model_id=model_id, url=url)
        
        raise ValueError(f"无效的模型ID: {model_id}")
    
    @classmethod
    def from_url(cls, url: str) -> "Model":
        """从URL创建Model对象"""
        match = REGEX_MODEL_ID.search(url)
        if match:
            model_id = match.group(1)
            return cls(model_id=model_id, url=url)
        
        # 尝试更宽松的匹配
        loose_match = re.search(r'/project/([^/]+)/', url)
        if loose_match:
            model_id = loose_match.group(1)
            return cls(model_id=model_id, url=url)
        
        raise ValueError(f"无效的模型URL: {url}")
    
    @property
    def full_url(self) -> str:
        """获取完整URL"""
        if self.url.startswith("http"):
            return self.url
        return urljoin(ROOT_URL, self.url)
    
    @property
    def thumbnail_url(self) -> str:
        """获取缩略图完整URL"""
        if not self.thumbnail:
            return ""
        if self.thumbnail.startswith("http"):
            return self.thumbnail
        return urljoin(ROOT_URL, self.thumbnail)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "model_id": self.model_id,
            "url": self.full_url,
            "title": self.title,
            "author": self.author.name if self.author else "",
            "author_url": self.author.profile_url if self.author else "",
            "thumbnail": self.thumbnail_url,
            "views": self.views,
            "downloads": self.downloads,
            "posted": self.posted,
            "published": self.published,
            "updated": self.updated,
            "category": self.category,
            "licence": self.licence,
            "description": self.description,
            "tags": self.tags,
        }
    
    def format_info(self, censored_thumbnail: bool = False) -> str:
        """格式化模型信息为文本"""
        lines = [
            f"📦 {self.title}",
            f"🔗 {self.full_url}",
        ]
        
        if self.author:
            lines.append(f"👤 作者: {self.author.name}")
        
        if self.category:
            lines.append(f"📁 分类: {self.category}")
        
        if self.views:
            lines.append(f"👀 浏览: {self.views:,}")
        
        if self.downloads:
            lines.append(f"📥 下载: {self.downloads:,}")
        
        if self.posted:
            lines.append(f"📅 发布: {self.posted}")
        
        if self.updated:
            lines.append(f"🔄 更新: {self.updated}")
        
        if self.licence:
            lines.append(f"📜 许可: {self.licence}")
        
        if self.tags:
            lines.append(f"🏷️ 标签: {', '.join(self.tags[:5])}")
        
        return "\n".join(lines) + "\u200E"  # 添加零宽字符防止strip
    
    def __str__(self) -> str:
        return f"Model({self.model_id}: {self.title})"
    
    def __repr__(self) -> str:
        return f"Model(id={self.model_id!r}, title={self.title!r}, url={self.url!r})"


@dataclass
class SearchResult:
    """搜索结果"""
    models: List[Model] = field(default_factory=list)
    total_pages: int = 1
    current_page: int = 1
    query: str = ""
    
    @property
    def total_count(self) -> int:
        """获取结果总数（近似值）"""
        return len(self.models)
    
    @property
    def has_next_page(self) -> bool:
        """是否有下一页"""
        return self.current_page < self.total_pages
    
    @property
    def has_prev_page(self) -> bool:
        """是否有上一页"""
        return self.current_page > 1
    
    def format_list(self, max_items: int = 10) -> str:
        """格式化搜索结果列表"""
        if not self.models:
            return "未找到相关模型\u200E"
        
        lines = [f"🔍 搜索结果 (第 {self.current_page}/{self.total_pages} 页):\n"]
        
        for i, model in enumerate(self.models[:max_items], 1):
            lines.append(f"{i}. {model.title}")
            lines.append(f"   ID: {model.model_id} | 👤 {model.author.name if model.author else '未知'}")
        
        if len(self.models) > max_items:
            lines.append(f"\n... 还有 {len(self.models) - max_items} 个结果")
        
        return "\n".join(lines) + "\u200E"