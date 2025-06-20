# app/api/auth.py - 完整Swagger版本
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_limiter.util import get_remote_address

from app.services.auth_service import AuthService
from app.utils.helpers import success_response, error_response, validate_json
from app.utils.decorators import rate_limit
from app import limiter

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
@validate_json('username', 'email', 'password')
def register():
    """
    用户注册
    ---
    tags:
      - Authentication
    summary: 用户注册
    description: 创建新用户账户
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - email
            - password
          properties:
            username:
              type: string
              description: 用户名，3-20个字符
              example: "testuser"
              minLength: 3
              maxLength: 20
            email:
              type: string
              format: email
              description: 邮箱地址
              example: "user@example.com"
            password:
              type: string
              description: 密码，至少8个字符
              example: "password123"
              minLength: 8
            nickname:
              type: string
              description: 昵称（可选）
              example: "测试用户"
              maxLength: 50
    responses:
      201:
        description: 注册成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "注册成功"
            data:
              type: object
              properties:
                user:
                  $ref: '#/definitions/User'
                permissions:
                  $ref: '#/definitions/UserPermission'
      400:
        description: 请求参数错误或用户已存在
        schema:
          $ref: '#/definitions/ErrorResponse'
      429:
        description: 请求过于频繁
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    data = request.get_json()

    success, message, user = AuthService.register_user(
        username=data['username'],
        email=data['email'],
        password=data['password'],
        nickname=data.get('nickname')
    )

    if success:
        return success_response(
            data={
                'user': user.to_dict(),
                'permissions': user.permissions.to_dict() if user.permissions else {}
            },
            message=message,
            code=201
        )
    else:
        return error_response(message, 400)

@bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
@validate_json('username', 'password')
def login():
    """
    用户登录
    ---
    tags:
      - Authentication
    summary: 用户登录
    description: 用户使用用户名或邮箱登录
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              description: 用户名或邮箱
              example: "testuser"
            password:
              type: string
              description: 密码
              example: "password123"
    responses:
      200:
        description: 登录成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "登录成功"
            data:
              type: object
              properties:
                tokens:
                  type: object
                  properties:
                    access_token:
                      type: string
                      description: JWT访问令牌
                      example: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                user:
                  $ref: '#/definitions/User'
                permissions:
                  $ref: '#/definitions/UserPermission'
      400:
        description: 请求参数错误
        schema:
          $ref: '#/definitions/ErrorResponse'
      401:
        description: 用户名或密码错误
        schema:
          $ref: '#/definitions/ErrorResponse'
      429:
        description: 请求过于频繁
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    data = request.get_json()

    success, message, tokens, user = AuthService.login_user(
        username_or_email=data['username'],
        password=data['password']
    )

    if success:
        return success_response(
            data={
                'tokens': tokens,
                'user': user.to_dict(),
                'permissions': user.permissions.to_dict() if user.permissions else {}
            },
            message=message
        )
    else:
        return error_response(message, 401)

@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    获取用户信息
    ---
    tags:
      - Authentication
    summary: 获取当前用户信息
    description: 获取已登录用户的详细信息
    security:
      - JWT: []
    responses:
      200:
        description: 获取成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "获取成功"
            data:
              type: object
              properties:
                user:
                  $ref: '#/definitions/UserDetail'
                permissions:
                  $ref: '#/definitions/UserPermission'
      401:
        description: 未授权或令牌无效
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: 用户不存在
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    user_id = get_jwt_identity()

    success, message, user = AuthService.get_user_profile(user_id)

    if success:
        return success_response(
            data={
                'user': user.to_dict(include_sensitive=True),
                'permissions': user.permissions.to_dict() if user.permissions else {}
            },
            message=message
        )
    else:
        return error_response(message, 404)

@bp.route('/profile', methods=['PUT'])
@jwt_required()
@limiter.limit("10 per hour")
def update_profile():
    """
    更新用户信息
    ---
    tags:
      - Authentication
    summary: 更新用户信息
    description: 更新当前用户的个人信息
    security:
      - JWT: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nickname:
              type: string
              description: 昵称
              example: "新昵称"
              maxLength: 50
            bio:
              type: string
              description: 个人简介
              example: "这是我的个人简介"
              maxLength: 500
            avatar_url:
              type: string
              format: uri
              description: 头像URL
              example: "https://example.com/avatar.jpg"
    responses:
      200:
        description: 更新成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "更新成功"
            data:
              type: object
              properties:
                user:
                  $ref: '#/definitions/User'
      400:
        description: 请求参数错误
        schema:
          $ref: '#/definitions/ErrorResponse'
      401:
        description: 未授权
        schema:
          $ref: '#/definitions/ErrorResponse'
      429:
        description: 请求过于频繁
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return error_response("请求体不能为空", 400)

    # 过滤允许更新的字段
    allowed_fields = ['nickname', 'bio', 'avatar_url']
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    if not update_data:
        return error_response("没有有效的更新字段", 400)

    success, message, user = AuthService.update_user_profile(user_id, **update_data)

    if success:
        return success_response(
            data={'user': user.to_dict()},
            message=message
        )
    else:
        return error_response(message, 400)

@bp.route('/change-password', methods=['POST'])
@jwt_required()
@limiter.limit("5 per hour")
@validate_json('old_password', 'new_password')
def change_password():
    """
    修改密码
    ---
    tags:
      - Authentication
    summary: 修改密码
    description: 修改当前用户的登录密码
    security:
      - JWT: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - old_password
            - new_password
          properties:
            old_password:
              type: string
              description: 原密码
              example: "oldpassword123"
            new_password:
              type: string
              description: 新密码，至少8个字符
              example: "newpassword123"
              minLength: 8
    responses:
      200:
        description: 修改成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "密码修改成功"
      400:
        description: 请求参数错误或原密码错误
        schema:
          $ref: '#/definitions/ErrorResponse'
      401:
        description: 未授权
        schema:
          $ref: '#/definitions/ErrorResponse'
      429:
        description: 请求过于频繁
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    user_id = get_jwt_identity()
    data = request.get_json()

    success, message = AuthService.change_password(
        user_id=user_id,
        old_password=data['old_password'],
        new_password=data['new_password']
    )

    if success:
        return success_response(message=message)
    else:
        return error_response(message, 400)

@bp.route('/verify-token', methods=['POST'])
@jwt_required()
def verify_token():
    """
    验证令牌
    ---
    tags:
      - Authentication
    summary: 验证JWT令牌
    description: 验证当前JWT令牌是否有效
    security:
      - JWT: []
    responses:
      200:
        description: 令牌有效
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "令牌有效"
            data:
              type: object
              properties:
                valid:
                  type: boolean
                  example: true
                user:
                  $ref: '#/definitions/User'
                claims:
                  type: object
                  description: JWT声明信息
      401:
        description: 令牌无效或已过期
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    user_id = get_jwt_identity()
    jwt_claims = get_jwt()

    success, message, user = AuthService.get_user_profile(user_id)

    if success:
        return success_response(
            data={
                'valid': True,
                'user': user.to_dict(),
                'claims': jwt_claims
            },
            message="令牌有效"
        )
    else:
        return error_response("令牌无效", 401)
