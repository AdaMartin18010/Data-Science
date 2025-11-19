#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 递归CTE示例 - 序列生成

演示使用递归CTE生成各种序列：
- 数字序列生成
- 日期序列生成
- 复杂序列生成

适用版本：SQLite 3.31+
"""

import sqlite3
from pathlib import Path

# 创建示例数据库
db_path = Path("recursive_cte_sequence_example.db")
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 60)
print("SQLite 递归CTE示例 - 序列生成")
print("=" * 60)

# 1. 生成数字序列
print("\n1. 生成数字序列")
print("生成1到10的数字序列:")
cursor.execute("""
    WITH RECURSIVE numbers AS (
        -- 基础查询：起始值
        SELECT 1 as n
        
        UNION ALL
        
        -- 递归查询：递增
        SELECT n + 1
        FROM numbers
        WHERE n < 10
    )
    SELECT n
    FROM numbers
""")
print("-" * 40)
result = [row[0] for row in cursor.fetchall()]
print(f"序列: {', '.join(map(str, result))}")

# 2. 生成斐波那契数列
print("\n2. 生成斐波那契数列")
print("生成前10个斐波那契数:")
cursor.execute("""
    WITH RECURSIVE fibonacci AS (
        -- 基础查询：前两个数
        SELECT 0 as n, 0 as fib_n, 1 as next_fib
        
        UNION ALL
        
        -- 递归查询：计算下一个数
        SELECT 
            n + 1,
            next_fib,
            fib_n + next_fib
        FROM fibonacci
        WHERE n < 9
    )
    SELECT n, fib_n as fibonacci_number
    FROM fibonacci
""")
print("-" * 40)
for row in cursor.fetchall():
    print(f"F({row[0]}) = {row[1]}")

# 3. 生成日期序列
print("\n3. 生成日期序列")
print("生成2025年1月的所有日期:")
cursor.execute("""
    WITH RECURSIVE dates AS (
        -- 基础查询：起始日期
        SELECT date('2025-01-01') as d
        
        UNION ALL
        
        -- 递归查询：递增日期
        SELECT date(d, '+1 day')
        FROM dates
        WHERE d < date('2025-01-31')
    )
    SELECT 
        d,
        strftime('%w', d) as day_of_week,
        CASE strftime('%w', d)
            WHEN '0' THEN '周日'
            WHEN '1' THEN '周一'
            WHEN '2' THEN '周二'
            WHEN '3' THEN '周三'
            WHEN '4' THEN '周四'
            WHEN '5' THEN '周五'
            WHEN '6' THEN '周六'
        END as weekday_name
    FROM dates
    ORDER BY d
""")
print("-" * 60)
for row in cursor.fetchall():
    print(f"{row[0]} ({row[2]})")

# 4. 生成工作日序列
print("\n4. 生成工作日序列（排除周末）")
print("生成2025年1月的工作日:")
cursor.execute("""
    WITH RECURSIVE workdays AS (
        -- 基础查询：起始日期
        SELECT date('2025-01-01') as d
        
        UNION ALL
        
        -- 递归查询：递增日期，跳过周末
        SELECT date(d, '+1 day')
        FROM workdays
        WHERE d < date('2025-01-31')
          AND strftime('%w', date(d, '+1 day')) NOT IN ('0', '6')
    )
    SELECT d, strftime('%w', d) as day_of_week
    FROM workdays
    ORDER BY d
""")
print("-" * 40)
workday_list = [row[0] for row in cursor.fetchall()]
print(f"工作日数量: {len(workday_list)}")
print(f"前5个工作日: {', '.join(workday_list[:5])}")

# 5. 生成月份序列
print("\n5. 生成月份序列")
print("生成2024年1月到12月的所有月份:")
cursor.execute("""
    WITH RECURSIVE months AS (
        -- 基础查询：起始月份
        SELECT date('2024-01-01') as month_start
        
        UNION ALL
        
        -- 递归查询：递增月份
        SELECT date(month_start, '+1 month')
        FROM months
        WHERE month_start < date('2024-12-01')
    )
    SELECT 
        strftime('%Y-%m', month_start) as month,
        strftime('%Y年%m月', month_start) as month_name
    FROM months
    ORDER BY month_start
""")
print("-" * 40)
for row in cursor.fetchall():
    print(f"{row[0]} ({row[1]})")

# 6. 生成时间序列（小时）
print("\n6. 生成时间序列（小时）")
print("生成一天中的每个小时:")
cursor.execute("""
    WITH RECURSIVE hours AS (
        -- 基础查询：起始小时
        SELECT 0 as hour
        
        UNION ALL
        
        -- 递归查询：递增小时
        SELECT hour + 1
        FROM hours
        WHERE hour < 23
    )
    SELECT 
        hour,
        printf('%02d:00', hour) as time_str
    FROM hours
""")
print("-" * 40)
for row in cursor.fetchall():
    print(f"{row[1]}")

# 7. 生成等差数列
print("\n7. 生成等差数列")
print("生成首项为5，公差为3，共10项的等差数列:")
cursor.execute("""
    WITH RECURSIVE arithmetic_sequence AS (
        -- 基础查询：首项
        SELECT 5 as value, 1 as term
        
        UNION ALL
        
        -- 递归查询：计算下一项
        SELECT value + 3, term + 1
        FROM arithmetic_sequence
        WHERE term < 10
    )
    SELECT term, value
    FROM arithmetic_sequence
""")
print("-" * 40)
for row in cursor.fetchall():
    print(f"a({row[0]}) = {row[1]}")

# 8. 生成等比数列
print("\n8. 生成等比数列")
print("生成首项为2，公比为3，共8项的等比数列:")
cursor.execute("""
    WITH RECURSIVE geometric_sequence AS (
        -- 基础查询：首项
        SELECT 2 as value, 1 as term
        
        UNION ALL
        
        -- 递归查询：计算下一项
        SELECT value * 3, term + 1
        FROM geometric_sequence
        WHERE term < 8
    )
    SELECT term, value
    FROM geometric_sequence
""")
print("-" * 40)
for row in cursor.fetchall():
    print(f"a({row[0]}) = {row[1]}")

# 9. 生成质数序列
print("\n9. 生成质数序列")
print("生成前10个质数:")
cursor.execute("""
    WITH RECURSIVE numbers AS (
        SELECT 2 as n
        
        UNION ALL
        
        SELECT n + 1
        FROM numbers
        WHERE n < 30
    ),
    primes AS (
        SELECT n
        FROM numbers n1
        WHERE NOT EXISTS (
            SELECT 1
            FROM numbers n2
            WHERE n2.n < n1.n
              AND n1.n % n2.n = 0
        )
    )
    SELECT n
    FROM primes
    ORDER BY n
    LIMIT 10
""")
print("-" * 40)
prime_list = [str(row[0]) for row in cursor.fetchall()]
print(f"前10个质数: {', '.join(prime_list)}")

# 10. 生成周序列
print("\n10. 生成周序列")
print("生成2025年1月的所有周（周一到周日）:")
cursor.execute("""
    WITH RECURSIVE weeks AS (
        -- 基础查询：第一周的周一
        SELECT date('2025-01-01', 'weekday 1') as week_start
        
        UNION ALL
        
        -- 递归查询：下一周的周一
        SELECT date(week_start, '+7 days')
        FROM weeks
        WHERE week_start < date('2025-01-31', 'weekday 1')
    )
    SELECT 
        week_start,
        date(week_start, '+6 days') as week_end,
        strftime('第%W周', week_start) as week_number
    FROM weeks
""")
print("-" * 60)
for row in cursor.fetchall():
    print(f"{row[2]}: {row[0]} 到 {row[1]}")

# 清理
conn.close()
if db_path.exists():
    db_path.unlink()
    print(f"\n✅ 清理完成，已删除 {db_path}")

print("\n" + "=" * 60)
print("示例完成！")
print("=" * 60)
print("\n💡 序列生成要点:")
print("  1. 数字序列：使用递归CTE生成连续数字")
print("  2. 日期序列：使用date()函数生成日期序列")
print("  3. 数学序列：使用数学公式生成特殊序列")
print("  4. 注意终止条件，避免无限递归")
