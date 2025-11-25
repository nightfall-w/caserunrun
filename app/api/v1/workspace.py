"""
@FileName：routes.py
@Description：工作空间相关API路由
@Author：baojun.wang
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth_middleware import get_current_user
from app.core.database import get_sync_db
from app.core.response import api_response, HttpErrcode
from app.user.controller import get_user_by_username
from app.user.request_models import CurrentUser
from app.workspace.controller import get_workspace_crud, WorkspaceCRUD
from app.workspace.models import MemberRole
from app.workspace.request_models import (
    CreateWorkspaceRequest, UpdateWorkspaceRequest,
    CreateMemberRoleRequest, UpdateMemberRoleRequest,
    AddMemberRequest, UpdateMemberRequest,
    WorkspaceListRequest, MemberListRequest, DeleteMemberRoleRequest, DetailsWorkspaceRequest
)

router = APIRouter(prefix="/workspace", tags=["工作空间管理"])


@router.post("/create")
def create_workspace(
        request: CreateWorkspaceRequest,
        db: Session = Depends(get_sync_db),
        userinfo: CurrentUser = Depends(get_current_user)
):
    """创建工作空间"""
    crud = get_workspace_crud(db)
    workspace = crud.create_workspace(
        workspace_name=request.workspace_name,
        workspace_desc=request.workspace_desc,
        create_user=userinfo.username,
        update_user=userinfo.username,
        manager=request.manager
    )

    if not workspace:
        return api_response(code=HttpErrcode.EXCEPTION, message="创建工作空间失败")

    admin_role = crud.get_role_by_role_name(role_name=MemberRole.ADMIN)
    # 将管理员添加到工作空间中
    try:
        for username in request.manager:
            crud.add_member_to_workspace(
                workspace_id=workspace.workspace_id,
                username=username,
                role_id=admin_role.role_id,
            )
    except Exception as e:
        return api_response(code=HttpErrcode.EXCEPTION, message=str(e))

    # 添加系统默认配置项
    from app.setting.controller import get_setting_crud
    setting_crud = get_setting_crud(db)

    # 添加GITLAB_API_URL配置项
    gitlab_api_url_config = setting_crud.get_system_config_by_key("GITLAB_API_URL")
    if not gitlab_api_url_config:
        setting_crud.create_system_config(
            key="GITLAB_API_URL",
            value="https://stash.yourgitlab.com",
            desc="gitlab的服务器地址，一般就是您访问gitlab的仓库的域名。如：https://company.pms.com 或者 https://10.20.3.12:8080之类的形式，只需要到域名或者ip+端口，不要加path",
            type="STRING",
            allowed_to_delete=False,
            required=True
        )

    # 添加PRIVATE_TOKEN配置项
    private_token_config = setting_crud.get_system_config_by_key("PRIVATE_TOKEN")
    if not private_token_config:
        setting_crud.create_system_config(
            key="PRIVATE_TOKEN",
            value="glpat-8aB3cD7eF9gH2jK4lM6nP8qR0(这只是一个示例)",
            desc="您代码仓账号的身份令牌，获取方式：https://docs.qq.com/aio/p/sc506mfg1wd0hc6?p=5sZDIuY3bphvGgshkGkA95",
            type="STRING",
            allowed_to_delete=False,
            required=True
        )

    return api_response(
        code=HttpErrcode.SUCCESS,
        data={
            "workspace_id": workspace.workspace_id,
            "workspace_name": workspace.workspace_name,
            "workspace_desc": workspace.workspace_desc,
            "create_user": workspace.create_user,
            "manager": workspace.manager,
            "create_time": workspace.create_time
        }
    )


@router.get("/detail")
def get_workspace_detail(
        workspace_id: int,
        db: Session = Depends(get_sync_db),
        userinfo: CurrentUser = Depends(get_current_user)
):
    """获取工作空间详情"""
    crud = get_workspace_crud(db)
    workspace = crud.get_workspace_by_id(workspace_id)

    if not workspace:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="工作空间不存在")
    manager_list = []
    for manager_username in workspace.manager:
        manager_userinfo = get_user_by_username(db, manager_username)
        if manager_userinfo:
            manager_list.append({
                "username": manager_userinfo.username,
                "nickname": manager_userinfo.nickname,
                "email": manager_userinfo.email
            })
    data = {
        "workspace_id": workspace.workspace_id,
        "workspace_name": workspace.workspace_name,
        "workspace_desc": workspace.workspace_desc,
        "create_user": workspace.create_user,
        "update_user": workspace.update_user,
        "manager_info_list": manager_list,
    }
    return api_response(
        code=HttpErrcode.SUCCESS,
        data=data
    )


@router.put("/update")
def update_workspace(
        request: UpdateWorkspaceRequest,
        db: Session = Depends(get_sync_db),
        userinfo: CurrentUser = Depends(get_current_user),
):
    """更新工作空间"""
    crud = get_workspace_crud(db)
    # 检查工作空间是否存在
    workspace = crud.get_workspace_by_id(request.workspace_id)
    if not workspace:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="工作空间不存在")

    admin_role = crud.get_role_by_role_name(role_name=MemberRole.ADMIN)
    member = crud.get_member_by_username_and_workspace(username=userinfo.username, workspace_id=request.workspace_id)
    if not member:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="您不是工作空间成员")
    if member.role_id != admin_role.role_id:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="您没有权限修改此工作空间")

    current_mangers = [manager for manager in workspace.manager]
    new_managers = [manager for manager in request.manager]
    # 获取新增的管理员
    new_managers_set = list(set(new_managers) - set(current_mangers))
    # 更新成为管理员的成员的角色
    admin_role = crud.get_role_by_role_name(role_name=MemberRole.ADMIN)
    for manager_username in new_managers_set:
        member = crud.get_member_by_username_and_workspace(username=manager_username, workspace_id=request.workspace_id)
        if member:
            crud.update_member(member_id=member.id, role_id=admin_role.role_id)
        else:
            try:
                crud.add_member_to_workspace(
                    workspace_id=request.workspace_id,
                    username=manager_username,
                    role_id=admin_role.role_id
                )
            except Exception as e:
                return api_response(code=HttpErrcode.EXCEPTION, message=str(e))
    # 获取被删除的管理员
    delete_managers = list(set(current_mangers) - set(new_managers))

    # 处理被删除的管理员（根据delete_manager_info_list决定是删除还是降级）
    delete_manager_info_dict = {}
    if request.delete_manager_info_list:
        delete_manager_info_dict = {item["username"]: item["role_id"] for item in request.delete_manager_info_list}

    for manager_username in delete_managers:
        member = crud.get_member_by_username_and_workspace(username=manager_username, workspace_id=request.workspace_id)
        if member:
            # 如果在delete_manager_info_list中有指定role_id，则降级到指定角色，否则直接删除
            if manager_username in delete_manager_info_dict and delete_manager_info_dict[manager_username] is not None:
                # 降级到指定角色
                crud.update_member(member_id=member.id, role_id=delete_manager_info_dict[manager_username])
            else:
                # 删除成员
                crud.remove_member_from_workspace(member_id=member.id)

    success = crud.update_workspace(
        workspace_id=request.workspace_id,
        workspace_name=request.workspace_name,
        workspace_desc=request.workspace_desc,
        update_user=userinfo.username,
        manager=request.manager
    )

    if not success:
        return api_response(code=HttpErrcode.EXCEPTION, message="更新工作空间失败")

    return api_response(code=HttpErrcode.SUCCESS, message="更新成功")


@router.delete("/delete")
def delete_workspace(
        workspace_id: int,
        db: Session = Depends(get_sync_db),
        userinfo: CurrentUser = Depends(get_current_user)
):
    """删除工作空间"""
    crud = get_workspace_crud(db)
    # 检查工作空间是否存在
    workspace = crud.get_workspace_by_id(workspace_id)
    if not workspace:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="工作空间不存在")

    admin_role = crud.get_role_by_role_name(role_name=MemberRole.ADMIN)
    member = crud.get_member_by_username_and_workspace(username=userinfo.username, workspace_id=workspace_id)
    if not member:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="您不是工作空间成员")
    if member.role_id != admin_role.role_id:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="您没有权限删除此工作空间")

    success = crud.delete_workspace(workspace_id)
    if not success:
        return api_response(code=HttpErrcode.EXCEPTION, message="删除工作空间失败")

    return api_response(code=HttpErrcode.SUCCESS, message="删除成功")


@router.post("/my/manage/list")
def list_workspaces(
        request: WorkspaceListRequest,
        db: Session = Depends(get_sync_db),
        userinfo: CurrentUser = Depends(get_current_user)):
    """
    获取我管理的工作空间列表
    """
    crud = get_workspace_crud(db)
    limit = request.page_size
    offset = (request.page_num - 1) * request.page_size
    workspaces, total = crud.get_my_manager_workspaces_with_count(
        username=userinfo.username,
        workspace_name=request.workspace_name,
        limit=limit,
        offset=offset
    )

    data = dict()
    data["workspaces"] = list()
    data["total"] = total
    for ws in workspaces:
        manager = []
        for manager_username in ws.manager:
            manager_userinfo = get_user_by_username(db, manager_username)
            if manager_userinfo:
                manager.append({
                    "username": manager_userinfo.username,
                    "nickname": manager_userinfo.nickname,
                    "email": manager_userinfo.email
                })
        data["workspaces"].append({
            "workspace_id": ws.workspace_id,
            "workspace_name": ws.workspace_name,
            "workspace_desc": ws.workspace_desc,
            "create_time": ws.create_time,
            "update_time": ws.update_time,
            "manager": manager
        })

    return api_response(code=HttpErrcode.SUCCESS, data=data)


@router.post("/my/list")
def list_my_workspaces(
        request: WorkspaceListRequest,
        db: Session = Depends(get_sync_db),
        userinfo: CurrentUser = Depends(get_current_user)
):
    """获取我所在的工作空间列表"""
    crud = get_workspace_crud(db)
    limit = request.page_size
    offset = (request.page_num - 1) * request.page_size
    workspaces, total = crud.get_my_workspaces_with_count(
        username=userinfo.username,
        workspace_name=request.workspace_name,
        limit=limit,
        offset=offset
    )

    data = dict()
    data["workspaces"] = list()
    data["total"] = total
    for ws in workspaces:
        manager = []
        for manager_username in ws.manager:
            manager_userinfo = get_user_by_username(db, manager_username)
            if manager_userinfo:
                manager.append({
                    "username": manager_userinfo.username,
                    "nickname": manager_userinfo.nickname,
                    "email": manager_userinfo.email
                })
        data["workspaces"].append({
            "workspace_id": ws.workspace_id,
            "workspace_name": ws.workspace_name,
            "workspace_desc": ws.workspace_desc,
            "create_time": ws.create_time,
            "update_time": ws.update_time,
            "manager": manager
        })

    return api_response(code=HttpErrcode.SUCCESS, data=data)


@router.post("/not-my/list")
def list_not_my_workspaces(
        request: WorkspaceListRequest,
        db: Session = Depends(get_sync_db),
        userinfo: CurrentUser = Depends(get_current_user)
):
    """获取我不在的工作空间列表"""
    crud = get_workspace_crud(db)
    limit = request.page_size
    offset = (request.page_num - 1) * request.page_size
    workspaces, total = crud.get_not_my_workspaces_with_count(
        username=userinfo.username,
        workspace_name=request.workspace_name,
        limit=limit,
        offset=offset
    )

    data = dict()
    data["workspaces"] = list()
    data["total"] = total
    for ws in workspaces:
        manager = []
        for manager_username in ws.manager:
            manager_userinfo = get_user_by_username(db, manager_username)
            if manager_userinfo:
                manager.append({
                    "username": manager_userinfo.username,
                    "nickname": manager_userinfo.nickname,
                    "email": manager_userinfo.email
                })
        data["workspaces"].append({
            "workspace_id": ws.workspace_id,
            "workspace_name": ws.workspace_name,
            "workspace_desc": ws.workspace_desc,
            "create_time": ws.create_time,
            "update_time": ws.update_time,
            "manager": manager
        })

    return api_response(code=HttpErrcode.SUCCESS, data=data)


# 角色相关接口
@router.post("/role/create")
def create_role(
        request: CreateMemberRoleRequest,
        db: Session = Depends(get_sync_db)
):
    """创建角色"""
    crud = get_workspace_crud(db)

    role = crud.create_member_role(
        role_name=request.role_name,
        role_description=request.role_description
    )

    if not role:
        return api_response(code=HttpErrcode.EXCEPTION, message="创建角色失败")

    return api_response(
        code=HttpErrcode.SUCCESS,
        data={
            "role_id": role.role_id,
            "role_name": role.role_name,
            "role_description": role.role_description
        }
    )


@router.get("/role/list")
def list_roles(db: Session = Depends(get_sync_db), userinfo: CurrentUser = Depends(get_current_user)):
    """获取角色列表"""
    crud = get_workspace_crud(db)
    roles = crud.get_all_roles()

    data = [
        {
            "role_id": role.role_id,
            "role_name": role.role_name,
            "role_description": role.role_description
        }
        for role in roles
    ]

    return api_response(code=HttpErrcode.SUCCESS, data=data)


@router.put("/role/update")
def update_role(
        request: UpdateMemberRoleRequest,
        db: Session = Depends(get_sync_db)
):
    """更新角色"""
    crud = get_workspace_crud(db)
    role_id = request.role_id
    # 检查角色是否存在
    role = crud.get_role_by_id(role_id)
    if not role:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="角色不存在")

    success = crud.update_role(
        role_id=role_id,
        role_name=request.role_name,
        role_description=request.role_description
    )

    if not success:
        return api_response(code=HttpErrcode.EXCEPTION, message="更新角色失败")

    return api_response(code=HttpErrcode.SUCCESS, message="更新成功")


@router.delete("/role/delete")
def delete_role(
        request: DeleteMemberRoleRequest,
        db: Session = Depends(get_sync_db)
):
    """删除角色"""
    crud = get_workspace_crud(db)
    role_id = request.role_id
    # 检查角色是否存在
    role = crud.get_role_by_id(role_id)
    if not role:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="角色不存在")

    success = crud.delete_role(role_id)
    if not success:
        return api_response(code=HttpErrcode.EXCEPTION, message="删除角色失败，可能仍有成员使用该角色")

    return api_response(code=HttpErrcode.SUCCESS, message="删除成功")


# 成员相关接口
@router.post("/member/join")
def member_join_workspace(
        request: AddMemberRequest,
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_user)
):
    """添加成员到工作空间"""
    crud = get_workspace_crud(db)
    try:
        member = crud.add_member_to_workspace(
            workspace_id=request.workspace_id,
            username=current_user.username,
            role_id=request.role_id
        )
    except Exception as e:
        return api_response(code=HttpErrcode.EXCEPTION, message=str(e))

    if not member:
        return api_response(code=HttpErrcode.EXCEPTION, message="添加成员失败")

    return api_response(
        code=HttpErrcode.SUCCESS,
        data={
            "member_id": member.id,
            "workspace_id": member.workspace_id,
            "role_id": member.role_id,
            "join_time": member.join_time
        }
    )


@router.get("/member/detail/")
def get_workspace_member_by_username(workspace_id: int, username: str, db: Session = Depends(get_sync_db)):
    """根据用户名获取工作空间成员"""
    if not workspace_id:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="参数错误")
    if not username:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="参数错误")
    crud = get_workspace_crud(db)
    member = crud.get_member_by_username_and_workspace(username, workspace_id)
    if not member:
        data = None
        return api_response(code=HttpErrcode.SUCCESS, data=data)
    data = {
        "member_id": member.id,
        "username": member.username,
        "role_id": member.role_id,
        "join_time": member.join_time,
    }
    return api_response(code=HttpErrcode.SUCCESS, data=data)


@router.get("/member/list/")
def list_members(
        request: MemberListRequest,
        db: Session = Depends(get_sync_db)
):
    """获取工作空间成员列表"""
    crud = get_workspace_crud(db)
    workspace_id = request.workspace_id
    limit = request.page_size
    offset = (request.page_num - 1) * limit
    # 检查工作空间是否存在
    workspace = crud.get_workspace_by_id(workspace_id)
    if not workspace:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="工作空间不存在")

    members, total_count = crud.get_members_by_workspace_with_count(workspace_id, limit, offset)

    # 获取详细信息
    member_details = []
    for member in members:
        role = crud.get_role_by_id(member.role_id)
        member_details.append({
            "member_id": member.id,
            "member_info": member.member_info,
            "role": {
                "role_id": role.role_id if role else None,
                "role_name": role.role_name if role else None
            },
            "join_time": member.join_time
        })

    return api_response(code=HttpErrcode.SUCCESS, data=member_details)


@router.put("/member/update")
def update_member(
        request: UpdateMemberRequest,
        db: Session = Depends(get_sync_db)
):
    """更新成员信息"""
    crud = get_workspace_crud(db)
    member_id = request.member_id
    # 检查成员是否存在
    member = crud.get_member_by_id(member_id)
    if not member:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="成员不存在")

    success = crud.update_member(
        member_id=member_id,
        role_id=request.role_id
    )

    if not success:
        return api_response(code=HttpErrcode.EXCEPTION, message="更新成员失败")

    return api_response(code=HttpErrcode.SUCCESS, message="更新成功")


@router.delete("/member/remove/{member_id}")
def remove_member(
        member_id: int,
        db: Session = Depends(get_sync_db)
):
    """移除成员"""
    crud = get_workspace_crud(db)

    # 检查成员是否存在
    member = crud.get_member_by_id(member_id)
    if not member:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="成员不存在")

    success = crud.remove_member_from_workspace(member_id)
    if not success:
        return api_response(code=HttpErrcode.EXCEPTION, message="移除成员失败")

    return api_response(code=HttpErrcode.SUCCESS, message="移除成功")


@router.get("/detail-with-members/{workspace_id}")
def get_workspace_with_members(
        workspace_id: int,
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_user)
):
    """获取工作空间及其成员详细信息"""
    crud = get_workspace_crud(db)

    result = crud.get_workspace_with_members(workspace_id)
    if not result:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="工作空间不存在")

    return api_response(code=HttpErrcode.SUCCESS, data=result)
