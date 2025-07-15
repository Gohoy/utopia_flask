import re
import logging
from typing import Dict, List, Optional, Tuple
from fuzzywuzzy import fuzz
from app.models.tag import Tag

logger = logging.getLogger(__name__)

class AITagMapper:
    """AI标签映射器 - 将AI识别结果映射到标签树中的合适位置"""
    
    def __init__(self):
        self.object_category_mapping = {
            # 生物类别
            'animals': ['动物', '哺乳动物', '鸟类', '鱼类', '爬行动物', '两栖动物', '昆虫', '节肢动物'],
            'plants': ['植物', '花卉', '树木', '草本植物', '蕨类', '藻类', '真菌'],
            'biological': ['生物', '微生物', '细菌', '病毒', '细胞', '器官', '组织'],
            
            # 物理对象
            'vehicles': ['车辆', '汽车', '自行车', '摩托车', '飞机', '船舶', '火车'],
            'buildings': ['建筑', '房屋', '桥梁', '塔楼', '纪念碑', '教堂', '寺庙'],
            'tools': ['工具', '设备', '机器', '器械', '仪器', '装置'],
            'furniture': ['家具', '椅子', '桌子', '床', '柜子', '沙发'],
            'food': ['食物', '食品', '饮料', '蔬菜', '水果', '肉类', '海鲜'],
            'clothing': ['服装', '衣服', '鞋子', '帽子', '配饰', '珠宝'],
            'technology': ['电子产品', '计算机', '手机', '电视', '音响', '相机'],
            
            # 自然现象
            'weather': ['天气', '云', '雨', '雪', '雷电', '风', '霜'],
            'landscapes': ['景观', '山脉', '海洋', '湖泊', '河流', '沙漠', '森林'],
            'celestial': ['天体', '太阳', '月亮', '星星', '行星', '银河'],
            
            # 抽象概念
            'emotions': ['情感', '情绪', '快乐', '悲伤', '愤怒', '恐惧', '爱'],
            'concepts': ['概念', '思想', '理念', '哲学', '宗教', '文化'],
            'activities': ['活动', '运动', '游戏', '工作', '学习', '娱乐'],
            'art': ['艺术', '绘画', '雕塑', '音乐', '舞蹈', '文学', '电影'],
            
            # 材料
            'materials': ['材料', '金属', '木材', '石头', '塑料', '玻璃', '纸张', '织物'],
            'chemicals': ['化学物质', '化学品', '药物', '化合物', '元素']
        }
        
        # 颜色到标签的映射
        self.color_mapping = {
            'red': '红色',
            'blue': '蓝色',
            'green': '绿色',
            'yellow': '黄色',
            'purple': '紫色',
            'orange': '橙色',
            'pink': '粉色',
            'brown': '棕色',
            'black': '黑色',
            'white': '白色',
            'gray': '灰色',
            'grey': '灰色'
        }
        
        # 常见英文到中文的映射
        self.english_to_chinese = {
            'person': '人',
            'people': '人群',
            'man': '男人',
            'woman': '女人',
            'child': '孩子',
            'baby': '婴儿',
            'cat': '猫',
            'dog': '狗',
            'bird': '鸟',
            'fish': '鱼',
            'horse': '马',
            'cow': '牛',
            'elephant': '大象',
            'car': '汽车',
            'truck': '卡车',
            'bus': '公交车',
            'bicycle': '自行车',
            'airplane': '飞机',
            'boat': '船',
            'train': '火车',
            'house': '房子',
            'building': '建筑',
            'tree': '树',
            'flower': '花',
            'grass': '草',
            'mountain': '山',
            'sky': '天空',
            'cloud': '云',
            'sun': '太阳',
            'moon': '月亮',
            'star': '星星',
            'water': '水',
            'fire': '火',
            'food': '食物',
            'book': '书',
            'chair': '椅子',
            'table': '桌子',
            'computer': '电脑',
            'phone': '手机',
            'camera': '相机',
            'clock': '钟',
            'ball': '球',
            'toy': '玩具',
            'tool': '工具',
            'weapon': '武器',
            'clothes': '衣服',
            'shoes': '鞋子',
            'hat': '帽子',
            'bag': '包',
            'bottle': '瓶子',
            'cup': '杯子',
            'plate': '盘子',
            'knife': '刀',
            'fork': '叉子',
            'spoon': '勺子'
        }
    
    def find_best_parent(self, tag_name: str, description: str = '', 
                         ai_context: Dict = None) -> Optional[Tag]:
        """
        为给定的标签找到最合适的父标签
        
        Args:
            tag_name: 标签名称
            description: 描述
            ai_context: AI识别上下文，包含objects、scene、colors等信息
            
        Returns:
            最合适的父标签，如果找不到返回None
        """
        try:
            # 综合评分候选父标签
            candidates = []
            
            # 1. 基于AI上下文的映射
            if ai_context:
                ai_candidates = self._map_from_ai_context(ai_context)
                candidates.extend(ai_candidates)
            
            # 2. 基于标签名称的语义匹配
            name_candidates = self._map_from_tag_name(tag_name)
            candidates.extend(name_candidates)
            
            # 3. 基于描述的关键词匹配
            if description:
                desc_candidates = self._map_from_description(description)
                candidates.extend(desc_candidates)
            
            # 4. 基于颜色的映射
            color_candidates = self._map_from_colors(tag_name, description, ai_context)
            candidates.extend(color_candidates)
            
            # 去重并评分
            scored_candidates = self._score_candidates(candidates, tag_name, description)
            
            # 返回得分最高的候选者
            if scored_candidates:
                return scored_candidates[0][1]  # (score, tag)
            
            return None
            
        except Exception as e:
            logger.error(f"查找父标签失败: {e}")
            return None
    
    def _map_from_ai_context(self, ai_context: Dict) -> List[Tuple[str, float]]:
        """基于AI上下文映射候选父标签"""
        candidates = []
        
        # 从检测到的物体中映射
        objects = ai_context.get('objects', [])
        for obj in objects:
            if isinstance(obj, dict):
                name = obj.get('name', '').lower()
                confidence = obj.get('confidence', 0.5)
            else:
                name = str(obj).lower()
                confidence = 0.5
            
            # 查找对应的父标签
            parent_tags = self._find_parent_tags_for_object(name)
            for parent_tag in parent_tags:
                candidates.append((parent_tag, confidence))
        
        # 从场景信息中映射
        scene = ai_context.get('scene', '')
        if scene:
            scene_tags = self._find_parent_tags_for_scene(scene)
            for tag in scene_tags:
                candidates.append((tag, 0.3))  # 场景信息权重较低
        
        return candidates
    
    def _map_from_tag_name(self, tag_name: str) -> List[Tuple[str, float]]:
        """基于标签名称映射候选父标签"""
        candidates = []
        name_lower = tag_name.lower()
        
        # 直接英文映射
        if name_lower in self.english_to_chinese:
            chinese_name = self.english_to_chinese[name_lower]
            parent_tags = self._find_parent_tags_for_object(chinese_name)
            for tag in parent_tags:
                candidates.append((tag, 0.9))
        
        # 基于分类映射
        for category, keywords in self.object_category_mapping.items():
            for keyword in keywords:
                if keyword in tag_name or fuzz.ratio(tag_name, keyword) > 80:
                    parent_tag = self._get_category_parent_tag(category)
                    if parent_tag:
                        candidates.append((parent_tag, 0.7))
        
        return candidates
    
    def _map_from_description(self, description: str) -> List[Tuple[str, float]]:
        """基于描述映射候选父标签"""
        candidates = []
        desc_lower = description.lower()
        
        # 关键词匹配
        for category, keywords in self.object_category_mapping.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    parent_tag = self._get_category_parent_tag(category)
                    if parent_tag:
                        candidates.append((parent_tag, 0.5))
        
        return candidates
    
    def _map_from_colors(self, tag_name: str, description: str, 
                        ai_context: Dict = None) -> List[Tuple[str, float]]:
        """基于颜色映射候选父标签"""
        candidates = []
        
        # 检查颜色信息
        colors = []
        if ai_context and 'colors' in ai_context:
            colors.extend(ai_context['colors'])
        
        # 从标签名称中提取颜色
        for color_en, color_zh in self.color_mapping.items():
            if color_en in tag_name.lower() or color_zh in tag_name:
                colors.append(color_zh)
        
        # 为颜色找到父标签
        if colors:
            color_parent = Tag.query.filter_by(name='颜色', status='active').first()
            if color_parent:
                candidates.append((color_parent.name, 0.8))
        
        return candidates
    
    def _find_parent_tags_for_object(self, object_name: str) -> List[str]:
        """为特定对象找到父标签"""
        parent_tags = []
        
        # 生物类别
        if any(keyword in object_name for keyword in ['动物', '猫', '狗', '鸟', '鱼', '昆虫']):
            parent_tags.append('动物')
        elif any(keyword in object_name for keyword in ['植物', '花', '树', '草', '叶子']):
            parent_tags.append('植物')
        
        # 人工制品
        elif any(keyword in object_name for keyword in ['车', '汽车', '自行车', '摩托车']):
            parent_tags.append('交通工具')
        elif any(keyword in object_name for keyword in ['房', '建筑', '桥']):
            parent_tags.append('建筑')
        elif any(keyword in object_name for keyword in ['工具', '设备', '机器']):
            parent_tags.append('工具')
        elif any(keyword in object_name for keyword in ['食物', '食品', '饮料']):
            parent_tags.append('食物')
        elif any(keyword in object_name for keyword in ['衣服', '服装', '鞋']):
            parent_tags.append('服装')
        elif any(keyword in object_name for keyword in ['电子', '电脑', '手机']):
            parent_tags.append('电子产品')
        
        # 自然现象
        elif any(keyword in object_name for keyword in ['天', '云', '雨', '雪']):
            parent_tags.append('自然现象')
        elif any(keyword in object_name for keyword in ['山', '海', '湖', '河']):
            parent_tags.append('地理特征')
        
        return parent_tags
    
    def _find_parent_tags_for_scene(self, scene: str) -> List[str]:
        """为场景找到父标签"""
        parent_tags = []
        scene_lower = scene.lower()
        
        if any(keyword in scene_lower for keyword in ['outdoor', '户外', '自然', '风景']):
            parent_tags.append('自然环境')
        elif any(keyword in scene_lower for keyword in ['indoor', '室内', '房间']):
            parent_tags.append('室内环境')
        elif any(keyword in scene_lower for keyword in ['city', '城市', '街道']):
            parent_tags.append('城市环境')
        elif any(keyword in scene_lower for keyword in ['ocean', '海洋', 'beach', '海滩']):
            parent_tags.append('海洋环境')
        elif any(keyword in scene_lower for keyword in ['mountain', '山', 'forest', '森林']):
            parent_tags.append('山地环境')
        
        return parent_tags
    
    def _get_category_parent_tag(self, category: str) -> Optional[str]:
        """获取分类对应的父标签名称"""
        category_mapping = {
            'animals': '动物',
            'plants': '植物',
            'biological': '生物',
            'vehicles': '交通工具',
            'buildings': '建筑',
            'tools': '工具',
            'furniture': '家具',
            'food': '食物',
            'clothing': '服装',
            'technology': '电子产品',
            'weather': '自然现象',
            'landscapes': '地理特征',
            'celestial': '天体',
            'emotions': '情感',
            'concepts': '抽象概念',
            'activities': '活动',
            'art': '艺术',
            'materials': '材料',
            'chemicals': '化学物质'
        }
        
        return category_mapping.get(category)
    
    def _score_candidates(self, candidates: List[Tuple[str, float]], 
                         tag_name: str, description: str) -> List[Tuple[float, Tag]]:
        """为候选父标签评分并排序"""
        scored = {}
        
        for parent_name, confidence in candidates:
            # 查找标签
            parent_tag = Tag.query.filter_by(name=parent_name, status='active').first()
            if not parent_tag:
                continue
            
            # 计算综合评分
            score = confidence
            
            # 根据标签的使用频率调整评分
            if parent_tag.usage_count > 0:
                score *= min(1.2, 1.0 + parent_tag.usage_count / 100)
            
            # 根据标签的质量评分调整
            score *= (parent_tag.quality_score / 10.0)
            
            # 累计相同标签的评分
            if parent_tag in scored:
                scored[parent_tag] = max(scored[parent_tag], score)
            else:
                scored[parent_tag] = score
        
        # 排序并返回
        return sorted(scored.items(), key=lambda x: x[1], reverse=True)
    
    def suggest_similar_tags(self, tag_name: str, limit: int = 5) -> List[Dict]:
        """建议相似的标签"""
        try:
            # 查找名称相似的标签
            similar_tags = Tag.query.filter(
                Tag.status == 'active',
                Tag.name.ilike(f"%{tag_name}%")
            ).limit(limit * 2).all()
            
            # 计算相似度并排序
            scored_tags = []
            for tag in similar_tags:
                similarity = fuzz.ratio(tag_name, tag.name)
                if similarity > 60:  # 只返回相似度大于60的标签
                    scored_tags.append({
                        'tag': tag.to_dict(),
                        'similarity': similarity
                    })
            
            # 按相似度排序
            scored_tags.sort(key=lambda x: x['similarity'], reverse=True)
            
            return scored_tags[:limit]
            
        except Exception as e:
            logger.error(f"建议相似标签失败: {e}")
            return []
    
    def extract_tags_from_text(self, text: str) -> List[str]:
        """从文本中提取可能的标签"""
        tags = []
        
        # 提取颜色
        for color_en, color_zh in self.color_mapping.items():
            if color_en in text.lower() or color_zh in text:
                tags.append(color_zh)
        
        # 提取常见对象
        for en_word, zh_word in self.english_to_chinese.items():
            if en_word in text.lower() or zh_word in text:
                tags.append(zh_word)
        
        # 提取分类关键词
        for category, keywords in self.object_category_mapping.items():
            for keyword in keywords:
                if keyword in text:
                    tags.append(keyword)
        
        # 去重
        return list(set(tags)) 