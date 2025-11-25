"""
@FileName：requests_models.py
@Description：
@Author：baojun.wang
@Time：2025/11/9 23:14
"""
from typing import Optional

from pydantic import BaseModel

from app.case_source.request_models import PaginationRequestModel


class TestCaseListRequest(PaginationRequestModel):
    workspace_id: int
    git_project_id: Optional[int] = None
    case_type: Optional[str] = None
    specific_type: Optional[int] = None
    case_name: Optional[str] = None
    case_author: Optional[str] = None
    case_level: Optional[int] = None
    case_path: Optional[str] = None


class GetTestCaseContent(BaseModel):
    case_id: int
    case_uuid: str
    workspace_id: int
    git_project_id: int
