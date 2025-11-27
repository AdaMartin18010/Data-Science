#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从备份恢复文件"""

import shutil
from pathlib import Path

backup_dir = Path('.structure_backup')
root_dir = Path('.')

if backup_dir.exists():
    for backup_file in backup_dir.rglob('*.md'):
        if backup_file.is_file():
            # 计算目标路径
            rel_path = backup_file.relative_to(backup_dir)
            target_file = root_dir / rel_path
            
            # 确保目标目录存在
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            shutil.copy2(backup_file, target_file)
            print(f"恢复: {rel_path}")

print("恢复完成")
