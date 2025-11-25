"""
@FileName：request_models.py
@Description：配置项相关请求模型
@Author：baojun.wang
@Time：2025/11/7 21:22
"""
from typing import Optional
from pydantic import BaseModel, Field

from app.case_source.request_models import PaginationRequestModel


class CreateSystemConfigRequest(BaseModel):
    """创建系统配置请求"""
    key: str = Field(..., description="配置项键名")
    value: str = Field(..., description="配置项值")
    desc: str = Field(..., description="配置项描述")
    type: str = Field(..., description="配置项类型")
    allowed_to_delete: bool = Field(default=True, description="是否允许删除")
    required: bool = Field(default=False, description="是否必填")


class UpdateSystemConfigRequest(BaseModel):
    """更新系统配置请求"""
    config_id: int = Field(..., description="配置项ID")
    key: Optional[str] = Field(None, description="配置项键名")
    value: Optional[str] = Field(None, description="配置项值")
    desc: Optional[str] = Field(None, description="配置项描述")
    type: Optional[str] = Field(None, description="配置项类型")
    verified: Optional[bool] = Field(None, description="是否通过验证")
    allowed_to_delete: Optional[bool] = Field(None, description="是否允许删除")
    required: Optional[bool] = Field(None, description="是否必填")


class DeleteSystemConfigRequest(BaseModel):
    """删除系统配置请求"""
    config_id: int = Field(..., description="配置项ID")


class GetSystemConfigRequest(BaseModel):
    """获取系统配置请求"""
    config_id: int = Field(..., description="配置项ID")


class ListSystemConfigRequest(PaginationRequestModel):
    """系统配置列表请求"""
    key: Optional[str] = Field(None, description="配置项键名")


class CreateWorkspaceConfigRequest(BaseModel):
    """创建工作空间配置请求"""
    workspace_id: int = Field(..., description="工作空间ID")
    key: str = Field(..., description="配置项键名")
    value: str = Field(..., description="配置项值")
    desc: str = Field(..., description="配置项描述")
    type: str = Field(..., description="配置项类型")
    allowed_to_delete: bool = Field(default=True, description="是否允许删除")
    required: bool = Field(default=False, description="是否必填")


class UpdateWorkspaceConfigRequest(BaseModel):
    """更新工作空间配置请求"""
    config_id: int = Field(..., description="配置项ID")
    workspace_id: Optional[int] = Field(None, description="工作空间ID")
    key: Optional[str] = Field(None, description="配置项键名")
    value: Optional[str] = Field(None, description="配置项值")
    desc: Optional[str] = Field(None, description="配置项描述")
    type: Optional[str] = Field(None, description="配置项类型")
    verified: Optional[bool] = Field(None, description="是否通过验证")
    allowed_to_delete: Optional[bool] = Field(None, description="是否允许删除")
    required: Optional[bool] = Field(None, description="是否必填")


class DeleteWorkspaceConfigRequest(BaseModel):
    """删除工作空间配置请求"""
    config_id: int = Field(..., description="配置项ID")


class GetWorkspaceConfigRequest(BaseModel):
    """获取工作空间配置请求"""
    config_id: int = Field(..., description="配置项ID")


class ListWorkspaceConfigRequest(PaginationRequestModel):
    """工作空间配置列表请求"""
    workspace_id: int = Field(..., description="工作空间ID")
    key: Optional[str] = Field(None, description="配置项键名")
