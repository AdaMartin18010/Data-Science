#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 生成列示例 - STORED生成列

演示STORED生成列的使用：
- STORED生成列创建
- 自动计算和存储
- 索引创建
- 性能优势

适用版本：SQLite 3.31+ 至 3.47.x
最后更新：2025-01-15
"""

import sqlite3
import time
from pathlib import Path

# 创建示例数据库
db_path = Path("stored_generated_example.db")
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 60)
print("SQLite 生成列示例 - STORED生成列")
print("=" * 60)

# 1. 创建带STORED生成列的表
print("\n1. 创建带STORED生成列的表")
cursor.execute("""
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        discount REAL DEFAULT 0.0,
        -- STORED生成列：总价 = (价格 * 数量) * (1 - 折扣)
        total_price REAL GENERATED ALWAYS AS (
            (price * quantity) * (1 - discount)
        ) STORED,
        -- STORED生成列：是否高价值商品（总价 > 1000）
        is_high_value INTEGER GENERATED ALWAYS AS (
            CASE WHEN (price * quantity) * (1 - discount) > 1000 
                 THEN 1 ELSE 0 END
        ) STORED
    )
""")
print("✅ 表创建成功，包含2个STORED生成列")

# 2. 插入数据
print("\n2. 插入数据")
products = [
    ("笔记本电脑", 8999.0, 1, 0.1),   # 总价: 8099.1, 高价值: 1
    ("鼠标", 99.0, 2, 0.0),          # 总价: 198.0, 高价值: 0
    ("键盘", 299.0, 1, 0.05),        # 总价: 284.05, 高价值: 0
    ("显示器", 1999.0, 2, 0.15),     # 总价: 3398.3, 高价值: 1
    ("耳机", 599.0, 1, 0.0),         # 总价: 599.0, 高价值: 0
]

cursor.executemany("""
    INSERT INTO products (name, price, quantity, discount)
    VALUES (?, ?, ?, ?)
""", products)
conn.commit()
print(f"✅ 插入 {len(products)} 条记录")

# 3. 查看生成列的值
print("\n3. 查看生成列的值")
cursor.execute("""
    SELECT 
        name,
        price,
        quantity,
        discount,
        total_price,
        is_high_value
    FROM products
    ORDER BY total_price DESC
""")
print("\n产品信息（按总价排序）:")
print("-" * 80)
for row in cursor.fetchall():
    high_value = "是" if row[5] else "否"
    print(f"名称: {row[0]:10} | 单价: ¥{row[1]:>7.2f} | 数量: {row[2]} | "
          f"折扣: {row[3]:.0%} | 总价: ¥{row[4]:>8.2f} | 高价值: {high_value}")

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

# 5. 尝试更新生成列（应该失败）
print("\n5. 尝试更新生成列（应该失败）")
try:
    cursor.execute("""
        UPDATE products
        SET total_price = 9999.0
        WHERE id = 1
    """)
    print("❌ 错误：应该不允许更新生成列")
except sqlite3.OperationalError as e:
    print(f"✅ 正确：不允许更新生成列 - {e}")

# 6. 更新基础列，观察生成列自动更新
print("\n6. 更新基础列，观察生成列自动更新")
cursor.execute("""
    SELECT id, name, price, quantity, discount, total_price
    FROM products
    WHERE id = 1
""")
row_before = cursor.fetchone()
print(f"\n更新前 - ID {row_before[0]}: {row_before[1]}")
print(f"  单价: ¥{row_before[2]}, 数量: {row_before[3]}, 折扣: {row_before[4]:.0%}")
print(f"  总价: ¥{row_before[5]:.2f}")

# 更新折扣
cursor.execute("""
    UPDATE products
    SET discount = 0.2
    WHERE id = 1
""")
conn.commit()

cursor.execute("""
    SELECT id, name, price, quantity, discount, total_price
    FROM products
    WHERE id = 1
""")
row_after = cursor.fetchone()
print(f"\n更新后 - ID {row_after[0]}: {row_after[1]}")
print(f"  单价: ¥{row_after[2]}, 数量: {row_after[3]}, 折扣: {row_after[4]:.0%}")
print(f"  总价: ¥{row_after[5]:.2f} (自动重新计算)")

# 7. 为生成列创建索引
print("\n7. 为生成列创建索引")
cursor.execute("""
    CREATE INDEX idx_total_price ON products(total_price)
""")
cursor.execute("""
    CREATE INDEX idx_high_value ON products(is_high_value)
""")
print("✅ 为生成列创建索引成功")

# 8. 测试索引查询性能
print("\n8. 测试索引查询性能")
# 插入更多数据
more_products = []
for i in range(1000):
    price = 100 + (i % 100) * 10
    quantity = (i % 5) + 1
    discount = (i % 10) / 100.0
    more_products.append((f"产品{i+1}", price, quantity, discount))

cursor.executemany("""
    INSERT INTO products (name, price, quantity, discount)
    VALUES (?, ?, ?, ?)
""", more_products)
conn.commit()
print(f"✅ 插入 {len(more_products)} 条记录用于性能测试")

# 测试查询性能
start_time = time.time()
cursor.execute("""
    SELECT COUNT(*) 
    FROM products
    WHERE total_price > 1000
""")
result = cursor.fetchone()[0]
time_with_index = time.time() - start_time
print(f"\n查询结果: {result} 条高价值商品")
print(f"查询时间: {time_with_index:.4f} 秒（使用索引）")

# 9. 使用生成列进行聚合查询
print("\n9. 使用生成列进行聚合查询")
cursor.execute("""
    SELECT 
        is_high_value,
        COUNT(*) as count,
        AVG(total_price) as avg_price,
        SUM(total_price) as total_amount
    FROM products
    GROUP BY is_high_value
""")
print("\n按高价值分类统计:")
print("-" * 60)
for row in cursor.fetchall():
    category = "高价值商品" if row[0] else "普通商品"
    print(f"{category}: {row[1]:4} 件 | 平均总价: ¥{row[2]:>8.2f} | 总金额: ¥{row[3]:>10.2f}")

# 10. 查看表结构
print("\n10. 查看表结构")
cursor.execute("PRAGMA table_info(products)")
print("\n表结构:")
print("-" * 80)
for row in cursor.fetchall():
    col_id, name, col_type, not_null, default_val, pk = row
    generated = " (生成列)" if default_val else ""
    print(f"  {name:15} {col_type:10} {'NOT NULL' if not_null else ''}{generated}")

# 11. 查看查询计划
print("\n11. 查看查询计划（使用生成列索引）")
cursor.execute("""
    EXPLAIN QUERY PLAN
    SELECT * FROM products
    WHERE total_price BETWEEN 500 AND 2000
    ORDER BY total_price DESC
    LIMIT 10
""")
print("\n查询计划:")
for row in cursor.fetchall():
    print(f"  {row}")

# 清理
conn.close()
if db_path.exists():
    db_path.unlink()
    print(f"\n✅ 清理完成，已删除 {db_path}")

print("\n" + "=" * 60)
print("示例完成！")
print("=" * 60)
print("\n💡 STORED生成列特点:")
print("  1. 值存储在磁盘上，查询时直接读取")
print("  2. 插入和更新时自动计算并存储")
print("  3. 可以创建索引，查询性能好")
print("  4. 占用存储空间")
print("  5. 适合频繁查询的列")
