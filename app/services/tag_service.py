from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from app import neo4j_client
from app.models.entry import EntryTag
from app.models.user import User
from app import db

logger = logging.getLogger(__name__)

class TagService:
    """标签服务类"""

    @classmethod
    def create_tag(cls, user_id: str, name: str, description: str = None,
                   category: str = None, parent_id: str = None,
                   name_en: str = None, aliases: List[str] = None) -> tuple:
        """
        创建标签

        Args:
            user_id: 创建者ID
            name: 标签名称
            description: 标签描述
            category: 标签分类
            parent_id: 父标签ID
            name_en: 英文名称
            aliases: 别名列表

        Returns:
            tuple: (success: bool, message: str, tag: dict|None)
        """
        try:
            if not neo4j_client or not neo4j_client.is_connected():
                return False, "标签服务不可用", None

            # 验证用户权限
            user = User.query.get(user_id)
            if not user:
                return False, "用户不存在", None

            if not user.permissions or not user.permissions.can_create_tags:
                return False, "没有创建标签的权限", None

            # 验证输入
            if not name or len(name.strip()) == 0:
                return False, "标签名称不能为空", None

            if len(name) > 100:
                return False, "标签名称长度不能超过100字符", None

            # 检查标签是否已存在
            existing_tag = neo4j_client.search_tags(name.strip(), limit=1)
            for tag in existing_tag:
                if tag['name'] == name.strip():
                    return False, "标签已存在", None

            # 验证父标签
            parent_level = 0
            if parent_id:
                parent_tag = neo4j_client.get_tag_by_id(parent_id)
                if not parent_tag:
                    return False, "父标签不存在", None
                parent_level = parent_tag.get('level', 0)

            # 生成标签ID
            import uuid
            tag_id = str(uuid.uuid4())

            # 构建标签数据
            tag_data = {
                'id': tag_id,
                'name': name.strip(),
                'description': description or '',
                'category': category or 'user_defined',
                'level': parent_level + 1,
                'status': 'active',
                'quality_score': 5.0,
                'usage_count': 0,
                'current_version': 1,
                'created_by': user_id,
                'created_at': datetime.utcnow().isoformat(),
                'last_modified_by': user_id,
                'last_modified_at': datetime.utcnow().isoformat(),
                'contributor_count': 1,
                'edit_count': 0,
                'aliases': aliases or [],
                'applicable_content_types': ['text', 'image', 'video', 'audio']
            }

            if name_en:
                tag_data['name_en'] = name_en

            # 创建标签
            created_tag = neo4j_client.create_tag(tag_data)
            if not created_tag:
                return False, "创建标签失败", None

            # 建立父子关系
            if parent_id:
                if not neo4j_client.create_tag_relationship(tag_id, parent_id):
                    logger.warning(f"建立标签关系失败: {tag_id} -> {parent_id}")

            logger.info(f"标签创建成功: {name} by {user.username}")
            return True, "标签创建成功", created_tag

        except Exception as e:
            logger.error(f"创建标签失败: {e}")
            return False, "创建标签失败", None

    @classmethod
    def get_tag_by_id(cls, tag_id: str) -> tuple:
        """获取标签详情"""
        try:
            if not neo4j_client or not neo4j_client.is_connected():
                return False, "标签服务不可用", None

            tag = neo4j_client.get_tag_by_id(tag_id)
            if not tag:
                return False, "标签不存在", None

            if tag.get('status') == 'deleted':
                return False, "标签已被删除", None

            # 获取统计信息
            tag_stats = neo4j_client.get_tag_stats(tag_id)
            if tag_stats:
                tag.update(tag_stats)

            # 获取层级信息
            hierarchy = neo4j_client.get_tag_hierarchy(tag_id)
            tag['hierarchy'] = hierarchy

            return True, "获取成功", tag

        except Exception as e:
            logger.error(f"获取标签失败: {e}")
            return False, "获取标签失败", None

    @classmethod
    def search_tags(cls, query: str, category: str = None,
                    page: int = 1, per_page: int = 20) -> tuple:
        """搜索标签"""
        try:
            if not neo4j_client or not neo4j_client.is_connected():
                return False, "标签服务不可用", None

            if not query or len(query.strip()) == 0:
                return False, "搜索关键词不能为空", None

            # 计算偏移量
            limit = min(per_page, 100)  # 限制最大100条

            # 搜索标签
            tags = neo4j_client.search_tags(query.strip(), category, limit)

            # 简单分页处理（Neo4j的分页比较复杂，这里简化处理）
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_tags = tags[start_idx:end_idx]

            result = {
                'tags': paginated_tags,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': len(tags),  # 实际实现中需要单独查询总数
                    'has_prev': page > 1,
                    'has_next': end_idx < len(tags)
                },
                'query': query,
                'category': category
            }

            return True, "搜索成功", result

        except Exception as e:
            logger.error(f"搜索标签失败: {e}")
            return False, "搜索失败", None

    @classmethod
    def get_popular_tags(cls, category: str = None, limit: int = 20) -> tuple:
        """获取热门标签"""
        try:
            if not neo4j_client or not neo4j_client.is_connected():
                return False, "标签服务不可用", None

            tags = neo4j_client.get_popular_tags(category, limit)

            result = {
                'tags': tags,
                'category': category,
                'count': len(tags)
            }

            return True, "获取成功", result

        except Exception as e:
            logger.error(f"获取热门标签失败: {e}")
            return False, "获取失败", None

    @classmethod
    def get_recommended_tags(cls, entry_tags: List[str], limit: int = 10) -> tuple:
        """获取推荐标签"""
        try:
            if not neo4j_client or not neo4j_client.is_connected():
                return False, "标签服务不可用", None

            if not entry_tags:
                # 如果没有现有标签，返回热门标签
                return cls.get_popular_tags(limit=limit)

            tags = neo4j_client.get_recommended_tags(entry_tags, limit)

            result = {
                'recommended_tags': tags,
                'based_on': entry_tags,
                'count': len(tags)
            }

            return True, "获取成功", result

        except Exception as e:
            logger.error(f"获取推荐标签失败: {e}")
            return False, "获取失败", None

    @classmethod
    def get_tag_tree(cls, root_id: str = None) -> tuple:
        """获取标签树"""
        try:
            if not neo4j_client or not neo4j_client.is_connected():
                return False, "标签服务不可用", None

            if root_id:
                # 获取指定根节点的子树
                root_tag = neo4j_client.get_tag_by_id(root_id)
                if not root_tag:
                    return False, "根标签不存在", None

                children = neo4j_client.get_child_tags(root_id)

                result = {
                    'root': root_tag,
                    'children': children
                }
            else:
                # 获取所有根标签
                root_tags = neo4j_client.get_root_tags()
                result = {
                    'roots': root_tags
                }

            return True, "获取成功", result

        except Exception as e:
            logger.error(f"获取标签树失败: {e}")
            return False, "获取失败", None

    @classmethod
    def update_tag(cls, tag_id: str, user_id: str, **update_data) -> tuple:
        """更新标签"""
        try:
            if not neo4j_client or not neo4j_client.is_connected():
                return False, "标签服务不可用", None

            # 验证用户权限
            user = User.query.get(user_id)
            if not user:
                return False, "用户不存在", None

            if not user.permissions or not user.permissions.can_edit_tags:
                return False, "没有编辑标签的权限", None

            # 获取现有标签
            existing_tag = neo4j_client.get_tag_by_id(tag_id)
            if not existing_tag:
                return False, "标签不存在", None

            if existing_tag.get('status') == 'deleted':
                return False, "标签已被删除", None

            # 过滤允许更新的字段
            allowed_fields = ['name', 'description', 'name_en', 'aliases', 'category']
            filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}

            if not filtered_data:
                return False, "没有有效的更新字段", None

            # 添加更新元数据
            filtered_data.update({
                'last_modified_by': user_id,
                'last_modified_at': datetime.utcnow().isoformat(),
                'edit_count': existing_tag.get('edit_count', 0) + 1
            })

            # 更新标签
            updated_tag = neo4j_client.update_tag(tag_id, filtered_data)
            if not updated_tag:
                return False, "更新标签失败", None

            logger.info(f"标签更新成功: {tag_id} by {user.username}")
            return True, "更新成功", updated_tag

        except Exception as e:
            logger.error(f"更新标签失败: {e}")
            return False, "更新失败", None

    @classmethod
    def delete_tag(cls, tag_id: str, user_id: str) -> tuple:
        """删除标签"""
        try:
            if not neo4j_client or not neo4j_client.is_connected():
                return False, "标签服务不可用", None

            # 验证用户权限（需要管理员权限或标签创建者）
            user = User.query.get(user_id)
            if not user:
                return False, "用户不存在", None

            tag = neo4j_client.get_tag_by_id(tag_id)
            if not tag:
                return False, "标签不存在", None

            # 检查权限
            is_creator = tag.get('created_by') == user_id
            is_admin = user.permissions and user.permissions.can_approve_changes

            if not (is_creator or is_admin):
                return False, "没有删除权限", None

            # 检查是否有子标签
            children = neo4j_client.get_child_tags(tag_id, limit=1)
            if children:
                return False, "标签下还有子标签，不能删除", None

            # 检查是否被使用
            usage_count = EntryTag.query.filter_by(tag_id=tag_id).count()
            if usage_count > 0:
                return False, f"标签正在被{usage_count}个图鉴条目使用，不能删除", None

            # 软删除标签
            success = neo4j_client.delete_tag(tag_id)
            if not success:
                return False, "删除标签失败", None

            logger.info(f"标签删除成功: {tag_id} by {user.username}")
            return True, "删除成功", None

        except Exception as e:
            logger.error(f"删除标签失败: {e}")
            return False, "删除失败", None

    # app/services/tag_service.py - 修改 validate_tags 方法
    @classmethod
    def validate_tags(cls, tag_ids: List[str]) -> tuple:
        """验证标签ID列表"""
        try:
            if not neo4j_client or not neo4j_client.is_connected():
                logger.warning("Neo4j服务不可用，跳过标签验证")
                return True, "标签服务不可用，跳过验证", tag_ids

            if not tag_ids:
                return True, "标签列表为空", []

            # 确保tag_ids是字符串列表
            if not isinstance(tag_ids, list):
                return False, "标签列表格式错误", []

            # 过滤空字符串和None
            clean_tag_ids = [str(tag_id).strip() for tag_id in tag_ids if tag_id and str(tag_id).strip()]

            if not clean_tag_ids:
                return True, "没有有效的标签ID", []

            valid_tags = []
            invalid_tags = []

            for tag_id in clean_tag_ids:
                try:
                    tag = neo4j_client.get_tag_by_id(tag_id)
                    if tag and tag.get('status') != 'deleted':
                        valid_tags.append(tag_id)
                        # 更新使用统计
                        neo4j_client.update_tag_usage(tag_id)
                    else:
                        invalid_tags.append(tag_id)
                except Exception as e:
                    logger.error(f"验证标签 {tag_id} 时出错: {e}")
                    invalid_tags.append(tag_id)

            if invalid_tags:
                logger.warning(f"发现无效标签: {invalid_tags}")
                return False, f"无效的标签: {', '.join(invalid_tags)}", valid_tags

            return True, "标签验证通过", valid_tags

        except Exception as e:
            logger.error(f"验证标签失败: {e}")
            # 异常时返回原始列表，允许系统继续运行
            return True, f"标签验证异常，跳过验证: {str(e)}", tag_ids
