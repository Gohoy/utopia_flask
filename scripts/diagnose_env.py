import sys
import os
import subprocess
import importlib

def check_python_env():
    """检查Python环境"""
    print("🐍 Python环境检查")
    print("-" * 30)
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"虚拟环境: {'是' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else '否'}")
    print(f"工作目录: {os.getcwd()}")
    print()

def check_required_packages():
    """检查必需的包"""
    print("📦 依赖包检查")
    print("-" * 30)

    required_packages = [
        'flask', 'flask_sqlalchemy', 'flask_jwt_extended',
        'flask_cors', 'flask_limiter', 'flask_migrate',
        'psycopg2', 'neo4j', 'redis', 'requests',
        'pytest', 'pytest-cov'
    ]

    missing_packages = []
    version_info = {}

    for package in required_packages:
        try:
            # 特殊处理带下划线的包名
            import_name = package.replace('-', '_').replace('flask_', 'flask.')
            if import_name == 'flask.sqlalchemy':
                import_name = 'flask_sqlalchemy'
            elif import_name == 'flask.jwt_extended':
                import_name = 'flask_jwt_extended'
            elif import_name == 'flask.cors':
                import_name = 'flask_cors'
            elif import_name == 'flask.limiter':
                import_name = 'flask_limiter'
            elif import_name == 'flask.migrate':
                import_name = 'flask_migrate'
            elif import_name == 'pytest_cov':
                import_name = 'pytest_cov'

            module = importlib.import_module(import_name)
            version = getattr(module, '__version__', 'Unknown')
            version_info[package] = version
            print(f"✅ {package}: {version}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}: 未安装")

    if missing_packages:
        print(f"\n⚠️ 缺失的包: {', '.join(missing_packages)}")
        return False, missing_packages

    return True, version_info

def check_project_structure():
    """检查项目结构"""
    print("\n📁 项目结构检查")
    print("-" * 30)

    required_dirs = ['app', 'tests', 'scripts']
    required_files = ['app.py', 'requirements.txt']

    all_good = True

    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✅ {dir_name}/ 目录存在")
        else:
            print(f"❌ {dir_name}/ 目录缺失")
            all_good = False

    for file_name in required_files:
        if os.path.exists(file_name):
            print(f"✅ {file_name} 文件存在")
        else:
            print(f"❌ {file_name} 文件缺失")
            all_good = False

    return all_good

def check_test_files():
    """检查测试文件"""
    print("\n🧪 测试文件检查")
    print("-" * 30)

    test_files = [
        'tests/conftest.py',
        'tests/test_auth.py',
        'tests/test_entries.py',
        'tests/test_tags.py'
    ]

    all_good = True

    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"✅ {test_file} 存在")
            # 检查文件是否为空
            try:
                with open(test_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        print(f"   内容: {len(content)} 字符")
                    else:
                        print(f"   ⚠️ 文件为空")
            except Exception as e:
                print(f"   ❌ 读取失败: {e}")
        else:
            print(f"❌ {test_file} 缺失")
            all_good = False

    return all_good

def check_database_connection():
    """检查数据库连接"""
    print("\n🗄️ 数据库连接检查")
    print("-" * 30)

    try:
        # 添加项目路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, project_root)

        from app import create_app, db

        app = create_app('testing')
        with app.app_context():
            # 测试数据库连接
            try:
                db.engine.execute('SELECT 1')
                print("✅ 测试数据库连接成功")
                return True
            except Exception as e:
                print(f"❌ 测试数据库连接失败: {e}")
                return False
    except Exception as e:
        print(f"❌ 无法创建测试应用: {e}")
        return False

def run_simple_test():
    """运行简单测试"""
    print("\n🎯 简单测试运行")
    print("-" * 30)

    try:
        # 运行pytest --version
        result = subprocess.run(['pytest', '--version'],
                                capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ pytest版本: {result.stdout.strip()}")
        else:
            print(f"❌ pytest版本检查失败: {result.stderr}")
            return False

        # 运行简单测试
        result = subprocess.run(['pytest', '--collect-only', '-q'],
                                capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 测试收集成功")
            print(f"   收集信息: {result.stdout.strip()}")
        else:
            print("❌ 测试收集失败")
            print(f"   错误: {result.stderr}")
            return False

        return True
    except FileNotFoundError:
        print("❌ pytest命令未找到")
        return False
    except Exception as e:
        print(f"❌ 测试运行异常: {e}")
        return False

def main():
    """主诊断流程"""
    print("🔍 测试环境诊断")
    print("=" * 50)

    # 1. Python环境检查
    check_python_env()

    # 2. 依赖包检查
    packages_ok, package_info = check_required_packages()

    # 3. 项目结构检查
    structure_ok = check_project_structure()

    # 4. 测试文件检查
    test_files_ok = check_test_files()

    # 5. 数据库连接检查
    db_ok = check_database_connection()

    # 6. 简单测试运行
    simple_test_ok = run_simple_test()

    # 总结
    print("\n📊 诊断总结")
    print("=" * 50)

    issues = []
    if not packages_ok:
        issues.append("缺失依赖包")
    if not structure_ok:
        issues.append("项目结构不完整")
    if not test_files_ok:
        issues.append("测试文件问题")
    if not db_ok:
        issues.append("数据库连接问题")
    if not simple_test_ok:
        issues.append("pytest运行问题")

    if issues:
        print(f"❌ 发现问题: {', '.join(issues)}")
        print("\n💡 建议修复步骤:")

        if not packages_ok:
            print("1. 重新安装依赖: pip install -r requirements.txt")
        if not simple_test_ok:
            print("2. 重新安装pytest: pip install pytest pytest-cov")
        if not db_ok:
            print("3. 检查数据库服务: docker-compose up -d")

        return False
    else:
        print("✅ 环境检查通过！")
        return True

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1)
