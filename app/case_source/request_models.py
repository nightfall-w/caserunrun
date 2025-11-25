"""
@FileName：case_source_models.py
@Description：用例源相关请求模型
@Author：baojun.wang
@Time：2025/10/29 16:50
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any


class PaginationRequestModel(BaseModel):
    page_num: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页大小")

    @model_validator(mode="after")
    def check_pagination(self):
        if self.page_num < 1 or self.page_size < 1:
            raise ValueError("分页参数必须大于等于1")
        return self


class CheckTokenRequest(BaseModel):
    gitlab_url: str = Field(..., description="gitlab地址")
    token: str = Field(..., description="token")


class BindCaseSourceRequest(BaseModel):
    workspaceId: int = Field(..., description="用例库ID")
    specificType: int = Field(..., description="测试类型 10-web、11-H5、12-接口")
    caseType: str = Field(..., description="用例类型")
    tokenType: str = Field(..., description="token类型")
    caseSourcePlatform: str = Field(..., description="用例源平台")
    desc: Optional[str] = Field(default="", description="用例源描述")
    caseSourceValue: Dict[Any, Any] = Field(..., description="用例源值")


class UpdateCaseSourceRequest(BaseModel):
    id: int = Field(..., description="用例源关系表id")
    workspaceId: int = Field(..., description="用例库ID")
    specificType: int = Field(..., description="测试类型 10-web、11-H5、12-接口")
    caseType: str = Field(..., description="用例类型")
    tokenType: str = Field(..., description="token类型")
    caseSourcePlatform: str = Field(..., description="用例源平台")
    desc: Optional[str] = Field(default="", description="用例源描述")
    caseSourceValue: Dict[Any, Any] = Field(..., description="用例源值")


class DeleteCaseSourceRequest(BaseModel):
    id: int = Field(..., description="用例源关系表id")
    workspaceId: int = Field(..., description="用例库ID")


class CaseSourceListRequest(PaginationRequestModel):
    workspaceId: int = Field(..., description="用例库ID")
