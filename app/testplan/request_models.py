from pydantic import BaseModel
from typing import Optional, List

from app.case_source.request_models import PaginationRequestModel


class CreateTestPlanRequest(BaseModel):
    """创建测试计划请求"""
    workspace_id: int
    plan_name: str
    description: Optional[str] = ""
    test_environment: str  # QA/PL/OL
    execution_mode: str  # Serial/Parallel
    # 新增字段
    enable_schedule: Optional[bool] = False
    schedule_cron_expression: Optional[str] = ""
    enable_notification: Optional[bool] = False
    wecom_webhooks: Optional[List[str]] = []
    lark_webhooks: Optional[List[str]] = []
    dingtalk_webhooks: Optional[List[str]] = []


class UpdateTestPlanRequest(BaseModel):
    """更新测试计划请求"""
    test_plan_id: int
    plan_name: Optional[str] = None
    description: Optional[str] = None
    test_environment: Optional[str] = None  # QA/PL/OL
    execution_mode: Optional[str] = None  # Serial/Parallel
    # 新增字段
    enable_schedule: Optional[bool] = None
    schedule_cron_expression: Optional[str] = None
    enable_notification: Optional[bool] = None
    wecom_webhooks: Optional[List[str]] = None
    lark_webhooks: Optional[List[str]] = None
    dingtalk_webhooks: Optional[List[str]] = None


class TestPlanListRequest(PaginationRequestModel):
    """测试计划列表请求"""
    workspace_id: int
    plan_name: Optional[str] = None
    creator: Optional[str] = None


class AddTestCaseRequest(BaseModel):
    """添加测试用例请求"""
    test_plan_id: int
    case_type: str  # pytest/testng
    case_uuid: str


class RemoveTestCaseRequest(BaseModel):
    """移除测试用例请求"""
    test_plan_id: int
    case_type: str  # pytest/testng
    case_uuid: str


class TestCaseInfo(BaseModel):
    """测试用例信息"""
    case_uuid: str
    case_type: str


class BatchAddTestCaseRequest(BaseModel):
    """批量添加测试用例请求"""
    test_plan_id: int
    cases: List[TestCaseInfo]


class TriggerTestPlanRequest(BaseModel):
    """触发测试计划请求"""
    test_plan_id: int


class TestTasksListRequest(PaginationRequestModel):
    """测试任务列表请求"""
    workspace_id: int
    test_plan_id: Optional[int] = None


class TestTaskDetailRequest(BaseModel):
    """测试任务详情请求"""
    task_id: int
