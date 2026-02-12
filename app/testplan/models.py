"""
@FileName：models.py
@Description：
@Author：baojun.wang
@Time：2025/12/1 17:47
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Table, CheckConstraint, event
from sqlalchemy.orm import relationship

from app.case_handler.models import PytestCaseModel, TestNGCaseModel
from app.core.database import Base
from utils.commonlib import now

from enum import StrEnum


class TestEnvironment(StrEnum):
    QA = "QA"
    PL = "PL"
    OL = "OL"


class ExecutionMode(StrEnum):
    SERIAL = "Serial"
    PARALLEL = "Parallel"


class TaskStatus(StrEnum):
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    CANCELED = "Canceled"
    TIMEOUT = "Timeout"


class JobStatus(StrEnum):
    PENDING = "Pending"
    RUNNING = "Running"
    SUCCESS = "Success"
    FAILED = "Failed"
    EXCEPTION = "Exception"
    CANCELED = "Canceled"
    TIMEOUT = "Timeout"


class CaseType(StrEnum):
    PYTEST = "pytest"
    TESTNG = "testng"


class TestPlanPytestCaseModel(Base):
    """
    测试计划与Pytest用例关联模型
    """
    __tablename__ = "test_plan_pytest_case"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_plan_id = Column(Integer, ForeignKey('test_plan.id'), nullable=False)
    fk_case_uuid = Column(String(400), ForeignKey('pytest_case.case_uuid', ondelete='SET NULL'), nullable=False)
    case_name = Column(String(200), nullable=False, comment="用例名称")
    case_author = Column(String(100), nullable=False, comment="用例作者")
    case_uuid = Column(String(400), nullable=False, comment="用例UUID")
    is_disabled = Column(Boolean, default=False, comment="是否失效")
    workspace_id = Column(Integer, nullable=False, comment="workspace用例库ID")
    create_time = Column(DateTime, default=now, comment="创建时间")
    update_time = Column(DateTime, default=now, onupdate=now, comment="更新时间")

    # 关联测试计划
    test_plan = relationship("TestPlanModel", back_populates="pytest_associations")

    def __repr__(self):
        return f"<TestPlanPytestCaseModel(id={self.id}, test_plan_id={self.test_plan_id}, case_uuid='{self.case_uuid}')>"


class TestPlanTestNGCaseModel(Base):
    """
    测试计划与TestNG用例关联模型
    """
    __tablename__ = "test_plan_testng_case"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_plan_id = Column(Integer, ForeignKey('test_plan.id'), nullable=False)
    fk_case_uuid = Column(String(400), ForeignKey('testng_case.case_uuid', ondelete='SET NULL'), nullable=False)
    case_name = Column(String(200), nullable=False, comment="用例名称")
    case_author = Column(String(100), nullable=False, comment="用例作者")
    case_uuid = Column(String(400), nullable=False, comment="用例UUID")
    is_disabled = Column(Boolean, default=False, comment="是否失效")
    workspace_id = Column(Integer, nullable=False, comment="workspace用例库ID")
    create_time = Column(DateTime, default=now, comment="创建时间")
    update_time = Column(DateTime, default=now, onupdate=now, comment="更新时间")

    # 关联测试计划
    test_plan = relationship("TestPlanModel", back_populates="testng_associations")

    def __repr__(self):
        return f"<TestPlanTestNGCaseModel(id={self.id}, test_plan_id={self.test_plan_id}, case_uuid='{self.case_uuid}')>"


class TestPlanModel(Base):
    """
    测试计划模型
    """
    __tablename__ = "test_plan"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id = Column(Integer, nullable=False, comment="workspace用例库ID")
    plan_name = Column(String(200), nullable=False, comment="测试计划名称")
    description = Column(Text, comment="测试计划描述")
    test_environment = Column(String(100), nullable=False, comment="测试环境")
    execution_mode = Column(String(20), nullable=False, comment="并发方式(串行/并行)")
    enable_schedule = Column(Boolean, default=False, comment="是否开启定时任务")
    schedule_task_id = Column(String(100), comment="定时任务id")
    schedule_cron_expression = Column(String(200), comment="定时规则")
    fail_stop = Column(Boolean, default=False, comment="失败停止,仅串行任务")
    enable_notification = Column(Boolean, default=False, comment="是否发送通知")
    wecom_webhooks = Column(JSON, default=[], comment="企微通知webhook列表")
    lark_webhooks = Column(JSON, default=[], comment="飞书通知webhook列表")
    dingtalk_webhooks = Column(JSON, default=[], comment="钉钉通知webhook列表")
    total_case_count = Column(Integer, default=0, comment="所有用例数量")
    running_task_count = Column(Integer, default=0, comment="运行中的测试任务数")
    pending_task_count = Column(Integer, default=0, comment="等待中的测试任务数")
    create_user = Column(String(100), comment="创建人")
    update_user = Column(String(100), comment="更新人")
    create_time = Column(DateTime, default=now, comment="创建时间")
    update_time = Column(DateTime, default=now, onupdate=now, comment="更新时间")

    # 关联Pytest用例
    pytest_associations = relationship("TestPlanPytestCaseModel", back_populates="test_plan",
                                       cascade="all, delete-orphan")
    # 关联TestNG用例（通过中间模型）
    testng_associations = relationship("TestPlanTestNGCaseModel", back_populates="test_plan",
                                       cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(test_environment.in_([env for env in TestEnvironment]), name='check_test_environment'),
        CheckConstraint(execution_mode.in_([mode for mode in ExecutionMode]), name='check_execution_mode'),
    )

    def __repr__(self):
        return f"<TestPlanModel(id={self.id}, plan_name='{self.plan_name}')>"


class TestTaskModel(Base):
    """
    测试任务模型
    """
    __tablename__ = "test_task"
    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id = Column(Integer, nullable=False, comment="workspace用例库ID")
    test_plan_id = Column(Integer, nullable=False, comment="关联的测试计划id")
    task_name = Column(String(200), nullable=False, comment="测试任务名称")
    test_environment = Column(String(100), nullable=False, comment="执行环境")
    fail_stop = Column(Boolean, default=False, comment="失败停止,仅串行任务")
    task_execution_mode = Column(String(20), nullable=False, comment="并发方式(串行/并行)")
    task_status = Column(String(20), nullable=False, comment="任务状态(运行中/完成)")
    task_result = Column(JSON, default=None, nullable=True, comment="任务结果")
    create_user = Column(String(100), comment="创建人")
    create_time = Column(DateTime, default=now, comment="创建时间")
    update_time = Column(DateTime, default=now, onupdate=now, comment="更新时间")

    __table_args__ = (
        CheckConstraint(task_execution_mode.in_([mode for mode in ExecutionMode]),
                        name='check_task_execution_mode'),
        CheckConstraint(test_environment.in_([env for env in TestEnvironment]), name='check_test_environment'),
        CheckConstraint(task_status.in_([status for status in TaskStatus]), name='check_task_status'),
    )


class TaskJobModel(Base):
    """
    任务作业模型
    """
    __tablename__ = "task_job"
    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id = Column(Integer, nullable=False, comment="workspace用例库ID")
    task_id = Column(Integer, nullable=False, comment="关联的测试任务id")
    case_commit_id = Column(String(100), nullable=False, comment="git提交id")
    test_plan_id = Column(Integer, nullable=False, comment="关联的测试计划id")
    case_name = Column(String(200), nullable=False, comment="case_name")
    case_uuid = Column(String(400), nullable=False, comment="case uuid")
    case_path = Column(String(400), nullable=False, comment="case路径")
    case_package = Column(String(400), nullable=False, comment="case包名")
    case_type = Column(String(20), nullable=False, comment="case类型")
    report_path = Column(String(400), nullable=False, comment="报告路径")
    case_function_list = Column(JSON, default=[], nullable=True, comment="case方法列表")
    job_status = Column(String(20), nullable=False, comment="作业状态")
    job_result = Column(JSON, default=None, nullable=True, comment="作业结果")
    create_time = Column(DateTime, default=now, comment="创建时间")
    update_time = Column(DateTime, default=now, onupdate=now, comment="更新时间")
    time_consuming = Column(Integer, default=0, comment="耗时/s")

    __table_args__ = (
        CheckConstraint(case_type.in_([type for type in CaseType]), name='check_case_type'),
        CheckConstraint(job_status.in_([status for status in JobStatus]), name='check_job_status'),
    )
