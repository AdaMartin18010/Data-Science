#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
列式物化视图示例

为分析查询创建列存储结构，模拟列存储的优势：
- 只扫描需要的列，I/O减少
- 适合聚合查询、统计查询
- 定期刷新，保持数据一致性
"""

import sqlite3
import time
import os

class ColumnarMaterializedView:
    """列式物化视图：为分析查询创建列存储结构"""
    
    def __init__(self, conn, source_table, columns):
        self.conn = conn
        self.source_table = source_table
        self.columns = columns
        self.column_tables = {}
        
    def create_column_tables(self):
        """为每列创建单独的表（模拟列存储）"""
        cursor = self.conn.cursor()
        
        for col in self.columns:
            col_table = f"{self.source_table}_{col}_column"
            self.column_tables[col] = col_table
            
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {col_table} (
                    row_id INTEGER PRIMARY KEY,
                    value TEXT,
                    INDEX idx_value (value)
                )
            """)
        
        self.conn.commit()
        print(f"✅ 创建了 {len(self.columns)} 个列表")
        
    def populate_columns(self):
        """从原始表填充列表（定期刷新）"""
        cursor = self.conn.cursor()
        
        # 清空现有数据
        for col_table in self.column_tables.values():
            cursor.execute(f"DELETE FROM {col_table}")
        
        # 获取所有行
        columns_str = ', '.join(self.columns)
        cursor.execute(f"SELECT rowid, {columns_str} FROM {self.source_table}")
        rows = cursor.fetchall()
        
        # 按列存储
        for col_idx, col in enumerate(self.columns):
            col_table = self.column_tables[col]
            col_values = [(row[0], str(row[col_idx + 1])) for row in rows]
            
            cursor.executemany(
                f"INSERT INTO {col_table} (row_id, value) VALUES (?, ?)",
                col_values
            )
        
        self.conn.commit()
        print(f"✅ 列式物化视图已更新，共 {len(rows)} 行")
        
    def query_aggregate(self, column, aggregate_func='COUNT', condition=None):
        """使用列存储进行聚合查询"""
        col_table = self.column_tables[column]
        cursor = self.conn.cursor()
        
        if aggregate_func == 'COUNT':
            if condition:
                query = f"SELECT COUNT(*) FROM {col_table} WHERE {condition}"
            else:
                query = f"SELECT COUNT(*) FROM {col_table}"
        elif aggregate_func == 'COUNT_DISTINCT':
            query = f"SELECT COUNT(DISTINCT value) FROM {col_table}"
            if condition:
                query = f"SELECT COUNT(DISTINCT value) FROM {col_table} WHERE {condition}"
        else:
            raise ValueError(f"Unsupported aggregate function: {aggregate_func}")
        
        result = cursor.execute(query).fetchone()
        return result[0] if result else 0
    
    def query_group_by(self, column):
        """使用列存储进行分组查询"""
        col_table = self.column_tables[column]
        cursor = self.conn.cursor()
        
        query = f"""
            SELECT value, COUNT(*) as count
            FROM {col_table}
            GROUP BY value
            ORDER BY count DESC
        """
        
        return cursor.execute(query).fetchall()

def create_sample_data(conn):
    """创建示例数据"""
    cursor = conn.cursor()
    
    # 创建日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            action TEXT,
            timestamp INTEGER,
            duration INTEGER
        )
    """)
    
    # 插入测试数据
    import random
    actions = ['login', 'logout', 'view', 'edit', 'delete', 'search', 'download']
    
    data = []
    base_time = int(time.time())
    for i in range(100000):
        data.append((
            random.randint(1, 1000),  # user_id
            random.choice(actions),   # action
            base_time - random.randint(0, 86400 * 7),  # timestamp
            random.randint(10, 5000)  # duration
        ))
    
    cursor.executemany("""
        INSERT INTO logs (user_id, action, timestamp, duration)
        VALUES (?, ?, ?, ?)
    """, data)
    
    conn.commit()
    print(f"✅ 创建了 {len(data)} 条日志数据")

def compare_query_performance(conn, view):
    """对比查询性能"""
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("查询性能对比（列存储 vs 行存储）")
    print("="*60)
    
    # 查询1：COUNT聚合
    print("\n查询1：COUNT聚合 - SELECT COUNT(*) FROM logs WHERE action = 'login'")
    
    start = time.time()
    cursor.execute("SELECT COUNT(*) FROM logs WHERE action = 'login'")
    result1 = cursor.fetchone()[0]
    time1 = time.time() - start
    print(f"  行存储查询: {time1*1000:.2f}ms, 结果: {result1}")
    
    start = time.time()
    result2 = view.query_aggregate('action', 'COUNT', "value = 'login'")
    time2 = time.time() - start
    print(f"  列存储查询: {time2*1000:.2f}ms, 结果: {result2}")
    print(f"  性能提升: {time1/time2:.2f}x")
    
    # 查询2：COUNT DISTINCT
    print("\n查询2：COUNT DISTINCT - SELECT COUNT(DISTINCT user_id) FROM logs")
    
    start = time.time()
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM logs")
    result3 = cursor.fetchone()[0]
    time3 = time.time() - start
    print(f"  行存储查询: {time3*1000:.2f}ms, 结果: {result3}")
    
    start = time.time()
    result4 = view.query_aggregate('user_id', 'COUNT_DISTINCT')
    time4 = time.time() - start
    print(f"  列存储查询: {time4*1000:.2f}ms, 结果: {result4}")
    print(f"  性能提升: {time3/time4:.2f}x")
    
    # 查询3：GROUP BY聚合
    print("\n查询3：GROUP BY聚合 - SELECT action, COUNT(*) FROM logs GROUP BY action")
    
    start = time.time()
    cursor.execute("SELECT action, COUNT(*) FROM logs GROUP BY action ORDER BY COUNT(*) DESC")
    results5 = cursor.fetchall()
    time5 = time.time() - start
    print(f"  行存储查询: {time5*1000:.2f}ms, 返回 {len(results5)} 组")
    
    start = time.time()
    results6 = view.query_group_by('action')
    time6 = time.time() - start
    print(f"  列存储查询: {time6*1000:.2f}ms, 返回 {len(results6)} 组")
    print(f"  性能提升: {time5/time6:.2f}x")
    
    # 显示分组结果
    print("\n  分组结果（前5组）:")
    for value, count in results6[:5]:
        print(f"    {value}: {count}")

def main():
    """主函数"""
    db_path = 'columnar_view_example.db'
    
    # 删除旧数据库
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    
    print("="*60)
    print("列式物化视图示例")
    print("="*60)
    
    # 创建示例数据
    print("\n1. 创建示例数据...")
    create_sample_data(conn)
    
    # 创建列式物化视图
    print("\n2. 创建列式物化视图...")
    view = ColumnarMaterializedView(conn, 'logs', ['user_id', 'action', 'timestamp', 'duration'])
    view.create_column_tables()
    view.populate_columns()
    
    # 对比查询性能
    print("\n3. 对比查询性能...")
    compare_query_performance(conn, view)
    
    print("\n" + "="*60)
    print("示例完成！")
    print("="*60)
    print(f"\n数据库文件: {db_path}")
    print("\n💡 总结：")
    print("  - 列存储适合聚合查询、统计查询")
    print("  - 只扫描需要的列，I/O减少，性能提升")
    print("  - 需要定期刷新物化视图，保持数据一致性")
    print("  - 适合读多写少的分析场景")
    
    conn.close()

if __name__ == '__main__':
    main()
