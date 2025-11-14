#!/usr/bin/env python3
"""
简单表迁移示例

演示如何将SQLite中的简单表迁移到PostgreSQL

功能：
- 创建示例SQLite表
- 迁移到PostgreSQL
- 数据验证
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_batch


def create_sqlite_example():
    """创建SQLite示例数据库和表"""
    print("📝 创建SQLite示例数据库...")
    
    conn = sqlite3.connect('example_migration.db')
    cursor = conn.cursor()
    
    # 创建表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            age INTEGER,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)
    
    # 插入示例数据
    users = [
        ('Alice', 'alice@example.com', 25),
        ('Bob', 'bob@example.com', 30),
        ('Charlie', 'charlie@example.com', 35),
    ]
    
    cursor.executemany(
        "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
        users
    )
    
    conn.commit()
    
    # 显示数据
    cursor.execute("SELECT * FROM users")
    print("\nSQLite数据:")
    for row in cursor.fetchall():
        print(f"  {row}")
    
    conn.close()
    print("✅ SQLite示例数据库创建完成\n")
    return 'example_migration.db'


def migrate_to_postgresql(sqlite_db: str, pg_conn_string: str):
    """迁移到PostgreSQL"""
    print("🚀 开始迁移到PostgreSQL...")
    
    # 连接SQLite
    sqlite_conn = sqlite3.connect(sqlite_db)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # 连接PostgreSQL
    pg_conn = psycopg2.connect(pg_conn_string)
    pg_cursor = pg_conn.cursor()
    
    try:
        # 1. 创建PostgreSQL表
        print("  📋 创建PostgreSQL表...")
        pg_cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                age INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        pg_conn.commit()
        print("  ✅ 表创建完成")
        
        # 2. 迁移数据
        print("  📊 迁移数据...")
        sqlite_cursor.execute("SELECT * FROM users")
        rows = sqlite_cursor.fetchall()
        
        data = []
        for row in rows:
            # 转换时间戳
            created_at = None
            if row['created_at']:
                from datetime import datetime
                created_at = datetime.fromtimestamp(row['created_at'])
            
            data.append((
                row['name'],
                row['email'],
                row['age'],
                created_at
            ))
        
        # 批量插入
        execute_batch(
            pg_cursor,
            "INSERT INTO users (name, email, age, created_at) VALUES (%s, %s, %s, %s)",
            data
        )
        pg_conn.commit()
        print(f"  ✅ 迁移 {len(data)} 行数据")
        
        # 3. 验证数据
        print("  🔍 验证数据...")
        sqlite_cursor.execute("SELECT COUNT(*) FROM users")
        sqlite_count = sqlite_cursor.fetchone()[0]
        
        pg_cursor.execute("SELECT COUNT(*) FROM users")
        pg_count = pg_cursor.fetchone()[0]
        
        if sqlite_count == pg_count:
            print(f"  ✅ 数据验证通过: {pg_count} 行")
        else:
            print(f"  ❌ 数据验证失败: SQLite={sqlite_count}, PostgreSQL={pg_count}")
        
        # 显示PostgreSQL数据
        pg_cursor.execute("SELECT * FROM users")
        print("\nPostgreSQL数据:")
        for row in pg_cursor.fetchall():
            print(f"  {row}")
        
    finally:
        sqlite_conn.close()
        pg_conn.close()
    
    print("\n✅ 迁移完成")


def main():
    """主函数"""
    import os
    
    # PostgreSQL连接字符串（需要根据实际情况修改）
    pg_conn_string = os.getenv(
        'POSTGRESQL_CONNECTION',
        'postgresql://postgres:postgres@localhost:5432/testdb'
    )
    
    print("="*60)
    print("SQLite 到 PostgreSQL 简单表迁移示例")
    print("="*60)
    print()
    
    # 创建SQLite示例
    sqlite_db = create_sqlite_example()
    
    # 迁移到PostgreSQL
    try:
        migrate_to_postgresql(sqlite_db, pg_conn_string)
    except psycopg2.OperationalError as e:
        print(f"\n❌ PostgreSQL连接错误: {e}")
        print("请确保:")
        print("  1. PostgreSQL服务正在运行")
        print("  2. 数据库已创建")
        print("  3. 连接字符串正确")
        print(f"\n当前连接字符串: {pg_conn_string}")
        print("可以通过环境变量 POSTGRESQL_CONNECTION 设置连接字符串")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 清理（可选）
    cleanup = input("\n是否删除SQLite示例数据库? (y/N): ")
    if cleanup.lower() == 'y':
        import os
        if os.path.exists(sqlite_db):
            os.remove(sqlite_db)
            print(f"✅ 已删除 {sqlite_db}")


if __name__ == '__main__':
    main()
