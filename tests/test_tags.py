# test_tags.py
import pytest
import json
import uuid

def test_create_tag(client, auth_headers, unique_tag_name):
    """测试创建标签"""
    tag_data = {
        'name': unique_tag_name,
        'description': '这是一个测试标签',
        'category': 'test',
        'name_en': f'Test Tag {str(uuid.uuid4())[:8]}',
        'aliases': ['测试', 'test']
    }

    response = client.post('/api/tags',
                           json=tag_data,
                           headers=auth_headers,
                           content_type='application/json')

    # 添加调试信息
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.get_data(as_text=True)}")

    # 如果Neo4j不可用，跳过测试
    if response.status_code == 503:
        pytest.skip("Neo4j服务不可用")

    # 如果是400错误，打印详细信息
    if response.status_code == 400:
        error_data = response.get_json()
        print(f"400 Error details: {error_data}")
        # 如果是标签已存在的错误，说明数据清理有问题
        if "已存在" in error_data.get('message', ''):
            pytest.fail(f"测试数据清理失败，标签仍然存在: {unique_tag_name}")

    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] == True
    assert data['data']['tag']['name'] == unique_tag_name

def test_create_duplicate_tag(client, auth_headers, unique_tag_name):
    """测试创建重复标签"""
    tag_data = {
        'name': unique_tag_name,
        'description': '这是一个测试标签',
        'category': 'test'
    }

    # 第一次创建应该成功
    response1 = client.post('/api/tags',
                            json=tag_data,
                            headers=auth_headers,
                            content_type='application/json')

    if response1.status_code == 503:
        pytest.skip("Neo4j服务不可用")

    assert response1.status_code == 201

    # 第二次创建相同标签应该失败
    response2 = client.post('/api/tags',
                            json=tag_data,
                            headers=auth_headers,
                            content_type='application/json')

    assert response2.status_code == 400
    data = response2.get_json()
    assert "已存在" in data['message']

def test_search_tags(client):
    """测试搜索标签"""
    # 先创建一些测试标签供搜索
    if neo4j_client and neo4j_client.is_connected():
        create_test_search_data()

    response = client.get('/api/tags/search?q=猫')

    print(f"Search response status: {response.status_code}")
    if response.status_code != 200:
        print(f"Search error: {response.get_data(as_text=True)}")

    if response.status_code == 503:
        pytest.skip("Neo4j服务不可用")

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'tags' in data['data']

def test_get_popular_tags(client):
    """测试获取热门标签"""
    # 创建一些热门标签数据
    if neo4j_client and neo4j_client.is_connected():
        create_test_popular_data()

    response = client.get('/api/tags/popular?limit=10')

    print(f"Popular tags response status: {response.status_code}")
    if response.status_code != 200:
        print(f"Popular tags error: {response.get_data(as_text=True)}")

    if response.status_code == 503:
        pytest.skip("Neo4j服务不可用")

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'tags' in data['data']

def test_get_tag_tree(client):
    """测试获取标签树"""
    response = client.get('/api/tags/tree')

    if response.status_code == 503:
        pytest.skip("Neo4j服务不可用")

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True

def test_validate_tags(client):
    """测试标签验证"""
    # 先创建一些标签用于验证
    test_tag_ids = []
    if neo4j_client and neo4j_client.is_connected():
        test_tag_ids = create_test_validation_data()

    validation_data = {
        'tag_ids': test_tag_ids + ['nonexistent_tag']
    }

    response = client.post('/api/tags/validate',
                           json=validation_data,
                           content_type='application/json')

    if response.status_code == 503:
        pytest.skip("Neo4j服务不可用")

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'valid_tags' in data['data']

def test_get_recommended_tags(client):
    """测试获取推荐标签"""
    # 创建一些标签用于推荐
    test_tag_ids = []
    if neo4j_client and neo4j_client.is_connected():
        test_tag_ids = create_test_recommendation_data()

    recommend_data = {
        'tags': test_tag_ids[:1] if test_tag_ids else ['test_tag']
    }

    response = client.post('/api/tags/recommend',
                           json=recommend_data,
                           content_type='application/json')

    if response.status_code == 503:
        pytest.skip("Neo4j服务不可用")

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'recommended_tags' in data['data']

def test_get_tag_categories(client):
    """测试获取标签分类"""
    response = client.get('/api/tags/categories')

    if response.status_code == 503:
        pytest.skip("Neo4j服务不可用")

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'categories' in data['data']

def test_unauthorized_tag_creation(client):
    """测试未授权创建标签"""
    tag_data = {
        'name': f'未授权标签_{str(uuid.uuid4())[:8]}',
        'description': '这应该失败'
    }

    response = client.post('/api/tags',
                           json=tag_data,
                           content_type='application/json')

    assert response.status_code == 401
# test_tags.py - 修改测试函数
def test_entry_with_tags(client, auth_headers):
    """测试创建带标签的图鉴条目"""
    # 先创建一些标签
    test_tag_ids = []
    if neo4j_client and neo4j_client.is_connected():
        test_tag_ids = create_test_entry_tags()
        print(f"Created test tag IDs: {test_tag_ids}")
    else:
        print("Neo4j not connected, using default tags")

    entry_data = {
        'title': '带标签的图鉴',
        'content': '这个图鉴条目有标签',
        'tags': test_tag_ids if test_tag_ids else []  # 如果没有标签就传空数组
    }

    print(f"Entry data: {entry_data}")

    response = client.post('/api/entries',
                           json=entry_data,
                           headers=auth_headers,
                           content_type='application/json')

    # 添加详细调试信息
    print(f"Entry creation response status: {response.status_code}")
    print(f"Entry creation response data: {response.get_data(as_text=True)}")

    # 如果是400错误，打印详细信息
    if response.status_code == 400:
        error_data = response.get_json()
        print(f"Entry creation error details: {error_data}")

    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] == True
    assert 'tags' in data['data']['entry']

# 修改创建测试标签的函数
def create_test_entry_tags():
    """创建图鉴条目标签测试数据"""
    if not neo4j_client or not neo4j_client.is_connected():
        print("Neo4j client not available")
        return []

    tag_ids = []
    test_tags = [
        {
            'id': f'entry_tag_1_{uuid.uuid4().hex[:8]}',
            'name': f'图鉴标签1_{uuid.uuid4().hex[:4]}',
            'category': 'entry',
            'status': 'active',
            'usage_count': 0,
            'quality_score': 5.0,
            'created_at': datetime.utcnow().isoformat()
        },
        {
            'id': f'entry_tag_2_{uuid.uuid4().hex[:8]}',
            'name': f'图鉴标签2_{uuid.uuid4().hex[:4]}',
            'category': 'entry',
            'status': 'active',
            'usage_count': 0,
            'quality_score': 5.0,
            'created_at': datetime.utcnow().isoformat()
        }
    ]

    try:
        with neo4j_client.get_session() as session:
            for tag in test_tags:
                result = session.run("""
                    CREATE (t:Tag $properties)
                    RETURN t.id as id
                """, properties=tag)
                record = result.single()
                if record:
                    tag_ids.append(record['id'])
                    print(f"Created tag: {record['id']}")

        print(f"Successfully created {len(tag_ids)} tags: {tag_ids}")
        return tag_ids
    except Exception as e:
        print(f"创建图鉴标签测试数据失败: {e}")
        return []

# 辅助函数：创建测试数据
def create_test_search_data():
    """创建搜索测试数据"""
    if not neo4j_client or not neo4j_client.is_connected():
        return

    test_tags = [
        {
            'id': f'search_cat_{uuid.uuid4().hex[:8]}',
            'name': '猫咪',
            'category': 'animal',
            'status': 'active',
            'usage_count': 10
        }
    ]

    try:
        with neo4j_client.get_session() as session:
            for tag in test_tags:
                session.run("""
                    CREATE (t:Tag $properties)
                """, properties=tag)
    except Exception as e:
        print(f"创建搜索测试数据失败: {e}")

def create_test_popular_data():
    """创建热门标签测试数据"""
    if not neo4j_client or not neo4j_client.is_connected():
        return

    test_tags = [
        {
            'id': f'popular_tag_{uuid.uuid4().hex[:8]}',
            'name': f'热门标签_{uuid.uuid4().hex[:4]}',
            'category': 'popular',
            'status': 'active',
            'usage_count': 100
        }
    ]

    try:
        with neo4j_client.get_session() as session:
            for tag in test_tags:
                session.run("""
                    CREATE (t:Tag $properties)
                """, properties=tag)
    except Exception as e:
        print(f"创建热门标签测试数据失败: {e}")

def create_test_validation_data():
    """创建验证测试数据"""
    if not neo4j_client or not neo4j_client.is_connected():
        return []

    tag_ids = []
    test_tags = [
        {
            'id': f'valid_tag_{uuid.uuid4().hex[:8]}',
            'name': f'有效标签_{uuid.uuid4().hex[:4]}',
            'category': 'test',
            'status': 'active'
        }
    ]

    try:
        with neo4j_client.get_session() as session:
            for tag in test_tags:
                session.run("""
                    CREATE (t:Tag $properties)
                """, properties=tag)
                tag_ids.append(tag['id'])
        return tag_ids
    except Exception as e:
        print(f"创建验证测试数据失败: {e}")
        return []

def create_test_recommendation_data():
    """创建推荐测试数据"""
    if not neo4j_client or not neo4j_client.is_connected():
        return []

    tag_ids = []
    test_tags = [
        {
            'id': f'recommend_tag_{uuid.uuid4().hex[:8]}',
            'name': f'推荐标签_{uuid.uuid4().hex[:4]}',
            'category': 'recommendation',
            'status': 'active',
            'usage_count': 20
        }
    ]

    try:
        with neo4j_client.get_session() as session:
            for tag in test_tags:
                session.run("""
                    CREATE (t:Tag $properties)
                """, properties=tag)
                tag_ids.append(tag['id'])
        return tag_ids
    except Exception as e:
        print(f"创建推荐测试数据失败: {e}")
        return []

def create_test_entry_tags():
    """创建图鉴条目标签测试数据"""
    if not neo4j_client or not neo4j_client.is_connected():
        return []

    tag_ids = []
    test_tags = [
        {
            'id': f'entry_tag_1_{uuid.uuid4().hex[:8]}',
            'name': f'图鉴标签1_{uuid.uuid4().hex[:4]}',
            'category': 'entry',
            'status': 'active'
        },
        {
            'id': f'entry_tag_2_{uuid.uuid4().hex[:8]}',
            'name': f'图鉴标签2_{uuid.uuid4().hex[:4]}',
            'category': 'entry',
            'status': 'active'
        }
    ]

    try:
        with neo4j_client.get_session() as session:
            for tag in test_tags:
                session.run("""
                    CREATE (t:Tag $properties)
                """, properties=tag)
                tag_ids.append(tag['id'])
        return tag_ids
    except Exception as e:
        print(f"创建图鉴标签测试数据失败: {e}")
        return []

# 在文件开头添加导入
from app import neo4j_client
