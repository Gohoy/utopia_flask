# app/models/user.py - 修复版本
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

from app import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(100))
    avatar_url = db.Column(db.String(500))
    bio = db.Column(db.Text)
    reputation_score = db.Column(db.Integer, default=0)
    contribution_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    account_status = db.Column(db.String(20), default='normal')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)

    # 关系
    permissions = db.relationship('UserPermission', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """检查密码"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_sensitive=False):
        """转换为字典 - 修复版本，确保包含所有必要字段"""
        data = {
            'id': str(self.id),
            'username': self.username,
            'email': self.email,  # 确保email字段总是包含
            'nickname': self.nickname,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'reputation_score': self.reputation_score or 0,
            'contribution_count': self.contribution_count or 0,
            'is_active': self.is_active,
            'account_status': self.account_status or 'normal',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
        }

        # 如果需要包含敏感信息
        if include_sensitive:
            data.update({
                'permissions': self.permissions.to_dict() if self.permissions else {
                    'can_create_tags': False,
                    'can_edit_tags': False,
                    'can_approve_changes': False,
                    'max_edits_per_day': 10
                }
            })

        return data

    def __repr__(self):
        return f'<User {self.username}>'

class UserPermission(db.Model):
    __tablename__ = 'user_permissions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    can_create_tags = db.Column(db.Boolean, default=True)
    can_edit_tags = db.Column(db.Boolean, default=True)
    can_approve_changes = db.Column(db.Boolean, default=False)
    max_edits_per_day = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'can_create_tags': self.can_create_tags,
            'can_edit_tags': self.can_edit_tags,
            'can_approve_changes': self.can_approve_changes,
            'max_edits_per_day': self.max_edits_per_day
        }

    def __repr__(self):
        return f'<UserPermission {self.user_id}>'
