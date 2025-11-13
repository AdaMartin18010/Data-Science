#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 诊断工具：索引使用分析

> **工具类型**：诊断工具
> **适用版本**：SQLite 3.31+
"""

import sqlite3
import sys
import os

def analyze_indexes(db_path):
    """分析索引使用情况"""
    print("=" * 60)
    print(f"索引使用分析：{db_path}")
    print("=" * 60)
    print()
    
    if not os.path.exists(db_path):
        print(f"❌ 错误：数据库文件不存在：{db_path}")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            # 获取所有索引
            print("1. 索引列表...")
            indexes = conn.execute('''
                SELECT name, tbl_name, sql
                FROM sqlite_master
                WHERE type = 'index'
                AND name NOT LIKE 'sqlite_%'
                ORDER BY tbl_name, name
            ''').fetchall()
            
            if not indexes:
                print("   ⚠️  没有找到用户创建的索引")
            else:
                print(f"   找到 {len(indexes)} 个索引：")
                for idx in indexes:
                    print(f"   - {idx[0]} (表: {idx[1]})")
            
            print()
            
            # 获取表信息
            print("2. 表信息...")
            tables = conn.execute('''
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            ''').fetchall()
            
            for table in tables:
                table_name = table[0]
                print(f"\n   表：{table_name}")
                
                # 获取表的索引
                table_indexes = [idx for idx in indexes if idx[1] == table_name]
                if table_indexes:
                    print(f"   索引：")
                    for idx in table_indexes:
                        print(f"     - {idx[0]}")
                else:
                    print(f"   ⚠️  没有索引")
            
            print()
            
            # 建议
            print("3. 索引优化建议...")
            print("   - 为WHERE条件中的列创建索引")
            print("   - 为JOIN条件中的列创建索引")
            print("   - 考虑创建覆盖索引以减少回表查询")
            print("   - 使用部分索引减少索引大小")
            
            print()
            print("=" * 60)
            print("✅ 索引分析完成")
            print("=" * 60)
            
    except sqlite3.Error as e:
        print(f"❌ 错误：{e}")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法：python 02-索引使用分析.py <database.db>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    analyze_indexes(db_path)

if __name__ == '__main__':
    main()
