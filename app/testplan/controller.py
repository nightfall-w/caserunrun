"""
@FileName：controller.py
@Description：测试计划控制器
@Author：baojun.wang
@Time：2025/12/1 17:48
"""
from typing import List, Tuple, Optional, Any, cast, Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.case_handler.case_parser import GitCaseParser
from app.case_handler.models import PytestCaseModel, TestNGCaseModel
from app.runner.tasks import case_task_executor, pytest_case_job_executor, testng_case_job_executor
from app.testplan.models import TestPlanModel, TestPlanPytestCaseModel, TestPlanTestNGCaseModel, CaseType, \
    TestTaskModel, TaskJobModel, TaskStatus, JobStatus, ExecutionMode
from app.user.controller import get_nickname_by_username
from utils.commonlib import now
from utils.custom_logging import logger


class TestPlanCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create_test_plan(
            self,
            workspace_id: int,
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
            workspace_id=workspace_id,
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

    def get_test_cases_by_plan_id(self, test_plan_id: int) -> Tuple[List[dict], List[dict]]:
        """
        根据测试计划ID获取关联的测试用例列表

        Args:
            test_plan_id: 测试计划ID

        Returns:
            包含Pytest和TestNG用例的列表，每个用例包含基本信息
        """

        # 查询关联的有效Pytest用例
        pytest_cases = self.db.query(
            PytestCaseModel.case_uuid,
            PytestCaseModel.case_name,
            PytestCaseModel.case_type,
            PytestCaseModel.case_author,
            PytestCaseModel.specific_type
        ).join(
            TestPlanPytestCaseModel,
            PytestCaseModel.case_uuid == TestPlanPytestCaseModel.fk_case_uuid
        ).filter(
            TestPlanPytestCaseModel.test_plan_id == test_plan_id,
        ).all()

        # 查询关联的有效TestNG用例
        testng_cases = self.db.query(
            TestNGCaseModel.case_uuid,
            TestNGCaseModel.case_name,
            TestNGCaseModel.case_type,
            TestNGCaseModel.case_author,
            TestNGCaseModel.specific_type
        ).join(
            TestPlanTestNGCaseModel,
            TestNGCaseModel.case_uuid == TestPlanTestNGCaseModel.fk_case_uuid
        ).filter(
            TestPlanTestNGCaseModel.test_plan_id == test_plan_id
        ).all()

        # 查询关联的失效Pytest用例
        invalid_pytest_cases = self.db.query(
            TestPlanPytestCaseModel.case_uuid,
            TestPlanPytestCaseModel.case_name,
            TestPlanPytestCaseModel.case_author
        ).filter(
            TestPlanPytestCaseModel.fk_case_uuid == None
        ).all()

        # 查询关联的有效TestNG用例
        invalid_testng_cases = self.db.query(
            TestPlanTestNGCaseModel.case_uuid,
            TestPlanTestNGCaseModel.case_name,
            TestPlanTestNGCaseModel.case_author
        ).filter(
            TestPlanTestNGCaseModel.fk_case_uuid == None
        ).all()

        # 合并两种类型的用例
        associated_cases = []
        # 失效的用例
        invalid_cases = []

        nickname_cache = {}

        # 处理Pytest和TestNG用例
        for case in pytest_cases + testng_cases:
            username = case.case_author
            if username not in nickname_cache:
                nickname_cache[username] = get_nickname_by_username(db=self.db, username=username)
            nickname = nickname_cache[username]
            associated_cases.append({
                "case_uuid": case.case_uuid,
                "case_name": case.case_name,
                "case_type": case.case_type,
                "specific_type": case.specific_type,
                "case_author": {
                    "username": username,
                    "nickname": nickname
                }
            })

        # 处理失效的pytest用例
        for case in invalid_pytest_cases + invalid_testng_cases:
            invalid_case_info = GitCaseParser.parse_case_uuid(case.case_uuid)
            case_type = invalid_case_info.get("case_type")
            specific_type = invalid_case_info.get("specific_type")

            username = case.case_author
            if username not in nickname_cache:
                nickname_cache[username] = get_nickname_by_username(db=self.db, username=username)
            nickname = nickname_cache[username]

            invalid_cases.append({
                "case_uuid": case.case_uuid,
                "case_name": case.case_name,
                "case_type": case_type,
                "specific_type": specific_type,
                "case_author": {
                    "username": username,
                    "nickname": nickname
                }
            })

        return associated_cases, invalid_cases

    def get_test_plan_cases_count(self, test_plan_id: int) -> int:
        """获取指定测试计划下的用例数量"""
        # 参数校验
        if not isinstance(test_plan_id, int) or test_plan_id <= 0:
            return 0

        try:
            # 查询指定测试计划下的pytest用例数量
            pytest_count = self.db.query(func.count(
                TestPlanPytestCaseModel.case_uuid
            )).filter(
                TestPlanPytestCaseModel.test_plan_id == test_plan_id,
                TestPlanPytestCaseModel.fk_case_uuid != None
            ).scalar() or 0

            # 查询指定测试计划下的testng用例数量
            testng_count = self.db.query(func.count(
                TestPlanTestNGCaseModel.case_uuid
            )).filter(
                TestPlanTestNGCaseModel.test_plan_id == test_plan_id,
                TestPlanTestNGCaseModel.fk_case_uuid != None
            ).scalar() or 0

            return pytest_count + testng_count
        except Exception as e:
            # 记录异常日志，避免程序崩溃
            raise Exception(f"查询测试计划用例数量失败: {str(e)}")

    def get_test_plans_with_count(
            self,
            workspace_id: int,
            plan_name: str = None,
            creator: str = None,
            limit: int = 10,
            offset: int = 0
    ) -> tuple[list[type[TestPlanModel]], int]:
        """分页获取测试计划列表"""
        query = self.db.query(TestPlanModel).filter(TestPlanModel.workspace_id == workspace_id)

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
        workspace_id = test_plan.workspace_id

        pytest_case = self.db.query(PytestCaseModel).filter(
            PytestCaseModel.case_uuid == pytest_case_uuid,
        ).filter(
            PytestCaseModel.workspace_id == workspace_id
        ).first()

        if not pytest_case:
            return False

        # 检查是否已关联
        exists = self.db.query(TestPlanPytestCaseModel).filter(
            TestPlanPytestCaseModel.test_plan_id == test_plan_id,
            TestPlanPytestCaseModel.case_uuid == pytest_case_uuid
        ).first()

        # 如果不存在，则插入新记录
        if not exists:
            # 创建新的关联记录
            association = TestPlanPytestCaseModel(
                workspace_id=workspace_id,
                test_plan_id=test_plan_id,
                case_uuid=pytest_case_uuid,
                fk_case_uuid=pytest_case_uuid,
                case_name=pytest_case.case_name,
                case_author=pytest_case.case_author,
                is_disabled=False  # 新增记录默认未失效
            )
            self.db.add(association)
            self.db.commit()
        else:
            # 如果存在，则修改is_disabled字段为False
            exists.fk_case_uuid = pytest_case_uuid
            exists.is_disabled = False
            self.db.commit()

        self.update_plan_cases_count(test_plan_id)
        return True

    def remove_pytest_case_from_plan(self, test_plan_id: int, pytest_case_uuid: str) -> bool:
        """从测试计划移除Pytest用例"""
        test_plan = self.get_test_plan_by_id(test_plan_id)
        if not test_plan:
            return False

        case = self.db.query(TestPlanPytestCaseModel).filter(
            TestPlanPytestCaseModel.test_plan_id == test_plan_id,
            TestPlanPytestCaseModel.case_uuid == pytest_case_uuid
        ).first()

        # 删除关联记录
        if case:
            self.db.delete(case)
            self.db.commit()
            self.update_plan_cases_count(test_plan_id)
        return True

    def add_testng_case_to_plan(self, test_plan_id: int, testng_case_uuid: str) -> bool:
        """添加TestNG用例到测试计划"""
        test_plan = self.get_test_plan_by_id(test_plan_id)
        if not test_plan:
            return False
        workspace_id = test_plan.workspace_id

        testng_case = self.db.query(TestNGCaseModel).filter(
            TestNGCaseModel.case_uuid == testng_case_uuid
        ).filter(
            TestNGCaseModel.workspace_id == workspace_id
        ).first()

        if not testng_case:
            return False

        # 检查是否已关联
        exists = self.db.query(TestPlanTestNGCaseModel).filter(
            TestPlanTestNGCaseModel.test_plan_id == test_plan_id,
            TestPlanTestNGCaseModel.case_uuid == testng_case_uuid
        ).first()

        # 如果不存在，则插入新记录
        if not exists:
            # 创建新的关联记录
            association = TestPlanTestNGCaseModel(
                workspace_id=workspace_id,
                test_plan_id=test_plan_id,
                case_uuid=testng_case_uuid,
                case_name=testng_case.case_name,
                case_author=testng_case.case_author,
                fk_case_uuid=testng_case_uuid,
                is_disabled=False  # 新增记录默认未失效
            )
            self.db.add(association)
            self.db.commit()
        else:
            # 如果存在，则修改is_disabled字段为False
            exists.fk_case_uuid = testng_case_uuid
            exists.is_disabled = False
            self.db.commit()
        self.update_plan_cases_count(test_plan_id)
        return True

    def remove_testng_case_from_plan(self, test_plan_id: int, testng_case_uuid: str) -> bool:
        """从测试计划移除TestNG用例"""
        test_plan = self.get_test_plan_by_id(test_plan_id)
        if not test_plan:
            return False
        case = self.db.query(TestPlanTestNGCaseModel).filter(
            TestPlanTestNGCaseModel.test_plan_id == test_plan_id,
            TestPlanTestNGCaseModel.case_uuid == testng_case_uuid
        ).first()
        if case:
            self.db.delete(case)
            self.db.commit()
            self.update_plan_cases_count(test_plan_id)
        return True

    def clear_cases_from_plan(self, test_plan_id: int) -> bool:
        """清空测试计划中的所有用例"""
        try:
            # 直接操作关联表
            self.db.query(TestPlanPytestCaseModel).filter(
                TestPlanPytestCaseModel.test_plan_id == test_plan_id
            ).delete()
            self.db.query(TestPlanTestNGCaseModel).filter(
                TestPlanTestNGCaseModel.test_plan_id == test_plan_id
            ).delete()
            self.db.commit()
            self.update_plan_cases_count(test_plan_id)
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"清空测试计划用例失败: {e}")
            return False

    def clear_invalid_cases_from_plan(self, test_plan_id: int) -> bool:
        """清空测试计划中的无效用例"""
        try:
            # 直接操作关联表
            self.db.query(TestPlanPytestCaseModel).filter(
                TestPlanPytestCaseModel.test_plan_id == test_plan_id,
                TestPlanPytestCaseModel.fk_case_uuid == None
            ).delete()
            self.db.query(TestPlanTestNGCaseModel).filter(
                TestPlanTestNGCaseModel.test_plan_id == test_plan_id,
                TestPlanTestNGCaseModel.fk_case_uuid == None
            ).delete()
            self.db.commit()
            self.update_plan_cases_count(test_plan_id)
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"清空测试计划中失效用例失败: {e}")
            return False

    def update_plan_cases_count(self, test_plan_id: int) -> bool:
        """刷新测试计划中的用例关联"""
        test_plan = self.get_test_plan_by_id(test_plan_id)
        count = self.get_test_plan_cases_count(test_plan_id)
        test_plan.total_case_count = count
        self.db.commit()
        return True

    def update_workspace_plan_case_status(self, workspace_id: int, case_type: str) -> bool:
        """刷新工作空间中的测试计划数量"""
        try:
            if case_type == CaseType.PYTEST:
                testplan_pytest_cases = self.db.query(TestPlanPytestCaseModel).filter(
                    TestPlanPytestCaseModel.workspace_id == workspace_id
                ).all()
                for testplan_pytest_case in testplan_pytest_cases:
                    pytest_case = self.db.query(PytestCaseModel).filter(
                        PytestCaseModel.case_uuid == testplan_pytest_case.case_uuid
                    ).first()
                    if pytest_case:
                        testplan_pytest_case.case_name = pytest_case.case_name
                        testplan_pytest_case.case_author = pytest_case.case_author
                        testplan_pytest_case.fk_case_uuid = pytest_case.case_uuid
                        testplan_pytest_case.is_disabled = False
                    else:
                        testplan_pytest_case.fk_case_uuid = None
                        testplan_pytest_case.is_disabled = False
            elif case_type == CaseType.TESTNG:
                testplan_testng_cases = self.db.query(TestPlanTestNGCaseModel).filter(
                    TestPlanTestNGCaseModel.workspace_id == workspace_id
                ).all()
                for testplan_testng_case in testplan_testng_cases:
                    testng_case = self.db.query(TestNGCaseModel).filter(
                        TestNGCaseModel.case_uuid == testplan_testng_case.case_uuid
                    ).first()
                    if testng_case:
                        testplan_testng_case.case_name = testng_case.case_name
                        testplan_testng_case.case_author = testng_case.case_author
                        testplan_testng_case.fk_case_uuid = testng_case.case_uuid
                        testplan_testng_case.is_disabled = False
                    else:
                        testplan_testng_case.fk_case_uuid = None
                        testplan_testng_case.is_disabled = False
            self.db.commit()
            # 更新测试计划中的用例数量
            test_plans = self.db.query(TestPlanModel).filter(TestPlanModel.workspace_id == workspace_id).all()
            for test_plan in test_plans:
                self.update_plan_cases_count(test_plan_id=test_plan.id)
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"刷新工作空间测试计划关联的用例状态失败: {e}")
            return False

    def get_test_tasks_with_count(
            self,
            workspace_id: int,
            test_plan_id: Optional[int] = None,
            page: Optional[int] = None,
            size: Optional[int] = None
    ) -> tuple[list[type[TestTaskModel]], int]:
        """
        获取指定工作空间下的测试任务（支持筛选测试计划，含总数+计划名称），按创建时间降序排列

        Args:
            workspace_id: 工作空间ID（必填）
            test_plan_id: 测试计划ID（可选，为空时查询该工作空间下所有任务）
            page: 页码（从1开始），为None时返回所有数据
            size: 每页条数，为None时返回所有数据

        Returns:
            Tuple[int, List[Dict]]: (总任务数, 任务列表)
            任务字典包含：TestTaskModel所有字段 + plan_name（测试计划名称）
        """
        # 校验必填参数
        if workspace_id is None or workspace_id <= 0:
            raise ValueError("workspace_id 必须为正整数")

        # 1. 构建基础查询：多表联查（左连接，保留无关联计划的任务）
        # 左连接说明：即使任务的test_plan_id无效/为空，也能返回任务（plan_name为None）
        base_query = self.db.query(
            TestTaskModel
        ).filter(
            # 核心过滤：工作空间ID（两张表都要过滤，避免跨工作空间关联）
            TestTaskModel.workspace_id == workspace_id
        )

        # 2. 可选过滤：测试计划ID
        if test_plan_id is not None and test_plan_id > 0:
            base_query = base_query.filter(TestTaskModel.test_plan_id == test_plan_id)

        # 3. 排序：按创建时间降序
        base_query = base_query.order_by(TestTaskModel.create_time.desc())

        # 4. 查询总条数（性能最优：仅查任务表主键，复用过滤条件）
        count_query = self.db.query(func.count(TestTaskModel.id)).filter(
            TestTaskModel.workspace_id == workspace_id
        )
        if test_plan_id is not None and test_plan_id > 0:
            count_query = count_query.filter(TestTaskModel.test_plan_id == test_plan_id)
        total = cast(int, count_query.scalar() or 0)

        # 5. 处理分页逻辑
        if page is not None and size is not None:
            # 参数合法性校验
            page = max(page, 1)
            size = max(size, 1)
            offset = (page - 1) * size
            base_query = base_query.offset(offset).limit(size)

        # 执行查询
        query_result = base_query.all()

        return query_result, total

    def trigger_testplan(self, test_plan_id: int, trigger_user: str) -> bool:
        """触发测试计划"""
        test_plan = self.get_test_plan_by_id(test_plan_id)
        if not test_plan:
            raise Exception(f"测试计划id：{test_plan_id} 不存在")

        # 获取所有关联的用例
        associated_cases, invalid_cases = self.get_test_cases_by_plan_id(test_plan_id)
        test_plan.total_case_count = len(associated_cases)

        # 有效的用例
        valid_cases = []

        for case in associated_cases:
            if case['case_type'] == CaseType.PYTEST:
                pytest_case = self.db.query(PytestCaseModel).filter(
                    PytestCaseModel.case_uuid == case['case_uuid']
                ).first()
                if not pytest_case:
                    continue
                valid_cases.append(pytest_case)
            elif case['case_type'] == CaseType.TESTNG:
                testng_case = self.db.query(TestNGCaseModel).filter(
                    TestNGCaseModel.case_uuid == case['case_uuid']
                ).first()
                if not testng_case:
                    continue
                valid_cases.append(testng_case)

        if not valid_cases:
            raise Exception("当前测试计划下没有有效的用例可以执行")

        # 创建测试任务task
        task = TestTaskModel(workspace_id=test_plan.workspace_id,
                             test_plan_id=test_plan_id,
                             task_name=test_plan.plan_name,
                             fail_stop=test_plan.fail_stop,
                             task_execution_mode=test_plan.execution_mode,
                             test_environment=test_plan.test_environment,
                             task_status=TaskStatus.PENDING,
                             create_user=trigger_user,
                             task_result={
                                 "total_case_count": len(valid_cases),
                                 "finished_case_count": 0
                             },
                             create_time=now(),
                             update_time=now()
                             )
        self.db.add(task)
        self.db.commit()
        task_id = task.id

        # 创建测试任务taskJob
        for case in valid_cases:
            job = TaskJobModel(workspace_id=test_plan.workspace_id,
                               task_id=task_id,
                               test_plan_id=test_plan_id,
                               case_name=case.case_name,
                               case_uuid=case.case_uuid,
                               case_type=case.case_type,
                               case_function_list=case.case_function_list,
                               job_status=JobStatus.PENDING,
                               case_path=case.case_path,
                               case_package=case.case_package,
                               create_time=now(),
                               update_time=now(),
                               time_consuming=0
                               )
            self.db.add(job)
            self.db.commit()
            test_plan.pending_task_count += 1
            self.db.commit()

        if task.task_execution_mode == ExecutionMode.SERIAL:
            case_task_executor.push(
                task_id=task_id,
                workspace_id=test_plan.workspace_id,
                plan_id=test_plan_id,
            )
        elif task.task_execution_mode == ExecutionMode.PARALLEL:
            case_jobs = self.db.query(TaskJobModel).filter(
                TaskJobModel.task_id == task_id
            )
            for case_job in case_jobs:
                if case_job.case_type == CaseType.PYTEST:
                    pytest_case_job_executor.push(
                        task_id=task_id,
                        workspace_id=test_plan.workspace_id,
                        plan_id=test_plan_id,
                        job_id=case_job.id
                    )
                elif case_job.case_type == CaseType.TESTNG:
                    testng_case_job_executor.push(
                        task_id=task_id,
                        workspace_id=test_plan.workspace_id,
                        plan_id=test_plan_id,
                        job_id=case_job.id
                    )


def get_test_plan_crud(db: Session) -> TestPlanCRUD:
    """获取测试计划CRUD实例"""
    return TestPlanCRUD(db)
