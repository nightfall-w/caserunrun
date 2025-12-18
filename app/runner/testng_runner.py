"""
@FileName：runner.py
@Description：testng case的运行管理器
@Author：baojun.wang
@Time：2024/1/15 14:50
"""
import os
import subprocess
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime

import pytz
from funboost.utils.func_timeout.exceptions import FunctionTimedOut

from app.case_handler.case_parser import GitCaseParser
from app.case_handler.models import TestNGCaseModel
from app.case_source.models import CaseSourceRelationModel
from app.core.config import REPORT_URL, REPORT_ROOT
from app.core.database import get_sync_db
from app.runner.pytest_runner import sync_last_git_project_to_local, create_error_html_report_file, cleanup_processes
from app.testplan.models import CaseType, JobStatus
from app.virtual_env.models import JavaEnvModel
from utils.custom_logging import logger


class TestNGCaseRunner:
    """
    【testng case的运行管理器】

    负责TestNG类型测试用例的执行、资源清理、结果解析与报告生成。
    """

    @classmethod
    def executor(cls, testplan_id: int, task_id: int, job_id: int, workspace_id: int, case_path: str, case_name: str,
                 case_package: str, project_id: int, case_uuid: str, env: int, branch_name):
        """
        执行TestNG类型的测试用例，并返回执行结果和日志信息。

        :param testplan_id: 任务计划id
        :param task_id: 任务id
        :param job_id: 工作id
        :param workspace_id: 用例库id
        :param case_path: case脚本路径
        :param case_package: case包
        :param case_uuid: case uuid
        :param case_name: case脚本名称
        :param project_id: 项目id
        :param env: 执行环境
        :param branch_name: 分支名称
        :return: dict，包含测试结果统计信息、详细执行信息和报告地址
        """
        _processes = []  # 进程列表

        # 同步Git项目到本地指定commit_id版本
        git_project_path = sync_last_git_project_to_local(workspace_id=workspace_id, project_id=project_id,
                                                          case_path=case_path, branch_name=branch_name)

        # 获取python虚拟环境与解释器路径
        db = next(get_sync_db())
        venv_id = db.query(CaseSourceRelationModel).filter(CaseSourceRelationModel.workspace_id == workspace_id,
                                                           CaseSourceRelationModel.case_source_value[
                                                               "projectId"] == project_id).first().venv_id
        venv_info = db.query(JavaEnvModel).filter(JavaEnvModel.id == venv_id).first()

        if not venv_info or not venv_info.maven_setting_path:
            raise Exception(f'请先配置用例源的Java虚拟环境,venv_id-{project_id}不存在')

        mvn = "mvn"
        xml_name = 'testng-results.xml'
        report_name = case_path.split('/')[-1].split('.')[0] + '.html'

        # case报告文件存放路径预先创建
        report_dir = os.path.join(
            REPORT_ROOT, str(workspace_id), str(testplan_id), str(task_id), str(job_id))
        report_html_path = os.path.join(report_dir, report_name)
        report_xml_path = os.path.join(report_dir, xml_name)
        report_url = os.path.join(REPORT_URL, str(workspace_id), str(testplan_id), str(task_id), str(job_id),
                                  report_name)

        try:
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
        except FileExistsError:
            pass

        case_key = f"{workspace_id}_{project_id}_{testplan_id}_{task_id}_{job_id}_{case_path}"
        try:
            # 构造case执行指令
            cmd = f'{mvn} test -Dtest={case_package} -DreportsDirectory={report_dir} -Denv={env}'
            logger.info(f"testng case开始运行:{case_key}, 执行指令:{cmd}")

            # 开始执行case
            p = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, cwd=git_project_path)

            _processes.append(p)

            out, err = p.communicate(timeout=60 * 60 * 2)
            read_data = out.decode("utf-8", "ignore")
            error_data = err.decode("utf-8", "ignore")

            # logger.info(f"case:{case_key} 执行结果:{read_data}")
            logger.info(f"case:{case_key} 执行错误:{error_data}")

            # 解析case执行结果
            logger.info(
                f"case:{case_key} 期望生成xml报告地址:{report_xml_path}")
            if os.path.exists(os.path.join(report_xml_path)):
                # 存在xml格式的报告文件
                logger.info(f'case:{case_key} xml报告地址存在')

                # 解析xml报告 并统计case运行结果（通过率）
                root = ET.parse(os.path.join(report_xml_path))
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

                db_case_info = db.query(TestNGCaseModel).filter(
                    TestNGCaseModel.case_uuid == case_uuid).first()
                report_url = create_error_html_report_file(workspace_id=workspace_id,
                                                           case_path=case_path,
                                                           git_project_name=db_case_info.git_project_name,
                                                           case_type=CaseType.TESTNG, case_name=db_case_info.case_name,
                                                           case_level=db_case_info.case_level,
                                                           case_author=db_case_info.case_author,
                                                           result=JobStatus.FAILED,
                                                           report_url=report_url,
                                                           report_path=report_html_path,
                                                           error_info=f"case运行异常，未能生成详细测试报告: {read_data}")
            return {"case_result": case_result, "case_report": report_url}
        except FunctionTimedOut as e:
            logger.error(f"case:{case_key}执行超时: {traceback.format_exc()}")
            raise e
        except Exception:
            # case执行异常
            logger.error(f"case:{case_key}执行异常: {traceback.format_exc()}")
            raise Exception(traceback.format_exc())
        finally:
            cleanup_processes(_processes)
