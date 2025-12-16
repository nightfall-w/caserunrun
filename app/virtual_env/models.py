"""
@FileName：models.py
@Description：虚拟环境模型定义
@Author：baojun.wang
@Time：2025/11/19 21:22
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base
from utils.commonlib import now


class PythonVirtualEnvModel(Base):
    """
    Python虚拟环境模型
    用于存储Python虚拟环境的相关信息
    """
    __tablename__ = "python_envs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 环境名称
    name = Column(String(100), nullable=False)
    # Python版本
    python_version = Column(String(20), nullable=False)
    # 虚拟环境路径
    path = Column(String(500), nullable=False)
    # 解释器路径
    interpreter_path = Column(String(500), nullable=False)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now, comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=now,
        onupdate=now,
        comment="最后一次更新时间"
    )
    # 是否已删除
    is_deleted = Column(Boolean, default=False)


class JavaEnvModel(Base):
    """
    Java环境模型
    用于存储Java环境的相关信息
    """
    __tablename__ = "java_envs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 环境名称
    name = Column(String(100), nullable=False)
    # Java版本
    java_version = Column(String(20), nullable=False)
    # JDK路径
    jdk_path = Column(String(500), nullable=False)
    # Maven路径（如果有）
    maven_setting_path = Column(String(500), nullable=True)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now, comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=now,
        onupdate=now,
        comment="最后一次更新时间"
    )
    # 是否已删除
    is_deleted = Column(Boolean, default=False)
