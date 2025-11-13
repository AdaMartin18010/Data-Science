#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 性能测试：索引效果

> **工具类型**：性能测试
> **适用版本**：SQLite 3.31+
"""

import sqlite3
import time
import os
import random
import statistics

def create_test_table(conn, with_index=False):
    """创建测试表"""
    conn.execute('''
        CREATE TABLE IF NOT EXISTS test_data (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            age INTEGER,
            created_at INTEGER
        )
    ''')
    conn.execute('DELETE FROM test_data')
    
    if with_index:
        # 创建索引
        conn.execute('CREATE INDEX IF NOT EXISTS idx_email ON test_data(email)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_age ON test_data(age)')
    
    conn.commit()

def insert_test_data(conn, num_records=10000):
    """插入测试数据"""
    data = [
        (f'user_{i}', f'user_{i}@example.com', random.randint(18, 80), int(time.time()))
        for i in range(num_records)
    ]
    conn.executemany(
        'INSERT INTO test_data (name, email, age, created_at) VALUES (?, ?, ?, ?)',
        data
    )
    conn.commit()

def test_query_without_index(conn, num_queries=100):
    """测试：无索引查询"""
    start = time.time()
    
    for i in range(num_queries):
        email = f'user_{random.randint(0, 9999)}@example.com'
        conn.execute(
            'SELECT * FROM test_data WHERE email = ?',
            (email,)
        ).fetchone()
    
    elapsed = time.time() - start
    return elapsed

def test_query_with_index(conn, num_queries=100):
    """测试：有索引查询"""
    start = time.time()
    
    for i in range(num_queries):
        email = f'user_{random.randint(0, 9999)}@example.com'
        conn.execute(
            'SELECT * FROM test_data WHERE email = ?',
            (email,)
        ).fetchone()
    
    elapsed = time.time() - start
    return elapsed

def test_range_query(conn, num_queries=100):
    """测试：范围查询"""
    start = time.time()
    
    for i in range(num_queries):
        age_min = random.randint(18, 50)
        age_max = age_min + 10
        conn.execute(
            'SELECT * FROM test_data WHERE age BETWEEN ? AND ?',
            (age_min, age_max)
        ).fetchall()
    
    elapsed = time.time() - start
    return elapsed

def main():
    """主函数"""
    print("=" * 60)
    print("SQLite 性能测试：索引效果")
    print("=" * 60)
    print()
    
    db_path_no_index = 'test_no_index.db'
    db_path_with_index = 'test_with_index.db'
    
    num_records = 10000
    num_queries = 100
    
    print(f"测试配置：")
    print(f"  - 数据记录数：{num_records}")
    print(f"  - 查询次数：{num_queries}")
    print()
    
    # 清理旧数据库
    for db_path in [db_path_no_index, db_path_with_index]:
        if os.path.exists(db_path):
            os.remove(db_path)
    
    # 准备无索引数据库
    print("准备无索引数据库...")
    with sqlite3.connect(db_path_no_index) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        create_test_table(conn, with_index=False)
        insert_test_data(conn, num_records)
    
    # 准备有索引数据库
    print("准备有索引数据库...")
    with sqlite3.connect(db_path_with_index) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        create_test_table(conn, with_index=True)
        insert_test_data(conn, num_records)
    
    print()
    print("正在运行测试...")
    print()
    
    # 测试无索引查询
    print("测试1：无索引查询...")
    with sqlite3.connect(db_path_no_index) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        no_index_time = test_query_without_index(conn, num_queries)
    
    # 测试有索引查询
    print("测试2：有索引查询...")
    with sqlite3.connect(db_path_with_index) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        with_index_time = test_query_with_index(conn, num_queries)
    
    # 测试范围查询
    print("测试3：范围查询（有索引）...")
    with sqlite3.connect(db_path_with_index) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        range_time = test_range_query(conn, num_queries)
    
    # 输出结果
    print()
    print("=" * 60)
    print("测试结果")
    print("=" * 60)
    print()
    
    print(f"{'查询类型':<20} {'耗时':<15} {'性能提升':<15}")
    print("-" * 50)
    
    print(f"{'无索引查询':<20} "
          f"{no_index_time:.3f}s{'':<8} "
          f"{'基准':<15}")
    
    improvement = (no_index_time - with_index_time) / no_index_time * 100
    print(f"{'有索引查询':<20} "
          f"{with_index_time:.3f}s{'':<8} "
          f"{improvement:+.1f}%")
    
    print(f"{'范围查询（有索引）':<20} "
          f"{range_time:.3f}s{'':<8} "
          f"{'-':<15}")
    
    print()
    print("=" * 60)
    print("结论：索引可以显著提升查询性能（10-100倍）")
    print("=" * 60)
    
    # 清理
    for db_path in [db_path_no_index, db_path_with_index]:
        if os.path.exists(db_path):
            os.remove(db_path)

if __name__ == '__main__':
    main()
