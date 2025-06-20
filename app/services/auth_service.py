from datetime import datetime, timedelta
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy.exc import IntegrityError
import re
import logging

from app import db
from app.models.user import User, UserPermission

logger = logging.getLogger(__name__)

class AuthService:
    """认证服务类"""

    @staticmethod
    def validate_email(email):
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_username(username):
        """验证用户名格式"""
        pattern = r'^[a-zA-Z0-9_\u4e00-\u9fff]{2,20}$'  # 支持中文，2-20位
        return re.match(pattern, username) is not None

    @staticmethod
    def validate_password(password):
        """验证密码强度"""
        if len(password) < 6:
            return False, "密码长度至少6位"

        if len(password) > 50:
            return False, "密码长度不能超过50位"

        return True, "密码符合要求"

    @classmethod
    def register_user(cls, username, email, password, nickname=None):
        """
        用户注册

        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            nickname: 昵称（可选）

        Returns:
            tuple: (success: bool, message: str, user: User|None)
        """
        try:
            # 验证输入
            if not cls.validate_username(username):
                return False, "用户名格式不正确，只能包含字母、数字、下划线和中文，长度2-20位", None

            if not cls.validate_email(email):
                return False, "邮箱格式不正确", None

            is_valid, password_msg = cls.validate_password(password)
            if not is_valid:
                return False, password_msg, None

            # 检查用户名和邮箱是否已存在
            if User.query.filter_by(username=username).first():
                return False, "用户名已存在", None

            if User.query.filter_by(email=email).first():
                return False, "邮箱已被注册", None

            # 创建用户
            user = User(
                username=username,
                email=email,
                nickname=nickname or username
            )
            user.set_password(password)

            db.session.add(user)
            db.session.flush()  # 获取user.id

            # 创建用户权限
            permissions = UserPermission(user_id=user.id)
            db.session.add(permissions)

            db.session.commit()

            logger.info(f"新用户注册成功: {username}")
            return True, "注册成功", user

        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"用户注册数据库错误: {e}")
            return False, "用户名或邮箱已存在", None
        except Exception as e:
            db.session.rollback()
            logger.error(f"用户注册失败: {e}")
            return False, f"注册失败，请稍后重试", None

    @classmethod
    def login_user(cls, username_or_email, password):
        """
        用户登录

        Args:
            username_or_email: 用户名或邮箱
            password: 密码

        Returns:
            tuple: (success: bool, message: str, tokens: dict|None, user: User|None)
        """
        try:
            # 查找用户（支持用户名或邮箱登录）
            if cls.validate_email(username_or_email):
                user = User.query.filter_by(email=username_or_email).first()
            else:
                user = User.query.filter_by(username=username_or_email).first()

            if not user:
                return False, "用户不存在", None, None

            if not user.is_active:
                return False, "账户已被禁用", None, None

            if user.account_status == 'banned':
                return False, "账户已被封禁", None, None

            # 验证密码
            if not user.check_password(password):
                return False, "密码错误", None, None

            # 生成JWT tokens
            access_token = create_access_token(
                identity=user.id,
                additional_claims={
                    'username': user.username,
                    'reputation': user.reputation_score
                }
            )
            refresh_token = create_refresh_token(identity=user.id)

            # 更新最后登录时间
            user.last_login_at = datetime.utcnow()
            db.session.commit()

            tokens = {
                'access_token': access_token,
                'refresh_token': refresh_token
            }

            logger.info(f"用户登录成功: {user.username}")
            return True, "登录成功", tokens, user

        except Exception as e:
            logger.error(f"用户登录失败: {e}")
            return False, "登录失败，请稍后重试", None, None

    @classmethod
    def get_user_profile(cls, user_id):
        """
        获取用户信息

        Args:
            user_id: 用户ID

        Returns:
            tuple: (success: bool, message: str, user: User|None)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "用户不存在", None

            return True, "获取成功", user

        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return False, "获取失败", None

    @classmethod
    def update_user_profile(cls, user_id, **kwargs):
        """
        更新用户信息

        Args:
            user_id: 用户ID
            **kwargs: 要更新的字段

        Returns:
            tuple: (success: bool, message: str, user: User|None)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "用户不存在", None

            # 允许更新的字段
            allowed_fields = ['nickname', 'bio', 'avatar_url']

            updated = False
            for field, value in kwargs.items():
                if field in allowed_fields and hasattr(user, field):
                    setattr(user, field, value)
                    updated = True

            if not updated:
                return False, "没有有效的更新字段", None

            user.updated_at = datetime.utcnow()
            db.session.commit()

            logger.info(f"用户信息更新成功: {user.username}")
            return True, "更新成功", user

        except Exception as e:
            db.session.rollback()
            logger.error(f"用户信息更新失败: {e}")
            return False, "更新失败", None

    @classmethod
    def change_password(cls, user_id, old_password, new_password):
        """
        修改密码

        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "用户不存在"

            # 验证旧密码
            if not user.check_password(old_password):
                return False, "原密码错误"

            # 验证新密码
            is_valid, password_msg = cls.validate_password(new_password)
            if not is_valid:
                return False, password_msg

            # 设置新密码
            user.set_password(new_password)
            user.updated_at = datetime.utcnow()
            db.session.commit()

            logger.info(f"用户密码修改成功: {user.username}")
            return True, "密码修改成功"

        except Exception as e:
            db.session.rollback()
            logger.error(f"密码修改失败: {e}")
            return False, "密码修改失败"
