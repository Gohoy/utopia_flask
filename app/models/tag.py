from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Index, text
import uuid

from app import db

class Tag(db.Model):
    """标签模型 - 支持层级结构的万物图鉴标签系统"""
    __tablename__ = 'tags'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 基础信息
    name = db.Column(db.String(100), nullable=False, index=True)
    name_en = db.Column(db.String(100), index=True)  # 英文名
    description = db.Column(db.Text)
    description_en = db.Column(db.Text)  # 英文描述
    
    # 层级关系
    parent_id = db.Column(db.String(36), db.ForeignKey('tags.id'), nullable=True)
    level = db.Column(db.Integer, default=0)  # 层级深度，0为根节点
    path = db.Column(db.String(1000))  # 层级路径，如 "root/existence/life/animal"
    
    # 分类信息
    category = db.Column(db.String(50), default='general')  # 分类：biological, philosophical, physical, etc.
    domain = db.Column(db.String(50), default='general')  # 域：science, art, culture, etc.
    
    # 标签属性
    is_abstract = db.Column(db.Boolean, default=False)  # 是否为抽象概念
    is_system = db.Column(db.Boolean, default=False)  # 是否为系统标签
    status = db.Column(db.String(20), default='active')  # active, deprecated, merged
    
    # 质量和使用统计
    quality_score = db.Column(db.Numeric(3, 2), default=5.0)  # 质量评分 0-10
    usage_count = db.Column(db.Integer, default=0)  # 使用次数
    popularity_score = db.Column(db.Numeric(5, 2), default=0.0)  # 热度评分
    
    # 元数据
    aliases = db.Column(JSONB, default=list)  # 别名列表
    related_tags = db.Column(JSONB, default=list)  # 相关标签ID列表
    external_links = db.Column(JSONB, default=dict)  # 外部链接 {'wikipedia': 'url', 'baidu': 'url'}
    properties = db.Column(JSONB, default=dict)  # 自定义属性
    
    # 内容类型适用性
    applicable_content_types = db.Column(JSONB, default=lambda: ['text', 'image', 'video', 'audio'])
    
    # 审核和权限
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    approved_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系定义
    parent = db.relationship('Tag', remote_side=[id], backref='children')
    creator = db.relationship('User', foreign_keys=[created_by])
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    # 索引
    __table_args__ = (
        Index('idx_tags_name', 'name'),
        Index('idx_tags_path', 'path'),
        Index('idx_tags_level', 'level'),
        Index('idx_tags_category', 'category'),
        Index('idx_tags_parent_id', 'parent_id'),
        Index('idx_tags_status', 'status'),
        Index('idx_tags_usage_count', 'usage_count'),
    )
    
    def get_full_path(self):
        """获取完整路径"""
        if self.path:
            return self.path
        
        # 动态构建路径
        path_parts = []
        current = self
        while current:
            path_parts.append(current.name)
            current = current.parent
        
        return '/'.join(reversed(path_parts))
    
    def get_ancestors(self):
        """获取所有祖先标签"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors
    
    def get_descendants(self, max_depth=None):
        """获取所有后代标签"""
        descendants = []
        
        def _collect_descendants(tag, current_depth=0):
            if max_depth and current_depth >= max_depth:
                return
            
            for child in tag.children:
                descendants.append(child)
                _collect_descendants(child, current_depth + 1)
        
        _collect_descendants(self)
        return descendants
    
    def get_siblings(self):
        """获取同级标签"""
        if not self.parent_id:
            return Tag.query.filter_by(parent_id=None, status='active').filter(Tag.id != self.id).all()
        return Tag.query.filter_by(parent_id=self.parent_id, status='active').filter(Tag.id != self.id).all()
    
    def can_be_parent_of(self, other_tag):
        """检查是否可以成为另一个标签的父标签"""
        # 不能成为自己的父标签
        if self.id == other_tag.id:
            return False
        
        # 不能成为自己祖先的父标签（避免循环）
        ancestors = self.get_ancestors()
        if other_tag in ancestors:
            return False
        
        return True
    
    def update_path(self):
        """更新路径"""
        if not self.parent:
            self.path = self.name
        else:
            self.path = f"{self.parent.path}/{self.name}"
        
        # 递归更新所有子标签的路径
        for child in self.children:
            child.update_path()
    
    def increment_usage(self):
        """增加使用次数"""
        self.usage_count += 1
        # 更新热度评分（可以根据时间衰减等因素调整）
        self.popularity_score = float(self.usage_count) * 0.1
    
    def to_dict(self, include_children=False, include_parent=False, max_depth=2):
        """转换为字典"""
        data = {
            'id': self.id,
            'name': self.name,
            'name_en': self.name_en,
            'description': self.description,
            'description_en': self.description_en,
            'parent_id': self.parent_id,
            'level': self.level,
            'path': self.get_full_path(),
            'category': self.category,
            'domain': self.domain,
            'is_abstract': self.is_abstract,
            'is_system': self.is_system,
            'status': self.status,
            'quality_score': float(self.quality_score),
            'usage_count': self.usage_count,
            'popularity_score': float(self.popularity_score),
            'aliases': self.aliases,
            'related_tags': self.related_tags,
            'external_links': self.external_links,
            'properties': self.properties,
            'applicable_content_types': self.applicable_content_types,
            'created_by': self.created_by,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        
        if include_parent and self.parent:
            data['parent'] = self.parent.to_dict(include_children=False, include_parent=False)
        
        if include_children and max_depth > 0:
            data['children'] = [
                child.to_dict(include_children=True, max_depth=max_depth-1)
                for child in self.children
                if child.status == 'active'
            ]
        
        return data
    
    def __repr__(self):
        return f'<Tag {self.name}>'

class TagHistory(db.Model):
    """标签历史记录"""
    __tablename__ = 'tag_history'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tag_id = db.Column(db.String(36), db.ForeignKey('tags.id'), nullable=False)
    
    # 操作信息
    action = db.Column(db.String(20), nullable=False)  # create, update, delete, move, merge
    action_description = db.Column(db.String(200))
    
    # 变更数据
    old_data = db.Column(JSONB)  # 变更前的数据
    new_data = db.Column(JSONB)  # 变更后的数据
    diff = db.Column(JSONB)  # 具体的变更内容
    
    # 操作者信息
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    user_agent = db.Column(db.String(500))
    ip_address = db.Column(db.String(45))
    
    # 审核信息
    reviewed_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    reviewed_at = db.Column(db.DateTime)
    review_status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    review_comment = db.Column(db.Text)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系定义
    tag = db.relationship('Tag', backref='history')
    user = db.relationship('User', foreign_keys=[user_id])
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'tag_id': self.tag_id,
            'action': self.action,
            'action_description': self.action_description,
            'old_data': self.old_data,
            'new_data': self.new_data,
            'diff': self.diff,
            'user_id': self.user_id,
            'user_agent': self.user_agent,
            'ip_address': self.ip_address,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'review_status': self.review_status,
            'review_comment': self.review_comment,
            'created_at': self.created_at.isoformat(),
        }
    
    def __repr__(self):
        return f'<TagHistory {self.action} on {self.tag_id}>'

class TagRelation(db.Model):
    """标签关系模型 - 用于存储标签之间的复杂关系"""
    __tablename__ = 'tag_relations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 关系的两端
    from_tag_id = db.Column(db.String(36), db.ForeignKey('tags.id'), nullable=False)
    to_tag_id = db.Column(db.String(36), db.ForeignKey('tags.id'), nullable=False)
    
    # 关系类型
    relation_type = db.Column(db.String(30), nullable=False)  # synonym, antonym, related, part_of, instance_of
    strength = db.Column(db.Numeric(3, 2), default=1.0)  # 关系强度 0-1
    
    # 方向性
    is_bidirectional = db.Column(db.Boolean, default=True)
    
    # 元数据
    description = db.Column(db.String(200))
    properties = db.Column(JSONB, default=dict)
    
    # 审核信息
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    approved_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='active')  # active, inactive, pending
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系定义
    from_tag = db.relationship('Tag', foreign_keys=[from_tag_id])
    to_tag = db.relationship('Tag', foreign_keys=[to_tag_id])
    creator = db.relationship('User', foreign_keys=[created_by])
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('from_tag_id', 'to_tag_id', 'relation_type', name='unique_tag_relation'),
        Index('idx_tag_relations_from', 'from_tag_id'),
        Index('idx_tag_relations_to', 'to_tag_id'),
        Index('idx_tag_relations_type', 'relation_type'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'from_tag_id': self.from_tag_id,
            'to_tag_id': self.to_tag_id,
            'relation_type': self.relation_type,
            'strength': float(self.strength),
            'is_bidirectional': self.is_bidirectional,
            'description': self.description,
            'properties': self.properties,
            'created_by': self.created_by,
            'approved_by': self.approved_by,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    def __repr__(self):
        return f'<TagRelation {self.from_tag_id} -> {self.to_tag_id} ({self.relation_type})>' 