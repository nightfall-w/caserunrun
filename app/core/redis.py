"""
@FileName：redis.py
@Description：
@Author：baojun.wang
@Time：2025/10/29 21:36
"""
import json
import os
from typing import Optional, Any

import redis
from dotenv import load_dotenv

load_dotenv()
# Redis 配置（可从环境变量读取）
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"  # 格式：redis://用户名:密码@主机:端口/数据库编号
REDIS_TIMEOUT = 3600  # 默认缓存过期时间（秒）


class RedisCache:
    def __init__(self, redis_url: str = REDIS_URL):
        self.redis_url = redis_url
        self.pool = None  # Redis 连接池

    def init_pool(self):
        """初始化 Redis 连接池（项目启动时调用）"""
        if not self.pool:
            self.pool = redis.ConnectionPool.from_url(self.redis_url)

    @property
    def client(self) -> redis.Redis:
        """获取 Redis 客户端实例（从连接池）"""
        if not self.pool:
            raise Exception("Redis 连接池未初始化，请先调用 init_pool()")
        return redis.Redis(connection_pool=self.pool)

    def set(
            self,
            key: str,
            value: Any,
            expire: Optional[int] = REDIS_TIMEOUT
    ):
        """设置缓存（自动序列化 Python 对象为 JSON）"""
        client = self.client
        # 序列化值（支持字典、列表等，简单类型直接存储）
        if isinstance(value, (dict, list, tuple)):
            value = json.dumps(value)
        client.set(key, value, ex=expire)

    def get(self, key: str) -> Optional[Any]:
        """获取缓存（自动反序列化 JSON 为 Python 对象）"""
        client = self.client
        value = client.get(key)
        print(value)
        if not value:
            return None
        # 尝试反序列化（如果是 JSON 字符串）
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value.decode("utf-8")  # 非 JSON 则返回字符串

    def delete(self, key: str):
        """删除缓存"""
        client = self.client
        client.delete(key)

    def clear(self):
        """清空当前数据库缓存（谨慎使用）"""
        client = self.client
        client.flushdb()


# 创建全局 Redis 缓存实例
redis_cache = RedisCache()


# 定义依赖项：确保 Redis 连接池已初始化
def get_redis_cache() -> RedisCache:
    redis_cache.init_pool()  # 首次调用时初始化连接池
    return redis_cache
