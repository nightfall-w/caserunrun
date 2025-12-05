"""
@FileName：models.py
@Description：
@Author：baojun.wang
@Time：2025/12/1 17:47
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Table, CheckConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from utils.commonlib import now

from enum import Enum


class TestEnvironment(Enum):
    QA = "QA"
    PL = "PL"
    OL = "OL"


class ExecutionMode(Enum):
    SERIAL = "Serial"
    PARALLEL = "Parallel"


# 测试计划与Pytest用例关联表
test_plan_pytest_case = Table('test_plan_pytest_case', Base.metadata,
                              Column('test_plan_id', Integer, ForeignKey('test_plan.id'), primary_key=True),
                              Column('pytest_case_uuid', String(400), ForeignKey('pytest_case.case_uuid'),
                                     primary_key=True)
                              )

# 测试计划与TestNG用例关联表
test_plan_testng_case = Table('test_plan_testng_case', Base.metadata,
                              Column('test_plan_id', Integer, ForeignKey('test_plan.id'), primary_key=True),
                              Column('testng_case_uuid', String(400), ForeignKey('testng_case.case_uuid'),
                                     primary_key=True)
                              )


class TestPlanModel(Base):
    """
    测试计划模型
    """
    __tablename__ = "test_plan"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_name = Column(String(200), nullable=False, comment="测试计划名称")
    description = Column(Text, comment="测试计划描述")
    test_environment = Column(String(100), nullable=False, comment="测试环境")
    execution_mode = Column(String(20), nullable=False, comment="并发方式(串行/并行)")
    enable_schedule = Column(Boolean, default=False, comment="是否开启定时任务")
    schedule_task_id = Column(String(100), comment="定时任务id")
    schedule_cron_expression = Column(String(200), comment="定时规则")
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
    pytest_cases = relationship("PytestCaseModel", secondary=test_plan_pytest_case, backref="test_plans")

    # 关联TestNG用例
    testng_cases = relationship("TestNGCaseModel", secondary=test_plan_testng_case, backref="test_plans")

    __table_args__ = (
        CheckConstraint(test_environment.in_(['QA', 'PL', 'OL']), name='check_test_environment'),
        CheckConstraint(execution_mode.in_(['Serial', 'Parallel']), name='check_execution_mode'),
    )

    def __repr__(self):
        return f"<TestPlanModel(id={self.id}, plan_name='{self.plan_name}')>"
