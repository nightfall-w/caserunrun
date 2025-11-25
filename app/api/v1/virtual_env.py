"""
@FileName：virtual_env.py
@Description：
@Author：baojun.wang
@Time：2025/11/20 17:15
"""
import os
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
from app.virtual_env.controller import get_installed_python_versions, create_python_venv
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
    import subprocess

    try:
        # 使用 update-alternatives --list java 命令获取已安装的 Java 版本
        result = subprocess.run(['update-alternatives', '--list', 'java'],
                                capture_output=True,
                                text=True,
                                check=True)

        # 解析输出，每一行都是一个 Java 安装路径
        java_paths = result.stdout.strip().split('\n') if result.stdout.strip() else []

        # 从路径中提取版本信息
        java_versions = []
        default_java_version = None

        # 获取当前默认的 Java 版本
        try:
            default_result = subprocess.run(['java', '-version'],
                                            capture_output=True,
                                            text=True)
            # java -version 输出到 stderr
            version_output = default_result.stderr
            if 'version' in version_output:
                # 提取版本号，例如 "java version "1.8.0_292""
                default_java_version = version_output.split('"')[1]
        except Exception:
            # 如果无法获取默认版本，继续执行而不中断
            pass

        for path in java_paths:
            # 通常路径格式类似于 /usr/lib/jvm/java-11-openjdk-amd64/bin/java
            # 提取版本号部分
            if 'java-' in path:
                version_part = path.split('java-')[1].split('-')[0]
                java_versions.append({
                    'version': version_part,
                    'path': path
                })

        return api_response(data={
            'versions': java_versions,
            'default_version': default_java_version
        }, message="获取已安装的 Java 版本列表成功")

    except subprocess.CalledProcessError as e:
        # 当 update-alternatives 没有找到 java 选项时会返回错误
        if e.returncode == 2:
            return api_response(data={'versions': [], 'default_version': None},
                                message="系统中未安装 Java 或未配置 alternatives")
        else:
            return api_response(code=HttpErrcode.EXCEPTION, message=f"获取 Java 版本列表失败: {str(e)}")
    except Exception as e:
        return api_response(code=HttpErrcode.EXCEPTION, message=f"获取 Java 版本列表时发生错误: {str(e)}")


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
    java_home_mapping = {
        "8": "/usr/lib/jvm/java-8-openjdk-arm64",
        "11": "/usr/lib/jvm/java-11-openjdk-arm64",
        "17": "/usr/lib/jvm/java-17-openjdk-arm64"
    }

    # 获取对应的JAVA_HOME路径
    java_home = java_home_mapping.get(java_version, f"/usr/lib/jvm/java-{java_version}-openjdk-amd64")

    project_root = os.path.join(CASE_HOUSE_ROOT, str(workspace_id), str(git_project_id), branch, project_name)

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
    import subprocess
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

    # 定义可能的 settings.xml 文件路径
    settings_paths = [
        "/etc/maven/settings.xml",  # 系统级配置
        os.path.expanduser("~/.m2/settings.xml"),  # 用户级配置
        os.path.expanduser("/opt/apache-maven-3.8.1/conf/settings.xml"),  # 用户级配置
    ]

    settings_content = None
    found_path = None

    # 查找存在的 settings.xml 文件
    for path in settings_paths:
        settings_file = Path(path)
        if settings_file.exists() and settings_file.is_file():
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    settings_content = file.read()
                    found_path = path
                    break
            except Exception as e:
                # 如果读取失败，继续尝试下一个路径
                continue

    # 如果没找到任何配置文件，返回默认模板
    if not settings_content:
        return api_response(data=None, code=HttpErrcode.NOT_FOUND, message="未找到任何配置文件")

    return api_response(data={
        "filePath": found_path,
        "content": settings_content
    }, message="获取成功")
