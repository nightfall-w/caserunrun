import os
import subprocess
import time
import traceback
from dataclasses import dataclass, field

from dotenv import load_dotenv
from gitlab import Gitlab

from app.core.config import CASE_HOUSE_ROOT
from app.core.redis import get_redis_cache
from utils.custom_logging import logger

load_dotenv()


class BranchState:
    PULLING = "PULLING"
    DONE = "DONE"
    FAILED = "FAILED"


@dataclass
class GitlabAPI(object):
    gitlab_url: str
    token: str
    gl: Gitlab = field(default=None)

    def __post_init__(self):
        # 初始化Gitlab客户端
        self.gl = Gitlab(url=self.gitlab_url, private_token=self.token, timeout=3)

    def get_project_default_branch(self, project_id):
        """
        获取项目的默认分支
        :param project_id: 项目ID或项目路径
        :return: 默认分支名称
        """
        project = self.gl.projects.get(project_id)
        return project.default_branch

    def get_project_branches(self, project_id):
        """
        获取项目的所有分支列表
        :param project_id: 项目ID或项目路径
        :return: 分支列表
        """
        project = self.gl.projects.get(project_id)
        branches = project.branches.list(all=True)
        return [branch.name for branch in branches]

    def get_current_user(self):
        """
        获取当前token对应的用户ID
        :return: 用户ID
        """
        self.gl.auth()
        current_user = self.gl.user
        return current_user

    def get_project_by_id(self, id):
        """
        通过项目id获取项目
        :param id:
        :return:
        """
        project = self.gl.projects.get(id)
        project.name = project.path
        return project

    def get_group_id_by_group_name(self, group_name):
        """
        通过组名获取组id
        :param group_name:
        :return:
        """
        group = self.gl.groups.get(group_name, all=True)
        return group.id

    def get_user_projects(self):
        """
        获取用户所拥有的项目
        :param userid:
        :return:
        """
        userid = self.get_current_user().id
        projects = self.gl.projects.owned(userid=userid, all=True)
        result_list = []
        for project in projects:
            result_list.append(project.http_url_to_repo)
        return result_list

    def get_group_projects(self, group_name):
        """
        获取组内项目
        :param group_name:
        :return:
        """
        group = self.gl.groups.get(group_name, all=True)
        projects = group.projects.list(all=True)
        return projects

    def get_project_commits(self, project_id, ref_name='master', get_all=False, per_page=50):
        """
        获取项目commit列表
        :param project_id: 项目id
        :param ref_name: 分支名或者commitId
        :param get_all: 是否获取所有commit
        :param per_page: 每页数量
        :return:
        """
        project = self.gl.projects.get(project_id)
        commits = project.commits.list(order_by='created_at', get_all=False, sort='desc', per_page=100, ref=ref_name,
                                       keep_base_url=True)
        return commits

    def get_project_latest_commit_id(self, project_id, ):
        """
        获取项目最新的commitId
        :param project_id:
        :return:
        """
        project = self.gl.projects.get(project_id)
        commits = project.commits.list(order_by='created_at', get_all=False, sort='desc', per_page=1,
                                       keep_base_url=True)
        if commits:
            return commits[0].id
        else:
            return ''

    def get_content(self, project_id, file_path: str, ref: str = 'master'):
        """
        通过项目id获取文件内容
        :param ref: 分支名或者commitId
        :param file_path: 文件路径
        :param project_id: 项目id
        :return: 文件内容
        """
        projects = self.gl.projects.get(project_id)
        f = projects.files.get(file_path=file_path, ref=ref, decode=True)
        content = f.decode()
        return content.decode('utf-8')

    def get_all_group(self):
        """
        获取所有群组
        :return:
        """
        return self.gl.groups.list(all=True)

    def get_webhooks(self, project_id):
        return [hook.url for hook in self.gl.projects.get(project_id).hooks.list()]

    def create_webhook(self, project_id, url, branch_name: str = 'master'):
        if url in self.get_webhooks(project_id):
            logger.info(f"项目{project_id}已经存在webhook:{url}")
            return True
        else:
            print(f"开始创建项目{project_id}的webhook:{url}")
            return self.gl.projects.get(project_id).hooks.create(
                {'url': url, 'push_events': True, 'push_events_branch_filter': branch_name})

    def clone_case_project_to_local(self, workspace_id: int, project_id: int, branch_name: str = 'master',
                                    commit_id: str = ''):
        """
        clone case project
        """
        for i in range(5):
            logger.info(
                f"第{i + 1}次尝试clone workspaceId:{workspace_id}绑定的gitlab项目:{project_id}的{branch_name}分支")
            # 从gitlab拉取代码
            success, pull_status, case_project_local_path = self.pull_project_code(
                workspace_id=workspace_id,
                project_id=project_id,
                branch_name=branch_name, commit_id=commit_id)
            if success:
                # 拉取成功 跳出重试循环
                return case_project_local_path
            else:
                if pull_status == BranchState.FAILED:
                    # 拉取失败 重试
                    logger.error(
                        f"workspaceId:{workspace_id}绑定的gitlab项目:{project_id}的{branch_name}分支拉取失败 重试中")
                    time.sleep(3)
                    continue
                elif pull_status == BranchState.PULLING:
                    # 正在拉取 等待
                    logger.info(
                        f"workspaceId:{workspace_id}绑定的gitlab项目:{project_id}的{branch_name}分支正在拉取中 请等待")
                    time.sleep(3)
                    continue
        else:
            # 重试次数用尽 拉取失败
            logger.error(
                f"workspaceId:{workspace_id}绑定的gitlab项目:{project_id}的{branch_name}分支拉取失败")
            raise Exception(
                f"workspaceId:{workspace_id}绑定的gitlab项目:{project_id}的{branch_name}分支拉取失败")

    def pull_project_code(self, workspace_id: int, project_id: int, branch_name: str = 'master',
                          commit_id: str = ''):
        """
        从gitlab拉取代码
        :param workspace_id: wtp项目id
        :param project_id: 项目id
        :param branch_name: 分支名
        :param commit_id: 提交id (非必填)
        """
        cmd = ''
        project = self.get_project_by_id(project_id)

        cache_key = "engineProxy:commit_pull_" + str(project_id) + "_" + branch_name + "_" + commit_id

        http_url_to_repo = project.attributes.get('http_url_to_repo')
        http_url_to_repo = http_url_to_repo.replace('//', '//' + f'oauth2:{self.token}@')
        clone_cmd = f'git clone -b {branch_name} {http_url_to_repo} --recurse'
        pull_cmd = f'git pull origin {branch_name} --recurse'
        redis_cache_instance = get_redis_cache()

        try:
            root_path = os.path.join(CASE_HOUSE_ROOT, str(workspace_id), str(project_id), commit_id,
                                     branch_name)
            if not os.path.isdir(root_path):
                os.makedirs(root_path)
            os.chdir(root_path)

            case_project_local_path = os.path.join(root_path, project.name)

            if os.path.exists(case_project_local_path) and not commit_id:
                # 如果项目已经存在 并且没有指定commitId 说明是项目解绑后重新初始化 则直接pull
                cmd, cwd = pull_cmd, case_project_local_path
            elif os.path.exists(case_project_local_path) and commit_id:
                # 如果项目已经存在 并且指定了commitId 不需要重新clone也不需要更新代码
                redis_cache_instance.set(cache_key, BranchState.DONE, 3)
                return True, BranchState.DONE, case_project_local_path
            else:
                # 如果项目不存在 则clone
                cmd, cwd = clone_cmd, root_path
            print(f'cmd: {cmd}')
            if redis_cache_instance.get(cache_key):
                logger.info(f'代码正在拉取中: {cache_key}')
                return False, BranchState.PULLING, ''
            redis_cache_instance.set(cache_key, BranchState.PULLING, 5)

            # 执行拉取代码指令
            p = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, cwd=cwd)
            out = p.stdout
            read_data = out.read().decode("utf-8", "ignore")
            logger.debug(f'代码拉取输出: {read_data}')
            if 'fatal' in read_data or 'failed' in read_data or 'error' in read_data:
                logger.error(f'cmd: {cmd} 代码拉取失败: {read_data}')
                redis_cache_instance.set(cache_key, BranchState.FAILED, 1)
                raise Exception(f'cmd: {cmd} 代码拉取失败: {read_data}')

            if commit_id:
                # 如果指定了commitId 切换到指定commit_id
                switch_commit_cmd = f'git checkout {commit_id}'
                p = subprocess.Popen(switch_commit_cmd, shell=True, stdout=subprocess.PIPE,
                                     cwd=case_project_local_path)
                out = p.stdout
                read_data = out.read().decode("utf-8", "ignore")
                logger.debug(f'代码commit拉取输出: {read_data}')

            redis_cache_instance.set(cache_key, BranchState.DONE, 3)
            time.sleep(1.5)
            return True, BranchState.DONE, case_project_local_path
        except Exception:
            logger.error(f'cmd: {cmd} 代码拉取失败:{traceback.format_exc()}')
            redis_cache_instance.set(cache_key, BranchState.FAILED, 3)
            return False, BranchState.FAILED, ''

    def get_project_tree_recursive(self, project_id, ref='master'):
        """递归获取完整文件树（处理分页）"""
        project = self.gl.projects.get(project_id)
        all_items = []
        page = 1
        per_page = 100  # 最大每页数量
        while True:
            tree = project.repository_tree(
                ref=ref,
                recursive=True,
                page=page,
                per_page=per_page
            )
            if not tree:
                break
            all_items.extend(tree)
            page += 1
        return all_items

    def get_project_tree_as_element_ui_format(self, project_id, ref='master'):
        """
        获取项目文件树并转换为 Element Plus Tree 组件所需的格式
        :param project_id: 项目ID
        :param ref: 分支名或commit ID，默认为'master'
        :return: Element Plus Tree 组件所需的树形结构
        """
        # 获取完整的文件树
        flat_tree = self.get_project_tree_recursive(project_id, ref)

        # 构建路径到节点的映射
        path_to_node = {}

        # 创建根节点
        root = {"label": "/", "children": []}
        path_to_node[""] = root

        # 按路径长度排序，确保父目录先处理
        sorted_items = sorted(flat_tree, key=lambda x: x['path'].count('/'))

        # 处理每个文件和目录
        for item in sorted_items:
            path = item['path']
            name = item['name']
            item_type = item['type']  # 'tree' 或 'blob'

            # 查找父目录路径
            parent_path = '/'.join(path.split('/')[:-1]) if '/' in path else ""

            # 确保父节点存在
            if parent_path not in path_to_node:
                # 创建缺失的中间目录节点
                self._create_missing_parents(path, path_to_node)

            # 创建当前节点
            if item_type == 'tree':  # 目录
                current_node = {"label": name, "children": []}
            else:  # 文件
                current_node = {"label": name, "path": path}

            # 将当前节点添加到父节点的子节点中
            path_to_node[parent_path]["children"].append(current_node)
            path_to_node[path] = current_node

        return root["children"]

    def _create_missing_parents(self, path, path_to_node):
        """
        创建缺失的父级目录节点
        :param path: 当前路径
        :param path_to_node: 路径到节点的映射字典
        """
        parts = path.split('/')
        for i in range(1, len(parts)):
            current_path = '/'.join(parts[:i])
            parent_path = '/'.join(parts[:i - 1]) if i > 1 else ""

            if current_path not in path_to_node:
                dir_name = parts[i - 1] if i > 0 else "/"
                dir_node = {"label": dir_name, "children": []}
                path_to_node[parent_path]["children"].append(dir_node)
                path_to_node[current_path] = dir_node

#
# if __name__ == '__main__':
#     gitlab_client = GitlabAPI(gitlab_url='https://stash.weimob.com', token='BAvpRcRyiT_uztes6W78')
#     default_branch = gitlab_client.get_project_default_branch(12737)
#     print(default_branch)
