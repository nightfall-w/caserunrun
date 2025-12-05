"""
@FileName：controller.py
@Description：测试计划控制器
@Author：baojun.wang
@Time：2025/12/1 17:48
"""
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.user.controller import get_nickname_by_username
from utils.custom_logging import logger
from app.testplan.models import TestPlanModel, test_plan_pytest_case, test_plan_testng_case
from app.case_handler.models import PytestCaseModel, TestNGCaseModel


class TestPlanCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create_test_plan(
            self,
            plan_name: str,
            description: str,
            test_environment: str,
            execution_mode: str,
            creator: str,
            enable_schedule: bool = False,
            schedule_cron_expression: str = None,
            enable_notification: bool = False,
            wecom_webhooks=None,
            lark_webhooks=None,
            dingtalk_webhooks=None,
    ) -> TestPlanModel:
        """创建测试计划"""
        test_plan = TestPlanModel(
            plan_name=plan_name,
            description=description,
            test_environment=test_environment,
            execution_mode=execution_mode,
            create_user=creator,
            update_user=creator,
            enable_schedule=enable_schedule,
            schedule_cron_expression=schedule_cron_expression,
            enable_notification=enable_notification,
            wecom_webhooks=wecom_webhooks,
            lark_webhooks=lark_webhooks,
            dingtalk_webhooks=dingtalk_webhooks
        )
        self.db.add(test_plan)
        self.db.commit()
        self.db.refresh(test_plan)
        return test_plan

    def get_test_plan_by_id(self, test_plan_id: int) -> Optional[TestPlanModel]:
        """根据ID获取测试计划"""
        return self.db.query(TestPlanModel).filter(TestPlanModel.id == test_plan_id).first()

    def update_test_plan(
            self,
            test_plan_id: int,
            plan_name: str = None,
            description: str = None,
            test_environment: str = None,
            execution_mode: str = None,
            updater: str = None,
            enable_schedule: bool = False,
            schedule_cron_expression: str = None,
            enable_notification: bool = False,
            wecom_webhooks=None,
            lark_webhooks=None,
            dingtalk_webhooks=None,
    ) -> bool:
        """更新测试计划"""
        test_plan = self.get_test_plan_by_id(test_plan_id)
        if not test_plan:
            return False

        if plan_name is not None:
            test_plan.plan_name = plan_name
        if description is not None:
            test_plan.description = description
        if test_environment is not None:
            test_plan.test_environment = test_environment
        if execution_mode is not None:
            test_plan.execution_mode = execution_mode
        if updater is not None:
            test_plan.update_user = updater
        if enable_schedule is not None:
            test_plan.enable_schedule = enable_schedule
        if schedule_cron_expression is not None:
            test_plan.schedule_cron_expression = schedule_cron_expression
        if enable_notification is not None:
            test_plan.enable_notification = enable_notification
        if wecom_webhooks is not None:
            test_plan.wecom_webhooks = wecom_webhooks
        if lark_webhooks is not None:
            test_plan.lark_webhooks = lark_webhooks

        self.db.commit()
        return True

    def delete_test_plan(self, test_plan_id: int) -> bool:
        """删除测试计划"""
        test_plan = self.get_test_plan_by_id(test_plan_id)
        if not test_plan:
            return False

        self.db.delete(test_plan)
        self.db.commit()
        return True

    def get_test_cases_by_plan_id(self, test_plan_id: int) -> List[dict]:
        """
        根据测试计划ID获取关联的测试用例列表

        Args:
            test_plan_id: 测试计划ID

        Returns:
            包含Pytest和TestNG用例的列表，每个用例包含基本信息
        """
        # 查询关联的Pytest用例
        pytest_cases = self.db.query(
            PytestCaseModel.case_uuid,
            PytestCaseModel.case_name,
            PytestCaseModel.case_type,
            PytestCaseModel.case_author,
            PytestCaseModel.specific_type
        ).join(
            test_plan_pytest_case,
            PytestCaseModel.case_uuid == test_plan_pytest_case.c.pytest_case_uuid
        ).filter(
            test_plan_pytest_case.c.test_plan_id == test_plan_id
        ).all()

        # 查询关联的TestNG用例
        testng_cases = self.db.query(
            TestNGCaseModel.case_uuid,
            TestNGCaseModel.case_name,
            TestNGCaseModel.case_type,
            TestNGCaseModel.case_author,
            TestNGCaseModel.specific_type
        ).join(
            test_plan_testng_case,
            TestNGCaseModel.case_uuid == test_plan_testng_case.c.testng_case_uuid
        ).filter(
            test_plan_testng_case.c.test_plan_id == test_plan_id
        ).all()

        # 合并两种类型的用例
        associated_cases = []

        # 处理Pytest用例
        for case in pytest_cases:
            associated_cases.append({
                "case_uuid": case.case_uuid,
                "case_name": case.case_name,
                "case_type": case.case_type,  # 应该是 "pytest"
                "specific_type": case.specific_type,
                "case_author": {"username": case.case_author,
                                "nickname": get_nickname_by_username(db=self.db, username=case.case_author)},
            })

        # 处理TestNG用例
        for case in testng_cases:
            associated_cases.append({
                "case_uuid": case.case_uuid,
                "case_name": case.case_name,
                "case_type": case.case_type,  # 应该是 "testng"
                "specific_type": case.specific_type,
                "case_author": {"username": case.case_author,
                                "nickname": get_nickname_by_username(db=self.db, username=case.case_author)},
            })

        return associated_cases

    def get_test_plan_cases_count(self, test_plan_id: int) -> int:
        """获取指定测试计划下的用例数量"""
        # 参数校验
        if not isinstance(test_plan_id, int) or test_plan_id <= 0:
            return 0

        try:
            # 查询指定测试计划下的pytest用例数量
            pytest_count = self.db.query(func.count(
                test_plan_pytest_case.c.pytest_case_uuid
            )).filter(
                test_plan_pytest_case.c.test_plan_id == test_plan_id
            ).scalar() or 0

            # 查询指定测试计划下的testng用例数量
            testng_count = self.db.query(func.count(
                test_plan_testng_case.c.testng_case_uuid
            )).filter(
                test_plan_testng_case.c.test_plan_id == test_plan_id
            ).scalar() or 0

            return pytest_count + testng_count
        except Exception as e:
            # 记录异常日志，避免程序崩溃
            raise Exception(f"查询测试计划用例数量失败: {str(e)}")

    def get_test_plans_with_count(
            self,
            plan_name: str = None,
            creator: str = None,
            limit: int = 10,
            offset: int = 0
    ) -> Tuple[List[TestPlanModel], int]:
        """分页获取测试计划列表"""
        query = self.db.query(TestPlanModel)

        if plan_name:
            query = query.filter(TestPlanModel.plan_name.like(f"%{plan_name}%"))
        if creator:
            query = query.filter(TestPlanModel.create_user == creator)

        total = query.count()
        test_plans = query.order_by(TestPlanModel.create_time.desc()).offset(offset).limit(limit).all()

        return test_plans, total

    def add_pytest_case_to_plan(self, test_plan_id: int, pytest_case_uuid: str) -> bool:
        """添加Pytest用例到测试计划"""
        test_plan = self.get_test_plan_by_id(test_plan_id)
        if not test_plan:
            return False

        pytest_case = self.db.query(PytestCaseModel).filter(
            PytestCaseModel.case_uuid == pytest_case_uuid
        ).first()

        if not pytest_case:
            return False

        # 检查是否已关联
        exists = self.db.query(test_plan_pytest_case).filter(
            test_plan_pytest_case.c.test_plan_id == test_plan_id,
            test_plan_pytest_case.c.pytest_case_uuid == pytest_case_uuid
        ).first()

        if not exists:
            self.db.execute(
                test_plan_pytest_case.insert().values(
                    test_plan_id=test_plan_id,
                    pytest_case_uuid=pytest_case_uuid
                )
            )
            self.db.commit()
        self.update_plan_cases_count(test_plan_id)
        return True

    def remove_pytest_case_from_plan(self, test_plan_id: int, pytest_case_uuid: str) -> bool:
        """从测试计划移除Pytest用例"""
        test_plan = self.get_test_plan_by_id(test_plan_id)
        if not test_plan:
            return False

        self.db.execute(
            test_plan_pytest_case.delete().where(
                test_plan_pytest_case.c.test_plan_id == test_plan_id,
                test_plan_pytest_case.c.pytest_case_uuid == pytest_case_uuid
            )
        )
        self.db.commit()
        self.update_plan_cases_count(test_plan_id)
        return True

    def add_testng_case_to_plan(self, test_plan_id: int, testng_case_uuid: str) -> bool:
        """添加TestNG用例到测试计划"""
        test_plan = self.get_test_plan_by_id(test_plan_id)
        if not test_plan:
            return False

        testng_case = self.db.query(TestNGCaseModel).filter(
            TestNGCaseModel.case_uuid == testng_case_uuid
        ).first()

        if not testng_case:
            return False

        # 检查是否已关联
        exists = self.db.query(test_plan_testng_case).filter(
            test_plan_testng_case.c.test_plan_id == test_plan_id,
            test_plan_testng_case.c.testng_case_uuid == testng_case_uuid
        ).first()

        if not exists:
            self.db.execute(
                test_plan_testng_case.insert().values(
                    test_plan_id=test_plan_id,
                    testng_case_uuid=testng_case_uuid
                )
            )
            self.db.commit()
        self.update_plan_cases_count(test_plan_id)
        return True

    def remove_testng_case_from_plan(self, test_plan_id: int, testng_case_uuid: str) -> bool:
        """从测试计划移除TestNG用例"""
        test_plan = self.get_test_plan_by_id(test_plan_id)
        if not test_plan:
            return False

        self.db.execute(
            test_plan_testng_case.delete().where(
                test_plan_testng_case.c.test_plan_id == test_plan_id,
                test_plan_testng_case.c.testng_case_uuid == testng_case_uuid
            )
        )
        self.db.commit()
        self.update_plan_cases_count(test_plan_id)
        return True

    def clear_cases_from_plan(self, test_plan_id: int) -> bool:
        """清空测试计划中的所有用例"""
        try:
            # 直接操作关联表
            self.db.execute(
                test_plan_pytest_case.delete().where(
                    test_plan_pytest_case.c.test_plan_id == test_plan_id
                )
            )
            self.db.execute(
                test_plan_testng_case.delete().where(
                    test_plan_testng_case.c.test_plan_id == test_plan_id
                )
            )
            self.db.commit()
            self.update_plan_cases_count(test_plan_id)
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"清空测试计划Pytest用例失败: {e}")
            return False

    def update_plan_cases_count(self, test_plan_id: int) -> bool:
        """刷新测试计划中的用例关联"""
        test_plan = self.get_test_plan_by_id(test_plan_id)
        count = self.get_test_plan_cases_count(test_plan_id)
        test_plan.total_case_count = count
        self.db.commit()


def get_test_plan_crud(db: Session) -> TestPlanCRUD:
    """获取测试计划CRUD实例"""
    return TestPlanCRUD(db)
