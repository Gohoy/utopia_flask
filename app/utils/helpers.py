from flask import jsonify, request
import logging
from functools import wraps

logger = logging.getLogger(__name__)
# app/utils/helpers.py
from flask import jsonify, request
import logging
from functools import wraps
import json
from datetime import datetime
from neo4j.time import DateTime as Neo4jDateTime

logger = logging.getLogger(__name__)

class CustomJSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，支持Neo4j数据类型"""
    def default(self, obj):
        if isinstance(obj, Neo4jDateTime):
            # 将Neo4j DateTime转换为ISO格式字符串
            return obj.isoformat()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def convert_neo4j_objects(obj):
    """递归转换Neo4j对象为Python原生对象"""
    if isinstance(obj, dict):
        return {k: convert_neo4j_objects(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_neo4j_objects(item) for item in obj]
    elif isinstance(obj, Neo4jDateTime):
        return obj.isoformat()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj

def success_response(data=None, message="操作成功", code=200):
    """成功响应格式 - 支持Neo4j数据类型"""
    response = {
        'success': True,
        'message': message,
        'code': code
    }
    if data is not None:
        # 转换Neo4j对象
        response['data'] = convert_neo4j_objects(data)

    return jsonify(response), code

def error_response(message="操作失败", code=400, errors=None):
    """错误响应格式"""
    response = {
        'success': False,
        'message': message,
        'code': code
    }
    if errors:
        response['errors'] = convert_neo4j_objects(errors)
    return jsonify(response), code


def register_error_handlers(app):
    """注册错误处理器"""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': '请求参数错误',
            'message': str(error.description) if hasattr(error, 'description') else '请求格式不正确'
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': '未授权访问',
            'message': '请先登录'
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': '权限不足',
            'message': '没有权限执行此操作'
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': '资源不存在',
            'message': '请求的资源未找到'
        }), 404

    @app.errorhandler(429)
    def too_many_requests(error):
        return jsonify({
            'error': '请求过于频繁',
            'message': '请稍后再试'
        }), 429

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"服务器内部错误: {error}")
        return jsonify({
            'error': '服务器内部错误',
            'message': '请联系管理员'
        }), 500

def register_commands(app):
    """注册命令行命令"""

    @app.cli.command()
    def init_db():
        """初始化数据库"""
        from app import db
        db.create_all()
        print("数据库初始化完成")

    @app.cli.command()
    def create_admin():
        """创建管理员用户"""
        from app.models.user import User, UserPermission
        from app import db

        admin = User(
            username='admin',
            email='admin@utopia.com',
            nickname='管理员'
        )
        admin.set_password('admin123')  # 生产环境请修改密码

        # 创建权限
        permissions = UserPermission(
            user_id=admin.id,
            can_approve_changes=True,
            max_edits_per_day=1000
        )

        db.session.add(admin)
        db.session.add(permissions)
        db.session.commit()

        print(f"管理员用户创建成功: {admin.username}")

def validate_json(*required_fields):
    """验证JSON请求装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return error_response("请求必须是JSON格式", 400)

            data = request.get_json()
            if not data:
                return error_response("请求体不能为空", 400)

            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return error_response(
                    f"缺少必填字段: {', '.join(missing_fields)}",
                    400,
                    {'missing_fields': missing_fields}
                )

            return f(*args, **kwargs)
        return decorated_function
    return decorator
