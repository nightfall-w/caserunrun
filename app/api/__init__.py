"""
@FileName：__init__.py.py
@Description：
@Author：baojun.wang
@Time：2025/10/27 10:33
"""
from fastapi import APIRouter

from app.api.v1 import router as v1_router

router = APIRouter(prefix="/api")  # 版本前缀
router.include_router(v1_router)
