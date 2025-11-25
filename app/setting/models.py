"""
@FileName：models.py
@Description：
@Author：baojun.wang
@Time：2025/11/6 10:06
"""
from datetime import datetime

from sqlalchemy import Integer, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from utils.commonlib import now


class SystemConfigModel(Base):
    """
    系统配置表
    """
    __tablename__ = "system_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    value: Mapped[str] = mapped_column(String, nullable=False, comment="系统配置值")
    key: Mapped[str] = mapped_column(String, nullable=False, comment="系统配置key")
    desc: Mapped[str] = mapped_column(Text, nullable=False, comment="系统配置描述")
    type: Mapped[str] = mapped_column(String, nullable=False, comment="系统配置类型")
    allowed_to_delete: Mapped[bool] = mapped_column(
        Integer,
        default=False,
        comment="是否允许删除"
    )
    required: Mapped[bool] = mapped_column(
        Integer,
        default=True,
        comment="是否必填"
    )
    verified = mapped_column(
        Integer,
        default=False,
        comment="是否有效"
    )
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now, comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=now,
        onupdate=now,
        comment="更新时间"
    )
    STRING_TYPE = "STRING"
    NUMBER_TYPE = "NUMBER"
    BOOLEAN_TYPE = "BOOLEAN"
    DICT_TYPE = "DICT"
    LIST_TYPE = "LIST"

    def __repr__(self) -> str:
        return f"<SystemConfigModel(id={self.id}, value={self.value}, key={self.key})>"


class WorkspaceConfigModel(Base):
    """
    工作空间配置
    """
    __tablename__ = "workspace_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    workspace_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="工作空间ID")
    value: Mapped[str] = mapped_column(String, nullable=False, comment="工作空间配置值")
    key: Mapped[str] = mapped_column(String, nullable=False, comment="工作空间配置key")
    desc: Mapped[str] = mapped_column(Text, nullable=False, comment="工作空间配置描述")
    type: Mapped[str] = mapped_column(String, nullable=False, comment="工作空间配置类型")
    allowed_to_delete: Mapped[bool] = mapped_column(
        Integer,
        default=False,
        comment="是否允许删除"
    )
    required: Mapped[bool] = mapped_column(
        Integer,
        default=True,
        comment="是否必填"
    )
    verified = mapped_column(
        Integer,
        default=False,
        comment="是否有效"
    )
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now, comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=now,
        onupdate=now,
        comment="更新时间"
    )
    STRING_TYPE = "STRING"
    NUMBER_TYPE = "NUMBER"
    BOOLEAN_TYPE = "BOOLEAN"
    DICT_TYPE = "DICT"
    LIST_TYPE = "LIST"

    def __repr__(self) -> str:
        return f"<WorkspaceConfigModel(id={self.id}, value={self.value}, key={self.key})>"
