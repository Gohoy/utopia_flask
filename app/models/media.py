from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
import uuid

from app import db

class MediaFile(db.Model):
    __tablename__ = 'media_files'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entry_id = db.Column(db.String(36), db.ForeignKey('entries.id', ondelete='CASCADE'), nullable=False)

    # 文件信息
    file_type = db.Column(db.String(20), nullable=False)  # image, video, audio
    original_filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger)
    mime_type = db.Column(db.String(100))

    # 媒体元数据
    width = db.Column(db.Integer)  # 图片/视频宽度
    height = db.Column(db.Integer)  # 图片/视频高度
    duration_seconds = db.Column(db.Integer)  # 视频/音频时长
    thumbnail_path = db.Column(db.String(500))  # 缩略图路径

    # EXIF和其他元数据
    file_metadata = db.Column(JSONB, default={})

    # 排序
    sort_order = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'entry_id': self.entry_id,
            'file_type': self.file_type,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'width': self.width,
            'height': self.height,
            'duration_seconds': self.duration_seconds,
            'thumbnail_path': self.thumbnail_path,
            'metadata': self.file_metadata,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<MediaFile {self.original_filename}>'
