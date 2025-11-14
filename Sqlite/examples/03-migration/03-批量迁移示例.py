#!/usr/bin/env python3
"""
批量迁移示例

演示如何高效迁移大批量数据

功能：
- 批量数据迁移
- 进度监控
- 性能优化
- 错误处理
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
import time
from datetime import datetime


def create_large_sqlite_example():
    """创建包含大量数据的SQLite示例数据库"""
    print("📝 创建SQLite示例数据库（大量数据）...")
    
    conn = sqlite3.connect('example_large.db')
    cursor = conn.cursor()
    
    # 创建表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL,
            category TEXT,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)
    
    # 批量插入数据
    print("  插入示例数据...")
    batch_size = 1000
    total_rows = 10000
    
    categories = ['Electronics', 'Clothing', 'Food', 'Books', 'Toys']
    
    for i in range(0, total_rows, batch_size):
        batch = []
        for j in range(batch_size):
            if i + j >= total_rows:
                break
            batch.append((
                f'Product {i+j+1}',
                10.0 + (i+j) % 1000,
                100 - (i+j) % 50,
                categories[(i+j) % len(categories)],
                int(time.time()) - (i+j)
            ))
        
        cursor.executemany(
            "INSERT INTO products (name, price, stock, category, created_at) VALUES (?, ?, ?, ?, ?)",
            batch
        )
        
        if (i // batch_size + 1) % 10 == 0:
            print(f"    已插入 {min(i+batch_size, total_rows)}/{total_rows} 行")
    
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    print(f"  ✅ 创建完成: {count} 行数据\n")
    
    conn.close()
    return 'example_large.db'


def migrate_with_progress(sqlite_db: str, pg_conn_string: str, batch_size: int = 1000):
    """批量迁移并显示进度"""
    print("🚀 开始批量迁移...")
    
    sqlite_conn = sqlite3.connect(sqlite_db)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    pg_conn = psycopg2.connect(pg_conn_string)
    pg_cursor = pg_conn.cursor()
    
    try:
        # 创建PostgreSQL表
        print("  📋 创建PostgreSQL表...")
        pg_cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                price NUMERIC(10,2) NOT NULL,
                stock INTEGER NOT NULL,
                category VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        pg_conn.commit()
        print("  ✅ 表创建完成")
        
        # 获取总行数
        sqlite_cursor.execute("SELECT COUNT(*) FROM products")
        total_rows = sqlite_cursor.fetchone()[0]
        
        print(f"\n  📊 开始迁移 {total_rows} 行数据 (批量大小: {batch_size})")
        print("  " + "-"*50)
        
        start_time = time.time()
        rows_migrated = 0
        offset = 0
        
        while offset < total_rows:
            # 读取一批数据
            sqlite_cursor.execute(
                "SELECT * FROM products LIMIT ? OFFSET ?",
                (batch_size, offset)
            )
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                break
            
            # 转换数据
            data = []
            for row in rows:
                created_at = datetime.fromtimestamp(row['created_at']) if row['created_at'] else None
                data.append((
                    row['name'],
                    row['price'],
                    row['stock'],
                    row['category'],
                    created_at
                ))
            
            # 批量插入
            try:
                execute_batch(
                    pg_cursor,
                    "INSERT INTO products (name, price, stock, category, created_at) VALUES (%s, %s, %s, %s, %s)",
                    data,
                    page_size=batch_size
                )
                pg_conn.commit()
                
                rows_migrated += len(data)
                offset += batch_size
                
                # 显示进度
                progress = (rows_migrated / total_rows) * 100
                elapsed = time.time() - start_time
                speed = rows_migrated / elapsed if elapsed > 0 else 0
                eta = (total_rows - rows_migrated) / speed if speed > 0 else 0
                
                print(f"\r  [{progress:6.2f}%] {rows_migrated:6}/{total_rows} 行 | "
                      f"速度: {speed:6.0f} 行/秒 | ETA: {eta:4.0f} 秒", end='', flush=True)
            
            except Exception as e:
                pg_conn.rollback()
                print(f"\n  ❌ 批量插入失败: {e}")
                raise
        
        elapsed_time = time.time() - start_time
        print(f"\n\n  ✅ 迁移完成!")
        print(f"     总行数: {rows_migrated}")
        print(f"     耗时: {elapsed_time:.2f} 秒")
        print(f"     平均速度: {rows_migrated/elapsed_time:.0f} 行/秒")
        
        # 验证数据
        print("\n  🔍 验证数据...")
        sqlite_cursor.execute("SELECT COUNT(*) FROM products")
        sqlite_count = sqlite_cursor.fetchone()[0]
        
        pg_cursor.execute("SELECT COUNT(*) FROM products")
        pg_count = pg_cursor.fetchone()[0]
        
        if sqlite_count == pg_count:
            print(f"  ✅ 数据验证通过: {pg_count} 行")
        else:
            print(f"  ❌ 数据验证失败: SQLite={sqlite_count}, PostgreSQL={pg_count}")
        
    finally:
        sqlite_conn.close()
        pg_conn.close()
    
    print("\n✅ 批量迁移完成")


def main():
    """主函数"""
    import os
    
    pg_conn_string = os.getenv(
        'POSTGRESQL_CONNECTION',
        'postgresql://postgres:postgres@localhost:5432/testdb'
    )
    
    print("="*60)
    print("SQLite 到 PostgreSQL 批量迁移示例")
    print("="*60)
    print()
    
    sqlite_db = create_large_sqlite_example()
    
    try:
        migrate_with_progress(sqlite_db, pg_conn_string, batch_size=1000)
    except psycopg2.OperationalError as e:
        print(f"\n❌ PostgreSQL连接错误: {e}")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    cleanup = input("\n是否删除SQLite示例数据库? (y/N): ")
    if cleanup.lower() == 'y':
        import os
        if os.path.exists(sqlite_db):
            os.remove(sqlite_db)
            print(f"✅ 已删除 {sqlite_db}")


if __name__ == '__main__':
    main()
