from .user import User, UserPermission
from .media import MediaFile
from .entry import Entry, EntryTag
from .tag import Tag, TagHistory, TagRelation

# 设置关系（如果需要）
def setup_relationships():
    """设置模型之间的关系"""
    # Entry的关系已经在模型中定义，这里可以为空
    pass

# 调用关系设置
setup_relationships()

__all__ = ['User', 'UserPermission', 'Entry', 'EntryTag', 'MediaFile', 'Tag', 'TagHistory', 'TagRelation']
