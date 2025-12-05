# -*- coding:utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import random
import re
import time
import traceback

from celery.exceptions import SoftTimeLimitExceeded

from app.case_handler.case_enum import CaseType
from app.case_handler.case_parser import GitCaseParser
from app.case_handler.case_sync import InitGitCase
from app.case_handler.gitlab_tool import GitlabAPI
from app.case_handler.models import PytestCaseModel, TestNGCaseModel
from app.case_source.models import CaseSourceRelationModel
from celery_tasks import celery_app
from app.runner.runner import PytestCaseRunner, create_error_html_report_file
from utils.custom_logging import logger


def get_script_case_function_count_and_update(uiId: str, git_commit_id: str, db_case_info=None):
    """
    从gitlab最新提交中获取脚本中case方法总数
    :param db_case_info: 数据库存在的case信息
    :param git_commit_id: 用例提交id
    :param uiId: 用例uid
    :return:
    """
    # 数据库不存在case functions信息 从gitlab获取 并保存到数据库
    case_info = GitCaseParser.parse_case_uuid(case_uuid=uiId)
    gitlab_client = GitlabAPI()
    case_content = gitlab_client.get_content(project_id=case_info['git_project_id'],
                                             file_path=case_info['case_path'],
                                             ref=git_commit_id)
    if case_info['case_type'] == CaseType.Pytest.value:
        case_functions_list = GitCaseParser.get_python_test_functions_by_context(case_content)
    elif case_info['case_type'] == CaseType.TestNG.value:
        case_functions_list = GitCaseParser.get_testng_test_functions_by_context(case_content)
    else:
        case_functions_list = []
    if db_case_info:
        db_case_info.refresh_from_db()
        db_case_info.case_function_list = case_functions_list
        db_case_info.save()
    return len(case_functions_list)


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
    await InitGitCase(case_source_relation=case_source_relation).sync()


@celery_app.task(name="pytest_case_task_executor", soft_time_limit=60 * 90,
                 time_limit=60 * 90 + 200)  # pytest串行任务超时时间为90分钟
def pytest_case_task_executor(workspace_id: int, plan_id: int, plan_result_id: int, wtp_case_info_list: list,
                              fail_stop: int,
                              env: int):
    """
    【case计划串行执行器】
    :param workspace_id: wtp用例库id
    :param plan_id: 计划id
    :param plan_result_id: ==taskId 预生成的任务id
    :param env: 环境
    :param wtp_case_info_list: case列表
    :param fail_stop: 失败时停止
    """

    def cancel_job(to_be_cancelled_job_list: list):
        """
        取消job
        :param to_be_cancelled_job_list: 待取消的任务列表
        :return:
        """
        for case_job in to_be_cancelled_job_list:
            logger.info(f'取消任务: {case_job}')

    def send_job_result(case_job: dict, result: int, case_execute_detail: dict,
                        case_function_total_count: int = 0,
                        case_function_success_count: int = 0):
        """
        发送成功任务
        :param case_function_success_count: 脚本中case方法通过数
        :param case_function_total_count: 脚本中case方法总数
        :param case_job: 执行成功的case信息
        :param result: 1：成功 0：失败 2：取消(终止)
        :param case_execute_detail: case执行结果详情
        :return:
        """
        logger.info(f'{case_job}case执行完成')
        wtp_api.send_result(workspace_id=workspace_id,
                            plan_id=plan_id,
                            plan_result_id=plan_result_id,
                            case_id=case_job["caseId"],
                            snapshot_id=case_job.get("snapshotId"),
                            snapshot_type=case_job.get("snapshotType"),
                            result_id=case_job["resultId"], result=result,
                            ui_log_json=json.dumps(case_execute_detail['case_result'], ensure_ascii=False),
                            # log=case_execute_detail['case_log'],
                            log="",
                            case_function_total_count=case_function_total_count,
                            case_function_success_count=case_function_success_count)

    for index, wtp_case_info in enumerate(wtp_case_info_list):
        logger.info(f'准备执行串行case:{wtp_case_info}')
        db_case = PytestCaseModel.objects.filter(workspace_id=workspace_id, case_uuid=wtp_case_info['uiId']).first()
        if db_case:
            # 数据库存在case信息 并获取case路径以及case方法总数
            case_path = db_case.case_path
            if db_case.case_function_list:
                # 数据库存在case functions信息 直接从数据库获取
                case_function_count = len(db_case.case_function_list)
            else:
                # 数据库不存在case functions信息 从gitlab获取 并保存到数据库
                case_function_count = get_script_case_function_count_and_update(db_case_info=db_case,
                                                                                uiId=wtp_case_info['uiId'],
                                                                                git_commit_id=db_case.git_project_commit_id)
        else:
            # 数据库不存在case信息 从gitlab获取 不保存到数据库
            case_function_count = get_script_case_function_count_and_update(uiId=wtp_case_info['uiId'],
                                                                            git_commit_id=db_case.git_project_commit_id)
            send_job_result(case_job=wtp_case_info,
                            result=0,
                            case_execute_detail={"case_result": {
                                "case_report": create_error_html_report_file(workspace_id=workspace_id,
                                                                             project_id=0,
                                                                             result_id=wtp_case_info["resultId"],
                                                                             case_path='',
                                                                             git_project_name='',
                                                                             case_name='',
                                                                             case_author='',
                                                                             case_level=0,
                                                                             case_type=CaseType.Pytest.value,
                                                                             error_info=f'{wtp_case_info} 执行异常,用例不存在请检查'
                                                                             )}},
                            case_function_total_count=case_function_count,
                            case_function_success_count=0)
            raise Exception("pytest用例不存在: workspaceId: {}, caseId: {}".format(workspace_id, wtp_case_info['uiId']))
        try:
            case_execute_result = PytestCaseRunner.executor(workspace_id=workspace_id, case_path=case_path,
                                                            project_id=db_case.git_project_id,
                                                            result_id=wtp_case_info["resultId"], env=env,
                                                            commit_id=db_case.git_project_commit_id,
                                                            branch_name=wtp_case_info.get('branchName', 'master'))
            logger.info(f'{wtp_case_info} 执行结果: {case_execute_result}')

            # 判断case执行结果
            if case_execute_result['case_result']['case_result']['successful'] < 100:
                # case通过率小于100 说明存在失败case
                logger.error(f'{wtp_case_info} 存在失败case')
                send_job_result(case_job=wtp_case_info, result=0, case_execute_detail=case_execute_result,
                                case_function_total_count=case_execute_result['case_result']['case_result']['total'],
                                case_function_success_count=case_execute_result['case_result']['case_result']['passed'])
                if fail_stop:
                    # 失败时停止 结束后续case执行
                    cancel_job(wtp_case_info_list[index + 1:])
                    raise Exception(f'{wtp_case_info} 执行失败,失败时终止: {traceback.format_exc()}')
            else:
                # case通过率等于100 说明全部执行成功
                logger.info(f'{wtp_case_info} case全部执行成功')
                send_job_result(case_job=wtp_case_info, result=1, case_execute_detail=case_execute_result,
                                case_function_total_count=case_execute_result['case_result']['case_result']['total'],
                                case_function_success_count=case_execute_result['case_result']['case_result']['passed'])
                continue

        except SoftTimeLimitExceeded:
            # case执行时间超时
            logger.error(
                f'{wtp_case_info} 执行超时: {traceback.format_exc()}')
            send_job_result(case_job=wtp_case_info,
                            result=0,
                            case_execute_detail={"case_result": {
                                "case_report": create_error_html_report_file(workspace_id=workspace_id,
                                                                             project_id=db_case.git_project_id,
                                                                             result_id=wtp_case_info["resultId"],
                                                                             case_path=db_case.case_path,
                                                                             git_project_name=db_case.git_project_name,
                                                                             case_name=db_case.case_name,
                                                                             case_author=db_case.case_author,
                                                                             case_level=db_case.case_level,
                                                                             case_type=db_case.case_type,
                                                                             error_info=f'{wtp_case_info} 执行超时: {traceback.format_exc()}'
                                                                             )},
                                "case_log": f'{wtp_case_info} 执行超时: {traceback.format_exc()}'},
                            case_function_total_count=case_function_count,
                            case_function_success_count=0
                            )
            cancel_job(wtp_case_info_list[index + 1:])
            raise Exception(f'{wtp_case_info} 执行超时: {traceback.format_exc()}')

        except Exception:
            # case执行异常
            logger.error(f'{wtp_case_info} 执行异常: {traceback.format_exc()}')
            send_job_result(case_job=wtp_case_info,
                            result=0,
                            case_execute_detail={"case_result": {
                                "case_report": create_error_html_report_file(workspace_id=workspace_id,
                                                                             project_id=db_case.git_project_id,
                                                                             result_id=wtp_case_info["resultId"],
                                                                             case_path=db_case.case_path,
                                                                             git_project_name=db_case.git_project_name,
                                                                             case_name=db_case.case_name,
                                                                             case_author=db_case.case_author,
                                                                             case_level=db_case.case_level,
                                                                             case_type=db_case.case_type,
                                                                             error_info=f'{wtp_case_info} 执行异常,失败时终止: {traceback.format_exc()}'
                                                                             )},
                                "case_log": f'{wtp_case_info} 执行异常,失败时终止: {traceback.format_exc()}'},
                            case_function_total_count=case_function_count,
                            case_function_success_count=0
                            )
            if fail_stop:
                # 失败时停止 结束后续case执行
                cancel_job(wtp_case_info_list[index + 1:])
                raise Exception(f'{wtp_case_info} 执行异常,失败时终止: {traceback.format_exc()}')
            else:
                continue
    return f'计划: {plan_id} 执行完成'


@celery_app.task(name="pytest_case_job_executor", soft_time_limit=60 * 60,
                 time_limit=60 * 60 + 200)  # pytest并行任务超时时间为1小时
def pytest_case_job_executor(workspace_id: int, plan_id: int, plan_result_id: int, wtp_case_info: dict, env: int):
    """
    【case job执行处理器】
    :param workspace_id: wtp用例库id
    :param plan_id: 计划id
    :param plan_result_id: ==taskId 预生成的任务id
    :param env: 环境
    :param wtp_case_info: case信息
    :return:
    """

    def send_job_result(case_job: dict, result: int, case_execute_detail: dict,
                        case_function_total_count: int = 0,
                        case_function_success_count: int = 0):
        """
        发送成功任务
        :param case_function_success_count: 脚本中case方法通过数
        :param case_function_total_count: 脚本中case方法总数
        :param case_job: 执行成功的case信息
        :param result: 1：成功 0：失败
        :param case_execute_detail: case执行结果详情
        :return:
        """
        logger.info(f'{case_job}case执行完成')

    # 执行case job
    db_case = PytestCaseModel.objects.filter(workspace_id=workspace_id, case_uuid=wtp_case_info['uiId']).first()
    if db_case:
        # 数据库存在case信息 并获取case路径以及case方法总数
        case_path = db_case.case_path
        if db_case.case_function_list:
            # 数据库存在case functions信息 直接从数据库获取
            case_function_count = len(db_case.case_function_list)
        else:
            # 数据库不存在case functions信息 从gitlab获取 并保存到数据库
            case_function_count = get_script_case_function_count_and_update(db_case_info=db_case,
                                                                            uiId=wtp_case_info['uiId'],
                                                                            git_commit_id=db_case.git_project_commit_id)
    else:
        # 数据库不存在case信息 从gitlab获取 不保存到数据库
        case_function_count = get_script_case_function_count_and_update(uiId=wtp_case_info['uiId'],
                                                                        git_commit_id=db_case.git_project_commit_id)
        send_job_result(case_job=wtp_case_info,
                        result=0,
                        case_execute_detail={"case_result": {
                            "case_report": create_error_html_report_file(workspace_id=workspace_id,
                                                                         project_id=0,
                                                                         result_id=wtp_case_info["resultId"],
                                                                         case_path='',
                                                                         git_project_name='',
                                                                         case_name='',
                                                                         case_author='',
                                                                         case_level=0,
                                                                         case_type=CaseType.Pytest.value,
                                                                         error_info=f'{wtp_case_info} 执行异常,用例不存在: {traceback.format_exc()}'
                                                                         )}},
                        case_function_total_count=case_function_count,
                        case_function_success_count=0)
        raise Exception("pytest用例不存在: workspaceId: {}, caseId: {}".format(workspace_id, wtp_case_info['uiId']))
    try:
        case_execute_result = PytestCaseRunner.executor(workspace_id=workspace_id, case_path=case_path,
                                                        project_id=db_case.git_project_id,
                                                        result_id=wtp_case_info["resultId"], env=env,
                                                        commit_id=db_case.git_project_commit_id,
                                                        branch_name=wtp_case_info.get('branchName', 'master'))
        logger.info(f'{wtp_case_info} 执行结果: {case_execute_result}')

        # 判断case执行结果
        if case_execute_result['case_result']['case_result']['successful'] < 100:
            # case通过率小于100 说明存在失败case
            logger.error(f'{wtp_case_info} 存在失败case')
            send_job_result(case_job=wtp_case_info, result=0, case_execute_detail=case_execute_result,
                            case_function_total_count=case_execute_result['case_result']['case_result']['total'],
                            case_function_success_count=case_execute_result['case_result']['case_result']['passed'])
            return f'存在失败case: {case_execute_result}'
        else:
            # case通过率等于100 说明全部执行成功
            logger.info(f'{wtp_case_info} case全部执行成功')
            send_job_result(case_job=wtp_case_info, result=1, case_execute_detail=case_execute_result,
                            case_function_total_count=case_execute_result['case_result']['case_result']['total'],
                            case_function_success_count=case_execute_result['case_result']['case_result']['passed'])
            return f'case全部执行成功: {case_execute_result}'

    except SoftTimeLimitExceeded:
        # case执行时间超时
        logger.error(
            f'{wtp_case_info} 执行超时: {traceback.format_exc()}')
        send_job_result(case_job=wtp_case_info,
                        result=0,
                        case_execute_detail={"case_result": {
                            "case_report": create_error_html_report_file(workspace_id=workspace_id,
                                                                         project_id=db_case.git_project_id,
                                                                         result_id=wtp_case_info["resultId"],
                                                                         case_path=db_case.case_path,
                                                                         git_project_name=db_case.git_project_name,
                                                                         case_name=db_case.case_name,
                                                                         case_author=db_case.case_author,
                                                                         case_level=db_case.case_level,
                                                                         case_type=db_case.case_type,
                                                                         error_info=f'{wtp_case_info} 执行超时: {traceback.format_exc()}'
                                                                         )},
                            "case_log": f'{wtp_case_info} 执行超时: {traceback.format_exc()}'},
                        case_function_total_count=case_function_count,
                        case_function_success_count=0
                        )
        raise Exception(f'{wtp_case_info} 执行超时: {traceback.format_exc()}')

    except Exception:
        # case执行异常
        logger.error(f'{wtp_case_info} 执行异常: {traceback.format_exc()}')
        send_job_result(case_job=wtp_case_info,
                        result=0,
                        case_execute_detail={"case_result": {
                            "case_report": create_error_html_report_file(workspace_id=workspace_id,
                                                                         project_id=db_case.git_project_id,
                                                                         result_id=wtp_case_info["resultId"],
                                                                         case_path=db_case.case_path,
                                                                         git_project_name=db_case.git_project_name,
                                                                         case_name=db_case.case_name,
                                                                         case_author=db_case.case_author,
                                                                         case_level=db_case.case_level,
                                                                         case_type=db_case.case_type,
                                                                         error_info=f'{wtp_case_info} 执行异常,失败时终止: {traceback.format_exc()}'
                                                                         )},
                            "case_log": f'{wtp_case_info} 执行异常,失败时终止: {traceback.format_exc()}'},
                        case_function_total_count=case_function_count,
                        case_function_success_count=0)
        raise Exception(f'{wtp_case_info} 执行异常: {traceback.format_exc()}')


@celery_app.task(name="testng_case_task_executor", soft_time_limit=60 * 90,
                 time_limit=60 * 90 + 200)  # testng串行任务超时时间为90分钟
def testng_case_task_executor(workspace_id: int, plan_id: int, plan_result_id: int, wtp_case_info_list: list,
                              fail_stop: int,
                              env: int):
    """
    【case计划串行执行器】
    :param workspace_id: wtp用例库id
    :param plan_id: 计划id
    :param plan_result_id: ==taskId 预生成的任务id
    :param env: 环境
    :param wtp_case_info_list: case列表
    :param fail_stop: 失败时停止
    """

    def cancel_job(to_be_cancelled_job_list: list):
        """
        取消job
        :param to_be_cancelled_job_list: 待取消的任务列表
        :return:
        """
        for case_job in to_be_cancelled_job_list:
            logger.info(f'取消任务: {case_job}')

    def send_job_result(case_job: dict, result: int, case_execute_detail: dict,
                        case_function_total_count: int = 0,
                        case_function_success_count: int = 0):
        """
        发送成功任务
        :param case_function_success_count: 脚本中case方法通过数
        :param case_function_total_count: 脚本中case方法总数
        :param case_job: 执行成功的case信息
        :param result: 1：成功 0：失败 2：取消(终止)
        :param case_execute_detail: case执行结果详情
        :return:
        """
        logger.info(f'{case_job}case执行完成')
        wtp_api.send_result(workspace_id=workspace_id,
                            plan_id=plan_id,
                            plan_result_id=plan_result_id,
                            case_id=case_job["caseId"],
                            snapshot_id=case_job.get("snapshotId"),
                            snapshot_type=case_job.get("snapshotType"),
                            result_id=case_job["resultId"], result=result,
                            ui_log_json=json.dumps(case_execute_detail['case_result'], ensure_ascii=False),
                            # log=case_execute_detail['case_log'],
                            log="",
                            case_function_total_count=case_function_total_count,
                            case_function_success_count=case_function_success_count)

    for index, wtp_case_info in enumerate(wtp_case_info_list):
        logger.info(f'准备执行串行case:{wtp_case_info}')
        db_case = TestNGCaseModel.objects.filter(workspace_id=workspace_id, case_uuid=wtp_case_info['uiId']).first()
        if db_case:
            # 数据库存在case信息 并获取case路径以及case方法总数
            case_path = db_case.case_path
            if db_case.case_function_list:
                # 数据库存在case functions信息 直接从数据库获取
                case_function_count = len(db_case.case_function_list)
            else:
                # 数据库不存在case functions信息 从gitlab获取 并保存到数据库
                case_function_count = get_script_case_function_count_and_update(db_case_info=db_case,
                                                                                uiId=wtp_case_info['uiId'],
                                                                                git_commit_id=db_case.git_project_commit_id)
        else:
            # 数据库不存在case信息 从gitlab获取 不保存到数据库
            case_function_count = get_script_case_function_count_and_update(uiId=wtp_case_info['uiId'],
                                                                            git_commit_id=db_case.git_project_commit_id)
            send_job_result(case_job=wtp_case_info,
                            result=0,
                            case_execute_detail={"case_result": {
                                "case_report": create_error_html_report_file(workspace_id=workspace_id,
                                                                             project_id=0,
                                                                             result_id=wtp_case_info["resultId"],
                                                                             case_path='',
                                                                             git_project_name='',
                                                                             case_name='',
                                                                             case_author='',
                                                                             case_level=0,
                                                                             case_type=CaseType.TestNG.value,
                                                                             error_info=f'{wtp_case_info} 执行异常,用例不存在请检查'
                                                                             )}},
                            case_function_total_count=case_function_count,
                            case_function_success_count=0)
            raise Exception("testng用例不存在: workspaceId: {}, caseId: {}".format(workspace_id, wtp_case_info['uiId']))
        try:
            case_execute_result = TestNGCaseRunner.executor(workspace_id=workspace_id, case_path=case_path,
                                                            case_package=db_case.case_package,
                                                            project_id=db_case.git_project_id,
                                                            result_id=wtp_case_info["resultId"], env=env,
                                                            commit_id=db_case.git_project_commit_id,
                                                            branch_name=wtp_case_info.get('branchName', 'master'))
            logger.info(f'{wtp_case_info} 执行结果: {case_execute_result}')

            # 判断case执行结果
            if case_execute_result['case_result']['case_result']['successful'] < 100:
                # case通过率小于100 说明存在失败case
                logger.error(f'{wtp_case_info} 存在失败case')
                send_job_result(case_job=wtp_case_info, result=0, case_execute_detail=case_execute_result)
                if fail_stop:
                    # 失败时停止 结束后续case执行
                    cancel_job(wtp_case_info_list[index + 1:])
                    raise Exception(f'{wtp_case_info} 执行失败,失败时终止: {traceback.format_exc()}')
            else:
                # case通过率等于100 说明全部执行成功
                logger.info(f'{wtp_case_info} case全部执行成功')
                send_job_result(case_job=wtp_case_info, result=1, case_execute_detail=case_execute_result)
                continue

        except SoftTimeLimitExceeded:
            # case执行时间超时
            logger.error(
                f'{wtp_case_info} 执行超时: {traceback.format_exc()}')
            send_job_result(case_job=wtp_case_info,
                            result=0,
                            case_execute_detail={"case_result": {
                                "case_report": create_error_html_report_file(workspace_id=workspace_id,
                                                                             project_id=db_case.git_project_id,
                                                                             result_id=wtp_case_info["resultId"],
                                                                             case_path=db_case.case_path,
                                                                             git_project_name=db_case.git_project_name,
                                                                             case_name=db_case.case_name,
                                                                             case_author=db_case.case_author,
                                                                             case_level=db_case.case_level,
                                                                             case_type=db_case.case_type,
                                                                             error_info=f'{wtp_case_info} 执行执行超时: {traceback.format_exc()}'
                                                                             )},
                                "case_log": f'{wtp_case_info} 执行超时: {traceback.format_exc()}'},
                            case_function_total_count=case_function_count,
                            case_function_success_count=0
                            )
            cancel_job(wtp_case_info_list[index + 1:])
            raise Exception(f'{wtp_case_info} 执行超时: {traceback.format_exc()}')

        except Exception:
            # case执行异常
            logger.error(f'{wtp_case_info} 执行异常: {traceback.format_exc()}')
            send_job_result(case_job=wtp_case_info,
                            result=0,
                            case_execute_detail={"case_result": {
                                "case_report": create_error_html_report_file(workspace_id=workspace_id,
                                                                             project_id=db_case.git_project_id,
                                                                             result_id=wtp_case_info["resultId"],
                                                                             case_path=db_case.case_path,
                                                                             git_project_name=db_case.git_project_name,
                                                                             case_name=db_case.case_name,
                                                                             case_author=db_case.case_author,
                                                                             case_level=db_case.case_level,
                                                                             case_type=db_case.case_type,
                                                                             error_info=f'{wtp_case_info} 执行异常,失败时终止: {traceback.format_exc()}'
                                                                             )},
                                "case_log": f'{wtp_case_info} 执行异常,失败时终止: {traceback.format_exc()}'},
                            case_function_total_count=case_function_count,
                            case_function_success_count=0
                            )
            if fail_stop:
                # 失败时停止 结束后续case执行
                cancel_job(wtp_case_info_list[index + 1:])
                raise Exception(f'{wtp_case_info} 执行异常,失败时终止: {traceback.format_exc()}')
            else:
                continue
    return f'计划: {plan_id} 执行完成'


@celery_app.task(name="testng_case_job_executor", soft_time_limit=60 * 60,
                 time_limit=60 * 60 + 200)  # testng并行任务超时时间为1小时
def testng_case_job_executor(workspace_id: int, plan_id: int, plan_result_id: int, wtp_case_info: dict, env: int):
    """
    【case job执行处理器】
    :param workspace_id: wtp用例库id
    :param plan_id: 计划id
    :param plan_result_id: ==taskId 预生成的任务id
    :param env: 环境
    :param wtp_case_info: case信息
    :return:
    """

    def send_job_result(case_job: dict, result: int, case_execute_detail: dict,
                        case_function_total_count: int = 0,
                        case_function_success_count: int = 0):
        """
        发送成功任务
        :param case_function_success_count: 脚本中case方法通过数
        :param case_function_total_count: 脚本中case方法总数
        :param case_job: 执行成功的case信息
        :param result: 1：成功 0：失败
        :param case_execute_detail: case执行结果详情
        :return:
        """
        logger.info(f'{case_job}case执行完成')
        wtp_api.send_result(workspace_id=workspace_id,
                            plan_id=plan_id,
                            plan_result_id=plan_result_id,
                            case_id=case_job["caseId"],
                            snapshot_id=case_job.get("snapshotId"),
                            snapshot_type=case_job.get("snapshotType"),
                            result_id=case_job["resultId"],
                            result=result,
                            ui_log_json=json.dumps(case_execute_detail['case_result'], ensure_ascii=False),
                            # log=case_execute_detail['case_log'],
                            log="",
                            case_function_total_count=case_function_total_count,
                            case_function_success_count=case_function_success_count)

    # 执行case job
    db_case = TestNGCaseModel.objects.filter(workspace_id=workspace_id, case_uuid=wtp_case_info['uiId']).first()
    if db_case:
        # 数据库存在case信息 并获取case路径以及case方法总数
        case_path = db_case.case_path
        if db_case.case_function_list:
            # 数据库存在case functions信息 直接从数据库获取
            case_function_count = len(db_case.case_function_list)
        else:
            # 数据库不存在case functions信息 从gitlab获取 并保存到数据库
            case_function_count = get_script_case_function_count_and_update(db_case_info=db_case,
                                                                            uiId=wtp_case_info['uiId'],
                                                                            git_commit_id=db_case.git_project_commit_id)
    else:
        # 数据库不存在case信息 从gitlab获取 不保存到数据库
        case_function_count = get_script_case_function_count_and_update(uiId=wtp_case_info['uiId'],
                                                                        git_commit_id=db_case.git_project_commit_id)
        send_job_result(case_job=wtp_case_info,
                        result=0,
                        case_execute_detail={"case_result": {
                            "case_report": create_error_html_report_file(workspace_id=workspace_id,
                                                                         project_id=0,
                                                                         result_id=wtp_case_info["resultId"],
                                                                         case_path='',
                                                                         git_project_name='',
                                                                         case_name='',
                                                                         case_author='',
                                                                         case_level=0,
                                                                         case_type=CaseType.TestNG.value,
                                                                         error_info=f'{wtp_case_info} 执行异常,用例不存在请检查'
                                                                         )}},
                        case_function_total_count=case_function_count,
                        case_function_success_count=0)
        raise Exception("testng用例不存在: workspaceId: {}, caseId: {}".format(workspace_id, wtp_case_info['uiId']))
    try:
        case_execute_result = TestNGCaseRunner.executor(workspace_id=workspace_id, case_path=case_path,
                                                        case_package=db_case.case_package,
                                                        project_id=db_case.git_project_id,
                                                        result_id=wtp_case_info["resultId"], env=env,
                                                        commit_id=db_case.git_project_commit_id,
                                                        branch_name=wtp_case_info.get('branchName', 'master'))
        logger.info(f'{wtp_case_info} 执行结果: {case_execute_result}')

        # 判断case执行结果
        if case_execute_result['case_result']['case_result']['successful'] < 100:
            # case通过率小于100 说明存在失败case
            logger.error(f'{wtp_case_info} 存在失败case')
            send_job_result(case_job=wtp_case_info, result=0, case_execute_detail=case_execute_result,
                            case_function_total_count=case_execute_result['case_result']['case_result']['total'],
                            case_function_success_count=case_execute_result['case_result']['case_result']['passed'])
            return f'存在失败case: {case_execute_result}'
        else:
            # case通过率等于100 说明全部执行成功
            logger.info(f'{wtp_case_info} case全部执行成功')
            send_job_result(case_job=wtp_case_info, result=1, case_execute_detail=case_execute_result,
                            case_function_total_count=case_execute_result['case_result']['case_result']['total'],
                            case_function_success_count=case_execute_result['case_result']['case_result']['passed'])
            return f'case全部执行成功: {case_execute_result}'

    except SoftTimeLimitExceeded:
        # case执行时间超时
        logger.error(
            f'{wtp_case_info} 执行超时: {traceback.format_exc()}')
        send_job_result(case_job=wtp_case_info,
                        result=0,
                        case_execute_detail={"case_result": {
                            "case_report": create_error_html_report_file(workspace_id=workspace_id,
                                                                         project_id=db_case.git_project_id,
                                                                         result_id=wtp_case_info["resultId"],
                                                                         case_path=db_case.case_path,
                                                                         git_project_name=db_case.git_project_name,
                                                                         case_name=db_case.case_name,
                                                                         case_author=db_case.case_author,
                                                                         case_level=db_case.case_level,
                                                                         case_type=db_case.case_type,
                                                                         error_info=f'{wtp_case_info} 执行超时: {traceback.format_exc()}'
                                                                         )},
                            "case_log": f'{wtp_case_info} 执行超时: {traceback.format_exc()}'},
                        case_function_total_count=case_function_count,
                        case_function_success_count=0
                        )
        raise Exception(f'{wtp_case_info} 执行超时: {traceback.format_exc()}')

    except Exception:
        # case执行异常
        logger.error(f'{wtp_case_info} 执行异常: {traceback.format_exc()}')
        send_job_result(case_job=wtp_case_info,
                        result=0,
                        case_execute_detail={"case_result": {
                            "case_report": create_error_html_report_file(workspace_id=workspace_id,
                                                                         project_id=db_case.git_project_id,
                                                                         result_id=wtp_case_info["resultId"],
                                                                         case_path=db_case.case_path,
                                                                         git_project_name=db_case.git_project_name,
                                                                         case_name=db_case.case_name,
                                                                         case_author=db_case.case_author,
                                                                         case_level=db_case.case_level,
                                                                         case_type=db_case.case_type,
                                                                         error_info=f'{wtp_case_info} 执行异常,失败时终止: {traceback.format_exc()}'
                                                                         )},
                            "case_log": f'{wtp_case_info} 执行异常: {traceback.format_exc()}'},
                        case_function_total_count=case_function_count,
                        case_function_success_count=0)
        raise Exception(f'{wtp_case_info} 执行异常: {traceback.format_exc()}')
