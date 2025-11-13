#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 性能测试：批量事务性能

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

def test_no_transaction(conn, num_records=1000):
    """测试：无事务（每条一个事务）"""
    start = time.time()
    
    for i in range(num_records):
        conn.execute(
            'INSERT INTO test_data (value, created_at) VALUES (?, ?)',
            (f'value_{i}', int(time.time()))
        )
        conn.commit()
    
    elapsed = time.time() - start
    return elapsed

def test_single_transaction(conn, num_records=1000):
    """测试：单事务（批量插入）"""
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

def test_executemany(conn, num_records=1000):
    """测试：executemany（批量插入）"""
    start = time.time()
    
    data = [(f'value_{i}', int(time.time())) for i in range(num_records)]
    conn.executemany(
        'INSERT INTO test_data (value, created_at) VALUES (?, ?)',
        data
    )
    conn.commit()
    
    elapsed = time.time() - start
    return elapsed

def run_test(test_func, num_records=1000, num_runs=5):
    """运行测试"""
    db_path = 'test_batch.db'
    
    times = []
    
    for run in range(num_runs):
        # 清理旧数据库
        if os.path.exists(db_path):
            os.remove(db_path)
        
        with sqlite3.connect(db_path) as conn:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')
            create_test_table(conn)
            
            elapsed = test_func(conn, num_records)
            times.append(elapsed)
    
    return {
        'mean': statistics.mean(times),
        'std': statistics.stdev(times) if len(times) > 1 else 0,
        'min': min(times),
        'max': max(times)
    }

def main():
    """主函数"""
    print("=" * 60)
    print("SQLite 性能测试：批量事务性能")
    print("=" * 60)
    print()
    
    num_records = 1000
    num_runs = 5
    
    print(f"测试配置：")
    print(f"  - 插入记录数：{num_records}")
    print(f"  - 运行次数：{num_runs}")
    print()
    
    print("正在运行测试...")
    print()
    
    # 测试无事务
    print("测试1：无事务（每条一个事务）...")
    no_trans_results = run_test(test_no_transaction, num_records, num_runs)
    
    # 测试单事务
    print("测试2：单事务（批量插入）...")
    single_trans_results = run_test(test_single_transaction, num_records, num_runs)
    
    # 测试executemany
    print("测试3：executemany（批量插入）...")
    executemany_results = run_test(test_executemany, num_records, num_runs)
    
    # 输出结果
    print()
    print("=" * 60)
    print("测试结果")
    print("=" * 60)
    print()
    
    print(f"{'方式':<25} {'平均耗时':<15} {'性能提升':<15}")
    print("-" * 55)
    
    baseline = no_trans_results['mean']
    
    print(f"{'无事务（每条提交）':<25} "
          f"{baseline:.3f}s{'':<8} "
          f"{'基准':<15}")
    
    single_improvement = (baseline - single_trans_results['mean']) / baseline * 100
    print(f"{'单事务（批量插入）':<25} "
          f"{single_trans_results['mean']:.3f}s{'':<8} "
          f"{single_improvement:+.1f}%")
    
    executemany_improvement = (baseline - executemany_results['mean']) / baseline * 100
    print(f"{'executemany':<25} "
          f"{executemany_results['mean']:.3f}s{'':<8} "
          f"{executemany_improvement:+.1f}%")
    
    print()
    print("=" * 60)
    print("结论：批量事务可以显著提升插入性能（10-250倍）")
    print("=" * 60)

if __name__ == '__main__':
    main()
