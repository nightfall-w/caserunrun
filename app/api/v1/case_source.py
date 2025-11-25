"""
@FileName：case_source.py
@Description：
@Author：baojun.wang
@Time：2025/10/29 15:55
"""
import copy
import traceback
from collections import Counter

from fastapi import APIRouter, Depends, Request
from gitlab import GitlabAuthenticationError
from requests import ConnectTimeout, ConnectionError
from requests.exceptions import InvalidURL
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.case_handler.case_enum import CaseType
from app.case_handler.case_parser import check_case_source_value
from app.case_handler.case_sync import get_case_model_by_case_type, init_case_project, GitCaseSync
from app.case_handler.gitlab_tool import GitlabAPI
from app.core.auth_middleware import get_current_user
from app.core.database import get_sync_db
from app.core.response import HttpErrcode, api_response
from app.case_source.models import CaseSourceRelationModel, TokenType
from app.case_source.request_models import BindCaseSourceRequest, UpdateCaseSourceRequest, DeleteCaseSourceRequest, \
    CaseSourceListRequest, CheckTokenRequest
from app.setting.controller import SettingCRUD
from app.user.request_models import CurrentUser
from utils.custom_logging import logger

router = APIRouter(prefix="/case_source", tags=["git仓库用例同步"])


@router.post("/checkToken")
def check_token(request: CheckTokenRequest, db: Session = Depends(get_sync_db),
                current_user: CurrentUser = Depends(get_current_user)):
    """
    检查token有效无效
    """
    gitlab_url = request.gitlab_url
    token = request.token
    try:
        current_userinfo = GitlabAPI(gitlab_url=gitlab_url, token=token).get_current_user()
    except GitlabAuthenticationError:
        return api_response(code=HttpErrcode.EXCEPTION, message="无效的PRIVATE_TOKEN")
    except ConnectTimeout:
        return api_response(code=HttpErrcode.EXCEPTION, message="连接超时，GITLAB_API_URL无法连接")
    except ConnectionError:
        return api_response(code=HttpErrcode.EXCEPTION, message="GITLAB_API_URL无效")
    except InvalidURL:
        return api_response(code=HttpErrcode.EXCEPTION, message="GITLAB_API_URL格式错误")
    data = {
        "id": current_userinfo.id,
        "username": current_userinfo.username,
        "name": current_userinfo.name,
        "state": current_userinfo.state,
        "avatar_url": current_userinfo.avatar_url
    }
    return api_response(code=HttpErrcode.SUCCESS, data=data)


@router.post("/bind")
def bind_case_source(request: BindCaseSourceRequest, db: Session = Depends(get_sync_db),
                     current_user: CurrentUser = Depends(get_current_user)):
    """
    绑定用例源
    """
    workspace_id = request.workspaceId
    specific_type = request.specificType
    case_type = request.caseType
    desc = request.desc
    token_type = request.tokenType
    case_source_platform = request.caseSourcePlatform
    case_source_value = request.caseSourceValue

    if not all([workspace_id, specific_type, case_type, case_source_value]):
        return api_response(code=HttpErrcode.PARAMS_MISSING, message="缺少必要参数")

    stmt = select(CaseSourceRelationModel).filter(
        and_(
            CaseSourceRelationModel.workspace_id == workspace_id,
            CaseSourceRelationModel.case_type == case_type,
            CaseSourceRelationModel.specific_type == specific_type,
            CaseSourceRelationModel.case_source_value['projectId'] == case_source_value['projectId']
        )
    )

    # 执行查询
    result = db.execute(stmt)
    # 获取第一条结果
    db_case_relation = result.scalars().first()

    if db_case_relation:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="用例源关系已存在")
    setting_crud = SettingCRUD(db)
    gitlab_url, token = setting_crud.get_gitlab_credentials(token_type=token_type, workspace_id=workspace_id)
    # 检查用例数据源值是否有效
    try:
        case_project_name = check_case_source_value(gitlab_url=gitlab_url, token=token,
                                                    case_type=case_type, case_source_value=case_source_value)
    except Exception as e:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message=f"用例源值无效: {str(e)}")

    # 保存用例源值
    case_source_relation = CaseSourceRelationModel(
        workspace_id=workspace_id,
        case_type=case_type,
        case_source_value=case_source_value,
        case_project_name=case_project_name,
        case_source_platform=case_source_platform,
        token_type=token_type,
        specific_type=specific_type,
        desc=desc,
        create_user=current_user.username,
        update_user=current_user.username
    )
    db.add(case_source_relation)
    db.commit()
    db.refresh(case_source_relation)

    setting_crud = SettingCRUD(db)
    server_domain = setting_crud.get_system_config_by_key("SERVER_DOMAIN").value
    try:
        init_case_project(gitlab_url=gitlab_url, token=token, case_source_relation=case_source_relation)
        if case_source_relation.case_type in [CaseType.Pytest.value, CaseType.TestNG.value]:
            GitlabAPI(gitlab_url=gitlab_url, token=token).create_webhook(
                project_id=case_source_relation.case_source_value['projectId'],
                url=server_domain + '/api/case/GitCaseSync'
            )
    except Exception as e:
        logger.error(f"初始化用例项目失败: {str(traceback.format_exc())}")
        db.delete(case_source_relation)
        db.commit()
        return api_response(code=HttpErrcode.EXCEPTION, message="初始化用例项目失败")

    data = {
        "id": case_source_relation.id,
        "workspaceId": case_source_relation.workspace_id,
        "desc": case_source_relation.desc,
        "caseType": case_source_relation.case_type,
        "caseSourcePlatform": case_source_relation.case_source_platform,
        "caseProjectName": case_source_relation.case_project_name,
        "tokenType": case_source_relation.token_type,
        "specificType": case_source_relation.specific_type,
        "caseSourceValue": case_source_relation.case_source_value,
        "createTime": case_source_relation.create_time,
        "createUser": case_source_relation.create_user,
        "updateTime": case_source_relation.update_time,
        "updateUser": case_source_relation.update_user

    }
    return api_response(code=HttpErrcode.SUCCESS, data=data)


@router.post("/update")
def update_case_source(request: UpdateCaseSourceRequest, db: Session = Depends(get_sync_db),
                       userinfo: CurrentUser = Depends(get_current_user)):
    """
    更新用例源
    """
    source_id = request.id
    workspace_id = request.workspaceId
    specific_type = request.specificType
    case_type = request.caseType
    token_type = request.tokenType
    case_source_platform = request.caseSourcePlatform
    desc = request.desc
    case_source_value = request.caseSourceValue

    if not all([source_id, workspace_id, specific_type, case_type, case_source_value]):
        return api_response(code=HttpErrcode.PARAMS_MISSING, message="缺少必要参数")

    stmt = select(CaseSourceRelationModel).filter(CaseSourceRelationModel.id == source_id)
    result = db.execute(stmt)
    case_source_relation = result.scalars().first()

    if not case_source_relation:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="用例源关系不存在")

    if case_source_relation.case_type == case_type and case_source_relation.specific_type == specific_type and \
            case_source_relation.token_type == token_type and case_source_relation.case_source_platform == \
            case_source_platform and Counter(case_source_relation.case_source_value) == Counter(
        case_source_value) and case_source_relation.desc == desc:
        # 无修改
        pass

    elif case_source_relation.case_type == case_type and case_source_relation.specific_type == specific_type and \
            case_source_relation.token_type == token_type and case_source_relation.case_source_platform == \
            case_source_platform and Counter(case_source_relation.case_source_value) == Counter(
        case_source_value) and case_source_relation.desc != desc:
        # 仅修改描述 仅更新用例源
        case_source_relation.desc = desc
        db.commit()
        db.refresh(case_source_relation)

    else:
        # 需要更新case
        setting_crud = SettingCRUD(db)
        gitlab_url, token = setting_crud.get_gitlab_credentials(token_type=token_type, workspace_id=workspace_id)

        # 检查用例数据源值是否有效
        try:
            case_project_name = check_case_source_value(gitlab_url=gitlab_url, token=token,
                                                        case_type=case_type, case_source_value=case_source_value)
        except Exception as e:
            return api_response(code=HttpErrcode.PARAMS_ERROR, message=f"用例源值无效: {str(e)}")

        for _case_type in (CaseType.Pytest.value, CaseType.TestNG.value):
            # 删除历史数据
            case_model = get_case_model_by_case_type(case_type=_case_type)
            # 修改后
            stmt = select(case_model).filter(
                and_(
                    case_model.workspace_id == workspace_id,
                    case_model.specific_type == case_source_relation.specific_type,
                    case_model.case_type == _case_type,
                    case_model.git_project_id == case_source_relation.case_source_value['projectId']
                )
            )
            result = db.execute(stmt)
            db_case_list = result.scalars().all()

            # 删除历史数据
            for db_case in db_case_list:
                db.delete(db_case)

        # 更新用例源值
        original_case_source_relation = copy.deepcopy(case_source_relation)
        case_source_relation.case_project_name = case_project_name
        case_source_relation.workspace_id = workspace_id
        case_source_relation.case_type = case_type
        case_source_relation.token_type = token_type
        case_source_relation.case_source_platform = case_source_platform
        case_source_relation.specific_type = specific_type
        case_source_relation.case_source_value = case_source_value
        case_source_relation.desc = desc
        case_source_relation.create_user = userinfo.username
        db.commit()
        db.refresh(case_source_relation)

        setting_crud = SettingCRUD(db)
        server_domain = setting_crud.get_system_config_by_key("SERVER_DOMAIN").value

        try:
            init_case_project(gitlab_url=gitlab_url, token=token, case_source_relation=case_source_relation)
            if case_source_relation.case_type in [CaseType.Pytest.value,
                                                  CaseType.TestNG.value]:
                GitlabAPI(gitlab_url=gitlab_url,
                          token=token).create_webhook(
                    project_id=case_source_relation.case_source_value['projectId'],
                    url=server_domain + '/api/case/GitCaseSync'
                )
        except Exception as e:
            logger.error(f"更新用例源后 初始化用例项目失败: {str(e)}")
            # 失败后回滚
            case_source_relation.case_project_name = original_case_source_relation.case_project_name
            case_source_relation.workspace_id = original_case_source_relation.workspace_id
            case_source_relation.case_type = original_case_source_relation.case_type
            case_source_relation.specific_type = original_case_source_relation.specific_type
            case_source_relation.case_source_value = original_case_source_relation.case_source_value
            case_source_relation.desc = original_case_source_relation.desc
            case_source_relation.create_user = original_case_source_relation.create_user
            db.commit()
            db.refresh(case_source_relation)
            return api_response(code=HttpErrcode.EXCEPTION, message="更新用例源后 初始化用例项目失败")

    data = {
        "id": case_source_relation.id,
        "workspaceId": case_source_relation.workspace_id,
        "caseType": case_source_relation.case_type,
        "specificType": case_source_relation.specific_type,
        "caseSourceValue": case_source_relation.case_source_value,
        "caseSourcePlatform": case_source_relation.case_source_platform,
        "caseProjectName": case_source_relation.case_project_name,
        "tokenType": case_source_relation.token_type,
        "desc": case_source_relation.desc,
        "createTime": case_source_relation.create_time,
        "createUser": case_source_relation.create_user,
        "updateTime": case_source_relation.update_time,
        "updateUser": case_source_relation.update_user
    }
    return api_response(code=HttpErrcode.SUCCESS, data=data)


@router.post("/delete")
def delete_case_source(request: DeleteCaseSourceRequest, db: Session = Depends(get_sync_db),
                       current_user: CurrentUser = Depends(get_current_user)):
    """
    删除用例源
    """
    source_id = request.id
    workspace_id = request.workspaceId

    if not all([source_id, workspace_id]):
        return api_response(code=HttpErrcode.PARAMS_MISSING, message="缺少必要参数")
    with db as session:
        # 修改为使用select方式查询
        stmt = select(CaseSourceRelationModel).filter(CaseSourceRelationModel.id == source_id)
        result = session.execute(stmt)
        case_source_relation = result.scalars().first()

        if not case_source_relation:
            return api_response(code=HttpErrcode.PARAMS_ERROR, message="用例源关系不存在")

        # 删除用例源值
        case_model = get_case_model_by_case_type(case_type=case_source_relation.case_type)
        # 修改为使用select方式查询
        stmt = select(case_model).filter(
            and_(
                case_model.workspace_id == workspace_id,
                case_model.specific_type == case_source_relation.specific_type,
                case_model.case_type == case_source_relation.case_type,
                case_model.git_project_id == case_source_relation.case_source_value['projectId']
            )
        )
        result = session.execute(stmt)
        db_case_list = result.scalars().all()  # 获取当前用例库下的所有符合条件的用例

        # 删除本地数据库
        for case_item in db_case_list:
            session.delete(case_item)
        session.commit()
        # 删除用例源关系
        session.delete(case_source_relation)
        session.commit()
        return api_response(code=HttpErrcode.SUCCESS, message="删除成功")


@router.post("/list")
def case_source_list(request: CaseSourceListRequest, db: Session = Depends(get_sync_db),
                     userinfo: CurrentUser = Depends(get_current_user)):
    """
    用例源列表
    """
    workspace_id = request.workspaceId

    stmt = select(CaseSourceRelationModel).filter(
        CaseSourceRelationModel.workspace_id == workspace_id
    )
    result = db.execute(stmt)
    case_source_relation_list = result.scalars().all()

    data = [{
        "id": case_source_relation.id,
        "desc": case_source_relation.desc,
        "workspaceId": case_source_relation.workspace_id,
        "caseType": case_source_relation.case_type,
        "specificType": case_source_relation.specific_type,
        "caseSourceValue": case_source_relation.case_source_value,
        "caseProjectName": case_source_relation.case_project_name,
        "tokenType": case_source_relation.token_type,
        "caseSourcePlatform": case_source_relation.case_source_platform,
        "venvId": case_source_relation.venv_id,
        "venvVersion": case_source_relation.venv_version,
        "createTime": case_source_relation.create_time,
        "createUser": case_source_relation.create_user,
    } for case_source_relation in case_source_relation_list]
    return api_response(code=HttpErrcode.SUCCESS, data=data)


@router.post("/GitCaseSync")
def sync_git_case(data: dict):
    """
    接收gitlab webhook推送的数据 以更新case
    :param data: gitlab webhook推送的数据
    """
    logger.info(f'接收到的gitlab webhook数据：{data}')
    project_id = data['project_id']  # 项目id
    project_name = data['project']['name']  # 项目名称
    if data['object_kind'] == 'push' and data['ref'] in ['refs/heads/master', 'refs/heads/main'] and data['commits']:
        # gitlab推送的是push事件 且推送的是主分支 且推送的是有commit的数据
        GitCaseSync(git_project_id=project_id, git_project_name=project_name, git_commits=data['commits'],
                    git_project_commit_id=data['after']).sync()
        return api_response(data=True, code=HttpErrcode.SUCCESS, message="success")

    else:
        # gitlab推送的不是push事件 或 推送的不是主分支 或 推送的是无commit的数据
        return api_response(data=None, code=HttpErrcode.PARAMS_ERROR, message="非push事件或非master分支或无commit数据")


@router.get("/queryFileContent")
def get_file_content(
        workspace_id: int, git_project_id: int, file_path: str,
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_user)
):
    """
    查询case的详情和内容
    :param workspace_id: get请求中的workspace_id参数
    :param git_project_id: get请求中的git_project_id参数
    :param file_path: get请求中的file_path参数
    :param db: 数据库session
    :param current_user: 验证当前用户的身份信息
    :return:
    """
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
        content = gitlab_client.get_content(project_id=git_project_id,
                                            file_path=file_path)
        return api_response(
            data={
                "content": content
            }
        )
    return api_response(code=HttpErrcode.NOT_FOUND, message="未找到文件")
