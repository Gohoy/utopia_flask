from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.services.tag_service import TagService
from app.utils.helpers import success_response, error_response, validate_json
from app.utils.decorators import rate_limit
from app import limiter

bp = Blueprint('tags', __name__)

@bp.route('', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
@validate_json('name')
def create_tag():
    """
    创建标签
    ---
    tags:
      - Tags
    summary: 创建新标签
    description: 创建一个新的标签
    security:
      - JWT: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              description: 标签名称
              example: "可爱动物"
              maxLength: 100
            description:
              type: string
              description: 标签描述
              example: "用于标记可爱的动物图片"
              maxLength: 500
            category:
              type: string
              description: 标签分类
              example: "animal"
              maxLength: 50
            parent_id:
              type: string
              description: 父标签ID
              example: "animal_root"
            name_en:
              type: string
              description: 英文名称
              example: "Cute Animals"
              maxLength: 100
            aliases:
              type: array
              items:
                type: string
              description: 别名列表
              example: ["萌宠", "小动物"]
    responses:
      201:
        description: 创建成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "标签创建成功"
            data:
              type: object
              properties:
                tag:
                  $ref: '#/definitions/Tag'
      400:
        description: 请求参数错误或标签已存在
        schema:
          $ref: '#/definitions/ErrorResponse'
      401:
        description: 未授权或没有创建权限
        schema:
          $ref: '#/definitions/ErrorResponse'
      429:
        description: 请求过于频繁
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    """创建标签"""
    user_id = get_jwt_identity()
    data = request.get_json()

    success, message, tag = TagService.create_tag(
        user_id=user_id,
        name=data.get('name'),
        description=data.get('description'),
        category=data.get('category'),
        parent_id=data.get('parent_id'),
        name_en=data.get('name_en'),
        aliases=data.get('aliases', [])
    )

    if success:
        return success_response(
            data={'tag': tag},
            message=message,
            code=201
        )
    else:
        return error_response(message, 400)

@bp.route('/<tag_id>', methods=['GET'])
def get_tag(tag_id):
    """获取标签详情"""
    success, message, tag = TagService.get_tag_by_id(tag_id)

    if success:
        return success_response(
            data={'tag': tag},
            message=message
        )
    else:
        return error_response(message, 404 if "不存在" in message else 400)

@bp.route('/<tag_id>', methods=['PUT'])
@jwt_required()
@limiter.limit("20 per hour")
def update_tag(tag_id):
    """更新标签"""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return error_response("请求体不能为空", 400)

    success, message, tag = TagService.update_tag(tag_id, user_id, **data)

    if success:
        return success_response(
            data={'tag': tag},
            message=message
        )
    else:
        return error_response(message, 403 if "权限" in message else 400)

@bp.route('/<tag_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("5 per hour")
def delete_tag(tag_id):
    """删除标签"""
    user_id = get_jwt_identity()

    success, message, _ = TagService.delete_tag(tag_id, user_id)

    if success:
        return success_response(message=message)
    else:
        return error_response(message, 403 if "权限" in message else 400)

@bp.route('/search', methods=['GET'])
def search_tags():
    """
    搜索标签
    ---
    tags:
      - Tags
    summary: 搜索标签
    description: 根据关键词搜索标签
    parameters:
      - name: q
        in: query
        required: true
        type: string
        description: 搜索关键词
        example: "动物"
      - name: category
        in: query
        type: string
        description: 标签分类筛选
        example: "animal"
      - name: page
        in: query
        type: integer
        minimum: 1
        description: 页码
        example: 1
        default: 1
      - name: per_page
        in: query
        type: integer
        minimum: 1
        maximum: 100
        description: 每页数量
        example: 20
        default: 20
    responses:
      200:
        description: 搜索成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "搜索成功"
            data:
              type: object
              properties:
                tags:
                  type: array
                  items:
                    $ref: '#/definitions/Tag'
                pagination:
                  $ref: '#/definitions/Pagination'
                query:
                  type: string
                  example: "动物"
                category:
                  type: string
                  example: "animal"
      400:
        description: 搜索关键词不能为空
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    """搜索标签"""
    query = request.args.get('q', '').strip()
    if not query:
        return error_response("搜索关键词不能为空", 400)

    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    success, message, data = TagService.search_tags(query, category, page, per_page)

    if success:
        return success_response(data=data, message=message)
    else:
        return error_response(message, 400)

@bp.route('/popular', methods=['GET'])
def get_popular_tags():
    """获取热门标签"""
    category = request.args.get('category')
    limit = request.args.get('limit', 20, type=int)

    success, message, data = TagService.get_popular_tags(category, limit)

    if success:
        return success_response(data=data, message=message)
    else:
        return error_response(message, 400)

@bp.route('/recommend', methods=['POST'])
def get_recommended_tags():
    """获取推荐标签"""
    data = request.get_json()
    existing_tags = data.get('tags', []) if data else []
    limit = request.args.get('limit', 10, type=int)

    success, message, data = TagService.get_recommended_tags(existing_tags, limit)

    if success:
        return success_response(data=data, message=message)
    else:
        return error_response(message, 400)

@bp.route('/tree', methods=['GET'])
def get_tag_tree():
    """获取标签树"""
    root_id = request.args.get('root_id')

    success, message, data = TagService.get_tag_tree(root_id)

    if success:
        return success_response(data=data, message=message)
    else:
        return error_response(message, 400)

@bp.route('/<tag_id>/children', methods=['GET'])
def get_tag_children(tag_id):
    """获取子标签"""
    from app import neo4j_client

    if not neo4j_client or not neo4j_client.is_connected():
        return error_response("标签服务不可用", 503)

    try:
        children = neo4j_client.get_child_tags(tag_id, limit=50)
        return success_response(
            data={
                'parent_id': tag_id,
                'children': children,
                'count': len(children)
            },
            message="获取成功"
        )
    except Exception as e:
        return error_response("获取子标签失败", 500)

@bp.route('/<tag_id>/hierarchy', methods=['GET'])
def get_tag_hierarchy(tag_id):
    """获取标签层级路径"""
    from app import neo4j_client

    if not neo4j_client or not neo4j_client.is_connected():
        return error_response("标签服务不可用", 503)

    try:
        hierarchy = neo4j_client.get_tag_hierarchy(tag_id)
        return success_response(
            data={
                'tag_id': tag_id,
                'hierarchy': hierarchy
            },
            message="获取成功"
        )
    except Exception as e:
        return error_response("获取标签层级失败", 500)

@bp.route('/<tag_id>/stats', methods=['GET'])
def get_tag_stats(tag_id):
    """获取标签统计"""
    from app import neo4j_client
    from app.models.entry import EntryTag

    if not neo4j_client or not neo4j_client.is_connected():
        return error_response("标签服务不可用", 503)

    try:
        # 获取Neo4j中的统计
        neo4j_stats = neo4j_client.get_tag_stats(tag_id)
        if not neo4j_stats:
            return error_response("标签不存在", 404)

        # 获取PostgreSQL中的使用统计
        pg_usage_count = EntryTag.query.filter_by(tag_id=tag_id).count()

        stats = {
            'tag_info': neo4j_stats,
            'usage_in_entries': pg_usage_count,
            'total_usage': neo4j_stats.get('usage_count', 0)
        }

        return success_response(
            data={'stats': stats},
            message="获取成功"
        )
    except Exception as e:
        return error_response("获取标签统计失败", 500)

@bp.route('/validate', methods=['POST'])
@validate_json('tag_ids')
def validate_tags():
    """批量验证标签"""
    data = request.get_json()
    tag_ids = data.get('tag_ids', [])

    if not isinstance(tag_ids, list):
        return error_response("tag_ids必须是数组", 400)

    success, message, valid_tags = TagService.validate_tags(tag_ids)

    return success_response(
        data={
            'valid_tags': valid_tags,
            'validation_message': message,
            'all_valid': success
        },
        message="验证完成"
    )

@bp.route('/categories', methods=['GET'])
def get_tag_categories():
    """获取标签分类列表"""
    from app import neo4j_client

    if not neo4j_client or not neo4j_client.is_connected():
        return error_response("标签服务不可用", 503)

    try:
        with neo4j_client.driver.session() as session:
            result = session.run("""
                MATCH (t:Tag)
                WHERE t.status <> 'deleted'
                RETURN DISTINCT t.category as category, count(t) as count
                ORDER BY count DESC, category ASC
            """)

            categories = [
                {
                    'category': record['category'],
                    'count': record['count']
                }
                for record in result
            ]

            return success_response(
                data={'categories': categories},
                message="获取成功"
            )
    except Exception as e:
        return error_response("获取分类失败", 500)

# 错误处理
@bp.errorhandler(429)
def ratelimit_handler(e):
    return error_response("请求过于频繁，请稍后再试", 429)
