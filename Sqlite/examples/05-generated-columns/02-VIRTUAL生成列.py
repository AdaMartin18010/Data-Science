#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 生成列示例 - VIRTUAL生成列

演示VIRTUAL生成列的使用：
- VIRTUAL生成列创建
- 按需计算
- 存储空间节省
- 性能考虑

适用版本：SQLite 3.31+ 至 3.47.x
最后更新：2025-01-15
"""

import sqlite3
import time
from pathlib import Path

# 创建示例数据库
db_path = Path("virtual_generated_example.db")
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 60)
print("SQLite 生成列示例 - VIRTUAL生成列")
print("=" * 60)

# 1. 创建带VIRTUAL生成列的表
print("\n1. 创建带VIRTUAL生成列的表")
cursor.execute("""
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        discount REAL DEFAULT 0.0,
        -- VIRTUAL生成列：总价 = (价格 * 数量) * (1 - 折扣)
        total_price REAL GENERATED ALWAYS AS (
            (price * quantity) * (1 - discount)
        ) VIRTUAL,
        -- VIRTUAL生成列：折扣金额
        discount_amount REAL GENERATED ALWAYS AS (
            price * quantity * discount
        ) VIRTUAL,
        -- VIRTUAL生成列：单价描述
        price_description TEXT GENERATED ALWAYS AS (
            '单价: ¥' || printf('%.2f', price) || 
            ', 数量: ' || quantity || 
            ', 总价: ¥' || printf('%.2f', (price * quantity) * (1 - discount))
        ) VIRTUAL
    )
""")
print("✅ 表创建成功，包含3个VIRTUAL生成列")

# 2. 插入数据
print("\n2. 插入数据")
products = [
    ("笔记本电脑", 8999.0, 1, 0.1),
    ("鼠标", 99.0, 2, 0.0),
    ("键盘", 299.0, 1, 0.05),
    ("显示器", 1999.0, 2, 0.15),
    ("耳机", 599.0, 1, 0.0),
]

cursor.executemany("""
    INSERT INTO products (name, price, quantity, discount)
    VALUES (?, ?, ?, ?)
""", products)
conn.commit()
print(f"✅ 插入 {len(products)} 条记录")

# 3. 查看生成列的值（按需计算）
print("\n3. 查看生成列的值（按需计算）")
cursor.execute("""
    SELECT 
        name,
        price,
        quantity,
        discount,
        total_price,
        discount_amount,
        price_description
    FROM products
    ORDER BY total_price DESC
""")
print("\n产品信息（按总价排序）:")
print("-" * 100)
for row in cursor.fetchall():
    print(f"名称: {row[0]:10} | 单价: ¥{row[1]:>7.2f} | 数量: {row[2]} | "
          f"折扣: {row[3]:.0%} | 总价: ¥{row[4]:>8.2f} | 折扣金额: ¥{row[5]:>6.2f}")
    print(f"  描述: {row[6]}")

# 4. 尝试直接插入生成列（应该失败）
print("\n4. 尝试直接插入生成列（应该失败）")
try:
    cursor.execute("""
        INSERT INTO products (name, price, quantity, discount, total_price)
        VALUES ('测试商品', 100.0, 1, 0.0, 999.0)
    """)
    print("❌ 错误：应该不允许直接插入生成列")
except sqlite3.OperationalError as e:
    print(f"✅ 正确：不允许直接插入生成列 - {e}")

# 5. 更新基础列，观察生成列自动重新计算
print("\n5. 更新基础列，观察生成列自动重新计算")
cursor.execute("""
    SELECT id, name, total_price, discount_amount
    FROM products
    WHERE id = 1
""")
row_before = cursor.fetchone()
print(f"\n更新前 - ID {row_before[0]}: {row_before[1]}")
print(f"  总价: ¥{row_before[2]:.2f}, 折扣金额: ¥{row_before[3]:.2f}")

# 更新折扣
cursor.execute("""
    UPDATE products
    SET discount = 0.2
    WHERE id = 1
""")
conn.commit()

cursor.execute("""
    SELECT id, name, total_price, discount_amount
    FROM products
    WHERE id = 1
""")
row_after = cursor.fetchone()
print(f"\n更新后 - ID {row_after[0]}: {row_after[1]}")
print(f"  总价: ¥{row_after[2]:.2f}, 折扣金额: ¥{row_after[3]:.2f} (自动重新计算)")

# 6. 为VIRTUAL生成列创建索引
print("\n6. 为VIRTUAL生成列创建索引")
cursor.execute("""
    CREATE INDEX idx_total_price ON products(total_price)
""")
print("✅ 为VIRTUAL生成列创建索引成功")

# 7. 插入大量数据测试性能
print("\n7. 插入大量数据测试性能")
more_products = []
for i in range(1000):
    price = 100 + (i % 100) * 10
    quantity = (i % 5) + 1
    discount = (i % 10) / 100.0
    more_products.append((f"产品{i+1}", price, quantity, discount))

start_time = time.time()
cursor.executemany("""
    INSERT INTO products (name, price, quantity, discount)
    VALUES (?, ?, ?, ?)
""", more_products)
conn.commit()
insert_time = time.time() - start_time
print(f"✅ 插入 {len(more_products)} 条记录，耗时: {insert_time:.4f} 秒")

# 8. 测试查询性能（使用索引）
print("\n8. 测试查询性能（使用索引）")
start_time = time.time()
cursor.execute("""
    SELECT COUNT(*) 
    FROM products
    WHERE total_price > 1000
""")
result = cursor.fetchone()[0]
query_time = time.time() - start_time
print(f"查询结果: {result} 条高价值商品")
print(f"查询时间: {query_time:.4f} 秒（使用VIRTUAL生成列索引）")

# 9. 测试不使用生成列的查询（需要计算）
print("\n9. 测试不使用生成列的查询（需要计算）")
start_time = time.time()
cursor.execute("""
    SELECT COUNT(*) 
    FROM products
    WHERE (price * quantity) * (1 - discount) > 1000
""")
result2 = cursor.fetchone()[0]
query_time2 = time.time() - start_time
print(f"查询结果: {result2} 条高价值商品")
print(f"查询时间: {query_time2:.4f} 秒（直接计算表达式）")
print(f"性能差异: {query_time2/query_time:.2f}x（使用生成列索引更快）")

# 10. 使用生成列进行复杂查询
print("\n10. 使用生成列进行复杂查询")
cursor.execute("""
    SELECT 
        CASE 
            WHEN total_price < 500 THEN '低价值'
            WHEN total_price < 2000 THEN '中价值'
            ELSE '高价值'
        END as value_category,
        COUNT(*) as count,
        AVG(total_price) as avg_price,
        SUM(total_price) as total_amount
    FROM products
    GROUP BY value_category
    ORDER BY avg_price DESC
""")
print("\n按价值分类统计:")
print("-" * 70)
for row in cursor.fetchall():
    print(f"{row[0]:8}: {row[1]:4} 件 | 平均总价: ¥{row[2]:>8.2f} | 总金额: ¥{row[3]:>10.2f}")

# 11. 查看表结构
print("\n11. 查看表结构")
cursor.execute("PRAGMA table_info(products)")
print("\n表结构:")
print("-" * 80)
for row in cursor.fetchall():
    col_id, name, col_type, not_null, default_val, pk = row
    if default_val:
        print(f"  {name:20} {col_type:10} (VIRTUAL生成列)")
    else:
        print(f"  {name:20} {col_type:10}")

# 12. 存储空间对比（需要实际测量）
print("\n12. 存储空间说明")
print("VIRTUAL生成列特点:")
print("  - 不占用存储空间（值不存储在磁盘上）")
print("  - 查询时按需计算")
print("  - 可以创建索引（索引会存储计算值）")
print("  - 适合不常查询或存储空间敏感的场景")

# 清理
conn.close()
if db_path.exists():
    db_path.unlink()
    print(f"\n✅ 清理完成，已删除 {db_path}")

print("\n" + "=" * 60)
print("示例完成！")
print("=" * 60)
print("\n💡 VIRTUAL生成列特点:")
print("  1. 值不存储在磁盘上，查询时按需计算")
print("  2. 节省存储空间")
print("  3. 可以创建索引（索引会存储计算值）")
print("  4. 查询时需要计算，但使用索引时性能好")
print("  5. 适合不常查询或存储空间敏感的场景")
