#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 性能测试：WAL vs DELETE模式对比

> **工具类型**：性能测试
> **适用版本**：SQLite 3.31+
"""

import sqlite3
import time
import os
import statistics

def create_test_table(conn):
    """创建测试表"""
    conn.execute('''
        CREATE TABLE IF NOT EXISTS test_data (
            id INTEGER PRIMARY KEY,
            value TEXT,
            created_at INTEGER
        )
    ''')
    conn.execute('DELETE FROM test_data')
    conn.commit()

def test_write_performance(conn, num_records=10000):
    """测试写入性能"""
    start = time.time()
    
    conn.execute('BEGIN')
    for i in range(num_records):
        conn.execute(
            'INSERT INTO test_data (value, created_at) VALUES (?, ?)',
            (f'value_{i}', int(time.time()))
        )
    conn.commit()
    
    elapsed = time.time() - start
    return elapsed

def test_read_performance(conn, num_queries=1000):
    """测试读取性能"""
    start = time.time()
    
    for i in range(num_queries):
        conn.execute(
            'SELECT * FROM test_data WHERE id = ?',
            (i % 10000 + 1,)
        ).fetchone()
    
    elapsed = time.time() - start
    return elapsed

def run_test(mode, num_runs=5):
    """运行测试"""
    db_path = f'test_{mode.lower()}.db'
    
    # 清理旧数据库
    if os.path.exists(db_path):
        os.remove(db_path)
    
    write_times = []
    read_times = []
    
    for run in range(num_runs):
        with sqlite3.connect(db_path) as conn:
            # 设置日志模式
            conn.execute(f'PRAGMA journal_mode={mode}')
            conn.execute('PRAGMA synchronous=NORMAL')
            
            # 创建表
            create_test_table(conn)
            
            # 测试写入性能
            write_time = test_write_performance(conn, 10000)
            write_times.append(write_time)
            
            # 测试读取性能
            read_time = test_read_performance(conn, 1000)
            read_times.append(read_time)
        
        # 清理数据库
        if os.path.exists(db_path):
            os.remove(db_path)
    
    return {
        'write_mean': statistics.mean(write_times),
        'write_std': statistics.stdev(write_times) if len(write_times) > 1 else 0,
        'read_mean': statistics.mean(read_times),
        'read_std': statistics.stdev(read_times) if len(read_times) > 1 else 0
    }

def main():
    """主函数"""
    print("=" * 60)
    print("SQLite 性能测试：WAL vs DELETE模式对比")
    print("=" * 60)
    print()
    
    print("正在运行测试（每个模式运行5次）...")
    print()
    
    # 测试DELETE模式
    print("测试DELETE模式...")
    delete_results = run_test('DELETE')
    
    # 测试WAL模式
    print("测试WAL模式...")
    wal_results = run_test('WAL')
    
    # 输出结果
    print()
    print("=" * 60)
    print("测试结果")
    print("=" * 60)
    print()
    
    print(f"{'指标':<20} {'DELETE模式':<20} {'WAL模式':<20} {'提升':<10}")
    print("-" * 70)
    
    # 写入性能
    write_improvement = (delete_results['write_mean'] - wal_results['write_mean']) / delete_results['write_mean'] * 100
    print(f"{'写入性能 (10000条)':<20} "
          f"{delete_results['write_mean']:.3f}s{'':<10} "
          f"{wal_results['write_mean']:.3f}s{'':<10} "
          f"{write_improvement:+.1f}%")
    
    # 读取性能
    read_improvement = (delete_results['read_mean'] - wal_results['read_mean']) / delete_results['read_mean'] * 100
    print(f"{'读取性能 (1000次)':<20} "
          f"{delete_results['read_mean']:.3f}s{'':<10} "
          f"{wal_results['read_mean']:.3f}s{'':<10} "
          f"{read_improvement:+.1f}%")
    
    print()
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == '__main__':
    main()
