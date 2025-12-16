"""
@FileName：models.py
@Description：
@Author：baojun.wang
"""
import enum
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import Integer, String, Text, DateTime, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

from utils.commonlib import now


class TokenType(enum.StrEnum):
    """
    token类型枚举
    """
    SYSTEM = "system"
    WORKSPACE = "workspace"


class SourcePlatformType(enum.StrEnum):
    """
    用例源类型枚举
    """
    GITLAB = "GitLab"
    Gitee = "Gitee"


class CaseSourceRelationModel(Base):
    """
    用例库关系模型 标记用例库workspaceId与引擎用例库的关系
    """
    __tablename__ = "case_source_relation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="WorkspaceID")
    desc: Mapped[str] = mapped_column(Text, nullable=False, comment="用例库描述")
    specific_type: Mapped[int] = mapped_column(Integer, nullable=False, comment="测试类型")
    case_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="用例类型")
    case_source_value: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, comment="用例源值")
    case_project_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="用例源项目名称")
    case_source_platform: Mapped[str] = mapped_column(String(20), nullable=False, comment="用例源平台")
    token_type = mapped_column(String(20), nullable=False, comment="token类型")
    venv_id: Mapped[int] = mapped_column(Integer, nullable=True, comment="虚拟环境ID")
    venv_version: Mapped[str] = mapped_column(String(200), nullable=True, comment="虚拟环境版本")
    create_user: Mapped[str] = mapped_column(String, nullable=False, comment="创建人信息")
    update_user: Mapped[str] = mapped_column(String, nullable=False, comment="更新人信息")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=now, comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=now,
        onupdate=now,
        comment="最后一次更新时间"
    )

    # 创建索引
    __table_args__ = (
        Index('idx_workspace_id', 'workspace_id'),
        Index('idx_case_type', 'case_type'),
    )

    def __repr__(self) -> str:
        return (f"<CaseSourceRelationModel(id={self.id}, "
                f"workspace_id={self.workspace_id}, "
                f"case_type='{self.case_type}')>")
