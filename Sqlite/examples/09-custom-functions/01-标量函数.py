#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 自定义函数示例 - 标量函数

演示如何在SQLite中创建和使用自定义标量函数：
- 创建标量函数
- 字符串处理函数
- 数学计算函数
- 日期时间函数

适用版本：SQLite 3.31+ 至 3.47.x
最后更新：2025-01-15
注意：Python sqlite3模块支持创建自定义函数
"""

import sqlite3
import re
import hashlib
from pathlib import Path
from datetime import datetime

# 创建示例数据库
db_path = Path("custom_functions_example.db")
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 60)
print("SQLite 自定义函数示例 - 标量函数")
print("=" * 60)

# 1. 创建自定义标量函数
print("\n1. 创建自定义标量函数")

# 字符串反转函数
def reverse_string(s):
    """反转字符串"""
    if s is None:
        return None
    return s[::-1]

# 字符串首字母大写函数
def capitalize_words(s):
    """将每个单词首字母大写"""
    if s is None:
        return None
    return ' '.join(word.capitalize() for word in s.split())

# MD5哈希函数
def md5_hash(s):
    """计算字符串的MD5哈希值"""
    if s is None:
        return None
    return hashlib.md5(s.encode('utf-8')).hexdigest()

# 正则匹配函数
def regex_match(pattern, text):
    """正则表达式匹配"""
    if pattern is None or text is None:
        return None
    return 1 if re.search(pattern, text) else 0

# 计算两点间距离（欧几里得距离）
def distance(x1, y1, x2, y2):
    """计算两点间的欧几里得距离"""
    if any(v is None for v in [x1, y1, x2, y2]):
        return None
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

# 注册自定义函数
conn.create_function("reverse", 1, reverse_string)
conn.create_function("capitalize_words", 1, capitalize_words)
conn.create_function("md5", 1, md5_hash)
conn.create_function("regex_match", 2, regex_match)
conn.create_function("distance", 4, distance)

print("✅ 自定义函数注册成功")

# 2. 创建测试表
print("\n2. 创建测试表")
cursor.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        x_coord REAL,
        y_coord REAL
    )
""")

users = [
    ("alice smith", "alice@example.com", 0.0, 0.0),
    ("bob jones", "bob@example.com", 3.0, 4.0),
    ("charlie brown", "charlie@example.com", 5.0, 12.0),
]

cursor.executemany("""
    INSERT INTO users (name, email, x_coord, y_coord)
    VALUES (?, ?, ?, ?)
""", users)
conn.commit()
print(f"✅ 插入 {len(users)} 条用户记录")

# 3. 使用字符串反转函数
print("\n3. 使用字符串反转函数")
cursor.execute("""
    SELECT name, reverse(name) as reversed_name
    FROM users
""")
print("字符串反转:")
for row in cursor.fetchall():
    print(f"  原字符串: {row[0]} | 反转: {row[1]}")

# 4. 使用首字母大写函数
print("\n4. 使用首字母大写函数")
cursor.execute("""
    SELECT name, capitalize_words(name) as capitalized_name
    FROM users
""")
print("首字母大写:")
for row in cursor.fetchall():
    print(f"  原字符串: {row[0]} | 大写: {row[1]}")

# 5. 使用MD5哈希函数
print("\n5. 使用MD5哈希函数")
cursor.execute("""
    SELECT email, md5(email) as email_hash
    FROM users
    LIMIT 2
""")
print("MD5哈希:")
for row in cursor.fetchall():
    print(f"  邮箱: {row[0]} | 哈希: {row[1]}")

# 6. 使用正则匹配函数
print("\n6. 使用正则匹配函数")
cursor.execute("""
    SELECT name, email
    FROM users
    WHERE regex_match('^[a-z]+@', email) = 1
""")
print("正则匹配（邮箱以小写字母开头）:")
for row in cursor.fetchall():
    print(f"  姓名: {row[0]} | 邮箱: {row[1]}")

# 7. 使用距离计算函数
print("\n7. 使用距离计算函数")
cursor.execute("""
    SELECT 
        name,
        x_coord,
        y_coord,
        distance(0, 0, x_coord, y_coord) as dist_from_origin
    FROM users
    ORDER BY dist_from_origin
""")
print("距离原点(0,0)的距离:")
for row in cursor.fetchall():
    print(f"  姓名: {row[0]:15} | 坐标: ({row[1]}, {row[2]}) | 距离: {row[3]:.2f}")

# 8. 在WHERE子句中使用自定义函数
print("\n8. 在WHERE子句中使用自定义函数")
cursor.execute("""
    SELECT name, email
    FROM users
    WHERE distance(0, 0, x_coord, y_coord) > 5
""")
print("距离原点超过5的用户:")
for row in cursor.fetchall():
    print(f"  姓名: {row[0]} | 邮箱: {row[1]}")

# 9. 在SELECT子句中使用自定义函数
print("\n9. 在SELECT子句中使用自定义函数")
cursor.execute("""
    SELECT 
        name,
        email,
        reverse(email) as reversed_email,
        md5(name) as name_hash
    FROM users
""")
print("使用多个自定义函数:")
for row in cursor.fetchall():
    print(f"  姓名: {row[0]}")
    print(f"  邮箱: {row[1]} | 反转: {row[2]}")
    print(f"  姓名哈希: {row[3]}")
    print()

# 10. 函数组合使用
print("\n10. 函数组合使用")
cursor.execute("""
    SELECT 
        capitalize_words(name) as formatted_name,
        md5(capitalize_words(name)) as formatted_name_hash
    FROM users
""")
print("函数组合（格式化+哈希）:")
for row in cursor.fetchall():
    print(f"  格式化姓名: {row[0]} | 哈希: {row[1]}")

# 清理
conn.close()
if db_path.exists():
    db_path.unlink()
    print(f"\n✅ 清理完成，已删除 {db_path}")

print("\n" + "=" * 60)
print("示例完成！")
print("=" * 60)
print("\n💡 自定义标量函数要点:")
print("  1. 使用conn.create_function()注册函数")
print("  2. 函数参数数量必须匹配")
print("  3. 函数可以返回任何SQLite支持的类型")
print("  4. 函数可以在SELECT、WHERE等子句中使用")
print("  5. 函数可以组合使用")
