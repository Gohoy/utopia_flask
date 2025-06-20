import pytest
import json
from datetime import datetime

def test_create_entry(client, auth_headers):
    """测试创建图鉴条目"""
    entry_data = {
        'title': '我的第一只猫',
        'content': '今天遇到了一只很可爱的橙色小猫',
        'content_type': 'mixed',
        'location_name': '公园',
        'geo_coordinates': '39.9042,116.4074',
        'mood_score': 8,
        'visibility': 'public',
        'tags': ['felis_catus', 'happiness']
    }

    response = client.post('/api/entries',
                           json=entry_data,
                           headers=auth_headers,
                           content_type='application/json')

    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] == True
    assert data['data']['entry']['title'] == '我的第一只猫'
    assert data['data']['entry']['mood_score'] == 8

    return data['data']['entry']['id']

def test_get_entry(client, auth_headers):
    """测试获取图鉴条目"""
    # 先创建一个条目
    entry_id = test_create_entry(client, auth_headers)

    # 获取条目
    response = client.get(f'/api/entries/{entry_id}')

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert data['data']['entry']['id'] == entry_id

def test_update_entry(client, auth_headers):
    """测试更新图鉴条目"""
    # 先创建一个条目
    entry_id = test_create_entry(client, auth_headers)

    # 更新条目
    update_data = {
        'title': '我的第一只猫（更新版）',
        'content': '今天遇到了一只很可爱的橙色小猫，后来发现它有主人',
        'mood_score': 9
    }

    response = client.put(f'/api/entries/{entry_id}',
                          json=update_data,
                          headers=auth_headers,
                          content_type='application/json')

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert data['data']['entry']['title'] == '我的第一只猫（更新版）'
    assert data['data']['entry']['mood_score'] == 9

def test_get_entries_list(client, auth_headers):
    """测试获取图鉴列表"""
    # 先创建几个条目
    test_create_entry(client, auth_headers)

    # 获取列表
    response = client.get('/api/entries?page=1&per_page=10')

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'entries' in data['data']
    assert 'pagination' in data['data']

def test_get_my_entries(client, auth_headers):
    """测试获取我的图鉴"""
    # 先创建一个条目
    test_create_entry(client, auth_headers)

    # 获取我的图鉴
    response = client.get('/api/entries/my', headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert len(data['data']['entries']) >= 1

def test_search_entries(client, auth_headers):
    """测试搜索图鉴"""
    # 先创建一个条目
    test_create_entry(client, auth_headers)

    # 搜索
    response = client.get('/api/entries/search?q=猫')

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True

def test_get_user_stats(client, auth_headers):
    """测试获取用户统计"""
    # 先创建一个条目
    test_create_entry(client, auth_headers)

    # 获取统计
    response = client.get('/api/entries/my/stats', headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'stats' in data['data']
    assert data['data']['stats']['total_entries'] >= 1

def test_create_entry_missing_title(client, auth_headers):
    """测试创建条目缺少标题"""
    entry_data = {
        'content': '没有标题的条目'
    }

    response = client.post('/api/entries',
                           json=entry_data,
                           headers=auth_headers,
                           content_type='application/json')

    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] == False

def test_delete_entry(client, auth_headers):
    """测试删除图鉴条目"""
    # 先创建一个条目
    entry_id = test_create_entry(client, auth_headers)

    # 删除条目
    response = client.delete(f'/api/entries/{entry_id}', headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True

    # 验证条目已被软删除
    response = client.get(f'/api/entries/{entry_id}')
    assert response.status_code == 404

def test_unauthorized_access(client):
    """测试未授权访问"""
    entry_data = {
        'title': '测试条目',
        'content': '这应该失败'
    }

    response = client.post('/api/entries',
                           json=entry_data,
                           content_type='application/json')

    assert response.status_code == 401
