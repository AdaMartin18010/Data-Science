#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 标准基准测试工具

提供标准的SQLite性能基准测试套件，包括：
- 插入性能测试
- 查询性能测试
- 更新性能测试
- 删除性能测试
- 并发性能测试
- 综合性能报告

适用版本：SQLite 3.31+
"""

import sqlite3
import time
import statistics
import json
from pathlib import Path
from typing import Dict, List, Tuple

class SQLiteBenchmark:
    """SQLite基准测试类"""
    
    def __init__(self, db_path: str = "benchmark.db", wal_mode: bool = True):
        """
        初始化基准测试
        
        Args:
            db_path: 数据库文件路径
            wal_mode: 是否启用WAL模式
        """
        self.db_path = db_path
        self.wal_mode = wal_mode
        self.results = {}
        
    def setup(self):
        """设置测试环境"""
        # 清理旧数据库
        if Path(self.db_path).exists():
            Path(self.db_path).unlink()
        
        conn = sqlite3.connect(self.db_path)
        if self.wal_mode:
            conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL')
        conn.execute('PRAGMA cache_size=-64000')  # 64MB
        conn.close()
        
    def create_test_table(self, conn):
        """创建测试表"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test_data (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                value INTEGER NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON test_data(name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_value ON test_data(value)")
        conn.commit()
        
    def test_insert_performance(self, num_records: int = 10000, num_runs: int = 5) -> Dict:
        """
        测试插入性能
        
        Args:
            num_records: 每次测试插入的记录数
            num_runs: 运行次数
            
        Returns:
            测试结果字典
        """
        print(f"\n测试插入性能 ({num_records} 条记录, {num_runs} 次运行)...")
        
        times = []
        for run in range(num_runs):
            # 清理表
            conn = sqlite3.connect(self.db_path)
            if self.wal_mode:
                conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('DELETE FROM test_data')
            conn.commit()
            
            # 测试插入
            start_time = time.time()
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO test_data (name, value, description)
                VALUES (?, ?, ?)
            """, [
                (f"record_{i}", i, f"Description for record {i}")
                for i in range(num_records)
            ])
            conn.commit()
            elapsed = time.time() - start_time
            times.append(elapsed)
            conn.close()
            
            print(f"  运行 {run + 1}: {elapsed:.4f} 秒 ({num_records/elapsed:.0f} 记录/秒)")
        
        avg_time = statistics.mean(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        throughput = num_records / avg_time
        
        result = {
            'test': 'insert',
            'num_records': num_records,
            'num_runs': num_runs,
            'avg_time': avg_time,
            'std_dev': std_dev,
            'throughput': throughput,
            'times': times
        }
        self.results['insert'] = result
        return result
        
    def test_select_performance(self, num_queries: int = 1000, num_runs: int = 5) -> Dict:
        """
        测试查询性能
        
        Args:
            num_queries: 每次测试的查询数
            num_runs: 运行次数
            
        Returns:
            测试结果字典
        """
        print(f"\n测试查询性能 ({num_queries} 次查询, {num_runs} 次运行)...")
        
        conn = sqlite3.connect(self.db_path)
        if self.wal_mode:
            conn.execute('PRAGMA journal_mode=WAL')
        cursor = conn.cursor()
        
        # 获取总记录数
        cursor.execute("SELECT COUNT(*) FROM test_data")
        total_records = cursor.fetchone()[0]
        conn.close()
        
        if total_records == 0:
            print("  警告：表中没有数据，跳过查询测试")
            return {}
        
        times = []
        for run in range(num_runs):
            conn = sqlite3.connect(self.db_path)
            if self.wal_mode:
                conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()
            
            start_time = time.time()
            for i in range(num_queries):
                record_id = (i * 7) % total_records + 1  # 伪随机选择
                cursor.execute("SELECT * FROM test_data WHERE id = ?", (record_id,))
                cursor.fetchone()
            elapsed = time.time() - start_time
            times.append(elapsed)
            conn.close()
            
            print(f"  运行 {run + 1}: {elapsed:.4f} 秒 ({num_queries/elapsed:.0f} 查询/秒)")
        
        avg_time = statistics.mean(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        qps = num_queries / avg_time
        
        result = {
            'test': 'select',
            'num_queries': num_queries,
            'num_runs': num_runs,
            'avg_time': avg_time,
            'std_dev': std_dev,
            'qps': qps,
            'times': times
        }
        self.results['select'] = result
        return result
        
    def test_update_performance(self, num_updates: int = 1000, num_runs: int = 5) -> Dict:
        """
        测试更新性能
        
        Args:
            num_updates: 每次测试的更新数
            num_runs: 运行次数
            
        Returns:
            测试结果字典
        """
        print(f"\n测试更新性能 ({num_updates} 次更新, {num_runs} 次运行)...")
        
        conn = sqlite3.connect(self.db_path)
        if self.wal_mode:
            conn.execute('PRAGMA journal_mode=WAL')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM test_data")
        total_records = cursor.fetchone()[0]
        conn.close()
        
        if total_records == 0:
            print("  警告：表中没有数据，跳过更新测试")
            return {}
        
        times = []
        for run in range(num_runs):
            conn = sqlite3.connect(self.db_path)
            if self.wal_mode:
                conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()
            
            start_time = time.time()
            for i in range(num_updates):
                record_id = (i * 11) % total_records + 1
                cursor.execute("""
                    UPDATE test_data 
                    SET value = value + 1, description = ?
                    WHERE id = ?
                """, (f"Updated description {i}", record_id))
            conn.commit()
            elapsed = time.time() - start_time
            times.append(elapsed)
            conn.close()
            
            print(f"  运行 {run + 1}: {elapsed:.4f} 秒 ({num_updates/elapsed:.0f} 更新/秒)")
        
        avg_time = statistics.mean(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        ups = num_updates / avg_time
        
        result = {
            'test': 'update',
            'num_updates': num_updates,
            'num_runs': num_runs,
            'avg_time': avg_time,
            'std_dev': std_dev,
            'ups': ups,
            'times': times
        }
        self.results['update'] = result
        return result
        
    def test_delete_performance(self, num_deletes: int = 1000, num_runs: int = 5) -> Dict:
        """
        测试删除性能
        
        Args:
            num_deletes: 每次测试的删除数
            num_runs: 运行次数
            
        Returns:
            测试结果字典
        """
        print(f"\n测试删除性能 ({num_deletes} 次删除, {num_runs} 次运行)...")
        
        times = []
        for run in range(num_runs):
            # 重新插入数据
            conn = sqlite3.connect(self.db_path)
            if self.wal_mode:
                conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('DELETE FROM test_data')
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO test_data (name, value, description)
                VALUES (?, ?, ?)
            """, [
                (f"record_{i}", i, f"Description {i}")
                for i in range(num_deletes * 2)  # 确保有足够的数据
            ])
            conn.commit()
            
            # 测试删除
            start_time = time.time()
            cursor.execute("DELETE FROM test_data WHERE id <= ?", (num_deletes,))
            conn.commit()
            elapsed = time.time() - start_time
            times.append(elapsed)
            conn.close()
            
            print(f"  运行 {run + 1}: {elapsed:.4f} 秒 ({num_deletes/elapsed:.0f} 删除/秒)")
        
        avg_time = statistics.mean(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        dps = num_deletes / avg_time
        
        result = {
            'test': 'delete',
            'num_deletes': num_deletes,
            'num_runs': num_runs,
            'avg_time': avg_time,
            'std_dev': std_dev,
            'dps': dps,
            'times': times
        }
        self.results['delete'] = result
        return result
        
    def test_range_query_performance(self, num_queries: int = 100, num_runs: int = 5) -> Dict:
        """
        测试范围查询性能
        
        Args:
            num_queries: 每次测试的查询数
            num_runs: 运行次数
            
        Returns:
            测试结果字典
        """
        print(f"\n测试范围查询性能 ({num_queries} 次查询, {num_runs} 次运行)...")
        
        conn = sqlite3.connect(self.db_path)
        if self.wal_mode:
            conn.execute('PRAGMA journal_mode=WAL')
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(value) FROM test_data")
        max_value = cursor.fetchone()[0] or 10000
        conn.close()
        
        times = []
        for run in range(num_runs):
            conn = sqlite3.connect(self.db_path)
            if self.wal_mode:
                conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()
            
            start_time = time.time()
            for i in range(num_queries):
                start_val = (i * 13) % (max_value - 100)
                end_val = start_val + 100
                cursor.execute("""
                    SELECT * FROM test_data 
                    WHERE value BETWEEN ? AND ?
                    ORDER BY value
                """, (start_val, end_val))
                cursor.fetchall()
            elapsed = time.time() - start_time
            times.append(elapsed)
            conn.close()
            
            print(f"  运行 {run + 1}: {elapsed:.4f} 秒 ({num_queries/elapsed:.0f} 查询/秒)")
        
        avg_time = statistics.mean(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        qps = num_queries / avg_time
        
        result = {
            'test': 'range_query',
            'num_queries': num_queries,
            'num_runs': num_runs,
            'avg_time': avg_time,
            'std_dev': std_dev,
            'qps': qps,
            'times': times
        }
        self.results['range_query'] = result
        return result
        
    def generate_report(self) -> str:
        """生成测试报告"""
        report = []
        report.append("=" * 80)
        report.append("SQLite 标准基准测试报告")
        report.append("=" * 80)
        report.append(f"\n测试配置:")
        report.append(f"  数据库: {self.db_path}")
        report.append(f"  WAL模式: {'启用' if self.wal_mode else '禁用'}")
        report.append(f"\n测试结果:")
        report.append("-" * 80)
        
        for test_name, result in self.results.items():
            if not result:
                continue
                
            report.append(f"\n{test_name.upper()} 测试:")
            if test_name == 'insert':
                report.append(f"  平均时间: {result['avg_time']:.4f} 秒")
                report.append(f"  吞吐量: {result['throughput']:.0f} 记录/秒")
            elif test_name == 'select':
                report.append(f"  平均时间: {result['avg_time']:.4f} 秒")
                report.append(f"  QPS: {result['qps']:.0f} 查询/秒")
            elif test_name == 'update':
                report.append(f"  平均时间: {result['avg_time']:.4f} 秒")
                report.append(f"  UPS: {result['ups']:.0f} 更新/秒")
            elif test_name == 'delete':
                report.append(f"  平均时间: {result['avg_time']:.4f} 秒")
                report.append(f"  DPS: {result['dps']:.0f} 删除/秒")
            elif test_name == 'range_query':
                report.append(f"  平均时间: {result['avg_time']:.4f} 秒")
                report.append(f"  QPS: {result['qps']:.0f} 查询/秒")
            
            if result.get('std_dev'):
                report.append(f"  标准差: {result['std_dev']:.4f} 秒")
        
        report.append("\n" + "=" * 80)
        return "\n".join(report)
        
    def save_results(self, filename: str = "benchmark_results.json"):
        """保存测试结果到JSON文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n测试结果已保存到: {filename}")


def main():
    """主函数"""
    print("=" * 80)
    print("SQLite 标准基准测试工具")
    print("=" * 80)
    
    # 创建基准测试实例
    benchmark = SQLiteBenchmark(db_path="benchmark.db", wal_mode=True)
    
    # 设置测试环境
    print("\n设置测试环境...")
    benchmark.setup()
    
    # 创建测试表
    conn = sqlite3.connect(benchmark.db_path)
    benchmark.create_test_table(conn)
    conn.close()
    
    # 运行测试
    print("\n开始运行基准测试...")
    benchmark.test_insert_performance(num_records=10000, num_runs=5)
    benchmark.test_select_performance(num_queries=1000, num_runs=5)
    benchmark.test_update_performance(num_updates=1000, num_runs=5)
    benchmark.test_delete_performance(num_deletes=1000, num_runs=5)
    benchmark.test_range_query_performance(num_queries=100, num_runs=5)
    
    # 生成报告
    print("\n" + benchmark.generate_report())
    
    # 保存结果
    benchmark.save_results()
    
    # 清理
    if Path(benchmark.db_path).exists():
        Path(benchmark.db_path).unlink()
        print(f"\n✅ 清理完成，已删除 {benchmark.db_path}")


if __name__ == "__main__":
    main()
