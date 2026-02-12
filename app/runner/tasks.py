# -*- coding:utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import os
import time
import traceback

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum
from funboost.utils.func_timeout.exceptions import FunctionTimedOut
from sqlalchemy.orm import Session

from app.case_handler.case_parser import GitCaseParser

from app.case_handler.models import PytestCaseModel, TestNGCaseModel
from app.core.config import REPORT_ROOT, REPORT_URL
from app.core.database import get_sync_db
from app.core.redis import get_redis_cache
from app.runner.pytest_runner import PytestCaseRunner, create_error_html_report_file
from app.runner.testng_runner import TestNGCaseRunner
from app.testplan.controller import get_test_plan_crud
from app.testplan.models import CaseType, TestTaskModel, TaskJobModel, JobStatus, TaskStatus, ExecutionMode
from utils.commonlib import now
from utils.custom_logging import logger


class BaseBoosterParams(BoosterParams):
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    max_retry_times: int = 0
    concurrent_mode: str = ConcurrentModeEnum.THREADING
    is_auto_start_consuming_message: bool = False


@boost(BaseBoosterParams(
    queue_name='trigger_testplan',
    qps=50,
    concurrent_num=500,
    function_timeout=5
))
def trigger_testplan(test_plan_id: int, trigger_user: str) -> bool:
    """触发测试计划"""
    db = next(get_sync_db())
    curd = get_test_plan_crud(db)
    test_plan = curd.get_test_plan_by_id(test_plan_id)
    if not test_plan:
        raise Exception(f"测试计划id：{test_plan_id} 不存在")

    # 获取所有关联的用例
    associated_cases, invalid_cases = curd.get_test_cases_by_plan_id(test_plan_id)
    test_plan.total_case_count = len(associated_cases)

    # 有效的用例
    valid_cases = []

    for case in associated_cases:
        if case['case_type'] == CaseType.PYTEST:
            pytest_case = curd.db.query(PytestCaseModel).filter(
                PytestCaseModel.case_uuid == case['case_uuid']
            ).first()
            if not pytest_case:
                continue
            valid_cases.append(pytest_case)
        elif case['case_type'] == CaseType.TESTNG:
            testng_case = curd.db.query(TestNGCaseModel).filter(
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
    curd.db.add(task)
    curd.db.commit()
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
                           time_consuming=0,
                           case_commit_id=case.case_commit_id
                           )
        curd.db.add(job)
        curd.db.commit()
        test_plan.pending_task_count += 1
        curd.db.commit()

    if task.task_execution_mode == ExecutionMode.SERIAL:
        case_task_executor.push(
            task_id=task_id,
            workspace_id=test_plan.workspace_id,
            plan_id=test_plan_id,
        )
    elif task.task_execution_mode == ExecutionMode.PARALLEL:
        case_jobs = curd.db.query(TaskJobModel).filter(
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


def ui_json_2_dict(ui_json: str):
    """
    将wtp传过来的uiJson转换成dict
    :param ui_json:
    :return:
    """
    ui_json = json.loads(ui_json)
    for item in ui_json:
        if not item.get('keyValue'):
            item['keyValue'] = ''
    try:
        ui_json = {item['keyName']: item['keyValue'] for item in ui_json}
        return ui_json
    except Exception:
        return {}


def update_task_status(task_id: int, db: Session):
    """
    更新任务状态
    :param task_id: 任务id
    :param db: 数据库会话
    :return:
    """
    redis_cache_instance = get_redis_cache()
    lock_key = f"task_lock:{task_id}"
    while True:
        if not redis_cache_instance.get(lock_key):
            redis_cache_instance.set(lock_key, 1, expire=5)
            try:
                # 直接使用传入的数据库会话
                # 查询指定的任务
                logger.info(f"更新任务状态: {task_id}")
                task = db.query(TestTaskModel).filter(TestTaskModel.id == task_id).first()
                task_result = task.task_result.copy()  # 这是大坑，一定要用 copy，SQLAlchemy的ORM跟踪机制对于复杂对象（如字典）的变更检测可能不如对简单属性的变更检测敏感。当修改字典内部元素时，ORM可能无法检测到这个变化，除非整个对象被重新赋值。使用.copy()方法创建新字典对象，确保ORM能正确检测到变更并同步到数据库。
                if task_result["finished_case_count"] + 1 == task_result["total_case_count"]:
                    task.task_status = TaskStatus.COMPLETED
                task_result["finished_case_count"] += 1
                logger.info(f"任务状态更新中: {task_id},task_result:{task_result}")
                task.task_result = task_result
                db.commit()
                logger.info(f"任务状态更新完成: {task_id}")

            except Exception as e:
                # 如果出现异常，回滚事务
                db.rollback()
                logger.error(f"更新任务状态时出错: {e}")
                raise e
            finally:
                # 防止死锁 释放锁
                redis_cache_instance.delete(lock_key)
                break
        else:
            # 已经被其他任务上锁 等待1s后重试
            time.sleep(1)
            continue


@boost(BaseBoosterParams(
    queue_name='case_task_executor',
    qps=1,
    concurrent_num=50,
    function_timeout=60 * 60 * 2
))
def case_task_executor(workspace_id: int, plan_id: int, task_id: int):
    """
    【case计划串行执行器】
    :param workspace_id: wtp用例库id
    :param plan_id: 计划id
    :param task_id: 任务id
    """

    def cancel_job(to_be_cancelled_job_list: list, _db: Session):
        """
        取消job
        :param to_be_cancelled_job_list: 待取消的任务列表
        :param _db 数据库session
        :return:
        """
        for cancel_case_job in to_be_cancelled_job_list:
            logger.info(f'取消任务: {cancel_case_job.case_name + "-----" + cancel_case_job.case_uuid}')
            cancel_case_job.job_status = JobStatus.CANCELED
            _db.commit()
            update_task_status(task_id, db)

    # 获取task实例和jobs实例
    db = next(get_sync_db())
    case_task = db.query(TestTaskModel).filter(TestTaskModel.id == task_id).first()
    if not case_task:
        logger.error(f'任务不存在: {task_id}')
        raise Exception(f'任务不存在: {task_id}')
    case_task.task_status = TaskStatus.RUNNING
    db.commit()

    case_jobs = db.query(TaskJobModel).filter(TaskJobModel.task_id == task_id).all()

    for index, case_job in enumerate(case_jobs):
        logger.info(f'准备执行串行case:{case_job.case_name + "-----" + case_job.case_uuid}')

        # 数据库不存在case信息 从gitlab获取 不保存到数据库
        case_extra_info = GitCaseParser.parse_case_uuid(case_uuid=case_job.case_uuid)
        case_job.job_status = JobStatus.RUNNING
        db.commit()
        from app.case_handler.case_sync import get_case_model_by_case_type
        case_model = get_case_model_by_case_type(case_type=case_job.case_type)

        try:
            if case_job.case_type == CaseType.PYTEST:
                # 获取pytest用例信息
                case_execute_result = PytestCaseRunner.executor(
                    testplan_id=case_task.test_plan_id,
                    task_id=task_id, job_id=case_job.id,
                    workspace_id=workspace_id,
                    case_path=case_job.case_path,
                    case_name=case_job.case_name,
                    project_id=case_extra_info["git_project_id"],
                    env=case_task.test_environment,
                    branch_name=case_extra_info["branch_name"],
                    case_uuid=case_job.case_uuid
                )
            elif case_job.case_type == CaseType.TESTNG:
                # 获取testng用例信息
                case_execute_result = TestNGCaseRunner.executor(
                    testplan_id=case_task.test_plan_id,
                    task_id=task_id, job_id=case_job.id,
                    workspace_id=workspace_id,
                    case_path=case_job.case_path,
                    case_name=case_job.case_name,
                    case_package=case_job.case_package,
                    project_id=case_extra_info["git_project_id"],
                    env=case_task.test_environment,
                    branch_name=case_extra_info["branch_name"],
                    case_uuid=case_job.case_uuid
                )
            else:
                raise Exception(f'不支持的case类型: {case_job.case_type}')

            logger.info(f'{case_job.case_name} 执行结果: {case_execute_result}')

            # 判断case执行结果
            if case_execute_result['case_result']['successful'] < 100:
                # case通过率小于100 说明存在失败case
                logger.error(f'{case_job.case_name + "-----" + case_job.case_uuid} 存在失败case')
                case_job.job_status = JobStatus.FAILED
                case_job.job_result = case_execute_result['case_result']
                case_job.report_path = case_execute_result['case_report']
                db.commit()
                update_task_status(task_id, db)
                if case_task.fail_stop:
                    # 失败时停止 结束后续case执行
                    cancel_job(case_jobs[index + 1:], db)
                    raise Exception(f'{case_job.case_name} 执行失败,失败时终止: {traceback.format_exc()}')
            else:
                # case通过率等于100 说明全部执行成功
                logger.info(f'{case_job} case全部执行成功')
                case_job.job_status = JobStatus.SUCCESS
                case_job.job_result = case_execute_result['case_result']
                case_job.report_path = case_execute_result['case_report']
                db.commit()
                update_task_status(task_id, db)
                continue

        except FunctionTimedOut:
            # case执行时间超时
            # logger.error(
            #     f'{case_job} 执行超时: {traceback.format_exc()}')
            case_job.job_status = JobStatus.TIMEOUT
            db.commit()
            logger.error(
                f'job状态{case_job.job_status}')
            db_case_info = db.query(case_model).filter(
                case_model.case_uuid == case_job.case_uuid).first()

            report_name = case_job.case_path.split('/')[-1].split('.')[0] + '.html'
            report_dir = os.path.join(
                REPORT_ROOT, str(workspace_id), str(plan_id), str(task_id), str(case_job.id))
            report_html_path = os.path.join(report_dir, report_name)
            report_url = os.path.join(REPORT_URL, str(workspace_id), str(plan_id), str(task_id), str(case_job.id),
                                      report_name)
            logger.info(f'生成错误报告: {report_html_path}')
            create_error_html_report_file(workspace_id=workspace_id,
                                          git_project_name=db_case_info.git_project_name,
                                          case_type=CaseType.PYTEST,
                                          case_path=case_job.case_path, case_name=case_job.case_name,
                                          case_level=db_case_info.case_level,
                                          case_author=db_case_info.case_author,
                                          report_url=report_url,
                                          report_path=report_html_path,
                                          result=JobStatus.TIMEOUT,
                                          error_info="case执行超时,未能生成详细测试报告")
            cancel_job(case_jobs[index + 1:], _db=db)
            case_job.report_path = report_url
            case_task.task_status = TaskStatus.TIMEOUT
            db.commit()
            cancel_job(case_jobs[index + 1:], db)
            update_task_status(task_id, db)
            raise Exception(f'{case_job.case_name} 执行超时: {traceback.format_exc()}')

        except Exception:
            # case执行异常
            logger.error(f'{case_job.case_name} 执行异常: {traceback.format_exc()}')
            case_job.job_status = JobStatus.EXCEPTION
            db_case_info = db.query(case_model).filter(
                case_model.case_uuid == case_job.case_uuid).first()

            report_name = case_job.case_path.split('/')[-1].split('.')[0] + '.html'
            report_dir = os.path.join(
                REPORT_ROOT, str(workspace_id), str(plan_id), str(task_id), str(case_job.id))
            report_html_path = os.path.join(report_dir, report_name)
            report_url = os.path.join(REPORT_URL, str(workspace_id), str(plan_id), str(task_id), str(case_job.id),
                                      report_name)
            create_error_html_report_file(workspace_id=workspace_id,
                                          git_project_name=db_case_info.git_project_name,
                                          case_type=CaseType.PYTEST,
                                          case_path=case_job.case_path, case_name=case_job.case_name,
                                          case_level=db_case_info.case_level,
                                          case_author=db_case_info.case_author,
                                          report_url=report_url,
                                          report_path=report_html_path,
                                          result=JobStatus.EXCEPTION,
                                          error_info=f"case执行异常,未能生成详细测试报告:{traceback.format_exc()}")
            case_job.report_path = report_url
            db.commit()
            if case_task.fail_stop:
                # 失败时停止 结束后续case执行
                cancel_job(case_jobs[index + 1:], _db=db)
                update_task_status(task_id, db)
                raise Exception(f'{case_job.case_name} 执行异常,失败时终止: {traceback.format_exc()}')
            else:
                update_task_status(task_id, db)
                continue

    return f'测试任务: {task_id} 执行完成'


@boost(BaseBoosterParams(
    queue_name='pytest_case_job_executor',
    qps=1,
    concurrent_num=50,
    function_timeout=40
))
def pytest_case_job_executor(workspace_id: int, plan_id: int, task_id: int, job_id: int):
    """
    【case job执行处理器】
    :param workspace_id: wtp用例库id
    :param plan_id: 计划id
    :param task_id 任务id
    :param job_id job id
    :return:
    """

    # 执行case job
    # 获取task实例和jobs实例
    db = next(get_sync_db())
    case_task = db.query(TestTaskModel).filter(TestTaskModel.id == task_id).first()
    if not case_task:
        logger.error(f'任务不存在: {task_id}')
        raise Exception(f'任务不存在: {task_id}')

    case_job = db.query(TaskJobModel).filter(TaskJobModel.id == job_id).first()
    case_job.job_status = JobStatus.RUNNING
    case_task.task_status = TaskStatus.RUNNING
    db.commit()
    case_extra_info = GitCaseParser.parse_case_uuid(case_uuid=case_job.case_uuid)
    try:
        case_execute_result = PytestCaseRunner.executor(
            testplan_id=case_task.test_plan_id,
            task_id=task_id, job_id=case_job.id,
            workspace_id=workspace_id,
            case_path=case_job.case_path,
            case_name=case_job.case_name,
            project_id=case_extra_info["git_project_id"],
            env=case_task.test_environment,
            branch_name=case_extra_info["branch_name"],
            case_uuid=case_job.case_uuid
        )
        logger.info(f'{case_job.case_name} 执行结果: {case_execute_result}')

        # 判断case执行结果
        if case_execute_result['case_result']['successful'] < 100:
            # case通过率小于100 说明存在失败case
            logger.error(f'{case_job.case_name} 存在失败case')
            case_job.job_status = JobStatus.FAILED
            case_job.job_result = case_execute_result['case_result']
            case_job.report_path = case_execute_result['case_report']
            db.commit()
            return f'存在失败case: {case_execute_result}'
        else:
            # case通过率等于100 说明全部执行成功
            logger.info(f'{case_job.case_name} case全部执行成功')
            case_job.job_status = JobStatus.SUCCESS
            case_job.job_result = case_execute_result['case_result']
            case_job.report_path = case_execute_result['case_report']
            db.commit()
            return f'case全部执行成功: {case_execute_result}'

    except FunctionTimedOut:
        # case执行时间超时
        case_job.job_status = JobStatus.TIMEOUT
        db.commit()
        db_case_info = db.query(PytestCaseModel).filter(
            PytestCaseModel.case_uuid == case_job.case_uuid).first()
        report_name = case_job.case_path.split('/')[-1].split('.')[0] + '.html'
        report_dir = os.path.join(
            REPORT_ROOT, str(workspace_id), str(plan_id), str(task_id), str(case_job.id))
        report_html_path = os.path.join(report_dir, report_name)
        report_url = os.path.join(REPORT_URL, str(workspace_id), str(plan_id), str(task_id), str(case_job.id),
                                  report_name)
        create_error_html_report_file(workspace_id=workspace_id,
                                      git_project_name=db_case_info.git_project_name,
                                      case_type=CaseType.PYTEST,
                                      case_path=case_job.case_path, case_name=case_job.case_name,
                                      case_level=db_case_info.case_level,
                                      case_author=db_case_info.case_author,
                                      report_url=report_url,
                                      report_path=report_html_path,
                                      result=JobStatus.TIMEOUT,
                                      error_info=f"case执行超时,未能生成详细测试报告")
        case_job.report_path = report_url
        db.commit()
        raise Exception(f'{case_job.case_name} 执行超时: {traceback.format_exc()}')

    except Exception:
        # case执行异常
        case_job.job_status = JobStatus.EXCEPTION
        db_case_info = db.query(PytestCaseModel).filter(
            PytestCaseModel.case_uuid == case_job.case_uuid).first()
        report_name = case_job.case_path.split('/')[-1].split('.')[0] + '.html'
        report_dir = os.path.join(
            REPORT_ROOT, str(workspace_id), str(plan_id), str(task_id), str(case_job.id))
        report_html_path = os.path.join(report_dir, report_name)
        report_url = os.path.join(REPORT_URL, str(workspace_id), str(plan_id), str(task_id), str(case_job.id),
                                  report_name)
        create_error_html_report_file(workspace_id=workspace_id,
                                      git_project_name=db_case_info.git_project_name,
                                      case_type=CaseType.PYTEST,
                                      case_path=case_job.case_path, case_name=case_job.case_name,
                                      case_level=db_case_info.case_level,
                                      case_author=db_case_info.case_author,
                                      report_url=report_url,
                                      report_path=report_html_path,
                                      result=JobStatus.EXCEPTION,
                                      error_info=f"case执行异常,未能生成详细测试报告:{traceback.format_exc()}")
        case_job.report_path = report_url
        db.commit()
        raise Exception(f'{case_job.case_name} 执行异常: {traceback.format_exc()}')


@boost(BaseBoosterParams(
    queue_name='testng_case_task_executor',
    qps=1,
    concurrent_num=50,
    function_timeout=5
))
def testng_case_task_executor(workspace_id: int, plan_id: int, task_id: int):
    """
    【case计划串行执行器】
    :param workspace_id: wtp用例库id
    :param plan_id: 计划id
    :param task_id: 任务id
    :return: 结果/异常
    """

    def cancel_job(to_be_cancelled_job_list: list, _db: Session):
        """
        取消job
        :param to_be_cancelled_job_list: 待取消的任务列表
        :param _db 数据库session
        :return:
        """
        for cancel_case_job in to_be_cancelled_job_list:
            logger.info(f'取消任务: {cancel_case_job.case_name + "-----" + cancel_case_job.case_uuid}')
            cancel_case_job.job_status = JobStatus.CANCELED
            _db.commit()

    # 获取task实例和jobs实例
    db = next(get_sync_db())
    case_task = db.query(TestTaskModel).filter(TestTaskModel.id == task_id).first()
    if not case_task:
        logger.error(f'任务不存在: {task_id}')
        raise Exception(f'任务不存在: {task_id}')
    case_task.task_status = TaskStatus.RUNNING
    db.commit()

    case_jobs = db.query(TaskJobModel).filter(TaskJobModel.task_id == task_id).all()

    for index, case_job in enumerate(case_jobs):
        logger.info(f'准备执行串行case:{case_job.case_name + "-----" + case_job.case_uuid}')

        # 数据库不存在case信息 从gitlab获取 不保存到数据库
        case_extra_info = GitCaseParser.parse_case_uuid(case_uuid=case_job.case_uuid)
        case_job.job_status = JobStatus.RUNNING
        db.commit()
        try:
            case_execute_result = TestNGCaseRunner.executor(
                testplan_id=case_task.test_plan_id,
                task_id=task_id, job_id=case_job.id,
                workspace_id=workspace_id,
                case_path=case_job.case_path,
                case_name=case_job.case_name,
                case_package=case_job.case_package,
                project_id=case_extra_info["git_project_id"],
                env=case_task.test_environment,
                branch_name=case_extra_info["branch_name"],
                case_uuid=case_job.case_uuid)
            logger.info(f'{case_job.case_name} 执行结果: {case_execute_result}')

            # 判断case执行结果
            if case_execute_result['case_result']['successful'] < 100:
                # case通过率小于100 说明存在失败case
                logger.error(f'{case_job.case_name + "-----" + case_job.case_uuid} 存在失败case')
                case_job.job_status = JobStatus.FAILED
                case_job.job_result = case_execute_result['case_result']
                case_job.report_path = case_execute_result['case_report']
                db.commit()
                if case_task.fail_stop:
                    # 失败时停止 结束后续case执行
                    cancel_job(case_jobs[index + 1:], db)
                    raise Exception(f'{case_job.case_name} 执行失败,失败时终止: {traceback.format_exc()}')
            else:
                # case通过率等于100 说明全部执行成功
                logger.info(f'{case_job} case全部执行成功')
                case_job.job_status = JobStatus.SUCCESS
                case_job.job_result = case_execute_result['case_result']
                case_job.report_path = case_execute_result['case_report']
                db.commit()
                continue

        except FunctionTimedOut:
            # case执行时间超时
            # logger.error(
            #     f'{case_job} 执行超时: {traceback.format_exc()}')
            case_job.job_status = JobStatus.TIMEOUT
            db.commit()
            logger.error(
                f'job状态{case_job.job_status}')
            db_case_info = db.query(TestNGCaseModel).filter(
                TestNGCaseModel.case_uuid == case_job.case_uuid).first()

            report_name = case_job.case_path.split('/')[-1].split('.')[0] + '.html'
            report_dir = os.path.join(
                REPORT_ROOT, str(workspace_id), str(plan_id), str(task_id), str(case_job.id))
            report_html_path = os.path.join(report_dir, report_name)
            report_url = os.path.join(REPORT_URL, str(workspace_id), str(plan_id), str(task_id), str(case_job.id),
                                      report_name)
            logger.info(f'生成错误报告: {report_html_path}')
            create_error_html_report_file(workspace_id=workspace_id,
                                          git_project_name=db_case_info.git_project_name,
                                          case_type=CaseType.PYTEST,
                                          case_path=case_job.case_path, case_name=case_job.case_name,
                                          case_level=db_case_info.case_level,
                                          case_author=db_case_info.case_author,
                                          report_url=report_url,
                                          report_path=report_html_path,
                                          result=JobStatus.TIMEOUT,
                                          error_info="case执行超时,未能生成详细测试报告")
            cancel_job(case_jobs[index + 1:], _db=db)
            case_job.report_path = report_url
            db.commit()
            raise Exception(f'{case_job.case_name} 执行超时: {traceback.format_exc()}')

        except Exception:
            # case执行异常
            logger.error(f'{case_job.case_name} 执行异常: {traceback.format_exc()}')
            case_job.job_status = JobStatus.EXCEPTION
            db_case_info = db.query(TestNGCaseModel).filter(
                TestNGCaseModel.case_uuid == case_job.case_uuid).first()

            report_name = case_job.case_path.split('/')[-1].split('.')[0] + '.html'
            report_dir = os.path.join(
                REPORT_ROOT, str(workspace_id), str(plan_id), str(task_id), str(case_job.id))
            report_html_path = os.path.join(report_dir, report_name)
            report_url = os.path.join(REPORT_URL, str(workspace_id), str(plan_id), str(task_id), str(case_job.id),
                                      report_name)
            create_error_html_report_file(workspace_id=workspace_id,
                                          git_project_name=db_case_info.git_project_name,
                                          case_type=CaseType.PYTEST,
                                          case_path=case_job.case_path, case_name=case_job.case_name,
                                          case_level=db_case_info.case_level,
                                          case_author=db_case_info.case_author,
                                          report_url=report_url,
                                          report_path=report_html_path,
                                          result=JobStatus.EXCEPTION,
                                          error_info=f"case执行异常,未能生成详细测试报告:{traceback.format_exc()}")
            case_job.report_path = report_url
            if case_task.fail_stop:
                # 失败时停止 结束后续case执行
                cancel_job(case_jobs[index + 1:], _db=db)
                raise Exception(f'{case_job.case_name} 执行异常,失败时终止: {traceback.format_exc()}')
            else:
                continue

    return f'测试任务: {task_id} 执行完成'


@boost(BaseBoosterParams(
    queue_name='testng_case_job_executor',
    qps=1,
    concurrent_num=50,
    function_timeout=40
))
def testng_case_job_executor(workspace_id: int, plan_id: int, task_id: int, job_id: int):
    """
    【case job执行处理器】
    :param workspace_id: wtp用例库id
    :param plan_id: 计划id
    :param task_id 任务id
    :param job_id job ID
    :return: 结果/异常
    """
    # 执行case job
    # 获取task实例和jobs实例
    db = next(get_sync_db())
    case_task = db.query(TestTaskModel).filter(TestTaskModel.id == task_id).first()
    if not case_task:
        logger.error(f'任务不存在: {task_id}')
        raise Exception(f'任务不存在: {task_id}')

    case_job = db.query(TaskJobModel).filter(TaskJobModel.id == job_id).first()
    case_job.job_status = JobStatus.RUNNING
    case_task.task_status = TaskStatus.RUNNING
    db.commit()
    case_extra_info = GitCaseParser.parse_case_uuid(case_uuid=case_job.case_uuid)
    try:
        case_execute_result = TestNGCaseRunner.executor(
            testplan_id=case_task.test_plan_id,
            task_id=task_id, job_id=case_job.id,
            workspace_id=workspace_id,
            case_path=case_job.case_path,
            case_name=case_job.case_name,
            case_package=case_job.case_package,
            project_id=case_extra_info["git_project_id"],
            env=case_task.test_environment,
            branch_name=case_extra_info["branch_name"],
            case_uuid=case_job.case_uuid
        )
        logger.info(f'{case_job.case_name} 执行结果: {case_execute_result}')

        # 判断case执行结果
        if case_execute_result['case_result']['successful'] < 100:
            # case通过率小于100 说明存在失败case
            logger.error(f'{case_job.case_name} 存在失败case')
            case_job.job_status = JobStatus.FAILED
            case_job.job_result = case_execute_result['case_result']
            case_job.report_path = case_execute_result['case_report']
            db.commit()
            return f'存在失败case: {case_execute_result}'
        else:
            # case通过率等于100 说明全部执行成功
            logger.info(f'{case_job.case_name} case全部执行成功')
            case_job.job_status = JobStatus.SUCCESS
            case_job.job_result = case_execute_result['case_result']
            case_job.report_path = case_execute_result['case_report']
            db.commit()
            return f'case全部执行成功: {case_execute_result}'

    except FunctionTimedOut:
        # case执行时间超时
        case_job.job_status = JobStatus.TIMEOUT
        db.commit()
        db_case_info = db.query(TestNGCaseModel).filter(
            TestNGCaseModel.case_uuid == case_job.case_uuid).first()
        report_name = case_job.case_path.split('/')[-1].split('.')[0] + '.html'
        report_dir = os.path.join(
            REPORT_ROOT, str(workspace_id), str(plan_id), str(task_id), str(case_job.id))
        report_html_path = os.path.join(report_dir, report_name)
        report_url = os.path.join(REPORT_URL, str(workspace_id), str(plan_id), str(task_id), str(case_job.id),
                                  report_name)
        create_error_html_report_file(workspace_id=workspace_id,
                                      git_project_name=db_case_info.git_project_name,
                                      case_type=CaseType.PYTEST,
                                      case_path=case_job.case_path, case_name=case_job.case_name,
                                      case_level=db_case_info.case_level,
                                      case_author=db_case_info.case_author,
                                      report_url=report_url,
                                      report_path=report_html_path,
                                      result=JobStatus.TIMEOUT,
                                      error_info=f"case执行超时,未能生成详细测试报告")
        case_job.report_path = report_url
        db.commit()
        raise Exception(f'{case_job.case_name} 执行超时: {traceback.format_exc()}')

    except Exception:
        # case执行异常
        case_job.job_status = JobStatus.EXCEPTION
        db_case_info = db.query(TestNGCaseModel).filter(
            TestNGCaseModel.case_uuid == case_job.case_uuid).first()
        report_name = case_job.case_path.split('/')[-1].split('.')[0] + '.html'
        report_dir = os.path.join(
            REPORT_ROOT, str(workspace_id), str(plan_id), str(task_id), str(case_job.id))
        report_html_path = os.path.join(report_dir, report_name)
        report_url = os.path.join(REPORT_URL, str(workspace_id), str(plan_id), str(task_id), str(case_job.id),
                                  report_name)
        create_error_html_report_file(workspace_id=workspace_id,
                                      git_project_name=db_case_info.git_project_name,
                                      case_type=CaseType.PYTEST,
                                      case_path=case_job.case_path, case_name=case_job.case_name,
                                      case_level=db_case_info.case_level,
                                      case_author=db_case_info.case_author,
                                      report_url=report_url,
                                      report_path=report_html_path,
                                      result=JobStatus.EXCEPTION,
                                      error_info=f"case执行异常,未能生成详细测试报告:{traceback.format_exc()}")
        case_job.report_path = report_url
        db.commit()
        raise Exception(f'{case_job.case_name} 执行异常: {traceback.format_exc()}')
