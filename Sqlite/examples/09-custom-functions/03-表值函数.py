#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 自定义函数示例 - 表值函数

演示如何在SQLite中创建和使用表值函数：
- 创建表值函数
- 返回多行数据
- 表值函数应用

注意：SQLite的表值函数需要使用C/C++扩展实现。
Python sqlite3模块不直接支持表值函数，本示例展示概念和设计思路。

适用版本：SQLite 3.31+
"""

import sqlite3
from pathlib import Path

# 创建示例数据库
db_path = Path("table_valued_functions_example.db")
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 60)
print("SQLite 自定义函数示例 - 表值函数")
print("=" * 60)

print("\n注意：SQLite的表值函数需要使用C/C++扩展实现。")
print("Python sqlite3模块不直接支持表值函数。")
print("本示例展示表值函数的概念和设计思路。")

# 1. 表值函数概念
print("\n1. 表值函数概念")
print("表值函数是返回多行数据的函数，可以在FROM子句中使用：")
print("""
-- 示例：生成序列
SELECT * FROM generate_series(1, 10);

-- 示例：分割字符串
SELECT * FROM split_string('a,b,c', ',');

-- 示例：读取CSV
SELECT * FROM read_csv('data.csv');
""")

# 2. 表值函数接口说明
print("\n2. 表值函数接口说明")
print("表值函数需要实现以下接口：")
print("  - xCreate/xConnect: 创建/连接表值函数")
print("  - xDestroy/xDisconnect: 销毁/断开")
print("  - xOpen: 打开游标")
print("  - xClose: 关闭游标")
print("  - xFilter: 过滤查询条件")
print("  - xNext: 获取下一行")
print("  - xEof: 检查是否结束")
print("  - xColumn: 获取列值")

# 3. 使用递归CTE模拟表值函数（生成序列）
print("\n3. 使用递归CTE模拟表值函数（生成序列）")
print("生成1到10的序列:")
cursor.execute("""
    WITH RECURSIVE generate_series(n) AS (
        SELECT 1
        UNION ALL
        SELECT n + 1
        FROM generate_series
        WHERE n < 10
    )
    SELECT n FROM generate_series
""")
print("序列:")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# 4. 使用递归CTE模拟表值函数（日期序列）
print("\n4. 使用递归CTE模拟表值函数（日期序列）")
print("生成2025年1月的日期序列:")
cursor.execute("""
    WITH RECURSIVE date_series(d) AS (
        SELECT date('2025-01-01')
        UNION ALL
        SELECT date(d, '+1 day')
        FROM date_series
        WHERE d < date('2025-01-31')
    )
    SELECT d, strftime('%w', d) as day_of_week
    FROM date_series
    LIMIT 7
""")
print("日期序列（前7天）:")
for row in cursor.fetchall():
    weekday = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][int(row[1])]
    print(f"  {row[0]} ({weekday})")

# 5. 创建辅助表模拟表值函数（字符串分割）
print("\n5. 创建辅助表模拟表值函数（字符串分割）")
print("""
虽然不能直接创建表值函数，但可以使用辅助表或视图来模拟：

-- 创建字符串分割辅助表
CREATE TABLE split_string_temp (
    value TEXT
);

-- 使用Python处理字符串分割
""")

# 模拟字符串分割
def split_string(text, delimiter):
    """分割字符串"""
    if text is None:
        return []
    return text.split(delimiter)

# 创建测试数据
test_string = "apple,banana,cherry,date"
result = split_string(test_string, ',')
print(f"分割字符串 '{test_string}':")
for i, item in enumerate(result, 1):
    print(f"  {i}. {item}")

# 6. 使用FTS5作为表值函数示例
print("\n6. 使用FTS5作为表值函数示例")
cursor.execute("""
    CREATE VIRTUAL TABLE search_results USING fts5(
        title,
        content
    )
""")

cursor.executemany("""
    INSERT INTO search_results (title, content)
    VALUES (?, ?)
""", [
    ("文档1", "SQLite是一个数据库"),
    ("文档2", "Python是编程语言"),
    ("文档3", "数据库设计很重要"),
])

print("✅ FTS5表创建并插入数据")

# 搜索并返回结果（类似表值函数）
print("\n搜索'数据库'，返回结果:")
cursor.execute("""
    SELECT 
        rowid,
        title,
        snippet(search_results, 1, '<b>', '</b>', '...', 30) as snippet
    FROM search_results
    WHERE search_results MATCH '数据库'
    ORDER BY bm25(search_results)
""")
for row in cursor.fetchall():
    print(f"  ID: {row[0]} | 标题: {row[1]} | 摘要: {row[2]}")

# 7. 表值函数应用场景
print("\n7. 表值函数应用场景")
print("表值函数适用于以下场景:")
print("  ✅ 生成序列数据")
print("  ✅ 字符串分割和解析")
print("  ✅ 外部数据源查询")
print("  ✅ 数据转换和格式化")
print("  ✅ 复杂数据生成")

# 8. 表值函数实现建议
print("\n8. 表值函数实现建议")
print("实现表值函数的建议:")
print("  1. 使用C/C++扩展实现（性能好）")
print("  2. 使用Python扩展模块（如apsw）")
print("  3. 使用递归CTE模拟简单场景")
print("  4. 使用辅助表和触发器")
print("  5. 考虑使用虚拟表替代")

# 清理
conn.close()
if db_path.exists():
    db_path.unlink()
    print(f"\n✅ 清理完成，已删除 {db_path}")

print("\n" + "=" * 60)
print("示例完成！")
print("=" * 60)
print("\n💡 表值函数要点:")
print("  1. 表值函数返回多行数据")
print("  2. 可以在FROM子句中使用")
print("  3. 需要使用C/C++扩展实现")
print("  4. 可以使用递归CTE模拟简单场景")
print("  5. 适合数据生成和转换场景")
