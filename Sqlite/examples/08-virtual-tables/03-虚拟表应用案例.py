#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 虚拟表示例 - 应用案例

演示虚拟表的实际应用案例：
- CSV文件虚拟表（概念）
- 内存数据虚拟表
- 外部数据源集成

注意：完整的虚拟表实现需要使用C/C++扩展或Python扩展模块。
本示例展示应用场景和设计思路。

适用版本：SQLite 3.31+ 至 3.47.x
最后更新：2025-01-15
"""

import sqlite3
import csv
import json
from pathlib import Path
from typing import List, Dict

# 创建示例数据库
db_path = Path("virtual_tables_app_example.db")
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 60)
print("SQLite 虚拟表示例 - 应用案例")
print("=" * 60)

# 1. CSV文件虚拟表（概念示例）
print("\n1. CSV文件虚拟表（概念示例）")
print("""
虚拟表可以用于直接查询CSV文件，无需导入数据库：

CREATE VIRTUAL TABLE csv_data USING csv(
    filename = 'data.csv',
    columns = 'id INTEGER, name TEXT, value REAL'
);

SELECT * FROM csv_data WHERE value > 100;
""")

# 创建CSV文件
csv_file = Path("sample_data.csv")
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'name', 'value'])
    writer.writerows([
        [1, 'Item A', 100.5],
        [2, 'Item B', 200.3],
        [3, 'Item C', 150.8],
    ])

print(f"✅ 创建示例CSV文件: {csv_file}")

# 模拟CSV查询（实际需要使用虚拟表扩展）
print("\n模拟CSV数据查询:")
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if float(row['value']) > 100:
            print(f"  ID: {row['id']}, 名称: {row['name']}, 值: {row['value']}")

# 2. 内存数据虚拟表（使用临时表模拟）
print("\n2. 内存数据虚拟表（使用临时表模拟）")
cursor.execute("""
    CREATE TEMP TABLE memory_data (
        id INTEGER PRIMARY KEY,
        key TEXT NOT NULL,
        value TEXT NOT NULL
    )
""")

# 插入内存数据
memory_items = [
    ('config1', 'value1'),
    ('config2', 'value2'),
    ('config3', 'value3'),
]

cursor.executemany("""
    INSERT INTO memory_data (key, value)
    VALUES (?, ?)
""", memory_items)

print("✅ 内存数据表创建并插入数据")

# 查询内存数据
cursor.execute("SELECT * FROM memory_data")
print("\n内存数据查询结果:")
for row in cursor.fetchall():
    print(f"  ID: {row[0]}, 键: {row[1]}, 值: {row[2]}")

# 3. JSON数据虚拟表（概念示例）
print("\n3. JSON数据虚拟表（概念示例）")
print("""
虚拟表可以用于直接查询JSON文件：

CREATE VIRTUAL TABLE json_data USING json(
    filename = 'data.json',
    root = '$.items'
);

SELECT * FROM json_data WHERE category = 'electronics';
""")

# 创建JSON文件
json_file = Path("sample_data.json")
json_data = {
    'items': [
        {'id': 1, 'name': 'Product A', 'category': 'electronics', 'price': 99.99},
        {'id': 2, 'name': 'Product B', 'category': 'books', 'price': 19.99},
        {'id': 3, 'name': 'Product C', 'category': 'electronics', 'price': 149.99},
    ]
}

with open(json_file, 'w', encoding='utf-8') as f:
    json.dump(json_data, f, ensure_ascii=False, indent=2)

print(f"✅ 创建示例JSON文件: {json_file}")

# 模拟JSON查询
print("\n模拟JSON数据查询:")
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)
    for item in data['items']:
        if item['category'] == 'electronics':
            print(f"  ID: {item['id']}, 名称: {item['name']}, 价格: ${item['price']}")

# 4. 使用FTS5作为文档搜索虚拟表
print("\n4. 使用FTS5作为文档搜索虚拟表")
cursor.execute("""
    CREATE VIRTUAL TABLE documents_fts USING fts5(
        title,
        content,
        metadata
    )
""")

documents = [
    ("技术文档1", "SQLite是一个轻量级数据库", '{"author": "张三", "date": "2025-01-01"}'),
    ("技术文档2", "Python是流行的编程语言", '{"author": "李四", "date": "2025-01-02"}'),
    ("技术文档3", "数据库设计很重要", '{"author": "王五", "date": "2025-01-03"}'),
]

cursor.executemany("""
    INSERT INTO documents_fts (title, content, metadata)
    VALUES (?, ?, ?)
""", documents)

print("✅ 文档搜索虚拟表创建并插入数据")

# 搜索文档
print("\n搜索'数据库':")
cursor.execute("""
    SELECT 
        title,
        snippet(documents_fts, 1, '<b>', '</b>', '...', 30) as snippet,
        metadata
    FROM documents_fts
    WHERE documents_fts MATCH '数据库'
    ORDER BY bm25(documents_fts)
""")
for row in cursor.fetchall():
    print(f"  标题: {row[0]}")
    print(f"  摘要: {row[1]}")
    print(f"  元数据: {row[2]}")
    print()

# 5. 虚拟表数据聚合
print("\n5. 虚拟表数据聚合")
print("虚拟表可以用于数据聚合和统计:")
cursor.execute("""
    SELECT 
        COUNT(*) as total_docs,
        COUNT(DISTINCT json_extract(metadata, '$.author')) as total_authors
    FROM documents_fts
""")
row = cursor.fetchone()
print(f"  总文档数: {row[0]}")
print(f"  总作者数: {row[1]}")

# 6. 虚拟表性能优化建议
print("\n6. 虚拟表性能优化建议")
print("虚拟表性能优化策略:")
print("  1. 实现索引支持（xBestIndex方法）")
print("  2. 缓存常用查询结果")
print("  3. 批量处理数据读取")
print("  4. 使用连接池管理连接")
print("  5. 优化查询条件过滤逻辑")
print("  6. 实现数据预加载机制")

# 7. 虚拟表应用场景总结
print("\n7. 虚拟表应用场景总结")
print("虚拟表适用于以下场景:")
print("  ✅ 外部文件查询（CSV、JSON、XML）")
print("  ✅ 全文搜索（FTS5）")
print("  ✅ 空间数据查询（rtree）")
print("  ✅ 内存数据查询")
print("  ✅ API数据集成")
print("  ✅ 数据转换和格式化")
print("  ✅ 实时数据查询")

# 清理
conn.close()
if csv_file.exists():
    csv_file.unlink()
if json_file.exists():
    json_file.unlink()
if db_path.exists():
    db_path.unlink()
    print(f"\n✅ 清理完成，已删除所有临时文件")

print("\n" + "=" * 60)
print("示例完成！")
print("=" * 60)
print("\n💡 虚拟表应用要点:")
print("  1. 适合外部数据源集成")
print("  2. 可以实现数据转换和查询")
print("  3. 支持复杂查询逻辑")
print("  4. 需要仔细设计性能优化")
print("  5. 可以使用现有扩展（FTS5、rtree）")
