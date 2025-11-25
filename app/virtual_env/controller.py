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
VENV_ROOT = os.path.join(os.path.expandvars("$HOME"), "venv")  # 虚拟环境存放目录
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
        # 对版本号进行排序
        versions.sort(key=lambda v: [int(x) for x in v.split('.')], reverse=True)
        print(versions)
        return versions
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"获取Python版本失败：{e.stderr}")


def get_installed_java_versions():
    """获取已安装的Java版本"""

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
                java_versions = sorted(java_versions, key=lambda x: int(x['version']), reverse=True)

        return java_versions, default_java_version

    except subprocess.CalledProcessError as e:
        # 当 update-alternatives 没有找到 java 选项时会返回错误
        if e.returncode == 2:
            return [], None
        else:
            raise e
    except Exception as e:
        raise e


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
            "venv_version": python_version,
        }
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"{e.stderr.decode('utf-8')}")


def create_java_venv(workspace_id, project_name: str, project_id: int, requirements_path: str, db: Session):
    """创建Java虚拟环境并安装依赖"""
    pass
