"""
@FileName：auth_middleware.py
@Description：
@Author：baojun.wang
@Time：2025/11/3 21:06
"""
import os
import time

from dotenv import load_dotenv
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.database import get_sync_db
from app.user.controller import get_user_by_username, verify_password, is_super_admin
from utils.commonlib import now_with_offset

load_dotenv()
# JWT 配置
REFRESH_TOKEN_THRESHOLD_MINUTES = 30  # 当 token 剩余时间少于 30 分钟时，生成新 token

SECRET_KEY = "2af555fd2e8c2e68b0af48b312de1009"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))


class JWTManager:
    @staticmethod
    def create_access_token(data: dict):
        to_encode = data.copy()
        expire = now_with_offset(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None

    @staticmethod
    def is_token_expiring_soon(payload: dict):
        """检查 token 是否即将过期"""
        if not payload or "exp" not in payload:
            return False
        exp_timestamp = payload["exp"]
        # 检查是否剩余时间少于阈值
        return exp_timestamp - time.time() < REFRESH_TOKEN_THRESHOLD_MINUTES * 60


# 创建认证依赖
security = HTTPBearer()


def authenticate_user(db: Session, username: str, password: str):
    """验证用户"""
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


# JWT工具

def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security),
                     db=Depends(get_sync_db)):
    token = credentials.credentials
    payload = JWTManager.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证凭证")

    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="无效的认证凭证")

    # 检查是否为环境变量中的超级管理员
    env_super_admin = os.getenv("SYSTEM_ADMIN")
    if env_super_admin and username == env_super_admin:
        # 为环境变量中的超级管理员构造用户对象
        # 使用id=0表示这是一个特殊用户（环境变量中的超级管理员）
        user = type('User', (), {
            'id': 0,
            'username': username,
            'email': 'admin@example.com',
            'nickname': '超级管理员',
            'is_deleted': False
        })()
    else:
        user = get_user_by_username(db, username)
        if user is None:
            raise HTTPException(status_code=401, detail="用户不存在")

    # 检查 token 是否即将过期，如果是则生成新 token
    new_token = None
    if JWTManager.is_token_expiring_soon(payload):
        new_token_data = {"sub": user.username}
        new_token = JWTManager.create_access_token(new_token_data)

    # 将 new_token 存储在请求状态中，供中间件使用
    request.state.new_token = new_token

    return user


def get_current_super_admin(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security),
                            db=Depends(get_sync_db)):
    """获取当前超级管理员用户"""
    user = get_current_user(request, credentials, db)

    # 检查是否为超级管理员（包括环境变量中的超级管理员）
    # 对于环境变量中的超级管理员（id=0），直接允许通过
    if user.id == 0:
        return user

    # 对于其他用户，检查是否在超级管理员表中
    if not is_super_admin(db, user.id):
        raise HTTPException(status_code=403, detail="需要超级管理员权限")

    return user
