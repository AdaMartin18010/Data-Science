#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 诊断工具：数据库完整性检查

> **工具类型**：诊断工具
> **适用版本**：SQLite 3.31+
"""

import sqlite3
import sys
import os

def check_integrity(db_path):
    """检查数据库完整性"""
    print("=" * 60)
    print(f"数据库完整性检查：{db_path}")
    print("=" * 60)
    print()
    
    if not os.path.exists(db_path):
        print(f"❌ 错误：数据库文件不存在：{db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            # 快速检查
            print("1. 快速检查（quick_check）...")
            result = conn.execute('PRAGMA quick_check').fetchone()[0]
            if result == 'ok':
                print("   ✅ 快速检查通过")
            else:
                print(f"   ❌ 快速检查失败：{result}")
                return False
            
            print()
            
            # 完整检查
            print("2. 完整检查（integrity_check）...")
            result = conn.execute('PRAGMA integrity_check').fetchone()[0]
            if result == 'ok':
                print("   ✅ 完整检查通过")
            else:
                print(f"   ❌ 完整检查失败：{result}")
                return False
            
            print()
            
            # 检查数据库信息
            print("3. 数据库信息...")
            page_size = conn.execute('PRAGMA page_size').fetchone()[0]
            page_count = conn.execute('PRAGMA page_count').fetchone()[0]
            db_size = page_size * page_count
            
            print(f"   页大小：{page_size} bytes")
            print(f"   页数量：{page_count}")
            print(f"   数据库大小：{db_size / 1024 / 1024:.2f} MB")
            
            print()
            
            # 检查WAL文件
            wal_path = db_path + '-wal'
            if os.path.exists(wal_path):
                wal_size = os.path.getsize(wal_path)
                print(f"4. WAL文件信息...")
                print(f"   WAL文件大小：{wal_size / 1024 / 1024:.2f} MB")
                
                # Checkpoint状态
                checkpoint = conn.execute('PRAGMA wal_checkpoint').fetchone()[0]
                print(f"   Checkpoint状态：{checkpoint}")
            
            print()
            print("=" * 60)
            print("✅ 数据库完整性检查完成")
            print("=" * 60)
            return True
            
    except sqlite3.Error as e:
        print(f"❌ 错误：{e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法：python 01-完整性检查.py <database.db>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    check_integrity(db_path)

if __name__ == '__main__':
    main()
