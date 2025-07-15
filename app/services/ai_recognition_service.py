import logging
import io
import base64
from typing import Dict, List, Optional, Tuple
from PIL import Image
import requests
import json
from datetime import datetime
import tempfile
import os

from app import neo4j_client
from app.models.entry import Entry
from app.services.tag_service import TagService
from app.services.ai_recognition_engine import AIRecognitionEngine

logger = logging.getLogger(__name__)

class AIRecognitionService:
    """AI图像识别服务"""
    
    def __init__(self):
        self.enabled = True
        # 初始化AI识别引擎
        self.ai_engine = AIRecognitionEngine()
        # 这里可以配置多个AI服务，比如百度、阿里云、Google Vision等
        self.recognition_providers = {
            'enhanced': {
                'enabled': True,
                'confidence_threshold': 0.6
            },
            'openai': {
                'enabled': True,
                'confidence_threshold': 0.7
            },
            'local': {
                'enabled': True,
                'confidence_threshold': 0.6
            }
        }
    
    @classmethod
    def recognize_image(cls, image_path: str, image_data: bytes = None) -> Tuple[bool, str, Dict]:
        """
        识别图片内容
        
        Args:
            image_path: 图片路径
            image_data: 图片二进制数据
            
        Returns:
            tuple: (success, message, recognition_result)
        """
        try:
            service = cls()
            
            # 检查AI引擎是否可用
            if not service.ai_engine.is_models_loaded():
                # 如果AI引擎不可用，使用原有的识别方法
                return service._fallback_recognition(image_path, image_data)
            
            # 准备图片路径
            temp_file = None
            try:
                # 如果有图片数据但没有路径，创建临时文件
                if image_data is not None and (not image_path or not os.path.exists(image_path)):
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                    temp_file.write(image_data)
                    temp_file.close()
                    image_path = temp_file.name
                
                # 如果没有图片数据，尝试从路径读取
                if image_data is None:
                    try:
                        with open(image_path, 'rb') as f:
                            image_data = f.read()
                    except Exception as e:
                        logger.error(f"读取图片失败: {e}")
                        return False, "读取图片失败", {}
                
                # 验证图片格式
                try:
                    image = Image.open(io.BytesIO(image_data))
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                except Exception as e:
                    logger.error(f"图片格式验证失败: {e}")
                    return False, "图片格式不支持", {}
                
                # 使用新的AI引擎进行综合分析
                recognition_result = service.ai_engine.analyze_image_comprehensive(image_path)
                
                if not recognition_result.get('success', False):
                    # 如果新引擎失败，尝试原有的识别方法
                    return service._fallback_recognition(image_path, image_data)
                
                return True, "识别成功", recognition_result
                
            finally:
                # 清理临时文件
                if temp_file and os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
            
        except Exception as e:
            logger.error(f"图像识别异常: {e}")
            return False, "图像识别服务异常", {}
    
    def _fallback_recognition(self, image_path: str, image_data: bytes) -> Tuple[bool, str, Dict]:
        """备用识别方法"""
        try:
            # 调用原有的识别服务
            recognition_result = self._recognize_with_openai(image_data)
            
            if not recognition_result:
                # 尝试本地识别
                recognition_result = self._recognize_with_local(image_data)
            
            if not recognition_result:
                return False, "图像识别失败", {}
            
            return True, "识别成功", recognition_result
            
        except Exception as e:
            logger.error(f"备用识别失败: {e}")
            return False, "备用识别失败", {}
    
    @classmethod
    def _extract_keywords_from_description(cls, description: str) -> List[str]:
        """从描述中提取关键词"""
        try:
            # 简单的关键词提取
            keywords = []
            
            # 定义一些常见的关键词
            common_keywords = [
                'cat', 'dog', 'bird', 'flower', 'tree', 'car', 'house', 'person',
                'animal', 'plant', 'building', 'water', 'sky', 'grass', 'food',
                'beautiful', 'colorful', 'bright', 'dark', 'large', 'small',
                '猫', '狗', '鸟', '花', '树', '车', '房子', '人', '动物', '植物',
                '建筑', '水', '天空', '草', '食物', '美丽', '彩色', '明亮', '黑暗',
                '大', '小', '红色', '蓝色', '绿色', '黄色', '白色', '黑色'
            ]
            
            description_lower = description.lower()
            
            for keyword in common_keywords:
                if keyword.lower() in description_lower:
                    keywords.append(keyword)
            
            return keywords[:10]  # 最多返回10个关键词
            
        except Exception as e:
            logger.error(f"关键词提取失败: {e}")
            return []
    
    def _recognize_with_openai(self, image_data: bytes) -> Optional[Dict]:
        """使用OpenAI Vision API进行图像识别"""
        try:
            # 将图片转换为base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # 模拟OpenAI API调用（需要实际API密钥时替换）
            # 这里使用模拟数据
            mock_response = {
                "objects": [
                    {"name": "花", "confidence": 0.95, "category": "plant"},
                    {"name": "玫瑰", "confidence": 0.89, "category": "flower"},
                    {"name": "红色", "confidence": 0.85, "category": "color"},
                    {"name": "自然", "confidence": 0.92, "category": "scene"}
                ],
                "scene": {
                    "description": "一朵美丽的红玫瑰",
                    "location": "室外",
                    "time_of_day": "白天"
                },
                "colors": ["红色", "绿色", "白色"],
                "emotions": ["美丽", "浪漫", "自然"]
            }
            
            return mock_response
            
        except Exception as e:
            logger.error(f"OpenAI识别失败: {e}")
            return None
    
    def _recognize_with_local(self, image_data: bytes) -> Optional[Dict]:
        """使用本地模型进行图像识别"""
        try:
            # 这里可以集成本地AI模型，比如使用深度学习框架
            # 暂时返回基础分类
            
            # 分析图片基本信息
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            
            # 简单的颜色分析
            colors = self._analyze_dominant_colors(image)
            
            result = {
                "objects": [
                    {"name": "物体", "confidence": 0.6, "category": "unknown"}
                ],
                "scene": {
                    "description": "图片内容",
                    "dimensions": f"{width}x{height}"
                },
                "colors": colors,
                "technical": {
                    "width": width,
                    "height": height,
                    "format": image.format
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"本地识别失败: {e}")
            return None
    
    def _analyze_dominant_colors(self, image: Image.Image) -> List[str]:
        """分析图片主要颜色"""
        try:
            # 缩小图片以提高处理速度
            image = image.resize((100, 100))
            
            # 获取颜色直方图
            colors = image.getcolors(maxcolors=256*256*256)
            if not colors:
                return ["未知"]
            
            # 排序获取主要颜色
            colors.sort(key=lambda x: x[0], reverse=True)
            
            # 简单的颜色映射
            color_map = {
                (255, 0, 0): "红色",
                (0, 255, 0): "绿色", 
                (0, 0, 255): "蓝色",
                (255, 255, 0): "黄色",
                (255, 0, 255): "紫色",
                (0, 255, 255): "青色",
                (255, 255, 255): "白色",
                (0, 0, 0): "黑色"
            }
            
            result_colors = []
            for count, color in colors[:5]:  # 取前5个颜色
                if isinstance(color, tuple) and len(color) == 3:
                    # 找到最近的颜色
                    min_distance = float('inf')
                    closest_color = "未知"
                    
                    for ref_color, color_name in color_map.items():
                        distance = sum((c1 - c2) ** 2 for c1, c2 in zip(color, ref_color))
                        if distance < min_distance:
                            min_distance = distance
                            closest_color = color_name
                    
                    if closest_color not in result_colors:
                        result_colors.append(closest_color)
            
            return result_colors[:3]  # 返回最多3个颜色
            
        except Exception as e:
            logger.error(f"颜色分析失败: {e}")
            return ["未知"]
    
    @classmethod
    def generate_tags_from_recognition(cls, recognition_result: Dict, user_id: str) -> Tuple[bool, str, List[str]]:
        """
        根据识别结果生成标签建议
        
        Args:
            recognition_result: 识别结果
            user_id: 用户ID
            
        Returns:
            tuple: (success, message, suggested_tags)
        """
        try:
            suggested_tags = []
            
            # 获取分析结果
            analysis = recognition_result.get('analysis', recognition_result)
            
            # 从建议的标签直接添加
            if 'suggested_tags' in analysis:
                for tag_name in analysis['suggested_tags']:
                    tag_id = cls._ensure_tag_exists(tag_name, 'ai_generated', user_id)
                    if tag_id:
                        suggested_tags.append(tag_id)
            
            # 从识别的物体生成标签
            if 'objects' in analysis:
                for obj in analysis['objects']:
                    if obj.get('confidence', 0) > 0.5:  # 降低阈值以包含更多标签
                        tag_name = obj.get('class', obj.get('name', ''))
                        category = 'object'
                        
                        # 检查标签是否存在，不存在则创建
                        tag_id = cls._ensure_tag_exists(tag_name, category, user_id)
                        if tag_id:
                            suggested_tags.append(tag_id)
            
            # 从实体生成标签
            if 'entities' in analysis:
                for entity in analysis['entities']:
                    entity_name = entity.get('entity', '')
                    if entity_name:
                        category = entity.get('category', 'entity')
                        tag_id = cls._ensure_tag_exists(entity_name, category, user_id)
                        if tag_id:
                            suggested_tags.append(tag_id)
            
            # 从颜色生成标签
            if 'dominant_colors' in analysis:
                for color in analysis['dominant_colors']:
                    tag_id = cls._ensure_tag_exists(f"颜色_{color}", 'color', user_id)
                    if tag_id:
                        suggested_tags.append(tag_id)
            
            # 从描述中提取关键词作为标签
            if 'description' in analysis:
                description = analysis['description']
                # 简单的关键词提取
                keywords = cls._extract_keywords_from_description(description)
                for keyword in keywords:
                    tag_id = cls._ensure_tag_exists(keyword, 'description', user_id)
                    if tag_id:
                        suggested_tags.append(tag_id)
            
            # 兼容旧格式
            # 从颜色生成标签
            if 'colors' in recognition_result:
                for color in recognition_result['colors']:
                    tag_id = cls._ensure_tag_exists(color, 'color', user_id)
                    if tag_id:
                        suggested_tags.append(tag_id)
            
            # 从情感生成标签
            if 'emotions' in recognition_result:
                for emotion in recognition_result['emotions']:
                    tag_id = cls._ensure_tag_exists(emotion, 'emotion', user_id)
                    if tag_id:
                        suggested_tags.append(tag_id)
            
            # 从场景生成标签
            if 'scene' in recognition_result:
                scene = recognition_result['scene']
                if 'location' in scene:
                    tag_id = cls._ensure_tag_exists(scene['location'], 'location', user_id)
                    if tag_id:
                        suggested_tags.append(tag_id)
            
            # 去重
            suggested_tags = list(set(suggested_tags))
            
            return True, f"生成了{len(suggested_tags)}个标签建议", suggested_tags
            
        except Exception as e:
            logger.error(f"生成标签建议失败: {e}")
            return False, "生成标签建议失败", []
    
    @classmethod
    def _ensure_tag_exists(cls, tag_name: str, category: str, user_id: str) -> Optional[str]:
        """确保标签存在，如果不存在则创建"""
        try:
            if not neo4j_client or not neo4j_client.is_connected():
                return None
            
            # 搜索现有标签
            existing_tags = neo4j_client.search_tags(tag_name, category, limit=1)
            if existing_tags:
                for tag in existing_tags:
                    if tag['name'] == tag_name:
                        return tag['id']
            
            # 创建新标签
            success, message, tag = TagService.create_tag(
                user_id=user_id,
                name=tag_name,
                description=f"AI识别生成的{category}标签",
                category=category
            )
            
            if success and tag:
                return tag['id']
            
            return None
            
        except Exception as e:
            logger.error(f"确保标签存在失败: {e}")
            return None
    
    @classmethod
    def auto_tag_entry(cls, entry_id: str, user_id: str) -> Tuple[bool, str, List[str]]:
        """
        自动为图鉴条目生成标签
        
        Args:
            entry_id: 条目ID
            user_id: 用户ID
            
        Returns:
            tuple: (success, message, applied_tags)
        """
        try:
            # 获取条目
            entry = Entry.query.get(entry_id)
            if not entry:
                return False, "条目不存在", []
            
            # 检查权限
            if entry.user_id != user_id:
                return False, "无权限操作", []
            
            # 获取条目的图片
            image_files = entry.media_files.filter_by(file_type='image').all()
            if not image_files:
                return False, "条目没有图片", []
            
            all_suggested_tags = []
            
            # 对每张图片进行识别
            for media_file in image_files:
                success, message, recognition_result = cls.recognize_image(media_file.file_path)
                
                if success:
                    success, message, tags = cls.generate_tags_from_recognition(recognition_result, user_id)
                    if success:
                        all_suggested_tags.extend(tags)
            
            # 去重
            all_suggested_tags = list(set(all_suggested_tags))
            
            # 应用标签到条目
            from app.services.entry_service import EntryService
            
            # 获取现有标签
            existing_tags = entry.get_tags()
            
            # 合并新标签
            final_tags = list(set(existing_tags + all_suggested_tags))
            
            # 更新条目标签
            success, message, updated_entry = EntryService.update_entry(
                entry_id, user_id, tags=final_tags
            )
            
            if success:
                return True, f"自动添加了{len(all_suggested_tags)}个标签", all_suggested_tags
            else:
                return False, "应用标签失败", []
            
        except Exception as e:
            logger.error(f"自动标记条目失败: {e}")
            return False, "自动标记失败", [] 