import pytest
import json

def test_health_check(client):
    """测试健康检查"""
    response = client.get('/health')
    assert response.status_code == 200

    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'endpoints' in data

def test_user_registration(client):
    """测试用户注册"""
    user_data = {
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'password123',
        'nickname': '新用户'
    }

    response = client.post('/api/auth/register',
                           json=user_data,
                           content_type='application/json')

    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] == True
    assert data['data']['user']['username'] == 'newuser'

def test_user_login(client, test_user):
    """测试用户登录"""
    login_data = {
        'username': 'testuser',
        'password': 'password123'
    }

    response = client.post('/api/auth/login',
                           json=login_data,
                           content_type='application/json')

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'tokens' in data['data']
    assert 'access_token' in data['data']['tokens']

def test_get_profile(client, auth_headers):
    """测试获取用户信息"""
    response = client.get('/api/auth/profile', headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert data['data']['user']['username'] == 'testuser'

def test_update_profile(client, auth_headers):
    """测试更新用户信息"""
    update_data = {
        'nickname': '更新后的昵称',
        'bio': '这是我的个人简介'
    }

    response = client.put('/api/auth/profile',
                          json=update_data,
                          headers=auth_headers,
                          content_type='application/json')

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert data['data']['user']['nickname'] == '更新后的昵称'

def test_login_invalid_credentials(client):
    """测试无效凭据登录"""
    login_data = {
        'username': 'nonexistent',
        'password': 'wrongpassword'
    }

    response = client.post('/api/auth/login',
                           json=login_data,
                           content_type='application/json')

    assert response.status_code == 401
    data = response.get_json()
    assert data['success'] == False

def test_registration_duplicate_username(client, test_user):
    """测试重复用户名注册"""
    user_data = {
        'username': 'testuser',  # 已存在的用户名
        'email': 'another@example.com',
        'password': 'password123'
    }

    response = client.post('/api/auth/register',
                           json=user_data,
                           content_type='application/json')

    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] == False
    assert '已存在' in data['message']
