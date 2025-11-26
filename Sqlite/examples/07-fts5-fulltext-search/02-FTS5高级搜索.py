#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite FTS5全文搜索示例 - 高级搜索

演示FTS5全文搜索的高级功能：
- 排名算法（bm25）
- 高亮显示
- 多列搜索
- 搜索优化
- 搜索统计

适用版本：SQLite 3.31+ 至 3.47.x
最后更新：2025-01-15（需要FTS5扩展）
"""

import sqlite3
from pathlib import Path

# 创建示例数据库
db_path = Path("fts5_advanced_example.db")
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 60)
print("SQLite FTS5全文搜索示例 - 高级搜索")
print("=" * 60)

# 1. 创建FTS5表（带配置）
print("\n1. 创建FTS5表（带配置）")
cursor.execute("""
    CREATE VIRTUAL TABLE documents_fts USING fts5(
        title,
        content,
        category,
        tokenize = 'unicode61'  -- Unicode分词器
    )
""")
print("✅ FTS5表创建成功（Unicode分词器）")

# 2. 插入测试数据
print("\n2. 插入测试数据")
documents = [
    ("SQLite数据库性能优化", 
     "SQLite是一个轻量级的嵌入式数据库系统，广泛应用于移动应用和桌面应用。本文详细介绍SQLite的性能优化技巧，包括索引优化、查询优化和WAL模式配置。通过合理的优化，SQLite可以处理大量数据并提供良好的查询性能。",
     "技术文档"),
    ("Python Web开发实战",
     "Python是流行的Web开发语言，Django和Flask是常用的Web框架。本文介绍如何使用Python进行Web开发，包括路由设计、模板引擎和数据库集成。通过实际案例展示Python Web开发的最佳实践。",
     "编程教程"),
    ("数据库设计原则与实践",
     "良好的数据库设计是应用成功的关键。本文介绍数据库设计的基本原则，包括范式化、反范式化和索引设计。通过实际案例展示如何设计高效的数据库结构，提高查询性能和数据完整性。",
     "技术文档"),
    ("SQLite并发控制机制",
     "SQLite通过WAL模式实现了高效的并发控制。本文详细介绍SQLite的并发控制机制，包括锁机制、事务隔离级别和WAL模式的工作原理。了解这些机制有助于更好地使用SQLite处理并发场景。",
     "技术文档"),
    ("全文搜索技术详解",
     "全文搜索是现代应用的重要功能。本文介绍全文搜索的基本原理，包括倒排索引、分词技术和排名算法。通过SQLite的FTS5扩展，可以轻松实现高效的全文搜索功能。",
     "技术文档"),
]

cursor.executemany("""
    INSERT INTO documents_fts (title, content, category)
    VALUES (?, ?, ?)
""", documents)
conn.commit()
print(f"✅ 插入 {len(documents)} 条文档记录")

# 3. 使用bm25()排名函数
print("\n3. 使用bm25()排名函数")
print("搜索'数据库'，按相关性排序:")
cursor.execute("""
    SELECT 
        title,
        category,
        bm25(documents_fts) as relevance_score,
        snippet(documents_fts, 1, '<mark>', '</mark>', '...', 40) as snippet
    FROM documents_fts
    WHERE documents_fts MATCH '数据库'
    ORDER BY bm25(documents_fts)
    LIMIT 5
""")
print("-" * 80)
for row in cursor.fetchall():
    print(f"标题: {row[0]}")
    print(f"分类: {row[1]}")
    print(f"相关性: {row[2]:.4f}")
    print(f"摘要: {row[3]}")
    print()

# 4. 高亮显示搜索结果
print("\n4. 高亮显示搜索结果")
print("搜索'SQLite'，高亮显示匹配内容:")
cursor.execute("""
    SELECT 
        title,
        highlight(documents_fts, 0, '<b>', '</b>') as highlighted_title,
        highlight(documents_fts, 1, '<mark>', '</mark>') as highlighted_content
    FROM documents_fts
    WHERE documents_fts MATCH 'SQLite'
    ORDER BY bm25(documents_fts)
""")
print("-" * 80)
for row in cursor.fetchall():
    print(f"标题: {row[1]}")
    print(f"内容: {row[2][:200]}...")
    print()

# 5. 多列搜索和权重
print("\n5. 多列搜索和权重")
print("搜索'性能'，标题权重更高:")
cursor.execute("""
    SELECT 
        title,
        category,
        bm25(documents_fts) as score
    FROM documents_fts
    WHERE documents_fts MATCH 'title:性能 OR content:性能'
    ORDER BY bm25(documents_fts)
""")
print("-" * 80)
for row in cursor.fetchall():
    print(f"标题: {row[0]} | 分类: {row[1]} | 得分: {row[2]:.4f}")

# 6. 搜索统计信息
print("\n6. 搜索统计信息")
cursor.execute("""
    SELECT 
        COUNT(*) as total_docs,
        COUNT(DISTINCT category) as total_categories
    FROM documents_fts
""")
row = cursor.fetchone()
print(f"总文档数: {row[0]}")
print(f"总分类数: {row[1]}")

# 7. 搜索词频统计
print("\n7. 搜索词频统计")
print("统计'数据库'在文档中的出现次数:")
cursor.execute("""
    SELECT 
        title,
        (LENGTH(content) - LENGTH(REPLACE(content, '数据库', ''))) / LENGTH('数据库') as word_count
    FROM documents_fts
    WHERE documents_fts MATCH '数据库'
    ORDER BY word_count DESC
""")
print("-" * 60)
for row in cursor.fetchall():
    print(f"标题: {row[0]} | 出现次数: {row[1]}")

# 8. 模糊搜索（使用前缀）
print("\n8. 模糊搜索（使用前缀）")
print("搜索以'SQL'开头的词:")
cursor.execute("""
    SELECT 
        title,
        snippet(documents_fts, 1, '<b>', '</b>', '...', 40) as snippet
    FROM documents_fts
    WHERE documents_fts MATCH 'SQL*'
    ORDER BY bm25(documents_fts)
""")
print("-" * 80)
for row in cursor.fetchall():
    print(f"标题: {row[0]}")
    print(f"摘要: {row[1]}")
    print()

# 9. 组合搜索（多条件）
print("\n9. 组合搜索（多条件）")
print("搜索包含('数据库'或'SQLite')和'性能'的文档:")
cursor.execute("""
    SELECT 
        title,
        category,
        bm25(documents_fts) as score
    FROM documents_fts
    WHERE documents_fts MATCH '(数据库 OR SQLite) AND 性能'
    ORDER BY bm25(documents_fts)
""")
print("-" * 60)
for row in cursor.fetchall():
    print(f"标题: {row[0]} | 分类: {row[1]} | 得分: {row[2]:.4f}")

# 10. 搜索性能测试
print("\n10. 搜索性能测试")
import time

search_terms = ['数据库', 'SQLite', '性能', '优化', '开发']

for term in search_terms:
    start_time = time.time()
    cursor.execute("""
        SELECT COUNT(*) 
        FROM documents_fts
        WHERE documents_fts MATCH ?
    """, (term,))
    result = cursor.fetchone()[0]
    elapsed = time.time() - start_time
    print(f"搜索'{term}': {result} 条结果, 耗时: {elapsed*1000:.2f}ms")

# 11. 搜索建议（查找相似词）
print("\n11. 搜索建议（查找相似词）")
print("查找包含'数据'的文档（前缀匹配）:")
cursor.execute("""
    SELECT DISTINCT
        title
    FROM documents_fts
    WHERE documents_fts MATCH '数据*'
    LIMIT 5
""")
print("-" * 60)
for row in cursor.fetchall():
    print(f"  - {row[0]}")

# 12. 高级snippet配置
print("\n12. 高级snippet配置")
print("自定义snippet格式:")
cursor.execute("""
    SELECT 
        title,
        snippet(
            documents_fts, 
            1,              -- content列（索引从0开始）
            '[',            -- 开始标记
            ']',            -- 结束标记
            '...',          -- 省略标记
            50              -- 最大字符数
        ) as custom_snippet
    FROM documents_fts
    WHERE documents_fts MATCH 'SQLite'
    ORDER BY bm25(documents_fts)
    LIMIT 3
""")
print("-" * 80)
for row in cursor.fetchall():
    print(f"标题: {row[0]}")
    print(f"摘要: {row[1]}")
    print()

# 清理
conn.close()
if db_path.exists():
    db_path.unlink()
    print(f"✅ 清理完成，已删除 {db_path}")

print("\n" + "=" * 60)
print("示例完成！")
print("=" * 60)
print("\n💡 FTS5高级搜索要点:")
print("  1. bm25()函数用于计算相关性排名")
print("  2. highlight()函数用于高亮显示")
print("  3. snippet()函数用于生成摘要")
print("  4. 可以自定义标记和格式")
print("  5. 多列搜索支持列限定")
