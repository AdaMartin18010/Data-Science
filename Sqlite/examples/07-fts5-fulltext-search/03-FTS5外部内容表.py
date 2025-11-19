#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite FTS5全文搜索示例 - 外部内容表

演示FTS5外部内容表的使用：
- 外部内容表配置
- 避免数据冗余
- 触发器同步
- 性能优化

适用版本：SQLite 3.31+（需要FTS5扩展）
"""

import sqlite3
from pathlib import Path

# 创建示例数据库
db_path = Path("fts5_external_content_example.db")
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 60)
print("SQLite FTS5全文搜索示例 - 外部内容表")
print("=" * 60)

# 1. 创建主表（存储完整数据）
print("\n1. 创建主表（存储完整数据）")
cursor.execute("""
    CREATE TABLE articles (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        author TEXT NOT NULL,
        category TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )
""")
print("✅ 主表创建成功")

# 2. 创建FTS5表（外部内容表模式）
print("\n2. 创建FTS5表（外部内容表模式）")
cursor.execute("""
    CREATE VIRTUAL TABLE articles_fts USING fts5(
        title,
        content,
        author,
        category,
        content = 'articles',      -- 外部内容表
        content_rowid = 'id'       -- 行ID列
    )
""")
print("✅ FTS5表创建成功（外部内容表模式）")

# 3. 创建触发器（自动同步）
print("\n3. 创建触发器（自动同步）")
# INSERT触发器
cursor.execute("""
    CREATE TRIGGER articles_fts_insert AFTER INSERT ON articles BEGIN
        INSERT INTO articles_fts(rowid, title, content, author, category)
        VALUES (NEW.id, NEW.title, NEW.content, NEW.author, NEW.category);
    END;
""")

# UPDATE触发器
cursor.execute("""
    CREATE TRIGGER articles_fts_update AFTER UPDATE ON articles BEGIN
        UPDATE articles_fts SET
            title = NEW.title,
            content = NEW.content,
            author = NEW.author,
            category = NEW.category
        WHERE rowid = NEW.id;
    END;
""")

# DELETE触发器
cursor.execute("""
    CREATE TRIGGER articles_fts_delete AFTER DELETE ON articles BEGIN
        DELETE FROM articles_fts WHERE rowid = OLD.id;
    END;
""")
print("✅ 触发器创建成功（INSERT/UPDATE/DELETE）")

# 4. 插入数据（只插入主表，FTS5表自动同步）
print("\n4. 插入数据（只插入主表，FTS5表自动同步）")
articles = [
    ("SQLite性能优化完全指南",
     "SQLite是一个轻量级的嵌入式数据库，本文详细介绍SQLite的性能优化技巧，包括索引设计、查询优化、WAL模式配置和PRAGMA参数调优。通过合理的优化，SQLite可以处理大量数据并提供优秀的查询性能。",
     "技术专家",
     "技术文档"),
    ("Python数据库编程最佳实践",
     "Python提供了sqlite3标准库用于SQLite数据库操作。本文介绍Python数据库编程的最佳实践，包括连接管理、事务处理、错误处理和性能优化。通过实际案例展示如何编写高效的数据库代码。",
     "编程导师",
     "编程教程"),
    ("数据库索引设计原理",
     "索引是提高数据库查询性能的关键技术。本文深入讲解数据库索引的设计原理，包括B-Tree索引、哈希索引和全文索引。了解索引原理有助于设计高效的数据库结构。",
     "数据库专家",
     "技术文档"),
]

cursor.executemany("""
    INSERT INTO articles (title, content, author, category)
    VALUES (?, ?, ?, ?)
""", articles)
conn.commit()
print(f"✅ 插入 {len(articles)} 条文章记录（FTS5表自动同步）")

# 5. 验证FTS5表数据
print("\n5. 验证FTS5表数据")
cursor.execute("SELECT COUNT(*) FROM articles_fts")
count = cursor.fetchone()[0]
print(f"FTS5表记录数: {count}（应与主表一致）")

# 6. 使用FTS5搜索（从外部内容表读取完整数据）
print("\n6. 使用FTS5搜索（从外部内容表读取完整数据）")
print("搜索'SQLite':")
cursor.execute("""
    SELECT 
        a.id,
        a.title,
        a.author,
        a.category,
        snippet(articles_fts, 1, '<b>', '</b>', '...', 50) as snippet
    FROM articles_fts
    JOIN articles a ON articles_fts.rowid = a.id
    WHERE articles_fts MATCH 'SQLite'
    ORDER BY bm25(articles_fts)
""")
print("-" * 80)
for row in cursor.fetchall():
    print(f"ID: {row[0]}")
    print(f"标题: {row[1]}")
    print(f"作者: {row[2]} | 分类: {row[3]}")
    print(f"摘要: {row[4]}")
    print()

# 7. 更新主表数据（FTS5表自动同步）
print("\n7. 更新主表数据（FTS5表自动同步）")
cursor.execute("""
    UPDATE articles
    SET content = content || ' 本文已更新，增加了更多实用技巧。',
        updated_at = datetime('now')
    WHERE id = 1
""")
conn.commit()
print("✅ 更新主表数据（FTS5表自动同步）")

# 验证更新
cursor.execute("""
    SELECT 
        a.content,
        snippet(articles_fts, 1, '<b>', '</b>', '...', 50) as fts_snippet
    FROM articles a
    JOIN articles_fts ON articles_fts.rowid = a.id
    WHERE a.id = 1
""")
row = cursor.fetchone()
print(f"主表内容长度: {len(row[0])} 字符")
print(f"FTS5摘要: {row[1]}")

# 8. 删除主表数据（FTS5表自动同步）
print("\n8. 删除主表数据（FTS5表自动同步）")
cursor.execute("DELETE FROM articles WHERE id = 3")
conn.commit()
print("✅ 删除主表数据（FTS5表自动同步）")

cursor.execute("SELECT COUNT(*) FROM articles")
main_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM articles_fts")
fts_count = cursor.fetchone()[0]
print(f"主表记录数: {main_count}")
print(f"FTS5表记录数: {fts_count}（应与主表一致）")

# 9. 存储空间对比
print("\n9. 存储空间对比")
cursor.execute("""
    SELECT 
        (SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size() WHERE name = 'articles') as main_table_size,
        (SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size() WHERE name = 'articles_fts') as fts_table_size
""")
# 注意：上面的查询可能不准确，这里仅作演示
print("存储空间说明:")
print("  - 主表：存储完整数据")
print("  - FTS5表：只存储索引，不存储完整内容（外部内容表模式）")
print("  - 节省存储空间，避免数据冗余")

# 10. 性能对比
print("\n10. 性能对比")
import time

# 搜索性能测试
start_time = time.time()
cursor.execute("""
    SELECT COUNT(*) 
    FROM articles_fts
    WHERE articles_fts MATCH '数据库'
""")
result = cursor.fetchone()[0]
search_time = time.time() - start_time
print(f"FTS5搜索性能: {result} 条结果, 耗时: {search_time*1000:.2f}ms")

# 11. 完整数据查询（从主表）
print("\n11. 完整数据查询（从主表）")
print("搜索'Python'，获取完整数据:")
cursor.execute("""
    SELECT 
        a.id,
        a.title,
        a.content,
        a.author,
        a.category,
        a.created_at,
        bm25(articles_fts) as relevance
    FROM articles_fts
    JOIN articles a ON articles_fts.rowid = a.id
    WHERE articles_fts MATCH 'Python'
    ORDER BY bm25(articles_fts)
""")
print("-" * 80)
for row in cursor.fetchall():
    print(f"ID: {row[0]}")
    print(f"标题: {row[1]}")
    print(f"作者: {row[2]} | 分类: {row[3]}")
    print(f"创建时间: {row[4]}")
    print(f"相关性: {row[5]:.4f}")
    print(f"内容: {row[2][:100]}...")
    print()

# 12. 触发器验证
print("\n12. 触发器验证")
print("查看触发器:")
cursor.execute("""
    SELECT name, sql
    FROM sqlite_master
    WHERE type = 'trigger' AND name LIKE 'articles_fts%'
""")
for row in cursor.fetchall():
    print(f"触发器: {row[0]}")
    print(f"SQL: {row[1][:80]}...")
    print()

# 清理
conn.close()
if db_path.exists():
    db_path.unlink()
    print(f"✅ 清理完成，已删除 {db_path}")

print("\n" + "=" * 60)
print("示例完成！")
print("=" * 60)
print("\n💡 外部内容表要点:")
print("  1. 避免数据冗余，节省存储空间")
print("  2. 主表存储完整数据，FTS5表只存储索引")
print("  3. 使用触发器自动同步数据")
print("  4. 搜索时从主表读取完整数据")
print("  5. 适合数据量大、存储空间敏感的场景")
