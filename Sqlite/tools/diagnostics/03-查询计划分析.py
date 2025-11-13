#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 诊断工具：查询计划分析

> **工具类型**：诊断工具
> **适用版本**：SQLite 3.31+
"""

import sqlite3
import sys
import os

def analyze_query_plan(db_path, query):
    """分析查询计划"""
    print("=" * 60)
    print(f"查询计划分析：{db_path}")
    print("=" * 60)
    print()
    
    if not os.path.exists(db_path):
        print(f"❌ 错误：数据库文件不存在：{db_path}")
        return
    
    print(f"查询语句：{query}")
    print()
    
    try:
        with sqlite3.connect(db_path) as conn:
            # 获取查询计划
            print("查询计划（EXPLAIN QUERY PLAN）：")
            print("-" * 60)
            
            plan_query = f"EXPLAIN QUERY PLAN {query}"
            plan = conn.execute(plan_query).fetchall()
            
            for row in plan:
                indent = "  " * row[0]  # 使用selectid作为缩进
                print(f"{indent}{row[3]}")
                if row[4]:
                    print(f"{indent}  └─ {row[4]}")
            
            print()
            print("-" * 60)
            
            # 分析查询计划
            print("\n查询计划分析：")
            
            plan_text = "\n".join([row[3] for row in plan])
            
            if "SCAN TABLE" in plan_text:
                print("   ⚠️  检测到全表扫描（SCAN TABLE）")
                print("   建议：为WHERE条件创建索引")
            elif "SEARCH TABLE" in plan_text:
                print("   ✅ 使用索引查找（SEARCH TABLE）")
            elif "USING COVERING INDEX" in plan_text:
                print("   ✅ 使用覆盖索引（COVERING INDEX）")
                print("   这是最优的查询方式")
            elif "USING INDEX" in plan_text:
                print("   ✅ 使用索引（USING INDEX）")
            
            print()
            print("=" * 60)
            print("✅ 查询计划分析完成")
            print("=" * 60)
            
    except sqlite3.Error as e:
        print(f"❌ 错误：{e}")

def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法：python 03-查询计划分析.py <database.db> <query>")
        print("示例：python 03-查询计划分析.py app.db \"SELECT * FROM users WHERE id = 123\"")
        sys.exit(1)
    
    db_path = sys.argv[1]
    query = sys.argv[2]
    analyze_query_plan(db_path, query)

if __name__ == '__main__':
    main()
