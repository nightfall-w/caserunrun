# -*- coding:utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import os
import subprocess
import traceback

from funboost import boost, BoosterParams, BrokerEnum, ConcurrentModeEnum
from funboost.utils.func_timeout.exceptions import FunctionTimedOut
from sqlalchemy.orm import Session

from app.case_handler.case_parser import GitCaseParser
from app.case_handler.case_sync import InitGitCase
from app.case_handler.models import PytestCaseModel
from app.case_source.models import CaseSourceRelationModel
from app.core.config import REPORT_ROOT, REPORT_URL
from app.core.database import get_sync_db
from app.runner.pytest_runner import PytestCaseRunner, create_error_html_report_file
from app.testplan.models import CaseType, TestTaskModel, TaskJobModel, JobStatus, TaskStatus
from utils.custom_logging import logger


class MyBoosterParams(BoosterParams):
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    max_retry_times: int = 0
    concurrent_mode: str = ConcurrentModeEnum.THREADING
    is_auto_start_consuming_message: bool = False


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


def init_case_project(case_source_relation: CaseSourceRelationModel):
    """
    :param 用例关系表记录
    初始化case项目
    :return:
    """
    InitGitCase(case_source_relation=case_source_relation).sync()


@boost(MyBoosterParams(
    queue_name='pytest_case_task_executor',
    qps=1,
    concurrent_num=50,
    function_timeout=5
))
def pytest_case_task_executor(workspace_id: int, plan_id: int, task_id: int):
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
            logger.info(f'取消任务: {cancel_case_job}')
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
                logger.error(f'{case_job.case_name + "-----" + case_job.case_uuid} 存在失败case')
                case_job.job_status = JobStatus.COMPLETED
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
                case_job.job_status = JobStatus.COMPLETED
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
            db_case_info = db.query(PytestCaseModel).filter(
                PytestCaseModel.case_uuid == case_job.case_uuid).first()

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
            case_job.job_status = JobStatus.FAILED
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
                                          result=JobStatus.FAILED,
                                          error_info=f"case执行异常,未能生成详细测试报告:{traceback.format_exc()}")
            case_job.report_path = report_url
            if case_task.fail_stop:
                # 失败时停止 结束后续case执行
                cancel_job(case_jobs[index + 1:], _db=db)
                raise Exception(f'{case_job.case_name} 执行异常,失败时终止: {traceback.format_exc()}')
            else:
                continue

    return f'计划: {plan_id} 执行完成'


@boost(MyBoosterParams(
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
            case_job.job_status = JobStatus.COMPLETED
            case_job.job_result = case_execute_result['case_result']
            case_job.report_path = case_execute_result['case_report']
            db.commit()
            return f'存在失败case: {case_execute_result}'
        else:
            # case通过率等于100 说明全部执行成功
            logger.info(f'{case_job.case_name} case全部执行成功')
            case_job.job_status = JobStatus.COMPLETED
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
        case_job.job_status = JobStatus.FAILED
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
                                      result=JobStatus.FAILED,
                                      error_info=f"case执行异常,未能生成详细测试报告:{traceback.format_exc()}")
        case_job.report_path = report_url
        db.commit()
        raise Exception(f'{case_job.case_name} 执行异常: {traceback.format_exc()}')

# def testng_case_task_executor(workspace_id: int, plan_id: int, plan_result_id: int, wtp_case_info_list: list,
#                               fail_stop: int,
#                               env: int):
#     """
#     【case计划串行执行器】
#     :param workspace_id: wtp用例库id
#     :param plan_id: 计划id
#     :param plan_result_id: ==taskId 预生成的任务id
#     :param env: 环境
#     :param wtp_case_info_list: case列表
#     :param fail_stop: 失败时停止
#     """
#
#     def cancel_job(to_be_cancelled_job_list: list):
#         """
#         取消job
#         :param to_be_cancelled_job_list: 待取消的任务列表
#         :return:
#         """
#         for case_job in to_be_cancelled_job_list:
#             logger.info(f'取消任务: {case_job}')
#
#     def send_job_result(case_job: dict, result: int, case_execute_detail: dict,
#                         case_function_total_count: int = 0,
#                         case_function_success_count: int = 0):
#         """
#         发送成功任务
#         :param case_function_success_count: 脚本中case方法通过数
#         :param case_function_total_count: 脚本中case方法总数
#         :param case_job: 执行成功的case信息
#         :param result: 1：成功 0：失败 2：取消(终止)
#         :param case_execute_detail: case执行结果详情
#         :return:
#         """
#         logger.info(f'{case_job}case执行完成')
#         wtp_api.send_result(workspace_id=workspace_id,
#                             plan_id=plan_id,
#                             plan_result_id=plan_result_id,
#                             case_id=case_job["caseId"],
#                             snapshot_id=case_job.get("snapshotId"),
#                             snapshot_type=case_job.get("snapshotType"),
#                             result_id=case_job["resultId"], result=result,
#                             ui_log_json=json.dumps(case_execute_detail['case_result'], ensure_ascii=False),
#                             # log=case_execute_detail['case_log'],
#                             log="",
#                             case_function_total_count=case_function_total_count,
#                             case_function_success_count=case_function_success_count)
#
#     for index, wtp_case_info in enumerate(wtp_case_info_list):
#         logger.info(f'准备执行串行case:{wtp_case_info}')
#         db_case = TestNGCaseModel.objects.filter(workspace_id=workspace_id, case_uuid=wtp_case_info['uiId']).first()
#         if db_case:
#             # 数据库存在case信息 并获取case路径以及case方法总数
#             case_path = db_case.case_path
#             if db_case.case_function_list:
#                 # 数据库存在case functions信息 直接从数据库获取
#                 case_function_count = len(db_case.case_function_list)
#             else:
#                 # 数据库不存在case functions信息 从gitlab获取 并保存到数据库
#                 case_function_count = get_script_case_function_count_and_update(db_case_info=db_case,
#                                                                                 uiId=wtp_case_info['uiId'],
#                                                                                 git_commit_id=db_case.git_project_commit_id)
#         else:
#             # 数据库不存在case信息 从gitlab获取 不保存到数据库
#             case_function_count = get_script_case_function_count_and_update(uiId=wtp_case_info['uiId'],
#                                                                             git_commit_id=db_case.git_project_commit_id)
#             send_job_result(case_job=wtp_case_info,
#                             result=0,
#                             case_execute_detail={"case_result": {
#                                 "case_report": create_error_html_report_file(workspace_id=workspace_id,
#                                                                              project_id=0,
#                                                                              result_id=wtp_case_info["resultId"],
#                                                                              case_path='',
#                                                                              git_project_name='',
#                                                                              case_name='',
#                                                                              case_author='',
#                                                                              case_level=0,
#                                                                              case_type=CaseType.TESTNG,
#                                                                              error_info=f'{wtp_case_info} 执行异常,用例不存在请检查'
#                                                                              )}},
#                             case_function_total_count=case_function_count,
#                             case_function_success_count=0)
#             raise Exception("testng用例不存在: workspaceId: {}, caseId: {}".format(workspace_id, wtp_case_info['uiId']))
#         try:
#             case_execute_result = TestNGCaseRunner.executor(workspace_id=workspace_id, case_path=case_path,
#                                                             case_package=db_case.case_package,
#                                                             project_id=db_case.git_project_id,
#                                                             result_id=wtp_case_info["resultId"], env=env,
#                                                             commit_id=db_case.git_project_commit_id,
#                                                             branch_name=wtp_case_info.get('branchName', 'master'))
#             logger.info(f'{wtp_case_info} 执行结果: {case_execute_result}')
#
#             # 判断case执行结果
#             if case_execute_result['case_result']['case_result']['successful'] < 100:
#                 # case通过率小于100 说明存在失败case
#                 logger.error(f'{wtp_case_info} 存在失败case')
#                 send_job_result(case_job=wtp_case_info, result=0, case_execute_detail=case_execute_result)
#                 if fail_stop:
#                     # 失败时停止 结束后续case执行
#                     cancel_job(wtp_case_info_list[index + 1:])
#                     raise Exception(f'{wtp_case_info} 执行失败,失败时终止: {traceback.format_exc()}')
#             else:
#                 # case通过率等于100 说明全部执行成功
#                 logger.info(f'{wtp_case_info} case全部执行成功')
#                 send_job_result(case_job=wtp_case_info, result=1, case_execute_detail=case_execute_result)
#                 continue
#
#         except SoftTimeLimitExceeded:
#             # case执行时间超时
#             logger.error(
#                 f'{wtp_case_info} 执行超时: {traceback.format_exc()}')
#             send_job_result(case_job=wtp_case_info,
#                             result=0,
#                             case_execute_detail={"case_result": {
#                                 "case_report": create_error_html_report_file(workspace_id=workspace_id,
#                                                                              project_id=db_case.git_project_id,
#                                                                              result_id=wtp_case_info["resultId"],
#                                                                              case_path=db_case.case_path,
#                                                                              git_project_name=db_case.git_project_name,
#                                                                              case_name=db_case.case_name,
#                                                                              case_author=db_case.case_author,
#                                                                              case_level=db_case.case_level,
#                                                                              case_type=db_case.case_type,
#                                                                              error_info=f'{wtp_case_info} 执行执行超时: {traceback.format_exc()}'
#                                                                              )},
#                                 "case_log": f'{wtp_case_info} 执行超时: {traceback.format_exc()}'},
#                             case_function_total_count=case_function_count,
#                             case_function_success_count=0
#                             )
#             cancel_job(wtp_case_info_list[index + 1:])
#             raise Exception(f'{wtp_case_info} 执行超时: {traceback.format_exc()}')
#
#         except Exception:
#             # case执行异常
#             logger.error(f'{wtp_case_info} 执行异常: {traceback.format_exc()}')
#             send_job_result(case_job=wtp_case_info,
#                             result=0,
#                             case_execute_detail={"case_result": {
#                                 "case_report": create_error_html_report_file(workspace_id=workspace_id,
#                                                                              project_id=db_case.git_project_id,
#                                                                              result_id=wtp_case_info["resultId"],
#                                                                              case_path=db_case.case_path,
#                                                                              git_project_name=db_case.git_project_name,
#                                                                              case_name=db_case.case_name,
#                                                                              case_author=db_case.case_author,
#                                                                              case_level=db_case.case_level,
#                                                                              case_type=db_case.case_type,
#                                                                              error_info=f'{wtp_case_info} 执行异常,失败时终止: {traceback.format_exc()}'
#                                                                              )},
#                                 "case_log": f'{wtp_case_info} 执行异常,失败时终止: {traceback.format_exc()}'},
#                             case_function_total_count=case_function_count,
#                             case_function_success_count=0
#                             )
#             if fail_stop:
#                 # 失败时停止 结束后续case执行
#                 cancel_job(wtp_case_info_list[index + 1:])
#                 raise Exception(f'{wtp_case_info} 执行异常,失败时终止: {traceback.format_exc()}')
#             else:
#                 continue
#     return f'计划: {plan_id} 执行完成'
#
#
# @celery_app.task(name="testng_case_job_executor", soft_time_limit=60 * 60,
#                  time_limit=60 * 60 + 200)  # testng并行任务超时时间为1小时
# def testng_case_job_executor(workspace_id: int, plan_id: int, plan_result_id: int, wtp_case_info: dict, env: int):
#     """
#     【case job执行处理器】
#     :param workspace_id: wtp用例库id
#     :param plan_id: 计划id
#     :param plan_result_id: ==taskId 预生成的任务id
#     :param env: 环境
#     :param wtp_case_info: case信息
#     :return:
#     """
#
#     def send_job_result(case_job: dict, result: int, case_execute_detail: dict,
#                         case_function_total_count: int = 0,
#                         case_function_success_count: int = 0):
#         """
#         发送成功任务
#         :param case_function_success_count: 脚本中case方法通过数
#         :param case_function_total_count: 脚本中case方法总数
#         :param case_job: 执行成功的case信息
#         :param result: 1：成功 0：失败
#         :param case_execute_detail: case执行结果详情
#         :return:
#         """
#         logger.info(f'{case_job}case执行完成')
#         wtp_api.send_result(workspace_id=workspace_id,
#                             plan_id=plan_id,
#                             plan_result_id=plan_result_id,
#                             case_id=case_job["caseId"],
#                             snapshot_id=case_job.get("snapshotId"),
#                             snapshot_type=case_job.get("snapshotType"),
#                             result_id=case_job["resultId"],
#                             result=result,
#                             ui_log_json=json.dumps(case_execute_detail['case_result'], ensure_ascii=False),
#                             # log=case_execute_detail['case_log'],
#                             log="",
#                             case_function_total_count=case_function_total_count,
#                             case_function_success_count=case_function_success_count)
#
#     # 执行case job
#     db_case = TestNGCaseModel.objects.filter(workspace_id=workspace_id, case_uuid=wtp_case_info['uiId']).first()
#     if db_case:
#         # 数据库存在case信息 并获取case路径以及case方法总数
#         case_path = db_case.case_path
#         if db_case.case_function_list:
#             # 数据库存在case functions信息 直接从数据库获取
#             case_function_count = len(db_case.case_function_list)
#         else:
#             # 数据库不存在case functions信息 从gitlab获取 并保存到数据库
#             case_function_count = get_script_case_function_count_and_update(db_case_info=db_case,
#                                                                             uiId=wtp_case_info['uiId'],
#                                                                             git_commit_id=db_case.git_project_commit_id)
#     else:
#         # 数据库不存在case信息 从gitlab获取 不保存到数据库
#         case_function_count = get_script_case_function_count_and_update(uiId=wtp_case_info['uiId'],
#                                                                         git_commit_id=db_case.git_project_commit_id)
#         send_job_result(case_job=wtp_case_info,
#                         result=0,
#                         case_execute_detail={"case_result": {
#                             "case_report": create_error_html_report_file(workspace_id=workspace_id,
#                                                                          project_id=0,
#                                                                          result_id=wtp_case_info["resultId"],
#                                                                          case_path='',
#                                                                          git_project_name='',
#                                                                          case_name='',
#                                                                          case_author='',
#                                                                          case_level=0,
#                                                                          case_type=CaseType.TESTNG,
#                                                                          error_info=f'{wtp_case_info} 执行异常,用例不存在请检查'
#                                                                          )}},
#                         case_function_total_count=case_function_count,
#                         case_function_success_count=0)
#         raise Exception("testng用例不存在: workspaceId: {}, caseId: {}".format(workspace_id, wtp_case_info['uiId']))
#     try:
#         case_execute_result = TestNGCaseRunner.executor(workspace_id=workspace_id, case_path=case_path,
#                                                         case_package=db_case.case_package,
#                                                         project_id=db_case.git_project_id,
#                                                         result_id=wtp_case_info["resultId"], env=env,
#                                                         commit_id=db_case.git_project_commit_id,
#                                                         branch_name=wtp_case_info.get('branchName', 'master'))
#         logger.info(f'{wtp_case_info} 执行结果: {case_execute_result}')
#
#         # 判断case执行结果
#         if case_execute_result['case_result']['case_result']['successful'] < 100:
#             # case通过率小于100 说明存在失败case
#             logger.error(f'{wtp_case_info} 存在失败case')
#             send_job_result(case_job=wtp_case_info, result=0, case_execute_detail=case_execute_result,
#                             case_function_total_count=case_execute_result['case_result']['case_result']['total'],
#                             case_function_success_count=case_execute_result['case_result']['case_result']['passed'])
#             return f'存在失败case: {case_execute_result}'
#         else:
#             # case通过率等于100 说明全部执行成功
#             logger.info(f'{wtp_case_info} case全部执行成功')
#             send_job_result(case_job=wtp_case_info, result=1, case_execute_detail=case_execute_result,
#                             case_function_total_count=case_execute_result['case_result']['case_result']['total'],
#                             case_function_success_count=case_execute_result['case_result']['case_result']['passed'])
#             return f'case全部执行成功: {case_execute_result}'
#
#     except SoftTimeLimitExceeded:
#         # case执行时间超时
#         logger.error(
#             f'{wtp_case_info} 执行超时: {traceback.format_exc()}')
#         send_job_result(case_job=wtp_case_info,
#                         result=0,
#                         case_execute_detail={"case_result": {
#                             "case_report": create_error_html_report_file(workspace_id=workspace_id,
#                                                                          project_id=db_case.git_project_id,
#                                                                          result_id=wtp_case_info["resultId"],
#                                                                          case_path=db_case.case_path,
#                                                                          git_project_name=db_case.git_project_name,
#                                                                          case_name=db_case.case_name,
#                                                                          case_author=db_case.case_author,
#                                                                          case_level=db_case.case_level,
#                                                                          case_type=db_case.case_type,
#                                                                          error_info=f'{wtp_case_info} 执行超时: {traceback.format_exc()}'
#                                                                          )},
#                             "case_log": f'{wtp_case_info} 执行超时: {traceback.format_exc()}'},
#                         case_function_total_count=case_function_count,
#                         case_function_success_count=0
#                         )
#         raise Exception(f'{wtp_case_info} 执行超时: {traceback.format_exc()}')
#
#     except Exception:
#         # case执行异常
#         logger.error(f'{wtp_case_info} 执行异常: {traceback.format_exc()}')
#         send_job_result(case_job=wtp_case_info,
#                         result=0,
#                         case_execute_detail={"case_result": {
#                             "case_report": create_error_html_report_file(workspace_id=workspace_id,
#                                                                          project_id=db_case.git_project_id,
#                                                                          result_id=wtp_case_info["resultId"],
#                                                                          case_path=db_case.case_path,
#                                                                          git_project_name=db_case.git_project_name,
#                                                                          case_name=db_case.case_name,
#                                                                          case_author=db_case.case_author,
#                                                                          case_level=db_case.case_level,
#                                                                          case_type=db_case.case_type,
#                                                                          error_info=f'{wtp_case_info} 执行异常,失败时终止: {traceback.format_exc()}'
#                                                                          )},
#                             "case_log": f'{wtp_case_info} 执行异常: {traceback.format_exc()}'},
#                         case_function_total_count=case_function_count,
#                         case_function_success_count=0)
#         raise Exception(f'{wtp_case_info} 执行异常: {traceback.format_exc()}')
