"""
@FileName：runner.py
@Description：执行器
@Author：baojun.wang
@Time：2023/11/11 19:49
"""
import os
import subprocess
import time
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime

import psutil
from funboost.utils.dependency_packages.mongomq.mongomq import JobStatus
from funboost.utils.func_timeout.exceptions import FunctionTimedOut
from jinja2 import Environment, FileSystemLoader

from app.case_handler.case_parser import GitCaseParser
from app.case_handler.gitlab_tool import GitlabAPI
from app.case_handler.models import PytestCaseModel
from app.case_source.models import CaseSourceRelationModel
from app.core.config import REPORT_URL, CASE_HOUSE_ROOT, REPORT_ROOT
from app.core.database import get_sync_db
from app.setting.controller import get_setting_crud
from app.testplan.models import CaseType
from app.virtual_env.models import PythonVirtualEnvModel
from utils.custom_logging import logger

setting_curd = get_setting_crud(next(get_sync_db()))


def create_error_html_report_file(workspace_id: int, git_project_name: str, case_type: str,
                                  case_path: str, case_name: str, case_author: str, case_level: int, result: str,
                                  error_info: str, report_path: str, report_url: str):
    """
    使用Jinja2渲染错误HTML报告文件
    :param workspace_id: 用例库ID
    :param git_project_name: 用例所属的gitlab项目名称
    :param case_type: 用例类型
    :param case_path: 用脚本路径
    :param case_name: 用例名称
    :param case_author: 用例作者
    :param case_level: 用例等级
    :param result: 运行结果
    :param error_info: 错误信息
    :param report_path: 报告路径
    :param report_url: 报告url
    :return: case报告的url
    """
    try:
        # 创建Jinja2环境
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'universal_test_report', 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))

        # 加载模板
        template = env.get_template('error_template.html')

        # 准备渲染数据
        data = {
            'workspace_id': workspace_id,
            'git_project_name': git_project_name,
            'case_type': case_type,
            'case_path': case_path,
            'case_name': case_name,
            'case_author': case_author,
            'case_level': case_level,
            'result': result,
            'error_info': error_info,
            'datetime': datetime
        }

        # 获取用例报告路径的上级目录
        case_report_dir = os.path.dirname(report_path)
        if not os.path.exists(case_report_dir):
            os.makedirs(case_report_dir)

        # 渲染模板并写入文件
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(template.render(data))

        return report_url
    except Exception as e:
        logger.error(f"创建错误报告文件时出错：{e}")
        logger.error(traceback.format_exc())
        return None


def terminate_process(pid):
    """
    终止进程
    :param pid: 待终止进程的pid
    :return:
    """
    try:
        process = psutil.Process(pid)
        process.terminate()
        logger.info(f"进程 {pid} 已成功终止。")
    except psutil.NoSuchProcess:
        logger.info(f"找不到进程 {pid}。")
    except Exception as e:
        logger.info(f"终止进程 {pid} 失败：{e}。")


def get_git_token(token_type: str, workspace_id: int) -> tuple[str, str]:
    """
    获取gitlab的token
    :return:
    """
    gitlab_url, token = setting_curd.get_gitlab_credentials(token_type=token_type, workspace_id=workspace_id)
    if gitlab_url and token:
        return gitlab_url, token
    else:
        raise Exception('请先配置gitlab的token')


def sync_last_git_project_to_local(workspace_id: int, project_id: int, case_path: str, branch_name: str = 'master'):
    """
    同步最新的case项目到本地
    :param workspace_id: 用例库ID
    :param project_id: gitlab项目ID
    :param case_path: 待执行case路径
    :param branch_name: case分支
    :param commit_id: case commit_id
    :return:
    """
    # 获取用例源token类型
    db = next(get_sync_db())
    token_type = db.query(CaseSourceRelationModel).filter(CaseSourceRelationModel.workspace_id == workspace_id,
                                                          CaseSourceRelationModel.case_source_value[
                                                              "projectId"] == project_id).first().token_type
    gitlab_url, token = get_git_token(token_type=token_type, workspace_id=workspace_id)
    # case项目名称
    gitlab = GitlabAPI(gitlab_url=gitlab_url, token=token)
    git_project_name = gitlab.get_project_by_id(id=project_id).name

    # 判断case项目commit路径是否存在 不存在则拉取代码
    git_project_path = os.path.join(CASE_HOUSE_ROOT, str(workspace_id), str(project_id),
                                    branch_name, git_project_name)
    for i in range(20):
        case_exist = os.path.exists(os.path.join(git_project_path, case_path))
        success, pull_status, case_project_local_path = gitlab.pull_project_code(workspace_id=workspace_id,
                                                                                 project_id=project_id,
                                                                                 branch_name=branch_name)
        if case_exist and success:
            return git_project_path
        else:
            time.sleep(5)
            continue
    else:
        raise Exception(f"case项目路径不存在, case拉取可能失败: {os.path.join(git_project_path, case_path)}")


def cleanup_processes(processes: list[subprocess.Popen]):
    """清理所有未完成的进程"""
    print("正在清理未完成进程...", len(processes))
    for proc in processes:  # 使用切片复制避免迭代时修改
        try:
            if proc.poll() is None:  # 进程仍在运行
                print("正在终止进程:", proc.pid)
                # 获取当前进程的所有子进程
                children = []
                try:
                    children = psutil.Process(proc.pid).children(recursive=True)
                except Exception as e:
                    logger.error(f"获取进程 {proc.pid} 的子进程失败: {e}")

                # 先终止所有子进程
                for child in children:
                    try:
                        print(f"正在终止子进程: {child.pid}")
                        child.terminate()
                        try:
                            child.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            child.kill()
                    except Exception as e:
                        logger.error(f"终止子进程 {child.pid} 失败: {e}")

                # 再终止父进程
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()

        except Exception as e:
            logger.error(f"清理进程 {proc.pid} 时发生错误: {e}")
        finally:
            if proc.poll() is not None:  # 进程已结束
                print("进程已结束:", proc.pid)
            else:
                print("进程未正常结束:", proc.pid)


class PytestCaseRunner:
    """
    【pytest case的运行管理器】
    """

    @classmethod
    def executor(cls, testplan_id: int, task_id: int, job_id: int, workspace_id: int, case_path: str, case_name: str,
                 project_id: int, case_uuid: str,
                 env: int, branch_name):
        """
        执行器
        :param testplan_id: 任务计划id
        :param task_id: 任务id
        :param job_id: 工作id
        :param workspace_id: 用例库id
        :param case_path: case脚本路径
        :param case_uuid: case uuid
        :param case_name: case脚本名称
        :param project_id: 项目id
        :param env: 执行环境
        :param branch_name: 分支名称
        :return:
        """
        _processes = []  # 进程列表

        git_project_path = sync_last_git_project_to_local(workspace_id=workspace_id, project_id=project_id,
                                                          case_path=case_path,
                                                          branch_name=branch_name)
        # 获取python虚拟环境与解释器路径
        db = next(get_sync_db())
        venv_id = db.query(CaseSourceRelationModel).filter(CaseSourceRelationModel.workspace_id == workspace_id,
                                                           CaseSourceRelationModel.case_source_value[
                                                               "projectId"] == project_id).first().venv_id
        venv_info = db.query(PythonVirtualEnvModel).filter(PythonVirtualEnvModel.id == venv_id).first()
        if not venv_info:
            raise Exception(f'请先配置python虚拟环境,venv_id-{project_id}不存在')
        venv_path = venv_info.path
        pytest_path = os.path.join(venv_path, 'bin', 'pytest')
        if not os.path.exists(pytest_path):
            raise Exception(f'请先配置python虚拟环境,python虚拟环境不存在: {pytest_path}')
        # case报告文件名称预先生成
        report_name = case_path.split('/')[-1].split('.')[0] + '.html'
        json_name = case_path.split('/')[-1].split('.')[0] + '.json'
        xml_name = case_path.split('/')[-1].split('.')[0] + '.xml'

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
        # 运行pytest 脚本
        try:
            # 构造case执行指令
            cmd = '{} {} -vv -s --reruns 1 --reruns-delay 1 --log-cli-level=INFO --report={} --title={} --desc={} --junit-xml={} --tb=short --env={}'.format(
                pytest_path, case_path, report_html_path, case_path.split('/')[-1], case_name,
                report_xml_path, str(env).lower())
            logger.info(f"pytest case开始运行:{case_key}, 执行指令:{cmd}")

            # 执行case
            p = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, cwd=git_project_path, stderr=subprocess.PIPE)
            print("pid", p.pid)
            _processes.append(p)

            out, err = p.communicate(timeout=60 * 60 * 2)
            read_data = out.decode("utf-8", "ignore")
            error_data = err.decode("utf-8", "ignore")

            # logger.info(f"case:{case_key} 执行结果:{read_data}")
            logger.info(f"case:{case_key} 执行错误:{error_data}")

            # 解析case执行结果
            logger.info(
                f"case:{case_key} 期望生成xml报告地址:{report_xml_path}")
            if os.path.exists(report_xml_path):
                # 存在xml格式的报告文件
                logger.info(f'case:{case_key} xml报告地址存在')

                # 设定默认值
                total, passed, failed, error, skipped, successful = 0, 0, 0, 0, 0, 0

                # 解析xml报告 并统计case运行结果（通过率）
                root = ET.parse(os.path.join(report_dir, xml_name))
                for testcase in root.findall('.//testsuite'):
                    total += int(testcase.get('tests'))
                    error += int(testcase.get('errors'))
                    skipped += int(testcase.get('skipped'))
                    failed += int(testcase.get('failures'))
                if total == 0:
                    # case运行结果统计异常 则解析case脚本获取case总数
                    total = len(GitCaseParser.get_python_test_functions_by_filepath(
                        filename=os.path.join(git_project_path, case_path)))

                passed = total - failed - error - skipped
                successful = round(passed / total * 100, 1)
                case_result = {"total": total, "passed": passed, "failed": failed, "error": error,
                               "skipped": skipped, "successful": successful}
                logger.info(f'case运行结果统计: {case_result}')
            else:
                # 不存在xml格式的报告文件
                logger.info(f'case:{case_key} xml报告地址不存在')
                logger.debug(f"失败case路径: {os.path.join(git_project_path, case_path)}")
                case_result = {
                    "total": len(GitCaseParser.get_python_test_functions_by_filepath(
                        filename=os.path.join(git_project_path, case_path))),
                    "passed": 0,
                    "failed": 0,
                    "error": 0,
                    "skipped": 0,
                    "successful": 0}
            if not os.path.exists(
                    os.path.join(report_html_path)):
                db_case_info = db.query(PytestCaseModel).filter(
                    PytestCaseModel.case_uuid == case_uuid).first()
                report_url = create_error_html_report_file(workspace_id=workspace_id,
                                                           git_project_name=db_case_info.git_project_name,
                                                           case_type=CaseType.PYTEST,
                                                           case_path=case_path, case_name=db_case_info.case_name,
                                                           case_level=db_case_info.case_level,
                                                           case_author=db_case_info.case_author,
                                                           report_url=report_url,
                                                           report_path=report_html_path,
                                                           result=JobStatus.FAILED,
                                                           error_info=f"case执行异常,未能生成详细测试报告: {read_data + '\n' + error_data}")

            return {"case_result": case_result,
                    "case_report": report_url}
        except FunctionTimedOut as e:
            logger.error(f"case:{case_key}执行超时: {traceback.format_exc()}")
            raise e
        except Exception:
            # case执行异常
            logger.error(f"case:{case_key}执行异常: {traceback.format_exc()}")
            raise Exception(traceback.format_exc())
        finally:
            cleanup_processes(_processes)
