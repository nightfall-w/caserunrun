"""
@FileName：controller.py
@Description：
@Author：baojun.wang
@Time：2025/11/20 12:44
"""
import os
import subprocess

from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.virtual_env.models import PythonVirtualEnvModel

app = FastAPI(title="Python虚拟环境管理工具")

# 配置项
VENV_ROOT = "/Users/baojunw/venvs"  # 虚拟环境存放目录
PYENV_ROOT = 'pyenv'

# 确保目录存在
os.makedirs(VENV_ROOT, exist_ok=True)


def get_installed_python_versions():
    """获取pyenv已安装的Python版本"""
    try:
        result = subprocess.run(
            [f"{PYENV_ROOT}", "versions", "--bare"],
            capture_output=True, text=True, check=True
        )
        versions = [v.strip() for v in result.stdout.split("\n") if v.strip()]
        print(versions)
        return versions
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"获取Python版本失败：{e.stderr}")


def get_python_path(python_version):
    """获取指定Python版本的可执行文件路径"""
    # 第一步：调用 pyenv prefix 获取版本根目录
    result = subprocess.run(
        ["pyenv", "prefix", python_version],
        capture_output=True,
        text=True,
        check=True  # 若命令失败（如版本不存在），抛出异常
    )
    pyenv_prefix = result.stdout.strip()  # 去除换行符
    # 拼接 Python 可执行文件路径
    python_path = f"{pyenv_prefix}/bin/python"
    return python_path


def save_python_venv_to_db(db: Session, name: str, python_version: str, venv_path: str, interpreter_path: str):
    """保存Python虚拟环境信息到数据库"""
    db_venv = PythonVirtualEnvModel(
        name=name,
        python_version=python_version,
        path=venv_path,
        interpreter_path=interpreter_path
    )
    db.add(db_venv)
    db.commit()
    db.refresh(db_venv)
    return db_venv


def create_python_venv(workspace_id, python_version: str, project_name: str, project_id: int, requirements_path: str,
                       db: Session):
    """创建虚拟环境并安装依赖"""
    # 1. 获取项目路径和虚拟环境路径
    venv_name = f"{workspace_id}_{project_id}_{project_name}_py{python_version.replace('.', '_')}"
    venv_path = os.path.join(VENV_ROOT, venv_name)

    # 2. 检查Python版本是否存在
    if python_version not in get_installed_python_versions():
        raise HTTPException(status_code=400, detail=f"Python版本{python_version}未安装")

    # 3. 用pyenv指定的Python版本创建虚拟环境
    try:
        python_exec = get_python_path(python_version)

        # 创建虚拟环境
        subprocess.run(
            [python_exec, "-m", "venv", venv_path],
            check=True, capture_output=True
        )

        # 安装requirements.txt依赖
        pip_exec = os.path.join(venv_path, "bin", "pip")
        result = subprocess.run(
            [pip_exec, "install", "-r", requirements_path],
            check=True, capture_output=True
        )
        print("STDOUT:", result.stdout.decode('utf-8'))
        print("STDERR:", result.stderr.decode('utf-8'))

        # 保存虚拟环境信息到数据库
        interpreter_path = os.path.join(venv_path, "bin", "python")
        db_venv = save_python_venv_to_db(
            db=db,
            name=venv_name,
            python_version=python_version,
            venv_path=venv_path,
            interpreter_path=interpreter_path
        )

        return {
            "log": f"{result.stdout.decode('utf-8')}\n{result.stderr.decode('utf-8')}",
            "venv_id": db_venv.id,
            "venv_name": venv_name,
        }
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"{e.stderr.decode('utf-8')}")


def create_java_venv(workspace_id, project_name: str, project_id: int, requirements_path: str, db: Session):
    """创建Java虚拟环境并安装依赖"""
    pass
