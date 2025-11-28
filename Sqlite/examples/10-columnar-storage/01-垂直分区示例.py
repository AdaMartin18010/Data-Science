#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
垂直分区（列分离）示例

将宽表拆分为多个窄表，模拟列存储的优势：
- 查询时只扫描需要的列
- 减少I/O，提升查询性能
- 适合宽表、查询部分列的场景
"""

import sqlite3
import time
import os

def create_sample_data(conn):
    """创建示例数据"""
    cursor = conn.cursor()
    
    # 创建原始宽表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users_full (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            profile_text TEXT,
            metadata_json TEXT,
            created_at INTEGER,
            updated_at INTEGER
        )
    """)
    
    # 插入测试数据
    import random
    names = ['Alice', 'Bob', 'Charlie', 'David', 'Eve']
    actions = ['login', 'logout', 'view', 'edit', 'delete']
    
    data = []
    for i in range(10000):
        data.append((
            f"User_{i}",
            f"user{i}@example.com",
            f"138{i:08d}",
            f"Address {i}",
            f"Profile text for user {i} " * 10,  # 长文本
            f'{{"action": "{random.choice(actions)}", "count": {random.randint(1, 100)}}}',
            int(time.time()) - random.randint(0, 86400 * 30),
            int(time.time())
        ))
    
    cursor.executemany("""
        INSERT INTO users_full (name, email, phone, address, profile_text, metadata_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    
    conn.commit()
    print(f"✅ 创建了 {len(data)} 条测试数据")

def create_vertical_partition(conn):
    """创建垂直分区"""
    cursor = conn.cursor()
    
    # 核心表（常用列）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users_core (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            phone TEXT,
            created_at INTEGER,
            updated_at INTEGER
        )
    """)
    
    # 扩展表（不常用列）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users_extended (
            id INTEGER PRIMARY KEY,
            address TEXT,
            profile_text TEXT,
            metadata_json TEXT,
            FOREIGN KEY (id) REFERENCES users_core(id)
        )
    """)
    
    # 从原始表复制数据
    cursor.execute("""
        INSERT INTO users_core (id, name, email, phone, created_at, updated_at)
        SELECT id, name, email, phone, created_at, updated_at
        FROM users_full
    """)
    
    cursor.execute("""
        INSERT INTO users_extended (id, address, profile_text, metadata_json)
        SELECT id, address, profile_text, metadata_json
        FROM users_full
    """)
    
    conn.commit()
    print("✅ 垂直分区创建完成")

def compare_query_performance(conn):
    """对比查询性能"""
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("查询性能对比")
    print("="*60)
    
    # 查询1：只查询核心列
    print("\n查询1：只查询核心列（name, email, phone）")
    
    # 原始表查询
    start = time.time()
    cursor.execute("""
        SELECT id, name, email, phone FROM users_full WHERE id < 1000
    """)
    results1 = cursor.fetchall()
    time1 = time.time() - start
    print(f"  原始表查询: {time1*1000:.2f}ms, 返回 {len(results1)} 行")
    
    # 分区表查询
    start = time.time()
    cursor.execute("""
        SELECT id, name, email, phone FROM users_core WHERE id < 1000
    """)
    results2 = cursor.fetchall()
    time2 = time.time() - start
    print(f"  分区表查询: {time2*1000:.2f}ms, 返回 {len(results2)} 行")
    print(f"  性能提升: {time1/time2:.2f}x")
    
    # 查询2：查询所有列
    print("\n查询2：查询所有列（需要JOIN）")
    
    # 原始表查询
    start = time.time()
    cursor.execute("""
        SELECT * FROM users_full WHERE id < 1000
    """)
    results3 = cursor.fetchall()
    time3 = time.time() - start
    print(f"  原始表查询: {time3*1000:.2f}ms, 返回 {len(results3)} 行")
    
    # 分区表查询（需要JOIN）
    start = time.time()
    cursor.execute("""
        SELECT c.*, e.address, e.profile_text, e.metadata_json
        FROM users_core c
        LEFT JOIN users_extended e ON c.id = e.id
        WHERE c.id < 1000
    """)
    results4 = cursor.fetchall()
    time4 = time.time() - start
    print(f"  分区表查询（JOIN）: {time4*1000:.2f}ms, 返回 {len(results4)} 行")
    print(f"  性能变化: {time3/time4:.2f}x")
    
    # 查询3：只查询扩展列
    print("\n查询3：只查询扩展列（address, profile_text）")
    
    # 原始表查询
    start = time.time()
    cursor.execute("""
        SELECT id, address, profile_text FROM users_full WHERE id < 1000
    """)
    results5 = cursor.fetchall()
    time5 = time.time() - start
    print(f"  原始表查询: {time5*1000:.2f}ms, 返回 {len(results5)} 行")
    
    # 分区表查询
    start = time.time()
    cursor.execute("""
        SELECT id, address, profile_text FROM users_extended WHERE id < 1000
    """)
    results6 = cursor.fetchall()
    time6 = time.time() - start
    print(f"  分区表查询: {time6*1000:.2f}ms, 返回 {len(results6)} 行")
    print(f"  性能提升: {time5/time6:.2f}x")

def compare_storage_size(conn):
    """对比存储大小"""
    cursor = conn.cursor()
    
    # 获取表大小（页数）
    def get_table_size(table_name):
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        return count
    
    print("\n" + "="*60)
    print("存储大小对比")
    print("="*60)
    
    full_count = get_table_size('users_full')
    core_count = get_table_size('users_core')
    extended_count = get_table_size('users_extended')
    
    print(f"\n原始表 (users_full): {full_count} 行")
    print(f"核心表 (users_core): {core_count} 行")
    print(f"扩展表 (users_extended): {extended_count} 行")
    
    # 注意：实际存储大小需要考虑列的大小
    print("\n💡 提示：分区表的总存储大小可能略大于原始表（因为需要存储外键），")
    print("   但查询时只扫描需要的表，I/O减少，性能提升。")

def main():
    """主函数"""
    db_path = 'vertical_partition_example.db'
    
    # 删除旧数据库
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    
    print("="*60)
    print("垂直分区（列分离）示例")
    print("="*60)
    
    # 创建示例数据
    print("\n1. 创建示例数据...")
    create_sample_data(conn)
    
    # 创建垂直分区
    print("\n2. 创建垂直分区...")
    create_vertical_partition(conn)
    
    # 对比查询性能
    print("\n3. 对比查询性能...")
    compare_query_performance(conn)
    
    # 对比存储大小
    print("\n4. 对比存储大小...")
    compare_storage_size(conn)
    
    print("\n" + "="*60)
    print("示例完成！")
    print("="*60)
    print(f"\n数据库文件: {db_path}")
    print("\n💡 总结：")
    print("  - 查询只涉及核心列时，分区表性能显著提升")
    print("  - 查询所有列时，需要JOIN，性能可能略降")
    print("  - 适合宽表、查询部分列的场景")
    
    conn.close()

if __name__ == '__main__':
    main()
