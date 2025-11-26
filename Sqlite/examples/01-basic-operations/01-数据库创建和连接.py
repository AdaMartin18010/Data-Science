#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 基础操作示例：数据库创建和连接

> **难度**：⭐ 入门级
> **适用版本**：SQLite 3.31+ 至 3.47.x
> **最后更新**：2025-01-15
"""

import sqlite3
import os

def example_01_create_database():
    """示例1：创建数据库文件"""
    print("=" * 50)
    print("示例1：创建数据库文件")
    print("=" * 50)
    
    # 创建数据库连接（如果文件不存在会自动创建）
    db_path = 'example.db'
    conn = sqlite3.connect(db_path)
    
    print(f"✅ 数据库已创建：{db_path}")
    print(f"   文件大小：{os.path.getsize(db_path)} bytes")
    
    conn.close()
    print("✅ 连接已关闭\n")


def example_02_connect_to_database():
    """示例2：连接到数据库"""
    print("=" * 50)
    print("示例2：连接到数据库")
    print("=" * 50)
    
    db_path = 'example.db'
    
    # 方式1：基本连接
    conn = sqlite3.connect(db_path)
    print("✅ 基本连接成功")
    conn.close()
    
    # 方式2：使用上下文管理器（推荐）
    with sqlite3.connect(db_path) as conn:
        print("✅ 使用上下文管理器连接成功")
        # 连接会在退出with块时自动关闭
    
    print()


def example_03_memory_database():
    """示例3：内存数据库"""
    print("=" * 50)
    print("示例3：内存数据库")
    print("=" * 50)
    
    # 使用:memory:创建内存数据库
    conn = sqlite3.connect(':memory:')
    
    # 创建表
    conn.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    ''')
    
    # 插入数据
    conn.execute("INSERT INTO users (name) VALUES ('Alice')")
    conn.commit()
    
    # 查询数据
    result = conn.execute("SELECT * FROM users").fetchall()
    print(f"✅ 内存数据库查询结果：{result}")
    
    conn.close()
    print("✅ 内存数据库连接已关闭\n")


def example_04_connection_configuration():
    """示例4：连接配置"""
    print("=" * 50)
    print("示例4：连接配置")
    print("=" * 50)
    
    db_path = 'example.db'
    
    with sqlite3.connect(db_path) as conn:
        # 配置PRAGMA
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL')
        conn.execute('PRAGMA foreign_keys=ON')
        
        # 检查配置
        journal_mode = conn.execute('PRAGMA journal_mode').fetchone()[0]
        print(f"✅ 日志模式：{journal_mode}")
        
        foreign_keys = conn.execute('PRAGMA foreign_keys').fetchone()[0]
        print(f"✅ 外键约束：{foreign_keys}")
    
    print()


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("SQLite 基础操作示例：数据库创建和连接")
    print("=" * 50 + "\n")
    
    # 运行示例
    example_01_create_database()
    example_02_connect_to_database()
    example_03_memory_database()
    example_04_connection_configuration()
    
    # 清理
    if os.path.exists('example.db'):
        os.remove('example.db')
        print("✅ 示例数据库已清理\n")
    
    print("=" * 50)
    print("所有示例执行完成！")
    print("=" * 50)
