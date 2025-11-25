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

import psutil
from celery.exceptions import SoftTimeLimitExceeded

from app.case_handler.case_enum import CaseType
from app.case_handler.case_parser import GitCaseParser
from app.case_handler.gitlab_tool import GitlabAPI
from app.case_handler.models import PytestCaseModel
from engineproxy.settings import MEDIA_ROOT, logger, MEDIA_URL, REPORT_DOMAIN


def create_error_html_report_file(workspace_id: int, project_id: int, git_project_name: str, case_type: str,
                                  case_path: str,
                                  case_name: str, case_author: str, case_level: int, result_id: int, error_info: str):
    """
    创建错误的html报告文件
    :param case_level: 用例等级
    :param case_type: 用例类型
    :param case_author: 用例作者
    :param case_name: 用例名称
    :param git_project_name: 用例所属的gitlab项目名称
    :param case_path: 用脚本路径
    :param workspace_id: 用例库ID
    :param project_id: gitlab项目ID
    :param result_id: WTP下发的result_id
    :param error_info: 要在html中展示的错误信息
    :return: case报告的url
    """
    case_report_url = REPORT_DOMAIN + os.path.join(
        MEDIA_URL, 'html-report', str(workspace_id), str(project_id), str(result_id), 'error.html')
    case_report_dir = os.path.join(MEDIA_ROOT, 'html-report', str(workspace_id), str(project_id), str(result_id))
    if not os.path.exists(case_report_dir):
        os.makedirs(case_report_dir)
    case_report_path = os.path.join(case_report_dir, 'error.html')
    with open(case_report_path, 'w', encoding='utf-8') as f:
        f.write(
            """<!DOCTYPE html>
            <html lang="en">
            <head>
            <meta charset="UTF-8">
            <title>测试报告</title>
            <style>
               body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
               .container {{ width: 80%; margin: 20px auto; }}
               h1, h2 {{ color: #333; }}
               .overview, .details {{ background-color: #f2f2f2; padding: 20px; margin-top: 20px; }}
               .overview p {{ margin: 10px 0; }}
               .key {{ font-weight: 300; }}
               .value {{ color: darkgoldenrod; }}
               .error {{ color: red; }}
            </style>
            </head>
            <body>
                <div class="container">
                    <h1>测试报告</h1>
                    <div class="overview">
                        <h2>概览</h2>
                        <p><span class="key">用例库ID:</span> <span class="value">{}</span></p>
                        <p><span class="key">用例类型:</span> <span class="value">{}</span></p>
                        <p><span class="key">git项目名称:</span> <span class="value">{}</span></p>
                        <p><span class="key">用例名称:</span> <span class="value">{}</span></p>
                        <p><span class="key">用例路径:</span> <span class="value">{}</span></p>
                        <p><span class="key">用例等级:</span> <span class="value">{}</span></p>
                        <p><span class="key">用例负责人:</span> <span class="value">{}</span></p>
                        <p><span class="key">运行结果:</span> <span class="value error">失败</span></p>
                    </div>
                    <div class="details">
                        <h2>详细信息</h2>
                        <p>在执行脚本时遇到了一些问题，以下是错误信息：</p>
                        <p class="error">错误信息：{}</p>
                        <!-- 更多错误信息 -->
                    </div>
                </div>
            </body>
            </html>""".format(
                workspace_id, case_type, git_project_name, case_name, case_path, case_level, case_author, error_info))
    return case_report_url


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


def sync_last_git_project_to_local(workspace_id: int, project_id: int, case_path: str, branch_name: str = 'master',
                                   commit_id: str = ''):
    """
    同步最新的case项目到本地
    :param workspace_id: 用例库ID
    :param project_id: gitlab项目ID
    :param case_path: 待执行case路径
    :param branch_name: case分支
    :param commit_id: case commit_id
    :return:
    """
    # case项目名称
    gitlab = GitlabAPI()
    git_project_name = gitlab.get_project_by_id(id=project_id).name

    # 判断case项目commit路径是否存在 不存在则拉取代码
    git_project_path = os.path.join(MEDIA_ROOT, 'case_house', str(workspace_id), str(project_id), commit_id,
                                    branch_name,
                                    git_project_name)
    for i in range(20):
        case_exist = os.path.exists(os.path.join(git_project_path, case_path))
        success, pull_status, case_project_local_path = gitlab.pull_project_code(workspace_id=workspace_id,
                                                                                 project_id=project_id,
                                                                                 branch_name=branch_name,
                                                                                 commit_id=commit_id)
        if case_exist and success:
            return git_project_path
        else:
            time.sleep(5)
            continue
    else:
        raise Exception(f"case项目路径不存在, case拉取可能失败: {os.path.join(git_project_path, case_path)}")


class PytestCaseRunner:
    """
    【pytest case的运行管理器】
    """

    @classmethod
    def executor(cls, workspace_id: int, case_path: str, project_id: int, result_id: int, env: int, commit_id: str,
                 branch_name="master"):
        """
        执行器
        :param workspace_id: 用例库id
        :param case_path: case路径
        :param project_id: 项目id
        :param result_id: case执行结果的唯一标识
        :param env: 执行环境
        :param commit_id: 要clone的commit_id
        :param branch_name: 分支名称
        :return:
        """
        git_project_path = sync_last_git_project_to_local(workspace_id=workspace_id, project_id=project_id,
                                                          case_path=case_path,
                                                          branch_name=branch_name, commit_id=commit_id)
        # 判断case项目是否存在venv虚拟环境
        if os.path.exists(os.path.join(git_project_path, 'venv')):
            venv_path = os.path.join(git_project_path, 'venv/bin/pytest')
        else:
            venv_path = 'pytest'

        # case报告文件名称预先生成
        report_name = case_path.split('/')[-1].split('.')[0] + '.html'
        json_name = case_path.split('/')[-1].split('.')[0] + '.json'
        xml_name = case_path.split('/')[-1].split('.')[0] + '.xml'

        # case报告文件存放路径预先创建
        report_path = os.path.join(
            MEDIA_ROOT, 'html-report', str(workspace_id), str(project_id), str(result_id))
        try:
            if not os.path.exists(report_path):
                os.makedirs(report_path)
        except FileExistsError:
            pass

        case_key = f"{workspace_id}_{project_id}_{result_id}_{case_path}"
        # 运行pytest 脚本
        try:
            # 构造case执行指令
            cmd = '{} {} -vv -s --reruns 1 --reruns-delay 1 --log-cli-level=INFO --html={} --self-contained-html --json-report={} --junit-xml={} --tb=short --env={}'.format(
                venv_path, case_path, os.path.join(report_path, report_name), os.path.join(report_path, json_name),
                os.path.join(report_path, xml_name),
                str(env))
            logger.info(f"pytest case开始运行:{case_key}, 执行指令:{cmd}")

            # 执行case
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
                terminate_process(child_pid)  # 终止进程

            # 解析case执行结果
            logger.info(
                f"case:{case_key} 期望生成xml报告地址:{os.path.join(report_path, xml_name)}")
            if os.path.exists(os.path.join(report_path, xml_name)):
                # 存在xml格式的报告文件
                logger.info(f'case:{case_key} xml报告地址存在')

                # 设定默认值
                total, passed, failed, error, skipped, successful = 0, 0, 0, 0, 0, 0

                # 解析xml报告 并统计case运行结果（通过率）
                root = ET.parse(os.path.join(report_path, xml_name))
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
            report_path_exist = True
            if not os.path.exists(
                    os.path.join(MEDIA_ROOT, 'html-report', str(workspace_id), str(project_id), str(result_id),
                                 report_name)):
                report_path_exist = False
                db_case_info = PytestCaseModel.objects.filter(workspace_id=workspace_id, case_path=case_path,
                                                              git_project_id=project_id).first()
                error_report_url = create_error_html_report_file(workspace_id=workspace_id, project_id=project_id,
                                                                 git_project_name=db_case_info.git_project_name,
                                                                 result_id=result_id,
                                                                 case_type=CaseType.Pytest.value,
                                                                 case_path=case_path, case_name=db_case_info.case_name,
                                                                 case_level=db_case_info.case_level,
                                                                 case_author=db_case_info.case_author,
                                                                 error_info=f"case执行异常,未能生成详细测试报告: {read_data}")
            case_report_url = REPORT_DOMAIN + os.path.join(MEDIA_URL, 'html-report', str(workspace_id), str(project_id),
                                                           str(result_id), report_name)
            return {"case_result": {"case_result": case_result,
                                    "case_report": case_report_url if report_path_exist else error_report_url}}
        except SoftTimeLimitExceeded:
            # case执行超时
            raise SoftTimeLimitExceeded
        except Exception:
            # case执行异常
            logger.error(f"case:{case_key}执行异常: {traceback.format_exc()}")
            raise Exception(traceback.format_exc())
