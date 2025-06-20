from .auth_service import AuthService

# 延后导入EntryService，避免循环导入
def get_entry_service():
    from .entry_service import EntryService
    return EntryService

# 或者直接导入，但确保所有依赖都已解决
try:
    from .entry_service import EntryService
    __all__ = ['AuthService', 'EntryService']
except ImportError:
    __all__ = ['AuthService']
