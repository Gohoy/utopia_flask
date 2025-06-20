import requests
import pytest
import time

BASE_URL = "http://localhost:15000"

class TestIntegration:
    """集成测试 - 需要运行的服务器"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """设置测试"""
        # 等待服务器启动
        self.wait_for_server()

    def wait_for_server(self, max_attempts=5):
        """等待服务器启动"""
        for i in range(max_attempts):
            try:
                response = requests.get(f"{BASE_URL}/health", timeout=2)
                if response.status_code == 200:
                    return True
            except:
                if i < max_attempts - 1:
                    time.sleep(1)
                    continue
        pytest.skip("服务器未运行，跳过集成测试")

    def test_full_workflow(self):
        """测试完整工作流程"""
        # 1. 注册用户
        register_data = {
            "username": "integrationuser",
            "email": "integration@test.com",
            "password": "password123",
            "nickname": "集成测试用户"
        }

        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        if response.status_code == 400 and "已存在" in response.json().get('message', ''):
            pass  # 用户已存在，继续测试
        else:
            assert response.status_code == 201

        # 2. 登录
        login_data = {
            "username": "integrationuser",
            "password": "password123"
        }

        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        assert response.status_code == 200

        token = response.json()['data']['tokens']['access_token']
        headers = {"Authorization": f"Bearer {token}"}

        # 3. 创建图鉴条目
        entry_data = {
            "title": "集成测试图鉴",
            "content": "这是一个集成测试创建的图鉴条目",
            "content_type": "text",
            "mood_score": 7,
            "visibility": "public",
            "tags": ["test", "integration"]
        }

        response = requests.post(f"{BASE_URL}/api/entries", json=entry_data, headers=headers)
        assert response.status_code == 201

        entry_id = response.json()['data']['entry']['id']

        # 4. 获取图鉴条目
        response = requests.get(f"{BASE_URL}/api/entries/{entry_id}")
        assert response.status_code == 200
        assert response.json()['data']['entry']['title'] == "集成测试图鉴"

        # 5. 更新图鉴条目
        update_data = {
            "title": "集成测试图鉴(更新版)",
            "mood_score": 8
        }

        response = requests.put(f"{BASE_URL}/api/entries/{entry_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        assert response.json()['data']['entry']['mood_score'] == 8

        # 6. 搜索图鉴
        response = requests.get(f"{BASE_URL}/api/entries/search?q=集成测试")
        assert response.status_code == 200

        # 7. 获取用户统计
        response = requests.get(f"{BASE_URL}/api/entries/my/stats", headers=headers)
        assert response.status_code == 200
        assert response.json()['data']['stats']['total_entries'] >= 1

        print("✅ 集成测试完整工作流程通过")
