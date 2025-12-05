import ast
import base64
import fnmatch
import os
import re

from gitlab import GitlabGetError

from app.case_handler.case_enum import CaseType
from app.case_handler.gitlab_tool import GitlabAPI
from utils.custom_logging import logger


class GitCaseParser:
    def __init__(self, root_path: str):
        self.root_path = root_path

    def get_case_list(self):
        raise NotImplementedError

    @staticmethod
    def generate_case_uuid(workspace_id: int, specific_type: int, case_type: str, git_project_id: int, branch_name: str,
                           case_path: str):
        """
        生成case uuid
        :param specific_type: 测试类型
        :param case_path:用例路径
        :param git_project_id: git项目ID
        :param branch_name: 分支名称
        :param case_type: 用例类型
        :param workspace_id: 用例库ID
        :return: base64编码后的case uuid
        """
        return base64.b64encode(
            f"{workspace_id}\0{specific_type}\0{case_type}\0{git_project_id}\0{branch_name}\0{case_path}".encode(
                "utf-8")).decode("utf-8")

    @staticmethod
    def parse_case_uuid(case_uuid: str):
        """
        解析case uuid
        :param case_uuid:case uuid
        :return:
        """
        decoded_string = base64.b64decode(case_uuid).decode("utf-8")
        workspace_id, specific_type, case_type, git_project_id, branch_name, case_path = tuple(
            decoded_string.split('\0'))
        return {
            'workspace_id': int(workspace_id),
            'specific_type': int(specific_type),
            'case_type': case_type,
            'git_project_id': int(git_project_id),
            'branch_name': branch_name,
            'case_path': case_path
        }

    @staticmethod
    def get_path_parts(full_path, start_part):
        """
        从指定路径开始截取并返回截取后的路径
        :param full_path: 完整路径
        :param start_part: 开始截取的部分
        :return: 截取后的路径
        """
        if '/' in start_part:
            # 例入参: /Users/admin/Documents/code/javaDemo/src/test/java/order/TestAA.java, javaDemo/src/test/java
            # return:  order/TestAA.java
            index = full_path.index(start_part)
            if start_part.endswith('/'):
                return full_path[index + len(start_part):]
            return full_path[index + len(start_part) + 1:]
        else:
            # 例入参: /Users/admin/Documents/code/javaDemo/src/test/java/order/TestAA.java, javaDemo
            # return:  src/test/java/order/TestAA.java
            parts = full_path.split(os.path.sep)
            start_index = parts.index(start_part)
            return os.path.sep.join(parts[start_index:])

    @staticmethod
    def is_python_test_script(filename: str):
        """
        判断是否是python测试脚本
        :return:
        """
        if fnmatch.fnmatch(filename, 'test_*.py') or fnmatch.fnmatch(filename, '_test*.py'):
            return True
        return False

    @staticmethod
    def is_testng_test_script(filename: str):
        """
        判断是否是testng测试脚本
        :return:
        """
        if fnmatch.fnmatch(filename, '*Test.java'):
            return True
        if fnmatch.fnmatch(filename, 'Test*.java'):
            return True
        if fnmatch.fnmatch(filename, '*TestCase.java'):
            return True
        return False

    @staticmethod
    def draw_comment_from_script(content_text: str):
        """
        从脚本中提取注释
        :return: 提取到的脚本注释
        """
        pattern = r'^([\'"]{3})(.*?)\1'
        match = re.search(pattern, content_text, re.DOTALL)
        if match:
            comment = match.group(2)
            return comment
        else:
            return ''

    @staticmethod
    def draw_comment_from_testng_decoration(content_text: str):
        """
        从testng 注解中提取注释
        :return: 提取到的脚本注释
        """
        pattern = r'@Test\(description(.*?)"(.*?)"'
        match = re.search(pattern, content_text, re.DOTALL)
        if match:
            comment = match.group(2)
            return comment
        else:
            return ''

    @staticmethod
    def format_code_comment(comment_text: str, code_type: str = 'pytest'):
        """
        解析格式化代码注释
        :param code_type: 脚本代码类型 pytest/testng
        :param comment_text: 代码注释原始文本
        :return: 格式化后的代码注释
        """

        def parse_pytest_decoration_string(string: str):
            """
            解析pytest注释字符串 并返回格式化的字典
            :param string: 原始注释字符串 形如: "case_desc: 测试发货管理批量发货\n author: pei.li\n level: S1"
            :return: 格式化后的字典
            """
            lines = string.split('\n')
            # 转换为字典
            dict_data = {re.split('[:：]', line)[0].strip(): re.split('[:：]', line)[1].strip() for line in lines if
                         ':' in line or '：' in line}
            return dict_data

        def parse_testng_decorator_string(string: str):
            """
            解析testng注解字符串 并返回格式化的字典
            :param string: 原始注释字符串 形如: "caseDesc: 调试脚本AA; author: baojun.wang; level: P1"
            :return: 格式化后的字典
            """
            # 将冒号和分号替换为英文冒号和分号
            string = string.upper().lower()
            string = string.replace(' ', '').replace('：', ':').replace('，', ',').replace('；', ';').replace('casedesc',
                                                                                                           'case_desc')
            # 将字符串按分号分割成多个部分
            parts = string.split(";")
            # 创建一个字典，将每个部分按冒号分割，并将冒号前的部分作为键，冒号后的部分作为值存储在字典中
            dict_data = {}
            try:
                for part in parts:
                    k, v = part.split(":")
                    dict_data[k] = v
            except Exception as e:
                return dict_data
            return dict_data

        if code_type == 'pytest':
            code_comment_dict = parse_pytest_decoration_string(comment_text)

        elif code_type == 'testng':
            code_comment_dict = parse_testng_decorator_string(comment_text)

        keys = ['level', 'case_desc', 'author']
        for key in keys:
            if key not in list(code_comment_dict.keys()):
                return None
        else:
            level = re.search(r'(\d)', code_comment_dict['level'])  # 检查注释中的用例等级数字是否存在
            if level:
                # 存在 提取
                code_comment_dict['level'] = level[0]
                return code_comment_dict
            else:
                # 不存在 返回None
                return None

    def get_python_script_comment(self, file_absolute_path: str):
        """
        获取python脚本的注释
        :param file_absolute_path: python脚本路径
        :return: 解析后的注释/None
        """
        # 获取测试脚本中的注释
        with open(file_absolute_path, 'r') as file:
            script = file.read()

        comment = self.draw_comment_from_script(content_text=script)
        if not comment:
            logger.error(f'文件: {file_absolute_path} 中没有找到注释')
            return None
        code_comment_dict = self.format_code_comment(comment)
        if code_comment_dict:
            case_info = {
                'case_name': code_comment_dict['case_desc'],
                'case_author': code_comment_dict['author'],
                'case_level': code_comment_dict['level']
            }
            return case_info
        else:
            logger.error(f'文件: {file_absolute_path} case注释格式不正确')
            return None

    def get_testng_script_comment(self, file_absolute_path: str):
        """
        获取testng脚本的注释
        :param file_absolute_path: testng脚本路径
        :return: 解析后的注释/None
        """
        # 获取测试脚本中的注释
        with open(file_absolute_path, 'r') as file:
            script = file.read()

        comment = self.draw_comment_from_testng_decoration(content_text=script)
        if not comment:
            logger.error(f'文件: {file_absolute_path} 中没有找到注释')
            return None
        code_comment_dict = self.format_code_comment(comment_text=comment, code_type='testng')
        if code_comment_dict:
            case_info = {
                'case_name': code_comment_dict['case_desc'],
                'case_author': code_comment_dict['author'],
                'case_level': code_comment_dict['level']
            }
            return case_info
        else:
            logger.error(f'文件: {file_absolute_path} case注释格式不正确')
            return None

    @staticmethod
    def get_package_corresponding_to_the_case_path(case_path: str):
        """
        获取case路径对应的模块
        :param case_path: case路径
        :return: case路径对应的模块
        """
        if case_path.endswith('.py'):
            return case_path.replace('/', '.').replace('.py', '')
        elif case_path.endswith('.java'):
            return case_path.split('/')[-1].replace('.java', '')

    def find_python_test_files(self, directory, case_dir='', include_project_name=False):
        """
        查找测试用例文件
        :param include_project_name: 返回的path以及模快路径包含项目名称
        :param case_dir: 项目下case脚本存放的目录名
        :param directory: 目录路径
        :return: 测试用例文件路径与模块的迭代器
        """
        # 获取项目名称
        project_name = os.path.basename(directory)
        # 遍历目录下的文件
        for root, dirs, files in os.walk(os.path.join(directory, case_dir), topdown=False):
            for basename in files:
                if self.is_python_test_script(filename=basename):  # 匹配python测试用例脚本
                    file_absolute_path = os.path.join(root, basename)  # 脚本绝对路径
                    relative_path = file_absolute_path[
                        file_absolute_path.index(project_name) + len(project_name) + 1:]  # 脚本相对项目路径
                    if include_project_name:
                        project_relative_path = self.get_path_parts(file_absolute_path,
                                                                    project_name)  # 包含项目名称的脚本相对路径
                        package = self.get_package_corresponding_to_the_case_path(
                            case_path=project_relative_path)  # 脚本所在模块
                    else:
                        package = self.get_package_corresponding_to_the_case_path(
                            case_path=relative_path)  # 脚本所在模块
                    yield file_absolute_path, relative_path, package

    def find_testng_test_files(self, directory, case_dir=''):
        """
        查找测试用例文件
        :param case_dir: 项目下case脚本存放的目录名
        :param directory: 目录路径
        :return: 测试用例文件路径与模块的迭代器
        """
        # 获取项目名称
        project_name = os.path.basename(directory)
        # 遍历目录下的文件
        for root, dirs, files in os.walk(os.path.join(directory, case_dir), topdown=False):
            for basename in files:
                if self.is_testng_test_script(filename=basename):  # 匹配testng测试用例脚本
                    file_absolute_path = os.path.join(root, basename)  # 脚本绝对路径
                    relative_path = file_absolute_path[
                        file_absolute_path.index(os.path.join(project_name, 'src/test/java')) + len(
                            project_name) + 1:]  # 脚本相对case_dir的路径

                    project_relative_path = self.get_path_parts(file_absolute_path,
                                                                os.path.join(project_name,
                                                                             case_dir))  # 包含项目名称的脚本相对路径
                    package = self.get_package_corresponding_to_the_case_path(
                        case_path=project_relative_path)  # 脚本所在模块
                    yield file_absolute_path, relative_path, package

    @staticmethod
    def get_python_test_functions_by_context(content_text: str) -> list:
        """
        通过脚本内容获取python脚本的测试方法
        :param content_text: 文本内容
        :return: 测试方法列表
        """
        tree = ast.parse(content_text)  # 解析脚本文件并返回ast对象
        # 遍历脚本中的方法
        functions = [{'function_name': f.name, 'desc': GitCaseParser.format_code_comment(ast.get_docstring(f, True))}
                     for f
                     in tree.body if
                     isinstance(f, ast.FunctionDef) and f.name.startswith('test_')]
        classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
        # 遍历类中的方法
        for class_obj in classes:
            # 遍历类中的方法 并添加到脚本方法列表中
            functions.extend(
                [{'function_name': f.name, 'desc': GitCaseParser.format_code_comment(
                    ast.get_docstring(f, True) if ast.get_docstring(f, True) else '')} for f
                 in
                 class_obj.body if
                 isinstance(f, ast.FunctionDef) and f.name.startswith('test_')])
        return functions

    @staticmethod
    def get_testng_test_functions_by_context(content_text: str) -> list:
        """
        通过脚本内容获取testng脚本的测试方法
        :param content_text: 文本内容
        :return:
        """
        content_text = content_text[content_text.index('public class'):]
        test_methods = re.findall(r'@Test.*?public void (\w+)\(.*?\)', content_text, flags=re.S)
        functions = [{'function_name': f, 'desc': ""} for f in test_methods]
        return functions

    @staticmethod
    def get_python_test_functions_by_filepath(filename: str):
        """
        通过脚本路径获取python脚本的测试方法
        :param filename: python脚本路径
        :return: 测试方法列表
        """
        with open(filename, "r", encoding="utf-8") as source_code:  # 打开脚本文件
            return GitCaseParser.get_python_test_functions_by_context(source_code.read())  # 读取脚本内容并返回测试方法列表

    @staticmethod
    def get_testng_test_functions_by_filepath(filename: str):
        """
        通过脚本路径获取testng测试用例的测试方法
        :param filename:
        :return:
        """
        with open(filename, "r", encoding="utf-8") as source_code:  # 打开脚本文件
            return GitCaseParser.get_testng_test_functions_by_context(source_code.read())


class PytestCaseParser(GitCaseParser):
    """
    webUI case解析器
    """

    @staticmethod
    def is_test_script(filename: str):
        return GitCaseParser.is_python_test_script(filename)

    @staticmethod
    def get_test_functions_by_context(content_text: str) -> list:
        return GitCaseParser.get_python_test_functions_by_context(content_text=content_text)

    def get_case_list(self, case_dir: str = 'case'):
        """
        获取pytest case list(生成器模式)
        """
        # 从指定目录下查找测试用例文件
        for file_absolute_path, relative_path, package in self.find_python_test_files(directory=self.root_path,
                                                                                      case_dir=case_dir,
                                                                                      include_project_name=False):
            # 获取测试脚本中的注释
            case_info_dict = self.get_python_script_comment(file_absolute_path)
            if case_info_dict:
                with open(file_absolute_path, 'r', encoding="utf-8") as file:
                    # 获取测试用例文件中的测试方法
                    case_content = file.read()
                # 获取测试用例文件中的测试方法
                function_list = self.get_python_test_functions_by_filepath(file_absolute_path)
                case_info_dict['case_path'] = relative_path
                case_info_dict['case_package'] = package
                case_info_dict['case_function_list'] = function_list
                yield case_info_dict, case_content


class TestNGCaseParser(GitCaseParser):
    """
    testng类型case的解析器
    """

    @staticmethod
    def is_test_script(filename: str):
        return GitCaseParser.is_testng_test_script(filename)

    @staticmethod
    def draw_comment_from_script(content_text: str):
        """
        从脚本中提取注释
        :param content_text:
        :return:
        """
        return GitCaseParser.draw_comment_from_testng_decoration(content_text=content_text)

    @staticmethod
    def format_code_comment(comment_text: str, code_type: str = 'testng'):
        """
        解析格式化代码注释
        :param code_type: 脚本代码类型 pytest/testng
        :param comment_text: 代码注释原始文本
        :return: 格式化后的代码注释
        """
        return GitCaseParser.format_code_comment(comment_text=comment_text, code_type='testng')

    @staticmethod
    def get_test_functions_by_context(content_text: str) -> list:
        return GitCaseParser.get_testng_test_functions_by_context(content_text=content_text)

    def get_case_list(self, case_dir: str = 'src/test/java'):
        """
        获取testng case list
        """
        # 从指定目录下查找测试用例文件
        for file_absolute_path, relative_path, package in self.find_testng_test_files(directory=self.root_path,
                                                                                      case_dir=case_dir):
            # 获取测试脚本中的注释
            case_info_dict = self.get_testng_script_comment(file_absolute_path)
            if case_info_dict:
                with open(file_absolute_path, 'r', encoding="utf-8") as file:
                    # 获取测试用例文件中的测试方法
                    case_content = file.read()
                function_list = self.get_testng_test_functions_by_filepath(file_absolute_path)
                case_info_dict['case_path'] = relative_path
                case_info_dict['case_package'] = package
                case_info_dict['case_function_list'] = function_list
                yield case_info_dict, case_content
    # 获取测试脚本中的注释


def check_case_source_value(gitlab_url: str, token: str, case_type: str, case_source_value: dict):
    """
    检查用例数据源值是否有效
    :param gitlab_url gitlab服务器地址
    :param token 身份令牌
    :param case_type: 用例类型
    :param case_source_value: 用例源值
    :return: True/False
    """
    if case_type in [CaseType.Pytest.value, CaseType.TestNG.value]:
        # 用例类型为testng或pytest 都通过gitlab托管case
        try:
            git_client = GitlabAPI(gitlab_url, token)
            git_project = git_client.get_project_by_id(case_source_value['projectId'])
            case_project_name = git_project.name
            branch_names = git_client.get_project_branches(project_id=git_project.id)
            if case_source_value['branchName'] not in branch_names:
                # 无效的分支名称 抛出错误
                raise Exception(f"不存在的分支名称: {case_source_value['branchName']}")
        except GitlabGetError:
            # 无效的gitProjectId 返回参数错误报错
            raise Exception(f"无效的gitProjectId: {case_source_value['projectId']}")
    else:
        # 无效的用例类型 返回参数错误报错
        raise Exception("无效的用例类型")
    return case_project_name


if __name__ == '__main__':
    s = TestNGCaseParser('/Users/baojunw/Documents/code/javaDemo').get_case_list()
    for i in s:
        print(i)
