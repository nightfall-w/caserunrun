"""
@FileName：database.py
@Description：
@Author：baojun.wang
@Time：2025/10/27 13:45
"""
import asyncio
import os
from contextlib import asynccontextmanager, contextmanager
from threading import local

from dotenv import load_dotenv  # 用于加载环境变量（需安装 python-dotenv）
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from utils.custom_logging import logger

# 加载环境变量（从 .env 文件读取数据库配置）
load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root1234")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "polymericTest")

# 同步引擎和session工厂
SYNC_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
SYNC_ENGINE = create_engine(SYNC_DATABASE_URL,
                            pool_size=100,  # 连接池大小（500过大，建议10-20，根据并发调整）
                            max_overflow=200,  # 超过pool_size时允许临时创建的连接数
                            pool_pre_ping=True,  # 检测连接可用性（避免失效连接）
                            pool_recycle=3600,  # 连接回收时间（避免MySQL自动断开连接）
                            echo=False  # 生产环境关闭SQL日志输出
                            )
SYNC_SESSION = sessionmaker(bind=SYNC_ENGINE,
                            autocommit=False,  # 关闭自动提交（手动控制事务）
                            autoflush=True,  # 关闭自动刷新（避免不必要的数据库查询）
                            expire_on_commit=False  # 提交后不失效实例（避免二次查询）
                            )


@contextmanager
def _sync_db_context() -> Session:
    """同步数据库会话上下文管理器（自动处理事务和连接释放）"""
    session = SYNC_SESSION()
    try:
        yield session  # 产出会话供业务使用
        session.commit()  # 无异常时提交事务
    except Exception as e:
        session.rollback()  # 异常时回滚事务
        raise  # 重新抛出异常，让上层处理
    finally:
        session.close()  # 无论成功失败，都关闭会话释放连接


# 供 FastAPI 依赖注入的函数（返回 Session 实例）
def get_sync_db() -> Session:
    with _sync_db_context() as session:
        yield session


thread_local = local()


def get_engine():
    """获取当前线程的引擎"""
    if not hasattr(thread_local, 'engine'):
        # 创建新的事件循环和引擎
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        engine = create_engine(
            SYNC_DATABASE_URL,
            pool_size=20,
            max_overflow=5,
            pool_recycle=1800,
            pool_pre_ping=True
        )

        thread_local.engine = engine
        thread_local.loop = loop

    return thread_local.engine


def get_session_factory():
    """获取当前线程的会话工厂"""
    engine = get_engine()

    if not hasattr(thread_local, 'session_factory'):
        thread_local.session_factory = sessionmaker(
            engine,
            class_=Session,
            expire_on_commit=False
        )

    return thread_local.session_factory


@asynccontextmanager
def get_db_for_multithreading():
    """提供当前线程的数据库会话"""
    session_factory = get_session_factory()

    with session_factory() as session:
        try:
            logger.debug(f"会话开始 - ID: {id(session)}")
            yield session
            session.commit()
        except Exception as e:
            logger.warning(f"会话回滚 - 错误: {str(e)}")
            session.rollback()
            raise
        finally:
            # 确保会话资源被正确释放
            logger.debug(f"会话关闭 - ID: {id(session)}")
            session.close()


Base = declarative_base()
