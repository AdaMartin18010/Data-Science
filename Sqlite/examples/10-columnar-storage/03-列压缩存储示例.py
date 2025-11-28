#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
列压缩存储示例

对低基数列应用压缩算法，模拟列存储的压缩优势：
- 字典编码：将重复值映射到字典索引
- 游程编码：压缩连续相同值
- 增量编码：存储相邻值的差值
"""

import sqlite3
import time
import os
from collections import Counter

class ColumnCompressor:
    """列压缩器：对列数据应用压缩算法"""
    
    def __init__(self, conn):
        self.conn = conn
        
    def dictionary_encode(self, values):
        """字典编码：将重复值映射到字典索引"""
        # 构建字典
        unique_values = list(set(values))
        dictionary = {val: idx for idx, val in enumerate(unique_values)}
        
        # 编码
        encoded = [dictionary[val] for val in values]
        
        # 计算压缩率
        original_size = len(values) * sum(len(str(v).encode('utf-8')) for v in values) / len(values) if values else 0
        encoded_size = len(encoded) * 4 + len(unique_values) * sum(len(str(v).encode('utf-8')) for v in unique_values) / len(unique_values) if unique_values else 0
        
        compression_ratio = encoded_size / original_size if original_size > 0 else 1.0
        
        return {
            'dictionary': unique_values,
            'encoded': encoded,
            'compression_ratio': compression_ratio
        }
    
    def run_length_encode(self, values):
        """游程编码：压缩连续相同值"""
        if not values:
            return {'encoded': [], 'compression_ratio': 1.0}
            
        encoded = []
        current_value = values[0]
        current_count = 1
        
        for val in values[1:]:
            if val == current_value:
                current_count += 1
            else:
                encoded.append((current_value, current_count))
                current_value = val
                current_count = 1
        encoded.append((current_value, current_count))
        
        original_size = len(values) * sum(len(str(v).encode('utf-8')) for v in values) / len(values) if values else 0
        encoded_size = len(encoded) * (sum(len(str(v[0]).encode('utf-8')) for v in encoded) / len(encoded) if encoded else 0 + 4)
        
        compression_ratio = encoded_size / original_size if original_size > 0 else 1.0
        
        return {
            'encoded': encoded,
            'compression_ratio': compression_ratio
        }
    
    def delta_encode(self, values):
        """增量编码：存储相邻值的差值"""
        if len(values) < 2:
            return {'base': values[0] if values else None, 'deltas': [], 'compression_ratio': 1.0}
        
        try:
            # 转换为数值
            numeric_values = [float(v) for v in values]
        except (ValueError, TypeError):
            return {'base': None, 'deltas': [], 'compression_ratio': 1.0, 'error': 'Non-numeric values'}
        
        base = numeric_values[0]
        deltas = [numeric_values[i] - numeric_values[i-1] for i in range(1, len(numeric_values))]
        
        original_size = len(numeric_values) * 8  # 假设每个值8字节
        # Varint编码：小值用更少字节
        delta_sizes = [1 if abs(d) < 128 else (2 if abs(d) < 16384 else 4) for d in deltas]
        encoded_size = 8 + sum(delta_sizes)  # base + deltas
        
        compression_ratio = encoded_size / original_size if original_size > 0 else 1.0
        
        return {
            'base': base,
            'deltas': deltas,
            'compression_ratio': compression_ratio
        }
    
    def compress_column(self, table_name, column_name, method='dictionary'):
        """压缩表中的列"""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT {column_name} FROM {table_name} ORDER BY rowid")
        values = [row[0] for row in cursor.fetchall()]
        
        if method == 'dictionary':
            result = self.dictionary_encode(values)
        elif method == 'rle':
            result = self.run_length_encode(values)
        elif method == 'delta':
            result = self.delta_encode(values)
        else:
            raise ValueError(f"Unknown compression method: {method}")
        
        # 存储压缩后的数据
        compressed_table = f"{table_name}_{column_name}_compressed"
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {compressed_table} (
                row_id INTEGER PRIMARY KEY,
                encoded_value INTEGER
            )
        """)
        
        if method == 'dictionary':
            # 存储字典
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {compressed_table}_dict (
                    encoded_value INTEGER PRIMARY KEY,
                    original_value TEXT
                )
            """)
            
            cursor.executemany(
                f"INSERT OR REPLACE INTO {compressed_table} (row_id, encoded_value) VALUES (?, ?)",
                [(i+1, val) for i, val in enumerate(result['encoded'])]
            )
            
            cursor.executemany(
                f"INSERT OR REPLACE INTO {compressed_table}_dict (encoded_value, original_value) VALUES (?, ?)",
                [(idx, val) for idx, val in enumerate(result['dictionary'])]
            )
        elif method == 'rle':
            # 存储游程编码
            row_id = 1
            for value, count in result['encoded']:
                cursor.execute(
                    f"INSERT INTO {compressed_table} (row_id, encoded_value) VALUES (?, ?)",
                    (row_id, count)
                )
                row_id += 1
        elif method == 'delta':
            # 存储增量编码
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {compressed_table}_base (
                    base_value REAL
                )
            """)
            cursor.execute(f"INSERT INTO {compressed_table}_base (base_value) VALUES (?)", (result['base'],))
            
            cursor.executemany(
                f"INSERT INTO {compressed_table} (row_id, encoded_value) VALUES (?, ?)",
                [(i+1, int(d)) for i, d in enumerate(result['deltas'])]
            )
        
        self.conn.commit()
        
        return result

def create_sample_data(conn):
    """创建示例数据"""
    cursor = conn.cursor()
    
    # 创建日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY,
            action TEXT,
            user_id INTEGER,
            timestamp INTEGER,
            status INTEGER
        )
    """)
    
    # 插入测试数据
    import random
    actions = ['login', 'logout', 'view', 'edit', 'delete']  # 低基数
    statuses = [0, 1]  # 布尔值，低基数
    
    data = []
    base_time = int(time.time())
    for i in range(50000):
        data.append((
            random.choice(actions),   # 低基数列
            random.randint(1, 100),   # 中等基数
            base_time + i,            # 有序数值列
            random.choice(statuses)   # 布尔列
        ))
    
    cursor.executemany("""
        INSERT INTO logs (action, user_id, timestamp, status)
        VALUES (?, ?, ?, ?)
    """, data)
    
    conn.commit()
    print(f"✅ 创建了 {len(data)} 条日志数据")

def demonstrate_compression(conn, compressor):
    """演示压缩效果"""
    print("\n" + "="*60)
    print("列压缩效果演示")
    print("="*60)
    
    # 压缩1：低基数列（字典编码）
    print("\n1. 低基数列压缩（action列）- 字典编码")
    result1 = compressor.compress_column('logs', 'action', method='dictionary')
    print(f"   压缩率: {result1['compression_ratio']:.2%}")
    print(f"   唯一值数量: {len(result1['dictionary'])}")
    print(f"   原始值示例: {result1['dictionary'][:5]}")
    
    # 压缩2：有序数值列（增量编码）
    print("\n2. 有序数值列压缩（timestamp列）- 增量编码")
    result2 = compressor.compress_column('logs', 'timestamp', method='delta')
    if 'error' not in result2:
        print(f"   压缩率: {result2['compression_ratio']:.2%}")
        print(f"   基准值: {result2['base']}")
        print(f"   差值范围: {min(result2['deltas'])} ~ {max(result2['deltas'])}")
    else:
        print(f"   错误: {result2['error']}")
    
    # 压缩3：布尔列（游程编码）
    print("\n3. 布尔列压缩（status列）- 游程编码")
    result3 = compressor.compress_column('logs', 'status', method='rle')
    print(f"   压缩率: {result3['compression_ratio']:.2%}")
    print(f"   游程数量: {len(result3['encoded'])}")
    print(f"   游程示例（前5个）: {result3['encoded'][:5]}")

def main():
    """主函数"""
    db_path = 'column_compression_example.db'
    
    # 删除旧数据库
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    
    print("="*60)
    print("列压缩存储示例")
    print("="*60)
    
    # 创建示例数据
    print("\n1. 创建示例数据...")
    create_sample_data(conn)
    
    # 演示压缩
    print("\n2. 演示列压缩...")
    compressor = ColumnCompressor(conn)
    demonstrate_compression(conn, compressor)
    
    print("\n" + "="*60)
    print("示例完成！")
    print("="*60)
    print(f"\n数据库文件: {db_path}")
    print("\n💡 总结：")
    print("  - 字典编码适合低基数列（重复值多）")
    print("  - 增量编码适合有序数值列（差值小）")
    print("  - 游程编码适合连续相同值多的列")
    print("  - 列压缩可以显著减少存储空间")
    
    conn.close()

if __name__ == '__main__':
    main()
