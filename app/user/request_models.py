"""
@FileName：request_models.py
@Description：
@Author：baojun.wang
@Time：2025/10/31 14:04
"""
from typing import Optional

from pydantic import BaseModel

from app.case_source.request_models import PaginationRequestModel


class UserCreate(BaseModel):
    username: str
    email: str
    nickname: str  # 中文名
    password: str  # 注册时需要密码


class UserDetail(BaseModel):
    id: int


class UserLogin(BaseModel):
    username: str
    password: str


class User(BaseModel):
    id: int
    is_deleted: bool

    class Config:
        from_attributes = True


class UserList(PaginationRequestModel):
    search: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class CurrentUser:
    def __init__(self, _id: int = None, username: str = None, email: str = None, nickname: str = None,
                 is_deleted: bool = False, new_token=None):
        self.id = _id
        self.username = username
        self.email = email
        self.nickname = nickname
        self.is_deleted = is_deleted
        self.new_token = new_token
