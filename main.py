"""
SmutBase AstrBot 插件
用于查询 smutba.se 网站的3D模型资源
"""

import os
from pathlib import Path
from typing import Optional
from io import BytesIO

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp

try:
    from .modules.client import Client
    from .modules.model import Model, SearchResult
    from .modules.consts import Category, ROOT_URL
    from .modules.errors import (
        SmutBaseError, ModelNotFound, NetworkError,
        InvalidModelID
    )
except ImportError:
    from modules.client import Client
    from modules.model import Model, SearchResult
    from modules.consts import Category, ROOT_URL
    from modules.errors import (
        SmutBaseError, ModelNotFound, NetworkError,
        InvalidModelID
    )


@register("smutba", "SmutBase Plugin", "SmutBase 3D模型资源查询插件", "1.0.0")
class SmutBasePlugin(Star):
    """SmutBase 3D模型资源查询插件"""
    
    def __init__(self, context: Context):
        super().__init__(context)
        self.client: Optional[Client] = None
        self.cache_dir: Optional[Path] = None
        self._last_cache_files: list = []
    
    async def initialize(self):
        """插件初始化"""
        # 获取配置
        config = self.context.get_config()
        plugin_config = config.get("smutba", {}) if config else {}
        
        # 初始化客户端
        proxy = plugin_config.get("proxy", "")
        timeout = plugin_config.get("timeout", 30)
        
        self.client = Client(
            proxy=proxy if proxy else None,
            timeout=timeout,
        )
        
        # 初始化缓存目录
        cache_dir_name = plugin_config.get("cache_dir", "cache")
        data_dir = self._get_data_dir()
        self.cache_dir = data_dir / cache_dir_name
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("SmutBase 插件初始化完成")
    
    async def terminate(self):
        """插件销毁"""
        if self.client:
            await self.client.close()
        
        # 清理缓存目录
        self._cleanup_cache()
        logger.info("SmutBase 插件已销毁")
    
    def _get_data_dir(self) -> Path:
        """获取插件数据目录"""
        # 使用插件目录下的 data 文件夹
        plugin_dir = Path(__file__).parent
        data_dir = plugin_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    
    def _get_config(self) -> dict:
        """获取插件配置"""
        config = self.context.get_config()
        return config.get("smutba", {}) if config else {}
    
    def _cleanup_cache(self):
        """清理缓存文件"""
        for file_path in self._last_cache_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"已清理缓存文件: {file_path}")
            except Exception as e:
                logger.warning(f"清理缓存文件失败: {file_path}, 错误: {e}")
        self._last_cache_files.clear()
    
    def _should_cleanup(self) -> bool:
        """检查是否需要自动清理"""
        config = self._get_config()
        return config.get("auto_cleanup", True)
    
    async def _download_and_blur_image(self, url: str, blur_level: int = 0) -> Optional[str]:
        """
        下载图片并可选地进行模糊处理
        
        Args:
            url: 图片URL
            blur_level: 模糊程度 (0-100)
            
        Returns:
            本地图片路径或None
        """
        if not url:
            return None
        
        try:
            import aiohttp
            from PIL import Image, ImageFilter
            
            # 下载图片
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        return None
                    image_data = await response.read()
            
            # 加载图片
            img = Image.open(BytesIO(image_data))
            
            # 如果需要模糊处理
            if blur_level > 0:
                # 将模糊程度映射到高斯模糊半径 (0-100 -> 0-50)
                radius = blur_level * 0.5
                img = img.filter(ImageFilter.GaussianBlur(radius=radius))
            
            # 保存到缓存目录
            import hashlib
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            cache_path = self.cache_dir / f"thumb_{url_hash}.jpg"
            
            # 转换为RGB（如果是RGBA）
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            img.save(str(cache_path), 'JPEG', quality=85)
            
            # 记录缓存文件
            self._last_cache_files.append(str(cache_path))
            
            return str(cache_path)
            
        except Exception as e:
            logger.warning(f"处理图片失败: {url}, 错误: {e}")
            return None
    
    async def _send_model_info(
        self,
        event: AstrMessageEvent,
        model: Model,
        show_thumbnail: bool = True
    ):
        """
        发送模型信息
        
        Args:
            event: 消息事件
            model: 模型对象
            show_thumbnail: 是否显示缩略图
        """
        # 自动清理上次的缓存
        if self._should_cleanup():
            self._cleanup_cache()
        
        config = self._get_config()
        blur_level = config.get("blur_level", 0)
        
        # 构建消息链
        chain = []
        
        # 如果需要显示缩略图
        if show_thumbnail and config.get("show_thumbnail", True) and model.thumbnail_url:
            image_path = await self._download_and_blur_image(
                model.thumbnail_url,
                blur_level
            )
            if image_path:
                chain.append(Comp.Image.fromFileSystem(image_path))
        
        # 添加文本信息
        chain.append(Comp.Plain(model.format_info()))
        
        yield event.chain_result(chain)
    
    async def _send_search_results(
        self,
        event: AstrMessageEvent,
        result: SearchResult
    ):
        """
        发送搜索结果
        
        Args:
            event: 消息事件
            result: 搜索结果对象
        """
        # 自动清理上次的缓存
        if self._should_cleanup():
            self._cleanup_cache()
        
        config = self._get_config()
        max_results = config.get("max_results", 10)
        
        yield event.plain_result(result.format_list(max_results))
    
    @filter.command("smutbase")
    async def cmd_model(self, event: AstrMessageEvent):
        """
        获取模型详情
        用法: /smutbase <模型ID>
        """
        message = event.message_str.strip()
        parts = message.split(maxsplit=1)
        
        if len(parts) < 2:
            yield event.plain_result("❌ 请提供模型ID\n用法: /smutbase <模型ID>\u200E")
            return
        
        model_id = parts[1].strip()
        
        try:
            model = await self.client.get_model(model_id)
            async for result in self._send_model_info(event, model):
                yield result
                
        except ModelNotFound:
            yield event.plain_result(f"❌ 模型不存在: {model_id}\u200E")
        except InvalidModelID:
            yield event.plain_result(f"❌ 无效的模型ID: {model_id}\u200E")
        except NetworkError as e:
            yield event.plain_result(f"❌ 网络错误: {e}\u200E")
        except SmutBaseError as e:
            yield event.plain_result(f"❌ 查询失败: {e}\u200E")
        except Exception as e:
            logger.error(f"获取模型失败: {e}")
            yield event.plain_result(f"❌ 发生错误: {e}\u200E")
    
    @filter.command("smutbase_search")
    async def cmd_search(self, event: AstrMessageEvent):
        """
        搜索模型
        用法: /smutbase_search <关键词>
        """
        message = event.message_str.strip()
        parts = message.split(maxsplit=1)
        
        query = parts[1].strip() if len(parts) > 1 else ""
        
        try:
            result = await self.client.search(query=query)
            async for r in self._send_search_results(event, result):
                yield r
                
        except NetworkError as e:
            yield event.plain_result(f"❌ 网络错误: {e}\u200E")
        except SmutBaseError as e:
            yield event.plain_result(f"❌ 搜索失败: {e}\u200E")
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            yield event.plain_result(f"❌ 发生错误: {e}\u200E")
    
    @filter.command("smutbase_page")
    async def cmd_search_page(self, event: AstrMessageEvent):
        """
        搜索模型（指定页码）
        用法: /smutbase_page <页码> [关键词]
        """
        message = event.message_str.strip()
        parts = message.split(maxsplit=2)
        
        if len(parts) < 2:
            yield event.plain_result("❌ 请提供页码\n用法: /smutbase_page <页码> [关键词]\u200E")
            return
        
        try:
            page = int(parts[1])
            if page < 1:
                page = 1
        except ValueError:
            yield event.plain_result("❌ 页码必须是数字\u200E")
            return
        
        query = parts[2].strip() if len(parts) > 2 else ""
        
        try:
            result = await self.client.search(query=query, page=page)
            async for r in self._send_search_results(event, result):
                yield r
                
        except NetworkError as e:
            yield event.plain_result(f"❌ 网络错误: {e}\u200E")
        except SmutBaseError as e:
            yield event.plain_result(f"❌ 搜索失败: {e}\u200E")
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            yield event.plain_result(f"❌ 发生错误: {e}\u200E")
    
    @filter.command("smutbase_latest")
    async def cmd_latest(self, event: AstrMessageEvent):
        """
        获取最新模型
        用法: /smutbase_latest [页码]
        """
        message = event.message_str.strip()
        parts = message.split(maxsplit=1)
        
        page = 1
        if len(parts) > 1:
            try:
                page = int(parts[1])
                if page < 1:
                    page = 1
            except ValueError:
                pass
        
        try:
            result = await self.client.get_latest(page=page)
            async for r in self._send_search_results(event, result):
                yield r
                
        except NetworkError as e:
            yield event.plain_result(f"❌ 网络错误: {e}\u200E")
        except SmutBaseError as e:
            yield event.plain_result(f"❌ 获取失败: {e}\u200E")
        except Exception as e:
            logger.error(f"获取最新模型失败: {e}")
            yield event.plain_result(f"❌ 发生错误: {e}\u200E")
    
    @filter.command("smutbase_popular")
    async def cmd_popular(self, event: AstrMessageEvent):
        """
        获取热门模型
        用法: /smutbase_popular [页码]
        """
        message = event.message_str.strip()
        parts = message.split(maxsplit=1)
        
        page = 1
        if len(parts) > 1:
            try:
                page = int(parts[1])
                if page < 1:
                    page = 1
            except ValueError:
                pass
        
        try:
            result = await self.client.get_popular(page=page)
            async for r in self._send_search_results(event, result):
                yield r
                
        except NetworkError as e:
            yield event.plain_result(f"❌ 网络错误: {e}\u200E")
        except SmutBaseError as e:
            yield event.plain_result(f"❌ 获取失败: {e}\u200E")
        except Exception as e:
            logger.error(f"获取热门模型失败: {e}")
            yield event.plain_result(f"❌ 发生错误: {e}\u200E")
    
    @filter.command("smutbase_random")
    async def cmd_random(self, event: AstrMessageEvent):
        """
        获取随机模型
        用法: /smutbase_random
        """
        try:
            model = await self.client.get_random()
            if model:
                async for result in self._send_model_info(event, model):
                    yield result
            else:
                yield event.plain_result("❌ 未能获取随机模型\u200E")
                
        except NetworkError as e:
            yield event.plain_result(f"❌ 网络错误: {e}\u200E")
        except SmutBaseError as e:
            yield event.plain_result(f"❌ 获取失败: {e}\u200E")
        except Exception as e:
            logger.error(f"获取随机模型失败: {e}")
            yield event.plain_result(f"❌ 发生错误: {e}\u200E")
    
    @filter.command("smutbase_category")
    async def cmd_category(self, event: AstrMessageEvent):
        """
        按分类搜索
        用法: /smutbase_category <分类> [页码]
        分类: models, textures, sceneries, hdris, other
        """
        message = event.message_str.strip()
        parts = message.split()
        
        if len(parts) < 2:
            categories = ", ".join(Category.all().keys())
            yield event.plain_result(f"❌ 请提供分类\n可用分类: {categories}\n用法: /smutbase_category <分类> [页码]\u200E")
            return
        
        category_name = parts[1].lower()
        page = 1
        
        if len(parts) > 2:
            try:
                page = int(parts[2])
                if page < 1:
                    page = 1
            except ValueError:
                pass
        
        # 查找分类
        categories = Category.all()
        if category_name not in categories:
            yield event.plain_result(f"❌ 未知分类: {category_name}\n可用分类: {', '.join(categories.keys())}\u200E")
            return
        
        category = categories[category_name]
        
        try:
            result = await self.client.search(category=category, page=page)
            async for r in self._send_search_results(event, result):
                yield r
                
        except NetworkError as e:
            yield event.plain_result(f"❌ 网络错误: {e}\u200E")
        except SmutBaseError as e:
            yield event.plain_result(f"❌ 搜索失败: {e}\u200E")
        except Exception as e:
            logger.error(f"分类搜索失败: {e}")
            yield event.plain_result(f"❌ 发生错误: {e}\u200E")
    
    @filter.command("smutbase_url")
    async def cmd_url(self, event: AstrMessageEvent):
        """
        获取模型页面链接
        用法: /smutbase_url <模型ID>
        """
        message = event.message_str.strip()
        parts = message.split(maxsplit=1)
        
        if len(parts) < 2:
            yield event.plain_result("❌ 请提供模型ID\n用法: /smutbase_url <模型ID>\u200E")
            return
        
        model_id = parts[1].strip()
        
        # UUID 格式验证
        import re
        uuid_pattern = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', re.I)
        
        if not uuid_pattern.match(model_id):
            yield event.plain_result(f"❌ 无效的模型ID格式，应为UUID格式: {model_id}\u200E")
            return
        
        url = f"{ROOT_URL}/project/{model_id}/"
        yield event.plain_result(f"🔗 模型链接:\n{url}\u200E")
    
    @filter.command("smutbase_clean")
    async def cmd_clean(self, event: AstrMessageEvent):
        """
        清理缓存
        用法: /smutbase_clean
        """
        try:
            # 清理缓存文件
            self._cleanup_cache()
            
            # 清理整个缓存目录
            if self.cache_dir and self.cache_dir.exists():
                for file in self.cache_dir.iterdir():
                    if file.is_file():
                        file.unlink()
                
            yield event.plain_result("✅ 缓存已清理\u200E")
            
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
            yield event.plain_result(f"❌ 清理失败: {e}\u200E")
