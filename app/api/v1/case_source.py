"""
@FileName：case_source.py
@Description：
@Author：baojun.wang
@Time：2025/10/29 15:55
"""
import copy
import traceback

from fastapi import APIRouter, Depends
from gitlab import GitlabAuthenticationError, GitlabGetError
from requests import ConnectTimeout, ConnectionError
from requests.exceptions import InvalidURL
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.case_handler.case_parser import check_case_source_value
from app.case_handler.case_sync import get_case_model_by_case_type, init_case_project, GitCaseSync
from app.case_handler.gitlab_tool import GitlabAPI
from app.case_source.models import CaseSourceRelationModel
from app.case_source.request_models import BindCaseSourceRequest, UpdateCaseSourceRequest, DeleteCaseSourceRequest, \
    CaseSourceListRequest, CheckTokenRequest
from app.core.auth_middleware import get_current_user
from app.core.database import get_sync_db
from app.core.response import HttpErrcode, api_response
from app.setting.controller import SettingCRUD
from app.testplan.models import CaseType
from app.testplan.controller import get_test_plan_crud
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
    origin = request.headers.get("origin")
    logger.info(f"origin:{origin}")

    if not all([workspace_id, specific_type, case_type, case_source_value]):
        return api_response(code=HttpErrcode.PARAMS_MISSING, message="缺少必要参数")

    stmt = select(CaseSourceRelationModel).filter(
        and_(
            CaseSourceRelationModel.workspace_id == workspace_id,
            CaseSourceRelationModel.case_type == case_type,
            CaseSourceRelationModel.specific_type == specific_type,
            CaseSourceRelationModel.case_source_value['projectId'] == case_source_value['projectId'],
            CaseSourceRelationModel.case_source_value['branchName'] == case_source_value['branchName']
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

    try:
        init_case_project(gitlab_url=gitlab_url, token=token, case_source_relation=case_source_relation)
        if case_source_relation.case_type in [CaseType.PYTEST, CaseType.TESTNG]:
            GitlabAPI(gitlab_url=gitlab_url, token=token).create_webhook(
                project_id=case_source_relation.case_source_value['projectId'],
                url=origin + '/api/case/GitCaseSync'
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
    更新用例源 - 只允许修改特定字段
    """
    source_id = request.id
    workspace_id = request.workspaceId

    if not all([source_id, workspace_id]):
        return api_response(code=HttpErrcode.PARAMS_MISSING, message="缺少必要参数")

    stmt = select(CaseSourceRelationModel).filter(CaseSourceRelationModel.id == source_id)
    result = db.execute(stmt)
    case_source_relation = result.scalars().first()

    if not case_source_relation:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="用例源关系不存在")

    # 检查是否有不允许修改的字段变更
    if (hasattr(request, 'caseType') and request.caseType != case_source_relation.case_type) or \
            (hasattr(request,
                     'caseSourcePlatform') and request.caseSourcePlatform != case_source_relation.case_source_platform):
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="不允许修改caseType或caseSourcePlatform字段")

    # 判断各字段是否发生变化
    desc_changed = hasattr(request, 'desc') and request.desc != case_source_relation.desc
    token_type_changed = hasattr(request, 'tokenType') and request.tokenType != case_source_relation.token_type
    specific_type_changed = hasattr(request,
                                    'specificType') and request.specificType != case_source_relation.specific_type

    # 检查caseDir是否变更
    case_dir_changed = False
    new_case_dir = None
    if hasattr(request, 'caseSourceValue') and 'caseDir' in request.caseSourceValue:
        current_case_dir = case_source_relation.case_source_value.get('caseDir')
        if request.caseSourceValue['caseDir'] != current_case_dir:
            case_dir_changed = True
            new_case_dir = request.caseSourceValue['caseDir']

    # 如果没有变更，则直接返回
    if not (desc_changed or token_type_changed or specific_type_changed or case_dir_changed):
        # 无修改
        pass
    else:
        # 需要执行更新操作
        original_case_source_relation = copy.deepcopy(case_source_relation)

        try:
            # 如果token_type变更，需要验证新的token_type是否有效
            if token_type_changed:
                setting_crud = SettingCRUD(db)
                new_gitlab_url, new_token = setting_crud.get_gitlab_credentials(
                    token_type=request.tokenType,
                    workspace_id=workspace_id
                )

                # 验证新token是否有权限访问该项目
                try:
                    gitlab_api = GitlabAPI(gitlab_url=new_gitlab_url, token=new_token)
                    gitlab_api.get_project_by_id(id=case_source_relation.case_source_value['projectId'])
                except Exception as e:
                    return api_response(
                        code=HttpErrcode.PARAMS_ERROR,
                        message=f"新token_type无权访问项目: {str(e)}"
                    )

            # 如果caseDir变更，需要重新拉取代码
            if case_dir_changed:
                # 更新case_source_value中的caseDir
                new_case_source_value = case_source_relation.case_source_value.copy()
                new_case_source_value['caseDir'] = new_case_dir

                # 如果caseDir变更，更新case_source_value并重新同步项目
                case_source_relation.case_source_value = new_case_source_value

                # 获取gitlab凭证
                setting_crud = SettingCRUD(db)
                gitlab_url, token = setting_crud.get_gitlab_credentials(
                    token_type=request.tokenType or case_source_relation.token_type,
                    workspace_id=workspace_id
                )

                # 重新初始化项目
                init_case_project(
                    gitlab_url=gitlab_url,
                    token=token,
                    case_source_relation=case_source_relation
                )

                # 如果specific_type也发生了变化，在重新同步后更新它
                if specific_type_changed:
                    case_source_relation.specific_type = request.specificType

            else:
                # caseDir未变更的情况
                # 如果只有specific_type变更，只需要更新数据库中的specific_type字段
                if specific_type_changed:
                    case_source_relation.specific_type = request.specificType

                    # 更新存量case的specific_type字段
                    case_model = get_case_model_by_case_type(case_type=case_source_relation.case_type)
                    stmt = select(case_model).filter(
                        and_(
                            case_model.workspace_id == workspace_id,
                            case_model.specific_type == original_case_source_relation.specific_type,
                            case_model.case_type == case_source_relation.case_type,
                            case_model.git_project_id == case_source_relation.case_source_value['projectId'],
                            case_model.branch_name == case_source_relation.case_source_value['branchName']
                        )
                    )
                    result = db.execute(stmt)
                    db_case_list = result.scalars().all()

                    for db_case in db_case_list:
                        db_case.specific_type = request.specificType

                    db.commit()

            # 更新其他可修改字段
            if token_type_changed:
                case_source_relation.token_type = request.tokenType

            if desc_changed:
                case_source_relation.desc = request.desc

            # 更新用户信息
            case_source_relation.update_user = userinfo.username

            # 提交更改
            db.commit()
            db.refresh(case_source_relation)

        except Exception as e:
            logger.error(f"更新用例源失败: {str(e)}")
            # 回滚更改
            db.rollback()
            return api_response(code=HttpErrcode.EXCEPTION, message=f"更新用例源失败: {str(e)}")

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
                case_model.git_project_id == case_source_relation.case_source_value['projectId'],
                case_model.branch_name == case_source_relation.case_source_value['branchName']
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

        testplan_crud = get_test_plan_crud(db=session)
        testplan_crud.update_workspace_plan_case_status(workspace_id=workspace_id,
                                                        case_type=case_source_relation.case_type)
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
    if data['object_kind'] == 'push' and data['commits']:
        # gitlab推送的是push事件 且推送的是主分支 且推送的是有commit的数据
        GitCaseSync(git_project_id=project_id, git_project_name=project_name, git_commits=data['commits'],
                    git_project_commit_id=data['after'], branch_name=data['ref'].split('/')[-1]).sync()
        return api_response(data=True, code=HttpErrcode.SUCCESS, message="success")

    else:
        # gitlab推送的不是push事件 或 推送的不是主分支 或 推送的是无commit的数据
        return api_response(data=None, code=HttpErrcode.PARAMS_ERROR, message="非push事件或非master分支或无commit数据")


@router.get("/queryFileContent")
def get_file_content(
        workspace_id: int, git_project_id: int, file_path: str, branch_name: str,
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_user)
):
    """
    查询case的详情和内容
    :param workspace_id: get请求中的workspace_id参数
    :param git_project_id: get请求中的git_project_id参数
    :param file_path: get请求中的file_path参数
    :param branch_name: 分支名称
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
                                            file_path=file_path, ref=branch_name)
        return api_response(
            data={
                "content": content
            }
        )
    return api_response(code=HttpErrcode.NOT_FOUND, message="未找到文件")


@router.get("/getProjectBranches")
def get_project_branches(workspace_id: int, git_project_id: int, token_type: str,
                         db: Session = Depends(get_sync_db),
                         current_user: CurrentUser = Depends(get_current_user)
                         ):
    """
    获取项目分支列表
    """
    setting_crud = SettingCRUD(db)
    gitlab_url, token = setting_crud.get_gitlab_credentials(token_type=token_type, workspace_id=workspace_id)
    gitlab_client = GitlabAPI(gitlab_url=gitlab_url, token=token)
    try:
        return api_response(data=gitlab_client.get_project_branches(project_id=git_project_id))
    except Exception as e:
        if isinstance(e, GitlabGetError) and e.response_code == 404:
            return api_response(code=HttpErrcode.NOT_FOUND,
                                message=f"当前凭证权限下不存在ID为:{git_project_id}的项目，请您确认项目ID是否正确")
        logger.error(f"获取项目分支列表失败: {traceback.format_exc()}")
        return api_response(code=HttpErrcode.EXCEPTION, message="获取项目分支列表异常，请检查项目ID与凭证是否有效")
