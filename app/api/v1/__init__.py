"""
@FileName：__init__.py.py
@Description：
@Author：baojun.wang
@Time：2025/10/27 10:33
"""
from fastapi import APIRouter

from app.api.v1.case_source import router as case_source_router
from app.api.v1.workspace import router as workspace_router
from app.api.v1.user import router as user_router
from app.api.v1.setting import router as setting_router
from app.api.v1.testcase import router as testcase_router
from app.api.v1.virtual_env import router as virtual_env_router
from app.api.v1.testplan import router as testplan_router

router = APIRouter(prefix="/v1")  # 版本前缀
router.include_router(case_source_router)
router.include_router(workspace_router)
router.include_router(user_router)
router.include_router(setting_router)
router.include_router(testcase_router)
router.include_router(virtual_env_router)
router.include_router(testplan_router)
