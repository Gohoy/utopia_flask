# app/__init__.py - 改进版本
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import Swagger
import logging
from datetime import datetime
import os

from app.config import config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局扩展对象
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)

# 全局客户端对象
neo4j_client = None
redis_client = None

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 初始化扩展
    init_extensions(app)

    # 初始化客户端
    init_clients(app)

    # 注册蓝图
    register_blueprints(app)

    # 注册错误处理器和命令
    register_handlers_and_commands(app)

    # 注册路由
    register_routes(app)

    # 初始化Swagger文档
    init_swagger(app)

    return app

def init_extensions(app):
    """初始化Flask扩展"""
    try:
        db.init_app(app)
        migrate.init_app(app, db)
        jwt.init_app(app)

        # 配置CORS
        CORS(app)

        # 初始化限流器
        limiter.init_app(app)
        logger.info("Flask extensions initialized successfully")

    except Exception as e:
        logger.error(f"Flask extensions initialization failed: {e}")

def init_clients(app):
    """初始化外部客户端"""
    global neo4j_client, redis_client

    # 初始化Neo4j客户端
    try:
        if all(key in app.config for key in ['NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD']):
            from app.utils.neo4j_client import Neo4jClient
            neo4j_client = Neo4jClient(
                app.config['NEO4J_URI'],
                app.config['NEO4J_USER'],
                app.config['NEO4J_PASSWORD']
            )
            logger.info("Neo4j client initialized successfully")
        else:
            logger.warning("Neo4j configuration not found, skipping initialization")
    except Exception as e:
        logger.error(f"Neo4j client initialization failed: {e}")
        neo4j_client = None

    # 初始化Redis客户端
    try:
        if 'REDIS_URL' in app.config:
            from app.utils.redis_client import RedisClient
            redis_client = RedisClient(app.config['REDIS_URL'])
            logger.info("Redis client initialized successfully")
        else:
            logger.warning("Redis configuration not found, skipping initialization")
    except Exception as e:
        logger.error(f"Redis client initialization failed: {e}")
        redis_client = None

def register_blueprints(app):
    """注册蓝图"""
    try:
        from app.api.auth import bp as auth_bp
        from app.api.entries import bp as entries_bp
        from app.api.tags import bp as tags_bp

        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(entries_bp, url_prefix='/api/entries')
        app.register_blueprint(tags_bp, url_prefix='/api/tags')
        logger.info("All blueprints registered successfully")
    except Exception as e:
        logger.error(f"Blueprint registration failed: {e}")
        import traceback
        traceback.print_exc()

def register_handlers_and_commands(app):
    """注册错误处理器和命令"""
    try:
        from app.utils.helpers import register_error_handlers, register_commands
        register_error_handlers(app)
        register_commands(app)
        logger.info("Error handlers and commands registered successfully")
    except Exception as e:
        logger.error(f"Handlers registration failed: {e}")

def init_swagger(app):
    """初始化Swagger文档"""
    try:
        swagger_config = {
            "headers": [],
            "specs": [
                {
                    "endpoint": 'apispec',
                    "route": '/apispec.json',
                    "rule_filter": lambda rule: True,
                    "model_filter": lambda tag: True,
                }
            ],
            "static_url_path": "/flasgger_static",
            "swagger_ui": True,
            "specs_route": "/api/docs"
        }

        swagger_template = {
            "swagger": "2.0",
            "info": {
                "title": "虚拟乌托邦 API",
                "description": "万物皆可图鉴的协作平台 API 文档",
                "version": "1.0.0",
                "contact": {
                    "name": "虚拟乌托邦团队",
                    "email": "support@utopia.com"
                },
                "license": {
                    "name": "MIT License",
                    "url": "https://opensource.org/licenses/MIT"
                }
            },
            "host": app.config.get('SERVER_NAME', 'localhost:5000'),
            "basePath": "/",
            "schemes": ["http", "https"],
            "consumes": ["application/json"],
            "produces": ["application/json"],
            "securityDefinitions": {
                "JWT": {
                    "type": "apiKey",
                    "name": "Authorization",
                    "in": "header",
                    "description": "JWT Token. 格式: 'Bearer <token>'"
                }
            },
            "tags": [
                {
                    "name": "Authentication",
                    "description": "用户认证相关接口"
                },
                {
                    "name": "Entries",
                    "description": "图鉴条目相关接口"
                },
                {
                    "name": "Tags",
                    "description": "标签系统相关接口"
                },
                {
                    "name": "System",
                    "description": "系统信息接口"
                }
            ]
        }

        Swagger(app, config=swagger_config, template=swagger_template)
        logger.info("Swagger documentation initialized successfully")

    except Exception as e:
        logger.error(f"Swagger initialization failed: {e}")

def register_routes(app):
    """注册基础路由"""

    @app.route('/')
    def index():
        """
        API 首页
        ---
        tags:
          - System
        responses:
          200:
            description: API信息
            schema:
              type: object
              properties:
                name:
                  type: string
                  example: "虚拟乌托邦API"
                version:
                  type: string
                  example: "1.0.0"
                description:
                  type: string
                  example: "万物皆可图鉴的协作平台"
                endpoints:
                  type: object
                docs:
                  type: object
        """
        return {
            'name': '虚拟乌托邦API',
            'version': '1.0.0',
            'description': '万物皆可图鉴的协作平台',
            'status': 'running',
            'timestamp': datetime.utcnow().isoformat(),
            'endpoints': {
                'health': '/health',
                'api_info': '/api',
                'auth': '/api/auth/',
                'entries': '/api/entries/',
                'tags': '/api/tags/'
            },
            'docs': {
                'swagger': '/api/docs',
                'api_spec': '/apispec.json',
                'github': 'https://github.com/your-repo/utopia-backend'
            }
        }

    @app.route('/health')
    def health_check():
        """
        健康检查
        ---
        tags:
          - System
        responses:
          200:
            description: 服务状态
            schema:
              type: object
              properties:
                status:
                  type: string
                  enum: [healthy, degraded, unhealthy]
                message:
                  type: string
                services:
                  type: object
                features:
                  type: object
        """
        services_status = check_services_status()

        # 计算整体状态
        connected_services = sum(1 for status in services_status.values() if status == 'connected')
        total_services = len(services_status)

        if connected_services == total_services:
            overall_status = 'healthy'
        elif connected_services >= total_services // 2:
            overall_status = 'degraded'
        else:
            overall_status = 'unhealthy'

        return {
            'status': overall_status,
            'message': '虚拟乌托邦服务运行状态',
            'version': '1.0.0',
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': get_uptime(),
            'services': services_status,
            'endpoints': {
                'auth': '/api/auth/',
                'entries': '/api/entries/',
                'tags': '/api/tags/',
                'docs': '/api/docs'
            },
            'features': {
                'authentication': True,
                'encyclopedia_entries': True,
                'tag_system': services_status.get('neo4j') == 'connected',
                'media_upload': False,
                'search': True,
                'caching': services_status.get('redis') == 'connected',
                'rate_limiting': True,
                'api_documentation': True
            }
        }

    @app.route('/api')
    def api_info():
        """
        API 信息
        ---
        tags:
          - System
        responses:
          200:
            description: API详细信息
            schema:
              type: object
              properties:
                name:
                  type: string
                version:
                  type: string
                available_endpoints:
                  type: object
        """
        return {
            'name': '虚拟乌托邦API',
            'version': '1.0.0',
            'description': '万物皆可图鉴的协作平台API',
            'documentation': {
                'swagger_ui': '/api/docs',
                'openapi_spec': '/apispec.json'
            },
            'available_endpoints': {
                'authentication': {
                    'base_url': '/api/auth',
                    'description': '用户认证和权限管理',
                    'endpoints': [
                        'POST /api/auth/register - 用户注册',
                        'POST /api/auth/login - 用户登录',
                        'GET /api/auth/profile - 获取用户信息',
                        'PUT /api/auth/profile - 更新用户信息',
                        'POST /api/auth/change-password - 修改密码',
                        'POST /api/auth/verify-token - 验证Token'
                    ]
                },
                'encyclopedia': {
                    'base_url': '/api/entries',
                    'description': '图鉴条目管理',
                    'endpoints': [
                        'POST /api/entries - 创建图鉴条目',
                        'GET /api/entries - 获取图鉴列表',
                        'GET /api/entries/<id> - 获取单个图鉴',
                        'PUT /api/entries/<id> - 更新图鉴条目',
                        'DELETE /api/entries/<id> - 删除图鉴条目',
                        'GET /api/entries/my - 获取我的图鉴',
                        'GET /api/entries/search - 搜索图鉴',
                        'GET /api/entries/my/stats - 获取统计数据',
                        'GET /api/entries/hot - 获取热门图鉴'
                    ]
                },
                'tags': {
                    'base_url': '/api/tags',
                    'description': '标签系统和分类管理',
                    'endpoints': [
                        'POST /api/tags - 创建标签',
                        'GET /api/tags/<id> - 获取标签详情',
                        'PUT /api/tags/<id> - 更新标签',
                        'DELETE /api/tags/<id> - 删除标签',
                        'GET /api/tags/search - 搜索标签',
                        'GET /api/tags/popular - 热门标签',
                        'GET /api/tags/tree - 标签树',
                        'POST /api/tags/recommend - 推荐标签',
                        'POST /api/tags/validate - 验证标签',
                        'GET /api/tags/categories - 标签分类'
                    ]
                }
            },
            'rate_limits': {
                'default': '100 requests per hour',
                'auth_endpoints': '20 requests per hour',
                'create_operations': '10-20 requests per hour'
            },
            'authentication': {
                'type': 'JWT Bearer Token',
                'header': 'Authorization: Bearer <token>',
                'token_expiry': '24 hours'
            }
        }

    @app.route('/api/stats')
    def api_stats():
        """
        API 统计信息
        ---
        tags:
          - System
        responses:
          200:
            description: API使用统计
        """
        try:
            from app.models.user import User
            from app.models.entry import Entry

            stats = {
                'total_users': User.query.count(),
                'total_entries': Entry.query.filter_by(is_deleted=False).count(),
                'public_entries': Entry.query.filter_by(is_deleted=False, visibility='public').count(),
                'services_status': check_services_status(),
                'timestamp': datetime.utcnow().isoformat()
            }

            return stats
        except Exception as e:
            logger.error(f"获取API统计失败: {e}")
            return {
                'error': 'Unable to fetch statistics',
                'timestamp': datetime.utcnow().isoformat()
            }, 500

def check_services_status():
    """检查各服务状态"""
    services_status = {}

    # 检查数据库
    try:
        # 使用新的SQLAlchemy语法
        with db.engine.connect() as conn:
            conn.execute(db.text('SELECT 1'))
        services_status['postgresql'] = 'connected'
    except Exception as e:
        logger.debug(f"PostgreSQL check failed: {e}")
        services_status['postgresql'] = 'disconnected'

    # 检查Neo4j
    try:
        if neo4j_client and neo4j_client.is_connected():
            services_status['neo4j'] = 'connected'
        else:
            services_status['neo4j'] = 'disconnected'
    except Exception as e:
        logger.debug(f"Neo4j check failed: {e}")
        services_status['neo4j'] = 'disconnected'

    # 检查Redis
    try:
        if redis_client and redis_client.is_connected():
            services_status['redis'] = 'connected'
        else:
            services_status['redis'] = 'disconnected'
    except Exception as e:
        logger.debug(f"Redis check failed: {e}")
        services_status['redis'] = 'disconnected'

    return services_status

def get_uptime():
    """获取服务运行时间（简化版本）"""
    # 这里可以存储应用启动时间，然后计算差值
    # 为简化，这里返回当前时间
    return datetime.utcnow().isoformat()
