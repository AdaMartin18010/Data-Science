#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 自定义函数示例 - 聚合函数

演示如何在SQLite中创建和使用自定义聚合函数：
- 创建聚合函数
- 自定义聚合逻辑
- 聚合函数应用

适用版本：SQLite 3.31+
注意：Python sqlite3模块支持创建自定义聚合函数
"""

import sqlite3
import statistics
from pathlib import Path
from typing import List

# 创建示例数据库
db_path = Path("custom_aggregate_example.db")
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 60)
print("SQLite 自定义函数示例 - 聚合函数")
print("=" * 60)

# 1. 创建自定义聚合函数类
print("\n1. 创建自定义聚合函数类")

class Median:
    """计算中位数的聚合函数"""
    def __init__(self):
        self.values = []
    
    def step(self, value):
        """处理每个值"""
        if value is not None:
            self.values.append(value)
    
    def finalize(self):
        """返回最终结果"""
        if not self.values:
            return None
        return statistics.median(self.values)

class Mode:
    """计算众数的聚合函数"""
    def __init__(self):
        self.counts = {}
    
    def step(self, value):
        """处理每个值"""
        if value is not None:
            self.counts[value] = self.counts.get(value, 0) + 1
    
    def finalize(self):
        """返回最终结果"""
        if not self.counts:
            return None
        return max(self.counts, key=self.counts.get)

class StringConcat:
    """字符串连接聚合函数"""
    def __init__(self, separator=', '):
        self.values = []
        self.separator = separator
    
    def step(self, value):
        """处理每个值"""
        if value is not None:
            self.values.append(str(value))
    
    def finalize(self):
        """返回最终结果"""
        if not self.values:
            return None
        return self.separator.join(self.values)

class GeometricMean:
    """计算几何平均数的聚合函数"""
    def __init__(self):
        self.values = []
    
    def step(self, value):
        """处理每个值"""
        if value is not None and value > 0:
            self.values.append(value)
    
    def finalize(self):
        """返回最终结果"""
        if not self.values:
            return None
        product = 1.0
        for v in self.values:
            product *= v
        return product ** (1.0 / len(self.values))

# 注册聚合函数
conn.create_aggregate("median", 1, Median)
conn.create_aggregate("mode", 1, Mode)
conn.create_aggregate("str_concat", 1, StringConcat)
conn.create_aggregate("geometric_mean", 1, GeometricMean)

print("✅ 自定义聚合函数注册成功")

# 2. 创建测试表
print("\n2. 创建测试表")
cursor.execute("""
    CREATE TABLE sales (
        id INTEGER PRIMARY KEY,
        product TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        sale_date TEXT NOT NULL
    )
""")

sales = [
    ("Product A", "Electronics", 99.99, 10, "2025-01-01"),
    ("Product B", "Electronics", 199.99, 5, "2025-01-01"),
    ("Product C", "Books", 19.99, 20, "2025-01-02"),
    ("Product D", "Electronics", 299.99, 3, "2025-01-02"),
    ("Product E", "Books", 29.99, 15, "2025-01-03"),
    ("Product F", "Electronics", 99.99, 8, "2025-01-03"),
    ("Product G", "Books", 19.99, 25, "2025-01-03"),
]

cursor.executemany("""
    INSERT INTO sales (product, category, price, quantity, sale_date)
    VALUES (?, ?, ?, ?, ?)
""", sales)
conn.commit()
print(f"✅ 插入 {len(sales)} 条销售记录")

# 3. 使用中位数聚合函数
print("\n3. 使用中位数聚合函数")
cursor.execute("""
    SELECT 
        category,
        AVG(price) as avg_price,
        median(price) as median_price
    FROM sales
    GROUP BY category
""")
print("按分类统计价格（平均值 vs 中位数）:")
print("-" * 60)
for row in cursor.fetchall():
    print(f"分类: {row[0]:15} | 平均: ${row[1]:>7.2f} | 中位数: ${row[2]:>7.2f}")

# 4. 使用众数聚合函数
print("\n4. 使用众数聚合函数")
cursor.execute("""
    SELECT 
        category,
        mode(price) as mode_price,
        COUNT(*) as count
    FROM sales
    GROUP BY category
""")
print("按分类统计价格众数:")
print("-" * 60)
for row in cursor.fetchall():
    print(f"分类: {row[0]:15} | 众数: ${row[1]:>7.2f} | 数量: {row[2]}")

# 5. 使用字符串连接聚合函数
print("\n5. 使用字符串连接聚合函数")
cursor.execute("""
    SELECT 
        category,
        str_concat(product) as products
    FROM sales
    GROUP BY category
""")
print("按分类连接产品名称:")
print("-" * 60)
for row in cursor.fetchall():
    print(f"分类: {row[0]}")
    print(f"产品: {row[1]}")
    print()

# 6. 使用几何平均数聚合函数
print("\n6. 使用几何平均数聚合函数")
cursor.execute("""
    SELECT 
        category,
        AVG(price) as arithmetic_mean,
        geometric_mean(price) as geometric_mean
    FROM sales
    GROUP BY category
""")
print("按分类统计价格（算术平均 vs 几何平均）:")
print("-" * 60)
for row in cursor.fetchall():
    print(f"分类: {row[0]:15} | 算术平均: ${row[1]:>7.2f} | 几何平均: ${row[2]:>7.2f}")

# 7. 组合使用聚合函数
print("\n7. 组合使用聚合函数")
cursor.execute("""
    SELECT 
        category,
        COUNT(*) as count,
        AVG(price) as avg_price,
        median(price) as median_price,
        MIN(price) as min_price,
        MAX(price) as max_price
    FROM sales
    GROUP BY category
""")
print("按分类完整统计:")
print("-" * 80)
for row in cursor.fetchall():
    print(f"分类: {row[0]:15} | 数量: {row[1]:3} | "
          f"平均: ${row[2]:>7.2f} | 中位数: ${row[3]:>7.2f} | "
          f"最小: ${row[4]:>7.2f} | 最大: ${row[5]:>7.2f}")

# 8. 在HAVING子句中使用自定义聚合函数
print("\n8. 在HAVING子句中使用自定义聚合函数")
cursor.execute("""
    SELECT 
        category,
        median(price) as median_price
    FROM sales
    GROUP BY category
    HAVING median(price) > 50
""")
print("中位数价格大于50的分类:")
print("-" * 60)
for row in cursor.fetchall():
    print(f"分类: {row[0]:15} | 中位数: ${row[1]:>7.2f}")

# 9. 聚合函数性能测试
print("\n9. 聚合函数性能测试")
import time

start_time = time.time()
cursor.execute("""
    SELECT category, median(price)
    FROM sales
    GROUP BY category
""")
results = cursor.fetchall()
elapsed = time.time() - start_time
print(f"聚合查询耗时: {elapsed*1000:.2f}ms")
print(f"结果数量: {len(results)}")

# 清理
conn.close()
if db_path.exists():
    db_path.unlink()
    print(f"\n✅ 清理完成，已删除 {db_path}")

print("\n" + "=" * 60)
print("示例完成！")
print("=" * 60)
print("\n💡 自定义聚合函数要点:")
print("  1. 需要实现step()和finalize()方法")
print("  2. step()处理每个值，finalize()返回最终结果")
print("  3. 使用conn.create_aggregate()注册函数")
print("  4. 可以在GROUP BY查询中使用")
print("  5. 可以在HAVING子句中使用")
