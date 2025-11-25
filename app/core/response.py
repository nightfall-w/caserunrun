"""
@FileName：response.py
@Description：
@Author：baojun.wang
@Time：2025/10/28 14:45
"""
from enum import IntEnum
from typing import Optional, Any

from pydantic import BaseModel, Field


class HttpErrcode(IntEnum):
    """
    接口错误码枚举
    """
    SUCCESS = 0  # 成功
    PERMISSION_DENIED = 40003  # 权限不足
    NOT_FOUND = 40004  # 未找到
    PARAMS_MISSING = 40010  # 缺少必要参数
    PARAMS_ERROR = 40011  # 参数错误
    EXCEPTION = 50000  # 服务器异常


class UnifiedResponse(BaseModel):
    """
    统一返回结果模型
    """
    data: Optional[Any] = None
    code: int = Field(..., description="错误码，0表示成功")
    message: str = Field(..., description="错误信息")


def api_response(data: Any = None, code: int = 0, message: str = "处理成功") -> dict:
    """
    统一返回结果
    :param data: 返回数据
    :param code: 错误码
    :param message: 错误信息
    :return:
    """
    return {
        "data": data,
        "code": code,
        "message": message
    }
