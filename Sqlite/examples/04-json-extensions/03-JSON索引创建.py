#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite JSON扩展示例 - 索引创建

演示如何为JSON字段创建索引以优化查询性能：
- 使用生成列创建JSON索引
- JSON字段查询性能对比
- 索引策略选择

适用版本：SQLite 3.31+（生成列需要3.31+）
"""

import sqlite3
import json
import time
from pathlib import Path

# 创建示例数据库
db_path = Path("json_index_example.db")
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 60)
print("SQLite JSON扩展示例 - 索引创建")
print("=" * 60)

# 1. 创建包含JSON列的表（无索引）
print("\n1. 创建包含JSON列的表（无索引）")
cursor.execute("""
    CREATE TABLE products_no_index (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        details TEXT  -- JSON字符串
    )
""")

# 2. 插入测试数据
print("\n2. 插入测试数据")
products = []
for i in range(1000):
    products.append((
        i + 1,
        f"产品{i+1}",
        json.dumps({
            "category": f"类别{(i % 10) + 1}",
            "brand": f"品牌{(i % 5) + 1}",
            "price": 100 + (i % 1000) * 10,
            "rating": 3.0 + (i % 20) / 10,
            "tags": [f"标签{j}" for j in range((i % 3) + 1)]
        })
    ))

cursor.executemany("""
    INSERT INTO products_no_index (id, name, details)
    VALUES (?, ?, ?)
""", products)
conn.commit()
print(f"✅ 插入 {len(products)} 条记录")

# 3. 测试无索引查询性能
print("\n3. 测试无索引查询性能")
start_time = time.time()
cursor.execute("""
    SELECT COUNT(*) 
    FROM products_no_index
    WHERE json_extract(details, '$.category') = '类别5'
""")
result_no_index = cursor.fetchone()[0]
time_no_index = time.time() - start_time
print(f"查询结果: {result_no_index} 条记录")
print(f"查询时间: {time_no_index:.4f} 秒（无索引）")

# 4. 创建带生成列和索引的表
print("\n4. 创建带生成列和索引的表")
cursor.execute("""
    CREATE TABLE products_with_index (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        details TEXT,  -- JSON字符串
        category TEXT GENERATED ALWAYS AS (json_extract(details, '$.category')) STORED,
        price INTEGER GENERATED ALWAYS AS (json_extract(details, '$.price')) STORED,
        rating REAL GENERATED ALWAYS AS (json_extract(details, '$.rating')) STORED
    )
""")

# 创建索引
cursor.execute("CREATE INDEX idx_category ON products_with_index(category)")
cursor.execute("CREATE INDEX idx_price ON products_with_index(price)")
cursor.execute("CREATE INDEX idx_rating ON products_with_index(rating)")

# 5. 插入相同数据
print("\n5. 插入相同数据到带索引的表")
cursor.executemany("""
    INSERT INTO products_with_index (id, name, details)
    VALUES (?, ?, ?)
""", products)
conn.commit()
print(f"✅ 插入 {len(products)} 条记录（带索引）")

# 6. 测试有索引查询性能
print("\n6. 测试有索引查询性能")
start_time = time.time()
cursor.execute("""
    SELECT COUNT(*) 
    FROM products_with_index
    WHERE category = '类别5'
""")
result_with_index = cursor.fetchone()[0]
time_with_index = time.time() - start_time
print(f"查询结果: {result_with_index} 条记录")
print(f"查询时间: {time_with_index:.4f} 秒（有索引）")

# 7. 性能对比
print("\n7. 性能对比")
speedup = time_no_index / time_with_index if time_with_index > 0 else 0
print(f"性能提升: {speedup:.2f}x")
print(f"时间减少: {(1 - time_with_index/time_no_index)*100:.1f}%")

# 8. 测试范围查询性能
print("\n8. 测试范围查询性能（价格范围）")
start_time = time.time()
cursor.execute("""
    SELECT COUNT(*) 
    FROM products_no_index
    WHERE json_extract(details, '$.price') BETWEEN 500 AND 1000
""")
result_no_index_range = cursor.fetchone()[0]
time_no_index_range = time.time() - start_time
print(f"无索引查询结果: {result_no_index_range} 条记录")
print(f"无索引查询时间: {time_no_index_range:.4f} 秒")

start_time = time.time()
cursor.execute("""
    SELECT COUNT(*) 
    FROM products_with_index
    WHERE price BETWEEN 500 AND 1000
""")
result_with_index_range = cursor.fetchone()[0]
time_with_index_range = time.time() - start_time
print(f"有索引查询结果: {result_with_index_range} 条记录")
print(f"有索引查询时间: {time_with_index_range:.4f} 秒")

speedup_range = time_no_index_range / time_with_index_range if time_with_index_range > 0 else 0
print(f"范围查询性能提升: {speedup_range:.2f}x")

# 9. 测试复合查询性能
print("\n9. 测试复合查询性能（类别+价格）")
start_time = time.time()
cursor.execute("""
    SELECT COUNT(*) 
    FROM products_no_index
    WHERE json_extract(details, '$.category') = '类别3'
      AND json_extract(details, '$.price') > 800
""")
result_no_index_composite = cursor.fetchone()[0]
time_no_index_composite = time.time() - start_time
print(f"无索引复合查询结果: {result_no_index_composite} 条记录")
print(f"无索引复合查询时间: {time_no_index_composite:.4f} 秒")

start_time = time.time()
cursor.execute("""
    SELECT COUNT(*) 
    FROM products_with_index
    WHERE category = '类别3'
      AND price > 800
""")
result_with_index_composite = cursor.fetchone()[0]
time_with_index_composite = time.time() - start_time
print(f"有索引复合查询结果: {result_with_index_composite} 条记录")
print(f"有索引复合查询时间: {time_with_index_composite:.4f} 秒")

speedup_composite = time_no_index_composite / time_with_index_composite if time_with_index_composite > 0 else 0
print(f"复合查询性能提升: {speedup_composite:.2f}x")

# 10. 查看查询计划
print("\n10. 查看查询计划对比")
print("\n无索引查询计划:")
cursor.execute("""
    EXPLAIN QUERY PLAN
    SELECT * FROM products_no_index
    WHERE json_extract(details, '$.category') = '类别5'
""")
for row in cursor.fetchall():
    print(f"  {row}")

print("\n有索引查询计划:")
cursor.execute("""
    EXPLAIN QUERY PLAN
    SELECT * FROM products_with_index
    WHERE category = '类别5'
""")
for row in cursor.fetchall():
    print(f"  {row}")

# 11. 使用VIRTUAL生成列（节省存储空间）
print("\n11. 使用VIRTUAL生成列（节省存储空间）")
cursor.execute("""
    CREATE TABLE products_virtual (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        details TEXT,
        category TEXT GENERATED ALWAYS AS (json_extract(details, '$.category')) VIRTUAL
    )
""")
cursor.execute("CREATE INDEX idx_category_virtual ON products_virtual(category)")

# 插入少量数据测试
cursor.executemany("""
    INSERT INTO products_virtual (id, name, details)
    VALUES (?, ?, ?)
""", products[:100])
conn.commit()

cursor.execute("""
    SELECT COUNT(*) 
    FROM products_virtual
    WHERE category = '类别5'
""")
result_virtual = cursor.fetchone()[0]
print(f"✅ VIRTUAL生成列查询结果: {result_virtual} 条记录")

# 12. 存储空间对比
print("\n12. 存储空间对比")
cursor.execute("""
    SELECT 
        (SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size() WHERE name = 'products_no_index') as no_index_size,
        (SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size() WHERE name = 'products_with_index') as with_index_size,
        (SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size() WHERE name = 'products_virtual') as virtual_size
""")
# 注意：上面的查询可能不准确，这里仅作演示
print("存储空间对比（需要实际测量）:")
print("  - 无索引表: 基础存储")
print("  - STORED生成列: 基础存储 + 生成列存储")
print("  - VIRTUAL生成列: 基础存储（计算时生成）")

# 清理
conn.close()
if db_path.exists():
    db_path.unlink()
    print(f"\n✅ 清理完成，已删除 {db_path}")

print("\n" + "=" * 60)
print("示例完成！")
print("=" * 60)
print("\n💡 最佳实践:")
print("  1. 对于频繁查询的JSON字段，使用生成列+索引")
print("  2. STORED生成列：查询快，占用存储空间")
print("  3. VIRTUAL生成列：节省空间，查询时计算")
print("  4. 根据查询频率和存储成本选择合适策略")
