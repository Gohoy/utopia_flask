import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def clean_database():
    """清理数据库"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='utopia_user',
            password='utopia_password',
            database='utopia_db'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        print("🗑️ 清理数据库...")
        cursor.execute("""
            DROP SCHEMA public CASCADE;
            CREATE SCHEMA public;
            GRANT ALL ON SCHEMA public TO utopia_user;
            GRANT ALL ON SCHEMA public TO public;
        """)

        cursor.close()
        conn.close()
        print("✅ 数据库清理完成")
        return True

    except Exception as e:
        print(f"❌ 数据库清理失败: {e}")
        return False

def setup_complete_database():
    """设置完整数据库"""
    print("🚀 开始设置虚拟乌托邦数据库（完整版）...")

    # 清理数据库
    if not clean_database():
        return False

    # 创建Flask应用
    from app import create_app, db
    app = create_app('development')

    with app.app_context():
        try:
            # 导入所有模型
            from app.models.user import User, UserPermission
            from app.models.entry import Entry, EntryTag
            from app.models.media import MediaFile

            print("📋 创建数据库表...")
            db.create_all()
            print("✅ 数据库表创建成功")

            # 创建测试用户
            print("👤 创建测试用户...")
            test_user = User(
                username='testuser',
                email='test@example.com',
                nickname='测试用户',
                bio='这是一个测试用户账号，用于开发和测试'
            )
            test_user.set_password('password123')

            db.session.add(test_user)
            db.session.flush()

            # 创建用户权限
            permissions = UserPermission(
                user_id=test_user.id,
                can_create_tags=True,
                can_edit_tags=True,
                can_approve_changes=False,
                max_edits_per_day=100
            )
            db.session.add(permissions)

            # 创建管理员用户
            print("👑 创建管理员用户...")
            admin_user = User(
                username='admin',
                email='admin@utopia.com',
                nickname='管理员',
                bio='系统管理员账号'
            )
            admin_user.set_password('admin123')

            db.session.add(admin_user)
            db.session.flush()

            admin_permissions = UserPermission(
                user_id=admin_user.id,
                can_create_tags=True,
                can_edit_tags=True,
                can_approve_changes=True,
                max_edits_per_day=1000
            )
            db.session.add(admin_permissions)

            # 创建示例图鉴条目
            print("📝 创建示例图鉴条目...")
            sample_entry = Entry(
                user_id=test_user.id,
                title="我的第一个图鉴条目",
                content="这是一个示例图鉴条目，用于测试系统功能。",
                content_type="text",
                location_name="测试地点",
                mood_score=8,
                visibility="public"
            )
            db.session.add(sample_entry)
            db.session.flush()

            # 为示例条目添加标签
            sample_tag = EntryTag(
                entry_id=sample_entry.id,
                tag_id="test_tag",
                tagged_by=test_user.id,
                source="manual"
            )
            db.session.add(sample_tag)

            # 提交所有更改
            db.session.commit()

            print("✅ 数据库设置完成！")
            print("\n📋 创建的账号:")
            print("  👤 测试用户:")
            print(f"     用户名: {test_user.username}")
            print(f"     邮箱: {test_user.email}")
            print("     密码: password123")
            print(f"     ID: {test_user.id}")

            print("  👑 管理员:")
            print(f"     用户名: {admin_user.username}")
            print(f"     邮箱: {admin_user.email}")
            print("     密码: admin123")
            print(f"     ID: {admin_user.id}")

            print(f"\n📝 示例图鉴条目:")
            print(f"     标题: {sample_entry.title}")
            print(f"     ID: {sample_entry.id}")

            return True

        except Exception as e:
            print(f"❌ 数据库设置失败: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = setup_complete_database()
    if success:
        print("\n🎉 数据库设置成功！现在可以启动应用了:")
        print("   python app.py")
        print("\n📋 可用的API端点:")
        print("   • GET  /health - 健康检查")
        print("   • POST /api/auth/register - 用户注册")
        print("   • POST /api/auth/login - 用户登录")
        print("   • GET  /api/auth/profile - 获取用户信息")
        print("   • POST /api/entries - 创建图鉴条目")
        print("   • GET  /api/entries - 获取图鉴列表")
        print("   • GET  /api/entries/<id> - 获取单个图鉴")
    else:
        print("\n❌ 数据库设置失败")
        sys.exit(1)
