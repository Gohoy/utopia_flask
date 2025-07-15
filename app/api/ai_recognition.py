from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import tempfile

from app.services.ai_recognition_service import AIRecognitionService
from app.utils.helpers import success_response, error_response
from app.utils.decorators import rate_limit
from app import limiter

bp = Blueprint('ai_recognition', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/recognize', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def recognize_image():
    """
    图像识别接口
    ---
    tags:
      - AI Recognition
    summary: 识别图片内容
    description: 上传图片进行AI识别，返回识别结果和标签建议
    security:
      - JWT: []
    consumes:
      - multipart/form-data
    parameters:
      - name: image
        in: formData
        type: file
        required: true
        description: 要识别的图片文件
    responses:
      200:
        description: 识别成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "识别成功"
            data:
              type: object
              properties:
                recognition_result:
                  type: object
                  description: 识别结果
                suggested_tags:
                  type: array
                  items:
                    type: string
                  description: 建议的标签ID列表
      400:
        description: 请求错误
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
    try:
        user_id = get_jwt_identity()
        
        # 检查是否有上传的文件
        if 'image' not in request.files:
            return error_response("没有上传图片文件", 400)
        
        file = request.files['image']
        if file.filename == '':
            return error_response("没有选择文件", 400)
        
        # 检查文件类型
        if not allowed_file(file.filename):
            return error_response("不支持的文件类型", 400)
        
        # 检查文件大小 (限制为10MB)
        file_size = len(file.read())
        file.seek(0)  # 重置文件指针
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            return error_response("文件大小超过10MB限制", 400)
        
        # 读取文件数据
        image_data = file.read()
        
        # 调用识别服务
        success, message, recognition_result = AIRecognitionService.recognize_image(
            image_path=None,
            image_data=image_data
        )
        
        if not success:
            return error_response(message, 500)
        
        # 生成标签建议
        success, tag_message, suggested_tags = AIRecognitionService.generate_tags_from_recognition(
            recognition_result, user_id
        )
        
        return success_response(
            data={
                'recognition_result': recognition_result,
                'suggested_tags': suggested_tags,
                'tag_generation_message': tag_message
            },
            message=message
        )
        
    except Exception as e:
        return error_response(f"识别失败1: {str(e)}", 500)

@bp.route('/auto-tag/<entry_id>', methods=['POST'])
@jwt_required()
@limiter.limit("5 per minute")
def auto_tag_entry(entry_id):
    """
    自动为图鉴条目生成标签
    ---
    tags:
      - AI Recognition
    summary: 自动标记图鉴条目
    description: 对指定的图鉴条目进行AI识别并自动添加标签
    security:
      - JWT: []
    parameters:
      - name: entry_id
        in: path
        type: string
        required: true
        description: 条目ID
    responses:
      200:
        description: 自动标记成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "自动添加了3个标签"
            data:
              type: object
              properties:
                applied_tags:
                  type: array
                  items:
                    type: string
                  description: 已应用的标签ID列表
      400:
        description: 请求错误
        schema:
          $ref: '#/definitions/ErrorResponse'
      403:
        description: 无权限
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: 条目不存在
        schema:
          $ref: '#/definitions/ErrorResponse'
      429:
        description: 请求过于频繁
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    try:
        user_id = get_jwt_identity()
        
        success, message, applied_tags = AIRecognitionService.auto_tag_entry(
            entry_id, user_id
        )
        
        if success:
            return success_response(
                data={'applied_tags': applied_tags},
                message=message
            )
        else:
            status_code = 404 if "不存在" in message else (403 if "权限" in message else 400)
            return error_response(message, status_code)
            
    except Exception as e:
        return error_response(f"自动标记失败: {str(e)}", 500)

@bp.route('/generate-tags', methods=['POST'])
@jwt_required()
@limiter.limit("20 per minute")
def generate_tags_from_text():
    """
    从文本生成标签建议
    ---
    tags:
      - AI Recognition
    summary: 从文本生成标签
    description: 根据文本内容生成标签建议
    security:
      - JWT: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            text:
              type: string
              description: 文本内容
              example: "今天去了公园看到了美丽的樱花"
            title:
              type: string
              description: 标题
              example: "春日赏花"
    responses:
      200:
        description: 生成成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "生成了5个标签建议"
            data:
              type: object
              properties:
                suggested_tags:
                  type: array
                  items:
                    type: string
                  description: 建议的标签ID列表
      400:
        description: 请求错误
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('text'):
            return error_response("文本内容不能为空", 400)
        
        text = data.get('text', '')
        title = data.get('title', '')
        
        # 基于文本内容生成标签建议
        suggested_tags = []
        
        # 这里可以实现更复杂的NLP处理
        # 暂时使用简单的关键词匹配
        keywords = {
            '花': 'flower',
            '樱花': 'cherry_blossom',
            '公园': 'park',
            '美丽': 'beautiful',
            '春天': 'spring',
            '旅行': 'travel',
            '食物': 'food',
            '动物': 'animal',
            '风景': 'scenery',
            '建筑': 'architecture'
        }
        
        full_text = f"{title} {text}".lower()
        
        for keyword, category in keywords.items():
            if keyword in full_text:
                tag_id = AIRecognitionService._ensure_tag_exists(keyword, category, user_id)
                if tag_id:
                    suggested_tags.append(tag_id)
        
        return success_response(
            data={'suggested_tags': suggested_tags},
            message=f"生成了{len(suggested_tags)}个标签建议"
        )
        
    except Exception as e:
        return error_response(f"生成标签失败: {str(e)}", 500)

@bp.route('/providers', methods=['GET'])
@jwt_required()
def get_recognition_providers():
    """
    获取可用的识别服务提供商
    ---
    tags:
      - AI Recognition
    summary: 获取识别服务列表
    description: 获取当前可用的AI识别服务提供商信息
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
                providers:
                  type: array
                  items:
                    type: object
                    properties:
                      name:
                        type: string
                        example: "openai"
                      enabled:
                        type: boolean
                        example: true
                      confidence_threshold:
                        type: number
                        example: 0.7
    """
    try:
        service = AIRecognitionService()
        
        providers = []
        for name, config in service.recognition_providers.items():
            providers.append({
                'name': name,
                'enabled': config.get('enabled', False),
                'confidence_threshold': config.get('confidence_threshold', 0.5)
            })
        
        return success_response(
            data={'providers': providers},
            message="获取成功"
        )
        
    except Exception as e:
        return error_response(f"获取识别服务失败: {str(e)}", 500)

# 错误处理
@bp.errorhandler(413)
def too_large(e):
    return error_response("文件大小超过限制", 413)

@bp.route('/comprehensive', methods=['POST'])
@jwt_required()
@limiter.limit("5 per minute")
def comprehensive_recognition():
    """
    综合图像识别接口
    ---
    tags:
      - AI Recognition
    summary: 综合识别图片内容
    description: 使用增强的AI模型进行全面的图像识别，包括物体检测、图像描述、实体识别等
    security:
      - JWT: []
    consumes:
      - multipart/form-data
    parameters:
      - name: image
        in: formData
        type: file
        required: true
        description: 要识别的图片文件
    responses:
      200:
        description: 识别成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "识别成功"
            data:
              type: object
              properties:
                analysis:
                  type: object
                  properties:
                    objects:
                      type: array
                      items:
                        type: object
                    description:
                      type: string
                    entities:
                      type: array
                      items:
                        type: object
                    suggested_tags:
                      type: array
                      items:
                        type: string
                    dominant_colors:
                      type: array
                      items:
                        type: string
                    image_info:
                      type: object
      400:
        description: 请求错误
      401:
        description: 未授权
      429:
        description: 请求过于频繁
    """
    try:
        # 检查是否有上传的文件
        if 'image' not in request.files:
            return error_response('请上传图片文件', 400)
        
        file = request.files['image']
        
        if file.filename == '':
            return error_response('请选择图片文件', 400)
        
        if not allowed_file(file.filename):
            return error_response('不支持的文件格式', 400)
        
        # 读取图片数据
        image_data = file.read()
        
        # 调用AI识别服务
        success, message, recognition_result = AIRecognitionService.recognize_image(
            image_path=None,
            image_data=image_data
        )
        
        if not success:
            return error_response(message, 400)
        
        # 获取当前用户ID
        current_user_id = get_jwt_identity()
        
        # 生成标签建议
        tag_success, tag_message, suggested_tag_ids = AIRecognitionService.generate_tags_from_recognition(
            recognition_result, current_user_id
        )
        
        # 添加标签信息到结果中
        if tag_success:
            recognition_result['suggested_tag_ids'] = suggested_tag_ids
        
        return success_response(
            "综合识别成功",
            {
                "recognition_result": recognition_result,
                "tag_suggestions": {
                    "success": tag_success,
                    "message": tag_message,
                    "tag_ids": suggested_tag_ids if tag_success else []
                }
            }
        )
        
    except Exception as e:
        logger.error(f"综合识别失败: {e}")
        return error_response("综合识别失败", 500)

@bp.route('/model-status', methods=['GET'])
@jwt_required()
@limiter.limit("10 per minute")
def get_model_status():
    """
    获取AI模型状态
    ---
    tags:
      - AI Recognition
    summary: 获取AI模型加载状态
    description: 查看AI识别模型的当前状态
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
                models_loaded:
                  type: boolean
                yolo_loaded:
                  type: boolean
                blip_loaded:
                  type: boolean
                knowledge_base_size:
                  type: integer
    """
    try:
        service = AIRecognitionService()
        
        if hasattr(service, 'ai_engine'):
            model_status = service.ai_engine.get_model_status()
        else:
            model_status = {
                "models_loaded": False,
                "yolo_loaded": False,
                "blip_loaded": False,
                "knowledge_base_size": 0
            }
        
        return success_response("获取模型状态成功", model_status)
        
    except Exception as e:
        logger.error(f"获取模型状态失败: {e}")
        return error_response("获取模型状态失败", 500)

@bp.errorhandler(429)
def ratelimit_handler(e):
    return error_response("请求过于频繁，请稍后再试", 429) 