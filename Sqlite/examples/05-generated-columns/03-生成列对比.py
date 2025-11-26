#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 生成列示例 - STORED vs VIRTUAL对比

对比STORED和VIRTUAL生成列的性能和存储特点：
- 性能对比
- 存储空间对比
- 使用场景选择

适用版本：SQLite 3.31+ 至 3.47.x
最后更新：2025-01-15
"""

import sqlite3
import time
from pathlib import Path

# 创建示例数据库
db_path_stored = Path("comparison_stored.db")
db_path_virtual = Path("comparison_virtual.db")

for db_path in [db_path_stored, db_path_virtual]:
    if db_path.exists():
        db_path.unlink()

print("=" * 60)
print("SQLite 生成列示例 - STORED vs VIRTUAL对比")
print("=" * 60)

# 1. 创建STORED生成列表
print("\n1. 创建STORED生成列表")
conn_stored = sqlite3.connect(str(db_path_stored))
cursor_stored = conn_stored.cursor()

cursor_stored.execute("""
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        discount REAL DEFAULT 0.0,
        total_price REAL GENERATED ALWAYS AS (
            (price * quantity) * (1 - discount)
        ) STORED
    )
""")
cursor_stored.execute("CREATE INDEX idx_total_price ON products(total_price)")

# 2. 创建VIRTUAL生成列表
print("2. 创建VIRTUAL生成列表")
conn_virtual = sqlite3.connect(str(db_path_virtual))
cursor_virtual = conn_virtual.cursor()

cursor_virtual.execute("""
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        discount REAL DEFAULT 0.0,
        total_price REAL GENERATED ALWAYS AS (
            (price * quantity) * (1 - discount)
        ) VIRTUAL
    )
""")
cursor_virtual.execute("CREATE INDEX idx_total_price ON products(total_price)")

# 3. 准备测试数据
print("\n3. 准备测试数据")
test_data = []
for i in range(5000):
    price = 100 + (i % 100) * 10
    quantity = (i % 5) + 1
    discount = (i % 10) / 100.0
    test_data.append((f"产品{i+1}", price, quantity, discount))

# 4. 插入性能对比
print("\n4. 插入性能对比")
print("-" * 60)

# STORED生成列插入
start_time = time.time()
cursor_stored.executemany("""
    INSERT INTO products (name, price, quantity, discount)
    VALUES (?, ?, ?, ?)
""", test_data)
conn_stored.commit()
stored_insert_time = time.time() - start_time
print(f"STORED生成列插入 {len(test_data)} 条记录: {stored_insert_time:.4f} 秒")

# VIRTUAL生成列插入
start_time = time.time()
cursor_virtual.executemany("""
    INSERT INTO products (name, price, quantity, discount)
    VALUES (?, ?, ?, ?)
""", test_data)
conn_virtual.commit()
virtual_insert_time = time.time() - start_time
print(f"VIRTUAL生成列插入 {len(test_data)} 条记录: {virtual_insert_time:.4f} 秒")
print(f"插入性能差异: {stored_insert_time/virtual_insert_time:.2f}x "
      f"({'STORED' if stored_insert_time > virtual_insert_time else 'VIRTUAL'}更慢)")

# 5. 查询性能对比（使用索引）
print("\n5. 查询性能对比（使用索引）")
print("-" * 60)

# STORED生成列查询
start_time = time.time()
cursor_stored.execute("""
    SELECT COUNT(*) 
    FROM products
    WHERE total_price > 1000
""")
stored_result = cursor_stored.fetchone()[0]
stored_query_time = time.time() - start_time
print(f"STORED生成列查询结果: {stored_result} 条记录")
print(f"STORED生成列查询时间: {stored_query_time:.4f} 秒")

# VIRTUAL生成列查询
start_time = time.time()
cursor_virtual.execute("""
    SELECT COUNT(*) 
    FROM products
    WHERE total_price > 1000
""")
virtual_result = cursor_virtual.fetchone()[0]
virtual_query_time = time.time() - start_time
print(f"VIRTUAL生成列查询结果: {virtual_result} 条记录")
print(f"VIRTUAL生成列查询时间: {virtual_query_time:.4f} 秒")

if stored_query_time > 0 and virtual_query_time > 0:
    if stored_query_time < virtual_query_time:
        print(f"查询性能差异: {virtual_query_time/stored_query_time:.2f}x (STORED更快)")
    else:
        print(f"查询性能差异: {stored_query_time/virtual_query_time:.2f}x (VIRTUAL更快)")

# 6. 范围查询性能对比
print("\n6. 范围查询性能对比")
print("-" * 60)

# STORED生成列范围查询
start_time = time.time()
cursor_stored.execute("""
    SELECT COUNT(*) 
    FROM products
    WHERE total_price BETWEEN 500 AND 2000
""")
stored_range_result = cursor_stored.fetchone()[0]
stored_range_time = time.time() - start_time
print(f"STORED生成列范围查询: {stored_range_result} 条记录, {stored_range_time:.4f} 秒")

# VIRTUAL生成列范围查询
start_time = time.time()
cursor_virtual.execute("""
    SELECT COUNT(*) 
    FROM products
    WHERE total_price BETWEEN 500 AND 2000
""")
virtual_range_result = cursor_virtual.fetchone()[0]
virtual_range_time = time.time() - start_time
print(f"VIRTUAL生成列范围查询: {virtual_range_result} 条记录, {virtual_range_time:.4f} 秒")

# 7. 聚合查询性能对比
print("\n7. 聚合查询性能对比")
print("-" * 60)

# STORED生成列聚合
start_time = time.time()
cursor_stored.execute("""
    SELECT 
        AVG(total_price) as avg_price,
        SUM(total_price) as total_amount,
        MIN(total_price) as min_price,
        MAX(total_price) as max_price
    FROM products
""")
stored_agg = cursor_stored.fetchone()
stored_agg_time = time.time() - start_time
print(f"STORED生成列聚合查询: {stored_agg_time:.4f} 秒")
print(f"  平均: ¥{stored_agg[0]:.2f}, 总计: ¥{stored_agg[1]:.2f}, "
      f"最小: ¥{stored_agg[2]:.2f}, 最大: ¥{stored_agg[3]:.2f}")

# VIRTUAL生成列聚合
start_time = time.time()
cursor_virtual.execute("""
    SELECT 
        AVG(total_price) as avg_price,
        SUM(total_price) as total_amount,
        MIN(total_price) as min_price,
        MAX(total_price) as max_price
    FROM products
""")
virtual_agg = cursor_virtual.fetchone()
virtual_agg_time = time.time() - start_time
print(f"VIRTUAL生成列聚合查询: {virtual_agg_time:.4f} 秒")
print(f"  平均: ¥{virtual_agg[0]:.2f}, 总计: ¥{virtual_agg[1]:.2f}, "
      f"最小: ¥{virtual_agg[2]:.2f}, 最大: ¥{virtual_agg[3]:.2f}")

# 8. 存储空间对比（数据库文件大小）
print("\n8. 存储空间对比")
print("-" * 60)
stored_size = db_path_stored.stat().st_size if db_path_stored.exists() else 0
virtual_size = db_path_virtual.stat().st_size if db_path_virtual.exists() else 0

print(f"STORED生成列数据库大小: {stored_size:,} 字节 ({stored_size/1024:.2f} KB)")
print(f"VIRTUAL生成列数据库大小: {virtual_size:,} 字节 ({virtual_size/1024:.2f} KB)")

if stored_size > 0 and virtual_size > 0:
    size_diff = ((stored_size - virtual_size) / virtual_size) * 100
    print(f"存储空间差异: {size_diff:+.1f}% "
          f"({'STORED占用更多' if stored_size > virtual_size else 'VIRTUAL占用更多'})")

# 9. 更新性能对比
print("\n9. 更新性能对比")
print("-" * 60)

# STORED生成列更新
start_time = time.time()
cursor_stored.execute("""
    UPDATE products
    SET discount = discount + 0.01
    WHERE id <= 1000
""")
conn_stored.commit()
stored_update_time = time.time() - start_time
print(f"STORED生成列更新1000条记录: {stored_update_time:.4f} 秒")

# VIRTUAL生成列更新
start_time = time.time()
cursor_virtual.execute("""
    UPDATE products
    SET discount = discount + 0.01
    WHERE id <= 1000
""")
conn_virtual.commit()
virtual_update_time = time.time() - start_time
print(f"VIRTUAL生成列更新1000条记录: {virtual_update_time:.4f} 秒")

if stored_update_time > 0 and virtual_update_time > 0:
    if stored_update_time < virtual_update_time:
        print(f"更新性能差异: {virtual_update_time/stored_update_time:.2f}x (STORED更快)")
    else:
        print(f"更新性能差异: {stored_update_time/virtual_update_time:.2f}x (VIRTUAL更快)")

# 10. 总结和建议
print("\n10. 总结和建议")
print("=" * 60)
print("\n📊 性能总结:")
print(f"  插入: {'STORED' if stored_insert_time > virtual_insert_time else 'VIRTUAL'} 更快")
print(f"  查询: {'STORED' if stored_query_time < virtual_query_time else 'VIRTUAL'} 更快")
print(f"  更新: {'STORED' if stored_update_time < virtual_update_time else 'VIRTUAL'} 更快")
print(f"  存储: {'STORED' if stored_size > virtual_size else 'VIRTUAL'} 占用更多空间")

print("\n💡 使用建议:")
print("  STORED生成列适用于:")
print("    - 频繁查询的列")
print("    - 查询性能要求高的场景")
print("    - 存储空间充足的情况")
print("    - 表达式计算成本高的场景")
print()
print("  VIRTUAL生成列适用于:")
print("    - 不常查询的列")
print("    - 存储空间敏感的场景")
print("    - 表达式计算成本低的场景")
print("    - 需要节省存储空间的情况")

# 清理
conn_stored.close()
conn_virtual.close()

for db_path in [db_path_stored, db_path_virtual]:
    if db_path.exists():
        db_path.unlink()
        print(f"\n✅ 清理完成，已删除 {db_path}")

print("\n" + "=" * 60)
print("对比测试完成！")
print("=" * 60)
