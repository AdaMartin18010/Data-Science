#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 基础操作示例：表创建和数据操作

> **难度**：⭐ 入门级
> **适用版本**：SQLite 3.31+
"""

import sqlite3
import os

def example_01_create_table():
    """示例1：创建表"""
    print("=" * 50)
    print("示例1：创建表")
    print("=" * 50)
    
    db_path = 'example.db'
    
    with sqlite3.connect(db_path) as conn:
        # 创建用户表
        conn.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                age INTEGER,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        ''')
        
        print("✅ 用户表已创建")
        
        # 查看表结构
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("\n表结构：")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    
    print()


def example_02_insert_data():
    """示例2：插入数据"""
    print("=" * 50)
    print("示例2：插入数据")
    print("=" * 50)
    
    db_path = 'example.db'
    
    with sqlite3.connect(db_path) as conn:
        # 方式1：单条插入
        conn.execute(
            "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
            ('Alice', 'alice@example.com', 25)
        )
        print("✅ 单条插入成功")
        
        # 方式2：批量插入
        users = [
            ('Bob', 'bob@example.com', 30),
            ('Charlie', 'charlie@example.com', 35),
            ('David', 'david@example.com', 28)
        ]
        conn.executemany(
            "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
            users
        )
        print("✅ 批量插入成功（3条记录）")
        
        conn.commit()
        print("✅ 事务已提交\n")


def example_03_query_data():
    """示例3：查询数据"""
    print("=" * 50)
    print("示例3：查询数据")
    print("=" * 50)
    
    db_path = 'example.db'
    
    with sqlite3.connect(db_path) as conn:
        # 查询所有数据
        print("所有用户：")
        cursor = conn.execute("SELECT * FROM users")
        for row in cursor:
            print(f"  {row}")
        
        # 条件查询
        print("\n年龄大于28的用户：")
        cursor = conn.execute(
            "SELECT name, age FROM users WHERE age > ?",
            (28,)
        )
        for row in cursor:
            print(f"  {row[0]}: {row[1]}岁")
        
        # 聚合查询
        avg_age = conn.execute("SELECT AVG(age) FROM users").fetchone()[0]
        print(f"\n平均年龄：{avg_age:.1f}岁")
    
    print()


def example_04_update_and_delete():
    """示例4：更新和删除"""
    print("=" * 50)
    print("示例4：更新和删除")
    print("=" * 50)
    
    db_path = 'example.db'
    
    with sqlite3.connect(db_path) as conn:
        # 更新数据
        conn.execute(
            "UPDATE users SET age = ? WHERE name = ?",
            (26, 'Alice')
        )
        print("✅ Alice的年龄已更新为26")
        
        # 删除数据
        conn.execute("DELETE FROM users WHERE name = ?", ('David',))
        print("✅ David的记录已删除")
        
        conn.commit()
        
        # 验证
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        print(f"✅ 当前用户数：{count}")
    
    print()


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("SQLite 基础操作示例：表创建和数据操作")
    print("=" * 50 + "\n")
    
    # 清理旧数据库
    if os.path.exists('example.db'):
        os.remove('example.db')
    
    # 运行示例
    example_01_create_table()
    example_02_insert_data()
    example_03_query_data()
    example_04_update_and_delete()
    
    # 清理
    if os.path.exists('example.db'):
        os.remove('example.db')
        print("✅ 示例数据库已清理\n")
    
    print("=" * 50)
    print("所有示例执行完成！")
    print("=" * 50)
