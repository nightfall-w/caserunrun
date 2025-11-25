"""
@FileName：controller.py
@Description：用户相关工具类
@Author：baojun.wang
"""
import os

from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.user.models import UserModel, SuperAdminModel
from app.user.request_models import UserCreate
from utils.commonlib import now

load_dotenv()
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


# 密码工具保持不变
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user_by_username(db: Session, username: str):
    """根据用户名查询用户"""
    result = db.execute(select(UserModel).filter(UserModel.username == username))
    return result.scalars().first()


def get_nickname_by_username(db: Session, username: str):
    """获取用户昵称"""
    result = db.execute(select(UserModel).filter(UserModel.username == username))
    user = result.scalars().first()
    return user.nickname if user else None


def get_user_by_email(db: Session, email: str):
    """根据邮箱查询用户"""
    result = db.execute(select(UserModel).filter(UserModel.email == email))
    return result.scalars().first()


def create_user(db: Session, user: UserCreate):
    """创建用户"""
    hashed_password = get_password_hash(user.password)
    db_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        nickname=user.nickname,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def is_super_admin(db: Session, user_id: int) -> bool:
    """判断用户是否为超级管理员"""
    # 检查是否为环境变量中的超级管理员
    env_super_admin = os.getenv("SYSTEM_ADMIN")
    if env_super_admin:
        env_user = get_user_by_username(db, env_super_admin)
        if env_user and env_user.id == user_id:
            return True

    # 检查是否为额外添加的超级管理员
    result = db.execute(select(SuperAdminModel).filter(SuperAdminModel.user_id == user_id))
    super_admin = result.scalars().first()
    return super_admin is not None


def get_super_admins(db: Session):
    """获取所有额外添加的超级管理员"""
    result = db.execute(select(SuperAdminModel))
    return result.scalars().all()


def add_super_admin(db: Session, user_id: int) -> bool:
    """添加超级管理员"""
    # 检查用户是否已存在
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        return False

    # 检查是否已经是超级管理员
    if is_super_admin(db, user_id):
        return False

    # 检查额外超级管理员数量是否已达上限
    super_admin_count = db.query(SuperAdminModel).count()
    if super_admin_count >= 3:
        return False

    # 添加超级管理员
    super_admin = SuperAdminModel(
        user_id=user_id,
        created_at=now()
    )
    db.add(super_admin)
    db.commit()
    return True


def remove_super_admin(db: Session, user_id: int) -> bool:
    """移除超级管理员"""
    # 检查是否为环境变量中的超级管理员
    env_super_admin = os.getenv("SYSTEM_ADMIN")
    if env_super_admin:
        env_user = get_user_by_username(db, env_super_admin)
        if env_user and env_user.id == user_id:
            # 环境变量中的超级管理员不能被移除
            return False

    # 移除额外添加的超级管理员
    super_admin = db.query(SuperAdminModel).filter(SuperAdminModel.user_id == user_id).first()
    if not super_admin:
        return False

    db.delete(super_admin)
    db.commit()
    return True
