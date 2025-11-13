#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite WAL模式示例：Checkpoint操作

> **难度**：⭐⭐ 进阶级
> **适用版本**：SQLite 3.31+
"""

import sqlite3
import os
import time

def setup_test_data(conn):
    """设置测试数据"""
    conn.execute('''
        CREATE TABLE IF NOT EXISTS test_data (
            id INTEGER PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.execute('DELETE FROM test_data')
    conn.commit()

def example_01_automatic_checkpoint():
    """示例1：自动Checkpoint"""
    print("=" * 50)
    print("示例1：自动Checkpoint")
    print("=" * 50)
    
    db_path = 'wal_checkpoint.db'
    
    if os.path.exists(db_path):
        os.remove(db_path)
    
    with sqlite3.connect(db_path) as conn:
        # 启用WAL模式
        conn.execute('PRAGMA journal_mode=WAL')
        
        # 设置自动Checkpoint
        conn.execute('PRAGMA wal_autocheckpoint=1000')
        checkpoint = conn.execute('PRAGMA wal_autocheckpoint').fetchone()[0]
        print(f"✅ 自动Checkpoint设置：{checkpoint}页")
        
        # 当WAL文件达到1000页时自动Checkpoint
        print("   当WAL文件达到1000页时自动执行Checkpoint")
    
    print()


def example_02_manual_checkpoint():
    """示例2：手动Checkpoint"""
    print("=" * 50)
    print("示例2：手动Checkpoint")
    print("=" * 50)
    
    db_path = 'wal_checkpoint.db'
    
    if os.path.exists(db_path):
        os.remove(db_path)
    
    with sqlite3.connect(db_path) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        setup_test_data(conn)
        
        # 插入一些数据
        for i in range(100):
            conn.execute(
                'INSERT INTO test_data (value) VALUES (?)',
                (f'value_{i}',)
            )
        conn.commit()
        
        # 手动Checkpoint（非阻塞）
        result = conn.execute('PRAGMA wal_checkpoint').fetchone()
        print(f"✅ Checkpoint结果：{result}")
        print(f"   0 = SQLITE_OK, 1 = SQLITE_BUSY, 2 = SQLITE_LOCKED")
        
        # 完全Checkpoint（阻塞直到完成）
        result = conn.execute('PRAGMA wal_checkpoint(FULL)').fetchone()
        print(f"✅ 完全Checkpoint结果：{result}")
        
        # 截断Checkpoint（尽可能截断WAL文件）
        result = conn.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()
        print(f"✅ 截断Checkpoint结果：{result}")
    
    print()


def example_03_checkpoint_timing():
    """示例3：Checkpoint时机"""
    print("=" * 50)
    print("示例3：Checkpoint时机")
    print("=" * 50)
    
    db_path = 'wal_checkpoint.db'
    
    if os.path.exists(db_path):
        os.remove(db_path)
    
    with sqlite3.connect(db_path) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        setup_test_data(conn)
        
        # 插入大量数据
        print("插入1000条数据...")
        start = time.time()
        for i in range(1000):
            conn.execute(
                'INSERT INTO test_data (value) VALUES (?)',
                (f'value_{i}',)
            )
        conn.commit()
        insert_time = time.time() - start
        print(f"✅ 插入耗时：{insert_time:.3f}秒")
        
        # 执行Checkpoint
        print("\n执行Checkpoint...")
        start = time.time()
        conn.execute('PRAGMA wal_checkpoint(FULL)')
        checkpoint_time = time.time() - start
        print(f"✅ Checkpoint耗时：{checkpoint_time:.3f}秒")
        
        # 检查WAL文件大小
        wal_path = db_path + '-wal'
        if os.path.exists(wal_path):
            wal_size = os.path.getsize(wal_path)
            print(f"✅ WAL文件大小：{wal_size} bytes")
        else:
            print("✅ WAL文件已清理（Checkpoint后）")
    
    # 清理
    if os.path.exists(db_path):
        os.remove(db_path)
    if os.path.exists(db_path + '-wal'):
        os.remove(db_path + '-wal')
    if os.path.exists(db_path + '-shm'):
        os.remove(db_path + '-shm')
    
    print()


def example_04_checkpoint_best_practices():
    """示例4：Checkpoint最佳实践"""
    print("=" * 50)
    print("示例4：Checkpoint最佳实践")
    print("=" * 50)
    
    db_path = 'wal_checkpoint.db'
    
    if os.path.exists(db_path):
        os.remove(db_path)
    
    with sqlite3.connect(db_path) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA wal_autocheckpoint=1000')
        setup_test_data(conn)
        
        print("✅ 推荐配置：")
        print("   1. 设置自动Checkpoint：PRAGMA wal_autocheckpoint=1000")
        print("   2. 应用关闭时执行完全Checkpoint：PRAGMA wal_checkpoint(FULL)")
        print("   3. 定期检查WAL文件大小，必要时手动Checkpoint")
        print("   4. 使用TRUNCATE模式减少WAL文件大小")
    
    # 清理
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print()


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("SQLite WAL模式示例：Checkpoint操作")
    print("=" * 50 + "\n")
    
    # 运行示例
    example_01_automatic_checkpoint()
    example_02_manual_checkpoint()
    example_03_checkpoint_timing()
    example_04_checkpoint_best_practices()
    
    print("=" * 50)
    print("所有示例执行完成！")
    print("=" * 50)
