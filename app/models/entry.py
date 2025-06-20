from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import func, text
import uuid

from app import db

class Entry(db.Model):
    __tablename__ = 'entries'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    # 内容
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    content_type = db.Column(db.String(20), default='mixed')  # text, image, video, audio, mixed

    # 元数据
    location_name = db.Column(db.String(200))
    geo_coordinates = db.Column(db.String(100))  # "lat,lng"格式
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    weather_info = db.Column(JSONB)
    mood_score = db.Column(db.Integer)  # 1-10

    # 状态
    visibility = db.Column(db.String(20), default='public')  # public, private, friends
    is_deleted = db.Column(db.Boolean, default=False)

    # 统计
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 搜索向量（PostgreSQL全文搜索）
    search_vector = db.Column(db.Text)

    # 关系定义（使用字符串引用避免循环导入）
    media_files = db.relationship('MediaFile', backref='entry', lazy='dynamic', cascade='all, delete-orphan')
    entry_tags = db.relationship('EntryTag', backref='entry', lazy='dynamic', cascade='all, delete-orphan')
    author = db.relationship('User', backref=db.backref('entries', lazy='dynamic'))

    def get_tags(self):
        """获取标签列表"""
        return [et.tag_id for et in self.entry_tags]

    def get_media_count(self):
        """获取媒体文件数量"""
        return self.media_files.count()

    def to_dict(self, include_content=True):
        """转换为字典"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content_type': self.content_type,
            'location_name': self.location_name,
            'geo_coordinates': self.geo_coordinates,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'weather_info': self.weather_info,
            'mood_score': self.mood_score,
            'visibility': self.visibility,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'author': {
                'id': self.author.id,
                'username': self.author.username,
                'nickname': self.author.nickname,
                'email': self.author.email,
                'created_at': self.author.created_at,
                'updated_at': self.author.updated_at,
            } if self.author else None,
            'tags': self.get_tags(),
            'media_count': self.get_media_count()
        }

        if include_content:
            data['content'] = self.content

        return data

    def __repr__(self):
        return f'<Entry {self.title or self.id}>'

class EntryTag(db.Model):
    __tablename__ = 'entry_tags'

    entry_id = db.Column(db.String(36), db.ForeignKey('entries.id'), primary_key=True)
    tag_id = db.Column(db.String(100), primary_key=True)

    # 标签元信息
    confidence = db.Column(db.Numeric(3, 2), default=1.00)
    source = db.Column(db.String(20), default='manual')  # manual, auto, suggested
    tagged_by = db.Column(db.String(36), db.ForeignKey('users.id'))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'entry_id': self.entry_id,
            'tag_id': self.tag_id,
            'confidence': float(self.confidence),
            'source': self.source,
            'tagged_by': self.tagged_by,
            'created_at': self.created_at.isoformat()
        }
