import redis
import json
import logging
from typing import Any, Optional, Union
from datetime import timedelta

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis客户端封装类"""

    def __init__(self, redis_url: str):
        """
        初始化Redis客户端

        Args:
            redis_url: Redis连接URL，格式如 redis://:password@host:port/db
        """
        try:
            self.client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # 测试连接
            self.client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            self.client = None

    def is_connected(self) -> bool:
        """检查Redis是否连接"""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except:
            return False

    def set(self, key: str, value: Any, expire: Optional[Union[int, timedelta]] = None) -> bool:
        """
        设置键值对

        Args:
            key: 键名
            value: 值（自动序列化为JSON）
            expire: 过期时间（秒数或timedelta对象）

        Returns:
            bool: 是否设置成功
        """
        if not self.is_connected():
            return False

        try:
            # 序列化值
            serialized_value = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value

            if expire:
                if isinstance(expire, timedelta):
                    expire = int(expire.total_seconds())
                return self.client.setex(key, expire, serialized_value)
            else:
                return self.client.set(key, serialized_value)
        except Exception as e:
            logger.error(f"Redis SET失败 {key}: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取值

        Args:
            key: 键名
            default: 默认值

        Returns:
            反序列化后的值
        """
        if not self.is_connected():
            return default

        try:
            value = self.client.get(key)
            if value is None:
                return default

            # 尝试反序列化JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # 如果不是JSON格式，直接返回字符串
                return value
        except Exception as e:
            logger.error(f"Redis GET失败 {key}: {e}")
            return default

    def delete(self, *keys: str) -> int:
        """
        删除键

        Args:
            keys: 要删除的键名列表

        Returns:
            int: 删除的键数量
        """
        if not self.is_connected():
            return 0

        try:
            return self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE失败 {keys}: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.is_connected():
            return False

        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS失败 {key}: {e}")
            return False

    def expire(self, key: str, time: Union[int, timedelta]) -> bool:
        """设置键的过期时间"""
        if not self.is_connected():
            return False

        try:
            if isinstance(time, timedelta):
                time = int(time.total_seconds())
            return self.client.expire(key, time)
        except Exception as e:
            logger.error(f"Redis EXPIRE失败 {key}: {e}")
            return False

    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """递增计数器"""
        if not self.is_connected():
            return None

        try:
            return self.client.incr(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR失败 {key}: {e}")
            return None

    def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """递减计数器"""
        if not self.is_connected():
            return None

        try:
            return self.client.decr(key, amount)
        except Exception as e:
            logger.error(f"Redis DECR失败 {key}: {e}")
            return None

    # 缓存相关方法
    def cache_set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """设置缓存（默认1小时过期）"""
        return self.set(f"cache:{key}", value, expire)

    def cache_get(self, key: str, default: Any = None) -> Any:
        """获取缓存"""
        return self.get(f"cache:{key}", default)

    def cache_delete(self, key: str) -> int:
        """删除缓存"""
        return self.delete(f"cache:{key}")

    # 标签相关缓存方法
    def cache_tag(self, tag_id: str, tag_data: dict, expire: int = 1800) -> bool:
        """缓存标签数据（30分钟）"""
        return self.cache_set(f"tag:{tag_id}", tag_data, expire)

    def get_cached_tag(self, tag_id: str) -> Optional[dict]:
        """获取缓存的标签数据"""
        return self.cache_get(f"tag:{tag_id}")

    def cache_tag_search(self, query: str, results: list, expire: int = 600) -> bool:
        """缓存标签搜索结果（10分钟）"""
        return self.cache_set(f"tag_search:{query}", results, expire)

    def get_cached_tag_search(self, query: str) -> Optional[list]:
        """获取缓存的标签搜索结果"""
        return self.cache_get(f"tag_search:{query}")

    # 用户会话相关方法
    def set_user_session(self, user_id: str, session_data: dict, expire: int = 86400) -> bool:
        """设置用户会话（24小时）"""
        return self.set(f"session:{user_id}", session_data, expire)

    def get_user_session(self, user_id: str) -> Optional[dict]:
        """获取用户会话"""
        return self.get(f"session:{user_id}")

    def delete_user_session(self, user_id: str) -> int:
        """删除用户会话"""
        return self.delete(f"session:{user_id}")

    # 速率限制相关方法
    def rate_limit_check(self, key: str, limit: int, window: int) -> dict:
        """
        检查速率限制

        Args:
            key: 限制键名（通常是用户ID或IP）
            limit: 限制次数
            window: 时间窗口（秒）

        Returns:
            dict: {
                'allowed': bool,  # 是否允许
                'current': int,   # 当前次数
                'remaining': int, # 剩余次数
                'reset_time': int # 重置时间戳
            }
        """
        if not self.is_connected():
            return {'allowed': True, 'current': 0, 'remaining': limit, 'reset_time': 0}

        try:
            pipe = self.client.pipeline()
            rate_key = f"rate_limit:{key}"

            pipe.incr(rate_key)
            pipe.expire(rate_key, window)
            results = pipe.execute()

            current = results[0]
            allowed = current <= limit
            remaining = max(0, limit - current)

            # 获取TTL来计算重置时间
            ttl = self.client.ttl(rate_key)
            reset_time = int(time.time()) + max(ttl, 0) if ttl > 0 else 0

            return {
                'allowed': allowed,
                'current': current,
                'remaining': remaining,
                'reset_time': reset_time
            }
        except Exception as e:
            logger.error(f"Redis速率限制检查失败 {key}: {e}")
            return {'allowed': True, 'current': 0, 'remaining': limit, 'reset_time': 0}

    # 热门内容统计
    def increment_view_count(self, entry_id: str) -> Optional[int]:
        """增加条目浏览次数"""
        return self.incr(f"views:{entry_id}")

    def get_view_count(self, entry_id: str) -> int:
        """获取条目浏览次数"""
        count = self.get(f"views:{entry_id}")
        return int(count) if count else 0

    def get_hot_entries(self, limit: int = 10) -> list:
        """获取热门条目（基于浏览次数）"""
        if not self.is_connected():
            return []

        try:
            # 获取所有浏览统计键
            keys = self.client.keys("views:*")
            if not keys:
                return []

            # 获取所有浏览次数
            pipe = self.client.pipeline()
            for key in keys:
                pipe.get(key)
            values = pipe.execute()

            # 组合并排序
            entries = []
            for key, value in zip(keys, values):
                entry_id = key.replace("views:", "")
                view_count = int(value) if value else 0
                entries.append({'entry_id': entry_id, 'view_count': view_count})

            # 按浏览次数排序并返回前N个
            entries.sort(key=lambda x: x['view_count'], reverse=True)
            return entries[:limit]
        except Exception as e:
            logger.error(f"获取热门条目失败: {e}")
            return []

    def close(self):
        """关闭Redis连接"""
        if self.client:
            self.client.close()

# 添加时间模块导入
import time
