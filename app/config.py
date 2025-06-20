import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-this'

    # 数据库配置
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        DATABASE_URL = 'postgresql://utopia_user:utopia_password@localhost:5432/utopia_db'

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 20
    }

    # Neo4j配置
    NEO4J_URI = os.environ.get('NEO4J_URI') or 'bolt://localhost:7687'
    NEO4J_USER = os.environ.get('NEO4J_USER') or 'neo4j'
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD') or 'utopia_neo4j_password'

    # Redis配置
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://:utopia_redis_password@localhost:6379/0'

    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string-change-this'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 86400))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    SWAGGER = {
        'title': '虚拟乌托邦 API',
        'uiversion': 3,
        'doc_dir': './docs/',
        'info': {
            'title': '虚拟乌托邦 API',
            'version': '1.0.0',
            'description': '万物皆可图鉴的协作平台 API'
        }
    }


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    TESTING = False
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
