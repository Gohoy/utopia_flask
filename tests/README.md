# 测试说明

## 单元测试和功能测试

```bash
# 安装pytest
pip install pytest pytest-cov

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_auth.py
pytest tests/test_entries.py

# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html

# 详细输出
pytest -v
