import torch
from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
import wikipedia
import requests
from transformers import BlipProcessor, BlipForConditionalGeneration
import json
import logging
from typing import Dict, List, Tuple, Optional
import os
import tempfile
from datetime import datetime
import traceback
import re
import io
import base64

logger = logging.getLogger(__name__)

class AIRecognitionEngine:
    """AI识别引擎 - 集成YOLO、BLIP等多种AI模型"""
    
    def __init__(self):
        """初始化AI识别引擎"""
        self.setup_logging()
        self.models_loaded = False
        self.yolo_model = None
        self.blip_processor = None
        self.blip_model = None
        self.knowledge_base = {}
        self.load_models()
        self.setup_knowledge_base()
        
    def setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger(__name__)
        
    def load_models(self):
        """加载预训练模型"""
        try:
            self.logger.info("正在加载AI识别模型...")
            
            # 1. 加载YOLO目标检测模型
            self.logger.info("加载YOLO模型...")
            self.yolo_model = YOLO('yolov8n.pt')
            self.logger.info("✅ YOLO模型加载成功")
            
            # 2. 加载BLIP图像描述模型
            self.logger.info("加载BLIP模型...")
            self.blip_processor = BlipProcessor.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
            self.blip_model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
            self.logger.info("✅ BLIP模型加载成功")
            
            self.models_loaded = True
            self.logger.info("✅ 所有AI模型加载完成")
            
        except Exception as e:
            self.logger.error(f"模型加载失败: {e}")
            self.models_loaded = False
            
    def setup_knowledge_base(self):
        """设置知识库"""
        try:
            # 基础知识库
            self.knowledge_base = {
                "动物": {
                    "猫": {"标签": ["宠物", "动物", "猫科"], "描述": "家养宠物猫"},
                    "狗": {"标签": ["宠物", "动物", "犬科"], "描述": "家养宠物狗"},
                    "鸟": {"标签": ["动物", "鸟类", "飞行"], "描述": "各种鸟类"},
                },
                "植物": {
                    "花": {"标签": ["植物", "花卉", "自然"], "描述": "各种花卉"},
                    "树": {"标签": ["植物", "树木", "自然"], "描述": "各种树木"},
                },
                "物体": {
                    "车": {"标签": ["交通工具", "汽车", "车辆"], "描述": "各种车辆"},
                    "建筑": {"标签": ["建筑", "房屋", "建筑物"], "描述": "各种建筑"},
                },
                "食物": {
                    "水果": {"标签": ["食物", "水果", "健康"], "描述": "各种水果"},
                    "蔬菜": {"标签": ["食物", "蔬菜", "健康"], "描述": "各种蔬菜"},
                }
            }
            
            self.logger.info("✅ 知识库设置完成")
            
        except Exception as e:
            self.logger.error(f"知识库设置失败: {e}")
            
    def detect_objects(self, image_path: str) -> List[Dict]:
        """使用YOLO检测图像中的物体"""
        try:
            if not self.models_loaded or not self.yolo_model:
                return []
                
            # 使用YOLO进行物体检测
            results = self.yolo_model(image_path)
            
            objects = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # 获取类别名称
                        class_id = int(box.cls[0])
                        class_name = self.yolo_model.names[class_id]
                        confidence = float(box.conf[0])
                        
                        # 获取边界框坐标
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        
                        objects.append({
                            "class": class_name,
                            "confidence": confidence,
                            "bbox": [x1, y1, x2, y2],
                            "area": (x2 - x1) * (y2 - y1)
                        })
                        
            # 按置信度排序
            objects.sort(key=lambda x: x["confidence"], reverse=True)
            
            self.logger.info(f"检测到 {len(objects)} 个物体")
            return objects
            
        except Exception as e:
            self.logger.error(f"物体检测失败: {e}")
            return []
            
    def generate_image_caption(self, image_path: str) -> str:
        """使用BLIP生成图像描述"""
        try:
            if not self.models_loaded or not self.blip_model:
                return "模型未加载"
                
            # 加载图像
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
                
            # 生成描述
            inputs = self.blip_processor(image, return_tensors="pt")
            
            with torch.no_grad():
                out = self.blip_model.generate(
                    pixel_values=inputs.pixel_values,
                    max_length=50,
                    num_beams=4,
                    early_stopping=True
                )
                
            caption = self.blip_processor.decode(out[0], skip_special_tokens=True)
            
            self.logger.info(f"生成图像描述: {caption}")
            return caption
            
        except Exception as e:
            self.logger.error(f"图像描述生成失败: {e}")
            return "描述生成失败"
            
    def get_wikipedia_info(self, entity: str, language='zh') -> Optional[Dict]:
        """获取维基百科信息"""
        try:
            wikipedia.set_lang(language)
            
            # 搜索相关页面
            search_results = wikipedia.search(entity, results=3)
            
            if not search_results:
                return None
                
            # 获取第一个结果的详细信息
            page = wikipedia.page(search_results[0])
            
            # 获取摘要（限制长度）
            summary = wikipedia.summary(entity, sentences=2)
            
            return {
                "title": page.title,
                "summary": summary,
                "url": page.url,
                "categories": getattr(page, 'categories', [])[:10]  # 限制类别数量
            }
            
        except Exception as e:
            self.logger.error(f"维基百科查询失败: {e}")
            return None
            
    def extract_entities_from_description(self, description: str) -> Tuple[List[Dict], List[str]]:
        """从描述中提取实体和标签"""
        try:
            entities = []
            suggested_tags = []
            
            # 简单的实体提取（基于关键词匹配）
            for category, items in self.knowledge_base.items():
                for item, info in items.items():
                    if item.lower() in description.lower():
                        entities.append({
                            "entity": item,
                            "category": category,
                            "confidence": 0.8,
                            "description": info["描述"]
                        })
                        suggested_tags.extend(info["标签"])
                        
            # 去重标签
            suggested_tags = list(set(suggested_tags))
            
            self.logger.info(f"提取到 {len(entities)} 个实体，{len(suggested_tags)} 个标签")
            return entities, suggested_tags
            
        except Exception as e:
            self.logger.error(f"实体提取失败: {e}")
            return [], []
            
    def analyze_image_comprehensive(self, image_path: str) -> Dict:
        """综合分析图像"""
        try:
            result = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "analysis": {
                    "objects": [],
                    "description": "",
                    "entities": [],
                    "suggested_tags": [],
                    "dominant_colors": [],
                    "image_info": {}
                }
            }
            
            # 1. 物体检测
            objects = self.detect_objects(image_path)
            result["analysis"]["objects"] = objects
            
            # 2. 图像描述生成
            description = self.generate_image_caption(image_path)
            result["analysis"]["description"] = description
            
            # 3. 从描述中提取实体
            entities, suggested_tags = self.extract_entities_from_description(description)
            result["analysis"]["entities"] = entities
            result["analysis"]["suggested_tags"] = suggested_tags
            
            # 4. 从检测到的物体中添加标签
            for obj in objects:
                if obj["confidence"] > 0.5:
                    suggested_tags.append(obj["class"])
                    
            # 5. 获取图像基本信息
            image = Image.open(image_path)
            result["analysis"]["image_info"] = {
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
                "format": image.format
            }
            
            # 6. 分析主要颜色
            dominant_colors = self._analyze_dominant_colors(image)
            result["analysis"]["dominant_colors"] = dominant_colors
            
            # 去重标签
            result["analysis"]["suggested_tags"] = list(set(suggested_tags))
            
            self.logger.info("图像综合分析完成")
            return result
            
        except Exception as e:
            self.logger.error(f"图像分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    def _analyze_dominant_colors(self, image: Image.Image, num_colors: int = 5) -> List[str]:
        """分析图像主要颜色"""
        try:
            # 调整图像大小以提高处理速度
            image = image.resize((150, 150))
            
            # 转换为numpy数组
            image_array = np.array(image)
            
            # 重塑数组
            pixels = image_array.reshape(-1, 3)
            
            # 使用K-means聚类找到主要颜色
            from sklearn.cluster import KMeans
            
            kmeans = KMeans(n_clusters=num_colors, random_state=42)
            kmeans.fit(pixels)
            
            # 获取聚类中心（主要颜色）
            colors = kmeans.cluster_centers_
            
            # 转换为十六进制颜色
            hex_colors = []
            for color in colors:
                hex_color = "#{:02x}{:02x}{:02x}".format(
                    int(color[0]), int(color[1]), int(color[2])
                )
                hex_colors.append(hex_color)
                
            return hex_colors
            
        except Exception as e:
            self.logger.error(f"颜色分析失败: {e}")
            return []
            
    def get_entity_details(self, entity: str) -> Dict:
        """获取实体详细信息"""
        try:
            # 先从知识库查询
            entity_info = None
            for category, items in self.knowledge_base.items():
                if entity in items:
                    entity_info = {
                        "entity": entity,
                        "category": category,
                        "local_info": items[entity],
                        "source": "local"
                    }
                    break
                    
            # 如果本地没有，尝试从维基百科获取
            if not entity_info:
                wiki_info = self.get_wikipedia_info(entity)
                if wiki_info:
                    entity_info = {
                        "entity": entity,
                        "category": "未知",
                        "wiki_info": wiki_info,
                        "source": "wikipedia"
                    }
                    
            return entity_info or {
                "entity": entity,
                "category": "未知",
                "message": "未找到相关信息",
                "source": "none"
            }
            
        except Exception as e:
            self.logger.error(f"实体详情获取失败: {e}")
            return {
                "entity": entity,
                "error": str(e),
                "source": "error"
            }
            
    def is_models_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self.models_loaded
        
    def get_model_status(self) -> Dict:
        """获取模型状态"""
        return {
            "models_loaded": self.models_loaded,
            "yolo_loaded": self.yolo_model is not None,
            "blip_loaded": self.blip_model is not None,
            "knowledge_base_size": len(self.knowledge_base)
        } 