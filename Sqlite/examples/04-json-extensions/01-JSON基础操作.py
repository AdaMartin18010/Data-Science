#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite JSON扩展示例 - 基础操作

演示SQLite JSON1扩展的基本功能：
- JSON数据存储
- json()函数使用
- json_extract()函数使用
- JSON数据类型验证

适用版本：SQLite 3.31+ 至 3.47.x
最后更新：2025-01-15
"""

import sqlite3
import json
from pathlib import Path

# 创建示例数据库
db_path = Path("json_example.db")
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 60)
print("SQLite JSON扩展示例 - 基础操作")
print("=" * 60)

# 1. 创建包含JSON列的表
print("\n1. 创建包含JSON列的表")
cursor.execute("""
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        details TEXT,  -- 存储JSON字符串
        metadata TEXT  -- 存储JSON字符串
    )
""")
print("✅ 表创建成功")

# 2. 插入JSON数据
print("\n2. 插入JSON数据")
products = [
    (1, "笔记本电脑", 
     json.dumps({"brand": "ThinkPad", "cpu": "Intel i7", "ram": "16GB", "price": 8999}),
     json.dumps({"tags": ["办公", "便携"], "rating": 4.5, "reviews": 128})),
    (2, "智能手机",
     json.dumps({"brand": "iPhone", "model": "15 Pro", "storage": "256GB", "price": 7999}),
     json.dumps({"tags": ["拍照", "性能"], "rating": 4.8, "reviews": 256})),
    (3, "无线耳机",
     json.dumps({"brand": "AirPods", "type": "Pro", "battery": "6小时", "price": 1899}),
     json.dumps({"tags": ["降噪", "便携"], "rating": 4.6, "reviews": 512})),
]

cursor.executemany("""
    INSERT INTO products (id, name, details, metadata)
    VALUES (?, ?, ?, ?)
""", products)
conn.commit()
print(f"✅ 插入 {len(products)} 条记录")

# 3. 使用json()函数验证和格式化JSON
print("\n3. 使用json()函数验证和格式化JSON")
cursor.execute("""
    SELECT 
        name,
        json(details) as formatted_details,
        json(metadata) as formatted_metadata
    FROM products
    WHERE id = 1
""")
row = cursor.fetchone()
print(f"产品名称: {row[0]}")
print(f"格式化详情: {row[1]}")
print(f"格式化元数据: {row[2]}")

# 4. 使用json_extract()提取JSON字段
print("\n4. 使用json_extract()提取JSON字段")
cursor.execute("""
    SELECT 
        name,
        json_extract(details, '$.brand') as brand,
        json_extract(details, '$.price') as price,
        json_extract(metadata, '$.rating') as rating
    FROM products
    ORDER BY json_extract(metadata, '$.rating') DESC
""")
print("\n产品信息（按评分排序）:")
print("-" * 60)
for row in cursor.fetchall():
    print(f"名称: {row[0]:12} | 品牌: {row[1]:10} | 价格: ¥{row[2]:>6} | 评分: {row[3]}")

# 5. 使用->和->>操作符（SQLite 3.38+）
print("\n5. 使用->和->>操作符（简化语法）")
try:
    cursor.execute("""
        SELECT 
            name,
            details->>'$.brand' as brand,
            details->>'$.price' as price,
            metadata->>'$.rating' as rating
        FROM products
        WHERE details->>'$.price' > 5000
    """)
    print("\n价格超过5000的产品:")
    print("-" * 60)
    for row in cursor.fetchall():
        print(f"名称: {row[0]:12} | 品牌: {row[1]:10} | 价格: ¥{row[2]:>6} | 评分: {row[3]}")
except sqlite3.OperationalError as e:
    print(f"⚠️  ->操作符需要SQLite 3.38+，当前版本可能不支持: {e}")

# 6. JSON数组操作
print("\n6. JSON数组操作")
cursor.execute("""
    SELECT 
        name,
        json_extract(metadata, '$.tags') as tags,
        json_array_length(json_extract(metadata, '$.tags')) as tag_count
    FROM products
""")
print("\n产品标签信息:")
print("-" * 60)
for row in cursor.fetchall():
    print(f"名称: {row[0]:12} | 标签: {row[1]:30} | 标签数: {row[2]}")

# 7. JSON对象操作
print("\n7. JSON对象操作")
cursor.execute("""
    SELECT 
        name,
        json_object('brand', json_extract(details, '$.brand'),
                    'price', json_extract(details, '$.price'),
                    'rating', json_extract(metadata, '$.rating')) as summary
    FROM products
    LIMIT 2
""")
print("\n产品摘要信息:")
print("-" * 60)
for row in cursor.fetchall():
    print(f"名称: {row[0]}")
    print(f"摘要: {row[1]}")
    print()

# 8. JSON聚合函数
print("\n8. JSON聚合函数")
cursor.execute("""
    SELECT 
        json_group_array(name) as all_products,
        json_group_object(name, json_extract(details, '$.price')) as price_map
    FROM products
""")
row = cursor.fetchone()
print(f"所有产品列表: {row[0]}")
print(f"价格映射: {row[1]}")

# 9. 条件查询JSON字段
print("\n9. 条件查询JSON字段")
cursor.execute("""
    SELECT 
        name,
        json_extract(details, '$.price') as price,
        json_extract(metadata, '$.rating') as rating
    FROM products
    WHERE json_extract(metadata, '$.rating') >= 4.6
    ORDER BY json_extract(details, '$.price') DESC
""")
print("\n高评分产品（评分>=4.6）:")
print("-" * 60)
for row in cursor.fetchall():
    print(f"名称: {row[0]:12} | 价格: ¥{row[1]:>6} | 评分: {row[2]}")

# 10. 更新JSON字段
print("\n10. 更新JSON字段")
cursor.execute("""
    UPDATE products
    SET metadata = json_set(metadata, '$.rating', 4.9, '$.reviews', 1000)
    WHERE id = 2
""")
conn.commit()

cursor.execute("""
    SELECT name, metadata
    FROM products
    WHERE id = 2
""")
row = cursor.fetchone()
print(f"更新后的元数据: {row[1]}")

# 清理
conn.close()
if db_path.exists():
    db_path.unlink()
    print(f"\n✅ 清理完成，已删除 {db_path}")

print("\n" + "=" * 60)
print("示例完成！")
print("=" * 60)
