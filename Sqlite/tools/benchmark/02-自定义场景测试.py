#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 自定义场景测试工具

提供自定义测试场景的性能测试，包括：
- 读密集型场景
- 写密集型场景
- 混合负载场景
- 压力测试
- 性能对比分析

适用版本：SQLite 3.31+
"""

import sqlite3
import time
import statistics
import argparse
import json
from pathlib import Path
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

class CustomScenarioTest:
    """自定义场景测试类"""
    
    def __init__(self, db_path: str = "scenario_test.db", wal_mode: bool = True):
        """
        初始化测试
        
        Args:
            db_path: 数据库文件路径
            wal_mode: 是否启用WAL模式
        """
        self.db_path = db_path
        self.wal_mode = wal_mode
        self.results = {}
        
    def setup(self):
        """设置测试环境"""
        if Path(self.db_path).exists():
            Path(self.db_path).unlink()
        
        conn = sqlite3.connect(self.db_path)
        if self.wal_mode:
            conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL')
        conn.execute('PRAGMA cache_size=-64000')
        conn.close()
        
    def create_test_table(self, conn):
        """创建测试表"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test_data (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                value INTEGER NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON test_data(name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_value ON test_data(value)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON test_data(status)")
        conn.commit()
        
    def read_heavy_scenario(self, num_reads: int = 10000, num_writes: int = 100) -> Dict:
        """
        读密集型场景测试
        
        Args:
            num_reads: 读取操作数
            num_writes: 写入操作数
            
        Returns:
            测试结果
        """
        print(f"\n读密集型场景测试 (读取: {num_reads}, 写入: {num_writes})...")
        
        # 准备数据
        conn = sqlite3.connect(self.db_path)
        if self.wal_mode:
            conn.execute('PRAGMA journal_mode=WAL')
        self.create_test_table(conn)
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO test_data (name, value, status)
            VALUES (?, ?, ?)
        """, [
            (f"record_{i}", i, 'active' if i % 10 != 0 else 'inactive')
            for i in range(10000)
        ])
        conn.commit()
        conn.close()
        
        # 执行测试
        start_time = time.time()
        
        # 读取操作
        read_times = []
        for i in range(num_reads):
            conn = sqlite3.connect(self.db_path)
            if self.wal_mode:
                conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()
            read_start = time.time()
            record_id = (i * 7) % 10000 + 1
            cursor.execute("SELECT * FROM test_data WHERE id = ?", (record_id,))
            cursor.fetchone()
            read_times.append(time.time() - read_start)
            conn.close()
        
        # 写入操作
        write_times = []
        for i in range(num_writes):
            conn = sqlite3.connect(self.db_path)
            if self.wal_mode:
                conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()
            write_start = time.time()
            cursor.execute("""
                INSERT INTO test_data (name, value, status)
                VALUES (?, ?, ?)
            """, (f"new_record_{i}", 10000 + i, 'active'))
            conn.commit()
            write_times.append(time.time() - write_start)
            conn.close()
        
        total_time = time.time() - start_time
        
        result = {
            'scenario': 'read_heavy',
            'num_reads': num_reads,
            'num_writes': num_writes,
            'total_time': total_time,
            'avg_read_time': statistics.mean(read_times),
            'avg_write_time': statistics.mean(write_times),
            'read_qps': num_reads / sum(read_times),
            'write_qps': num_writes / sum(write_times)
        }
        self.results['read_heavy'] = result
        return result
        
    def write_heavy_scenario(self, num_reads: int = 100, num_writes: int = 10000) -> Dict:
        """
        写密集型场景测试
        
        Args:
            num_reads: 读取操作数
            num_writes: 写入操作数
            
        Returns:
            测试结果
        """
        print(f"\n写密集型场景测试 (读取: {num_reads}, 写入: {num_writes})...")
        
        # 准备数据
        conn = sqlite3.connect(self.db_path)
        if self.wal_mode:
            conn.execute('PRAGMA journal_mode=WAL')
        self.create_test_table(conn)
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO test_data (name, value, status)
            VALUES (?, ?, ?)
        """, [
            (f"record_{i}", i, 'active')
            for i in range(1000)
        ])
        conn.commit()
        conn.close()
        
        # 执行测试
        start_time = time.time()
        
        # 写入操作
        write_times = []
        for i in range(num_writes):
            conn = sqlite3.connect(self.db_path)
            if self.wal_mode:
                conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()
            write_start = time.time()
            cursor.execute("""
                INSERT INTO test_data (name, value, status)
                VALUES (?, ?, ?)
            """, (f"new_record_{i}", 1000 + i, 'active'))
            conn.commit()
            write_times.append(time.time() - write_start)
            conn.close()
        
        # 读取操作
        read_times = []
        for i in range(num_reads):
            conn = sqlite3.connect(self.db_path)
            if self.wal_mode:
                conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()
            read_start = time.time()
            record_id = (i * 7) % 1000 + 1
            cursor.execute("SELECT * FROM test_data WHERE id = ?", (record_id,))
            cursor.fetchone()
            read_times.append(time.time() - read_start)
            conn.close()
        
        total_time = time.time() - start_time
        
        result = {
            'scenario': 'write_heavy',
            'num_reads': num_reads,
            'num_writes': num_writes,
            'total_time': total_time,
            'avg_read_time': statistics.mean(read_times),
            'avg_write_time': statistics.mean(write_times),
            'read_qps': num_reads / sum(read_times),
            'write_qps': num_writes / sum(write_times)
        }
        self.results['write_heavy'] = result
        return result
        
    def mixed_load_scenario(self, num_operations: int = 10000, read_ratio: float = 0.7) -> Dict:
        """
        混合负载场景测试
        
        Args:
            num_operations: 总操作数
            read_ratio: 读取操作比例
            
        Returns:
            测试结果
        """
        print(f"\n混合负载场景测试 (总操作: {num_operations}, 读比例: {read_ratio:.0%})...")
        
        # 准备数据
        conn = sqlite3.connect(self.db_path)
        if self.wal_mode:
            conn.execute('PRAGMA journal_mode=WAL')
        self.create_test_table(conn)
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO test_data (name, value, status)
            VALUES (?, ?, ?)
        """, [
            (f"record_{i}", i, 'active' if i % 10 != 0 else 'inactive')
            for i in range(5000)
        ])
        conn.commit()
        conn.close()
        
        num_reads = int(num_operations * read_ratio)
        num_writes = num_operations - num_reads
        
        # 执行测试
        start_time = time.time()
        read_times = []
        write_times = []
        
        for i in range(num_operations):
            conn = sqlite3.connect(self.db_path)
            if self.wal_mode:
                conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()
            
            if i < num_reads:
                # 读取操作
                op_start = time.time()
                record_id = (i * 7) % 5000 + 1
                cursor.execute("SELECT * FROM test_data WHERE id = ?", (record_id,))
                cursor.fetchone()
                read_times.append(time.time() - op_start)
            else:
                # 写入操作
                op_start = time.time()
                cursor.execute("""
                    INSERT INTO test_data (name, value, status)
                    VALUES (?, ?, ?)
                """, (f"new_record_{i}", 5000 + i, 'active'))
                conn.commit()
                write_times.append(time.time() - op_start)
            conn.close()
        
        total_time = time.time() - start_time
        
        result = {
            'scenario': 'mixed_load',
            'num_operations': num_operations,
            'num_reads': num_reads,
            'num_writes': num_writes,
            'read_ratio': read_ratio,
            'total_time': total_time,
            'avg_read_time': statistics.mean(read_times) if read_times else 0,
            'avg_write_time': statistics.mean(write_times) if write_times else 0,
            'read_qps': num_reads / sum(read_times) if read_times else 0,
            'write_qps': num_writes / sum(write_times) if write_times else 0,
            'total_qps': num_operations / total_time
        }
        self.results['mixed_load'] = result
        return result
        
    def stress_test(self, num_threads: int = 4, operations_per_thread: int = 1000) -> Dict:
        """
        压力测试（多线程）
        
        Args:
            num_threads: 线程数
            operations_per_thread: 每个线程的操作数
            
        Returns:
            测试结果
        """
        print(f"\n压力测试 (线程数: {num_threads}, 每线程操作: {operations_per_thread})...")
        
        # 准备数据
        conn = sqlite3.connect(self.db_path)
        if self.wal_mode:
            conn.execute('PRAGMA journal_mode=WAL')
        self.create_test_table(conn)
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO test_data (name, value, status)
            VALUES (?, ?, ?)
        """, [
            (f"record_{i}", i, 'active')
            for i in range(1000)
        ])
        conn.commit()
        conn.close()
        
        def worker(thread_id: int):
            """工作线程函数"""
            times = []
            for i in range(operations_per_thread):
                conn = sqlite3.connect(self.db_path)
                if self.wal_mode:
                    conn.execute('PRAGMA journal_mode=WAL')
                cursor = conn.cursor()
                
                op_start = time.time()
                if i % 2 == 0:
                    # 读取
                    record_id = ((thread_id * operations_per_thread + i) * 7) % 1000 + 1
                    cursor.execute("SELECT * FROM test_data WHERE id = ?", (record_id,))
                    cursor.fetchone()
                else:
                    # 写入
                    cursor.execute("""
                        INSERT INTO test_data (name, value, status)
                        VALUES (?, ?, ?)
                    """, (f"thread_{thread_id}_record_{i}", 1000 + thread_id * operations_per_thread + i, 'active'))
                    conn.commit()
                times.append(time.time() - op_start)
                conn.close()
            return times
        
        # 执行多线程测试
        start_time = time.time()
        all_times = []
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            for future in as_completed(futures):
                all_times.extend(future.result())
        total_time = time.time() - start_time
        
        total_operations = num_threads * operations_per_thread
        
        result = {
            'scenario': 'stress_test',
            'num_threads': num_threads,
            'operations_per_thread': operations_per_thread,
            'total_operations': total_operations,
            'total_time': total_time,
            'avg_operation_time': statistics.mean(all_times),
            'std_dev': statistics.stdev(all_times) if len(all_times) > 1 else 0,
            'ops_per_second': total_operations / total_time
        }
        self.results['stress_test'] = result
        return result
        
    def generate_report(self) -> str:
        """生成测试报告"""
        report = []
        report.append("=" * 80)
        report.append("SQLite 自定义场景测试报告")
        report.append("=" * 80)
        report.append(f"\n测试配置:")
        report.append(f"  数据库: {self.db_path}")
        report.append(f"  WAL模式: {'启用' if self.wal_mode else '禁用'}")
        report.append(f"\n测试结果:")
        report.append("-" * 80)
        
        for scenario, result in self.results.items():
            report.append(f"\n{scenario.upper()} 场景:")
            if scenario == 'read_heavy':
                report.append(f"  总时间: {result['total_time']:.4f} 秒")
                report.append(f"  读取QPS: {result['read_qps']:.0f}")
                report.append(f"  写入QPS: {result['write_qps']:.0f}")
            elif scenario == 'write_heavy':
                report.append(f"  总时间: {result['total_time']:.4f} 秒")
                report.append(f"  读取QPS: {result['read_qps']:.0f}")
                report.append(f"  写入QPS: {result['write_qps']:.0f}")
            elif scenario == 'mixed_load':
                report.append(f"  总时间: {result['total_time']:.4f} 秒")
                report.append(f"  总QPS: {result['total_qps']:.0f}")
                report.append(f"  读取QPS: {result['read_qps']:.0f}")
                report.append(f"  写入QPS: {result['write_qps']:.0f}")
            elif scenario == 'stress_test':
                report.append(f"  总时间: {result['total_time']:.4f} 秒")
                report.append(f"  操作/秒: {result['ops_per_second']:.0f}")
                report.append(f"  平均操作时间: {result['avg_operation_time']:.4f} 秒")
        
        report.append("\n" + "=" * 80)
        return "\n".join(report)
        
    def save_results(self, filename: str = "scenario_results.json"):
        """保存测试结果"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n测试结果已保存到: {filename}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='SQLite自定义场景测试工具')
    parser.add_argument('--scenario', choices=['read-heavy', 'write-heavy', 'mixed', 'stress', 'all'],
                       default='all', help='测试场景')
    parser.add_argument('--wal', action='store_true', default=True, help='启用WAL模式')
    parser.add_argument('--no-wal', dest='wal', action='store_false', help='禁用WAL模式')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("SQLite 自定义场景测试工具")
    print("=" * 80)
    
    # 创建测试实例
    test = CustomScenarioTest(db_path="scenario_test.db", wal_mode=args.wal)
    
    # 设置测试环境
    print("\n设置测试环境...")
    test.setup()
    
    # 运行测试
    print("\n开始运行场景测试...")
    
    if args.scenario in ['read-heavy', 'all']:
        test.read_heavy_scenario(num_reads=10000, num_writes=100)
    
    if args.scenario in ['write-heavy', 'all']:
        test.write_heavy_scenario(num_reads=100, num_writes=10000)
    
    if args.scenario in ['mixed', 'all']:
        test.mixed_load_scenario(num_operations=10000, read_ratio=0.7)
    
    if args.scenario in ['stress', 'all']:
        test.stress_test(num_threads=4, operations_per_thread=1000)
    
    # 生成报告
    print("\n" + test.generate_report())
    
    # 保存结果
    test.save_results()
    
    # 清理
    if Path(test.db_path).exists():
        Path(test.db_path).unlink()
        print(f"\n✅ 清理完成，已删除 {test.db_path}")


if __name__ == "__main__":
    main()
