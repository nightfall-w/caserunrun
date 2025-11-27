from sqlalchemy import Column, Integer, String, Text, DateTime, JSON

from app.core.database import Base
from utils.commonlib import now


class PytestCaseModel(Base):
    """
    pytest用例模型
    """
    __tablename__ = "pytest_case"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id = Column(Integer, nullable=False, comment="workspace用例库ID")
    specific_type = Column(Integer, nullable=False, comment="workspace定义的测试类型")
    case_type = Column(String(10), nullable=False, comment="用例类型")
    case_source_value = Column(JSON, nullable=False, comment="用例源值")
    git_project_id = Column(Integer, nullable=False, comment="gitlab项目ID")
    git_project_name = Column(String(200), nullable=False, comment="gitlab项目名称")
    branch_name = Column(String(200), nullable=False, comment="项目分支名称")
    git_project_commit_id = Column(String(50), nullable=False, comment="项目当前最新的提交ID")
    case_commit_id = Column(String(50), nullable=False, comment="case提交ID")
    case_uuid = Column(String(400), nullable=False, comment="用例uuid")
    case_name = Column(Text, nullable=False, comment="用例名称")
    case_function_list = Column(JSON, default=[], comment="测试方法case列表")
    case_path = Column(Text, nullable=False, comment="用例地址")
    case_package = Column(Text, nullable=False, comment="用例包名")
    case_author = Column(String(50), nullable=False, comment="用例作者")
    case_level = Column(Integer, nullable=False, comment="用例等级")
    create_time = Column(DateTime, default=now, comment="创建时间")
    update_time = Column(DateTime, default=now, comment="更新时间")

    def __repr__(self):
        return f"<PytestCaseModel(id={self.id}, case_name='{self.case_name}')>"


class TestNGCaseModel(Base):
    """
    TestNg用例模型
    """
    __tablename__ = "testng_case"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id = Column(Integer, nullable=False, comment="workspace用例库ID")
    specific_type = Column(Integer, nullable=False, comment="workspace定义的测试类型")
    case_type = Column(String(10), nullable=False, comment="用例类型")
    case_source_value = Column(JSON, nullable=False, comment="用例源值")
    git_project_id = Column(Integer, nullable=False, comment="gitlab项目ID")
    git_project_name = Column(String(200), nullable=False, comment="gitlab项目名称")
    branch_name = Column(String(200), nullable=False, comment="项目分支名称")
    git_project_commit_id = Column(String(50), nullable=False, comment="项目当前最新的提交ID")
    case_commit_id = Column(String(50), nullable=False, comment="case提交ID")
    case_uuid = Column(String(400), nullable=False, comment="用例uuid")
    case_name = Column(Text, nullable=False, comment="用例名称")
    case_function_list = Column(JSON, default=[], comment="测试方法case列表")
    case_path = Column(Text, nullable=False, comment="用例地址")
    case_package = Column(Text, nullable=False, comment="用例包名")
    case_author = Column(String(50), nullable=False, comment="用例作者")
    case_level = Column(Integer, nullable=False, comment="用例等级")
    create_time = Column(DateTime, default=now, comment="创建时间")
    update_time = Column(DateTime, default=now, comment="更新时间")

    def __repr__(self):
        return f"<TestNGCaseModel(id={self.id}, case_name='{self.case_name}')>"
