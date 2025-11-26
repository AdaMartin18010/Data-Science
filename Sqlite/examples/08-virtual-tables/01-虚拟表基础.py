#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 虚拟表示例 - 基础使用

演示SQLite虚拟表的基础使用：
- 虚拟表概念
- 使用内置虚拟表（FTS5、rtree）
- 虚拟表查询

适用版本：SQLite 3.31+ 至 3.47.x
最后更新：2025-01-15
"""

import sqlite3
from pathlib import Path

# 创建示例数据库
db_path = Path("virtual_tables_basic_example.db")
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 60)
print("SQLite 虚拟表示例 - 基础使用")
print("=" * 60)

# 1. 虚拟表概念说明
print("\n1. 虚拟表概念")
print("虚拟表是SQLite的一种特殊表类型，数据不存储在数据库中，")
print("而是通过回调函数动态生成。常见的虚拟表包括：")
print("  - FTS5：全文搜索虚拟表")
print("  - rtree：空间索引虚拟表")
print("  - 自定义虚拟表：通过扩展实现")

# 2. 使用FTS5虚拟表（全文搜索）
print("\n2. 使用FTS5虚拟表（全文搜索）")
cursor.execute("""
    CREATE VIRTUAL TABLE documents_fts USING fts5(
        title,
        content
    )
""")

cursor.executemany("""
    INSERT INTO documents_fts (title, content)
    VALUES (?, ?)
""", [
    ("SQLite性能优化", "SQLite是一个轻量级数据库，本文介绍性能优化技巧。"),
    ("Python编程指南", "Python是流行的编程语言，本文介绍Python编程实践。"),
    ("数据库设计原则", "良好的数据库设计是应用成功的关键。"),
])

print("✅ FTS5虚拟表创建并插入数据")

# 3. 查询FTS5虚拟表
print("\n3. 查询FTS5虚拟表")
cursor.execute("""
    SELECT title, snippet(documents_fts, 1, '<b>', '</b>', '...', 30)
    FROM documents_fts
    WHERE documents_fts MATCH 'SQLite'
""")
print("搜索'SQLite':")
for row in cursor.fetchall():
    print(f"  标题: {row[0]} | 摘要: {row[1]}")

# 4. 使用rtree虚拟表（空间索引）
print("\n4. 使用rtree虚拟表（空间索引）")
try:
    cursor.execute("""
        CREATE VIRTUAL TABLE locations USING rtree(
            id,
            minX, maxX,
            minY, maxY
        )
    """)
    
    # 插入空间数据（矩形区域）
    cursor.executemany("""
        INSERT INTO locations (id, minX, maxX, minY, maxY)
        VALUES (?, ?, ?, ?, ?)
    """, [
        (1, 0, 10, 0, 10),      # 区域1: (0,0) 到 (10,10)
        (2, 5, 15, 5, 15),      # 区域2: (5,5) 到 (15,15)
        (3, 20, 30, 20, 30),    # 区域3: (20,20) 到 (30,30)
    ])
    
    print("✅ rtree虚拟表创建并插入数据")
    
    # 查询重叠区域
    print("\n查询与区域(3,3,12,12)重叠的区域:")
    cursor.execute("""
        SELECT id, minX, maxX, minY, maxY
        FROM locations
        WHERE minX <= 12 AND maxX >= 3
          AND minY <= 12 AND maxY >= 3
    """)
    for row in cursor.fetchall():
        print(f"  区域{row[0]}: ({row[1]},{row[2]}) x ({row[3]},{row[4]})")
        
except sqlite3.OperationalError as e:
    print(f"⚠️  rtree扩展可能未启用: {e}")

# 5. 查看虚拟表信息
print("\n5. 查看虚拟表信息")
cursor.execute("""
    SELECT name, sql
    FROM sqlite_master
    WHERE type = 'table' AND sql LIKE '%VIRTUAL%'
""")
print("虚拟表列表:")
for row in cursor.fetchall():
    print(f"  表名: {row[0]}")
    print(f"  SQL: {row[1][:80]}...")
    print()

# 6. 虚拟表与普通表的区别
print("\n6. 虚拟表与普通表的区别")
print("虚拟表特点:")
print("  - 数据不存储在数据库中")
print("  - 通过回调函数动态生成数据")
print("  - 可以访问外部数据源")
print("  - 支持自定义查询逻辑")
print("  - 可以与其他表JOIN")

# 7. 虚拟表性能考虑
print("\n7. 虚拟表性能考虑")
print("虚拟表性能特点:")
print("  - 查询性能取决于实现")
print("  - 可以缓存数据提高性能")
print("  - 支持索引优化")
print("  - 适合数据转换和集成场景")

# 清理
conn.close()
if db_path.exists():
    db_path.unlink()
    print(f"\n✅ 清理完成，已删除 {db_path}")

print("\n" + "=" * 60)
print("示例完成！")
print("=" * 60)
print("\n💡 虚拟表要点:")
print("  1. 虚拟表数据不存储在数据库中")
print("  2. 通过回调函数动态生成数据")
print("  3. 可以访问外部数据源")
print("  4. 支持自定义查询逻辑")
print("  5. 适合数据集成和转换场景")
