# conftest.py
import pytest
import os
import sys
import uuid

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db, neo4j_client
from app.models.user import User, UserPermission

@pytest.fixture(scope='session')
def app():
    """创建测试应用"""
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'JWT_SECRET_KEY': 'test-secret-key',
        # Neo4j测试配置
        'NEO4J_URI': os.getenv('NEO4J_TEST_URI', 'bolt://localhost:7687'),
        'NEO4J_USER': os.getenv('NEO4J_TEST_USER', 'neo4j'),
        'NEO4J_PASSWORD': os.getenv('NEO4J_TEST_PASSWORD', 'password'),
    })

    with app.app_context():
        db.create_all()
        yield app

        # 清理资源
        db.drop_all()

        # 清理Neo4j连接
        if neo4j_client:
            neo4j_client.close()

@pytest.fixture(scope='function')
def client(app):
    """创建测试客户端"""
    return app.test_client()

# conftest.py - 最终推荐版本
@pytest.fixture(scope='function', autouse=True)
def clean_db(app):
    """每个测试前后清理数据库"""
    with app.app_context():
        # 测试前清理
        clean_test_data_safely()
        clean_neo4j_test_data()

        yield

        # 测试后清理
        clean_test_data_safely()
        clean_neo4j_test_data()

def clean_test_data_safely():
    """安全地清理测试数据"""
    try:
        from app.models.user import User

        # 只删除测试用户及其相关数据
        # SQLAlchemy的cascade会自动处理相关数据的删除
        test_users = User.query.filter(
            db.or_(
                User.email.like('%test%'),
                User.username.like('%test%')
            )
        ).all()

        for user in test_users:
            db.session.delete(user)  # 会级联删除相关的Entry、UserPermission等

        db.session.commit()
        if test_users:
            print(f"清理了 {len(test_users)} 个测试用户及其相关数据")

    except Exception as e:
        db.session.rollback()
        print(f"数据库清理失败: {e}")
        # 测试继续进行，不抛出异常

def clean_neo4j_test_data():
    """清理Neo4j中的测试数据"""
    if not neo4j_client or not neo4j_client.is_connected():
        return

    try:
        with neo4j_client.get_session() as session:
            # 删除所有测试相关标签
            session.run("""
                MATCH (t:Tag)
                WHERE t.name CONTAINS '测试' 
                OR t.name CONTAINS 'Test'
                OR t.category = 'test'
                OR t.id STARTS WITH 'test_'
                OR t.name_en CONTAINS 'Test'
                DETACH DELETE t
            """)
            print("Neo4j测试数据清理完成")
    except Exception as e:
        print(f"清理Neo4j测试数据失败: {e}")

@pytest.fixture
def test_user(app):
    """创建测试用户"""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            nickname='测试用户'
        )
        user.set_password('password123')

        db.session.add(user)
        db.session.flush()

        permissions = UserPermission(
            user_id=user.id,
            can_create_tags=True,
            can_edit_tags=True,
            can_approve_changes=False,
            max_edits_per_day=100
        )
        db.session.add(permissions)
        db.session.commit()

        return user

@pytest.fixture
def auth_headers(client, test_user):
    """获取认证头"""
    login_data = {
        'username': 'testuser',
        'password': 'password123'
    }

    response = client.post('/api/auth/login',
                           json=login_data,
                           content_type='application/json')

    assert response.status_code == 200
    data = response.get_json()
    token = data['data']['tokens']['access_token']

    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def unique_tag_name():
    """生成唯一的标签名称"""
    return f"测试标签_{str(uuid.uuid4())[:8]}"
