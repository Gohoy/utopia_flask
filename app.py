import os
import sys
from app import create_app, db

app = create_app(os.getenv('FLASK_ENV', 'default'))

if __name__ == '__main__':
    # 处理命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'setup':
            print("🚀 请使用独立的设置脚本:")
            print("   python scripts/setup_complete_db.py")
            sys.exit(0)
        else:
            print(f"❌ 未知命令: {command}")
            print("💡 请使用: python scripts/setup_complete_db.py")
            sys.exit(1)
    else:
        # 正常启动Flask应用
        print("🚀 启动虚拟乌托邦服务...")
        print("📍 端口: 15000")
        print("📍 健康检查: http://localhost:15000/health")
        print("📍 认证API: http://localhost:15000/api/auth/")
        print("📍 图鉴API: http://localhost:15000/api/entries/")
        app.run(host='0.0.0.0', port=15000, debug=True)
