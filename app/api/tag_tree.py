from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
import logging

from app.services.tag_tree_service import TagTreeService
from app.utils.helpers import success_response, error_response, validate_json
from app.utils.decorators import rate_limit
from app import limiter

logger = logging.getLogger(__name__)
bp = Blueprint('tag_tree', __name__)

@bp.route('/tree', methods=['GET'])
@jwt_required()
@rate_limit("100 per hour")
def get_tag_tree():
    """获取标签树
    ---
    tags:
      - tag_tree
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: root_id
        type: string
        description: 根标签ID，不提供则返回所有根标签
      - in: query
        name: max_depth
        type: integer
        default: 3
        description: 最大深度
      - in: query
        name: include_stats
        type: boolean
        default: false
        description: 是否包含统计信息
    responses:
      200:
        description: 标签树获取成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                  name:
                    type: string
                  path:
                    type: string
                  children:
                    type: array
                    items:
                      type: object
      400:
        description: 请求错误
    """
    try:
        root_id = request.args.get('root_id')
        max_depth = int(request.args.get('max_depth', 3))
        include_stats = request.args.get('include_stats', 'false').lower() == 'true'
        
        tree_data = TagTreeService.get_tag_tree(root_id, max_depth, include_stats)
        
        return success_response(tree_data, "标签树获取成功")
        
    except Exception as e:
        logger.error(f"获取标签树失败: {e}")
        return error_response("获取标签树失败")

@bp.route('/search', methods=['GET'])
@jwt_required()
@rate_limit("200 per hour")
def search_tags():
    """搜索标签
    ---
    tags:
      - tag_tree
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: keyword
        type: string
        required: true
        description: 搜索关键词
      - in: query
        name: category
        type: string
        description: 分类筛选
      - in: query
        name: domain
        type: string
        description: 域筛选
      - in: query
        name: limit
        type: integer
        default: 20
        description: 结果限制
    responses:
      200:
        description: 搜索成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                  name:
                    type: string
                  path:
                    type: string
                  usage_count:
                    type: integer
      400:
        description: 请求错误
    """
    try:
        keyword = request.args.get('keyword', '').strip()
        if not keyword:
            return error_response("搜索关键词不能为空")
        
        category = request.args.get('category')
        domain = request.args.get('domain')
        limit = int(request.args.get('limit', 20))
        
        results = TagTreeService.search_tags(keyword, category, domain, limit)
        
        return success_response(results, f"找到 {len(results)} 个标签")
        
    except Exception as e:
        logger.error(f"搜索标签失败: {e}")
        return error_response("搜索标签失败")

@bp.route('/suggestions', methods=['GET'])
@jwt_required()
@rate_limit("300 per hour")
def get_tag_suggestions():
    """获取标签建议
    ---
    tags:
      - tag_tree
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: partial_name
        type: string
        required: true
        description: 部分标签名称
      - in: query
        name: limit
        type: integer
        default: 10
        description: 结果限制
    responses:
      200:
        description: 获取建议成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                  name:
                    type: string
                  path:
                    type: string
    """
    try:
        partial_name = request.args.get('partial_name', '').strip()
        if not partial_name:
            return error_response("部分名称不能为空")
        
        limit = int(request.args.get('limit', 10))
        
        suggestions = TagTreeService.get_tag_suggestions(partial_name, limit)
        
        return success_response(suggestions, f"找到 {len(suggestions)} 个建议")
        
    except Exception as e:
        logger.error(f"获取标签建议失败: {e}")
        return error_response("获取标签建议失败")

@bp.route('', methods=['POST'])
@jwt_required()
@rate_limit("50 per hour")
@validate_json('name')
def create_tag():
    """创建标签
    ---
    tags:
      - tag_tree
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              description: 标签名称
              example: "新标签"
            parent_id:
              type: string
              description: 父标签ID
              example: "parent-tag-id"
            description:
              type: string
              description: 标签描述
              example: "这是一个新的标签"
            name_en:
              type: string
              description: 英文名称
              example: "New Tag"
            category:
              type: string
              description: 分类
              example: "general"
            domain:
              type: string
              description: 域
              example: "general"
            is_abstract:
              type: boolean
              description: 是否为抽象概念
              example: false
            aliases:
              type: array
              items:
                type: string
              description: 别名列表
              example: ["别名1", "别名2"]
            properties:
              type: object
              description: 自定义属性
              example: {"key": "value"}
    responses:
      201:
        description: 标签创建成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                id:
                  type: string
                name:
                  type: string
                path:
                  type: string
            message:
              type: string
              example: "标签创建成功"
      400:
        description: 请求错误
    """
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # 提取参数
        name = data.get('name', '').strip()
        parent_id = data.get('parent_id')
        description = data.get('description', '')
        name_en = data.get('name_en', '')
        category = data.get('category', 'general')
        domain = data.get('domain', 'general')
        is_abstract = data.get('is_abstract', False)
        aliases = data.get('aliases', [])
        properties = data.get('properties', {})
        
        # 创建标签
        success, message, tag = TagTreeService.create_tag(
            name=name,
            user_id=user_id,
            parent_id=parent_id,
            description=description,
            name_en=name_en,
            category=category,
            domain=domain,
            is_abstract=is_abstract,
            aliases=aliases,
            properties=properties
        )
        
        if success:
            return success_response(tag.to_dict(), message), 201
        else:
            return error_response(message), 400
            
    except Exception as e:
        logger.error(f"创建标签失败: {e}")
        return error_response("创建标签失败")

@bp.route('/<tag_id>', methods=['GET'])
@jwt_required()
@rate_limit("200 per hour")
def get_tag_details(tag_id):
    """获取标签详情
    ---
    tags:
      - tag_tree
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: tag_id
        type: string
        required: true
        description: 标签ID
    responses:
      200:
        description: 获取成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                id:
                  type: string
                name:
                  type: string
                path:
                  type: string
                children:
                  type: array
                parent:
                  type: object
      404:
        description: 标签不存在
    """
    try:
        tag = TagTreeService.get_tag_by_id(tag_id)
        if not tag:
            return error_response("标签不存在", 404)
        
        tag_data = tag.to_dict(include_children=True, include_parent=True)
        
        return success_response(tag_data, "获取标签详情成功")
        
    except Exception as e:
        logger.error(f"获取标签详情失败: {e}")
        return error_response("获取标签详情失败")

@bp.route('/<tag_id>/move', methods=['POST'])
@jwt_required()
@rate_limit("30 per hour")
def move_tag(tag_id):
    """移动标签
    ---
    tags:
      - tag_tree
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: tag_id
        type: string
        required: true
        description: 要移动的标签ID
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            new_parent_id:
              type: string
              description: 新父标签ID，null表示移动到根节点
              example: "new-parent-id"
    responses:
      200:
        description: 移动成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "标签移动成功"
      400:
        description: 请求错误
    """
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        new_parent_id = data.get('new_parent_id')
        
        success, message = TagTreeService.move_tag(tag_id, new_parent_id, user_id)
        
        if success:
            return success_response(None, message)
        else:
            return error_response(message), 400
            
    except Exception as e:
        logger.error(f"移动标签失败: {e}")
        return error_response("移动标签失败")

@bp.route('/<source_tag_id>/merge', methods=['POST'])
@jwt_required()
@rate_limit("20 per hour")
def merge_tags(source_tag_id):
    """合并标签
    ---
    tags:
      - tag_tree
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: source_tag_id
        type: string
        required: true
        description: 源标签ID（将被合并的标签）
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            target_tag_id:
              type: string
              required: true
              description: 目标标签ID（保留的标签）
              example: "target-tag-id"
    responses:
      200:
        description: 合并成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "标签合并成功"
      400:
        description: 请求错误
    """
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        target_tag_id = data.get('target_tag_id')
        if not target_tag_id:
            return error_response("目标标签ID不能为空"), 400
        
        success, message = TagTreeService.merge_tags(source_tag_id, target_tag_id, user_id)
        
        if success:
            return success_response(None, message)
        else:
            return error_response(message), 400
            
    except Exception as e:
        logger.error(f"合并标签失败: {e}")
        return error_response("合并标签失败")

@bp.route('/<tag_id>/history', methods=['GET'])
@jwt_required()
@rate_limit("100 per hour")
def get_tag_history(tag_id):
    """获取标签历史记录
    ---
    tags:
      - tag_tree
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: tag_id
        type: string
        required: true
        description: 标签ID
      - in: query
        name: limit
        type: integer
        default: 50
        description: 结果限制
    responses:
      200:
        description: 获取成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                  action:
                    type: string
                  action_description:
                    type: string
                  created_at:
                    type: string
                  user_id:
                    type: string
    """
    try:
        limit = int(request.args.get('limit', 50))
        
        history = TagTreeService.get_tag_history(tag_id, limit)
        
        return success_response(history, f"获取到 {len(history)} 条历史记录")
        
    except Exception as e:
        logger.error(f"获取标签历史失败: {e}")
        return error_response("获取标签历史失败")

@bp.route('/popular', methods=['GET'])
@jwt_required()
@rate_limit("100 per hour")
def get_popular_tags():
    """获取热门标签
    ---
    tags:
      - tag_tree
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: limit
        type: integer
        default: 20
        description: 结果限制
    responses:
      200:
        description: 获取成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                  name:
                    type: string
                  usage_count:
                    type: integer
                  popularity_score:
                    type: number
    """
    try:
        limit = int(request.args.get('limit', 20))
        
        popular_tags = TagTreeService.get_popular_tags(limit)
        
        return success_response(popular_tags, f"获取到 {len(popular_tags)} 个热门标签")
        
    except Exception as e:
        logger.error(f"获取热门标签失败: {e}")
        return error_response("获取热门标签失败")

@bp.route('/categories', methods=['GET'])
@jwt_required()
@rate_limit("100 per hour")
def get_categories():
    """获取所有分类
    ---
    tags:
      - tag_tree
    security:
      - BearerAuth: []
    responses:
      200:
        description: 获取成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: array
              items:
                type: object
                properties:
                  category:
                    type: string
                  count:
                    type: integer
    """
    try:
        categories = TagTreeService.get_categories()
        
        return success_response(categories, f"获取到 {len(categories)} 个分类")
        
    except Exception as e:
        logger.error(f"获取分类失败: {e}")
        return error_response("获取分类失败")

@bp.route('/auto-place', methods=['POST'])
@jwt_required()
@rate_limit("50 per hour")
@validate_json('tag_name')
def auto_place_tag():
    """自动放置标签
    ---
    tags:
      - tag_tree
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            tag_name:
              type: string
              required: true
              description: 标签名称
              example: "苹果"
            description:
              type: string
              description: 描述
              example: "一种红色的水果"
            ai_context:
              type: object
              description: AI识别上下文
              properties:
                objects:
                  type: array
                  items:
                    type: object
                colors:
                  type: array
                  items:
                    type: string
                scene:
                  type: string
    responses:
      200:
        description: 自动放置成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                suggested_parent_id:
                  type: string
                suggested_parent_name:
                  type: string
            message:
              type: string
              example: "找到合适的父标签"
      400:
        description: 请求错误
    """
    try:
        data = request.get_json()
        
        tag_name = data.get('tag_name', '').strip()
        description = data.get('description', '')
        ai_context = data.get('ai_context', {})
        
        suggested_parent_id = TagTreeService.auto_place_tag(tag_name, description, ai_context)
        
        if suggested_parent_id:
            parent_tag = TagTreeService.get_tag_by_id(suggested_parent_id)
            result = {
                'suggested_parent_id': suggested_parent_id,
                'suggested_parent_name': parent_tag.name if parent_tag else None,
                'suggested_parent_path': parent_tag.get_full_path() if parent_tag else None
            }
            return success_response(result, "找到合适的父标签")
        else:
            return success_response(None, "未找到合适的父标签，可以创建为根标签")
            
    except Exception as e:
        logger.error(f"自动放置标签失败: {e}")
        return error_response("自动放置标签失败") 