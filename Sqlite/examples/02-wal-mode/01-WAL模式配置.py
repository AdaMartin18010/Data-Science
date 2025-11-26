#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite WAL模式示例：WAL模式配置

> **难度**：⭐⭐ 进阶级
> **适用版本**：SQLite 3.31+ 至 3.47.x
> **最后更新**：2025-01-15
"""

import sqlite3
import os

def example_01_enable_wal_mode():
    """示例1：启用WAL模式"""
    print("=" * 50)
    print("示例1：启用WAL模式")
    print("=" * 50)
    
    db_path = 'wal_example.db'
    
    with sqlite3.connect(db_path) as conn:
        # 检查当前日志模式
        current_mode = conn.execute('PRAGMA journal_mode').fetchone()[0]
        print(f"当前日志模式：{current_mode}")
        
        # 启用WAL模式
        result = conn.execute('PRAGMA journal_mode=WAL').fetchone()[0]
        print(f"✅ WAL模式已启用：{result}")
        
        # 验证WAL模式
        if result.upper() == 'WAL':
            print("✅ WAL模式验证成功")
        else:
            print("❌ WAL模式启用失败")
    
    print()


def example_02_wal_configuration():
    """示例2：WAL模式配置"""
    print("=" * 50)
    print("示例2：WAL模式配置")
    print("=" * 50)
    
    db_path = 'wal_example.db'
    
    with sqlite3.connect(db_path) as conn:
        # 确保WAL模式
        conn.execute('PRAGMA journal_mode=WAL')
        
        # 配置WAL自动Checkpoint
        conn.execute('PRAGMA wal_autocheckpoint=1000')
        checkpoint = conn.execute('PRAGMA wal_autocheckpoint').fetchone()[0]
        print(f"✅ WAL自动Checkpoint：{checkpoint}页")
        
        # 配置同步模式
        conn.execute('PRAGMA synchronous=NORMAL')
        sync = conn.execute('PRAGMA synchronous').fetchone()[0]
        print(f"✅ 同步模式：{sync}")
        
        # 查看WAL文件信息
        wal_size = conn.execute('PRAGMA wal_checkpoint').fetchone()[0]
        print(f"✅ WAL Checkpoint状态：{wal_size}")
    
    print()


def example_03_wal_performance():
    """示例3：WAL模式性能对比"""
    print("=" * 50)
    print("示例3：WAL模式性能对比")
    print("=" * 50)
    
    import time
    
    db_path = 'wal_example.db'
    
    # 创建测试表
    with sqlite3.connect(db_path) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS test_data (
                id INTEGER PRIMARY KEY,
                value TEXT
            )
        ''')
        conn.commit()
    
    # 测试DELETE模式（需要重新创建数据库）
    delete_db = 'delete_example.db'
    if os.path.exists(delete_db):
        os.remove(delete_db)
    
    with sqlite3.connect(delete_db) as conn:
        conn.execute('PRAGMA journal_mode=DELETE')
        conn.execute('''
            CREATE TABLE test_data (
                id INTEGER PRIMARY KEY,
                value TEXT
            )
        ''')
        
        start = time.time()
        for i in range(1000):
            conn.execute('INSERT INTO test_data (value) VALUES (?)', (f'value_{i}',))
        conn.commit()
        delete_time = time.time() - start
        print(f"DELETE模式插入1000条：{delete_time:.3f}秒")
    
    # 测试WAL模式
    with sqlite3.connect(db_path) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('DELETE FROM test_data')
        conn.commit()
        
        start = time.time()
        for i in range(1000):
            conn.execute('INSERT INTO test_data (value) VALUES (?)', (f'value_{i}',))
        conn.commit()
        wal_time = time.time() - start
        print(f"WAL模式插入1000条：{wal_time:.3f}秒")
        
        if wal_time < delete_time:
            improvement = (delete_time - wal_time) / delete_time * 100
            print(f"✅ WAL模式性能提升：{improvement:.1f}%")
    
    # 清理
    if os.path.exists(delete_db):
        os.remove(delete_db)
    
    print()


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("SQLite WAL模式示例：WAL模式配置")
    print("=" * 50 + "\n")
    
    # 清理旧数据库
    if os.path.exists('wal_example.db'):
        os.remove('wal_example.db')
    
    # 运行示例
    example_01_enable_wal_mode()
    example_02_wal_configuration()
    example_03_wal_performance()
    
    # 清理
    if os.path.exists('wal_example.db'):
        os.remove('wal_example.db')
        print("✅ 示例数据库已清理\n")
    
    print("=" * 50)
    print("所有示例执行完成！")
    print("=" * 50)
