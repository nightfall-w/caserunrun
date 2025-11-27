"""
@FileName：request_models.py
@Description：
@Author：baojun.wang
@Time：2025/11/21 10:55
"""
from typing import Optional

from pydantic import BaseModel, Field


class CreatePythonVirtualEnvModel(BaseModel):
    """
    创建python虚拟环境
    """
    case_source_id: int = Field(..., description="用例源ID")
    workspace_id: int = Field(..., description="工作空间id")
    branch_name: str = Field(..., description="分支名称")
    git_project_id: int = Field(..., description="git项目的id")
    python_version: str = Field(..., description="选择的python版本")
    project_name: str = Field(..., description="项目名称")
    requirements_path: str = Field(..., description="依赖文件路径")


class CreateJavaVirtualEnvModel(BaseModel):
    """
    创建java虚拟环境
    """
    case_source_id: int = Field(..., description="用例源ID")
    workspace_id: int = Field(..., description="工作空间id")
    branch_name: str = Field(..., description="分支名称")
    git_project_id: int = Field(..., description="git项目的id")
    java_version: str = Field(..., description="选择的java版本")
    maven_setting_path: Optional[str] = Field(None, description="maven_setting路径")
    project_name: str = Field(..., description="项目名称")
