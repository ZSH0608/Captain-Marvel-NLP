"""pytest 配置：把 momentjump 目录加入 sys.path，使 `from src.xxx import ...` 可用。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
