"""
@FileName：case_sync.py
@Description：case数据源发生变化 本地case同步更新
@Author：baojun.wang
"""
import copy
import os
import traceback
from dataclasses import dataclass, field

import gitlab
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.case_handler.case_enum import CaseType
from app.case_handler.case_parser import PytestCaseParser, TestNGCaseParser
from app.case_handler.gitlab_tool import GitlabAPI
from app.case_handler.models import PytestCaseModel, TestNGCaseModel
from app.core.database import get_sync_db
from app.core.orm_tools import model_to_dict
from app.case_source.models import CaseSourceRelationModel
from app.setting.controller import SettingCRUD
from utils.commonlib import now
from utils.custom_logging import logger


def get_case_model_by_case_type(case_type: str):
    """
    根据case类型获取case数据库模型
    :return:
    """
    if case_type == CaseType.Pytest.value:
        return PytestCaseModel
    elif case_type == CaseType.TestNG.value:
        return TestNGCaseModel
    else:
        raise Exception(f'不支持的case类型: {case_type}')


@dataclass
class GitCaseSync:
    """
    case数据源发生变化 本地case同步更新
    """
    git_project_id: int  # gitlab项目ID
    git_project_name: str  # gitlab项目名称
    git_project_commit_id: str  # gitlab项目当前最新的提交ID
    git_commits: list = field(default_factory=list)  # gitlab项目提交记录
    branch_name: str = 'master'  # 分支名
    gitlab_client: GitlabAPI = field(default=None)  # gitlab客户端
    case_model: object = None  # case数据库模型
    case_parser: object = None  # case解析器
    case_source_relation: CaseSourceRelationModel = CaseSourceRelationModel  # 用例库关系模型
    db_session: Session = None

    def __post_init__(self):
        # 修复：在初始化时获取实际的数据库会话
        self.db_session = next(get_sync_db())

    def identify_git_project(self):
        """
        根据git_project_id识别git项目类型以及项目是否有效
        """
        # 查找case类型为webui的用例库关系并且case_source_value为git_project_id的用例库关系
        case_source_relations = self.db_session.query(CaseSourceRelationModel).filter(
            or_(
                CaseSourceRelationModel.case_type == CaseType.Pytest.value,
                CaseSourceRelationModel.case_type == CaseType.TestNG.value
            ),
            CaseSourceRelationModel.case_source_value['projectId'] == self.git_project_id,
            CaseSourceRelationModel.case_source_value['branch_name'] == self.branch_name
        ).all()
        if case_source_relations:
            # 有gitProject的绑定关系 说明此gitProject是有效的
            logger.info(
                f"gitProjectId: {self.git_project_id} 有效, 查找到的用例库关系: "
                f"{[_case_source_relation.workspace_id for _case_source_relation in case_source_relations]}")
            return case_source_relations
        else:
            # 没有gitProject的绑定关系 说明此gitProject是无效的
            logger.error(f"gitProjectId: {self.git_project_id} 无效")
            return None

    def filter_case_from_git_commit(self, commit_id: str, added_file_list: list = None, removed_file_list: list = None,
                                    modified_file_list: list = None):
        """
        从git_commit中过滤case（非case变更不处理）
        :param modified_file_list: 修改的文件
        :param removed_file_list: 删除的文件
        :param added_file_list: 添加的文件
        :param commit_id: commit_id
        :return: 处理后的列表
        """
        added_file_list = added_file_list or []
        removed_file_list = removed_file_list or []
        modified_file_list = modified_file_list or []

        added_case_list, removed_case_list, modified_case_list = [], [], []
        default_case_info = {
            "workspace_id": self.case_source_relation.workspace_id,  # 用例库ID
            "specific_type": self.case_source_relation.specific_type,  # WTP定义的测试类型
            "case_type": self.case_source_relation.case_type,  # 用例类型
            "case_commit_id": commit_id,  # 用例commitId
            "case_path": '',  # 用例路径
            "case_package": '',  # 用例包名
            "git_project_id": '',  # gitlab项目ID
            "git_project_name": '',  # gitlab项目名称
            "git_project_commit_id": '',  # gitlab项目当前最新的提交ID
            "case_name": '',  # 用例名称
            'case_author': '',  # 用例作者
            'case_level': '',  # 用例等级
            'case_detail': ''  # 用例详情
        }
        setting_crud = SettingCRUD(self.db_session)
        gitlab_url, token = setting_crud.get_gitlab_credentials(token_type=self.case_source_relation.token_type,
                                                                workspace_id=self.case_source_relation.workspace_id)
        self.gitlab_client = GitlabAPI(
            gitlab_url=gitlab_url,
            token=token
        )

        git_project_id = self.case_source_relation.case_source_value['projectId']
        for modified_file_path in modified_file_list:
            # 判断修改的文件是否为测试用例
            if self.case_parser.is_test_script(
                    filename=os.path.split(modified_file_path)[-1]) and modified_file_path.startswith(
                self.case_source_relation.case_source_value['caseDir']):
                case_content = self.gitlab_client.get_content(project_id=self.git_project_id,
                                                              file_path=modified_file_path,
                                                              ref=commit_id)
                # 提取注释
                comment_text = self.case_parser.draw_comment_from_script(content_text=case_content)
                code_comment_dict = self.case_parser.format_code_comment(comment_text=comment_text)
                case_function_list = self.case_parser.get_test_functions_by_context(content_text=case_content)
                if not comment_text or not code_comment_dict:
                    # 测试用例没有注释或者case注释不符合规范  需要删除case
                    inactivated_cases = self.db_session.query(self.case_model).filter(
                        and_(
                            self.case_model.workspace_id == self.case_source_relation.workspace_id,
                            self.case_model.case_type == self.case_source_relation.case_type,
                            self.case_model.git_project_id == self.case_source_relation.case_source_value['projectId'],
                            self.case_model.case_path == modified_file_path
                        )
                    ).all()
                    if inactivated_cases:
                        # 数据库中存在此用例 添加到待删除的用例列表中
                        removed_case_info = copy.deepcopy(default_case_info)
                        removed_case_info['case_path'] = modified_file_path
                        removed_case_list.append(removed_case_info)
                        continue
                    else:
                        # 数据库中原本就不存在此用例 说明之前这个脚本也没有正确的注释 所以不需要同步case
                        continue
                else:
                    # 注释格式正确
                    valid_cases = self.db_session.query(self.case_model).filter(
                        and_(
                            self.case_model.workspace_id == self.case_source_relation.workspace_id,
                            self.case_model.case_type == self.case_source_relation.case_type,
                            self.case_model.git_project_id == self.case_source_relation.case_source_value['projectId'],
                            self.case_model.case_path == modified_file_path
                        )
                    ).all()
                    if valid_cases:
                        # 数据库中存在此用例 添加到待修改的用例列表中
                        modified_case_info = copy.deepcopy(default_case_info)
                        modified_case_info['case_name'] = code_comment_dict['case_desc']
                        modified_case_info['case_author'] = code_comment_dict['author']
                        modified_case_info['case_level'] = code_comment_dict['level']
                        modified_case_info['case_detail'] = case_content
                        modified_case_info['case_function_list'] = case_function_list
                        modified_case_info['case_path'] = modified_file_path
                        modified_case_info[
                            'case_package'] = self.case_parser.get_package_corresponding_to_the_case_path(
                            case_path=modified_file_path)
                        modified_case_info['git_project_id'] = git_project_id
                        modified_case_info['git_project_name'] = self.case_source_relation.case_project_name
                        modified_case_info['case_uuid'] = self.case_parser.generate_case_uuid(
                            workspace_id=self.case_source_relation.workspace_id,
                            specific_type=self.case_source_relation.specific_type,
                            case_type=self.case_source_relation.case_type,
                            git_project_id=
                            self.case_source_relation.case_source_value[
                                'projectId'],
                            case_path=modified_file_path)
                        modified_case_list.append(modified_case_info)
                    else:
                        # 数据库中不存在此用例 添加到待新增的用例列表中
                        added_case_info = copy.deepcopy(default_case_info)
                        added_case_info['case_name'] = code_comment_dict['case_desc']
                        added_case_info['case_author'] = code_comment_dict['author']
                        added_case_info['case_level'] = code_comment_dict['level']
                        added_case_info['case_detail'] = case_content
                        added_case_info['case_function_list'] = case_function_list
                        added_case_info['case_path'] = modified_file_path
                        added_case_info['case_package'] = self.case_parser.get_package_corresponding_to_the_case_path(
                            case_path=modified_file_path)
                        added_case_info['git_project_id'] = git_project_id
                        added_case_info['git_project_name'] = self.case_source_relation.case_project_name
                        added_case_info['case_uuid'] = self.case_parser.generate_case_uuid(
                            workspace_id=self.case_source_relation.workspace_id,
                            specific_type=self.case_source_relation.specific_type,
                            case_type=self.case_source_relation.case_type,
                            git_project_id=
                            self.case_source_relation.case_source_value[
                                'projectId'],
                            case_path=modified_file_path)
                        added_case_list.append(added_case_info)

        # 处理git中case目录移动的情况: 目录移动等同于删除+新增，但是删除的case不在removed_case_list中 需要兜底解决
        for added_file_path in added_file_list:
            # 新增文件移动了路径 需要查询原先的路径并且删除原路径
            if self.case_parser.is_test_script(
                    filename=os.path.split(added_file_path)[-1]):
                history_db_case_info_list = self.db_session.query(self.case_model).filter(
                    and_(
                        self.case_model.workspace_id == self.case_source_relation.workspace_id,
                        self.case_model.case_type == self.case_source_relation.case_type,
                        self.case_model.git_project_id == self.case_source_relation.case_source_value['projectId'],
                        self.case_model.case_path.contains(os.path.split(added_file_path)[-1])
                    )
                ).all()
                if history_db_case_info_list:
                    for history_db_case_info in history_db_case_info_list:
                        try:
                            self.gitlab_client.get_content(project_id=self.git_project_id,
                                                           file_path=history_db_case_info.case_path,
                                                           ref=commit_id)
                        except gitlab.exceptions.GitlabGetError:
                            # 新增的文件不存在 需要删除原路径
                            removed_case_info = copy.deepcopy(default_case_info)
                            removed_case_info['case_path'] = history_db_case_info.case_path
                            removed_case_info['case_uuid'] = self.case_parser.generate_case_uuid(
                                workspace_id=self.case_source_relation.workspace_id,
                                specific_type=self.case_source_relation.specific_type,
                                case_type=self.case_source_relation.case_type,
                                git_project_id=
                                self.case_source_relation.case_source_value[
                                    'projectId'],
                                case_path=history_db_case_info.case_path)
                            removed_case_list.append(removed_case_info)
                            continue

        for removed_file_path in removed_file_list:
            # 处理需要删除的文件
            if self.case_parser.is_test_script(
                    filename=os.path.split(removed_file_path)[-1]) and added_file_path.startswith(
                self.case_source_relation.case_source_value['caseDir']):
                # 文件是测试用例
                removed_case_info = copy.deepcopy(default_case_info)
                removed_case_info['case_path'] = removed_file_path
                removed_case_info['case_uuid'] = self.case_parser.generate_case_uuid(
                    workspace_id=self.case_source_relation.workspace_id,
                    specific_type=self.case_source_relation.specific_type,
                    case_type=self.case_source_relation.case_type,
                    git_project_id=
                    self.case_source_relation.case_source_value[
                        'projectId'],
                    case_path=removed_file_path)
                removed_case_list.append(removed_case_info)

        for added_file_path in added_file_list:
            # 处理需要新增的文件
            if self.case_parser.is_test_script(
                    filename=os.path.split(added_file_path)[-1]) and added_file_path.startswith(
                self.case_source_relation.case_source_value['caseDir']):
                case_content = self.gitlab_client.get_content(project_id=self.git_project_id, file_path=added_file_path,
                                                              ref=commit_id)  # 获取文件内容
                # 提取注释
                comment_text = self.case_parser.draw_comment_from_script(content_text=case_content)
                if not comment_text:
                    # 测试用例没有注释 不同步case
                    continue
                else:
                    # 测试用例有注释
                    code_comment_dict = self.case_parser.format_code_comment(comment_text=comment_text)
                    case_function_list = self.case_parser.get_test_functions_by_context(
                        content_text=case_content)
                    if code_comment_dict:
                        # 注释格式正确
                        added_case_info = copy.deepcopy(default_case_info)
                        added_case_info['case_name'] = code_comment_dict['case_desc']
                        added_case_info['case_author'] = code_comment_dict['author']
                        added_case_info['case_level'] = code_comment_dict['level']
                        added_case_info['case_detail'] = case_content
                        added_case_info['case_function_list'] = case_function_list
                        added_case_info['case_path'] = added_file_path
                        added_case_info['case_package'] = self.case_parser.get_package_corresponding_to_the_case_path(
                            case_path=added_file_path)
                        added_case_info['git_project_id'] = git_project_id
                        added_case_info['git_project_name'] = self.case_source_relation.case_project_name
                        added_case_info['case_uuid'] = self.case_parser.generate_case_uuid(
                            workspace_id=self.case_source_relation.workspace_id,
                            specific_type=self.case_source_relation.specific_type,
                            case_type=self.case_source_relation.case_type,
                            git_project_id=
                            self.case_source_relation.case_source_value[
                                'projectId'],
                            case_path=added_file_path)
                        added_case_list.append(added_case_info)

        return added_case_list, removed_case_list, modified_case_list

    def parse_git_commits(self):
        """
        解析git_commits
        :return: 处理完成以后的git_commits
        """
        git_commits = sorted(self.git_commits, key=lambda x: x['timestamp'])
        for commit in git_commits:  # 遍历所有提交记录
            if commit['message'].startswith('合并分支 ') or commit['message'].startswith('Merge '):
                # 合并分支的commit 不同步case
                continue

            added_case_list, removed_case_list, modified_case_list = self.filter_case_from_git_commit(
                commit_id=commit['id'],
                added_file_list=commit['added'],
                removed_file_list=commit['removed'],
                modified_file_list=commit['modified']
            )

            yield commit['id'], added_case_list, removed_case_list, modified_case_list

    def sync(self):
        """
        同步case
        """
        # 根据git_project_id识别git项目类型以及项目是否有效
        case_source_relations = self.identify_git_project()
        if not case_source_relations:
            # 无效的gitProjectId 不同步case
            return False

        # 找到wtp与此gitProject的绑定关系
        for case_source_relation in case_source_relations:
            # 根据用例类型同步case
            if case_source_relation.case_type == CaseType.Pytest.value:
                self.case_source_relation, self.case_model, self.case_parser = case_source_relation, \
                                                                               PytestCaseModel, PytestCaseParser
                self.sync_case()

            elif case_source_relation.case_type == CaseType.TestNG.value:
                self.case_source_relation, self.case_model, self.case_parser = case_source_relation, \
                                                                               TestNGCaseModel, TestNGCaseParser
                self.sync_case()  # TestNG的case与pytest的case同步逻辑一致 可以直接复用
            else:
                raise Exception(f'不支持的case类型: {case_source_relation.case_type}')

            logger.info(f"gitProjectId: {self.git_project_id} 同步完成")

        else:
            return True

    def sync_case(self):
        """
        同步webui的case
        :return: True/False
        """
        # 同步commits用例
        for commit_id, added_case_list, removed_case_list, modified_case_list in self.parse_git_commits():
            # 同步commit case变更到数据库
            self.sync_case_change_to_db(
                added_case_list=copy.deepcopy(added_case_list), removed_case_list=copy.deepcopy(removed_case_list),
                modified_case_list=copy.deepcopy(modified_case_list))
        # 批量更新git_project_commit_id到数据库
        self.batch_update_git_project_commit_id_2_db()

    def sync_case_change_to_db(self, added_case_list=None,
                               removed_case_list=None,
                               modified_case_list=None):
        """
        同步case变更到数据库
        :return:
        """
        if not added_case_list: added_case_list = []
        if not removed_case_list: removed_case_list = []
        if not modified_case_list: modified_case_list = []
        git_project_id = self.case_source_relation.case_source_value['projectId']
        try:
            for add_case in added_case_list:
                # 将add_case插入到数据库
                del add_case['case_detail']
                add_case['workspace_id'] = self.case_source_relation.workspace_id
                add_case['case_type'] = self.case_source_relation.case_type
                add_case['specific_type'] = self.case_source_relation.specific_type
                add_case['case_source_value'] = self.case_source_relation.case_source_value
                add_case['case_type'] = self.case_source_relation.case_type

                # 创建模型实例并添加到会话
                case_instance = self.case_model(**add_case)
                self.db_session.add(case_instance)
            # 提交事务
            self.db_session.commit()

            for remove_case in removed_case_list:
                # 将remove_case从数据库删除
                self.db_session.query(self.case_model).filter(
                    and_(
                        self.case_model.workspace_id == self.case_source_relation.workspace_id,
                        self.case_model.specific_type == self.case_source_relation.specific_type,
                        self.case_model.case_type == self.case_source_relation.case_type,
                        self.case_model.git_project_id == git_project_id,
                        self.case_model.case_path == remove_case['case_path']
                    )
                ).delete()
            # 提交事务
            self.db_session.commit()

            for modified_case in modified_case_list:
                # 将modified_case更新到数据库
                del modified_case['case_detail']
                modified_case['update_time'] = now()
                self.db_session.query(self.case_model).filter(
                    and_(
                        self.case_model.workspace_id == self.case_source_relation.workspace_id,
                        self.case_model.specific_type == self.case_source_relation.specific_type,
                        self.case_model.case_type == self.case_source_relation.case_type,
                        self.case_model.git_project_id == git_project_id,
                        self.case_model.case_path == modified_case['case_path']
                    )
                ).update(modified_case)

            # 提交事务
            self.db_session.commit()
        except Exception:
            # 回滚事务
            self.db_session.rollback()
            error_msg = traceback.format_exc()
            logger.error(
                f"接受到gitlab id:{git_project_id}的webhook通知处理后 同步case变更到数据库失败 {error_msg}")
            raise Exception(f"接受到gitlab webhook通知处理后 同步case变更到数据库失败 {error_msg}")
        else:
            # 同步成功
            logger.info(f"接受到gitlab webhook通知处理后 同步case变更到数据库成功")
            return True

    def batch_update_git_project_commit_id_2_db(self):
        """
        批量更新git_project_commit_id到数据库
        :return: True/False
        """
        try:
            self.db_session.query(self.case_model).filter(
                and_(
                    self.case_model.workspace_id == self.case_source_relation.workspace_id,
                    self.case_model.specific_type == self.case_source_relation.specific_type,
                    self.case_model.case_type == self.case_source_relation.case_type,
                    self.case_model.git_project_id == self.git_project_id
                )
            ).update({
                'git_project_commit_id': self.git_project_commit_id,
                # 'update_time': now()
            })
            # 提交事务
            self.db_session.commit()
            return True
        except Exception as e:
            # 回滚事务
            self.db_session.rollback()
            raise e


@dataclass
class InitGitCase:
    """
    在初次绑定case源信息后 初始化case
    """
    case_source_relation: CaseSourceRelationModel  # 用例库关系
    case_model: object = None  # case数据库模型
    case_parser: object = None  # case解析器
    gitlab_client: GitlabAPI = field(default=None)  # gitlab客户端
    db_session: Session = None
    gitlab_url: str = None
    token: str = None

    def __post_init__(self):
        self.db_session = next(get_sync_db())
        self.git_project_id = self.case_source_relation.case_source_value['projectId']
        self.branch_name = self.case_source_relation.case_source_value['branchName']
        self.gitlab_client = GitlabAPI(gitlab_url=self.gitlab_url, token=self.token)

    def sync(self):
        """
        同步case
        """
        # 根据用例类型同步case
        if self.case_source_relation.case_type == CaseType.Pytest.value:
            self.case_model, self.case_parser = PytestCaseModel, PytestCaseParser
        elif self.case_source_relation.case_type == CaseType.TestNG.value:
            self.case_model, self.case_parser = TestNGCaseModel, TestNGCaseParser
        else:
            # 无效的用例类型 不同步case
            return False
        # 开始同步case
        self.sync_case()
        return True

    def sync_case(self):
        """
        同步代码仓库的case
        """
        # 获取case project最新的commitId
        project_latest_commit_id = self.gitlab_client.get_project_latest_commit_id(
            project_id=self.git_project_id)
        # clone case project到本地
        case_project_local_path = self.gitlab_client.clone_case_project_to_local(
            workspace_id=self.case_source_relation.workspace_id, project_id=self.git_project_id,
            branch_name=self.branch_name)

        # 从case_project_local_path中读取case列表
        case_list = self.case_parser(root_path=case_project_local_path).get_case_list(
            self.case_source_relation.case_source_value['caseDir'])

        # 删除case库中之前的相同的用例
        stmt = select(self.case_model).where(
            and_(
                self.case_model.workspace_id == self.case_source_relation.workspace_id,
                self.case_model.case_type == self.case_source_relation.case_type,
                self.case_model.git_project_id == self.git_project_id,
                self.case_model.branch_name == self.branch_name
            )
        )

        result = self.db_session.execute(stmt)
        historical_case_list = result.scalars().all()
        removed_case_list = []
        for historical_case in historical_case_list:
            # 将删除的case信息转为dict类型（排除'id', 'case_function_list'字段）
            historical_case_dict = model_to_dict(historical_case, exclude=['id', 'case_function_list'])
            historical_case_dict['case_detail'] = ''  # 删除的case不关心用例内容了 直接置为空字符串
            # 追加到removed_case_list中
            removed_case_list.append(historical_case_dict)
            # 从数据库删除历史老旧case
            self.db_session.delete(historical_case)

        # 发生修改的case 初始化case时都是空
        modified_case_list = []

        added_case_list = []  # 收集新增的用例信息

        for case_info_dict, case_content in case_list:
            # 1. 补充/更新用例字段（保持原有逻辑）
            case_info_dict['workspace_id'] = self.case_source_relation.workspace_id
            case_info_dict['git_project_id'] = self.git_project_id
            case_info_dict['git_project_name'] = self.case_source_relation.case_project_name
            case_info_dict['git_project_commit_id'] = project_latest_commit_id
            case_info_dict['case_commit_id'] = project_latest_commit_id
            case_info_dict['case_type'] = self.case_source_relation.case_type
            case_info_dict['specific_type'] = self.case_source_relation.specific_type
            case_info_dict['case_source_value'] = self.case_source_relation.case_source_value

            # 生成 case_uuid（保持原有逻辑）
            case_info_dict['case_uuid'] = self.case_parser.generate_case_uuid(
                workspace_id=self.case_source_relation.workspace_id,
                specific_type=self.case_source_relation.specific_type,
                case_type=self.case_source_relation.case_type,
                git_project_id=self.case_source_relation.case_source_value['projectId'],
                branch_name=self.branch_name,
                case_path=case_info_dict['case_path']
            )

            # 2. 插入数据库
            case_instance = self.case_model(**case_info_dict)
            self.db_session.add(case_instance)  # 关键：用有效会话执行 add
            # 3. 补充 case_detail 并收集结果（非数据库操作，可正常执行）
            case_info_dict['case_detail'] = case_content
            added_case_list.append(case_info_dict)
        self.db_session.commit()

        return added_case_list, removed_case_list, modified_case_list


def init_case_project(gitlab_url: str, token: str, case_source_relation: CaseSourceRelationModel):
    """
    :param 用例关系表记录
    初始化case项目
    :return:
    """
    InitGitCase(gitlab_url=gitlab_url, token=token, case_source_relation=case_source_relation).sync()
