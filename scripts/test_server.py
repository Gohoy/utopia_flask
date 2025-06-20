import requests
import time
import sys

BASE_URL = "http://localhost:15000"

def test_server_startup():
    """测试服务器启动状态"""
    print("🧪 测试服务器状态...")

    try:
        # 测试健康检查
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 服务器健康检查通过")
            print(f"   状态: {data['status']}")
            print(f"   版本: {data['version']}")
            print(f"   可用端点: {data['endpoints']}")

            # 测试登录API
            login_data = {
                "username": "testuser",
                "password": "password123"
            }

            response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
            if response.status_code == 200:
                print("✅ 认证API正常工作")

                # 获取token并测试entries API
                token = response.json()['data']['tokens']['access_token']
                headers = {"Authorization": f"Bearer {token}"}

                # 测试获取图鉴列表
                response = requests.get(f"{BASE_URL}/api/entries", headers=headers)
                if response.status_code == 200:
                    print("✅ 图鉴API正常工作")
                    entries_data = response.json()['data']
                    print(f"   图鉴总数: {entries_data['pagination']['total']}")
                    return True
                else:
                    print(f"❌ 图鉴API测试失败: {response.status_code}")
                    print(f"   响应: {response.text}")
            else:
                print(f"❌ 认证API测试失败: {response.status_code}")
                print(f"   响应: {response.text}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            print(f"   响应: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        print("💡 请确保服务器正在运行: python app.py")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

    return False

if __name__ == "__main__":
    success = test_server_startup()
    if success:
        print("\n🎉 服务器测试通过！所有API正常工作")
    else:
        print("\n❌ 服务器测试失败")
        sys.exit(1)
