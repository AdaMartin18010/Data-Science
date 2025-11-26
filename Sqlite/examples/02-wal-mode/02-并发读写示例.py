#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite WAL模式示例：并发读写

> **难度**：⭐⭐ 进阶级
> **适用版本**：SQLite 3.31+ 至 3.47.x
> **最后更新**：2025-01-15
"""

import sqlite3
import threading
import time
import os

def setup_test_data(conn):
    """设置测试数据"""
    conn.execute('''
        CREATE TABLE IF NOT EXISTS test_data (
            id INTEGER PRIMARY KEY,
            value INTEGER,
            updated_at INTEGER
        )
    ''')
    conn.execute('DELETE FROM test_data')
    conn.executemany(
        'INSERT INTO test_data (value, updated_at) VALUES (?, ?)',
        [(i, int(time.time())) for i in range(100)]
    )
    conn.commit()

def reader_thread(db_path, thread_id, num_reads=100):
    """读线程"""
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA journal_mode=WAL')
    
    read_count = 0
    for i in range(num_reads):
        try:
            result = conn.execute(
                'SELECT COUNT(*) FROM test_data WHERE value > ?',
                (i % 100,)
            ).fetchone()[0]
            read_count += 1
        except sqlite3.OperationalError as e:
            print(f"读线程{thread_id}错误: {e}")
    
    conn.close()
    return read_count

def writer_thread(db_path, thread_id, num_writes=50):
    """写线程"""
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    
    write_count = 0
    for i in range(num_writes):
        try:
            conn.execute('BEGIN IMMEDIATE')
            conn.execute(
                'UPDATE test_data SET value = ?, updated_at = ? WHERE id = ?',
                (i, int(time.time()), (i % 100) + 1)
            )
            conn.commit()
            write_count += 1
        except sqlite3.OperationalError as e:
            print(f"写线程{thread_id}错误: {e}")
            conn.rollback()
    
    conn.close()
    return write_count

def example_01_concurrent_reads():
    """示例1：并发读操作"""
    print("=" * 50)
    print("示例1：并发读操作（WAL模式）")
    print("=" * 50)
    
    db_path = 'wal_concurrent.db'
    
    # 清理旧数据库
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # 设置测试数据
    with sqlite3.connect(db_path) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        setup_test_data(conn)
    
    # 创建多个读线程
    threads = []
    num_threads = 5
    num_reads = 100
    
    start_time = time.time()
    
    for i in range(num_threads):
        thread = threading.Thread(
            target=reader_thread,
            args=(db_path, i, num_reads)
        )
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    elapsed = time.time() - start_time
    
    print(f"✅ {num_threads}个读线程，每个{num_reads}次读取")
    print(f"   总耗时：{elapsed:.3f}秒")
    print(f"   平均每次读取：{elapsed / (num_threads * num_reads) * 1000:.2f}ms")
    
    # 清理
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print()


def example_02_concurrent_read_write():
    """示例2：并发读写操作"""
    print("=" * 50)
    print("示例2：并发读写操作（WAL模式）")
    print("=" * 50)
    
    db_path = 'wal_concurrent.db'
    
    # 清理旧数据库
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # 设置测试数据
    with sqlite3.connect(db_path) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        setup_test_data(conn)
    
    # 创建读线程和写线程
    threads = []
    num_readers = 3
    num_writers = 1
    num_reads = 100
    num_writes = 50
    
    start_time = time.time()
    
    # 启动读线程
    for i in range(num_readers):
        thread = threading.Thread(
            target=reader_thread,
            args=(db_path, i, num_reads)
        )
        threads.append(thread)
        thread.start()
    
    # 启动写线程
    for i in range(num_writers):
        thread = threading.Thread(
            target=writer_thread,
            args=(db_path, i, num_writes)
        )
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    elapsed = time.time() - start_time
    
    print(f"✅ {num_readers}个读线程 + {num_writers}个写线程")
    print(f"   总耗时：{elapsed:.3f}秒")
    print(f"   WAL模式支持一写多读并发")
    
    # 清理
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print()


def example_03_wal_vs_delete_concurrency():
    """示例3：WAL vs DELETE模式并发性能对比"""
    print("=" * 50)
    print("示例3：WAL vs DELETE模式并发性能对比")
    print("=" * 50)
    
    import time
    
    # 测试DELETE模式
    delete_db = 'delete_concurrent.db'
    if os.path.exists(delete_db):
        os.remove(delete_db)
    
    with sqlite3.connect(delete_db) as conn:
        conn.execute('PRAGMA journal_mode=DELETE')
        setup_test_data(conn)
    
    threads = []
    num_readers = 3
    
    start = time.time()
    for i in range(num_readers):
        thread = threading.Thread(
            target=reader_thread,
            args=(delete_db, i, 50)
        )
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    delete_time = time.time() - start
    
    # 测试WAL模式
    wal_db = 'wal_concurrent.db'
    if os.path.exists(wal_db):
        os.remove(wal_db)
    
    with sqlite3.connect(wal_db) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        setup_test_data(conn)
    
    threads = []
    start = time.time()
    for i in range(num_readers):
        thread = threading.Thread(
            target=reader_thread,
            args=(wal_db, i, 50)
        )
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    wal_time = time.time() - start
    
    print(f"DELETE模式并发读：{delete_time:.3f}秒")
    print(f"WAL模式并发读：{wal_time:.3f}秒")
    
    if wal_time < delete_time:
        improvement = (delete_time - wal_time) / delete_time * 100
        print(f"✅ WAL模式性能提升：{improvement:.1f}%")
    
    # 清理
    if os.path.exists(delete_db):
        os.remove(delete_db)
    if os.path.exists(wal_db):
        os.remove(wal_db)
    
    print()


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("SQLite WAL模式示例：并发读写")
    print("=" * 50 + "\n")
    
    # 运行示例
    example_01_concurrent_reads()
    example_02_concurrent_read_write()
    example_03_wal_vs_delete_concurrency()
    
    print("=" * 50)
    print("所有示例执行完成！")
    print("=" * 50)
