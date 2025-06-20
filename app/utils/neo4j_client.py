# app/utils/neo4j_client.py
from neo4j import GraphDatabase
import logging
from typing import Dict, List, Optional, Any
import json
import atexit
from datetime import datetime

logger = logging.getLogger(__name__)

class Neo4jClient:
    """Neo4j数据库客户端"""

    def __init__(self, uri: str, user: str, password: str):
        """初始化Neo4j连接"""
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # 测试连接
            with self.driver.session() as session:
                session.run("RETURN 1 as test")
            logger.info("Neo4j连接成功")

            # 注册退出时清理函数
            atexit.register(self.close)

        except Exception as e:
            logger.error(f"Neo4j连接失败: {e}")
            if self.driver:
                try:
                    self.driver.close()
                except:
                    pass
                self.driver = None

    def close(self):
        """关闭连接"""
        if self.driver:
            try:
                self.driver.close()
                logger.info("Neo4j连接已关闭")
            except Exception as e:
                logger.error(f"关闭Neo4j连接失败: {e}")
            finally:
                self.driver = None

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def is_connected(self) -> bool:
        """检查连接状态"""
        if not self.driver:
            return False
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            return True
        except Exception as e:
            logger.debug(f"Neo4j连接检查失败: {e}")
            return False

    def get_session(self):
        """获取会话的上下文管理器"""
        if not self.driver:
            raise RuntimeError("Neo4j驱动未初始化")
        return self.driver.session()

    # ==================== 标签基础操作 ====================

    def create_tag(self, tag_data: Dict[str, Any]) -> Optional[Dict]:
        """创建标签"""
        if not self.is_connected():
            return None

        try:
            with self.get_session() as session:
                result = session.run("""
                    CREATE (t:Tag $properties)
                    RETURN t
                """, properties=tag_data)

                record = result.single()
                return dict(record['t']) if record else None

        except Exception as e:
            logger.error(f"创建标签失败: {e}")
            return None

    def get_tag_by_id(self, tag_id: str) -> Optional[Dict]:
        """根据ID获取标签"""
        if not self.is_connected():
            return None

        try:
            with self.get_session() as session:
                result = session.run("""
                    MATCH (t:Tag {id: $tag_id})
                    RETURN t
                """, tag_id=tag_id)

                record = result.single()
                return dict(record['t']) if record else None

        except Exception as e:
            logger.error(f"获取标签失败: {e}")
            return None

    def update_tag(self, tag_id: str, update_data: Dict[str, Any]) -> Optional[Dict]:
        """更新标签"""
        if not self.is_connected():
            return None

        try:
            with self.get_session() as session:
                # 构建SET语句
                set_clauses = []
                for key, value in update_data.items():
                    if key != 'id':  # 不允许更新ID
                        set_clauses.append(f"t.{key} = ${key}")

                if not set_clauses:
                    return self.get_tag_by_id(tag_id)

                set_statement = ", ".join(set_clauses)
                query = f"""
                    MATCH (t:Tag {{id: $tag_id}})
                    SET {set_statement}
                    RETURN t
                """

                params = {'tag_id': tag_id, **update_data}
                result = session.run(query, params)

                record = result.single()
                return dict(record['t']) if record else None

        except Exception as e:
            logger.error(f"更新标签失败: {e}")
            return None

    def delete_tag(self, tag_id: str) -> bool:
        """删除标签（软删除）"""
        if not self.is_connected():
            return False

        try:
            with self.get_session() as session:
                result = session.run("""
                    MATCH (t:Tag {id: $tag_id})
                    SET t.status = 'deleted', t.deleted_at = datetime()
                    RETURN count(t) as deleted_count
                """, tag_id=tag_id)

                record = result.single()
                return record['deleted_count'] > 0 if record else False

        except Exception as e:
            logger.error(f"删除标签失败: {e}")
            return False

    # ==================== 标签层级操作 ====================

    def get_tag_hierarchy(self, tag_id: str) -> List[Dict]:
        """获取标签的层级路径（从根到当前标签）"""
        if not self.is_connected():
            return []

        try:
            with self.get_session() as session:
                result = session.run("""
                    MATCH path = (root:Tag)-[:CONTAINS*0..]->(t:Tag {id: $tag_id})
                    WHERE root.level = 0 OR NOT (root)<-[:CONTAINS]-()
                    WITH path, length(path) as pathLength
                    ORDER BY pathLength ASC
                    LIMIT 1
                    RETURN [node in nodes(path) | {
                        id: node.id,
                        name: node.name,
                        name_en: node.name_en,
                        level: coalesce(node.level, 0),
                        category: node.category
                    }] as hierarchy
                """, tag_id=tag_id)

                record = result.single()
                return record['hierarchy'] if record else []

        except Exception as e:
            logger.error(f"获取标签层级失败: {e}")
            return []

    def get_child_tags(self, parent_id: str, limit: int = 50) -> List[Dict]:
        """获取子标签"""
        if not self.is_connected():
            return []

        try:
            with self.get_session() as session:
                result = session.run("""
                    MATCH (parent:Tag {id: $parent_id})-[:CONTAINS]->(child:Tag)
                    WHERE child.status <> 'deleted'
                    RETURN child
                    ORDER BY child.name
                    LIMIT $limit
                """, parent_id=parent_id, limit=limit)

                return [dict(record['child']) for record in result]

        except Exception as e:
            logger.error(f"获取子标签失败: {e}")
            return []

    def get_parent_tag(self, tag_id: str) -> Optional[Dict]:
        """获取父标签"""
        if not self.is_connected():
            return None

        try:
            with self.get_session() as session:
                result = session.run("""
                    MATCH (child:Tag {id: $tag_id})-[:CONTAINS]->(parent:Tag)
                    WHERE parent.status <> 'deleted'
                    RETURN parent
                    LIMIT 1
                """, tag_id=tag_id)

                record = result.single()
                return dict(record['parent']) if record else None

        except Exception as e:
            logger.error(f"获取父标签失败: {e}")
            return None

    def create_tag_relationship(self, child_id: str, parent_id: str) -> bool:
        """建立标签父子关系"""
        if not self.is_connected():
            return False

        try:
            with self.get_session() as session:
                result = session.run("""
                    MATCH (child:Tag {id: $child_id}), (parent:Tag {id: $parent_id})
                    WHERE child.status <> 'deleted' AND parent.status <> 'deleted'
                    CREATE (parent)-[:CONTAINS {created_at: datetime()}]->(child)
                    RETURN count(*) as created_count
                """, child_id=child_id, parent_id=parent_id)

                record = result.single()
                return record['created_count'] > 0 if record else False

        except Exception as e:
            logger.error(f"建立标签关系失败: {e}")
            return False

    # ==================== 标签搜索操作 ====================

    def search_tags(self, query: str, category: Optional[str] = None,
                    limit: int = 20) -> List[Dict]:
        """搜索标签"""
        if not self.is_connected():
            return []

        try:
            with self.get_session() as session:
                # 构建搜索条件
                where_conditions = ["t.status <> 'deleted'"]
                params = {'query': query, 'limit': limit}

                if category:
                    where_conditions.append("t.category = $category")
                    params['category'] = category

                where_clause = " AND ".join(where_conditions)

                query_cypher = f"""
                    MATCH (t:Tag)
                    WHERE {where_clause}
                    AND (
                        toLower(t.name) CONTAINS toLower($query)
                        OR any(alias IN coalesce(t.aliases, []) WHERE toLower(alias) CONTAINS toLower($query))
                        OR toLower(coalesce(t.description, '')) CONTAINS toLower($query)
                        OR toLower(coalesce(t.name_en, '')) CONTAINS toLower($query)
                    )
                    RETURN t
                    ORDER BY coalesce(t.usage_count, 0) DESC, t.name ASC
                    LIMIT $limit
                """

                result = session.run(query_cypher, params)
                return [dict(record['t']) for record in result]

        except Exception as e:
            logger.error(f"搜索标签失败: {e}")
            return []

    def get_popular_tags(self, category: Optional[str] = None,
                         limit: int = 20) -> List[Dict]:
        """获取热门标签"""
        if not self.is_connected():
            return []

        try:
            with self.get_session() as session:
                where_conditions = ["t.status <> 'deleted'"]
                params = {'limit': limit}

                if category:
                    where_conditions.append("t.category = $category")
                    params['category'] = category

                where_clause = " AND ".join(where_conditions)

                query = f"""
                    MATCH (t:Tag)
                    WHERE {where_clause}
                    RETURN t
                    ORDER BY coalesce(t.usage_count, 0) DESC, coalesce(t.quality_score, 0) DESC
                    LIMIT $limit
                """

                result = session.run(query, params)
                return [dict(record['t']) for record in result]

        except Exception as e:
            logger.error(f"获取热门标签失败: {e}")
            return []

    def get_recommended_tags(self, existing_tags: List[str],
                             limit: int = 10) -> List[Dict]:
        """根据已有标签推荐相关标签"""
        if not self.is_connected() or not existing_tags:
            return []

        try:
            with self.get_session() as session:
                result = session.run("""
                    MATCH (existing:Tag)
                    WHERE existing.id IN $existing_tags
                    AND existing.status <> 'deleted'
                    
                    // 获取相同分类的标签
                    MATCH (recommended:Tag)
                    WHERE recommended.category IN [e IN collect(existing) | e.category]
                    AND NOT recommended.id IN $existing_tags
                    AND recommended.status <> 'deleted'
                    
                    // 计算推荐分数
                    WITH recommended, 
                         coalesce(recommended.usage_count, 0) as usage_score,
                         coalesce(recommended.quality_score, 0) as quality_score
                    
                    RETURN DISTINCT recommended as tag
                    ORDER BY usage_score DESC, quality_score DESC
                    LIMIT $limit
                """, existing_tags=existing_tags, limit=limit)

                return [dict(record['tag']) for record in result]

        except Exception as e:
            logger.error(f"获取推荐标签失败: {e}")
            return []

    # ==================== 标签统计操作 ====================

    def update_tag_usage(self, tag_id: str, increment: int = 1) -> bool:
        """更新标签使用次数"""
        if not self.is_connected():
            return False

        try:
            with self.get_session() as session:
                session.run("""
                    MATCH (t:Tag {id: $tag_id})
                    SET t.usage_count = coalesce(t.usage_count, 0) + $increment,
                        t.last_used_at = datetime()
                """, tag_id=tag_id, increment=increment)

                return True

        except Exception as e:
            logger.error(f"更新标签使用统计失败: {e}")
            return False

    def get_tag_stats(self, tag_id: str) -> Optional[Dict]:
        """获取标签统计信息"""
        if not self.is_connected():
            return None

        try:
            with self.get_session() as session:
                result = session.run("""
                    MATCH (t:Tag {id: $tag_id})
                    OPTIONAL MATCH (t)-[:CONTAINS]->(child:Tag)
                    WHERE child.status <> 'deleted'
                    OPTIONAL MATCH (parent:Tag)-[:CONTAINS]->(t)
                    WHERE parent.status <> 'deleted'
                    
                    RETURN {
                        id: t.id,
                        name: t.name,
                        description: t.description,
                        category: t.category,
                        usage_count: coalesce(t.usage_count, 0),
                        quality_score: coalesce(t.quality_score, 0),
                        child_count: count(DISTINCT child),
                        has_parent: count(DISTINCT parent) > 0,
                        level: coalesce(t.level, 0),
                        status: t.status,
                        created_at: t.created_at,
                        last_used_at: t.last_used_at
                    } as stats
                """, tag_id=tag_id)

                record = result.single()
                return record['stats'] if record else None

        except Exception as e:
            logger.error(f"获取标签统计失败: {e}")
            return None

    # ==================== 标签分类操作 ====================

    def get_root_tags(self) -> List[Dict]:
        """获取根标签"""
        if not self.is_connected():
            return []

        try:
            with self.get_session() as session:
                result = session.run("""
                    MATCH (t:Tag)
                    WHERE (t.level = 0 OR NOT (t)<-[:CONTAINS]-())
                    AND t.status <> 'deleted'
                    RETURN t
                    ORDER BY t.name
                """)

                return [dict(record['t']) for record in result]

        except Exception as e:
            logger.error(f"获取根标签失败: {e}")
            return []

    def get_categories(self) -> List[Dict]:
        """获取所有标签分类"""
        if not self.is_connected():
            return []

        try:
            with self.get_session() as session:
                result = session.run("""
                    MATCH (t:Tag)
                    WHERE t.status <> 'deleted'
                    WITH t.category as category, count(t) as count
                    WHERE category IS NOT NULL
                    RETURN category, count
                    ORDER BY count DESC, category ASC
                """)

                return [
                    {
                        'category': record['category'],
                        'count': record['count']
                    }
                    for record in result
                ]

        except Exception as e:
            logger.error(f"获取分类失败: {e}")
            return []

    # ==================== 批量操作 ====================

    def batch_create_tags(self, tags_data: List[Dict[str, Any]]) -> List[Dict]:
        """批量创建标签"""
        if not self.is_connected():
            return []

        created_tags = []
        try:
            with self.get_session() as session:
                for tag_data in tags_data:
                    try:
                        result = session.run("""
                            CREATE (t:Tag $properties)
                            RETURN t
                        """, properties=tag_data)

                        record = result.single()
                        if record:
                            created_tags.append(dict(record['t']))
                    except Exception as e:
                        logger.error(f"创建标签失败 {tag_data.get('name', 'unknown')}: {e}")
                        continue

                return created_tags

        except Exception as e:
            logger.error(f"批量创建标签失败: {e}")
            return created_tags

    def validate_tags(self, tag_ids: List[str]) -> List[str]:
        """验证标签ID列表，返回有效的标签ID"""
        if not self.is_connected() or not tag_ids:
            return []

        try:
            with self.get_session() as session:
                result = session.run("""
                    MATCH (t:Tag)
                    WHERE t.id IN $tag_ids
                    AND t.status <> 'deleted'
                    RETURN collect(t.id) as valid_ids
                """, tag_ids=tag_ids)

                record = result.single()
                return record['valid_ids'] if record else []

        except Exception as e:
            logger.error(f"验证标签失败: {e}")
            return []

    # ==================== 数据维护操作 ====================

    def initialize_sample_data(self):
        """初始化示例数据"""
        if not self.is_connected():
            return False

        sample_tags = [
            {
                'id': 'life',
                'name': '生物',
                'name_en': 'Life',
                'description': '所有生物的根分类',
                'category': 'biology',
                'level': 0,
                'status': 'active',
                'usage_count': 0,
                'quality_score': 10.0,
                'created_at': datetime.utcnow().isoformat(),
                'current_version': 1
            },
            {
                'id': 'animal',
                'name': '动物',
                'name_en': 'Animal',
                'description': '动物界',
                'category': 'biology',
                'level': 1,
                'status': 'active',
                'usage_count': 0,
                'quality_score': 9.0,
                'created_at': datetime.utcnow().isoformat(),
                'current_version': 1
            },
            {
                'id': 'felis_catus',
                'name': '猫',
                'name_en': 'Cat',
                'description': '家猫，学名 Felis catus',
                'category': 'biology',
                'level': 2,
                'status': 'active',
                'usage_count': 50,
                'quality_score': 9.5,
                'aliases': ['家猫', 'cat', '喵星人'],
                'created_at': datetime.utcnow().isoformat(),
                'current_version': 1
            },
            {
                'id': 'happiness',
                'name': '快乐',
                'name_en': 'Happiness',
                'description': '积极的情感状态',
                'category': 'emotion',
                'level': 0,
                'status': 'active',
                'usage_count': 30,
                'quality_score': 8.0,
                'aliases': ['开心', '愉快', 'happy'],
                'created_at': datetime.utcnow().isoformat(),
                'current_version': 1
            }
        ]

        try:
            with self.get_session() as session:
                # 创建标签
                for tag_data in sample_tags:
                    session.run("""
                        MERGE (t:Tag {id: $id})
                        SET t += $properties
                    """, id=tag_data['id'], properties=tag_data)

                # 创建关系
                relationships = [
                    ('life', 'animal'),
                    ('animal', 'felis_catus')
                ]

                for parent_id, child_id in relationships:
                    session.run("""
                        MATCH (parent:Tag {id: $parent_id})
                        MATCH (child:Tag {id: $child_id})
                        MERGE (parent)-[:CONTAINS]->(child)
                    """, parent_id=parent_id, child_id=child_id)

                logger.info("Neo4j示例数据初始化完成")
                return True

        except Exception as e:
            logger.error(f"初始化示例数据失败: {e}")
            return False

    def cleanup_test_data(self):
        """清理测试数据"""
        if not self.is_connected():
            return

        try:
            with self.get_session() as session:
                # 删除测试标签
                session.run("""
                    MATCH (t:Tag)
                    WHERE t.name CONTAINS '测试' 
                    OR t.category = 'test'
                    OR t.id STARTS WITH 'test_'
                    DETACH DELETE t
                """)
                logger.info("测试数据清理完成")

        except Exception as e:
            logger.error(f"清理测试数据失败: {e}")

    def get_database_stats(self) -> Dict[str, int]:
        """获取数据库统计信息"""
        if not self.is_connected():
            return {}

        try:
            with self.get_session() as session:
                result = session.run("""
                    MATCH (t:Tag)
                    OPTIONAL MATCH (t)-[r:CONTAINS]-()
                    RETURN {
                        total_tags: count(DISTINCT t),
                        active_tags: count(DISTINCT CASE WHEN t.status <> 'deleted' THEN t END),
                        total_relationships: count(DISTINCT r),
                        categories: count(DISTINCT t.category)
                    } as stats
                """)

                record = result.single()
                return record['stats'] if record else {}

        except Exception as e:
            logger.error(f"获取数据库统计失败: {e}")
            return {}
