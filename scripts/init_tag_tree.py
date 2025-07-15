#!/usr/bin/env python3
"""
标签树初始化脚本
创建完整的默认标签树结构，可以囊括世界上一切事物
"""

import os
import sys
import logging
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models.tag import Tag, TagHistory
from app.models.user import User

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 默认标签树结构
DEFAULT_TAG_TREE = {
    'root': {
        'id': 'root',
        'name': '万物图鉴',
        'name_en': 'Universal Encyclopedia',
        'description': '包含一切可记录事物的根分类',
        'level': 0,
        'category': 'root',
        'domain': 'universal',
        'is_system': True,
        'quality_score': 10.0,
        'aliases': ['根节点', '全部', '所有'],
        'children': {
            'existence': {
                'name': '存在界',
                'name_en': 'Existence Realm',
                'description': '一切有形的、可感知的客观存在',
                'category': 'philosophical',
                'domain': 'ontology',
                'is_abstract': True,
                'aliases': ['物质世界', '客观存在', '现实世界'],
                'children': {
                    'life': {
                        'name': '生命域',
                        'name_en': 'Life Domain',
                        'description': '所有具有生命特征的存在',
                        'category': 'biological',
                        'domain': 'biology',
                        'aliases': ['生物域', '生命体', '有机体'],
                        'children': {
                            'animals': {
                                'name': '动物',
                                'name_en': 'Animals',
                                'description': '具有运动能力和感知能力的生物',
                                'category': 'biological',
                                'domain': 'zoology',
                                'aliases': ['动物界', '动物王国'],
                                'children': {
                                    'vertebrates': {
                                        'name': '脊椎动物',
                                        'name_en': 'Vertebrates',
                                        'description': '具有脊椎的动物',
                                        'category': 'biological',
                                        'domain': 'zoology',
                                        'aliases': ['有脊椎动物'],
                                        'children': {
                                            'mammals': {
                                                'name': '哺乳动物',
                                                'name_en': 'Mammals',
                                                'description': '体温恒定、用乳汁哺育幼体的动物',
                                                'category': 'biological',
                                                'domain': 'zoology',
                                                'aliases': ['哺乳类']
                                            },
                                            'birds': {
                                                'name': '鸟类',
                                                'name_en': 'Birds',
                                                'description': '具有羽毛和飞行能力的动物',
                                                'category': 'biological',
                                                'domain': 'zoology',
                                                'aliases': ['鸟', '飞禽']
                                            },
                                            'reptiles': {
                                                'name': '爬行动物',
                                                'name_en': 'Reptiles',
                                                'description': '体表覆盖鳞片的冷血动物',
                                                'category': 'biological',
                                                'domain': 'zoology',
                                                'aliases': ['爬行类', '爬虫']
                                            },
                                            'amphibians': {
                                                'name': '两栖动物',
                                                'name_en': 'Amphibians',
                                                'description': '既能在水中也能在陆地生活的动物',
                                                'category': 'biological',
                                                'domain': 'zoology',
                                                'aliases': ['两栖类']
                                            },
                                            'fish': {
                                                'name': '鱼类',
                                                'name_en': 'Fish',
                                                'description': '生活在水中，用鳃呼吸的动物',
                                                'category': 'biological',
                                                'domain': 'zoology',
                                                'aliases': ['鱼', '水族']
                                            }
                                        }
                                    },
                                    'invertebrates': {
                                        'name': '无脊椎动物',
                                        'name_en': 'Invertebrates',
                                        'description': '没有脊椎的动物',
                                        'category': 'biological',
                                        'domain': 'zoology',
                                        'aliases': ['无脊椎类'],
                                        'children': {
                                            'insects': {
                                                'name': '昆虫',
                                                'name_en': 'Insects',
                                                'description': '具有三对足和一对或两对翅膀的节肢动物',
                                                'category': 'biological',
                                                'domain': 'entomology',
                                                'aliases': ['昆虫类', '虫子']
                                            },
                                            'arachnids': {
                                                'name': '蛛形动物',
                                                'name_en': 'Arachnids',
                                                'description': '包括蜘蛛、蝎子等的节肢动物',
                                                'category': 'biological',
                                                'domain': 'zoology',
                                                'aliases': ['蛛形类', '蜘蛛类']
                                            },
                                            'crustaceans': {
                                                'name': '甲壳动物',
                                                'name_en': 'Crustaceans',
                                                'description': '具有外壳的节肢动物',
                                                'category': 'biological',
                                                'domain': 'zoology',
                                                'aliases': ['甲壳类']
                                            },
                                            'mollusks': {
                                                'name': '软体动物',
                                                'name_en': 'Mollusks',
                                                'description': '身体柔软，通常有外壳的动物',
                                                'category': 'biological',
                                                'domain': 'zoology',
                                                'aliases': ['软体类']
                                            }
                                        }
                                    }
                                }
                            },
                            'plants': {
                                'name': '植物',
                                'name_en': 'Plants',
                                'description': '能够进行光合作用的生物',
                                'category': 'biological',
                                'domain': 'botany',
                                'aliases': ['植物界', '植物王国'],
                                'children': {
                                    'flowering_plants': {
                                        'name': '开花植物',
                                        'name_en': 'Flowering Plants',
                                        'description': '能开花结果的植物',
                                        'category': 'biological',
                                        'domain': 'botany',
                                        'aliases': ['被子植物', '花卉']
                                    },
                                    'trees': {
                                        'name': '树木',
                                        'name_en': 'Trees',
                                        'description': '高大的木本植物',
                                        'category': 'biological',
                                        'domain': 'botany',
                                        'aliases': ['树', '乔木']
                                    },
                                    'herbs': {
                                        'name': '草本植物',
                                        'name_en': 'Herbs',
                                        'description': '茎部较软的植物',
                                        'category': 'biological',
                                        'domain': 'botany',
                                        'aliases': ['草', '草本']
                                    },
                                    'ferns': {
                                        'name': '蕨类植物',
                                        'name_en': 'Ferns',
                                        'description': '通过孢子繁殖的植物',
                                        'category': 'biological',
                                        'domain': 'botany',
                                        'aliases': ['蕨类']
                                    },
                                    'mosses': {
                                        'name': '苔藓植物',
                                        'name_en': 'Mosses',
                                        'description': '小型的非维管植物',
                                        'category': 'biological',
                                        'domain': 'botany',
                                        'aliases': ['苔藓']
                                    }
                                }
                            },
                            'microorganisms': {
                                'name': '微生物',
                                'name_en': 'Microorganisms',
                                'description': '需要显微镜才能看到的微小生物',
                                'category': 'biological',
                                'domain': 'microbiology',
                                'aliases': ['微生物界', '细菌'],
                                'children': {
                                    'bacteria': {
                                        'name': '细菌',
                                        'name_en': 'Bacteria',
                                        'description': '单细胞的原核生物',
                                        'category': 'biological',
                                        'domain': 'microbiology',
                                        'aliases': ['细菌界']
                                    },
                                    'viruses': {
                                        'name': '病毒',
                                        'name_en': 'Viruses',
                                        'description': '需要寄生在其他生物体内才能繁殖的微小生物',
                                        'category': 'biological',
                                        'domain': 'virology',
                                        'aliases': ['病毒体']
                                    },
                                    'fungi': {
                                        'name': '真菌',
                                        'name_en': 'Fungi',
                                        'description': '既不是植物也不是动物的真核生物',
                                        'category': 'biological',
                                        'domain': 'mycology',
                                        'aliases': ['真菌界', '蘑菇']
                                    }
                                }
                            }
                        }
                    },
                    'matter': {
                        'name': '物质域',
                        'name_en': 'Matter Domain',
                        'description': '非生命的物质存在',
                        'category': 'physical',
                        'domain': 'physics',
                        'aliases': ['物质世界', '无机界'],
                        'children': {
                            'natural_matter': {
                                'name': '自然物质',
                                'name_en': 'Natural Matter',
                                'description': '自然形成的物质',
                                'category': 'physical',
                                'domain': 'geology',
                                'aliases': ['天然物质', '自然物'],
                                'children': {
                                    'minerals': {
                                        'name': '矿物',
                                        'name_en': 'Minerals',
                                        'description': '地球上自然形成的无机物质',
                                        'category': 'physical',
                                        'domain': 'geology',
                                        'aliases': ['矿物质', '矿石']
                                    },
                                    'rocks': {
                                        'name': '岩石',
                                        'name_en': 'Rocks',
                                        'description': '由矿物组成的固体物质',
                                        'category': 'physical',
                                        'domain': 'geology',
                                        'aliases': ['石头', '岩']
                                    },
                                    'crystals': {
                                        'name': '晶体',
                                        'name_en': 'Crystals',
                                        'description': '原子或分子有序排列的固体',
                                        'category': 'physical',
                                        'domain': 'chemistry',
                                        'aliases': ['水晶', '结晶']
                                    },
                                    'water': {
                                        'name': '水',
                                        'name_en': 'Water',
                                        'description': '生命必需的液体',
                                        'category': 'physical',
                                        'domain': 'chemistry',
                                        'aliases': ['水分', '液体']
                                    },
                                    'air': {
                                        'name': '空气',
                                        'name_en': 'Air',
                                        'description': '地球大气层中的气体混合物',
                                        'category': 'physical',
                                        'domain': 'atmospheric_science',
                                        'aliases': ['大气', '气体']
                                    }
                                }
                            },
                            'celestial_bodies': {
                                'name': '天体',
                                'name_en': 'Celestial Bodies',
                                'description': '宇宙中的天然物体',
                                'category': 'physical',
                                'domain': 'astronomy',
                                'aliases': ['天体物理', '星体'],
                                'children': {
                                    'stars': {
                                        'name': '恒星',
                                        'name_en': 'Stars',
                                        'description': '自己发光的天体',
                                        'category': 'physical',
                                        'domain': 'astronomy',
                                        'aliases': ['星星', '恒星系']
                                    },
                                    'planets': {
                                        'name': '行星',
                                        'name_en': 'Planets',
                                        'description': '围绕恒星运行的天体',
                                        'category': 'physical',
                                        'domain': 'astronomy',
                                        'aliases': ['行星系']
                                    },
                                    'moons': {
                                        'name': '卫星',
                                        'name_en': 'Moons',
                                        'description': '围绕行星运行的天体',
                                        'category': 'physical',
                                        'domain': 'astronomy',
                                        'aliases': ['月球', '天然卫星']
                                    }
                                }
                            },
                            'geographical_features': {
                                'name': '地理特征',
                                'name_en': 'Geographical Features',
                                'description': '地球表面的自然特征',
                                'category': 'physical',
                                'domain': 'geography',
                                'aliases': ['地貌', '地形'],
                                'children': {
                                    'mountains': {
                                        'name': '山脉',
                                        'name_en': 'Mountains',
                                        'description': '高耸的地形',
                                        'category': 'physical',
                                        'domain': 'geography',
                                        'aliases': ['山', '山峰']
                                    },
                                    'oceans': {
                                        'name': '海洋',
                                        'name_en': 'Oceans',
                                        'description': '地球上的咸水体',
                                        'category': 'physical',
                                        'domain': 'oceanography',
                                        'aliases': ['海', '大洋']
                                    },
                                    'rivers': {
                                        'name': '河流',
                                        'name_en': 'Rivers',
                                        'description': '流动的淡水',
                                        'category': 'physical',
                                        'domain': 'hydrology',
                                        'aliases': ['河', '水系']
                                    },
                                    'lakes': {
                                        'name': '湖泊',
                                        'name_en': 'Lakes',
                                        'description': '被陆地包围的水体',
                                        'category': 'physical',
                                        'domain': 'hydrology',
                                        'aliases': ['湖', '水库']
                                    },
                                    'deserts': {
                                        'name': '沙漠',
                                        'name_en': 'Deserts',
                                        'description': '降水稀少的干燥地区',
                                        'category': 'physical',
                                        'domain': 'geography',
                                        'aliases': ['荒漠', '沙地']
                                    },
                                    'forests': {
                                        'name': '森林',
                                        'name_en': 'Forests',
                                        'description': '树木茂密的地区',
                                        'category': 'physical',
                                        'domain': 'ecology',
                                        'aliases': ['树林', '林地']
                                    }
                                }
                            }
                        }
                    },
                    'artifacts': {
                        'name': '人工制品',
                        'name_en': 'Artifacts',
                        'description': '人类创造的物质对象',
                        'category': 'artificial',
                        'domain': 'technology',
                        'aliases': ['人造物', '制品', '工艺品'],
                        'children': {
                            'tools': {
                                'name': '工具',
                                'name_en': 'Tools',
                                'description': '用于完成特定任务的器具',
                                'category': 'artificial',
                                'domain': 'technology',
                                'aliases': ['器具', '设备', '用具'],
                                'children': {
                                    'hand_tools': {
                                        'name': '手工工具',
                                        'name_en': 'Hand Tools',
                                        'description': '用手操作的工具',
                                        'category': 'artificial',
                                        'domain': 'technology',
                                        'aliases': ['手工具', '简单工具']
                                    },
                                    'power_tools': {
                                        'name': '电动工具',
                                        'name_en': 'Power Tools',
                                        'description': '需要电力或其他动力的工具',
                                        'category': 'artificial',
                                        'domain': 'technology',
                                        'aliases': ['电动器具', '机械工具']
                                    },
                                    'measuring_tools': {
                                        'name': '测量工具',
                                        'name_en': 'Measuring Tools',
                                        'description': '用于测量的工具',
                                        'category': 'artificial',
                                        'domain': 'technology',
                                        'aliases': ['测量仪器', '量具']
                                    }
                                }
                            },
                            'machines': {
                                'name': '机器',
                                'name_en': 'Machines',
                                'description': '复杂的机械设备',
                                'category': 'artificial',
                                'domain': 'technology',
                                'aliases': ['机械', '设备', '机器设备'],
                                'children': {
                                    'vehicles': {
                                        'name': '交通工具',
                                        'name_en': 'Vehicles',
                                        'description': '用于运输的机器',
                                        'category': 'artificial',
                                        'domain': 'transportation',
                                        'aliases': ['车辆', '运输工具']
                                    },
                                    'computers': {
                                        'name': '计算机',
                                        'name_en': 'Computers',
                                        'description': '用于计算和信息处理的机器',
                                        'category': 'artificial',
                                        'domain': 'technology',
                                        'aliases': ['电脑', '计算设备']
                                    },
                                    'appliances': {
                                        'name': '家用电器',
                                        'name_en': 'Appliances',
                                        'description': '家庭使用的电器设备',
                                        'category': 'artificial',
                                        'domain': 'technology',
                                        'aliases': ['家电', '电器']
                                    }
                                }
                            },
                            'structures': {
                                'name': '建筑结构',
                                'name_en': 'Structures',
                                'description': '建造的物理结构',
                                'category': 'artificial',
                                'domain': 'architecture',
                                'aliases': ['建筑', '构造物'],
                                'children': {
                                    'buildings': {
                                        'name': '建筑物',
                                        'name_en': 'Buildings',
                                        'description': '封闭的建筑结构',
                                        'category': 'artificial',
                                        'domain': 'architecture',
                                        'aliases': ['房屋', '建筑']
                                    },
                                    'bridges': {
                                        'name': '桥梁',
                                        'name_en': 'Bridges',
                                        'description': '跨越障碍的结构',
                                        'category': 'artificial',
                                        'domain': 'engineering',
                                        'aliases': ['桥', '桥梁工程']
                                    },
                                    'monuments': {
                                        'name': '纪念建筑',
                                        'name_en': 'Monuments',
                                        'description': '纪念性的建筑或雕塑',
                                        'category': 'artificial',
                                        'domain': 'architecture',
                                        'aliases': ['纪念碑', '雕塑']
                                    }
                                }
                            },
                            'materials': {
                                'name': '材料',
                                'name_en': 'Materials',
                                'description': '制造物品的原料',
                                'category': 'artificial',
                                'domain': 'materials_science',
                                'aliases': ['原料', '材质'],
                                'children': {
                                    'metals': {
                                        'name': '金属',
                                        'name_en': 'Metals',
                                        'description': '具有光泽和导电性的材料',
                                        'category': 'artificial',
                                        'domain': 'materials_science',
                                        'aliases': ['金属材料', '合金']
                                    },
                                    'plastics': {
                                        'name': '塑料',
                                        'name_en': 'Plastics',
                                        'description': '合成的高分子材料',
                                        'category': 'artificial',
                                        'domain': 'materials_science',
                                        'aliases': ['塑胶', '高分子']
                                    },
                                    'ceramics': {
                                        'name': '陶瓷',
                                        'name_en': 'Ceramics',
                                        'description': '烧制的无机材料',
                                        'category': 'artificial',
                                        'domain': 'materials_science',
                                        'aliases': ['陶器', '瓷器']
                                    },
                                    'textiles': {
                                        'name': '纺织品',
                                        'name_en': 'Textiles',
                                        'description': '纤维制成的材料',
                                        'category': 'artificial',
                                        'domain': 'materials_science',
                                        'aliases': ['织物', '布料']
                                    }
                                }
                            }
                        }
                    }
                }
            },
            'consciousness': {
                'name': '意识界',
                'name_en': 'Consciousness Realm',
                'description': '精神层面的、主观的内在体验',
                'category': 'philosophical',
                'domain': 'psychology',
                'is_abstract': True,
                'aliases': ['精神世界', '主观体验', '内在世界'],
                'children': {
                    'emotions': {
                        'name': '情感',
                        'name_en': 'Emotions',
                        'description': '人类的情感体验',
                        'category': 'psychological',
                        'domain': 'psychology',
                        'is_abstract': True,
                        'aliases': ['情绪', '感情'],
                        'children': {
                            'positive_emotions': {
                                'name': '积极情感',
                                'name_en': 'Positive Emotions',
                                'description': '令人愉快的情感体验',
                                'category': 'psychological',
                                'domain': 'psychology',
                                'is_abstract': True,
                                'aliases': ['正面情绪', '正能量']
                            },
                            'negative_emotions': {
                                'name': '消极情感',
                                'name_en': 'Negative Emotions',
                                'description': '令人不快的情感体验',
                                'category': 'psychological',
                                'domain': 'psychology',
                                'is_abstract': True,
                                'aliases': ['负面情绪', '负能量']
                            }
                        }
                    },
                    'concepts': {
                        'name': '概念',
                        'name_en': 'Concepts',
                        'description': '抽象的思想和理念',
                        'category': 'philosophical',
                        'domain': 'philosophy',
                        'is_abstract': True,
                        'aliases': ['理念', '思想', '观念'],
                        'children': {
                            'abstract_concepts': {
                                'name': '抽象概念',
                                'name_en': 'Abstract Concepts',
                                'description': '无法直接感知的概念',
                                'category': 'philosophical',
                                'domain': 'philosophy',
                                'is_abstract': True,
                                'aliases': ['抽象思维', '抽象理念']
                            },
                            'philosophical_concepts': {
                                'name': '哲学概念',
                                'name_en': 'Philosophical Concepts',
                                'description': '哲学思考的概念',
                                'category': 'philosophical',
                                'domain': 'philosophy',
                                'is_abstract': True,
                                'aliases': ['哲学思想', '哲学理念']
                            }
                        }
                    },
                    'activities': {
                        'name': '活动',
                        'name_en': 'Activities',
                        'description': '人类的各种活动和行为',
                        'category': 'behavioral',
                        'domain': 'sociology',
                        'aliases': ['行为', '动作', '行动'],
                        'children': {
                            'social_activities': {
                                'name': '社会活动',
                                'name_en': 'Social Activities',
                                'description': '涉及社会交往的活动',
                                'category': 'behavioral',
                                'domain': 'sociology',
                                'aliases': ['社交活动', '集体活动']
                            },
                            'cultural_activities': {
                                'name': '文化活动',
                                'name_en': 'Cultural Activities',
                                'description': '与文化相关的活动',
                                'category': 'behavioral',
                                'domain': 'cultural_studies',
                                'aliases': ['文化事业', '文化项目']
                            },
                            'sports': {
                                'name': '体育运动',
                                'name_en': 'Sports',
                                'description': '身体锻炼和竞技活动',
                                'category': 'behavioral',
                                'domain': 'sports_science',
                                'aliases': ['运动', '体育', '健身']
                            },
                            'arts': {
                                'name': '艺术',
                                'name_en': 'Arts',
                                'description': '创造美的活动',
                                'category': 'cultural',
                                'domain': 'arts',
                                'aliases': ['艺术创作', '美术'],
                                'children': {
                                    'visual_arts': {
                                        'name': '视觉艺术',
                                        'name_en': 'Visual Arts',
                                        'description': '主要通过视觉感受的艺术',
                                        'category': 'cultural',
                                        'domain': 'arts',
                                        'aliases': ['美术', '造型艺术']
                                    },
                                    'performing_arts': {
                                        'name': '表演艺术',
                                        'name_en': 'Performing Arts',
                                        'description': '通过表演展示的艺术',
                                        'category': 'cultural',
                                        'domain': 'arts',
                                        'aliases': ['演艺', '表演']
                                    },
                                    'music': {
                                        'name': '音乐',
                                        'name_en': 'Music',
                                        'description': '通过声音表达的艺术',
                                        'category': 'cultural',
                                        'domain': 'music',
                                        'aliases': ['音乐艺术', '声乐']
                                    },
                                    'literature': {
                                        'name': '文学',
                                        'name_en': 'Literature',
                                        'description': '通过文字表达的艺术',
                                        'category': 'cultural',
                                        'domain': 'literature',
                                        'aliases': ['文学艺术', '文字艺术']
                                    }
                                }
                            }
                        }
                    }
                }
            },
            'phenomena': {
                'name': '现象域',
                'name_en': 'Phenomena Domain',
                'description': '各种可观察的现象和过程',
                'category': 'observational',
                'domain': 'science',
                'aliases': ['现象界', '过程'],
                'children': {
                    'natural_phenomena': {
                        'name': '自然现象',
                        'name_en': 'Natural Phenomena',
                        'description': '自然界中发生的现象',
                        'category': 'observational',
                        'domain': 'natural_science',
                        'aliases': ['自然界现象', '自然过程'],
                        'children': {
                            'weather': {
                                'name': '天气现象',
                                'name_en': 'Weather Phenomena',
                                'description': '大气中的各种现象',
                                'category': 'observational',
                                'domain': 'meteorology',
                                'aliases': ['天气', '气象']
                            },
                            'geological_phenomena': {
                                'name': '地质现象',
                                'name_en': 'Geological Phenomena',
                                'description': '地球内部和表面的现象',
                                'category': 'observational',
                                'domain': 'geology',
                                'aliases': ['地质过程', '地质活动']
                            },
                            'astronomical_phenomena': {
                                'name': '天文现象',
                                'name_en': 'Astronomical Phenomena',
                                'description': '宇宙中的各种现象',
                                'category': 'observational',
                                'domain': 'astronomy',
                                'aliases': ['天象', '宇宙现象']
                            }
                        }
                    },
                    'physical_phenomena': {
                        'name': '物理现象',
                        'name_en': 'Physical Phenomena',
                        'description': '物理学研究的现象',
                        'category': 'observational',
                        'domain': 'physics',
                        'aliases': ['物理过程', '物理效应'],
                        'children': {
                            'mechanical_phenomena': {
                                'name': '力学现象',
                                'name_en': 'Mechanical Phenomena',
                                'description': '与运动和力相关的现象',
                                'category': 'observational',
                                'domain': 'mechanics',
                                'aliases': ['力学过程', '运动现象']
                            },
                            'thermal_phenomena': {
                                'name': '热现象',
                                'name_en': 'Thermal Phenomena',
                                'description': '与温度和热量相关的现象',
                                'category': 'observational',
                                'domain': 'thermodynamics',
                                'aliases': ['热力学现象', '温度现象']
                            },
                            'optical_phenomena': {
                                'name': '光学现象',
                                'name_en': 'Optical Phenomena',
                                'description': '与光相关的现象',
                                'category': 'observational',
                                'domain': 'optics',
                                'aliases': ['光现象', '光学效应']
                            },
                            'electrical_phenomena': {
                                'name': '电磁现象',
                                'name_en': 'Electromagnetic Phenomena',
                                'description': '与电和磁相关的现象',
                                'category': 'observational',
                                'domain': 'electromagnetism',
                                'aliases': ['电现象', '磁现象']
                            }
                        }
                    },
                    'chemical_phenomena': {
                        'name': '化学现象',
                        'name_en': 'Chemical Phenomena',
                        'description': '物质发生化学变化的现象',
                        'category': 'observational',
                        'domain': 'chemistry',
                        'aliases': ['化学反应', '化学过程']
                    },
                    'biological_phenomena': {
                        'name': '生物现象',
                        'name_en': 'Biological Phenomena',
                        'description': '生物体中发生的现象',
                        'category': 'observational',
                        'domain': 'biology',
                        'aliases': ['生物过程', '生命现象']
                    }
                }
            },
            'properties': {
                'name': '属性域',
                'name_en': 'Properties Domain',
                'description': '事物的各种属性和特征',
                'category': 'descriptive',
                'domain': 'general',
                'is_abstract': True,
                'aliases': ['特征', '性质', '属性'],
                'children': {
                    'physical_properties': {
                        'name': '物理属性',
                        'name_en': 'Physical Properties',
                        'description': '物质的物理特征',
                        'category': 'descriptive',
                        'domain': 'physics',
                        'is_abstract': True,
                        'aliases': ['物理特性', '物理性质'],
                        'children': {
                            'color': {
                                'name': '颜色',
                                'name_en': 'Color',
                                'description': '物体反射光的特征',
                                'category': 'descriptive',
                                'domain': 'optics',
                                'is_abstract': True,
                                'aliases': ['色彩', '颜色特征']
                            },
                            'shape': {
                                'name': '形状',
                                'name_en': 'Shape',
                                'description': '物体的外形特征',
                                'category': 'descriptive',
                                'domain': 'geometry',
                                'is_abstract': True,
                                'aliases': ['外形', '形态']
                            },
                            'size': {
                                'name': '尺寸',
                                'name_en': 'Size',
                                'description': '物体的大小',
                                'category': 'descriptive',
                                'domain': 'geometry',
                                'is_abstract': True,
                                'aliases': ['大小', '尺度']
                            },
                            'texture': {
                                'name': '质地',
                                'name_en': 'Texture',
                                'description': '物体表面的触感特征',
                                'category': 'descriptive',
                                'domain': 'materials_science',
                                'is_abstract': True,
                                'aliases': ['质感', '纹理']
                            }
                        }
                    },
                    'chemical_properties': {
                        'name': '化学属性',
                        'name_en': 'Chemical Properties',
                        'description': '物质的化学特征',
                        'category': 'descriptive',
                        'domain': 'chemistry',
                        'is_abstract': True,
                        'aliases': ['化学特性', '化学性质']
                    },
                    'biological_properties': {
                        'name': '生物属性',
                        'name_en': 'Biological Properties',
                        'description': '生物体的特征',
                        'category': 'descriptive',
                        'domain': 'biology',
                        'is_abstract': True,
                        'aliases': ['生物特性', '生物性质']
                    }
                }
            }
        }
    }
}

def create_tag_tree():
    """创建完整的标签树"""
    logger.info("开始创建标签树...")
    
    app = create_app('development')
    
    with app.app_context():
        try:
            # 获取系统用户
            system_user = User.query.filter_by(username='admin').first()
            if not system_user:
                logger.warning("未找到admin用户，使用第一个用户作为系统用户")
                system_user = User.query.first()
                
            if not system_user:
                logger.error("数据库中没有用户，请先创建用户")
                return False
            
            # 递归创建标签树
            created_count = 0
            
            def create_tags_recursive(tag_data, parent_id=None, level=0):
                nonlocal created_count
                
                # 创建当前标签
                tag_info = tag_data.copy()
                children = tag_info.pop('children', {})
                
                # 设置默认值
                tag_info.setdefault('level', level)
                tag_info.setdefault('category', 'general')
                tag_info.setdefault('domain', 'general')
                tag_info.setdefault('is_abstract', False)
                tag_info.setdefault('is_system', False)
                tag_info.setdefault('quality_score', 8.0)
                tag_info.setdefault('aliases', [])
                
                # 检查标签是否已存在
                existing_tag = Tag.query.filter_by(name=tag_info['name']).first()
                if existing_tag:
                    logger.info(f"标签 '{tag_info['name']}' 已存在，跳过创建")
                    current_tag = existing_tag
                else:
                    # 创建新标签
                    current_tag = Tag(
                        name=tag_info['name'],
                        name_en=tag_info.get('name_en', ''),
                        description=tag_info.get('description', ''),
                        parent_id=parent_id,
                        level=level,
                        category=tag_info['category'],
                        domain=tag_info['domain'],
                        is_abstract=tag_info['is_abstract'],
                        is_system=tag_info['is_system'],
                        quality_score=tag_info['quality_score'],
                        aliases=tag_info['aliases'],
                        created_by=system_user.id,
                        status='active'
                    )
                    
                    db.session.add(current_tag)
                    db.session.flush()  # 获取ID
                    
                    # 更新路径
                    current_tag.update_path()
                    
                    # 记录历史
                    history = TagHistory(
                        tag_id=current_tag.id,
                        action='create',
                        action_description=f"系统初始化创建标签: {current_tag.name}",
                        new_data=current_tag.to_dict(),
                        user_id=system_user.id
                    )
                    db.session.add(history)
                    
                    created_count += 1
                    logger.info(f"创建标签: {current_tag.name} (级别: {level})")
                
                # 递归创建子标签
                for child_key, child_data in children.items():
                    create_tags_recursive(child_data, current_tag.id, level + 1)
                
                return current_tag
            
            # 开始创建标签树
            root_data = DEFAULT_TAG_TREE['root']
            create_tags_recursive(root_data)
            
            # 提交所有更改
            db.session.commit()
            
            logger.info(f"标签树创建完成！共创建 {created_count} 个标签")
            return True
            
        except Exception as e:
            logger.error(f"创建标签树失败: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

def main():
    """主函数"""
    print("🌳 开始初始化标签树...")
    
    success = create_tag_tree()
    
    if success:
        print("✅ 标签树初始化成功！")
        print("\n📊 标签树结构:")
        print("根节点: 万物图鉴")
        print("├── 存在界 (物质世界)")
        print("│   ├── 生命域 (生物)")
        print("│   │   ├── 动物")
        print("│   │   │   ├── 脊椎动物")
        print("│   │   │   └── 无脊椎动物")
        print("│   │   ├── 植物")
        print("│   │   └── 微生物")
        print("│   ├── 物质域 (非生命)")
        print("│   │   ├── 自然物质")
        print("│   │   ├── 天体")
        print("│   │   └── 地理特征")
        print("│   └── 人工制品")
        print("│       ├── 工具")
        print("│       ├── 机器")
        print("│       ├── 建筑结构")
        print("│       └── 材料")
        print("├── 意识界 (精神世界)")
        print("│   ├── 情感")
        print("│   ├── 概念")
        print("│   └── 活动")
        print("│       └── 艺术")
        print("├── 现象域 (过程)")
        print("│   ├── 自然现象")
        print("│   ├── 物理现象")
        print("│   ├── 化学现象")
        print("│   └── 生物现象")
        print("└── 属性域 (特征)")
        print("    ├── 物理属性")
        print("    │   ├── 颜色")
        print("    │   ├── 形状")
        print("    │   ├── 尺寸")
        print("    │   └── 质地")
        print("    ├── 化学属性")
        print("    └── 生物属性")
        print("\n🎯 现在你可以使用 API 来:")
        print("1. 搜索标签: GET /api/tag-tree/search?keyword=动物")
        print("2. 获取标签树: GET /api/tag-tree/tree")
        print("3. 创建新标签: POST /api/tag-tree/")
        print("4. 自动放置标签: POST /api/tag-tree/auto-place")
    else:
        print("❌ 标签树初始化失败！")
        sys.exit(1)

if __name__ == '__main__':
    main() 