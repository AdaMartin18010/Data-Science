#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 递归CTE示例 - 树形结构查询

演示递归CTE在树形结构查询中的应用：
- 组织架构树查询
- 分类树查询
- 递归路径查询

适用版本：SQLite 3.31+ 至 3.47.x
最后更新：2025-01-15
"""

import sqlite3
from pathlib import Path

# 创建示例数据库
db_path = Path("recursive_cte_tree_example.db")
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 60)
print("SQLite 递归CTE示例 - 树形结构查询")
print("=" * 60)

# 1. 创建组织架构表
print("\n1. 创建组织架构表")
cursor.execute("""
    CREATE TABLE employees (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        position TEXT NOT NULL,
        manager_id INTEGER,
        FOREIGN KEY (manager_id) REFERENCES employees(id)
    )
""")

# 插入组织架构数据
employees = [
    (1, "CEO", "首席执行官", None),
    (2, "CTO", "首席技术官", 1),
    (3, "CFO", "首席财务官", 1),
    (4, "技术总监", "技术总监", 2),
    (5, "产品总监", "产品总监", 2),
    (6, "财务经理", "财务经理", 3),
    (7, "高级工程师", "高级工程师", 4),
    (8, "工程师", "工程师", 4),
    (9, "产品经理", "产品经理", 5),
    (10, "产品助理", "产品助理", 5),
    (11, "会计师", "会计师", 6),
]

cursor.executemany("""
    INSERT INTO employees (id, name, position, manager_id)
    VALUES (?, ?, ?, ?)
""", employees)
conn.commit()
print(f"✅ 插入 {len(employees)} 条员工记录")

# 2. 查询所有下属（向下递归）
print("\n2. 查询所有下属（向下递归）")
print("查询CTO的所有下属:")
cursor.execute("""
    WITH RECURSIVE subordinates AS (
        -- 基础查询：起始节点（CTO）
        SELECT id, name, position, manager_id, 0 as level
        FROM employees
        WHERE name = 'CTO'
        
        UNION ALL
        
        -- 递归查询：查找下属
        SELECT e.id, e.name, e.position, e.manager_id, s.level + 1
        FROM employees e
        INNER JOIN subordinates s ON e.manager_id = s.id
    )
    SELECT 
        printf('%*s', level * 2, '') || name as hierarchy,
        position,
        level
    FROM subordinates
    ORDER BY level, name
""")
print("-" * 60)
for row in cursor.fetchall():
    print(f"{row[0]} ({row[1]}) - 层级: {row[2]}")

# 3. 查询所有上级（向上递归）
print("\n3. 查询所有上级（向上递归）")
print("查询工程师的所有上级:")
cursor.execute("""
    WITH RECURSIVE managers AS (
        -- 基础查询：起始节点（工程师）
        SELECT id, name, position, manager_id, 0 as level
        FROM employees
        WHERE name = '工程师'
        
        UNION ALL
        
        -- 递归查询：查找上级
        SELECT e.id, e.name, e.position, e.manager_id, m.level + 1
        FROM employees e
        INNER JOIN managers m ON e.id = m.manager_id
    )
    SELECT 
        name,
        position,
        level
    FROM managers
    ORDER BY level DESC
""")
print("-" * 60)
for row in cursor.fetchall():
    print(f"层级 {row[2]}: {row[0]} ({row[1]})")

# 4. 查询完整路径
print("\n4. 查询完整路径（从根到叶子）")
print("查询每个员工的完整汇报路径:")
cursor.execute("""
    WITH RECURSIVE employee_paths AS (
        -- 基础查询：所有员工
        SELECT id, name, position, manager_id, name as path, 0 as level
        FROM employees
        
        UNION ALL
        
        -- 递归查询：构建路径
        SELECT e.id, e.name, e.position, e.manager_id, 
               ep.path || ' -> ' || e.name, ep.level + 1
        FROM employees e
        INNER JOIN employee_paths ep ON e.manager_id = ep.id
    )
    SELECT 
        name,
        position,
        path,
        level
    FROM employee_paths
    WHERE manager_id IS NULL OR id NOT IN (
        SELECT manager_id FROM employees WHERE manager_id IS NOT NULL
    )
    ORDER BY path
""")
print("-" * 80)
for row in cursor.fetchall():
    print(f"{row[0]} ({row[1]}) - 路径: {row[2]} - 层级: {row[3]}")

# 5. 创建分类表
print("\n5. 创建分类表")
cursor.execute("""
    CREATE TABLE categories (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        parent_id INTEGER,
        FOREIGN KEY (parent_id) REFERENCES categories(id)
    )
""")

# 插入分类数据
categories = [
    (1, "电子产品", None),
    (2, "电脑", 1),
    (3, "手机", 1),
    (4, "笔记本", 2),
    (5, "台式机", 2),
    (6, "智能手机", 3),
    (7, "功能手机", 3),
    (8, "游戏本", 4),
    (9, "商务本", 4),
]

cursor.executemany("""
    INSERT INTO categories (id, name, parent_id)
    VALUES (?, ?, ?)
""", categories)
conn.commit()
print(f"✅ 插入 {len(categories)} 条分类记录")

# 6. 查询分类树
print("\n6. 查询分类树")
print("查询'电子产品'分类下的所有子分类:")
cursor.execute("""
    WITH RECURSIVE category_tree AS (
        -- 基础查询：起始分类
        SELECT id, name, parent_id, 0 as level, name as path
        FROM categories
        WHERE name = '电子产品'
        
        UNION ALL
        
        -- 递归查询：查找子分类
        SELECT c.id, c.name, c.parent_id, ct.level + 1, 
               ct.path || ' > ' || c.name
        FROM categories c
        INNER JOIN category_tree ct ON c.parent_id = ct.id
    )
    SELECT 
        printf('%*s', level * 2, '') || name as hierarchy,
        path,
        level
    FROM category_tree
    ORDER BY path
""")
print("-" * 80)
for row in cursor.fetchall():
    print(f"{row[0]} - 路径: {row[1]} - 层级: {row[2]}")

# 7. 统计每个分类的子分类数量
print("\n7. 统计每个分类的子分类数量")
cursor.execute("""
    WITH RECURSIVE category_counts AS (
        -- 基础查询：所有分类
        SELECT id, name, parent_id, 0 as direct_children
        FROM categories
        
        UNION ALL
        
        -- 递归查询：计算子分类
        SELECT c.id, c.name, c.parent_id, cc.direct_children + 1
        FROM categories c
        INNER JOIN category_counts cc ON c.parent_id = cc.id
    ),
    category_stats AS (
        SELECT 
            id,
            name,
            parent_id,
            COUNT(*) - 1 as total_children
        FROM category_counts
        GROUP BY id, name, parent_id
    )
    SELECT 
        cs.name,
        COALESCE(p.name, '根分类') as parent_name,
        cs.total_children
    FROM category_stats cs
    LEFT JOIN categories p ON cs.parent_id = p.id
    ORDER BY cs.total_children DESC
""")
print("-" * 60)
for row in cursor.fetchall():
    print(f"{row[0]:15} | 父分类: {row[1]:10} | 子分类数: {row[2]}")

# 8. 查找叶子节点（没有子节点的节点）
print("\n8. 查找叶子节点（没有子节点的节点）")
cursor.execute("""
    WITH RECURSIVE all_categories AS (
        -- 基础查询：所有分类
        SELECT id, name, parent_id
        FROM categories
        
        UNION ALL
        
        -- 递归查询：所有子分类
        SELECT c.id, c.name, c.parent_id
        FROM categories c
        INNER JOIN all_categories ac ON c.parent_id = ac.id
    )
    SELECT DISTINCT name
    FROM all_categories
    WHERE id NOT IN (
        SELECT DISTINCT parent_id 
        FROM categories 
        WHERE parent_id IS NOT NULL
    )
    ORDER BY name
""")
print("-" * 40)
for row in cursor.fetchall():
    print(f"叶子节点: {row[0]}")

# 9. 查找特定深度的节点
print("\n9. 查找特定深度的节点")
print("查找深度为2的节点:")
cursor.execute("""
    WITH RECURSIVE depth_nodes AS (
        -- 基础查询：根节点
        SELECT id, name, parent_id, 0 as depth
        FROM categories
        WHERE parent_id IS NULL
        
        UNION ALL
        
        -- 递归查询：增加深度
        SELECT c.id, c.name, c.parent_id, dn.depth + 1
        FROM categories c
        INNER JOIN depth_nodes dn ON c.parent_id = dn.id
    )
    SELECT name, depth
    FROM depth_nodes
    WHERE depth = 2
    ORDER BY name
""")
print("-" * 40)
for row in cursor.fetchall():
    print(f"{row[0]} - 深度: {row[1]}")

# 10. 查找两个节点之间的路径
print("\n10. 查找两个节点之间的路径")
print("查找'游戏本'到'电子产品'的路径:")
cursor.execute("""
    WITH RECURSIVE path_to_root AS (
        -- 基础查询：起始节点
        SELECT id, name, parent_id, name as path
        FROM categories
        WHERE name = '游戏本'
        
        UNION ALL
        
        -- 递归查询：向上查找
        SELECT c.id, c.name, c.parent_id, ptr.path || ' <- ' || c.name
        FROM categories c
        INNER JOIN path_to_root ptr ON c.id = ptr.parent_id
    )
    SELECT path
    FROM path_to_root
    WHERE parent_id IS NULL
""")
row = cursor.fetchone()
if row:
    print(f"路径: {row[0]}")

# 清理
conn.close()
if db_path.exists():
    db_path.unlink()
    print(f"\n✅ 清理完成，已删除 {db_path}")

print("\n" + "=" * 60)
print("示例完成！")
print("=" * 60)
print("\n💡 递归CTE要点:")
print("  1. 基础查询：定义起始节点")
print("  2. 递归查询：定义递归关系")
print("  3. 终止条件：当没有更多匹配行时停止")
print("  4. 可以向上递归（查找父节点）或向下递归（查找子节点）")
