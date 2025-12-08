"""
@FileName：runner.py
@Description：testng case的运行管理器
@Author：baojun.wang
@Time：2024/1/15 14:50
"""
import os
import subprocess
import time
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime

import psutil
import pytz
from celery.exceptions import SoftTimeLimitExceeded

from app.case_handler.case_parser import GitCaseParser
from app.case_handler.models import TestNGCaseModel
from app.runner.pytest_runner import sync_last_git_project_to_local, terminate_process, create_error_html_report_file
from utils.custom_logging import logger
from app.core.config import MEDIA_ROOT, REPORT_URL

from app.testplan.models import CaseType


class TestNGCaseRunner:
    """
    【testng case的运行管理器】

    负责TestNG类型测试用例的执行、资源清理、结果解析与报告生成。
    """

    @classmethod
    def executor(cls, workspace_id: int, case_path: str, case_package: str, project_id: int, result_id: int, env: int,
                 commit_id: str, branch_name="master"):
        """
        执行TestNG类型的测试用例，并返回执行结果和日志信息。

        :param workspace_id: 用例库ID，用于标识测试用例所属的用例库
        :param case_path: 测试用例文件路径（相对于项目根目录）
        :param case_package: 测试用例模块名，用于指定Maven执行的测试类
        :param project_id: 项目ID，用于标识测试用例所属的Git项目
        :param result_id: 测试结果唯一标识，用于生成报告路径
        :param env: 执行环境标识，用于传递给测试用例运行时环境参数
        :param commit_id: Git提交ID，用于拉取指定版本的代码
        :param branch_name: Git分支名称，默认为master，用于拉取指定分支代码
        :return: dict，包含测试结果统计信息、详细执行信息和报告地址
        """

        # 同步Git项目到本地指定commit_id版本
        git_project_path = sync_last_git_project_to_local(workspace_id=workspace_id, project_id=project_id,
                                                          case_path=case_path,
                                                          branch_name=branch_name, commit_id=commit_id)

        mvn = 'mvn'  # maven命令的路径
        # case报告文件名称预先生成
        xml_name = 'testng-results.xml'

        # case报告文件存放路径预先创建
        report_path = os.path.join(
            MEDIA_ROOT, 'html-report', str(workspace_id), str(project_id), str(result_id))
        try:
            if not os.path.exists(report_path):
                os.makedirs(report_path)
        except FileExistsError:
            pass

        case_key = f"{workspace_id}_{project_id}_{result_id}_{case_path}"
        try:
            # 构造case执行指令
            cmd = f'{mvn} test -Dtest={case_package} -DreportsDirectory={report_path} -Denv={env}'
            logger.info(f"testng case开始运行:{case_key}, 执行指令:{cmd}")

            # 开始执行case
            p = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, cwd=git_project_path)

            # 等待case完全运行起来 浏览器，chromedriver等资源加载成功
            time.sleep(8)
            # 获取父进程的子进程列表
            child_processes = psutil.Process(p.pid).children(recursive=True)
            # 遍历子进程列表
            child_pid_list = []
            for child in child_processes:
                # 打印子进程的PID
                logger.info(f"pid: {p.pid}的子进程的PID: {child.pid}")
                child_pid_list.append(child.pid)

            out, err = p.communicate()
            read_data = out.decode("utf-8", "ignore")
            logger.info(f"case:{case_key} 执行结果:{read_data}")

            # 清理case占用的浏览器资源
            for child_pid in child_pid_list:
                terminate_process(child_pid)

            # 解析case执行结果
            logger.info(
                f"case:{case_key} 期望生成xml报告地址:{os.path.join(report_path, xml_name)}")
            if os.path.exists(os.path.join(report_path, xml_name)):
                # 存在xml格式的报告文件
                logger.info(f'case:{case_key} xml报告地址存在')

                # 设定默认值
                total, passed, failed, skipped, successful = 0, 0, 0, 0, 0

                # 解析xml报告 并统计case运行结果（通过率）
                root = ET.parse(os.path.join(report_path, xml_name))
                root = root.getroot()

                # 提取total、passed、skipped属性值
                total = int(root.attrib['total'])
                passed = int(root.attrib['passed'])
                skipped = int(root.attrib['skipped'])
                failed = int(root.attrib['failed'])
                ignored = int(root.attrib['ignored'])

                successful = round(passed / total * 100, 1)
                case_result = {"total": total, "passed": passed, "failed": failed, "skipped": skipped,
                               "ignored": ignored, "successful": successful}
                logger.info(f'case运行结果统计: {case_result}')

                # 解析xml报告 获取case运行结果详情（case function执行详情）
                case_detail = []
                cst = pytz.timezone('Asia/Shanghai')  # 定义时区
                class_element = root.find(".//class")
                class_name = class_element.attrib['name']
                for test_method in class_element.findall("test-method"):
                    method_name = test_method.attrib['name']
                    start_time = datetime.strptime(test_method.attrib['started-at'], '%Y-%m-%dT%H:%M:%SZ').astimezone(
                        cst).strftime('%Y-%m-%d %H:%M:%S')
                    end_time = datetime.strptime(test_method.attrib['finished-at'], '%Y-%m-%dT%H:%M:%SZ').astimezone(
                        cst).strftime('%Y-%m-%d %H:%M:%S')
                    duration_ms = f'{round(int(test_method.attrib["duration-ms"]) / 1000, 1)}s'  # 毫秒转换为秒
                    status = test_method.attrib['status']

                    result = 'passed'
                    case_msg = ""
                    if status == "FAIL":
                        result = 'failed'
                        reporter_output = test_method.find('.//failure')
                        if reporter_output is not None:
                            case_msg = reporter_output.text

                    case_detail.append(
                        {"classname": class_name, "file_path": case_path,
                         "case_name": method_name, "case_time": duration_ms,
                         "start_time": start_time, "end_time": end_time,
                         "result": result, "case_msg": case_msg}
                    )
            else:
                # 不存在xml格式的报告文件
                logger.info(f'case:{case_key} xml报告地址不存在')
                case_result = {
                    "total": len(GitCaseParser.get_testng_test_functions_by_filepath(
                        filename=os.path.join(git_project_path, case_path))),
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "ignored": 0,
                    "successful": 0}
                case_detail = []
                db_case_info = TestNGCaseModel.objects.filter(workspace_id=workspace_id, case_path=case_path,
                                                              git_project_id=project_id).first()
                create_error_html_report_file(workspace_id=workspace_id, project_id=project_id, result_id=result_id,
                                              case_path=case_path, git_project_name=db_case_info.git_project_name,
                                              case_type=CaseType.TESTNG, case_name=db_case_info.case_name,
                                              case_level=db_case_info.case_level,
                                              case_author=db_case_info.case_author,
                                              error_info=f"case运行异常，未能生成详细测试报告: {read_data}")
            return {"case_result": {"case_result": case_result, "case_detail": case_detail,
                                    "case_report": REPORT_DOMAIN + os.path.join(
                                        MEDIA_URL, 'html-report', str(workspace_id), str(project_id), str(result_id),
                                        'error.html' if os.path.exists(
                                            os.path.join(report_path, 'error.html')) else xml_name)},
                    "case_log": read_data}
        except SoftTimeLimitExceeded:
            # case执行超时
            raise SoftTimeLimitExceeded
        except Exception:
            # case执行异常
            logger.error(f"case:{case_key}执行异常: {traceback.format_exc()}")
            raise Exception(traceback.format_exc())
