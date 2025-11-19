#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite JSON扩展示例 - 路径查询

演示SQLite JSON1扩展的高级路径查询功能：
- JSON路径表达式
- 嵌套JSON访问
- JSON数组索引访问
- 复杂JSON结构查询

适用版本：SQLite 3.31+
"""

import sqlite3
import json
from pathlib import Path

# 创建示例数据库
db_path = Path("json_path_example.db")
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 60)
print("SQLite JSON扩展示例 - 路径查询")
print("=" * 60)

# 1. 创建包含复杂JSON结构的表
print("\n1. 创建包含复杂JSON结构的表")
cursor.execute("""
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        order_info TEXT  -- 存储复杂JSON结构
    )
""")

# 2. 插入复杂JSON数据
print("\n2. 插入复杂JSON数据")
orders_data = [
    (1, json.dumps({
        "order_id": "ORD-001",
        "customer": {
            "name": "张三",
            "email": "zhangsan@example.com",
            "address": {
                "city": "北京",
                "district": "朝阳区",
                "street": "建国路88号"
            }
        },
        "items": [
            {"product": "笔记本电脑", "quantity": 1, "price": 8999},
            {"product": "鼠标", "quantity": 2, "price": 99}
        ],
        "total": 9197,
        "status": "已发货"
    })),
    (2, json.dumps({
        "order_id": "ORD-002",
        "customer": {
            "name": "李四",
            "email": "lisi@example.com",
            "address": {
                "city": "上海",
                "district": "浦东新区",
                "street": "陆家嘴环路1000号"
            }
        },
        "items": [
            {"product": "智能手机", "quantity": 1, "price": 7999},
            {"product": "保护壳", "quantity": 1, "price": 199}
        ],
        "total": 8198,
        "status": "已完成"
    })),
    (3, json.dumps({
        "order_id": "ORD-003",
        "customer": {
            "name": "王五",
            "email": "wangwu@example.com",
            "address": {
                "city": "深圳",
                "district": "南山区",
                "street": "科技园南路2号"
            }
        },
        "items": [
            {"product": "无线耳机", "quantity": 1, "price": 1899}
        ],
        "total": 1899,
        "status": "待发货"
    })),
]

cursor.executemany("""
    INSERT INTO orders (id, order_info)
    VALUES (?, ?)
""", orders_data)
conn.commit()
print(f"✅ 插入 {len(orders_data)} 条订单记录")

# 3. 访问嵌套JSON对象
print("\n3. 访问嵌套JSON对象")
cursor.execute("""
    SELECT 
        json_extract(order_info, '$.order_id') as order_id,
        json_extract(order_info, '$.customer.name') as customer_name,
        json_extract(order_info, '$.customer.email') as email,
        json_extract(order_info, '$.customer.address.city') as city
    FROM orders
""")
print("\n订单客户信息:")
print("-" * 70)
for row in cursor.fetchall():
    print(f"订单号: {row[0]:10} | 客户: {row[1]:8} | 邮箱: {row[2]:25} | 城市: {row[3]}")

# 4. 访问JSON数组元素
print("\n4. 访问JSON数组元素")
cursor.execute("""
    SELECT 
        json_extract(order_info, '$.order_id') as order_id,
        json_extract(order_info, '$.items[0].product') as first_item,
        json_extract(order_info, '$.items[0].quantity') as first_quantity,
        json_extract(order_info, '$.items[0].price') as first_price
    FROM orders
""")
print("\n订单第一项商品:")
print("-" * 70)
for row in cursor.fetchall():
    print(f"订单号: {row[0]:10} | 商品: {row[1]:12} | 数量: {row[2]} | 价格: ¥{row[3]}")

# 5. 获取JSON数组长度
print("\n5. 获取JSON数组长度")
cursor.execute("""
    SELECT 
        json_extract(order_info, '$.order_id') as order_id,
        json_array_length(json_extract(order_info, '$.items')) as item_count,
        json_extract(order_info, '$.total') as total
    FROM orders
""")
print("\n订单商品数量统计:")
print("-" * 50)
for row in cursor.fetchall():
    print(f"订单号: {row[0]:10} | 商品数: {row[1]} | 总金额: ¥{row[2]}")

# 6. 遍历JSON数组（使用json_each）
print("\n6. 遍历JSON数组（使用json_each）")
cursor.execute("""
    SELECT 
        json_extract(o.order_info, '$.order_id') as order_id,
        json_extract(value, '$.product') as product,
        json_extract(value, '$.quantity') as quantity,
        json_extract(value, '$.price') as price
    FROM orders o,
         json_each(json_extract(o.order_info, '$.items')) as items
    ORDER BY order_id, json_extract(value, '$.price') DESC
""")
print("\n所有订单商品明细:")
print("-" * 70)
for row in cursor.fetchall():
    print(f"订单号: {row[0]:10} | 商品: {row[1]:12} | 数量: {row[2]} | 价格: ¥{row[3]}")

# 7. 使用json_tree遍历整个JSON结构
print("\n7. 使用json_tree遍历整个JSON结构")
cursor.execute("""
    SELECT 
        json_extract(o.order_info, '$.order_id') as order_id,
        json_tree.key as json_key,
        json_tree.value as json_value,
        json_tree.type as value_type
    FROM orders o,
         json_tree(o.order_info) as json_tree
    WHERE json_tree.type = 'text' 
      AND json_extract(o.order_info, '$.order_id') = 'ORD-001'
    LIMIT 10
""")
print("\n订单ORD-001的JSON结构（文本值）:")
print("-" * 70)
for row in cursor.fetchall():
    print(f"订单号: {row[0]:10} | 键: {row[1]:25} | 值: {row[2]:30} | 类型: {row[3]}")

# 8. 条件查询嵌套JSON字段
print("\n8. 条件查询嵌套JSON字段")
cursor.execute("""
    SELECT 
        json_extract(order_info, '$.order_id') as order_id,
        json_extract(order_info, '$.customer.name') as customer_name,
        json_extract(order_info, '$.customer.address.city') as city,
        json_extract(order_info, '$.total') as total
    FROM orders
    WHERE json_extract(order_info, '$.customer.address.city') = '北京'
""")
print("\n北京客户的订单:")
print("-" * 60)
for row in cursor.fetchall():
    print(f"订单号: {row[0]:10} | 客户: {row[1]:8} | 城市: {row[2]} | 总金额: ¥{row[3]}")

# 9. 聚合JSON数组中的数值
print("\n9. 聚合JSON数组中的数值")
cursor.execute("""
    SELECT 
        json_extract(o.order_info, '$.order_id') as order_id,
        SUM(json_extract(value, '$.price') * json_extract(value, '$.quantity')) as calculated_total,
        json_extract(o.order_info, '$.total') as stored_total
    FROM orders o,
         json_each(json_extract(o.order_info, '$.items')) as items
    GROUP BY o.id
""")
print("\n订单总金额验证（计算值 vs 存储值）:")
print("-" * 60)
for row in cursor.fetchall():
    match = "✅" if row[1] == row[2] else "❌"
    print(f"订单号: {row[0]:10} | 计算值: ¥{row[1]:>6} | 存储值: ¥{row[2]:>6} {match}")

# 10. 使用json_insert添加JSON字段
print("\n10. 使用json_insert添加JSON字段")
cursor.execute("""
    UPDATE orders
    SET order_info = json_insert(
        order_info,
        '$.discount', 100,
        '$.final_total', json_extract(order_info, '$.total') - 100
    )
    WHERE json_extract(order_info, '$.order_id') = 'ORD-001'
""")
conn.commit()

cursor.execute("""
    SELECT 
        json_extract(order_info, '$.order_id') as order_id,
        json_extract(order_info, '$.total') as original_total,
        json_extract(order_info, '$.discount') as discount,
        json_extract(order_info, '$.final_total') as final_total
    FROM orders
    WHERE json_extract(order_info, '$.order_id') = 'ORD-001'
""")
row = cursor.fetchone()
print(f"\n订单ORD-001折扣信息:")
print(f"  原价: ¥{row[1]}")
print(f"  折扣: ¥{row[2]}")
print(f"  实付: ¥{row[3]}")

# 清理
conn.close()
if db_path.exists():
    db_path.unlink()
    print(f"\n✅ 清理完成，已删除 {db_path}")

print("\n" + "=" * 60)
print("示例完成！")
print("=" * 60)
