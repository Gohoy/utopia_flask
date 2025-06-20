from datetime import datetime, timedelta
from sqlalchemy import desc, asc, func, or_
from sqlalchemy.exc import IntegrityError
import logging

from app import db
from app.models.entry import Entry, EntryTag
from app.models.user import User
from app.models.media import MediaFile  # 从正确的位置导入

logger = logging.getLogger(__name__)


class EntryService:
    """图鉴条目服务类"""

    @classmethod
    def create_entry(cls, user_id, title, content=None, content_type='mixed',
                     location_name=None, geo_coordinates=None, recorded_at=None,
                     weather_info=None, mood_score=None, visibility='public', tags=None):
        """
        创建图鉴条目

        Args:
            user_id: 用户ID
            title: 标题
            content: 内容
            content_type: 内容类型
            location_name: 地点名称
            geo_coordinates: 地理坐标 "lat,lng"
            recorded_at: 记录时间
            weather_info: 天气信息
            mood_score: 心情评分 1-10
            visibility: 可见性 public/private/friends
            tags: 标签列表

        Returns:
            tuple: (success: bool, message: str, entry: Entry|None)
        """
        try:
            # 验证用户存在
            user = User.query.get(user_id)
            if not user:
                return False, "用户不存在", None

            # 验证必填字段
            if not title or len(title.strip()) == 0:
                return False, "标题不能为空", None

            if len(title) > 200:
                return False, "标题长度不能超过200字符", None

            # 验证心情评分
            if mood_score is not None and (mood_score < 1 or mood_score > 10):
                return False, "心情评分必须在1-10之间", None

            # 验证可见性
            if visibility not in ['public', 'private', 'friends']:
                return False, "可见性设置无效", None

            # 处理记录时间
            if recorded_at:
                if isinstance(recorded_at, str):
                    try:
                        recorded_at = datetime.fromisoformat(recorded_at.replace('Z', '+00:00'))
                    except ValueError:
                        return False, "记录时间格式错误", None

            # 验证地理坐标格式
            if geo_coordinates:
                try:
                    lat, lng = geo_coordinates.split(',')
                    lat, lng = float(lat.strip()), float(lng.strip())
                    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                        return False, "地理坐标超出有效范围", None
                except:
                    return False, "地理坐标格式错误，应为 'lat,lng'", None

            # 验证标签
            valid_tags = []
            if tags and len(tags) > 0:
                from app.services.tag_service import TagService
                try:
                    success, message, validated_tags = TagService.validate_tags(tags)
                    if success:
                        valid_tags = validated_tags
                    else:
                        # 标签验证失败时，记录警告但不阻止条目创建
                        logger.warning(f"标签验证失败，跳过标签: {message}")
                        # 可以选择是否返回错误，或者忽略无效标签继续创建
                        # 这里选择继续创建条目，但不添加标签
                        valid_tags = []
                except Exception as e:
                    # 标签服务异常时，记录错误但不阻止条目创建
                    logger.error(f"标签验证异常: {e}")
                    valid_tags = []
            # 创建条目
            entry = Entry(
                user_id=user_id,
                title=title.strip(),
                content=content,
                content_type=content_type,
                location_name=location_name,
                geo_coordinates=geo_coordinates,
                recorded_at=recorded_at or datetime.utcnow(),
                weather_info=weather_info,
                mood_score=mood_score,
                visibility=visibility
            )

            db.session.add(entry)
            db.session.flush()  # 获取entry.id

            # 添加标签
            if valid_tags:
                success, message = cls._add_tags_to_entry(entry.id, valid_tags, user_id)
                if not success:
                    db.session.rollback()
                    return False, f"添加标签失败: {message}", None

            db.session.commit()

            logger.info(f"图鉴条目创建成功: {entry.id} by {user.username}")
            return True, "创建成功", entry

        except Exception as e:
            db.session.rollback()
            logger.error(f"创建图鉴条目失败: {e}")
            return False, "创建失败，请稍后重试", None

    @classmethod
    def get_entry_by_id(cls, entry_id, current_user_id=None):
        """
        根据ID获取图鉴条目

        Args:
            entry_id: 条目ID
            current_user_id: 当前用户ID（用于权限检查）

        Returns:
            tuple: (success: bool, message: str, entry: Entry|None)
        """
        try:
            entry = Entry.query.filter_by(id=entry_id, is_deleted=False).first()

            if not entry:
                return False, "条目不存在", None

            # 权限检查
            if entry.visibility == 'private' and entry.user_id != current_user_id:
                return False, "没有权限查看此条目", None

            # 增加浏览次数（不为自己的浏览计数）
            if current_user_id != entry.user_id:
                entry.view_count += 1
                db.session.commit()

            return True, "获取成功", entry

        except Exception as e:
            logger.error(f"获取图鉴条目失败: {e}")
            return False, "获取失败", None

    @classmethod
    def update_entry(cls, entry_id, user_id, **kwargs):
        """
        更新图鉴条目

        Args:
            entry_id: 条目ID
            user_id: 用户ID
            **kwargs: 要更新的字段

        Returns:
            tuple: (success: bool, message: str, entry: Entry|None)
        """
        try:
            entry = Entry.query.filter_by(id=entry_id, is_deleted=False).first()

            if not entry:
                return False, "条目不存在", None

            # 权限检查
            if entry.user_id != user_id:
                return False, "没有权限修改此条目", None

            # 允许更新的字段
            allowed_fields = [
                'title', 'content', 'content_type', 'location_name',
                'geo_coordinates', 'recorded_at', 'weather_info',
                'mood_score', 'visibility'
            ]

            updated = False
            for field, value in kwargs.items():
                if field in allowed_fields and hasattr(entry, field):
                    # 特殊处理
                    if field == 'title':
                        if not value or len(value.strip()) == 0:
                            return False, "标题不能为空", None
                        if len(value) > 200:
                            return False, "标题长度不能超过200字符", None
                        value = value.strip()

                    if field == 'mood_score' and value is not None:
                        if value < 1 or value > 10:
                            return False, "心情评分必须在1-10之间", None

                    if field == 'visibility' and value not in ['public', 'private', 'friends']:
                        return False, "可见性设置无效", None

                    if field == 'recorded_at' and isinstance(value, str):
                        try:
                            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except ValueError:
                            return False, "记录时间格式错误", None

                    if field == 'geo_coordinates' and value:
                        try:
                            lat, lng = value.split(',')
                            lat, lng = float(lat.strip()), float(lng.strip())
                            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                                return False, "地理坐标超出有效范围", None
                        except:
                            return False, "地理坐标格式错误，应为 'lat,lng'", None

                    setattr(entry, field, value)
                    updated = True

            # 处理标签更新
            if 'tags' in kwargs:
                success, message = cls._update_entry_tags(entry_id, kwargs['tags'], user_id)
                if not success:
                    return False, f"更新标签失败: {message}", None
                updated = True

            if not updated:
                return False, "没有有效的更新字段", None

            entry.updated_at = datetime.utcnow()
            db.session.commit()

            logger.info(f"图鉴条目更新成功: {entry_id}")
            return True, "更新成功", entry

        except Exception as e:
            db.session.rollback()
            logger.error(f"更新图鉴条目失败: {e}")
            return False, "更新失败", None

    @classmethod
    def delete_entry(cls, entry_id, user_id):
        """
        删除图鉴条目（软删除）

        Args:
            entry_id: 条目ID
            user_id: 用户ID

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            entry = Entry.query.filter_by(id=entry_id, is_deleted=False).first()

            if not entry:
                return False, "条目不存在"

            # 权限检查
            if entry.user_id != user_id:
                return False, "没有权限删除此条目"

            # 软删除
            entry.is_deleted = True
            entry.updated_at = datetime.utcnow()
            db.session.commit()

            logger.info(f"图鉴条目删除成功: {entry_id}")
            return True, "删除成功"

        except Exception as e:
            db.session.rollback()
            logger.error(f"删除图鉴条目失败: {e}")
            return False, "删除失败"

    @classmethod
    def get_entries_list(cls, page=1, per_page=20, user_id=None, tag_id=None,
                         search_query=None, content_type=None, visibility='public',
                         sort_by='created_at', sort_order='desc', current_user_id=None):
        """
        获取图鉴条目列表

        Args:
            page: 页码
            per_page: 每页数量
            user_id: 筛选特定用户的条目
            tag_id: 筛选特定标签的条目
            search_query: 搜索关键词
            content_type: 内容类型筛选
            visibility: 可见性筛选
            sort_by: 排序字段
            sort_order: 排序方向 asc/desc
            current_user_id: 当前用户ID

        Returns:
            tuple: (success: bool, message: str, data: dict|None)
        """
        try:
            # 构建查询
            query = Entry.query.filter_by(is_deleted=False)

            # 可见性筛选
            if current_user_id:
                # 登录用户可以看到：公开的 + 自己的私有/朋友可见的
                query = query.filter(
                    or_(
                        Entry.visibility == 'public',
                        Entry.user_id == current_user_id
                    )
                )
            else:
                # 未登录用户只能看到公开的
                query = query.filter_by(visibility='public')

            # 用户筛选
            if user_id:
                query = query.filter_by(user_id=user_id)

            # 内容类型筛选
            if content_type:
                query = query.filter_by(content_type=content_type)

            # 标签筛选
            if tag_id:
                query = query.join(EntryTag).filter(EntryTag.tag_id == tag_id)

            # 搜索功能
            if search_query:
                search_filter = or_(
                    Entry.title.ilike(f'%{search_query}%'),
                    Entry.content.ilike(f'%{search_query}%'),
                    Entry.location_name.ilike(f'%{search_query}%')
                )
                query = query.filter(search_filter)

            # 排序
            if hasattr(Entry, sort_by):
                if sort_order.lower() == 'desc':
                    query = query.order_by(desc(getattr(Entry, sort_by)))
                else:
                    query = query.order_by(asc(getattr(Entry, sort_by)))
            else:
                query = query.order_by(desc(Entry.created_at))

            # 分页
            try:
                pagination = query.paginate(
                    page=page,
                    per_page=min(per_page, 100),  # 限制最大50条
                    error_out=False
                )
            except Exception as e:
                logger.error(f"分页查询失败: {e}")
                return False, "查询失败", None

            # 构建响应数据
            entries_data = []
            for entry in pagination.items:
                entry_dict = entry.to_dict(include_content=False)  # 列表不包含完整内容
                entries_data.append(entry_dict)

            result = {
                'entries': entries_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next,
                    'prev_num': pagination.prev_num,
                    'next_num': pagination.next_num
                },
                'filters': {
                    'user_id': user_id,
                    'tag_id': tag_id,
                    'search_query': search_query,
                    'content_type': content_type,
                    'sort_by': sort_by,
                    'sort_order': sort_order
                }
            }

            return True, "获取成功", result

        except Exception as e:
            logger.error(f"获取条目列表失败: {e}")
            return False, "获取失败", None

    @classmethod
    def get_user_entries_stats(cls, user_id):
        """
        获取用户图鉴条目统计

        Args:
            user_id: 用户ID

        Returns:
            tuple: (success: bool, message: str, stats: dict|None)
        """
        try:
            # 基础统计
            total_entries = Entry.query.filter_by(user_id=user_id, is_deleted=False).count()

            # 按内容类型统计
            content_type_stats = db.session.query(
                Entry.content_type,
                func.count(Entry.id).label('count')
            ).filter_by(
                user_id=user_id,
                is_deleted=False
            ).group_by(Entry.content_type).all()

            # 按可见性统计
            visibility_stats = db.session.query(
                Entry.visibility,
                func.count(Entry.id).label('count')
            ).filter_by(
                user_id=user_id,
                is_deleted=False
            ).group_by(Entry.visibility).all()

            # 最近30天的创建统计
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_entries = Entry.query.filter(
                Entry.user_id == user_id,
                Entry.is_deleted == False,
                Entry.created_at >= thirty_days_ago
            ).count()

            # 总浏览量
            total_views = db.session.query(
                func.sum(Entry.view_count)
            ).filter_by(
                user_id=user_id,
                is_deleted=False
            ).scalar() or 0

            # 总点赞数
            total_likes = db.session.query(
                func.sum(Entry.like_count)
            ).filter_by(
                user_id=user_id,
                is_deleted=False
            ).scalar() or 0

            stats = {
                'total_entries': total_entries,
                'recent_entries_30d': recent_entries,
                'total_views': int(total_views),
                'total_likes': int(total_likes),
                'content_type_distribution': {
                    stat.content_type: stat.count
                    for stat in content_type_stats
                },
                'visibility_distribution': {
                    stat.visibility: stat.count
                    for stat in visibility_stats
                }
            }

            return True, "获取成功", stats

        except Exception as e:
            logger.error(f"获取用户统计失败: {e}")
            return False, "获取失败", None

    @classmethod
    def _add_tags_to_entry(cls, entry_id, tag_ids, user_id):
        """为条目添加标签 - 更新版本"""
        try:
            # 验证标签ID格式
            if not isinstance(tag_ids, list):
                return False, "标签列表格式错误"

            # 使用TagService验证标签
            from app.services.tag_service import TagService
            success, message, valid_tags = TagService.validate_tags(tag_ids)

            # 删除现有标签关联
            EntryTag.query.filter_by(entry_id=entry_id).delete()

            # 添加新的标签关联
            for tag_id in valid_tags:
                entry_tag = EntryTag(
                    entry_id=entry_id,
                    tag_id=tag_id.strip(),
                    tagged_by=user_id,
                    source='manual'
                )
                db.session.add(entry_tag)

            if not success:
                logger.warning(f"标签验证警告: {message}")

            return True, f"成功添加{len(valid_tags)}个标签"

        except Exception as e:
            logger.error(f"添加标签失败: {e}")
            return False, "添加标签失败"

    @classmethod
    def _update_entry_tags(cls, entry_id, tag_ids, user_id):
        """
        更新条目标签

        Args:
            entry_id: 条目ID
            tag_ids: 标签ID列表
            user_id: 用户ID

        Returns:
            tuple: (success: bool, message: str)
        """
        return cls._add_tags_to_entry(entry_id, tag_ids, user_id)
