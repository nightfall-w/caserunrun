"""
@FileName：config.py
@Description：
@Author：baojun.wang
@Time：2025/10/29 19:49
"""
from pathlib import Path

# 获取当前文件（config.py）的绝对路径
current_file = Path(__file__).resolve()

PROJECT_ROOT = current_file.parent.parent.parent
MEDIA_ROOT = PROJECT_ROOT / 'media'
CASE_HOUSE_ROOT = MEDIA_ROOT / 'case_warehouse'
