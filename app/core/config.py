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
REPORT_ROOT = MEDIA_ROOT / 'html-report'
REPORT_URL = 'media/html-report'
print("项目根目录：", PROJECT_ROOT)
print("媒体目录：", MEDIA_ROOT)
print("用例仓库目录：", CASE_HOUSE_ROOT)
