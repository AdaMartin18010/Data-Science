#!/usr/bin/env python3
"""
SQLite到PostgreSQL数据迁移工具

功能：
- 全量数据迁移
- 增量数据迁移（基于变更日志）
- 数据验证
- 进度报告

使用方法：
    python 04-数据迁移工具.py sqlite.db postgresql://user:pass@host/db [--table TABLE] [--batch-size SIZE]
"""

import sqlite3
import psycopg2
import sys
import argparse
import time
from typing import Dict, List, Optional
from psycopg2.extras import execute_batch


class DataMigrator:
    def __init__(self, sqlite_path: str, pg_conn_string: str):
        self.sqlite_path = sqlite_path
        self.sqlite_conn = sqlite3.connect(sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row
        self.pg_conn = psycopg2.connect(pg_conn_string)
        self.stats = {
            'tables_migrated': 0,
            'rows_migrated': 0,
            'errors': [],
            'start_time': None,
            'end_time': None
        }
    
    def migrate_table(self, table_name: str, batch_size: int = 1000):
        """迁移单个表"""
        print(f"📋 开始迁移表: {table_name}")
        
        sqlite_cursor = self.sqlite_conn.cursor()
        pg_cursor = self.pg_conn.cursor()
        
        try:
            # 获取列信息
            sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in sqlite_cursor.fetchall()]
            
            # 获取总行数
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_rows = sqlite_cursor.fetchone()[0]
            
            if total_rows == 0:
                print(f"  ⚠️  表 {table_name} 为空，跳过")
                return
            
            # 批量迁移
            offset = 0
            rows_migrated = 0
            
            while offset < total_rows:
                # 读取一批数据
                sqlite_cursor.execute(
                    f"SELECT * FROM {table_name} LIMIT ? OFFSET ?",
                    (batch_size, offset)
                )
                
                rows = sqlite_cursor.fetchall()
                if not rows:
                    break
                
                # 准备插入语句
                placeholders = ','.join(['%s'] * len(columns))
                insert_sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
                
                # 转换数据格式
                data_rows = []
                for row in rows:
                    data_row = []
                    for i, value in enumerate(row):
                        # 处理特殊类型
                        if isinstance(value, bytes):
                            data_row.append(psycopg2.Binary(value))
                        else:
                            data_row.append(value)
                    data_rows.append(tuple(data_row))
                
                # 批量插入
                try:
                    execute_batch(pg_cursor, insert_sql, data_rows, page_size=batch_size)
                    self.pg_conn.commit()
                    
                    rows_migrated += len(rows)
                    offset += batch_size
                    
                    # 显示进度
                    progress = (rows_migrated / total_rows) * 100
                    print(f"  📊 进度: {rows_migrated}/{total_rows} ({progress:.1f}%)", end='\r')
                
                except Exception as e:
                    self.pg_conn.rollback()
                    raise e
            
            print(f"\n  ✅ 完成: {table_name} ({rows_migrated} 行)")
            self.stats['tables_migrated'] += 1
            self.stats['rows_migrated'] += rows_migrated
        
        except Exception as e:
            error_msg = f"迁移表 {table_name} 时出错: {e}"
            print(f"\n  ❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            self.pg_conn.rollback()
            raise
    
    def migrate_all(self, table_names: Optional[List[str]] = None, batch_size: int = 1000):
        """迁移所有表"""
        self.stats['start_time'] = time.time()
        
        # 获取所有表
        sqlite_cursor = self.sqlite_conn.cursor()
        if table_names:
            tables = table_names
        else:
            sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in sqlite_cursor.fetchall()]
        
        print(f"🚀 开始迁移 {len(tables)} 个表...")
        print("="*60)
        
        for table_name in tables:
            try:
                self.migrate_table(table_name, batch_size)
            except Exception as e:
                print(f"  ❌ 跳过表 {table_name} 继续迁移其他表")
                continue
        
        self.stats['end_time'] = time.time()
        self._print_summary()
    
    def verify_migration(self, table_name: str) -> bool:
        """验证迁移结果"""
        print(f"🔍 验证表: {table_name}")
        
        sqlite_cursor = self.sqlite_conn.cursor()
        pg_cursor = self.pg_conn.cursor()
        
        # 检查行数
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        sqlite_count = sqlite_cursor.fetchone()[0]
        
        pg_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        pg_count = pg_cursor.fetchone()[0]
        
        if sqlite_count == pg_count:
            print(f"  ✅ 行数匹配: {sqlite_count}")
            return True
        else:
            print(f"  ❌ 行数不匹配: SQLite={sqlite_count}, PostgreSQL={pg_count}")
            return False
    
    def _print_summary(self):
        """打印迁移摘要"""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        print("\n" + "="*60)
        print("📊 迁移摘要")
        print("="*60)
        print(f"  表数量: {self.stats['tables_migrated']}")
        print(f"  行数量: {self.stats['rows_migrated']:,}")
        print(f"  耗时: {duration:.2f} 秒")
        print(f"  速度: {self.stats['rows_migrated'] / duration:.0f} 行/秒")
        
        if self.stats['errors']:
            print(f"\n  ⚠️  错误数量: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                print(f"    - {error}")
        else:
            print("\n  ✅ 迁移成功，无错误")
        
        print("="*60)
    
    def close(self):
        """关闭连接"""
        self.sqlite_conn.close()
        self.pg_conn.close()


def main():
    parser = argparse.ArgumentParser(description='SQLite到PostgreSQL数据迁移工具')
    parser.add_argument('sqlite_db', help='SQLite数据库文件路径')
    parser.add_argument('pg_conn', help='PostgreSQL连接字符串 (postgresql://user:pass@host/db)')
    parser.add_argument('--table', '-t', action='append', help='指定要迁移的表（可多次使用）')
    parser.add_argument('--batch-size', '-b', type=int, default=1000, help='批量大小（默认1000）')
    parser.add_argument('--verify', '-v', action='store_true', help='迁移后验证数据')
    
    args = parser.parse_args()
    
    try:
        migrator = DataMigrator(args.sqlite_db, args.pg_conn)
        
        try:
            migrator.migrate_all(args.table, args.batch_size)
            
            # 验证
            if args.verify:
                print("\n🔍 开始验证...")
                sqlite_cursor = migrator.sqlite_conn.cursor()
                sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in sqlite_cursor.fetchall()]
                
                all_verified = True
                for table in tables:
                    if not migrator.verify_migration(table):
                        all_verified = False
                
                if all_verified:
                    print("\n✅ 所有表验证通过")
                else:
                    print("\n⚠️  部分表验证失败")
        
        finally:
            migrator.close()
    
    except FileNotFoundError:
        print(f"❌ 错误: 找不到SQLite数据库文件 {args.sqlite_db}")
        sys.exit(1)
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL错误: {e}")
        sys.exit(1)
    except sqlite3.Error as e:
        print(f"❌ SQLite错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
