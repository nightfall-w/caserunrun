"""
@FileName：user.py
@Description：用户相关API路由
@Author：baojun.wang
"""
import os

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select, func, delete
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.core.auth_middleware import JWTManager, authenticate_user, get_current_user
from app.core.database import get_sync_db
from app.core.response import api_response, HttpErrcode
from app.user.controller import get_user_by_username, get_user_by_email, create_user, verify_password

from app.user.models import UserModel, SuperAdminModel
from app.user.request_models import UserCreate, UserLogin, CurrentUser, UserList
from utils.commonlib import now

load_dotenv()

router = APIRouter(prefix="/user", tags=["用户"])


@router.post("/register")
def register(
        user: UserCreate,
        db: Session = Depends(get_sync_db)
):
    # 查询用户名是否存在
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        return api_response(code=HttpErrcode.PARAMS_MISSING, message="用户名已经存在")

    # 查询邮箱是否存在
    db_email = get_user_by_email(db, email=user.email)
    if db_email:
        return api_response(code=HttpErrcode.PARAMS_MISSING, message="邮箱已被注册")

    # 创建用户
    user_instance = create_user(db, user=user)
    data = {
        "id": user_instance.id,
        "username": user_instance.username,
        "email": user_instance.email,
        "nickname": user_instance.nickname,
        "is_deleted": user_instance.is_deleted
    }
    return api_response(data=data, code=HttpErrcode.SUCCESS)


@router.post("/login")
def login_for_access_token(
        request: UserLogin,
        db: Session = Depends(get_sync_db)
):
    """登录接口"""
    # 检查是否为.env中配置的超级管理员账号
    env_super_admin = os.getenv("SYSTEM_ADMIN")
    env_super_admin_password = os.getenv("SYSTEM_ADMIN_PASSWORD")

    if env_super_admin and env_super_admin_password:
        # 如果用户名匹配超级管理员账号
        if request.username == env_super_admin:
            # 验证密码（注意：环境变量中的密码是明文）
            if request.password == env_super_admin_password:
                # 生成JWT token
                access_token = JWTManager.create_access_token(data={"sub": request.username})
                userinfo = {
                    "id": 0,  # 特殊ID表示环境变量中的超级管理员
                    "username": request.username,
                    "email": "admin@example.com",  # 默认邮箱
                    "nickname": "超级管理员",
                    "is_deleted": False,
                    "access_token": access_token,
                    "token_type": "bearer"
                }
                return api_response(data=userinfo, code=HttpErrcode.SUCCESS)

    # 非超级管理员账号或未配置超级管理员，使用常规登录逻辑
    user = authenticate_user(db, request.username, request.password)
    if not user:
        return api_response(code=HttpErrcode.PARAMS_MISSING, message="用户名或密码错误")

    access_token = JWTManager.create_access_token(data={"sub": user.username})
    userinfo = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "nickname": user.nickname,
        "is_deleted": user.is_deleted,
        "access_token": access_token,
        "token_type": "bearer"
    }
    return api_response(data=userinfo, code=HttpErrcode.SUCCESS)


@router.post("/users/list")
def get_users(
        request: UserList,
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_user)
):
    """用户列表接口"""
    offset = request.page_size * (request.page_num - 1)
    limit = request.page_size

    # 获取总数
    if not request.search:
        # 查询所有用户总数
        total = db.execute(select(func.count(UserModel.id))).scalar()
        # 查询所有用户
        result = db.execute(select(UserModel).offset(offset).limit(limit))
        users = result.scalars().all()
    else:
        # 条件查询总数
        total = db.execute(
            select(func.count(UserModel.id)).filter(
                or_(
                    UserModel.nickname.like(f"%{request.search}%"),
                    UserModel.username.like(f"%{request.search}%")
                )
            )
        ).scalar()
        # 条件查询用户
        result = db.execute(
            select(UserModel).filter(
                or_(
                    UserModel.nickname.like(f"%{request.search}%"),
                    UserModel.username.like(f"%{request.search}%")
                )
            ).offset(offset).limit(limit)
        )
        users = result.scalars().all()

    data = [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname,
            "is_deleted": user.is_deleted
        } for user in users
    ]

    # 返回数据中包含总数量和分页信息
    response_data = {
        "list": data,
        "total": total
    }
    return api_response(code=HttpErrcode.SUCCESS, data=response_data)


@router.get("/users/me")
def read_users_me(
        current_user: CurrentUser = Depends(get_current_user)
):
    """获取当前用户信息"""
    return current_user


@router.get("/users/me/items")
def read_own_items(
        current_user: CurrentUser = Depends(get_current_user)
):
    """受保护资源示例（无需修改）"""
    return [{"item_id": "1", "owner": current_user.username}]


@router.post("/super-admin/update")
def update_admins(
        request: dict,
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_user)
):
    """更新管理员列表（支持增删）"""
    user_ids = request.get("user_ids", [])
    if not isinstance(user_ids, list):
        return api_response(code=HttpErrcode.PARAMS_MISSING, message="user_ids 必须是数组")

    # 获取当前数据库中所有的额外管理员
    existing_admins = db.execute(
        select(SuperAdminModel.user_id)
    ).scalars().all()

    # 要删除的用户 ID（在数据库中存在但在新列表中不存在的）
    to_remove = set(existing_admins) - set(user_ids)

    # 要添加的用户 ID（在新列表中存在但在数据库中不存在的）
    to_add = set(user_ids) - set(existing_admins)

    # 删除旧的管理员记录
    for user_id in to_remove:
        db.execute(delete(SuperAdminModel).where(SuperAdminModel.user_id == user_id))

    # 添加新的管理员记录
    for user_id in to_add:
        db.add(SuperAdminModel(user_id=user_id, created_at=now()))

    db.commit()

    return api_response(code=HttpErrcode.SUCCESS, message="管理员列表更新成功")


@router.get("/super-admin/list")
def list_super_admins(
        db: Session = Depends(get_sync_db),
        current_user: CurrentUser = Depends(get_current_user)
):
    """获取所有额外添加的超级管理员"""
    result = db.execute(
        select(UserModel, SuperAdminModel.created_at)
        .join(SuperAdminModel, SuperAdminModel.user_id == UserModel.id)
    )
    admins = result.all()

    data = [
        {
            "id": admin.UserModel.id,
            "username": admin.UserModel.username,
            "nickname": admin.UserModel.nickname,
            "email": admin.UserModel.email,
            "created_at": admin.created_at
        } for admin in admins
    ]

    return api_response(data=data, code=HttpErrcode.SUCCESS)
