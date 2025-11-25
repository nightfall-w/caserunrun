"""
@FileName：virtual_env.py
@Description：
@Author：baojun.wang
@Time：2025/11/20 17:15
"""
import os
import subprocess
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.case_handler.gitlab_tool import GitlabAPI
from app.case_source.models import CaseSourceRelationModel
from app.core.config import CASE_HOUSE_ROOT
from app.core.database import get_sync_db
from app.core.response import api_response, HttpErrcode
from app.setting.controller import SettingCRUD
from app.virtual_env.controller import get_installed_python_versions, create_python_venv, get_installed_java_versions, \
    get_default_maven_setting_path_and_content
from app.virtual_env.request_models import CreatePythonVirtualEnvModel, CreateJavaVirtualEnvModel

router = APIRouter(prefix="/virtual-env", tags=["虚拟环境管理"])


@router.get("/python-versions")
async def list_python_versions():
    """
    获取已安装的 Python 版本列表
    """
    try:
        versions = get_installed_python_versions()
        return api_response(data=versions, message="获取已安装的 Python版本 列表成功")
    except Exception as e:
        return api_response(code=HttpErrcode.EXCEPTION, message=str(e))


@router.get("/java-versions")
async def list_java_versions():
    """
    获取已安装的 java 版本列表
    """
    try:
        java_versions, default_java_version = get_installed_java_versions()
        return api_response(data={
            'versions': java_versions,
            'default_version': default_java_version
        }, message="获取已安装的 Java 版本列表成功")
    except Exception as e:
        return api_response(code=HttpErrcode.EXCEPTION, message=f"获取 Java 版本列表失败: {str(e)}")


@router.post("/create_python_virtual_environment")
async def create_python_virtual_environment(
        request: CreatePythonVirtualEnvModel,
        db: Session = Depends(get_sync_db),
):
    """
    创建python虚拟环境并安装依赖
    """
    case_source_id = request.case_source_id
    workspace_id = request.workspace_id
    python_version = request.python_version
    project_name = request.project_name
    git_project_id = request.git_project_id
    requirements_path = request.requirements_path
    stmt = select(CaseSourceRelationModel).where(
        and_(
            CaseSourceRelationModel.workspace_id == workspace_id,
            CaseSourceRelationModel.case_source_value['projectId'] == git_project_id
        )
    )
    result = db.execute(stmt)
    case_source = result.scalars().first()
    # 如果需要使用case_source进行后续操作
    requirements_temp_path = None
    if case_source:
        setting_crud = SettingCRUD(db)
        gitlab_url, token = setting_crud.get_gitlab_credentials(token_type=case_source.token_type,
                                                                workspace_id=workspace_id)
        gitlab_client = GitlabAPI(gitlab_url=gitlab_url, token=token)
        content = gitlab_client.get_content(project_id=git_project_id,
                                            file_path=requirements_path)
        # 创建临时文件存储requirements内容
        if content:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(content)
                requirements_temp_path = f.name
    try:
        if requirements_temp_path:
            result = create_python_venv(workspace_id, python_version, project_name, git_project_id,
                                        requirements_temp_path, db=db)
            os.remove(requirements_temp_path)
            if case_source_id and "venv_id" in result:
                stmt = select(CaseSourceRelationModel).where(
                    CaseSourceRelationModel.id == case_source_id
                )
                db_case_source = db.execute(stmt).scalars().first()
                if db_case_source:
                    db_case_source.venv_id = result["venv_id"]
                    db_case_source.venv_version = result["venv_version"]
                    db.commit()
            return api_response(data=result, message="创建虚拟环境成功")
        else:
            return api_response(code=HttpErrcode.EXCEPTION, message="创建虚拟环境失败")
    except HTTPException as e:
        return api_response(code=HttpErrcode.EXCEPTION, message=str(e.detail))


@router.post("/create_java_virtual_environment")
async def create_java_virtual_environment(
        request: CreateJavaVirtualEnvModel,
        db: Session = Depends(get_sync_db),
):
    """
    创建java虚拟环境并安装依赖
    """
    workspace_id = request.workspace_id
    java_version = request.java_version
    project_name = request.project_name
    git_project_id = request.git_project_id
    maven_setting_path = request.maven_setting_path
    branch = "master"
    # 根据Java版本确定JAVA_HOME路径
    java_versions, default_java_version = get_installed_java_versions()
    for version_item in java_versions:
        if version_item['version'] == java_version:
            java_path = version_item['path']
            break
    else:
        return api_response(code=HttpErrcode.EXCEPTION, message="Java版本不存在")

    # 获取对应的JAVA_HOME路径
    java_home = java_path.replace("/bin/java", "")

    project_root = os.path.join(CASE_HOUSE_ROOT, str(workspace_id), str(git_project_id), branch, project_name)

    if not maven_setting_path:
        # 使用默认配置
        settings_content, maven_setting_path = get_default_maven_setting_path_and_content()
    # 创建.envrc文件
    envrc_content = f"""#!/bin/bash
                    # 项目专属JDK路径（Java {java_version}）
                    export JAVA_HOME={java_home}
                    export PATH=$JAVA_HOME/bin:$PATH
                    
                    # 项目专属Maven配置
                    export MAVEN_OPTS="-s {maven_setting_path}"  
                    """

    # 写入.envrc文件
    envrc_path = os.path.join(project_root, ".envrc")
    with open(envrc_path, "w") as f:
        f.write(envrc_content)

    # 执行 direnv allow 命令使.envrc文件生效
    try:
        result = subprocess.run(["direnv", "allow", project_root],
                                cwd=project_root,
                                capture_output=True,
                                text=True)
        if result.returncode != 0:
            return api_response(code=HttpErrcode.EXCEPTION,
                                message=f"direnv allow执行失败: {result.stderr}")
    except FileNotFoundError:
        return api_response(code=HttpErrcode.EXCEPTION,
                            message="未找到direnv命令，请确保已安装direnv")
    except Exception as e:
        return api_response(code=HttpErrcode.EXCEPTION,
                            message=f"执行direnv allow时发生错误: {str(e)}")

    # 执行 mvn install -DskipTests 安装项目依赖
    try:
        result = subprocess.run(["mvn", "install", "-DskipTests"],
                                cwd=project_root,
                                capture_output=True,
                                text=True)
        if result.returncode != 0:
            return api_response(code=HttpErrcode.EXCEPTION, message=f"mvn install -DskipTests执行失败: {result.stderr}")
    except Exception as e:
        return api_response(code=HttpErrcode.EXCEPTION, message=f"执行mvn install -DskipTests时发生错误: {str(e)}")

    return api_response(data={
        "envrc_path": envrc_path,
        "envrc_content": envrc_content,
        "java_home": java_home,
        "java_version": java_version
    }, message="Java虚拟环境创建成功")


@router.get("/get_default_maven_setting")
async def get_default_maven_setting():
    """
    获取默认的maven设置
    """
    settings_content, maven_setting_path = get_default_maven_setting_path_and_content()

    # 如果没找到任何配置文件，返回默认模板
    if not settings_content:
        return api_response(data=None, code=HttpErrcode.NOT_FOUND, message="未找到任何配置文件")

    return api_response(data={
        "filePath": maven_setting_path,
        "content": settings_content
    }, message="获取成功")
