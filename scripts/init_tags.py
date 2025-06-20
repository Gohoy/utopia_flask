import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app
from app.utils.neo4j_client import Neo4jClient

# 基础标签树数据（保持不变）
INITIAL_TAGS = [
    # 根节点
    {
        'id': 'root',
        'name': '万物图鉴',
        'name_en': 'Universal Encyclopedia',
        'description': '包含一切可记录事物的根分类',
        'level': 0,
        'category': 'root',
        'status': 'active',
        'quality_score': 10.0,
        'usage_count': 0,
        'created_by': 'system',
        'aliases': ['根节点', '全部'],
        'applicable_content_types': ['text', 'image', 'video', 'audio']
    },

    # 一级分类
    {
        'id': 'existence',
        'name': '存在界',
        'name_en': 'Existence Realm',
        'description': '一切有形的、可感知的客观存在',
        'level': 1,
        'category': 'philosophical',
        'parent_id': 'root',
        'aliases': ['物质世界', '客观存在']
    },
    {
        'id': 'consciousness',
        'name': '意识界',
        'name_en': 'Consciousness Realm',
        'description': '精神层面的、主观的内在体验',
        'level': 1,
        'category': 'philosophical',
        'parent_id': 'root',
        'aliases': ['精神世界', '主观体验', '内在世界']
    },

    # 生物分类
    {
        'id': 'life',
        'name': '生命域',
        'name_en': 'Life Domain',
        'description': '所有具有生命特征的存在',
        'level': 2,
        'category': 'biological',
        'parent_id': 'existence',
        'aliases': ['生物域', '生命体']
    },
    {
        'id': 'animalia',
        'name': '动物界',
        'name_en': 'Animalia',
        'scientific_name': 'Animalia',
        'description': '真核多细胞异养生物',
        'level': 3,
        'category': 'biological',
        'parent_id': 'life',
        'aliases': ['动物', 'Animal Kingdom']
    },
    {
        'id': 'plantae',
        'name': '植物界',
        'name_en': 'Plantae',
        'scientific_name': 'Plantae',
        'description': '自养的真核生物，通常进行光合作用',
        'level': 3,
        'category': 'biological',
        'parent_id': 'life',
        'aliases': ['植物', 'Plant Kingdom']
    },

    # 动物详细分类
    {
        'id': 'chordata',
        'name': '脊索动物门',
        'name_en': 'Chordata',
        'scientific_name': 'Chordata',
        'description': '具有脊索、背神经管等特征',
        'level': 4,
        'category': 'biological',
        'parent_id': 'animalia',
        'aliases': ['脊索动物']
    },
    {
        'id': 'mammalia',
        'name': '哺乳纲',
        'name_en': 'Mammalia',
        'scientific_name': 'Mammalia',
        'description': '温血脊椎动物，具毛发，哺乳喂养幼体',
        'level': 5,
        'category': 'biological',
        'parent_id': 'chordata',
        'aliases': ['哺乳动物', 'mammals']
    },
    {
        'id': 'aves',
        'name': '鸟纲',
        'name_en': 'Aves',
        'scientific_name': 'Aves',
        'description': '有羽毛、喙、能飞行的温血脊椎动物',
        'level': 5,
        'category': 'biological',
        'parent_id': 'chordata',
        'aliases': ['鸟类', 'birds']
    },

    # 具体物种
    {
        'id': 'felidae',
        'name': '猫科',
        'name_en': 'Felidae',
        'scientific_name': 'Felidae',
        'description': '食肉目猫型总科下的一科',
        'level': 7,
        'category': 'biological',
        'parent_id': 'mammalia',
        'aliases': ['猫科动物', 'cats']
    },
    {
        'id': 'felis_catus',
        'name': '家猫',
        'name_en': 'Domestic Cat',
        'scientific_name': 'Felis catus',
        'description': '被人类驯化的小型猫科动物',
        'level': 9,
        'category': 'biological',
        'parent_id': 'felidae',
        'aliases': ['猫', '小猫', '喵星人', 'cat']
    },
    {
        'id': 'panthera_tigris',
        'name': '虎',
        'name_en': 'Tiger',
        'scientific_name': 'Panthera tigris',
        'description': '大型猫科动物，有黑色条纹',
        'level': 9,
        'category': 'biological',
        'parent_id': 'felidae',
        'aliases': ['老虎', '大虫', 'tiger']
    },

    # 人造物分类
    {
        'id': 'artificial',
        'name': '人造物域',
        'name_en': 'Artificial Domain',
        'description': '人类创造的一切物品和结构',
        'level': 2,
        'category': 'artificial',
        'parent_id': 'existence',
        'aliases': ['人造物', '人工制品']
    },
    {
        'id': 'architecture',
        'name': '建筑',
        'name_en': 'Architecture',
        'description': '人类建造的各种建筑物和构筑物',
        'level': 3,
        'category': 'artificial',
        'parent_id': 'artificial',
        'aliases': ['建筑物', '房屋', 'construction']
    },
    {
        'id': 'residential_building',
        'name': '住宅建筑',
        'name_en': 'Residential Building',
        'description': '供人居住的建筑',
        'level': 4,
        'category': 'artificial',
        'parent_id': 'architecture',
        'aliases': ['住宅', '民居', 'house']
    },

    # 意识界分类
    {
        'id': 'emotions',
        'name': '情绪',
        'name_en': 'Emotions',
        'description': '内在的情感体验和感受',
        'level': 2,
        'category': 'psychological',
        'parent_id': 'consciousness',
        'aliases': ['情感', '感受', 'feelings']
    },
    {
        'id': 'happiness',
        'name': '快乐',
        'name_en': 'Happiness',
        'description': '积极的情绪状态，感到愉悦和满足',
        'level': 3,
        'category': 'psychological',
        'parent_id': 'emotions',
        'aliases': ['开心', '愉快', '欢喜', 'joy']
    },
    {
        'id': 'sadness',
        'name': '悲伤',
        'name_en': 'Sadness',
        'description': '消极的情绪状态，感到失落和难过',
        'level': 3,
        'category': 'psychological',
        'parent_id': 'emotions',
        'aliases': ['伤心', '难过', '忧伤', 'sorrow']
    },

    # 记忆和梦境
    {
        'id': 'memories',
        'name': '记忆',
        'name_en': 'Memories',
        'description': '过往经历的记忆片段',
        'level': 2,
        'category': 'psychological',
        'parent_id': 'consciousness',
        'aliases': ['回忆', '记忆片段']
    },
    {
        'id': 'dreams',
        'name': '梦境',
        'name_en': 'Dreams',
        'description': '睡眠中的幻象和体验',
        'level': 2,
        'category': 'psychological',
        'parent_id': 'consciousness',
        'aliases': ['梦', '梦境体验']
    }
]

# 关系数据
TAG_RELATIONSHIPS = [
    ('existence', 'root'),
    ('consciousness', 'root'),
    ('life', 'existence'),
    ('animalia', 'life'),
    ('plantae', 'life'),
    ('chordata', 'animalia'),
    ('mammalia', 'chordata'),
    ('aves', 'chordata'),
    ('felidae', 'mammalia'),
    ('felis_catus', 'felidae'),
    ('panthera_tigris', 'felidae'),
    ('artificial', 'existence'),
    ('architecture', 'artificial'),
    ('residential_building', 'architecture'),
    ('emotions', 'consciousness'),
    ('happiness', 'emotions'),
    ('sadness', 'emotions'),
    ('memories', 'consciousness'),
    ('dreams', 'consciousness')
]

def init_tags():
    """初始化标签数据"""
    print("🚀 开始初始化标签数据...")

    # 创建Flask应用
    app = create_app('development')

    with app.app_context():
        try:
            # 在应用上下文中创建Neo4j客户端
            neo4j_client = Neo4jClient(
                app.config['NEO4J_URI'],
                app.config['NEO4J_USER'],
                app.config['NEO4J_PASSWORD']
            )

            if not neo4j_client or not neo4j_client.is_connected():
                print("❌ Neo4j服务不可用")
                print("💡 请检查:")
                print("   1. Docker服务是否运行: docker-compose up -d neo4j")
                print("   2. Neo4j端口是否可访问: telnet localhost 7687")
                print("   3. 配置是否正确")
                return False

            print("✅ Neo4j连接成功")

            # 清空现有标签（小心使用）
            print("🗑️ 清空现有标签...")
            with neo4j_client.driver.session() as session:
                session.run("MATCH (t:Tag) DETACH DELETE t")

            # 创建标签
            print("📝 开始创建标签...")
            created_count = 0
            failed_tags = []

            for tag_data in INITIAL_TAGS:
                # 设置默认值
                default_data = {
                    'status': 'active',
                    'quality_score': 8.0,
                    'usage_count': 0,
                    'current_version': 1,
                    'created_by': 'system',
                    'created_at': datetime.utcnow().isoformat(),
                    'last_modified_by': 'system',
                    'last_modified_at': datetime.utcnow().isoformat(),
                    'contributor_count': 1,
                    'edit_count': 0,
                    'aliases': [],
                    'applicable_content_types': ['text', 'image', 'video', 'audio']
                }

                # 合并数据
                full_tag_data = {**default_data, **tag_data}

                # 创建标签
                try:
                    created_tag = neo4j_client.create_tag(full_tag_data)
                    if created_tag:
                        created_count += 1
                        print(f"✅ 创建标签: {tag_data['name']}")
                    else:
                        failed_tags.append(tag_data['name'])
                        print(f"❌ 创建标签失败: {tag_data['name']}")
                except Exception as e:
                    failed_tags.append(tag_data['name'])
                    print(f"❌ 创建标签异常: {tag_data['name']} - {e}")

            print(f"\n📊 标签创建结果: {created_count}/{len(INITIAL_TAGS)} 成功")
            if failed_tags:
                print(f"❌ 失败的标签: {', '.join(failed_tags)}")

            # 建立关系
            print("\n🔗 开始建立标签关系...")
            relationship_count = 0
            failed_relationships = []

            for child_id, parent_id in TAG_RELATIONSHIPS:
                try:
                    success = neo4j_client.create_tag_relationship(child_id, parent_id)
                    if success:
                        relationship_count += 1
                        print(f"✅ 建立关系: {child_id} -> {parent_id}")
                    else:
                        failed_relationships.append(f"{child_id} -> {parent_id}")
                        print(f"❌ 建立关系失败: {child_id} -> {parent_id}")
                except Exception as e:
                    failed_relationships.append(f"{child_id} -> {parent_id}")
                    print(f"❌ 建立关系异常: {child_id} -> {parent_id} - {e}")

            print(f"\n📊 关系建立结果: {relationship_count}/{len(TAG_RELATIONSHIPS)} 成功")
            if failed_relationships:
                print(f"❌ 失败的关系: {', '.join(failed_relationships)}")

            # 验证结果
            print("\n🔍 验证初始化结果...")
            try:
                root_tags = neo4j_client.get_root_tags()
                print(f"   根标签数量: {len(root_tags)}")

                for root in root_tags:
                    children = neo4j_client.get_child_tags(root['id'])
                    print(f"   {root['name']}: {len(children)} 个直接子标签")

                # 统计总标签数
                with neo4j_client.driver.session() as session:
                    result = session.run("MATCH (t:Tag) RETURN count(t) as total")
                    record = result.single()
                    total_tags = record['total'] if record else 0
                    print(f"   总标签数量: {total_tags}")

            except Exception as e:
                print(f"⚠️ 验证过程出错: {e}")

            # 关闭连接
            neo4j_client.close()

            print("\n🎉 标签数据初始化完成！")

            # 成功条件：创建了一半以上的标签
            success_rate = created_count / len(INITIAL_TAGS)
            if success_rate >= 0.5:
                print(f"✅ 初始化成功 (成功率: {success_rate:.1%})")
                return True
            else:
                print(f"⚠️ 初始化部分成功 (成功率: {success_rate:.1%})")
                return False

        except Exception as e:
            print(f"❌ 初始化标签数据失败: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = init_tags()
    if success:
        print("\n🎯 后续操作建议:")
        print("1. 启动应用: python app.py")
        print("2. 测试标签功能: python scripts/test_tags_simple.py")
        print("3. 浏览标签树: curl http://localhost:15000/api/tags/tree")
        print("4. 搜索标签: curl 'http://localhost:15000/api/tags/search?q=猫'")
    else:
        print("\n💡 故障排除:")
        print("1. 检查Neo4j服务: docker-compose ps neo4j")
        print("2. 检查Neo4j日志: docker-compose logs neo4j")
        print("3. 检查连接配置: python scripts/check_neo4j.py")
        sys.exit(1)
