#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite FTS5全文搜索示例 - 基础搜索

演示FTS5全文搜索的基本功能：
- FTS5表创建
- 基本搜索查询
- 多词搜索（AND/OR）
- 短语搜索
- 前缀搜索

适用版本：SQLite 3.31+（需要FTS5扩展）
"""

import sqlite3
from pathlib import Path

# 创建示例数据库
db_path = Path("fts5_basic_example.db")
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 60)
print("SQLite FTS5全文搜索示例 - 基础搜索")
print("=" * 60)

# 1. 创建FTS5虚拟表
print("\n1. 创建FTS5虚拟表")
cursor.execute("""
    CREATE VIRTUAL TABLE articles_fts USING fts5(
        title,
        content,
        author,
        tags
    )
""")
print("✅ FTS5表创建成功")

# 2. 插入测试数据
print("\n2. 插入测试数据")
articles = [
    ("SQLite性能优化指南", 
     "SQLite是一个轻量级的嵌入式数据库，本文介绍如何优化SQLite的性能，包括索引优化、查询优化和WAL模式的使用。",
     "张三",
     "SQLite 性能 优化 数据库"),
    ("Python数据库编程实践",
     "Python提供了多种数据库接口，包括sqlite3标准库。本文介绍如何使用Python进行数据库编程，包括连接管理、事务处理和错误处理。",
     "李四",
     "Python 数据库 编程 实践"),
    ("SQLite WAL模式详解",
     "WAL（Write-Ahead Logging）模式是SQLite提供的一种日志模式，可以显著提高并发性能。本文详细介绍WAL模式的原理和使用方法。",
     "王五",
     "SQLite WAL 并发 日志"),
    ("数据库索引设计原则",
     "索引是提高数据库查询性能的重要手段。本文介绍数据库索引的设计原则，包括何时创建索引、如何选择索引字段和索引维护。",
     "赵六",
     "数据库 索引 设计 性能"),
    ("SQLite JSON扩展使用",
     "SQLite提供了JSON1扩展，支持JSON数据的存储和查询。本文介绍如何使用JSON扩展，包括JSON函数和JSON路径查询。",
     "张三",
     "SQLite JSON 扩展 数据"),
]

cursor.executemany("""
    INSERT INTO articles_fts (title, content, author, tags)
    VALUES (?, ?, ?, ?)
""", articles)
conn.commit()
print(f"✅ 插入 {len(articles)} 条文章记录")

# 3. 基本搜索
print("\n3. 基本搜索")
print("搜索包含'SQLite'的文章:")
cursor.execute("""
    SELECT title, author, snippet(articles_fts, 2, '<b>', '</b>', '...', 32) as snippet
    FROM articles_fts
    WHERE articles_fts MATCH 'SQLite'
    ORDER BY rank
""")
print("-" * 80)
for row in cursor.fetchall():
    print(f"标题: {row[0]}")
    print(f"作者: {row[1]}")
    print(f"摘要: {row[2]}")
    print()

# 4. 多词搜索（AND）
print("\n4. 多词搜索（AND）")
print("搜索同时包含'SQLite'和'性能'的文章:")
cursor.execute("""
    SELECT title, author
    FROM articles_fts
    WHERE articles_fts MATCH 'SQLite AND 性能'
    ORDER BY rank
""")
print("-" * 60)
for row in cursor.fetchall():
    print(f"标题: {row[0]} | 作者: {row[1]}")

# 5. 多词搜索（OR）
print("\n5. 多词搜索（OR）")
print("搜索包含'SQLite'或'Python'的文章:")
cursor.execute("""
    SELECT title, author
    FROM articles_fts
    WHERE articles_fts MATCH 'SQLite OR Python'
    ORDER BY rank
""")
print("-" * 60)
for row in cursor.fetchall():
    print(f"标题: {row[0]} | 作者: {row[1]}")

# 6. 短语搜索
print("\n6. 短语搜索")
print("搜索包含短语'性能优化'的文章:")
cursor.execute("""
    SELECT title, author, snippet(articles_fts, 2, '<b>', '</b>', '...', 32) as snippet
    FROM articles_fts
    WHERE articles_fts MATCH '"性能优化"'
    ORDER BY rank
""")
print("-" * 80)
for row in cursor.fetchall():
    print(f"标题: {row[0]}")
    print(f"作者: {row[1]}")
    print(f"摘要: {row[2]}")
    print()

# 7. 前缀搜索
print("\n7. 前缀搜索")
print("搜索以'SQL'开头的词:")
cursor.execute("""
    SELECT title, author
    FROM articles_fts
    WHERE articles_fts MATCH 'SQL*'
    ORDER BY rank
""")
print("-" * 60)
for row in cursor.fetchall():
    print(f"标题: {row[0]} | 作者: {row[1]}")

# 8. 排除词搜索（NOT）
print("\n8. 排除词搜索（NOT）")
print("搜索包含'数据库'但不包含'Python'的文章:")
cursor.execute("""
    SELECT title, author
    FROM articles_fts
    WHERE articles_fts MATCH '数据库 NOT Python'
    ORDER BY rank
""")
print("-" * 60)
for row in cursor.fetchall():
    print(f"标题: {row[0]} | 作者: {row[1]}")

# 9. 列限定搜索
print("\n9. 列限定搜索")
print("在标题中搜索'SQLite':")
cursor.execute("""
    SELECT title, author
    FROM articles_fts
    WHERE articles_fts MATCH 'title:SQLite'
    ORDER BY rank
""")
print("-" * 60)
for row in cursor.fetchall():
    print(f"标题: {row[0]} | 作者: {row[1]}")

# 10. 复杂搜索表达式
print("\n10. 复杂搜索表达式")
print("搜索包含('SQLite'或'数据库')和'优化'的文章:")
cursor.execute("""
    SELECT title, author
    FROM articles_fts
    WHERE articles_fts MATCH '(SQLite OR 数据库) AND 优化'
    ORDER BY rank
""")
print("-" * 60)
for row in cursor.fetchall():
    print(f"标题: {row[0]} | 作者: {row[1]}")

# 11. 搜索统计
print("\n11. 搜索统计")
cursor.execute("""
    SELECT 
        COUNT(*) as total_articles,
        COUNT(DISTINCT author) as total_authors
    FROM articles_fts
""")
row = cursor.fetchone()
print(f"总文章数: {row[0]}")
print(f"总作者数: {row[1]}")

# 12. 查看FTS5表结构
print("\n12. 查看FTS5表结构")
cursor.execute("""
    SELECT name, sql
    FROM sqlite_master
    WHERE type='table' AND name LIKE '%fts%'
""")
for row in cursor.fetchall():
    print(f"表名: {row[0]}")
    print(f"SQL: {row[1][:100]}...")
    print()

# 清理
conn.close()
if db_path.exists():
    db_path.unlink()
    print(f"✅ 清理完成，已删除 {db_path}")

print("\n" + "=" * 60)
print("示例完成！")
print("=" * 60)
print("\n💡 FTS5搜索要点:")
print("  1. MATCH操作符用于全文搜索")
print("  2. AND/OR/NOT支持布尔逻辑")
print("  3. 双引号表示短语搜索")
print("  4. 星号(*)表示前缀搜索")
print("  5. 列名:关键词 限定搜索列")
