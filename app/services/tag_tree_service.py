from datetime import datetime
from sqlalchemy import and_, or_, func, text
from sqlalchemy.exc import IntegrityError
from flask import request
import logging
import json
from typing import List, Dict, Optional, Tuple, Any

from app import db
from app.models.tag import Tag, TagHistory, TagRelation
from app.models.user import User
from app.utils.ai_mapping import AITagMapper

logger = logging.getLogger(__name__)

class TagTreeService:
    """标签树服务 - 管理层级化的标签系统"""
    
    @classmethod
    def create_tag(cls, name: str, user_id: str, parent_id: Optional[str] = None, 
                   description: str = '', name_en: str = '', category: str = 'general',
                   domain: str = 'general', is_abstract: bool = False, 
                   aliases: List[str] = None, properties: Dict = None) -> Tuple[bool, str, Optional[Tag]]:
        """
        创建新标签
        
        Args:
            name: 标签名称
            user_id: 创建者ID
            parent_id: 父标签ID
            description: 描述
            name_en: 英文名
            category: 分类
            domain: 域
            is_abstract: 是否为抽象概念
            aliases: 别名列表
            properties: 自定义属性
            
        Returns:
            tuple: (success, message, tag)
        """
        try:
            # 验证标签名称
            if not name or len(name.strip()) == 0:
                return False, "标签名称不能为空", None
                
            name = name.strip()
            
            # 检查名称是否已存在
            existing_tag = Tag.query.filter_by(name=name, status='active').first()
            if existing_tag:
                return False, f"标签 '{name}' 已存在", None
            
            # 验证父标签
            parent_tag = None
            level = 0
            if parent_id:
                parent_tag = Tag.query.filter_by(id=parent_id, status='active').first()
                if not parent_tag:
                    return False, "父标签不存在", None
                level = parent_tag.level + 1
            
            # 创建标签
            tag = Tag(
                name=name,
                name_en=name_en,
                description=description,
                parent_id=parent_id,
                level=level,
                category=category,
                domain=domain,
                is_abstract=is_abstract,
                aliases=aliases or [],
                properties=properties or {},
                created_by=user_id,
                status='active'
            )
            
            db.session.add(tag)
            db.session.flush()  # 获取ID
            
            # 更新路径
            tag.update_path()
            
            # 记录历史
            cls._record_history(tag.id, 'create', user_id, {
                'name': name,
                'parent_id': parent_id,
                'description': description
            })
            
            db.session.commit()
            logger.info(f"创建标签成功: {name} (ID: {tag.id})")
            return True, "标签创建成功", tag
            
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"创建标签失败 - 数据完整性错误: {e}")
            return False, "标签创建失败，可能存在重复数据", None
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建标签失败: {e}")
            return False, f"创建标签失败: {str(e)}", None
    
    @classmethod
    def get_tag_tree(cls, root_id: Optional[str] = None, max_depth: int = 3, 
                     include_stats: bool = False) -> List[Dict]:
        """
        获取标签树
        
        Args:
            root_id: 根标签ID，None表示所有根标签
            max_depth: 最大深度
            include_stats: 是否包含统计信息
            
        Returns:
            标签树列表
        """
        try:
            # 查询根标签
            if root_id:
                root_tags = Tag.query.filter_by(id=root_id, status='active').all()
            else:
                root_tags = Tag.query.filter_by(parent_id=None, status='active').order_by(Tag.name).all()
            
            result = []
            for tag in root_tags:
                tree_data = cls._build_tag_tree(tag, max_depth, include_stats)
                result.append(tree_data)
            
            return result
            
        except Exception as e:
            logger.error(f"获取标签树失败: {e}")
            return []
    
    @classmethod
    def _build_tag_tree(cls, tag: Tag, max_depth: int, include_stats: bool = False) -> Dict:
        """递归构建标签树"""
        tree_data = tag.to_dict()
        
        if include_stats:
            tree_data['stats'] = cls._get_tag_stats(tag)
        
        # 递归获取子标签
        if max_depth > 0:
            children = Tag.query.filter_by(
                parent_id=tag.id, 
                status='active'
            ).order_by(Tag.name).all()
            
            tree_data['children'] = []
            for child in children:
                child_tree = cls._build_tag_tree(child, max_depth - 1, include_stats)
                tree_data['children'].append(child_tree)
        
        return tree_data
    
    @classmethod
    def _get_tag_stats(cls, tag: Tag) -> Dict:
        """获取标签统计信息"""
        # 子标签数量
        children_count = Tag.query.filter_by(parent_id=tag.id, status='active').count()
        
        # 使用次数（从EntryTag表中统计）
        from app.models.entry import EntryTag
        usage_count = EntryTag.query.filter_by(tag_id=tag.id).count()
        
        # 更新使用次数
        if tag.usage_count != usage_count:
            tag.usage_count = usage_count
            tag.increment_usage()
        
        return {
            'children_count': children_count,
            'usage_count': usage_count,
            'total_descendants': len(tag.get_descendants())
        }
    
    @classmethod
    def search_tags(cls, keyword: str, category: Optional[str] = None, 
                    domain: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        搜索标签
        
        Args:
            keyword: 搜索关键词
            category: 分类筛选
            domain: 域筛选
            limit: 结果限制
            
        Returns:
            标签列表
        """
        try:
            query = Tag.query.filter(Tag.status == 'active')
            
            # 关键词搜索
            if keyword:
                keyword = f"%{keyword}%"
                query = query.filter(
                    or_(
                        Tag.name.ilike(keyword),
                        Tag.name_en.ilike(keyword),
                        Tag.description.ilike(keyword),
                        Tag.aliases.contains([keyword.strip('%')])
                    )
                )
            
            # 分类筛选
            if category:
                query = query.filter(Tag.category == category)
            
            # 域筛选
            if domain:
                query = query.filter(Tag.domain == domain)
            
            # 按使用次数和质量评分排序
            query = query.order_by(
                Tag.usage_count.desc(),
                Tag.quality_score.desc(),
                Tag.name
            )
            
            tags = query.limit(limit).all()
            return [tag.to_dict() for tag in tags]
            
        except Exception as e:
            logger.error(f"搜索标签失败: {e}")
            return []
    
    @classmethod
    def get_tag_suggestions(cls, partial_name: str, limit: int = 10) -> List[Dict]:
        """获取标签建议"""
        try:
            query = Tag.query.filter(
                and_(
                    Tag.status == 'active',
                    Tag.name.ilike(f"{partial_name}%")
                )
            ).order_by(
                Tag.usage_count.desc(),
                Tag.quality_score.desc()
            ).limit(limit)
            
            tags = query.all()
            return [{'id': tag.id, 'name': tag.name, 'path': tag.get_full_path()} for tag in tags]
            
        except Exception as e:
            logger.error(f"获取标签建议失败: {e}")
            return []
    
    @classmethod
    def move_tag(cls, tag_id: str, new_parent_id: Optional[str], user_id: str) -> Tuple[bool, str]:
        """
        移动标签到新的父标签下
        
        Args:
            tag_id: 要移动的标签ID
            new_parent_id: 新父标签ID
            user_id: 操作者ID
            
        Returns:
            tuple: (success, message)
        """
        try:
            # 获取标签
            tag = Tag.query.filter_by(id=tag_id, status='active').first()
            if not tag:
                return False, "标签不存在"
            
            # 验证新父标签
            new_parent = None
            if new_parent_id:
                new_parent = Tag.query.filter_by(id=new_parent_id, status='active').first()
                if not new_parent:
                    return False, "新父标签不存在"
                
                # 检查是否会创建循环
                if not new_parent.can_be_parent_of(tag):
                    return False, "无法移动到此位置，会创建循环引用"
            
            # 记录原始数据
            old_data = {
                'parent_id': tag.parent_id,
                'level': tag.level,
                'path': tag.path
            }
            
            # 更新标签
            tag.parent_id = new_parent_id
            tag.level = new_parent.level + 1 if new_parent else 0
            tag.update_path()
            
            # 记录历史
            cls._record_history(tag_id, 'move', user_id, old_data, {
                'parent_id': new_parent_id,
                'level': tag.level,
                'path': tag.path
            })
            
            db.session.commit()
            logger.info(f"移动标签成功: {tag.name} -> {new_parent.name if new_parent else 'root'}")
            return True, "标签移动成功"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"移动标签失败: {e}")
            return False, f"移动标签失败: {str(e)}"
    
    @classmethod
    def merge_tags(cls, source_tag_id: str, target_tag_id: str, user_id: str) -> Tuple[bool, str]:
        """
        合并标签
        
        Args:
            source_tag_id: 源标签ID（将被合并的标签）
            target_tag_id: 目标标签ID（保留的标签）
            user_id: 操作者ID
            
        Returns:
            tuple: (success, message)
        """
        try:
            # 获取标签
            source_tag = Tag.query.filter_by(id=source_tag_id, status='active').first()
            target_tag = Tag.query.filter_by(id=target_tag_id, status='active').first()
            
            if not source_tag or not target_tag:
                return False, "标签不存在"
            
            if source_tag.id == target_tag.id:
                return False, "不能合并相同的标签"
            
            # 更新使用该标签的条目
            from app.models.entry import EntryTag
            EntryTag.query.filter_by(tag_id=source_tag_id).update({'tag_id': target_tag_id})
            
            # 合并使用统计
            target_tag.usage_count += source_tag.usage_count
            target_tag.increment_usage()
            
            # 合并别名
            if source_tag.aliases:
                target_aliases = set(target_tag.aliases or [])
                source_aliases = set(source_tag.aliases or [])
                target_tag.aliases = list(target_aliases.union(source_aliases))
            
            # 标记源标签为已合并
            source_tag.status = 'merged'
            source_tag.properties = source_tag.properties or {}
            source_tag.properties['merged_to'] = target_tag_id
            
            # 记录历史
            cls._record_history(source_tag_id, 'merge', user_id, 
                               source_tag.to_dict(), 
                               {'merged_to': target_tag_id})
            
            db.session.commit()
            logger.info(f"合并标签成功: {source_tag.name} -> {target_tag.name}")
            return True, f"标签已合并到 '{target_tag.name}'"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"合并标签失败: {e}")
            return False, f"合并标签失败: {str(e)}"
    
    @classmethod
    def auto_place_tag(cls, tag_name: str, description: str = '', 
                       ai_context: Dict = None) -> Optional[str]:
        """
        自动将标签放置到合适的位置
        
        Args:
            tag_name: 标签名称
            description: 描述
            ai_context: AI识别上下文
            
        Returns:
            建议的父标签ID
        """
        try:
            # 使用AI映射器找到合适的父标签
            mapper = AITagMapper()
            suggested_parent = mapper.find_best_parent(tag_name, description, ai_context)
            
            if suggested_parent:
                return suggested_parent.id
            
            # 如果AI映射失败，使用基于关键词的匹配
            return cls._find_parent_by_keywords(tag_name, description)
            
        except Exception as e:
            logger.error(f"自动放置标签失败: {e}")
            return None
    
    @classmethod
    def _find_parent_by_keywords(cls, tag_name: str, description: str) -> Optional[str]:
        """基于关键词查找父标签"""
        # 生物相关关键词
        biological_keywords = ['动物', '植物', '生物', '昆虫', '鸟类', '哺乳动物', '鱼类']
        # 物理相关关键词
        physical_keywords = ['材料', '金属', '石头', '矿物', '化学']
        # 人工制品关键词
        artificial_keywords = ['工具', '机器', '建筑', '车辆', '设备']
        
        text = f"{tag_name} {description}".lower()
        
        # 查找相应的父标签
        if any(keyword in text for keyword in biological_keywords):
            parent = Tag.query.filter_by(name='生命域', status='active').first()
            if parent:
                return parent.id
        
        if any(keyword in text for keyword in physical_keywords):
            parent = Tag.query.filter_by(name='物质域', status='active').first()
            if parent:
                return parent.id
        
        if any(keyword in text for keyword in artificial_keywords):
            parent = Tag.query.filter_by(name='人工制品', status='active').first()
            if parent:
                return parent.id
        
        return None
    
    @classmethod
    def get_tag_by_id(cls, tag_id: str) -> Optional[Tag]:
        """根据ID获取标签"""
        return Tag.query.filter_by(id=tag_id, status='active').first()
    
    @classmethod
    def get_tag_by_name(cls, name: str) -> Optional[Tag]:
        """根据名称获取标签"""
        return Tag.query.filter_by(name=name, status='active').first()
    
    @classmethod
    def get_tag_history(cls, tag_id: str, limit: int = 50) -> List[Dict]:
        """获取标签历史记录"""
        try:
            history = TagHistory.query.filter_by(tag_id=tag_id)\
                .order_by(TagHistory.created_at.desc())\
                .limit(limit).all()
            
            return [h.to_dict() for h in history]
            
        except Exception as e:
            logger.error(f"获取标签历史失败: {e}")
            return []
    
    @classmethod
    def _record_history(cls, tag_id: str, action: str, user_id: str, 
                        old_data: Dict = None, new_data: Dict = None):
        """记录标签历史"""
        try:
            # 计算差异
            diff = {}
            if old_data and new_data:
                for key in set(old_data.keys()) | set(new_data.keys()):
                    old_val = old_data.get(key)
                    new_val = new_data.get(key)
                    if old_val != new_val:
                        diff[key] = {'old': old_val, 'new': new_val}
            
            # 创建历史记录
            history = TagHistory(
                tag_id=tag_id,
                action=action,
                old_data=old_data,
                new_data=new_data,
                diff=diff,
                user_id=user_id,
                user_agent=request.headers.get('User-Agent', '') if request else '',
                ip_address=request.remote_addr if request else ''
            )
            
            db.session.add(history)
            
        except Exception as e:
            logger.error(f"记录标签历史失败: {e}")
    
    @classmethod
    def get_popular_tags(cls, limit: int = 20) -> List[Dict]:
        """获取热门标签"""
        try:
            tags = Tag.query.filter_by(status='active')\
                .order_by(Tag.usage_count.desc(), Tag.popularity_score.desc())\
                .limit(limit).all()
            
            return [tag.to_dict() for tag in tags]
            
        except Exception as e:
            logger.error(f"获取热门标签失败: {e}")
            return []
    
    @classmethod
    def get_categories(cls) -> List[Dict]:
        """获取所有分类"""
        try:
            categories = db.session.query(
                Tag.category,
                func.count(Tag.id).label('count')
            ).filter_by(status='active')\
             .group_by(Tag.category)\
             .order_by(func.count(Tag.id).desc()).all()
            
            return [{'category': cat[0], 'count': cat[1]} for cat in categories]
            
        except Exception as e:
            logger.error(f"获取分类失败: {e}")
            return [] 