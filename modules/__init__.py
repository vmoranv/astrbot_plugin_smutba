"""
SmutBase API 模块
用于解析 smutba.se 网站内容
"""

from .client import Client as Client
from .model import Model as Model, Author as Author, SearchResult as SearchResult
from .errors import (
    SmutBaseError as SmutBaseError,
    InvalidURL as InvalidURL,
    InvalidModelID as InvalidModelID,
    ModelNotFound as ModelNotFound,
    NetworkError as NetworkError,
    ParseError as ParseError,
)
from .consts import (
    ROOT_URL as ROOT_URL,
    Category as Category,
    SortBy as SortBy,
    REGEX_MODEL_ID as REGEX_MODEL_ID,
)

__all__ = [
    "Client",
    "Model",
    "Author",
    "SearchResult",
    "SmutBaseError",
    "InvalidURL",
    "InvalidModelID",
    "ModelNotFound",
    "NetworkError",
    "ParseError",
    "ROOT_URL",
    "Category",
    "SortBy",
    "REGEX_MODEL_ID",
]