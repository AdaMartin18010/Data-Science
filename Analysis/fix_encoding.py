#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复文件编码问题"""

from pathlib import Path

file_path = Path('3-数据模型与算法/3.4-AI与机器学习算法/3.4.7-概率图模型.md')

try:
    # 尝试用UTF-16读取
    with open(file_path, 'r', encoding='utf-16-le') as f:
        content = f.read()
    
    # 写入UTF-8
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ 已修复文件编码: {file_path}")
except Exception as e:
    print(f"✗ 修复失败: {e}")
