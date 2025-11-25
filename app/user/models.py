"""
@FileName：models.py
@Description：
@Author：baojun.wang
@Time：2025/10/31 13:52
"""

from sqlalchemy import Column, Integer, String, Boolean

from app.core.database import Base


# 用户模型
class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    nickname = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_deleted = Column(Boolean, default=False)


# 超级管理员模型
class SuperAdminModel(Base):
    __tablename__ = "super_admins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False, comment="用户ID")
    created_at = Column(String, nullable=False, comment="创建时间")
