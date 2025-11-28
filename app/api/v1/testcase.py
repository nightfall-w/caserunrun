"""
@FileName：testcase.py
@Description：
@Author：baojun.wang
@Time：2025/11/9 23:08
"""
import traceback

from fastapi import APIRouter, Depends
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.case_handler.case_parser import GitCaseParser
from app.case_handler.gitlab_tool import GitlabAPI
from app.case_handler.models import PytestCaseModel, TestNGCaseModel
from app.case_handler.requests_models import TestCaseListRequest
from app.case_source.models import CaseSourceRelationModel
from app.core.auth_middleware import get_current_user
from app.core.database import get_sync_db
from app.core.response import HttpErrcode, api_response
from app.setting.controller import SettingCRUD
from app.user.controller import get_nickname_by_username
from app.user.request_models import CurrentUser
from utils.custom_logging import logger

router = APIRouter(prefix="/testcase", tags=["测试用例管理"])


@router.post("/list")
def get_testcase_list(
        request: TestCaseListRequest,
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_user)
):
    """
    获取测试用例
    """
    try:
        # 构建查询条件
        filters = [PytestCaseModel.workspace_id == request.workspace_id]

        # 添加可选的过滤条件
        if request.git_project_id:
            filters.append(PytestCaseModel.git_project_id == request.git_project_id)

        if request.case_type:
            filters.append(PytestCaseModel.case_type == request.case_type)

        if request.specific_type:
            filters.append(PytestCaseModel.specific_type == request.specific_type)

        if request.case_level is not None:
            filters.append(PytestCaseModel.case_level == request.case_level)

        if request.case_name:
            filters.append(PytestCaseModel.case_name.contains(request.case_name))

        if request.case_author:
            filters.append(PytestCaseModel.case_author.contains(request.case_author))

        if request.case_path:
            filters.append(PytestCaseModel.case_path.contains(request.case_path))

        # 构建Pytest查询
        pytest_query = db.query(PytestCaseModel).filter(and_(*filters))

        # 构建TestNG查询，使用相同的过滤条件但针对TestNG模型
        testng_filters = []
        for f in filters:
            # 将Pytest模型的过滤条件转换为TestNG模型的过滤条件
            if hasattr(f.left, 'name') and f.left.name == 'workspace_id':
                testng_filters.append(TestNGCaseModel.workspace_id == f.right.value)
            elif hasattr(f.left, 'name') and f.left.name == 'git_project_id':
                testng_filters.append(TestNGCaseModel.git_project_id == f.right.value)
            elif hasattr(f.left, 'name') and f.left.name == 'case_type':
                testng_filters.append(TestNGCaseModel.case_type == f.right.value)
            elif hasattr(f.left, 'name') and f.left.name == 'specific_type':
                testng_filters.append(TestNGCaseModel.specific_type == f.right.value)
            elif hasattr(f.left, 'name') and f.left.name == 'case_level':
                testng_filters.append(TestNGCaseModel.case_level == f.right.value)
            elif hasattr(f.left, 'name') and f.left.name == 'case_name':
                testng_filters.append(TestNGCaseModel.case_name.contains(f.right.value))
            elif hasattr(f.left, 'name') and f.left.name == 'case_author':
                testng_filters.append(TestNGCaseModel.case_author.contains(f.right.value))

        testng_query = db.query(TestNGCaseModel).filter(and_(*testng_filters))

        # 执行查询并获取结果
        pytest_results = pytest_query.all()
        testng_results = testng_query.all()

        # 合并结果
        all_results = pytest_results + testng_results

        # 应用分页
        start_index = (request.page_num - 1) * request.page_size
        end_index = start_index + request.page_size
        paginated_results = all_results[start_index:end_index]

        def format_item(item):
            return {
                "id": item.id,
                "workspace_id": item.workspace_id,
                "specific_type": item.specific_type,
                "case_type": item.case_type,
                "case_source_value": item.case_source_value,
                "git_project_id": item.git_project_id,
                "git_project_name": item.git_project_name,
                "git_project_commit_id": item.git_project_commit_id,
                "case_commit_id": item.case_commit_id,
                "case_uuid": item.case_uuid,
                "case_name": item.case_name,
                "case_function_list": item.case_function_list,
                "case_path": item.case_path,
                "case_package": item.case_package,
                "case_author": {"username": item.case_author,
                                "nickname": get_nickname_by_username(db=db, username=item.case_author)},
                "case_level": item.case_level,
                "create_time": item.create_time,
                "update_time": item.update_time
            }

        # 返回结果
        return api_response(
            data={
                "items": [format_item(item) for item in paginated_results],
                "total": len(all_results)
            }
        )
    except Exception as e:
        logger.error(f"获取测试用例列表失败: {str(e)}, traceback: {traceback.format_exc()}")
        return api_response(code=HttpErrcode.EXCEPTION, message="获取用例列表失败！")


@router.get("/queryCaseContentDetail")
def get_testcase_content_detail(
        case_uuid: str, case_commit_id: str,
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_user)
):
    """
    查询case的详情和内容
    :param case_uuid: get请求中的case_uuid参数
    :param case_commit_id: get请求中的case_commit_id参数
    :param db: 数据库session
    :param current_user: 验证当前用户的身份信息
    :return:
    """
    try:
        case_info = GitCaseParser.parse_case_uuid(case_uuid=case_uuid)
    except Exception:
        logger.error(f"解析case_uuid失败: {traceback.format_exc()}")
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="解析case_uuid失败！请检查case_uuid是否正确")
    workspace_id = case_info["workspace_id"]
    git_project_id = case_info["git_project_id"]
    case_path = case_info["case_path"]
    branch_name = case_info["branch_name"]
    # 查询匹配的记录
    stmt = select(CaseSourceRelationModel).where(
        and_(
            CaseSourceRelationModel.workspace_id == workspace_id,
            CaseSourceRelationModel.case_source_value['projectId'] == git_project_id
        )
    )
    result = db.execute(stmt)
    case_source = result.scalars().first()
    # 如果需要使用case_source进行后续操作
    if case_source:
        setting_crud = SettingCRUD(db)
        gitlab_url, token = setting_crud.get_gitlab_credentials(token_type=case_source.token_type,
                                                                workspace_id=workspace_id)
        gitlab_client = GitlabAPI(gitlab_url=gitlab_url, token=token)
        case_content = gitlab_client.get_content(project_id=git_project_id,
                                                 file_path=case_path, ref=branch_name)
        return api_response(
            data={
                "case_content": case_content,
                "case_commit_id": case_commit_id
            }
        )
    return api_response(code=HttpErrcode.NOT_FOUND, message="未找到匹配的用例数据")


@router.get("/getProjectFileTree")
def get_project_file_tree(workspace_id: int, git_project_id: int, branch_name: str, db: Session = Depends(get_sync_db)):
    """
    获取项目文件树
    :param db: 数据库session
    :param workspace_id: 工作空间id
    :param branch_name: 分支
    :param git_project_id: git项目id
    :return:
    """
    # 查询匹配的记录
    stmt = select(CaseSourceRelationModel).where(
        and_(
            CaseSourceRelationModel.workspace_id == workspace_id,
            CaseSourceRelationModel.case_source_value['projectId'] == git_project_id,
            CaseSourceRelationModel.case_source_value['branchName'] == branch_name
        )
    )
    result = db.execute(stmt)
    case_source = result.scalars().first()
    # 如果需要使用case_source进行后续操作
    if case_source:
        setting_crud = SettingCRUD(db)
        gitlab_url, token = setting_crud.get_gitlab_credentials(token_type=case_source.token_type,
                                                                workspace_id=workspace_id)
        gitlab_client = GitlabAPI(gitlab_url=gitlab_url, token=token)
        result = gitlab_client.get_project_tree_as_element_ui_format(project_id=git_project_id, ref=branch_name)
        return api_response(data=result)
    return api_response(code=HttpErrcode.NOT_FOUND, message="未找到匹配的用例源数据")
