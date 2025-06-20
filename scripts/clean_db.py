import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def clean_database():
    """彻底清理数据库"""

    # 数据库连接配置
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'user': 'utopia_user',
        'password': 'utopia_password',
        'database': 'utopia_db'
    }

    try:
        # 连接数据库
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        print("🔍 检查现有表...")

        # 查看所有表
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public';
        """)

        tables = cursor.fetchall()
        print(f"现有表: {[table[0] for table in tables]}")

        # 删除所有表
        for table in tables:
            table_name = table[0]
            if table_name != 'alembic_version':  # 保留迁移版本表
                print(f"🗑️  删除表: {table_name}")
                cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")

        print("✅ 数据库清理完成")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ 数据库清理失败: {e}")

if __name__ == '__main__':
    clean_database()
