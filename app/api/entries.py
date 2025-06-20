from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.entry_service import EntryService
from app.utils.helpers import success_response, error_response, validate_json
from app.utils.decorators import rate_limit, cache_response
from app import limiter

bp = Blueprint('entries', __name__)

@bp.route('', methods=['POST'])
@jwt_required()
@limiter.limit("20 per hour")
@validate_json('title', 'content')
def create_entry():
    """创建图鉴条目
    ---
    tags:
      - entries
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
              description: 条目标题
              example: "我的第一次旅行"
            content:
              type: string
              description: 条目内容
              example: "2023年5月1日，我去了黄山..."
            content_type:
              type: string
              description: 内容类型 (mixed/text/photo/video)
              default: mixed
            location_name:
              type: string
              description: 地点名称
              example: "黄山风景区"
            geo_coordinates:
              type: array
              items:
                type: number
              description: 地理坐标 [经度, 纬度]
              example: [118.144, 30.12]
            recorded_at:
              type: string
              format: date
              description: 记录时间
              example: "2023-05-01"
            weather_info:
              type: string
              description: 天气信息
              example: "晴天，25°C"
            mood_score:
              type: integer
              description: 心情评分 (1-10)
              example: 8
            visibility:
              type: string
              description: 可见性 (public/private/friends)
              default: public
            tags:
              type: array
              items:
                type: string
              description: 标签列表
              example: ["旅行", "自然"]
    responses:
      201:
        description: 创建成功
        schema:
          $ref: '#/definitions/SuccessResponse'
      400:
        description: 请求错误
        schema:
          $ref: '#/definitions/ErrorResponse'
      429:
        description: 请求过于频繁
    """
    user_id = get_jwt_identity()
    data = request.get_json()

    success, message, entry = EntryService.create_entry(
        user_id=user_id,
        title=data.get('title'),
        content=data.get('content'),
        content_type=data.get('content_type', 'mixed'),
        location_name=data.get('location_name'),
        geo_coordinates=data.get('geo_coordinates'),
        recorded_at=data.get('recorded_at'),
        weather_info=data.get('weather_info'),
        mood_score=data.get('mood_score'),
        visibility=data.get('visibility', 'public'),
        tags=data.get('tags', [])
    )

    if success:
        return success_response(
            data={'entry': entry.to_dict()},
            message=message,
            code=201
        )
    else:
        return error_response(message, 400)

@bp.route('/<entry_id>', methods=['GET'])
@rate_limit(max_requests=100, window=60, per='ip')
def get_entry(entry_id):
    """获取单个图鉴条目
    ---
    tags:
      - entries
    parameters:
      - in: path
        name: entry_id
        type: string
        required: true
        description: 条目ID
    responses:
      200:
        description: 获取成功
        schema:
          $ref: '#/definitions/SuccessResponse'
      403:
        description: 无权限
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: 条目不存在
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    # 尝试获取当前用户ID（如果已登录）
    current_user_id = None
    try:
        current_user_id = get_jwt_identity()
    except:
        pass  # 未登录用户

    success, message, entry = EntryService.get_entry_by_id(entry_id, current_user_id)

    if success:
        return success_response(
            data={'entry': entry.to_dict()},
            message=message
        )
    else:
        return error_response(message, 404 if "不存在" in message else 403)

@bp.route('/<entry_id>', methods=['PUT'])
@jwt_required()
@limiter.limit("30 per hour")
def update_entry(entry_id):
    """更新图鉴条目
    ---
    tags:
      - entries
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: entry_id
        type: string
        required: true
        description: 条目ID
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
              description: 标题
            content:
              type: string
              description: 内容
            content_type:
              type: string
              description: 内容类型
            location_name:
              type: string
              description: 地点名称
            geo_coordinates:
              type: array
              items:
                type: number
              description: 地理坐标
            recorded_at:
              type: string
              format: date
              description: 记录时间
            weather_info:
              type: string
              description: 天气信息
            mood_score:
              type: integer
              description: 心情评分
            visibility:
              type: string
              description: 可见性
            tags:
              type: array
              items:
                type: string
              description: 标签
    responses:
      200:
        description: 更新成功
        schema:
          $ref: '#/definitions/SuccessResponse'
      400:
        description: 请求错误
        schema:
          $ref: '#/definitions/ErrorResponse'
      403:
        description: 无权限
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return error_response("请求体不能为空", 400)

    success, message, entry = EntryService.update_entry(entry_id, user_id, **data)

    if success:
        return success_response(
            data={'entry': entry.to_dict()},
            message=message
        )
    else:
        return error_response(message, 400 if "权限" not in message else 403)

@bp.route('/<entry_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("10 per hour")
def delete_entry(entry_id):
    """删除图鉴条目
    ---
    tags:
      - entries
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: entry_id
        type: string
        required: true
        description: 条目ID
    responses:
      200:
        description: 删除成功
        schema:
          $ref: '#/definitions/SuccessResponse'
      403:
        description: 无权限
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: 条目不存在
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    user_id = get_jwt_identity()

    success, message = EntryService.delete_entry(entry_id, user_id)

    if success:
        return success_response(message=message)
    else:
        return error_response(message, 403 if "权限" in message else 404)

@bp.route('', methods=['GET'])
@cache_response(expire=300, key_prefix="entries_list")  # 5分钟缓存
def get_entries_list():
    """获取图鉴条目列表
    ---
    tags:
      - entries
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
        description: 页码
      - in: query
        name: per_page
        type: integer
        default: 20
        maximum: 100
        description: 每页数量
      - in: query
        name: user_id
        type: string
        description: 用户ID
      - in: query
        name: tag_id
        type: string
        description: 标签ID
      - in: query
        name: search
        type: string
        description: 搜索关键词
      - in: query
        name: content_type
        type: string
        description: 内容类型
      - in: query
        name: sort_by
        type: string
        default: created_at
        description: 排序字段
      - in: query
        name: sort_order
        type: string
        default: desc
        description: 排序顺序
    responses:
      200:
        description: 获取成功
        schema:
          $ref: '#/definitions/SuccessResponse'
      400:
        description: 请求错误
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)  # 最大100条
    user_id = request.args.get('user_id')
    tag_id = request.args.get('tag_id')
    search_query = request.args.get('search')
    content_type = request.args.get('content_type')
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')

    # 获取当前用户ID
    current_user_id = None
    try:
        current_user_id = get_jwt_identity()
    except:
        pass

    success, message, data = EntryService.get_entries_list(
        page=page,
        per_page=per_page,
        user_id=user_id,
        tag_id=tag_id,
        search_query=search_query,
        content_type=content_type,
        sort_by=sort_by,
        sort_order=sort_order,
        current_user_id=current_user_id
    )

    if success:
        return success_response(data=data, message=message)
    else:
        return error_response(message, 400)

@bp.route('/my', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=60, window=60)
def get_my_entries():
    """获取我的图鉴条目
    ---
    tags:
      - entries
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
        description: 页码
      - in: query
        name: per_page
        type: integer
        default: 20
        maximum: 100
        description: 每页数量
      - in: query
        name: content_type
        type: string
        description: 内容类型
      - in: query
        name: visibility
        type: string
        default: all
        description: 可见性 (all/public/private/friends)
      - in: query
        name: sort_by
        type: string
        default: created_at
        description: 排序字段
      - in: query
        name: sort_order
        type: string
        default: desc
        description: 排序顺序
    responses:
      200:
        description: 获取成功
        schema:
          $ref: '#/definitions/SuccessResponse'
      400:
        description: 请求错误
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    user_id = get_jwt_identity()

    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    content_type = request.args.get('content_type')
    visibility = request.args.get('visibility', 'all')  # all, public, private, friends
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')

    success, message, data = EntryService.get_entries_list(
        page=page,
        per_page=per_page,
        user_id=user_id,
        content_type=content_type,
        visibility=None if visibility == 'all' else visibility,
        sort_by=sort_by,
        sort_order=sort_order,
        current_user_id=user_id
    )

    if success:
        return success_response(data=data, message=message)
    else:
        return error_response(message, 400)

@bp.route('/stats/<user_id>', methods=['GET'])
@cache_response(expire=1800, key_prefix="user_stats")  # 30分钟缓存
def get_user_stats(user_id):
    """获取用户图鉴统计
    ---
    tags:
      - entries
    parameters:
      - in: path
        name: user_id
        type: string
        required: true
        description: 用户ID
    responses:
      200:
        description: 获取成功
        schema:
          $ref: '#/definitions/SuccessResponse'
      404:
        description: 用户不存在
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    success, message, stats = EntryService.get_user_entries_stats(user_id)

    if success:
        return success_response(data={'stats': stats}, message=message)
    else:
        return error_response(message, 404)

@bp.route('/my/stats', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=30, window=60)
def get_my_stats():
    """获取我的图鉴统计
    ---
    tags:
      - entries
    security:
      - BearerAuth: []
    responses:
      200:
        description: 获取成功
        schema:
          $ref: '#/definitions/SuccessResponse'
      400:
        description: 请求错误
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    user_id = get_jwt_identity()

    success, message, stats = EntryService.get_user_entries_stats(user_id)

    if success:
        return success_response(data={'stats': stats}, message=message)
    else:
        return error_response(message, 400)

@bp.route('/<entry_id>/tags', methods=['PUT'])
@jwt_required()
@limiter.limit("50 per hour")
@validate_json('tags')
def update_entry_tags(entry_id):
    """更新图鉴条目的标签
    ---
    tags:
      - entries
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: entry_id
        type: string
        required: true
        description: 条目ID
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            tags:
              type: array
              items:
                type: string
              description: 标签列表
              example: ["旅行", "自然"]
    responses:
      200:
        description: 更新成功
        schema:
          $ref: '#/definitions/SuccessResponse'
      400:
        description: 请求错误
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    tags = data.get('tags', [])

    if not isinstance(tags, list):
        return error_response("标签必须是数组格式", 400)

    success, message, entry = EntryService.update_entry(
        entry_id, user_id, tags=tags
    )

    if success:
        return success_response(
            data={'entry': entry.to_dict()},
            message="标签更新成功"
        )
    else:
        return error_response(message, 400)

@bp.route('/search', methods=['GET'])
@cache_response(expire=600, key_prefix="entries_search")  # 10分钟缓存
def search_entries():
    """搜索图鉴条目
    ---
    tags:
      - entries
    parameters:
      - in: query
        name: q
        type: string
        required: true
        description: 搜索关键词
      - in: query
        name: page
        type: integer
        default: 1
        description: 页码
      - in: query
        name: per_page
        type: integer
        default: 20
        maximum: 50
        description: 每页数量
    responses:
      200:
        description: 搜索成功
        schema:
          $ref: '#/definitions/SuccessResponse'
      400:
        description: 请求错误
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    query = request.args.get('q', '').strip()
    if not query:
        return error_response("搜索关键词不能为空", 400)

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    # 获取当前用户ID
    current_user_id = None
    try:
        current_user_id = get_jwt_identity()
    except:
        pass

    success, message, data = EntryService.get_entries_list(
        page=page,
        per_page=per_page,
        search_query=query,
        current_user_id=current_user_id
    )

    if success:
        return success_response(data=data, message=message)
    else:
        return error_response(message, 400)

@bp.route('/hot', methods=['GET'])
@cache_response(expire=3600, key_prefix="hot_entries")  # 1小时缓存
def get_hot_entries():
    """获取热门图鉴条目
    ---
    tags:
      - entries
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
        description: 页码
      - in: query
        name: per_page
        type: integer
        default: 20
        maximum: 50
        description: 每页数量
    responses:
      200:
        description: 获取成功
        schema:
          $ref: '#/definitions/SuccessResponse'
      400:
        description: 请求错误
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    success, message, data = EntryService.get_entries_list(
        page=page,
        per_page=per_page,
        sort_by='view_count',
        sort_order='desc'
    )

    if success:
        return success_response(data=data, message="获取热门条目成功")
    else:
        return error_response(message, 400)

# 错误处理
@bp.errorhandler(429)
def ratelimit_handler(e):
    return error_response("请求过于频繁，请稍后再试", 429)
