"""
SmutBase API 异常类定义
"""


class SmutBaseError(Exception):
    """SmutBase API 基础异常类"""
    pass


class InvalidURL(SmutBaseError):
    """无效的URL异常"""
    pass


class InvalidModelID(SmutBaseError):
    """无效的模型ID异常"""
    pass


class ModelNotFound(SmutBaseError):
    """模型未找到异常"""
    pass


class NetworkError(SmutBaseError):
    """网络请求异常"""
    pass


class ParseError(SmutBaseError):
    """解析异常"""
    pass


class RateLimitError(SmutBaseError):
    """请求频率限制异常"""
    pass


class AuthorNotFound(SmutBaseError):
    """作者未找到异常"""
    pass


class SearchError(SmutBaseError):
    """搜索异常"""
    pass