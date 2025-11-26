#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 递归CTE示例 - 层级数据查询

演示递归CTE在层级数据查询中的应用：
- 多级分类查询
- 评论回复树查询
- 权限继承查询

适用版本：SQLite 3.31+ 至 3.47.x
最后更新：2025-01-15
"""

import sqlite3
from pathlib import Path

# 创建示例数据库
db_path = Path("recursive_cte_hierarchy_example.db")
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 60)
print("SQLite 递归CTE示例 - 层级数据查询")
print("=" * 60)

# 1. 创建评论表
print("\n1. 创建评论表")
cursor.execute("""
    CREATE TABLE comments (
        id INTEGER PRIMARY KEY,
        content TEXT NOT NULL,
        author TEXT NOT NULL,
        parent_id INTEGER,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (parent_id) REFERENCES comments(id)
    )
""")

# 插入评论数据（模拟论坛评论）
comments = [
    (1, "这篇文章写得真好！", "用户A", None, "2025-01-10 10:00:00"),
    (2, "我也觉得不错", "用户B", 1, "2025-01-10 10:05:00"),
    (3, "同意楼上的观点", "用户C", 2, "2025-01-10 10:10:00"),
    (4, "但是有些地方可以改进", "用户D", 1, "2025-01-10 10:15:00"),
    (5, "具体是哪些地方？", "用户E", 4, "2025-01-10 10:20:00"),
    (6, "比如第三段", "用户D", 5, "2025-01-10 10:25:00"),
    (7, "感谢大家的反馈", "用户A", 1, "2025-01-10 10:30:00"),
    (8, "期待更多好文章", "用户F", None, "2025-01-10 11:00:00"),
    (9, "同期待", "用户G", 8, "2025-01-10 11:05:00"),
]

cursor.executemany("""
    INSERT INTO comments (id, content, author, parent_id, created_at)
    VALUES (?, ?, ?, ?, ?)
""", comments)
conn.commit()
print(f"✅ 插入 {len(comments)} 条评论记录")

# 2. 查询评论树（显示所有回复）
print("\n2. 查询评论树（显示所有回复）")
print("查询第一条评论的所有回复:")
cursor.execute("""
    WITH RECURSIVE comment_tree AS (
        -- 基础查询：根评论
        SELECT id, content, author, parent_id, created_at, 0 as level
        FROM comments
        WHERE id = 1
        
        UNION ALL
        
        -- 递归查询：查找回复
        SELECT c.id, c.content, c.author, c.parent_id, c.created_at, ct.level + 1
        FROM comments c
        INNER JOIN comment_tree ct ON c.parent_id = ct.id
    )
    SELECT 
        printf('%*s', level * 3, '') || '└─ ' || author as hierarchy,
        content,
        created_at,
        level
    FROM comment_tree
    ORDER BY created_at
""")
print("-" * 80)
for row in cursor.fetchall():
    print(f"{row[0]}")
    print(f"  {row[1]}")
    print(f"  时间: {row[2]}")
    print()

# 3. 统计每个评论的回复数量
print("\n3. 统计每个评论的回复数量")
cursor.execute("""
    WITH RECURSIVE reply_counts AS (
        -- 基础查询：所有评论
        SELECT id, content, author, parent_id, 0 as reply_count
        FROM comments
        
        UNION ALL
        
        -- 递归查询：计算回复数
        SELECT rc.id, rc.content, rc.author, rc.parent_id, rc.reply_count + 1
        FROM reply_counts rc
        INNER JOIN comments c ON c.parent_id = rc.id
    ),
    comment_stats AS (
        SELECT 
            id,
            content,
            author,
            parent_id,
            COUNT(*) - 1 as total_replies
        FROM reply_counts
        GROUP BY id, content, author, parent_id
    )
    SELECT 
        cs.id,
        cs.author,
        LEFT(cs.content, 30) || '...' as content_preview,
        cs.total_replies
    FROM comment_stats cs
    ORDER BY cs.total_replies DESC
""")
print("-" * 80)
for row in cursor.fetchall():
    print(f"ID {row[0]}: {row[1]} - {row[2]}")
    print(f"  回复数: {row[3]}")
    print()

# 4. 创建权限表
print("\n4. 创建权限表")
cursor.execute("""
    CREATE TABLE permissions (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        parent_id INTEGER,
        FOREIGN KEY (parent_id) REFERENCES permissions(id)
    )
""")

# 插入权限数据（权限继承）
permissions = [
    (1, "系统管理", None),
    (2, "用户管理", 1),
    (3, "角色管理", 1),
    (4, "创建用户", 2),
    (5, "删除用户", 2),
    (6, "编辑用户", 2),
    (7, "创建角色", 3),
    (8, "分配权限", 3),
    (9, "内容管理", None),
    (10, "文章管理", 9),
    (11, "发布文章", 10),
    (12, "删除文章", 10),
]

cursor.executemany("""
    INSERT INTO permissions (id, name, parent_id)
    VALUES (?, ?, ?)
""", permissions)
conn.commit()
print(f"✅ 插入 {len(permissions)} 条权限记录")

# 5. 查询权限继承（所有子权限）
print("\n5. 查询权限继承（所有子权限）")
print("查询'系统管理'权限下的所有子权限:")
cursor.execute("""
    WITH RECURSIVE permission_tree AS (
        -- 基础查询：起始权限
        SELECT id, name, parent_id, 0 as level
        FROM permissions
        WHERE name = '系统管理'
        
        UNION ALL
        
        -- 递归查询：查找子权限
        SELECT p.id, p.name, p.parent_id, pt.level + 1
        FROM permissions p
        INNER JOIN permission_tree pt ON p.parent_id = pt.id
    )
    SELECT 
        printf('%*s', level * 2, '') || name as hierarchy,
        level
    FROM permission_tree
    ORDER BY level, name
""")
print("-" * 60)
for row in cursor.fetchall():
    print(f"{row[0]} - 层级: {row[1]}")

# 6. 查询用户拥有的所有权限（包括继承的）
print("\n6. 查询用户拥有的所有权限（包括继承的）")
# 创建用户权限关联表
cursor.execute("""
    CREATE TABLE user_permissions (
        user_id INTEGER,
        permission_id INTEGER,
        PRIMARY KEY (user_id, permission_id),
        FOREIGN KEY (permission_id) REFERENCES permissions(id)
    )
""")

# 假设用户1直接拥有"用户管理"权限，应该继承所有子权限
cursor.execute("""
    INSERT INTO user_permissions (user_id, permission_id)
    VALUES (1, 2)  -- 用户1拥有"用户管理"权限
""")
conn.commit()

print("查询用户1的所有权限（包括继承的）:")
cursor.execute("""
    WITH RECURSIVE user_all_permissions AS (
        -- 基础查询：用户直接拥有的权限
        SELECT p.id, p.name, p.parent_id
        FROM permissions p
        INNER JOIN user_permissions up ON p.id = up.permission_id
        WHERE up.user_id = 1
        
        UNION ALL
        
        -- 递归查询：查找所有子权限
        SELECT p.id, p.name, p.parent_id
        FROM permissions p
        INNER JOIN user_all_permissions uap ON p.parent_id = uap.id
    )
    SELECT DISTINCT name
    FROM user_all_permissions
    ORDER BY name
""")
print("-" * 40)
for row in cursor.fetchall():
    print(f"  - {row[0]}")

# 7. 查找权限路径（从根到叶子）
print("\n7. 查找权限路径（从根到叶子）")
print("查找每个权限的完整路径:")
cursor.execute("""
    WITH RECURSIVE permission_paths AS (
        -- 基础查询：根权限
        SELECT id, name, parent_id, name as path
        FROM permissions
        WHERE parent_id IS NULL
        
        UNION ALL
        
        -- 递归查询：构建路径
        SELECT p.id, p.name, p.parent_id, pp.path || ' > ' || p.name
        FROM permissions p
        INNER JOIN permission_paths pp ON p.parent_id = pp.id
    )
    SELECT name, path
    FROM permission_paths
    WHERE id NOT IN (SELECT DISTINCT parent_id FROM permissions WHERE parent_id IS NOT NULL)
    ORDER BY path
""")
print("-" * 80)
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]}")

# 8. 查找共同祖先
print("\n8. 查找两个权限的共同祖先")
print("查找'创建用户'和'角色管理'的共同祖先:")
cursor.execute("""
    WITH RECURSIVE ancestors1 AS (
        SELECT id, name, parent_id
        FROM permissions
        WHERE name = '创建用户'
        
        UNION ALL
        
        SELECT p.id, p.name, p.parent_id
        FROM permissions p
        INNER JOIN ancestors1 a ON p.id = a.parent_id
    ),
    ancestors2 AS (
        SELECT id, name, parent_id
        FROM permissions
        WHERE name = '角色管理'
        
        UNION ALL
        
        SELECT p.id, p.name, p.parent_id
        FROM permissions p
        INNER JOIN ancestors2 a ON p.id = a.parent_id
    )
    SELECT a1.name
    FROM ancestors1 a1
    INNER JOIN ancestors2 a2 ON a1.id = a2.id
    WHERE a1.parent_id IS NOT NULL
    ORDER BY a1.id
    LIMIT 1
""")
row = cursor.fetchone()
if row:
    print(f"共同祖先: {row[0]}")

# 清理
conn.close()
if db_path.exists():
    db_path.unlink()
    print(f"\n✅ 清理完成，已删除 {db_path}")

print("\n" + "=" * 60)
print("示例完成！")
print("=" * 60)
print("\n💡 层级数据查询要点:")
print("  1. 评论系统：使用递归CTE构建评论树")
print("  2. 权限系统：使用递归CTE实现权限继承")
print("  3. 分类系统：使用递归CTE查询多级分类")
print("  4. 可以向上查找（祖先）或向下查找（后代）")
