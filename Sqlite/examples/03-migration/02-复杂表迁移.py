#!/usr/bin/env python3
"""
复杂表迁移示例

演示如何迁移包含外键、约束的复杂表结构

功能：
- 多表迁移
- 外键处理
- 约束迁移
- 依赖关系处理
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime


def create_sqlite_example():
    """创建包含外键的SQLite示例数据库"""
    print("📝 创建SQLite示例数据库（复杂表结构）...")
    
    conn = sqlite3.connect('example_complex.db')
    cursor = conn.cursor()
    
    # 启用外键（SQLite需要显式启用）
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # 创建用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)
    
    # 创建订单表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total REAL NOT NULL CHECK (total > 0),
            status TEXT NOT NULL DEFAULT 'pending',
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # 创建订单项表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            price REAL NOT NULL CHECK (price > 0),
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    """)
    
    # 插入示例数据
    cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", ('Alice', 'alice@example.com'))
    user_id = cursor.lastrowid
    
    cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", ('Bob', 'bob@example.com'))
    
    cursor.execute("INSERT INTO orders (user_id, total, status) VALUES (?, ?, ?)", (user_id, 99.99, 'paid'))
    order_id = cursor.lastrowid
    
    cursor.executemany(
        "INSERT INTO order_items (order_id, product_name, quantity, price) VALUES (?, ?, ?, ?)",
        [
            (order_id, 'Product A', 2, 29.99),
            (order_id, 'Product B', 1, 40.01),
        ]
    )
    
    conn.commit()
    
    # 显示数据
    print("\nSQLite数据:")
    cursor.execute("SELECT * FROM users")
    print("Users:")
    for row in cursor.fetchall():
        print(f"  {row}")
    
    cursor.execute("SELECT * FROM orders")
    print("\nOrders:")
    for row in cursor.fetchall():
        print(f"  {row}")
    
    cursor.execute("SELECT * FROM order_items")
    print("\nOrder Items:")
    for row in cursor.fetchall():
        print(f"  {row}")
    
    conn.close()
    print("\n✅ SQLite示例数据库创建完成\n")
    return 'example_complex.db'


def migrate_to_postgresql(sqlite_db: str, pg_conn_string: str):
    """迁移到PostgreSQL（处理外键和约束）"""
    print("🚀 开始迁移到PostgreSQL...")
    
    # 连接SQLite
    sqlite_conn = sqlite3.connect(sqlite_db)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # 连接PostgreSQL
    pg_conn = psycopg2.connect(pg_conn_string)
    pg_cursor = pg_conn.cursor()
    
    try:
        # 1. 创建PostgreSQL表（按依赖顺序）
        print("  📋 创建PostgreSQL表...")
        
        # 用户表（无依赖）
        pg_cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 订单表（依赖用户表）
        pg_cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                total NUMERIC(10,2) NOT NULL CHECK (total > 0),
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 订单项表（依赖订单表）
        pg_cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER NOT NULL,
                product_name VARCHAR(255) NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                price NUMERIC(10,2) NOT NULL CHECK (price > 0)
            )
        """)
        
        pg_conn.commit()
        print("  ✅ 表创建完成")
        
        # 2. 迁移数据（按依赖顺序）
        print("  📊 迁移数据...")
        
        # 迁移用户
        sqlite_cursor.execute("SELECT * FROM users")
        users_data = []
        for row in sqlite_cursor.fetchall():
            created_at = datetime.fromtimestamp(row['created_at']) if row['created_at'] else None
            users_data.append((row['name'], row['email'], created_at))
        
        execute_batch(
            pg_cursor,
            "INSERT INTO users (name, email, created_at) VALUES (%s, %s, %s)",
            users_data
        )
        
        # 获取用户ID映射（SQLite和PostgreSQL的ID可能不同）
        sqlite_cursor.execute("SELECT id, email FROM users")
        sqlite_users = {row['email']: row['id'] for row in sqlite_cursor.fetchall()}
        
        pg_cursor.execute("SELECT id, email FROM users")
        pg_users = {row[1]: row[0] for row in pg_cursor.fetchall()}
        
        # 迁移订单
        sqlite_cursor.execute("SELECT * FROM orders")
        orders_data = []
        order_id_map = {}  # SQLite order_id -> PostgreSQL order_id
        for row in sqlite_cursor.fetchall():
            # 映射user_id
            sqlite_user_id = row['user_id']
            sqlite_user_email = None
            for email, uid in sqlite_users.items():
                if uid == sqlite_user_id:
                    sqlite_user_email = email
                    break
            
            pg_user_id = pg_users.get(sqlite_user_email)
            created_at = datetime.fromtimestamp(row['created_at']) if row['created_at'] else None
            
            pg_cursor.execute(
                "INSERT INTO orders (user_id, total, status, created_at) VALUES (%s, %s, %s, %s) RETURNING id",
                (pg_user_id, row['total'], row['status'], created_at)
            )
            pg_order_id = pg_cursor.fetchone()[0]
            order_id_map[row['id']] = pg_order_id
        
        # 迁移订单项
        sqlite_cursor.execute("SELECT * FROM order_items")
        items_data = []
        for row in sqlite_cursor.fetchall():
            pg_order_id = order_id_map[row['order_id']]
            items_data.append((
                pg_order_id,
                row['product_name'],
                row['quantity'],
                row['price']
            ))
        
        execute_batch(
            pg_cursor,
            "INSERT INTO order_items (order_id, product_name, quantity, price) VALUES (%s, %s, %s, %s)",
            items_data
        )
        
        pg_conn.commit()
        print(f"  ✅ 迁移完成: {len(users_data)} 用户, {len(orders_data)} 订单, {len(items_data)} 订单项")
        
        # 3. 添加外键约束
        print("  🔗 添加外键约束...")
        pg_cursor.execute("""
            ALTER TABLE orders
            ADD CONSTRAINT IF NOT EXISTS fk_orders_user
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        """)
        
        pg_cursor.execute("""
            ALTER TABLE order_items
            ADD CONSTRAINT IF NOT EXISTS fk_order_items_order
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
        """)
        
        pg_conn.commit()
        print("  ✅ 外键约束添加完成")
        
        # 4. 验证数据
        print("  🔍 验证数据...")
        for table in ['users', 'orders', 'order_items']:
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = sqlite_cursor.fetchone()[0]
            
            pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            pg_count = pg_cursor.fetchone()[0]
            
            if sqlite_count == pg_count:
                print(f"    ✅ {table}: {pg_count} 行")
            else:
                print(f"    ❌ {table}: SQLite={sqlite_count}, PostgreSQL={pg_count}")
        
        # 显示PostgreSQL数据
        print("\nPostgreSQL数据:")
        pg_cursor.execute("SELECT * FROM users")
        print("Users:")
        for row in pg_cursor.fetchall():
            print(f"  {row}")
        
        pg_cursor.execute("SELECT * FROM orders")
        print("\nOrders:")
        for row in pg_cursor.fetchall():
            print(f"  {row}")
        
        pg_cursor.execute("SELECT * FROM order_items")
        print("\nOrder Items:")
        for row in pg_cursor.fetchall():
            print(f"  {row}")
        
    finally:
        sqlite_conn.close()
        pg_conn.close()
    
    print("\n✅ 迁移完成")


def main():
    """主函数"""
    import os
    
    pg_conn_string = os.getenv(
        'POSTGRESQL_CONNECTION',
        'postgresql://postgres:postgres@localhost:5432/testdb'
    )
    
    print("="*60)
    print("SQLite 到 PostgreSQL 复杂表迁移示例")
    print("="*60)
    print()
    
    sqlite_db = create_sqlite_example()
    
    try:
        migrate_to_postgresql(sqlite_db, pg_conn_string)
    except psycopg2.OperationalError as e:
        print(f"\n❌ PostgreSQL连接错误: {e}")
        print("请确保PostgreSQL服务正在运行且连接字符串正确")
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
