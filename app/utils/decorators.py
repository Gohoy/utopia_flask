from functools import wraps
from flask import request, current_app
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.utils.helpers import error_response
from app import redis_client

def rate_limit(max_requests=100, window=3600, per='user'):
    """
    速率限制装饰器

    Args:
        max_requests: 最大请求次数
        window: 时间窗口（秒）
        per: 限制类型 ('user', 'ip')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not redis_client or not redis_client.is_connected():
                # Redis不可用时跳过限制
                return f(*args, **kwargs)

            # 确定限制键
            if per == 'user':
                try:
                    verify_jwt_in_request()
                    key = f"user:{get_jwt_identity()}"
                except:
                    key = f"ip:{request.remote_addr}"
            else:
                key = f"ip:{request.remote_addr}"

            # 检查速率限制
            limit_result = redis_client.rate_limit_check(key, max_requests, window)

            if not limit_result['allowed']:
                return error_response(
                    "请求过于频繁，请稍后再试",
                    429,
                    {
                        'retry_after': limit_result['reset_time'],
                        'limit': max_requests,
                        'remaining': limit_result['remaining']
                    }
                )

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def cache_response(expire=300, key_prefix=None):
    """
    响应缓存装饰器

    Args:
        expire: 缓存过期时间（秒）
        key_prefix: 缓存键前缀
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not redis_client or not redis_client.is_connected():
                return f(*args, **kwargs)

            # 生成缓存键
            if key_prefix:
                cache_key = f"{key_prefix}:{request.full_path}"
            else:
                cache_key = f"response:{f.__name__}:{request.full_path}"

            # 尝试从缓存获取
            cached_response = redis_client.get(cache_key)
            if cached_response:
                return cached_response

            # 执行函数并缓存结果
            response = f(*args, **kwargs)
            redis_client.set(cache_key, response, expire)

            return response
        return decorated_function
    return decorator
