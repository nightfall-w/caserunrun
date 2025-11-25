"""
@FileName：setting.py
@Description：配置项相关API路由
@Author：baojun.wang
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth_middleware import get_current_user, get_current_super_admin
from app.core.database import get_sync_db
from app.core.response import api_response, HttpErrcode
from app.setting.controller import get_setting_crud
from app.setting.request_models import (
    CreateSystemConfigRequest, UpdateSystemConfigRequest, ListSystemConfigRequest, CreateWorkspaceConfigRequest,
    UpdateWorkspaceConfigRequest,
    ListWorkspaceConfigRequest
)
from app.user.request_models import CurrentUser

router = APIRouter(prefix="/setting", tags=["配置管理"])


@router.post("/system-config/create")
def create_system_config(
        request: CreateSystemConfigRequest,
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_super_admin)
):
    """创建系统配置项"""
    crud = get_setting_crud(db)

    # 检查配置项是否已存在
    existing_config = crud.get_system_config_by_key(request.key)
    if existing_config:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="配置项已存在")

    config = crud.create_system_config(
        key=request.key,
        value=request.value,
        desc=request.desc,
        type=request.type,
        allowed_to_delete=request.allowed_to_delete,
        required=request.required
    )

    if not config:
        return api_response(code=HttpErrcode.EXCEPTION, message="创建配置项失败")

    return api_response(
        code=HttpErrcode.SUCCESS,
        data={
            "id": config.id,
            "key": config.key,
            "value": config.value,
            "desc": config.desc,
            "type": config.type,
            "allowed_to_delete": config.allowed_to_delete,
            "required": config.required,
            "create_time": config.create_time,
            "update_time": config.update_time
        }
    )


@router.get("/system-config/detail")
def get_system_config(
        config_id: int,
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_super_admin)
):
    """获取系统配置项详情"""
    crud = get_setting_crud(db)
    config = crud.get_system_config_by_id(config_id)

    if not config:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="配置项不存在")

    return api_response(
        code=HttpErrcode.SUCCESS,
        data={
            "id": config.id,
            "key": config.key,
            "value": config.value,
            "desc": config.desc,
            "type": config.type,
            "allowed_to_delete": config.allowed_to_delete,
            "required": config.required,
            "verified": config.verified,
            "create_time": config.create_time,
            "update_time": config.update_time
        }
    )


@router.post("/system-config/list")
def list_system_configs(
        request: ListSystemConfigRequest,
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_super_admin)
):
    """获取系统配置项列表"""
    crud = get_setting_crud(db)
    configs, total = crud.get_all_system_configs(page=request.page_num, size=request.page_size)

    data = []
    for config in configs:
        data.append({
            "id": config.id,
            "key": config.key,
            "value": config.value,
            "desc": config.desc,
            "type": config.type,
            "allowed_to_delete": config.allowed_to_delete,
            "required": config.required,
            "verified": config.verified,
            "create_time": config.create_time,
            "update_time": config.update_time
        })

    return api_response(
        code=HttpErrcode.SUCCESS,
        data={
            "configs": data,
            "total": total
        }
    )


@router.put("/system-config/update")
def update_system_config(
        request: UpdateSystemConfigRequest,
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_super_admin)
):
    """更新系统配置项"""
    crud = get_setting_crud(db)

    # 检查配置项是否存在
    config = crud.get_system_config_by_id(request.config_id)
    if not config:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="配置项不存在")

    update_data = {}
    if request.key is not None:
        update_data["key"] = request.key
    if request.value is not None:
        update_data["value"] = request.value
    if request.desc is not None:
        update_data["desc"] = request.desc
    if request.type is not None:
        update_data["type"] = request.type
    if request.allowed_to_delete is not None:
        update_data["allowed_to_delete"] = request.allowed_to_delete
    if request.required is not None:
        update_data["required"] = request.required
    if request.verified is not None:
        update_data["verified"] = request.verified

    success = crud.update_system_config(request.config_id, **update_data)
    if not success:
        return api_response(code=HttpErrcode.EXCEPTION, message="更新配置项失败")

    return api_response(code=HttpErrcode.SUCCESS, message="更新成功")


@router.delete("/system-config/delete")
def delete_system_config(
        config_id: int,
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_super_admin)
):
    """删除系统配置项"""
    crud = get_setting_crud(db)

    # 检查配置项是否存在
    config = crud.get_system_config_by_id(config_id)
    if not config:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="配置项不存在")

    # 检查是否允许删除
    if not config.allowed_to_delete:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="该配置项不允许删除")

    success = crud.delete_system_config(config_id)
    if not success:
        return api_response(code=HttpErrcode.EXCEPTION, message="删除配置项失败")

    return api_response(code=HttpErrcode.SUCCESS, message="删除成功")


@router.post("/workspace-config/create")
def create_workspace_config(
        request: CreateWorkspaceConfigRequest,
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_user)
):
    """创建工作空间配置项"""
    crud = get_setting_crud(db)

    # 检查配置项是否已存在
    existing_config = crud.get_workspace_config_by_key(request.workspace_id, request.key)
    if existing_config:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="配置项已存在")

    config = crud.create_workspace_config(
        workspace_id=request.workspace_id,
        key=request.key,
        value=request.value,
        desc=request.desc,
        type=request.type,
        allowed_to_delete=request.allowed_to_delete,
        required=request.required
    )

    if not config:
        return api_response(code=HttpErrcode.EXCEPTION, message="创建配置项失败")

    return api_response(
        code=HttpErrcode.SUCCESS,
        data={
            "id": config.id,
            "workspace_id": config.workspace_id,
            "key": config.key,
            "value": config.value,
            "desc": config.desc,
            "type": config.type,
            "allowed_to_delete": config.allowed_to_delete,
            "required": config.required,
            "verified": config.verified,
            "create_time": config.create_time,
            "update_time": config.update_time
        }
    )


@router.get("/workspace-config/detail")
def get_workspace_config(
        config_id: int,
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_user)
):
    """获取工作空间配置项详情"""
    crud = get_setting_crud(db)
    config = crud.get_workspace_config_by_id(config_id)

    if not config:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="配置项不存在")

    return api_response(
        code=HttpErrcode.SUCCESS,
        data={
            "id": config.id,
            "workspace_id": config.workspace_id,
            "key": config.key,
            "value": config.value,
            "desc": config.desc,
            "type": config.type,
            "allowed_to_delete": config.allowed_to_delete,
            "required": config.required,
            "verified": config.verified,
            "create_time": config.create_time,
            "update_time": config.update_time
        }
    )


@router.post("/workspace-config/list")
def list_workspace_configs(
        request: ListWorkspaceConfigRequest,
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_user)
):
    """获取工作空间配置项列表"""
    crud = get_setting_crud(db)
    configs, total = crud.get_workspace_configs(workspace_id=request.workspace_id, page=request.page_num,
                                                size=request.page_size)

    data = []
    for config in configs:
        data.append({
            "id": config.id,
            "workspace_id": config.workspace_id,
            "key": config.key,
            "value": config.value,
            "desc": config.desc,
            "type": config.type,
            "allowed_to_delete": config.allowed_to_delete,
            "required": config.required,
            "verified": config.verified,
            "create_time": config.create_time,
            "update_time": config.update_time
        })

    return api_response(
        code=HttpErrcode.SUCCESS,
        data={
            "configs": data,
            "total": total
        }
    )


@router.put("/workspace-config/update")
def update_workspace_config(
        request: UpdateWorkspaceConfigRequest,
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_user)
):
    """更新工作空间配置项"""
    crud = get_setting_crud(db)

    # 检查配置项是否存在
    config = crud.get_workspace_config_by_id(request.config_id)
    if not config:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="配置项不存在")

    update_data = {}
    if request.workspace_id is not None:
        update_data["workspace_id"] = request.workspace_id
    if request.key is not None:
        update_data["key"] = request.key
    if request.value is not None:
        update_data["value"] = request.value
    if request.desc is not None:
        update_data["desc"] = request.desc
    if request.type is not None:
        update_data["type"] = request.type
    if request.allowed_to_delete is not None:
        update_data["allowed_to_delete"] = request.allowed_to_delete
    if request.required is not None:
        update_data["required"] = request.required
    if request.verified is not None:
        update_data["verified"] = request.verified

    success = crud.update_workspace_config(request.config_id, **update_data)
    if not success:
        return api_response(code=HttpErrcode.EXCEPTION, message="更新配置项失败")

    return api_response(code=HttpErrcode.SUCCESS, message="更新成功")


@router.delete("/workspace-config/delete")
def delete_workspace_config(
        config_id: int,
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_user)
):
    """删除工作空间配置项"""
    crud = get_setting_crud(db)

    # 检查配置项是否存在
    config = crud.get_workspace_config_by_id(config_id)
    if not config:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="配置项不存在")

    # 检查是否允许删除
    if not config.allowed_to_delete:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="该配置项不允许删除")

    success = crud.delete_workspace_config(config_id)
    if not success:
        return api_response(code=HttpErrcode.EXCEPTION, message="删除配置项失败")

    return api_response(code=HttpErrcode.SUCCESS, message="删除成功")


@router.get("/gitTokenVerified/info")
def get_config_info(
        workspace_id: int,
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_user)):
    """
    获取系统和工作空间下的gitToken凭证
    :param workspace_id: 工作空间id
    :param db:
    :param current_user:
    :return:
    """
    crud = get_setting_crud(db)
    system_gitlab_api_url_config = crud.get_system_config_by_key("GITLAB_API_URL")
    system_private_token_config = crud.get_system_config_by_key("PRIVATE_TOKEN")
    workspace_gitlab_api_url_config = crud.get_workspace_config_by_key(workspace_id=workspace_id, key="GITLAB_API_URL")
    workspace_private_token_config = crud.get_workspace_config_by_key(workspace_id=workspace_id, key="PRIVATE_TOKEN")

    if system_gitlab_api_url_config.verified and system_private_token_config.verified:
        system_config_result = True
    else:
        system_config_result = False

    if workspace_gitlab_api_url_config.verified and workspace_private_token_config.verified:
        workspace_config_result = True
    else:
        workspace_config_result = False

    return api_response(code=HttpErrcode.SUCCESS, data={
        "system_config_result": system_config_result,
        "workspace_config_result": workspace_config_result
    })
